"""SecureDx AI — Auth Endpoints"""
from fastapi import APIRouter
router = APIRouter()

@router.get("/me", summary="Get current user profile")
async def get_me():
    """Returns the authenticated user's profile. Token validated by middleware."""
    return {"message": "Implement with get_current_user dependency"}
