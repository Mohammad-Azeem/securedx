"""SecureDx AI — Feedback Schemas"""
from pydantic import BaseModel, Field
from typing import Literal

class FeedbackRequest(BaseModel):
    inference_id: str
    patient_pseudo_id: str
    decision: Literal["accept", "modify", "reject", "flag"]
    original_icd10_code: str
    corrected_icd10_code: str | None = None
    quality_rating: int | None = Field(None, ge=1, le=5)
    reason_code: str | None = None
    notes: str | None = None

class FeedbackResponse(BaseModel):
    feedback_id: str
    inference_id: str
    decision: str
    message: str
    queued_for_training: bool
