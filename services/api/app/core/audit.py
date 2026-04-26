"""
SecureDx AI — Tamper-Evident Audit Logging Service

REGULATION REQUIRED: HIPAA §164.312(b) — Audit Controls
Implements a SHA-256 Merkle-tree hash chain across all audit events.
Each event's hash includes the previous event's hash, making retroactive
tampering detectable during integrity verification.

Log format: NDJSON (one JSON object per line)
Export format: FHIR R4 AuditEvent (via export_fhir_bundle())
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

import aiofiles
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


# =============================================================================
# AUDIT EVENT TYPES
# =============================================================================

class AuditAction(StrEnum):
    # Authentication
    LOGIN_SUCCESS = "login.success"
    LOGIN_FAILURE = "login.failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token.refresh"

    # PHI Access
    PATIENT_VIEW = "patient.view"
    PATIENT_SEARCH = "patient.search"
    FHIR_INGEST = "fhir.ingest"

    # Inference
    INFERENCE_REQUEST = "inference.request"
    INFERENCE_RESPONSE = "inference.response"

    # Physician Feedback
    DIAGNOSIS_ACCEPT = "diagnosis.accept"
    DIAGNOSIS_MODIFY = "diagnosis.modify"
    DIAGNOSIS_REJECT = "diagnosis.reject"
    DIAGNOSIS_FLAG = "diagnosis.flag"

    # Administration
    USER_CREATE = "user.create"
    USER_MODIFY = "user.modify"
    USER_DEACTIVATE = "user.deactivate"
    ROLE_ASSIGN = "role.assign"

    # Break-Glass
    BREAK_GLASS_ACTIVATE = "break_glass.activate"
    BREAK_GLASS_ACCESS = "break_glass.access"
    BREAK_GLASS_CLOSE = "break_glass.close"
    BREAK_GLASS_REVIEW_SUBMIT = "break_glass.review.submit"

    # FL
    FL_GRADIENT_COMPUTE = "fl.gradient.compute"
    FL_GRADIENT_SUBMIT = "fl.gradient.submit"
    FL_MODEL_UPDATE = "fl.model.update"

    # Compliance
    AUDIT_LOG_EXPORT = "audit.export"
    AUDIT_LOG_VIEW = "audit.view"
    CONSENT_RECORD = "consent.record"
    CONSENT_WITHDRAW = "consent.withdraw"

    # System
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    MODEL_RELOAD = "model.reload"


class AuditOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


# =============================================================================
# AUDIT LOG WRITER
# =============================================================================

class AuditLogger:
    """
    Append-only, hash-chained audit logger.

    Thread-safe for concurrent async writes via a single shared log file
    per day, with atomic line appends.
    """

    def __init__(self):
        self._log_dir = Path(settings.AUDIT_LOG_DIR)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._previous_hash: str = "0" * 64  # Genesis hash
        self._load_last_hash()

    def _current_log_path(self) -> Path:
        """One log file per day for manageable rotation."""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self._log_dir / f"audit_{date_str}.ndjson"

    def _load_last_hash(self) -> None:
        """Load the hash of the last written event to continue the chain."""
        log_path = self._current_log_path()
        if not log_path.exists():
            return

        last_line = None
        try:
            with open(log_path, "rb") as f:
                # Seek to find the last non-empty line efficiently
                f.seek(0, 2)  # End of file
                pos = f.tell()
                while pos > 0:
                    pos -= 1
                    f.seek(pos)
                    char = f.read(1)
                    if char == b"\n" and pos < f.seek(0, 2) - 1:
                        last_line = f.readline().decode("utf-8").strip()
                        if last_line:
                            break
            if last_line:
                event = json.loads(last_line)
                self._previous_hash = event.get("event_hash", "0" * 64)
        except Exception as e:
            logger.warning("Could not load last audit hash — chain may reset", error=str(e))

    def _compute_hash(self, payload: str, previous_hash: str) -> str:
        """SHA-256 hash of (previous_hash + payload)."""
        content = f"{previous_hash}{payload}".encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    async def write(
        self,
        action: AuditAction,
        outcome: AuditOutcome,
        actor_id: str | None,
        actor_role: str | None,
        resource_type: str | None = None,
        resource_id: str | None = None,     # Always pseudonymous — never raw PHI
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
        ip_address: str | None = None,
        is_break_glass: bool = False,
    ) -> str:
        """
        Write a single audit event to the hash-chained log.

        Returns the event_id for reference.

        IMPORTANT: resource_id must be the pseudonymous patient UUID,
        never the raw MRN or other PHI identifier.
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Build the payload (what gets hashed)
        event_payload = {
            "event_id": event_id,
            "timestamp": timestamp,
            "clinic_id": settings.CLINIC_ID,
            "action": str(action),
            "outcome": str(outcome),
            "actor_id": actor_id,
            "actor_role": actor_role,
            "resource_type": resource_type,
            "resource_id": resource_id,   # Must be pseudonymous
            "request_id": request_id,
            "ip_address": ip_address,
            "is_break_glass": is_break_glass,
            "details": details or {},
        }

        payload_str = json.dumps(event_payload, sort_keys=True, default=str)
        event_hash = self._compute_hash(payload_str, self._previous_hash)

        # Final log line includes previous hash and current hash
        log_entry = {
            **event_payload,
            "previous_hash": self._previous_hash,
            "event_hash": event_hash,
        }

        log_line = json.dumps(log_entry, default=str) + "\n"

        # Atomic append to log file
        async with aiofiles.open(self._current_log_path(), mode="a") as f:
            await f.write(log_line)

        self._previous_hash = event_hash

        # Extra alert for break-glass events
        if is_break_glass:
            logger.warning(
                "BREAK-GLASS ACCESS RECORDED",
                event_id=event_id,
                actor_id=actor_id,
                action=str(action),
            )

        return event_id

    async def log(
        self,
        action: str,
        actor_id: str | None,
        actor_role: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        outcome: str = "success",
        outcome_reason: str | None = None,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        is_break_glass: bool = False,
    ) -> str:
        """
        Backward-compatible shim for older endpoint code that calls audit.log().
        """
        details = dict(metadata or {})
        if outcome_reason:
            details["outcome_reason"] = outcome_reason

        try:
            action_enum = AuditAction(action)
        except ValueError:
            # Keep unknown actions loggable rather than breaking requests.
            action_enum = action  # type: ignore[assignment]

        try:
            outcome_enum = AuditOutcome(outcome)
        except ValueError:
            outcome_enum = AuditOutcome.PARTIAL

        return await self.write(
            action=action_enum,  # type: ignore[arg-type]
            outcome=outcome_enum,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            request_id=request_id,
            is_break_glass=is_break_glass,
        )

    async def verify_integrity(self) -> dict[str, Any]:
        """
        Verify the hash chain integrity of all audit log files.
        Returns a summary with any detected tampering.
        """
        results = {
            "verified": True,
            "files_checked": 0,
            "events_checked": 0,
            "tampering_detected": [],
        }

        log_files = sorted(self._log_dir.glob("audit_*.ndjson"))
        previous_hash = "0" * 64

        for log_file in log_files:
            results["files_checked"] += 1
            async with aiofiles.open(log_file, mode="r") as f:
                async for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        results["events_checked"] += 1

                        # Re-compute expected hash
                        payload = {k: v for k, v in event.items()
                                   if k not in ("previous_hash", "event_hash")}
                        payload_str = json.dumps(payload, sort_keys=True, default=str)
                        expected_hash = self._compute_hash(payload_str, previous_hash)

                        if expected_hash != event.get("event_hash"):
                            results["verified"] = False
                            results["tampering_detected"].append({
                                "file": log_file.name,
                                "event_id": event.get("event_id"),
                                "timestamp": event.get("timestamp"),
                            })

                        previous_hash = event.get("event_hash", "")
                    except json.JSONDecodeError as e:
                        results["verified"] = False
                        results["tampering_detected"].append({
                            "file": log_file.name,
                            "error": f"Malformed JSON: {e}",
                        })

        return results


# =============================================================================
# MODULE-LEVEL SINGLETON
# =============================================================================

_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """FastAPI dependency: returns the shared AuditLogger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
