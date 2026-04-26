"""
SecureDx AI — Patient Repository

The "warehouse manager" for patient data.

For a 15-year-old:
Imagine a warehouse where boxes (patients) are stored:
- get() = Find a specific box by its label
- list() = Get all boxes on today's shelf
- create() = Put a new box in the warehouse
- The warehouse manager (repository) knows where everything is stored

For an interviewer:
Repository pattern provides:
- Abstraction layer between business logic and data access
- Centralized query logic (easier to optimize)
- Testability (mock the repository, not the database)
- Type safety with return types

Design decisions:
- Async methods for non-blocking I/O
- List operations return DTOs, not ORM models (prevent lazy loading issues)
- Filtering happens at database level (not in Python)
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.patient import Patient


class PatientRepository:
    """Data access layer for Patient entities"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, pseudo_id: UUID) -> Optional[Patient]:
        """
        Retrieve a single patient by pseudonymous ID.
        
        Returns None if not found (not an exception).
        """
        result = await self.session.execute(
            select(Patient).where(Patient.pseudo_id == pseudo_id)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        status: Optional[str] = 'active',
        limit: int = 100,
        offset: int = 0,
    ) -> List[Patient]:
        """
        List patients with optional filtering.
        
        Default: Returns active patients only.
        
        For a 15-year-old:
        This is like asking the warehouse manager:
        "Show me all the ACTIVE boxes (not the archived ones),
        but only show me 100 at a time so I don't get overwhelmed."
        
        For an interviewer:
        - Pagination via limit/offset prevents memory issues
        - Status filter happens in SQL (efficient)
        - Default to active prevents accidentally showing discharged patients
        """
        query = select(Patient)
        
        if status:
            query = query.where(Patient.status == status)
        
        query = query.limit(limit).offset(offset).order_by(Patient.display_name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(self, patient: Patient) -> Patient:
        """
        Create a new patient record.
        
        Note: Encryption of PII happens in the application layer
        before calling this method.
        """
        self.session.add(patient)
        await self.session.flush()  # Get the ID without committing
        return patient
    
    async def update(self, patient: Patient) -> Patient:
        """Update an existing patient record"""
        await self.session.merge(patient)
        await self.session.flush()
        return patient
    
    async def count(self, status: Optional[str] = None) -> int:
        """Count patients (useful for pagination)"""
        from sqlalchemy import func
        
        query = select(func.count(Patient.pseudo_id))
        
        if status:
            query = query.where(Patient.status == status)
        
        result = await self.session.execute(query)
        return result.scalar_one()
