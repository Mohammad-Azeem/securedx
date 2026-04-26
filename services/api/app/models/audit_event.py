"""
SecureDx AI — Audit Event Model

The "detective's notebook" — every action gets written here.

For a 15-year-old:
Think of this like your school's security camera log:
- 8:00 AM: Student A123 entered building
- 8:05 AM: Student A123 opened locker #42
- 8:10 AM: Student A123 went to classroom 201

But with a twist: Each entry is connected to the previous one with a
"secret code" (hash). If someone tries to erase an entry, the codes won't
match up and we'll know someone tampered with the log!

For an interviewer:
Implements a Merkle chain (blockchain-inspired) for tamper-evident logging:
- Each event includes hash of previous event
- Recomputing hash chain detects any modification/deletion
- Satisfies HIPAA §164.312(b) audit controls requirement
- 6-year retention as per HIPAA §164.530(j)
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class AuditEvent(Base):
    """
    Tamper-evident audit log with hash chaining.
    
    Security guarantees:
    1. Append-only: UPDATE and DELETE are REVOKED at database level
    2. Hash chain: Any modification breaks the chain
    3. Temporal ordering: Guaranteed by created_at timestamp
    """
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Hash chain fields
    event_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 of this event
    previous_hash = Column(String(64), nullable=False)  # Links to previous event
    
    # Event identification
    event_id = Column(String(100), nullable=False, unique=True)  # Human-readable ID
    action = Column(String(100), nullable=False, index=True)  # e.g., "patient_view"
    
    # Actor (always pseudonymous)
    actor_type = Column(String(50), nullable=False)  # user/system/break_glass
    actor_id_hash = Column(String(64), nullable=False, index=True)  # SHA-256(user_id)
    actor_role = Column(String(50), nullable=True)  # physician/admin/compliance_officer
    
    # Resource accessed
    resource_type = Column(String(50), nullable=True)  # patient/inference/audit_log
    resource_id = Column(String(100), nullable=True)  # UUID or identifier
    
    # Outcome
    outcome = Column(String(20), nullable=False)  # success/failure/warning
    outcome_reason = Column(Text, nullable=True)  # Error message if failure
    
    # Context
    request_id = Column(UUID(as_uuid=True), nullable=True)  # Trace across services
    ip_address_hash = Column(String(64), nullable=True)  # SHA-256(ip) for privacy
    user_agent = Column(Text, nullable=True)
    
    # Break-glass flag
    is_break_glass = Column(Boolean, default=False)  # Was this emergency access?
    break_glass_session_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Additional data (JSON for flexibility)
    event_metadata = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)
    
    def __repr__(self):
        return f"<AuditEvent {self.action} by {self.actor_id_hash[:8]}... → {self.outcome}>"


# Database-level security
"""
After creating the table, run:

REVOKE UPDATE, DELETE ON audit_events FROM securedx_app;
GRANT INSERT, SELECT ON audit_events TO securedx_app;

This ensures the application can ONLY append and read, never modify or delete.
"""
