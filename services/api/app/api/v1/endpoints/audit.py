"""SecureDx AI — Audit Log Endpoints"""
from fastapi import APIRouter
router = APIRouter()

@router.get("/", summary="View audit log")
async def list_audit():
    return {"endpoint": "audit", "status": "stub — Sprint 2"}

@router.post("/export", summary="Export FHIR AuditEvent bundle")
async def export_audit():
    return {"endpoint": "audit_export", "status": "stub — Sprint 2"}
