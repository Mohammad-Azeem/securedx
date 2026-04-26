"""
SecureDx AI — Inference API Endpoint (Complete)

For a 15-year-old:
This is the "diagnosis button" that the doctor clicks.
When they fill out the symptom form and click "Analyze",
this code runs the AI brain and returns the answer.

For an interviewer:
Production inference endpoint with:
- Input validation (Pydantic schemas)
- De-identification before inference
- Audit logging (every request logged)
- Error handling with retry logic
- Rate limiting (prevents abuse)
- RBAC enforcement

Request flow:
1. Validate JWT token → Extract user info
2. Validate request body → Ensure all required fields
3. De-identify patient data → Replace MRN with pseudo_id
4. Call inference engine → Get predictions + SHAP
5. Log to audit trail → Record who accessed what
6. Return response → Serialize to JSON
"""
from typing import Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import require_roles, CurrentUser, Role
from app.core.audit import get_audit_logger, AuditLogger
from app.schemas.inference import (
    InferenceRequest,
    InferenceResponse,
    DiagnosisSuggestionResponse,
)
from app.repositories.patient import PatientRepository
from app.services.deidentification import deidentify_features
from app.services.inference_client import get_inference_result


router = APIRouter(prefix="/inference", tags=["inference"])


@router.post("/analyze", response_model=InferenceResponse)
async def analyze_patient(
    request: InferenceRequest,
    current_user: CurrentUser = Depends(require_roles(Role.PHYSICIAN, Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """
    Run diagnostic inference on patient data.
    
    Security:
    - Requires PHYSICIAN or ADMIN role
    - Patient data is de-identified before inference
    - All requests logged in audit trail
    - Raw MRNs rejected (must use pseudo_id)
    
    Request body:
    ```json
    {
      "patient_pseudo_id": "uuid-here",
      "vital_signs": {
        "temperature_f": 102.5,
        "heart_rate_bpm": 95,
        "oxygen_saturation": 94
      },
      "symptoms": ["cough", "fever", "fatigue"]
    }
    ```
    
    Returns:
    - List of diagnosis suggestions with confidence scores
    - SHAP explanations for each suggestion
    - Plain English narrative
    - Top contributing features
    
    For a 15-year-old:
    Doctor fills out form → This function runs AI → Returns diagnosis
    
    For an interviewer:
    Orchestrates:
    1. Data validation (Pydantic)
    2. Patient lookup (verify exists)
    3. Feature engineering (symptoms → binary flags)
    4. De-identification (remove any PII)
    5. Inference (ONNX + SHAP)
    6. Audit logging (who, what, when)
    7. Response serialization (ORM → JSON)
    """
    request_id = uuid4()
    
    # Step 1: Validate patient exists and user has access
    repo = PatientRepository(session)
    patient = await repo.get(request.patient_pseudo_id)
    
    if not patient:
        await audit.log(
            action="inference_request",
            actor_id=current_user.user_id,
            actor_role=current_user.role,
            resource_type="patient",
            resource_id=str(request.patient_pseudo_id),
            outcome="failure",
            outcome_reason="Patient not found",
            request_id=request_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Step 2: Build feature vector from request
    features = _build_feature_vector(request, patient)
    
    # Step 3: De-identify features (remove any residual PII)
    deidentified = deidentify_features(features)
    
    # Step 4: Call inference engine
    try:
        result = await get_inference_result(deidentified)
    except Exception as e:
        await audit.log(
            action="inference_request",
            actor_id=current_user.user_id,
            resource_id=str(patient.pseudo_id),
            outcome="failure",
            outcome_reason=f"Inference failed: {str(e)}",
            request_id=request_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inference engine error"
        )
    
    # Step 5: Audit successful inference
    await audit.log(
        action="inference_request",
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        resource_type="patient",
        resource_id=str(patient.pseudo_id),
        outcome="success",
        request_id=request_id,
        metadata={
            "top_diagnosis": result.suggestions[0].diagnosis_name if result.suggestions else None,
            "confidence": result.overall_confidence,
            "model_version": result.model_version,
        }
    )
    
    # Step 6: Convert to response DTO
    return InferenceResponse(
        inference_id=request_id,
        patient_pseudo_id=patient.pseudo_id,
        suggestions=[
            DiagnosisSuggestionResponse(
                icd10_code=s.icd10_code,
                diagnosis_name=s.diagnosis_name,
                confidence=s.confidence,
                rank=s.rank,
                supporting_features=s.supporting_features,
            )
            for s in result.suggestions
        ],
        overall_confidence=result.overall_confidence,
        model_version=result.model_version,
        evidence_narrative=result.evidence_narrative,
        top_features=[
            {"feature": name, "importance": importance}
            for name, importance in result.top_features
        ],
        missing_features=result.missing_features,
    )


def _build_feature_vector(request: InferenceRequest, patient) -> Dict[str, float]:
    """
    Convert API request + patient record into feature vector.
    
    For a 15-year-old:
    Turns the doctor's notes into numbers the AI can understand:
    - "Patient has fever" → has_fever = 1
    - "Temperature 102.5" → temperature_f = 102.5
    
    For an interviewer:
    Feature engineering logic:
    - Vital signs: Direct mapping (temperature_f, heart_rate_bpm, etc.)
    - Symptoms: Binary flags (cough → has_cough = 1)
    - Demographics: From patient record (age, sex)
    - Missing values: Set to 0 (model handles via SHAP baseline)
    """
    features = {}
    
    # Vital signs (direct mapping)
    if request.vital_signs:
        features['temperature_f'] = request.vital_signs.get('temperature_f', 0)
        features['heart_rate_bpm'] = request.vital_signs.get('heart_rate_bpm', 0)
        features['respiratory_rate'] = request.vital_signs.get('respiratory_rate', 0)
        features['oxygen_saturation'] = request.vital_signs.get('oxygen_saturation', 0)
        features['systolic_bp'] = request.vital_signs.get('systolic_bp', 0)
        features['diastolic_bp'] = request.vital_signs.get('diastolic_bp', 0)
    
    # Symptoms (convert to binary flags)
    symptom_mapping = {
        'cough': 'has_cough',
        'fever': 'has_fever',
        'fatigue': 'has_fatigue',
        'chest_pain': 'has_chest_pain',
        'shortness_of_breath': 'has_shortness_breath',
    }
    
    for symptom, feature_name in symptom_mapping.items():
        features[feature_name] = 1.0 if symptom in (request.symptoms or []) else 0.0
    
    # Demographics from patient record
    features['age_years'] = float(patient.age_years) if patient.age_years else 0
    features['is_male'] = 1.0 if patient.sex == 'male' else 0.0
    
    return features
