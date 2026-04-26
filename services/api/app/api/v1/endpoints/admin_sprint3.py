"""SecureDx AI — Admin Endpoints"""
from fastapi import APIRouter
router = APIRouter()

@router.get("/users", summary="List users")
async def list_users():
    return {"endpoint": "admin_users", "status": "stub — Sprint 2"}
