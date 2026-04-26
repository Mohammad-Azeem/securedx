"""
SecureDx AI — Patient Schemas

DTOs (Data Transfer Objects) for API requests/responses.

For a 15-year-old:
These are like "permission slips" that say what information is allowed
to leave the building. We NEVER let the encrypted stuff (like real names)
go through the door — only safe stuff like age and pseudonymous IDs.

For an interviewer:
Pydantic v2 schemas provide:
- Request/response validation
- Automatic API documentation (OpenAPI)
- Type safety at API boundary
- Separation of concerns (API layer vs database layer)

Key design:
- Response schemas exclude encrypted fields entirely
- UUID validation prevents SQL injection via patient_id parameter
- Optional fields marked explicitly (aids frontend development)
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class PatientResponse(BaseModel):
    """
    Patient data safe for transmission over API.
    
    Security:
    - NO encrypted fields (encrypted_name, encrypted_mrn, encrypted_ssn)
    - Only pseudonymous identifier (pseudo_id) and derived fields
    - Safe to log, cache, and send to frontend
    """
    pseudo_id: UUID = Field(..., description="Pseudonymous patient identifier")
    display_name: str = Field(..., description="Human-readable pseudonymous name (e.g., 'Patient A123')")
    age_years: Optional[int] = Field(None, description="Age in years (computed from DOB)", ge=0, le=150)
    sex: Optional[str] = Field(None, description="Biological sex", pattern="^(male|female|other|unknown)$")
    last_visit_date: Optional[datetime] = Field(None, description="Most recent clinic visit")
    status: str = Field("active", description="Patient status", pattern="^(active|inactive)$")
    
    model_config = ConfigDict(from_attributes=True)  # Enable ORM mode (SQLAlchemy models -> Pydantic)


class PatientCreateRequest(BaseModel):
    """
    Request to create a new patient.
    
    For admins only. Real identifiers will be encrypted before storage.
    """
    mrn: str = Field(..., description="Medical Record Number", min_length=1, max_length=50)
    full_name: str = Field(..., description="Patient full name", min_length=1, max_length=200)
    ssn: Optional[str] = Field(None, description="Social Security Number (optional)", pattern=r"^\d{3}-\d{2}-\d{4}$")
    age_years: Optional[int] = Field(None, ge=0, le=150)
    sex: Optional[str] = Field(None, pattern="^(male|female|other|unknown)$")


class PatientListFilters(BaseModel):
    """Query parameters for listing patients"""
    status: str = Field("active", pattern="^(active|inactive)$")
    limit: int = Field(100, ge=1, le=500, description="Max results per page")
    offset: int = Field(0, ge=0, description="Pagination offset")
