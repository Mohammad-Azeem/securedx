"""
SecureDx AI — Inference Endpoint

Orchestrates clinical diagnostic analysis:
1. Validates and de-identifies the input
2. Calls the ONNX inference service
3. Computes SHAP explanations
4. Returns differential diagnoses with evidence narratives
5. Logs the request to the audit trail

PHI BOUNDARY: This endpoint receives clinical input but strips all
PHI identifiers before passing data to the inference engine.
No PHI is ever forwarded to external services.
"""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction, AuditOutcome, get_audit_logger, AuditLogger
from app.core.database import get_session
from app.core.security import CurrentUser, require_physician
from app.schemas.inference import (
    InferenceRequest,
    InferenceResponse,
    DiagnosisSuggestion,
)
from app.services.deidentification import DeidentificationService
from app.services.inference_client import InferenceClient
from app.middleware.request_id import get_request_id

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post(
    "/analyze",
    response_model=InferenceResponse,
    summary="Run clinical diagnostic analysis",
    description=(
        "Accepts structured clinical inputs (labs, vitals, symptoms, medications) "
        "and returns AI-generated differential diagnosis suggestions with SHAP "
        "explainability. All PHI is de-identified before inference. "
        "**HIPAA §164.312(c)**: Input/output integrity verified."
    ),
)
async def analyze(
    request: InferenceRequest,
    current_user: Annotated[CurrentUser, Depends(require_physician)],
    db: AsyncSession = Depends(get_session),
    audit: AuditLogger = Depends(get_audit_logger),
    request_id: str = Depends(get_request_id),
) -> InferenceResponse:

    log = logger.bind(
        user_id=current_user.user_id,
        patient_pseudo_id=request.patient_pseudo_id,
        request_id=request_id,
    )
    log.info("Inference request received")

    # --- 1. Log the incoming request (before processing) ---
    await audit.write(
        action=AuditAction.INFERENCE_REQUEST,
        outcome=AuditOutcome.SUCCESS,
        actor_id=current_user.user_id,
        actor_role=str(current_user.roles[0]) if current_user.roles else None,
        resource_type="ClinicalEncounter",
        resource_id=request.patient_pseudo_id,  # Pseudonymous only
        request_id=request_id,
        details={
            "input_types": [k for k, v in request.model_dump().items()
                            if v is not None and k != "patient_pseudo_id"],
            "is_break_glass": current_user.is_break_glass,
        },
        is_break_glass=current_user.is_break_glass,
    )

    # --- 2. De-identify inputs (belt-and-suspenders) ---
    deident_service = DeidentificationService()
    sanitized_input = await deident_service.sanitize_inference_input(request)

    # --- 3. Call local inference engine ---
    inference_client = InferenceClient()
    try:
        raw_result = await inference_client.predict(sanitized_input)
    except Exception as e:
        log.error("Inference engine call failed", error=str(e))
        await audit.write(
            action=AuditAction.INFERENCE_RESPONSE,
            outcome=AuditOutcome.FAILURE,
            actor_id=current_user.user_id,
            actor_role=str(current_user.roles[0]) if current_user.roles else None,
            resource_type="ClinicalEncounter",
            resource_id=request.patient_pseudo_id,
            request_id=request_id,
            details={"error": "inference_service_unavailable"},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inference service temporarily unavailable. Clinical workflow unaffected — proceed with standard assessment.",
        )

    # --- 4. Build response ---
    response = InferenceResponse(
        patient_pseudo_id=request.patient_pseudo_id,
        encounter_id=raw_result.encounter_id,
        suggestions=raw_result.suggestions,
        missing_data_prompts=raw_result.missing_data_prompts,
        overall_confidence=raw_result.overall_confidence,
        model_version=raw_result.model_version,
        inference_latency_ms=raw_result.inference_latency_ms,
        disclaimer=(
            "AI suggestions are for clinical decision support only. "
            "The treating physician is the decision-maker of record. "
            "All suggestions require clinician review before action."
        ),
    )

    # --- 5. Log the response ---
    await audit.write(
        action=AuditAction.INFERENCE_RESPONSE,
        outcome=AuditOutcome.SUCCESS,
        actor_id=current_user.user_id,
        actor_role=str(current_user.roles[0]) if current_user.roles else None,
        resource_type="ClinicalEncounter",
        resource_id=request.patient_pseudo_id,
        request_id=request_id,
        details={
            "num_suggestions": len(response.suggestions),
            "top_diagnosis_code": response.suggestions[0].icd10_code if response.suggestions else None,
            "top_confidence": response.suggestions[0].confidence if response.suggestions else None,
            "model_version": response.model_version,
            "latency_ms": response.inference_latency_ms,
        },
    )

    log.info(
        "Inference complete",
        num_suggestions=len(response.suggestions),
        latency_ms=response.inference_latency_ms,
    )

    return response
