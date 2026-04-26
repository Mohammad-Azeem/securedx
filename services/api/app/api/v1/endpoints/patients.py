"""SecureDx AI — Patient Endpoints"""
# services/api/app/api/v1/endpoints/patients.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.patient import Patient
from app.schemas.patient import PatientResponse

router = APIRouter()

@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Get all patients from database"""
    query = select(Patient).where(Patient.status == 'active')
    result = await session.execute(query)
    patients = result.scalars().all()
    return patients

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Get single patient by ID"""
    query = select(Patient).where(Patient.pseudo_id == patient_id)
    result = await session.execute(query)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(404, "Patient not found")
    
    return patient