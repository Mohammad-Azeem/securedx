"""
SecureDx AI — Clinician Feedback Loop Endpoint

The feedback loop is the core model improvement flywheel.
Physician accept/modify/reject/flag decisions are:
  1. Logged to the audit trail
  2. Stored as training signals in the local feedback store
  3. Queued for inclusion in the next FL gradient submission

Privacy: Physician IDs stored as one-way SHA-256 hashes.
PHI: Only pseudonymous patient IDs are stored — never raw identifiers.
"""

import hashlib
from enum import StrEnum
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction, AuditOutcome, AuditLogger, get_audit_logger
from app.core.database import get_session
from app.core.security import CurrentUser, require_physician
from app.middleware.request_id import get_request_id
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.repositories.feedback import FeedbackRepository

router = APIRouter()
logger = structlog.get_logger(__name__)


class FeedbackDecision(StrEnum):
    ACCEPT  = "accept"   # Physician agrees with AI suggestion
    MODIFY  = "modify"   # Physician selects a different diagnosis
    REJECT  = "reject"   # Physician rejects all suggestions
    FLAG    = "flag"     # Physician flags for quality review


DECISION_TO_AUDIT = {
    FeedbackDecision.ACCEPT:  AuditAction.DIAGNOSIS_ACCEPT,
    FeedbackDecision.MODIFY:  AuditAction.DIAGNOSIS_MODIFY,
    FeedbackDecision.REJECT:  AuditAction.DIAGNOSIS_REJECT,
    FeedbackDecision.FLAG:    AuditAction.DIAGNOSIS_FLAG,
}


@router.post(
    "/",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit clinician feedback on a diagnostic suggestion",
    description=(
        "Records physician accept/modify/reject/flag decisions on AI diagnostic "
        "suggestions. Feedback is stored locally as a training signal for "
        "federated model improvement. Physician identity is one-way hashed. "
        "No raw PHI is stored in the feedback record."
    ),
)
async def submit_feedback(
    body: FeedbackRequest,
    current_user: Annotated[CurrentUser, Depends(require_physician)],
    db: AsyncSession = Depends(get_session),
    audit: AuditLogger = Depends(get_audit_logger),
    request_id: str = Depends(get_request_id),
) -> FeedbackResponse:

    # One-way hash of physician ID (privacy preservation)
    physician_id_hash = hashlib.sha256(
        current_user.user_id.encode("utf-8")
    ).hexdigest()

    log = logger.bind(
        physician_hash=physician_id_hash[:8] + "...",  # Partial hash for logging
        inference_id=body.inference_id,
        decision=body.decision,
    )
    log.info("Clinician feedback received")

    # Store feedback as training signal
    feedback_repo = FeedbackRepository(db)
    feedback_record = await feedback_repo.create(
        inference_id=body.inference_id,
        patient_pseudo_id=body.patient_pseudo_id,
        physician_id_hash=physician_id_hash,
        decision=body.decision,
        original_icd10=body.original_icd10_code,
        corrected_icd10=body.corrected_icd10_code,   # Set when decision == MODIFY
        quality_rating=body.quality_rating,           # 1-5 stars
        reason_code=body.reason_code,
        notes=body.notes,
    )

    # Audit log
    await audit.write(
        action=DECISION_TO_AUDIT[body.decision],
        outcome=AuditOutcome.SUCCESS,
        actor_id=current_user.user_id,
        actor_role=str(current_user.roles[0]),
        resource_type="DiagnosisSuggestion",
        resource_id=body.inference_id,
        request_id=request_id,
        details={
            "decision": body.decision,
            "original_icd10": body.original_icd10_code,
            "corrected_icd10": body.corrected_icd10_code,
            "quality_rating": body.quality_rating,
            "reason_code": body.reason_code,
            "patient_pseudo_id": body.patient_pseudo_id,
        },
    )

    log.info("Feedback stored", feedback_id=str(feedback_record.id))

    return FeedbackResponse(
        feedback_id=str(feedback_record.id),
        inference_id=body.inference_id,
        decision=body.decision,
        message="Feedback recorded. Thank you — this improves future suggestions.",
        queued_for_training=True,
    )
