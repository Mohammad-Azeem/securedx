"""
SecureDx AI — Feedback Event Model

This is the "teacher correcting the AI's homework" database.

For a 15-year-old:
Imagine the AI is a student learning to diagnose diseases. Every time a doctor
uses it, they grade the AI's answer:
- ✅ "Accept" = Perfect! You got it right.
- ✏️ "Modify" = Close, but the real answer is X.
- ❌ "Reject" = Completely wrong.
- 🚩 "Flag" = This answer is dangerous!

The AI uses these grades to improve (federated learning).

For an interviewer:
This implements a continuous feedback loop for model improvement:
1. Physician reviews AI suggestion
2. Decision logged with timestamp, reasoning, and modified diagnosis
3. Feedback queue feeds into FL training pipeline
4. Privacy: Physician ID is SHA-256 hashed (pseudonymous)
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, JSON, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class FeedbackEvent(Base):
    """
    Physician feedback on AI-generated diagnosis suggestions.
    
    Privacy design:
    - physician_id_hash: SHA-256(physician_id + salt) — irreversible
    - patient_pseudo_id: References Patient.pseudo_id (already de-identified)
    - inference_payload: Contains only de-identified features
    """
    __tablename__ = "feedback_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # References
    patient_pseudo_id = Column(UUID(as_uuid=True), ForeignKey("patients.pseudo_id"), nullable=False)
    inference_request_id = Column(UUID(as_uuid=True), nullable=False)  # Links to audit log
    
    # Physician identity (hashed for privacy)
    # Why hash? Even within the clinic, we don't want to identify which specific
    # physician disagreed with the AI (could create perverse incentives)
    physician_id_hash = Column(String(64), nullable=False, index=True)  # SHA-256 output
    
    # Physician decision
    decision = Column(String(20), nullable=False)  # accept/modify/reject/flag
    
    # Modified diagnosis (if physician changed AI's suggestion)
    modified_diagnosis_code = Column(String(50), nullable=True)  # ICD-10 code
    modified_diagnosis_name = Column(String(200), nullable=True)
    modified_confidence = Column(Float, nullable=True)
    
    # Rationale (free text, optional)
    physician_notes = Column(Text, nullable=True)
    
    # Original AI suggestion (for comparison during FL training)
    original_suggestions = Column(JSON, nullable=False)  # Serialized DiagnosisSuggestion[]
    
    # Features used for inference (de-identified)
    # This is what gets sent to FL training
    feature_vector = Column(JSON, nullable=False)
    
    # Metadata
    submitted_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)
    queued_for_fl = Column(Boolean, default=True)  # Has this been picked up by FL client?
    fl_processed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Feedback {self.decision} by {self.physician_id_hash[:8]}... on {self.patient_pseudo_id}>"
