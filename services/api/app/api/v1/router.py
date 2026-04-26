"""SecureDx AI — API v1 Router"""

from fastapi import APIRouter
#from app.api import patients_endpoint              # This is wrong, it causes circular imports. The correct import is below, which registers the patients endpoint with the API router without causing circular imports.
from app.api.v1.endpoints import patients                         # This import is necessary to register the patients endpoint with the API router, even if it's not directly used in this file.

from app.api.v1.endpoints import (
    auth,
    inference,
    fhir,
    audit,
    break_glass,
    admin,
    feedback,
)

api_router = APIRouter()

api_router.include_router(auth.router,        prefix="/auth",        tags=["Authentication"])
api_router.include_router(fhir.router,        prefix="/fhir",        tags=["FHIR Ingestion"])
api_router.include_router(patients.router,    prefix="/patients",    tags=["Patients"])
api_router.include_router(inference.router,   prefix="/inference",   tags=["Inference"])
api_router.include_router(feedback.router,    prefix="/feedback",    tags=["Clinician Feedback"])
api_router.include_router(break_glass.router, prefix="/break-glass", tags=["Break-Glass"])
api_router.include_router(audit.router,       prefix="/audit",       tags=["Audit"])
api_router.include_router(admin.router,       prefix="/admin",       tags=["Administration"])


# Add health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}