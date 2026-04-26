"""SecureDx AI — Break-Glass Schemas"""
from datetime import datetime
from pydantic import BaseModel

class BreakGlassActivateRequest(BaseModel):
    patient_pseudo_id: str
    reason_code: str
    justification: str

class BreakGlassActivateResponse(BaseModel):
    session_id: str
    patient_pseudo_id: str
    activated_by: str
    activated_at: datetime
    expires_at: datetime
    review_deadline: datetime
    message: str

class BreakGlassReviewRequest(BaseModel):
    clinical_necessity: str
    actions_taken: str
    clinical_outcome: str
    patient_notified: bool

class BreakGlassSession(BaseModel):
    session_id: str
    patient_pseudo_id: str
    activated_by: str
    activated_at: datetime
