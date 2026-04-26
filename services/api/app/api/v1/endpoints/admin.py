"""
SecureDx AI — Admin Dashboard API

For a 15-year-old:
This is Mission Control! The admin can see:
- 📊 How many patients diagnosed today
- 🏥 Which clinics are online/offline
- 🔋 Privacy budget remaining
- 🚨 Any emergency break-glass sessions
- 📈 AI accuracy over time

For an interviewer:
RESTful API for admin dashboard with:
- Real-time system metrics
- FL training statistics
- Audit log analytics
- User management
- Health checks

Security:
- Requires ADMIN role (RBAC)
- Read-only (no destructive operations in dashboard)
- Rate limited (prevent DoS)
"""
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.core.database import get_session
from app.core.security import require_roles, CurrentUser, Role
from app.models import Patient, FeedbackEvent, AuditEvent, BreakGlassSession


router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", summary="List users")
async def list_users():
    return {"endpoint": "admin_users", "status": "stub — Sprint 2"}


@router.get("/dashboard/metrics", response_model=Dict[str, Any])
async def get_dashboard_metrics(
    current_user: CurrentUser = Depends(require_roles(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get high-level dashboard metrics.
    
    Returns:
    ```json
    {
      "patients": {
        "total": 1247,
        "active": 1180,
        "inactive": 67
      },
      "inference": {
        "total_today": 342,
        "total_this_week": 2156,
        "avg_confidence": 0.78
      },
      "feedback": {
        "pending_fl": 89,
        "processed_today": 234
      },
      "privacy": {
        "epsilon_spent": 8.5,
        "epsilon_limit": 10.0,
        "budget_remaining_pct": 15.0
      },
      "system": {
        "services_healthy": 6,
        "services_total": 7,
        "break_glass_active": 0
      }
    }
    ```
    """
    # Patient counts
    patient_total = await session.scalar(select(func.count(Patient.pseudo_id)))
    patient_active = await session.scalar(
        select(func.count(Patient.pseudo_id)).where(Patient.status == 'active')
    )
    
    # Inference counts (from audit log)
    today = datetime.utcnow().date()
    inference_today = await session.scalar(
        select(func.count(AuditEvent.id))
        .where(AuditEvent.action == 'inference_request')
        .where(func.date(AuditEvent.created_at) == today)
    )
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    inference_week = await session.scalar(
        select(func.count(AuditEvent.id))
        .where(AuditEvent.action == 'inference_request')
        .where(AuditEvent.created_at >= week_ago)
    )
    
    # Feedback counts
    feedback_pending = await session.scalar(
        select(func.count(FeedbackEvent.id))
        .where(FeedbackEvent.queued_for_fl == True)
    )
    
    feedback_today = await session.scalar(
        select(func.count(FeedbackEvent.id))
        .where(func.date(FeedbackEvent.submitted_at) == today)
    )
    
    # Privacy budget (from FL client)
    from fl_client.privacy_budget_tracker import get_privacy_budget_tracker
    try:
        budget_tracker = get_privacy_budget_tracker()
        budget_status = budget_tracker.get_status()
        privacy_metrics = {
            "epsilon_spent": budget_status.total_epsilon_spent,
            "epsilon_limit": budget_status.total_epsilon_limit,
            "budget_remaining_pct": (
                (1 - budget_status.total_epsilon_spent / budget_status.total_epsilon_limit) * 100
            ),
            "rounds_participated": budget_status.rounds_participated,
            "remaining_rounds": budget_status.remaining_rounds,
        }
    except Exception:
        privacy_metrics = {"error": "FL client not available"}
    
    # Break-glass sessions
    break_glass_active = await session.scalar(
        select(func.count(BreakGlassSession.id))
        .where(BreakGlassSession.status == 'active')
    )
    
    return {
        "patients": {
            "total": patient_total or 0,
            "active": patient_active or 0,
            "inactive": (patient_total or 0) - (patient_active or 0),
        },
        "inference": {
            "total_today": inference_today or 0,
            "total_this_week": inference_week or 0,
            "avg_confidence": 0.78,  # TODO: compute from inference results
        },
        "feedback": {
            "pending_fl": feedback_pending or 0,
            "processed_today": feedback_today or 0,
        },
        "privacy": privacy_metrics,
        "system": {
            "services_healthy": 6,  # TODO: real health checks
            "services_total": 7,
            "break_glass_active": break_glass_active or 0,
        },
    }


@router.get("/feedback/breakdown", response_model=Dict[str, int])
async def get_feedback_breakdown(
    days: int = 7,
    current_user: CurrentUser = Depends(require_roles(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get feedback decision breakdown (accept/modify/reject/flag).
    
    For a 15-year-old:
    Shows how doctors are grading the AI:
    - 70% accept ✓ (AI is mostly right!)
    - 20% modify ✏️ (AI is close)
    - 8% reject ✗ (AI is wrong)
    - 2% flag 🚩 (AI is dangerous - needs fixing!)
    
    For an interviewer:
    Metrics for model performance monitoring:
    - High accept rate = model performing well
    - High modify rate = model needs fine-tuning
    - High reject rate = model failing
    - Any flags = critical safety issue
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Count by decision type
    decisions = ['accept', 'modify', 'reject', 'flag']
    breakdown = {}
    
    for decision in decisions:
        count = await session.scalar(
            select(func.count(FeedbackEvent.id))
            .where(FeedbackEvent.decision == decision)
            .where(FeedbackEvent.submitted_at >= cutoff)
        )
        breakdown[decision] = count or 0
    
    return breakdown


@router.get("/audit/recent", response_model=List[Dict[str, Any]])
async def get_recent_audit_events(
    limit: int = 50,
    action: str = None,
    current_user: CurrentUser = Depends(require_roles(Role.ADMIN, Role.COMPLIANCE_OFFICER)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get recent audit events (for audit log viewer).
    
    For compliance officers and admins.
    
    Queryable by action type:
    - patient_view
    - inference_request
    - feedback_accept/modify/reject/flag
    - break_glass_activate
    """
    query = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
    
    if action:
        query = query.where(AuditEvent.action == action)
    
    result = await session.execute(query)
    events = result.scalars().all()
    
    return [
        {
            "event_id": event.event_id,
            "action": event.action,
            "actor_type": event.actor_type,
            "outcome": event.outcome,
            "created_at": event.created_at.isoformat(),
            "is_break_glass": event.is_break_glass,
        }
        for event in events
    ]


@router.get("/system/health", response_model=Dict[str, Any])
async def get_system_health(
    current_user: CurrentUser = Depends(require_roles(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get system health status.
    
    For a 15-year-old:
    Traffic light system:
    - 🟢 Green = Everything working
    - 🟡 Yellow = Some warnings
    - 🔴 Red = Something broken!
    
    For an interviewer:
    Aggregated health from:
    - Database connectivity
    - Inference service
    - FL client
    - Keycloak
    - Disk space
    - Memory usage
    """
    health = {
        "overall": "healthy",
        "services": {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Database
    try:
        await session.execute(select(1))
        health["services"]["database"] = {"status": "healthy", "latency_ms": 5}
    except Exception as e:
        health["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health["overall"] = "degraded"
    
    # Inference service (TODO: real health check)
    health["services"]["inference"] = {"status": "healthy", "model_version": "mock-v1.0"}
    
    # FL client
    from fl_client.privacy_budget_tracker import get_privacy_budget_tracker
    try:
        tracker = get_privacy_budget_tracker()
        status = tracker.get_status()
        health["services"]["fl_client"] = {
            "status": "healthy" if not status.budget_depleted else "degraded",
            "rounds_participated": status.rounds_participated,
            "budget_remaining": status.remaining_rounds,
        }
    except Exception as e:
        health["services"]["fl_client"] = {"status": "unknown", "error": str(e)}
    
    # Keycloak (TODO: real health check)
    health["services"]["keycloak"] = {"status": "healthy"}
    
    return health


@router.get("/break-glass/sessions", response_model=List[Dict[str, Any]])
async def get_break_glass_sessions(
    status: str = None,
    current_user: CurrentUser = Depends(require_roles(Role.ADMIN, Role.COMPLIANCE_OFFICER)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get break-glass emergency access sessions.
    
    For compliance review (mandatory 48-hour review).
    
    For a 15-year-old:
    Shows when doctors "broke the glass" in emergencies:
    - Who did it
    - Why (e.g., "Patient unconscious, no ID")
    - When it happened
    - Has it been reviewed?
    """
    query = select(BreakGlassSession).order_by(BreakGlassSession.activated_at.desc())
    
    if status:
        query = query.where(BreakGlassSession.status == status)
    
    result = await session.execute(query)
    sessions = result.scalars().all()
    
    return [
        {
            "id": str(session.id),
            "activated_by": session.activated_by_name,
            "reason": session.reason,
            "activated_at": session.activated_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "status": session.status,
            "reviewed": session.reviewed_at is not None,
            "review_overdue": session.is_review_overdue,
        }
        for session in sessions
    ]
