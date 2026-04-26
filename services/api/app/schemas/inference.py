"""
SecureDx AI — Inference Schemas

All schemas use strict Pydantic v2 validation.
PHI NOTE: InferenceRequest must only contain de-identified or
pseudonymized data. The patient_pseudo_id is a clinic-local UUID,
not a name, MRN, or other direct identifier.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# INPUT SCHEMAS
# =============================================================================

class LabResult(BaseModel):
    """A single lab test result."""
    loinc_code: str = Field(..., description="LOINC code for the test")
    display_name: str = Field(..., description="Human-readable test name")
    value: float = Field(..., description="Numeric result value")
    unit: str = Field(..., description="Unit of measurement (e.g., mg/dL)")
    reference_low: float | None = None
    reference_high: float | None = None
    collected_at: datetime | None = None

    @property
    def is_abnormal(self) -> bool:
        if self.reference_low is not None and self.value < self.reference_low:
            return True
        if self.reference_high is not None and self.value > self.reference_high:
            return True
        return False


class VitalSigns(BaseModel):
    """Current encounter vital signs."""
    systolic_bp: int | None = Field(None, ge=50, le=300, description="Systolic BP (mmHg)")
    diastolic_bp: int | None = Field(None, ge=20, le=200, description="Diastolic BP (mmHg)")
    heart_rate: int | None = Field(None, ge=20, le=300, description="Heart rate (bpm)")
    respiratory_rate: int | None = Field(None, ge=4, le=60, description="Resp rate (breaths/min)")
    temperature_celsius: float | None = Field(None, ge=30.0, le=45.0, description="Temp (°C)")
    spo2_percent: float | None = Field(None, ge=50.0, le=100.0, description="SpO2 (%)")
    weight_kg: float | None = Field(None, ge=0.5, le=500.0, description="Weight (kg)")
    bmi: float | None = Field(None, ge=5.0, le=100.0, description="BMI")
    pain_score: int | None = Field(None, ge=0, le=10, description="VAS pain score (0-10)")


class Symptom(BaseModel):
    """A reported symptom mapped to SNOMED CT."""
    snomed_code: str = Field(..., description="SNOMED CT concept ID")
    display_name: str
    duration_days: int | None = Field(None, ge=0)
    severity: int | None = Field(None, ge=1, le=10, description="Severity (1-10 VAS)")
    onset: str | None = Field(None, description="sudden | gradual | unknown")


class Medication(BaseModel):
    """An active medication."""
    rxnorm_code: str = Field(..., description="RxNorm concept ID")
    display_name: str
    dose_mg: float | None = None
    frequency: str | None = None   # e.g., "once daily", "BID"
    duration_days: int | None = None


class ImagingMetadata(BaseModel):
    """
    Structured imaging metadata only — NOT the image itself.
    Images (DICOM) are excluded from MVP to simplify PHI boundary.
    """
    modality: str = Field(..., description="CT | MRI | XR | US | NM")
    body_part: str = Field(..., description="Body part examined (SNOMED CT preferred)")
    impression_codes: list[str] = Field(default_factory=list, description="SNOMED CT impression codes")
    laterality: str | None = Field(None, description="left | right | bilateral | na")
    study_date: datetime | None = None


class DiagnosisHistory(BaseModel):
    """A prior diagnosis (de-identified encounter)."""
    icd10_code: str
    display_name: str
    onset_date: datetime | None = None
    resolved: bool = False


class InferenceRequest(BaseModel):
    """
    Clinical data submitted for diagnostic analysis.

    CRITICAL: patient_pseudo_id must be a pseudonymous UUID generated
    by the de-identification pipeline. Never submit raw MRN, name,
    DOB, or other direct identifiers.
    """
    # Patient context (pseudonymous only)
    patient_pseudo_id: str = Field(
        ...,
        description="Pseudonymous patient UUID (never raw MRN/name)",
        min_length=36,
        max_length=36,
    )
    patient_age_years: int | None = Field(None, ge=0, le=130)
    patient_sex: str | None = Field(None, description="male | female | other | unknown")

    # Clinical inputs (all optional — engine handles missing data gracefully)
    lab_results: list[LabResult] | None = None
    vital_signs: VitalSigns | None = None
    symptoms: list[Symptom] | None = None
    medications: list[Medication] | None = None
    imaging_metadata: list[ImagingMetadata] | None = None
    diagnosis_history: list[DiagnosisHistory] | None = None

    @field_validator("patient_pseudo_id")
    @classmethod
    def validate_pseudo_id(cls, v: str) -> str:
        """Ensure patient_pseudo_id looks like a UUID, not a raw MRN."""
        import re
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        if not uuid_pattern.match(v):
            raise ValueError(
                "patient_pseudo_id must be a UUID. "
                "Raw patient identifiers (MRN, name, DOB) are not permitted."
            )
        return v


# =============================================================================
# OUTPUT SCHEMAS
# =============================================================================

class ShapFeature(BaseModel):
    """SHAP attribution for a single feature."""
    feature_name: str
    feature_value: str         # Formatted for display (e.g., "2.4 mg/dL")
    shap_value: float          # Positive = pushes toward diagnosis, negative = against
    direction: str             # "supporting" | "opposing"
    magnitude: str             # "strong" | "moderate" | "weak"


class DiagnosisSuggestion(BaseModel):
    """A single differential diagnosis suggestion with full XAI context."""
    rank: int = Field(..., ge=1, le=10)
    icd10_code: str
    icd10_display: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence (0-1)")
    confidence_label: str       # "High" | "Moderate" | "Low"

    # Explainability
    evidence_narrative: str     # NLG-generated clinical rationale
    top_features: list[ShapFeature]  # SHAP attributions (top 5)

    # Referral and urgency flags
    referral_recommended: bool = False
    referral_specialty: str | None = None
    urgency: str | None = None  # "routine" | "urgent" | "emergent"

    # Drug interaction flag
    drug_interaction_alert: str | None = None


class InferenceResponse(BaseModel):
    """Full inference response returned to the physician UI."""
    patient_pseudo_id: str
    encounter_id: str
    suggestions: list[DiagnosisSuggestion]
    missing_data_prompts: list[str] = Field(
        default_factory=list,
        description="Inputs that would improve confidence if provided",
    )
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    inference_latency_ms: int
    disclaimer: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
