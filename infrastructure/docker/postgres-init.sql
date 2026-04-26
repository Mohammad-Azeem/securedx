-- =============================================================================
-- SecureDx AI — PostgreSQL Initialization
-- Runs once on first container start.
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create application schema
CREATE SCHEMA IF NOT EXISTS securedx;

-- Set default search path
ALTER DATABASE securedx SET search_path TO securedx, public;

-- =============================================================================
-- AUDIT LOG TABLE (supplement to file-based audit log)
-- =============================================================================
CREATE TABLE IF NOT EXISTS securedx.audit_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id        TEXT NOT NULL UNIQUE,
    clinic_id       TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    action          TEXT NOT NULL,
    outcome         TEXT NOT NULL,
    actor_id        TEXT,           -- User UUID (pseudonymous)
    actor_role      TEXT,
    resource_type   TEXT,
    resource_id     TEXT,           -- Always pseudonymous patient UUID
    request_id      TEXT,
    ip_address      TEXT,
    is_break_glass  BOOLEAN DEFAULT FALSE,
    details         JSONB,
    previous_hash   TEXT NOT NULL,
    event_hash      TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp   ON securedx.audit_events (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_actor        ON securedx.audit_events (actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_break_glass  ON securedx.audit_events (is_break_glass) WHERE is_break_glass = TRUE;
CREATE INDEX IF NOT EXISTS idx_audit_action       ON securedx.audit_events (action);

-- =============================================================================
-- FEEDBACK TABLE (clinician training signal store)
-- =============================================================================
CREATE TABLE IF NOT EXISTS securedx.feedback_events (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inference_id        TEXT NOT NULL,
    patient_pseudo_id   TEXT NOT NULL,      -- Pseudonymous UUID only
    physician_id_hash   TEXT NOT NULL,      -- SHA-256 of physician user_id
    decision            TEXT NOT NULL,      -- accept | modify | reject | flag
    original_icd10      TEXT,
    corrected_icd10     TEXT,               -- Set when decision = modify
    quality_rating      SMALLINT CHECK (quality_rating BETWEEN 1 AND 5),
    reason_code         TEXT,
    notes               TEXT,
    queued_for_fl       BOOLEAN DEFAULT TRUE,
    fl_submitted_at     TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_inference   ON securedx.feedback_events (inference_id);
CREATE INDEX IF NOT EXISTS idx_feedback_queued      ON securedx.feedback_events (queued_for_fl) WHERE queued_for_fl = TRUE;
CREATE INDEX IF NOT EXISTS idx_feedback_created     ON securedx.feedback_events (created_at DESC);

-- =============================================================================
-- BREAK-GLASS SESSIONS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS securedx.break_glass_sessions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id          TEXT NOT NULL UNIQUE,
    patient_pseudo_id   TEXT NOT NULL,
    activated_by        TEXT NOT NULL,      -- User UUID
    activated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ NOT NULL,
    review_deadline     TIMESTAMPTZ NOT NULL,
    reason_code         TEXT NOT NULL,
    justification       TEXT NOT NULL,
    review_submitted    BOOLEAN DEFAULT FALSE,
    review_submitted_at TIMESTAMPTZ,
    review_data         JSONB,
    closed_at           TIMESTAMPTZ,
    alert_sent          BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bg_pending_review ON securedx.break_glass_sessions (review_submitted, review_deadline)
    WHERE review_submitted = FALSE;

-- =============================================================================
-- PATIENT CONSENT TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS securedx.patient_consents (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_pseudo_id   TEXT NOT NULL,
    consent_type        TEXT NOT NULL,      -- ai_analysis | data_retention | fl_participation
    status              TEXT NOT NULL,      -- granted | withdrawn | pending
    granted_at          TIMESTAMPTZ,
    withdrawn_at        TIMESTAMPTZ,
    recorded_by         TEXT,               -- Staff user UUID
    method              TEXT,               -- paper | electronic | verbal
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_consent_unique ON securedx.patient_consents (patient_pseudo_id, consent_type);

-- =============================================================================
-- GRANT MINIMAL PERMISSIONS TO APP USER
-- =============================================================================
GRANT USAGE ON SCHEMA securedx TO securedx_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA securedx TO securedx_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA securedx TO securedx_app;

-- Audit events: INSERT only (no UPDATE/DELETE — append-only)
REVOKE UPDATE, DELETE ON securedx.audit_events FROM securedx_app;

COMMENT ON TABLE securedx.audit_events IS
    'HIPAA §164.312(b) audit control. Append-only — no updates or deletes permitted.';
COMMENT ON TABLE securedx.feedback_events IS
    'Clinician feedback training signals. PHI-free: physician_id is SHA-256 hashed.';
COMMENT ON TABLE securedx.break_glass_sessions IS
    'HIPAA §164.312(a)(2)(ii) emergency access procedure records.';
