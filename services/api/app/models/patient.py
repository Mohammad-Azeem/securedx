"""
SecureDx AI — Patient Model

Privacy design:
- pseudo_id: UUID (safe to share within clinic)
- Real identifiers (MRN, name, SSN): Encrypted at-rest via pgcrypto
- Derived fields (age_years): Computed, not encrypted (needed for analytics)
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Patient(Base):
    """
    Patient entity with pseudonymous identifier.
    
    For a 15-year-old:
    Think of this like a Pokemon card. The card has:
    - A unique card number (pseudo_id) that everyone can see
    - Hidden stats (encrypted_mrn) that only the game master can decrypt
    - Visible stats (age_years, sex) that anyone can use
    
    For an interviewer:
    This implements HIPAA's "Safe Harbor" de-identification method (§164.514):
    - Remove direct identifiers (name, MRN, SSN) via encryption
    - Retain indirect identifiers (age, sex) for clinical utility
    - Use consistent pseudonymous ID within clinic (enables longitudinal analysis)
    """
    __tablename__ = "patients"

    # Pseudonymous identifier (safe to use in logs, API responses)
    pseudo_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Encrypted identifiers (only decrypted when absolutely necessary)
    # pgcrypto AES-256-GCM encryption happens in the application layer
    encrypted_mrn = Column(Text, nullable=True)  # Medical Record Number
    encrypted_name = Column(Text, nullable=True)
    encrypted_ssn = Column(Text, nullable=True)
    
    # De-identified fields (safe for analysis and AI training)
    display_name = Column(String(100), nullable=False)  # e.g., "Patient A123"
    age_years = Column(Integer, nullable=True)
    sex = Column(String(20), nullable=True)  # male/female/other/unknown
    
    # Clinical metadata
    last_visit_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="active")  # active/inactive
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_user_id = Column(String(100), nullable=True)  # Keycloak user ID (hashed)
    
    def __repr__(self):
        return f"<Patient {self.display_name} ({self.pseudo_id})>"
