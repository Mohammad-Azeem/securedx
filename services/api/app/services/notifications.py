"""SecureDx AI — Notification Service (break-glass alerts)"""
import structlog
logger = structlog.get_logger(__name__)

class NotificationService:
    async def send_break_glass_alert(self, activating_user, patient_pseudo_id,
                                     reason_code, justification, event_id, expires_at):
        """Send multi-channel alert. Sprint 2: wire up email + in-app notifications."""
        logger.warning(
            "BREAK-GLASS ALERT (stub — configure email in Sprint 2)",
            activating_user=activating_user.user_id,
            patient=patient_pseudo_id,
            reason=reason_code,
            event_id=event_id,
        )
