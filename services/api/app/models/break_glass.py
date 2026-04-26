"""
SecureDx AI — Break-Glass Session Model

The "emergency override" log.

For a 15-year-old:
Imagine a fire alarm with a glass case that says "Break in case of emergency."
When a doctor breaks the glass:
1. An alarm goes off (SMS to admin)
2. They get special access for 4 hours
3. Everything they do gets marked with a 🚨 emoji
4. After 48 hours, someone MUST review what happened

For an interviewer:
Implements HIPAA §164.312(a)(2)(ii) Emergency Access Procedure:
- Time-limited access (4 hours default)
- Multi-channel alerting (SMS + email)
- Mandatory post-event review within 48 hours
- All actions during session tagged with is_break_glass=True in audit log
"""
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class BreakGlassSession(Base):
    """
    Emergency access session with mandatory review.
    
    Lifecycle:
    1. Activated: Doctor provides reason + justification
    2. Active: 4-hour window where access is granted
    3. Expired: Session ends automatically
    4. Reviewed: Compliance officer reviews within 48 hours
    """
    __tablename__ = "break_glass_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Who activated it
    activated_by_user_id_hash = Column(String(64), nullable=False)  # SHA-256(user_id)
    activated_by_name = Column(String(200), nullable=False)  # For human readability
    activated_by_role = Column(String(50), nullable=False)
    
    # Why it was activated
    reason = Column(String(200), nullable=False)  # e.g., "Patient unconscious, no ID"
    justification = Column(Text, nullable=False)  # Detailed explanation
    
    # Resource being accessed
    patient_pseudo_id = Column(UUID(as_uuid=True), nullable=True)  # If specific patient
    resource_description = Column(String(500), nullable=True)  # If general access
    
    # Time window
    activated_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    actually_ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(20), default="active")  # active/expired/terminated
    
    # Alerting
    admin_notified_at = Column(DateTime(timezone=True), nullable=True)
    admin_notified_via = Column(String(100), nullable=True)  # sms/email/both
    
    # Mandatory review
    review_deadline = Column(DateTime(timezone=True), nullable=False)  # activated_at + 48h
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id_hash = Column(String(64), nullable=True)
    review_outcome = Column(String(20), nullable=True)  # approved/flagged/escalated
    review_notes = Column(Text, nullable=True)
    
    # Usage stats
    actions_performed = Column(Integer, default=0)  # Count of audit events
    patients_accessed = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<BreakGlass {self.reason} by {self.activated_by_name} ({self.status})>"
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_review_overdue(self):
        return datetime.utcnow() > self.review_deadline and not self.reviewed_at
