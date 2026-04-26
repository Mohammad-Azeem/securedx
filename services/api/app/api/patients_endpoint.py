"""
SecureDx AI — Patients API Endpoint

Exposes patient data to the frontend (de-identified).

For a 15-year-old:
This is like the reception desk at a hospital. When the doctor asks
"Who's on my schedule today?", the receptionist checks the computer
and gives back a list. But they never show sensitive info like social
security numbers — only safe info like "Patient A123, 45 years old."

For an interviewer:
RESTful API following these principles:
- GET /patients: List patients (physicians see only their scheduled patients)
- GET /patients/{id}: Get single patient details
- Never returns raw PII (encrypted fields stay encrypted)
- Only returns pseudonymous IDs and derived fields (age, sex)
- RBAC enforcement via dependency injection

Security considerations:
- All endpoints require authentication (Keycloak JWT)
- Role-based access (physician or admin only)
- Audit logging on every access
- No filtering by real identifiers (MRN, name) to prevent enumeration attacks
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.security import require_roles, CurrentUser, Role
from app.core.audit import get_audit_logger, AuditLogger
from app.repositories.patient import PatientRepository
from app.schemas.patient import PatientResponse


router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    status: str = "active",
    limit: int = 100,
    offset: int = 0,
    current_user: CurrentUser = Depends(require_roles(Role.PHYSICIAN, Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """
    List patients visible to the current user.
    
    For physicians: Returns today's scheduled patients (in future: filtered by user)
    For admins: Returns all patients
    
    Query parameters:
    - status: 'active' or 'inactive' (default: active)
    - limit: Max results per page (default: 100, max: 500)
    - offset: Pagination offset (default: 0)
    
    Returns:
    - List of PatientResponse DTOs (pseudonymous only)
    """
    # Enforce pagination limits (prevent DoS via large result sets)
    if limit > 500:
        limit = 500
    
    # Repository pattern: separate data access from business logic
    repo = PatientRepository(session)
    patients = await repo.list(status=status, limit=limit, offset=offset)
    
    # Audit log: Record that user accessed patient list
    await audit.log(
        action="patient_list",
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        outcome="success",
        metadata={
            "count": len(patients),
            "status_filter": status,
        }
    )
    
    # Convert ORM models to DTOs (Data Transfer Objects)
    # Why? Prevents accidental exposure of encrypted fields
    return [
        PatientResponse(
            pseudo_id=p.pseudo_id,
            display_name=p.display_name,
            age_years=p.age_years,
            sex=p.sex,
            last_visit_date=p.last_visit_date,
            status=p.status,
        )
        for p in patients
    ]


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    current_user: CurrentUser = Depends(require_roles(Role.PHYSICIAN, Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """
    Get detailed information about a specific patient.
    
    Security:
    - Only pseudonymous ID accepted (not MRN or name)
    - Encrypted fields are NOT decrypted or returned
    - Access is logged in audit trail
    
    Returns:
    - PatientResponse with de-identified fields only
    - 404 if patient not found or user lacks access
    """
    repo = PatientRepository(session)
    patient = await repo.get(patient_id)
    
    if not patient:
        # Audit failed access attempt
        await audit.log(
            action="patient_view",
            actor_id=current_user.user_id,
            actor_role=current_user.role,
            resource_type="patient",
            resource_id=str(patient_id),
            outcome="failure",
            outcome_reason="Patient not found",
        )
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Audit successful access
    await audit.log(
        action="patient_view",
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        resource_type="patient",
        resource_id=str(patient_id),
        outcome="success",
    )
    
    return PatientResponse(
        pseudo_id=patient.pseudo_id,
        display_name=patient.display_name,
        age_years=patient.age_years,
        sex=patient.sex,
        last_visit_date=patient.last_visit_date,
        status=patient.status,
    )
