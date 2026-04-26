"""
SecureDx AI — Break-Glass Emergency Access Endpoint

HIPAA §164.312(a)(2)(ii): Emergency Access Procedure (Addressable)

The Break-Glass protocol allows an authorized physician to access a patient's
data in a clinical emergency, even without the standard access path.

Every break-glass activation:
  1. Creates an immediate multi-channel alert (email + in-app)
  2. Grants time-limited elevated access (4 hours by default)
  3. Tags ALL subsequent actions as [BREAK-GLASS] in the audit log
  4. Requires a mandatory post-event review within 48 hours

This satisfies HIPAA's requirement for an emergency access procedure
while maintaining a complete, auditable access record.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction, AuditOutcome, AuditLogger, get_audit_logger
from app.core.database import get_session
from app.core.security import CurrentUser, Role, require_roles
from app.middleware.request_id import get_request_id
from app.schemas.break_glass import (
    BreakGlassActivateRequest,
    BreakGlassActivateResponse,
    BreakGlassReviewRequest,
    BreakGlassSession,
)
from app.services.notifications import NotificationService

router = APIRouter()
logger = structlog.get_logger(__name__)

BREAK_GLASS_DURATION_HOURS = 4
BREAK_GLASS_REVIEW_DEADLINE_HOURS = 48


@router.post(
    "/activate",
    response_model=BreakGlassActivateResponse,
    summary="Activate break-glass emergency access",
    description=(
        "Grants temporary elevated access to a patient record in an emergency. "
        "Immediately triggers multi-channel alerts to the clinic administrator "
        "and compliance officer. All subsequent actions are tagged BREAK-GLASS "
        "in the audit log. A mandatory review must be completed within 48 hours."
    ),
)
async def activate_break_glass(
    body: BreakGlassActivateRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_roles(Role.PHYSICIAN, Role.ADMIN))],
    db: AsyncSession = Depends(get_session),
    audit: AuditLogger = Depends(get_audit_logger),
    request_id: str = Depends(get_request_id),
) -> BreakGlassActivateResponse:

    log = logger.bind(
        user_id=current_user.user_id,
        patient_pseudo_id=body.patient_pseudo_id,
        reason_code=body.reason_code,
    )
    log.warning("BREAK-GLASS ACTIVATION INITIATED")

    # Write activation audit event
    event_id = await audit.write(
        action=AuditAction.BREAK_GLASS_ACTIVATE,
        outcome=AuditOutcome.SUCCESS,
        actor_id=current_user.user_id,
        actor_role=str(current_user.roles[0]),
        resource_type="Patient",
        resource_id=body.patient_pseudo_id,
        request_id=request_id,
        ip_address=request.client.host if request.client else None,
        details={
            "reason_code": body.reason_code,
            "justification": body.justification,
            "duration_hours": BREAK_GLASS_DURATION_HOURS,
        },
        is_break_glass=True,
    )

    # Calculate session expiry
    expires_at = datetime.now(timezone.utc) + timedelta(hours=BREAK_GLASS_DURATION_HOURS)
    review_deadline = datetime.now(timezone.utc) + timedelta(hours=BREAK_GLASS_REVIEW_DEADLINE_HOURS)

    # Send immediate multi-channel alerts
    notification_service = NotificationService()
    await notification_service.send_break_glass_alert(
        activating_user=current_user,
        patient_pseudo_id=body.patient_pseudo_id,
        reason_code=body.reason_code,
        justification=body.justification,
        event_id=event_id,
        expires_at=expires_at,
    )

    log.warning(
        "BREAK-GLASS SESSION CREATED",
        event_id=event_id,
        expires_at=expires_at.isoformat(),
        alerts_sent=True,
    )

    return BreakGlassActivateResponse(
        session_id=event_id,
        patient_pseudo_id=body.patient_pseudo_id,
        activated_by=current_user.user_id,
        activated_at=datetime.now(timezone.utc),
        expires_at=expires_at,
        review_deadline=review_deadline,
        message=(
            "Emergency access granted. All actions during this session are tagged "
            "[BREAK-GLASS] in the audit log. Alerts have been sent to the clinic "
            f"administrator and compliance officer. A review is required by "
            f"{review_deadline.strftime('%Y-%m-%d %H:%M UTC')}."
        ),
    )


@router.post(
    "/review/{session_id}",
    summary="Submit mandatory post-access review",
    description=(
        "Submits the required post-event review for a break-glass session. "
        "Reviews must be completed within 48 hours of activation."
    ),
)
async def submit_review(
    session_id: str,
    body: BreakGlassReviewRequest,
    current_user: Annotated[CurrentUser, Depends(require_roles(Role.PHYSICIAN, Role.ADMIN))],
    audit: AuditLogger = Depends(get_audit_logger),
    request_id: str = Depends(get_request_id),
) -> dict:

    await audit.write(
        action=AuditAction.BREAK_GLASS_REVIEW_SUBMIT,
        outcome=AuditOutcome.SUCCESS,
        actor_id=current_user.user_id,
        actor_role=str(current_user.roles[0]),
        resource_type="BreakGlassSession",
        resource_id=session_id,
        request_id=request_id,
        details={
            "clinical_necessity": body.clinical_necessity,
            "actions_taken": body.actions_taken,
            "outcome": body.clinical_outcome,
            "patient_notified": body.patient_notified,
        },
        is_break_glass=True,
    )

    logger.info("Break-glass review submitted", session_id=session_id, reviewer=current_user.user_id)

    return {"status": "review_submitted", "session_id": session_id}
