"""
SecureDx AI — Audit Log Integrity Tests

HIPAA §164.312(b): Audit log tamper detection must work correctly.
"""

import json
import tempfile
from pathlib import Path

import pytest

from app.core.audit import AuditLogger, AuditAction, AuditOutcome


@pytest.fixture
def temp_audit_logger(tmp_path, monkeypatch):
    """AuditLogger with a temporary directory for testing."""
    monkeypatch.setenv("AUDIT_LOG_DIR", str(tmp_path))
    from app.core import audit
    monkeypatch.setattr(audit.settings, "AUDIT_LOG_DIR", str(tmp_path))
    monkeypatch.setattr(audit.settings, "CLINIC_ID", "test-clinic-001")
    return AuditLogger.__new__(AuditLogger), tmp_path


@pytest.mark.asyncio
async def test_audit_log_creates_file(tmp_path, monkeypatch):
    """Audit log file must be created on first write."""
    monkeypatch.setattr("app.core.audit.settings.AUDIT_LOG_DIR", str(tmp_path))
    monkeypatch.setattr("app.core.audit.settings.CLINIC_ID", "test-clinic")

    logger = AuditLogger.__new__(AuditLogger)
    logger._log_dir = tmp_path
    logger._previous_hash = "0" * 64

    await logger.write(
        action=AuditAction.LOGIN_SUCCESS,
        outcome=AuditOutcome.SUCCESS,
        actor_id="user-uuid-123",
        actor_role="physician",
    )

    log_files = list(tmp_path.glob("audit_*.ndjson"))
    assert len(log_files) == 1, "Audit log file should be created"


@pytest.mark.asyncio
async def test_audit_log_hash_chain(tmp_path, monkeypatch):
    """Each audit event's hash must incorporate the previous event's hash."""
    monkeypatch.setattr("app.core.audit.settings.AUDIT_LOG_DIR", str(tmp_path))
    monkeypatch.setattr("app.core.audit.settings.CLINIC_ID", "test-clinic")

    logger = AuditLogger.__new__(AuditLogger)
    logger._log_dir = tmp_path
    logger._previous_hash = "0" * 64

    # Write 3 events
    for i in range(3):
        await logger.write(
            action=AuditAction.PATIENT_VIEW,
            outcome=AuditOutcome.SUCCESS,
            actor_id=f"user-{i}",
            actor_role="physician",
            resource_id=f"patient-pseudo-{i}",
        )

    # Parse the log file
    log_file = list(tmp_path.glob("audit_*.ndjson"))[0]
    events = [json.loads(line) for line in log_file.read_text().strip().split("\n")]

    assert len(events) == 3

    # Verify hash chain
    assert events[0]["previous_hash"] == "0" * 64, "First event should chain to genesis hash"
    assert events[1]["previous_hash"] == events[0]["event_hash"], "Chain broken between events 0 and 1"
    assert events[2]["previous_hash"] == events[1]["event_hash"], "Chain broken between events 1 and 2"


@pytest.mark.asyncio
async def test_audit_tampering_detected(tmp_path, monkeypatch):
    """Modifying an audit log entry must be detected during integrity verification."""
    monkeypatch.setattr("app.core.audit.settings.AUDIT_LOG_DIR", str(tmp_path))
    monkeypatch.setattr("app.core.audit.settings.CLINIC_ID", "test-clinic")

    logger = AuditLogger.__new__(AuditLogger)
    logger._log_dir = tmp_path
    logger._previous_hash = "0" * 64

    await logger.write(
        action=AuditAction.LOGIN_SUCCESS,
        outcome=AuditOutcome.SUCCESS,
        actor_id="user-123",
        actor_role="admin",
    )

    # Tamper with the log file (simulate malicious modification)
    log_file = list(tmp_path.glob("audit_*.ndjson"))[0]
    content = log_file.read_text()
    tampered = content.replace("admin", "physician")  # Change role in log
    log_file.write_text(tampered)

    # Verify integrity — tampering must be detected
    result = await logger.verify_integrity()

    assert result["verified"] is False, "Tampering was NOT detected — HIPAA audit control failed!"
    assert len(result["tampering_detected"]) > 0


@pytest.mark.asyncio
async def test_phi_not_in_audit_log(tmp_path, monkeypatch):
    """Raw PHI identifiers must never appear in audit log entries."""
    monkeypatch.setattr("app.core.audit.settings.AUDIT_LOG_DIR", str(tmp_path))
    monkeypatch.setattr("app.core.audit.settings.CLINIC_ID", "test-clinic")

    logger = AuditLogger.__new__(AuditLogger)
    logger._log_dir = tmp_path
    logger._previous_hash = "0" * 64

    raw_phi_examples = ["John Smith", "MRN-12345", "1965-03-12", "SSN-123-45-6789"]

    await logger.write(
        action=AuditAction.PATIENT_VIEW,
        outcome=AuditOutcome.SUCCESS,
        actor_id="user-123",
        actor_role="physician",
        resource_id="550e8400-e29b-41d4-a716-446655440000",  # UUID only
        details={"note": "test event"},
    )

    log_file = list(tmp_path.glob("audit_*.ndjson"))[0]
    log_content = log_file.read_text()

    for phi in raw_phi_examples:
        assert phi not in log_content, f"PHI '{phi}' found in audit log!"
