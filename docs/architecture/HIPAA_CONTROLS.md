# HIPAA Technical Safeguards Implementation

**Standard:** 45 CFR §164.312  
**Status:** Implemented in SecureDx AI v1.0  
**Last reviewed:** See git blame

---

## §164.312(a)(1) — Access Control

| Specification | Status | Implementation |
|---------------|--------|----------------|
| Unique User Identification (R) | ✅ Required — Implemented | Keycloak OIDC, every user has a unique UUID. Shared accounts prohibited. |
| Emergency Access Procedure (A) | ✅ Addressable — Implemented | Break-Glass protocol in `services/api/app/api/v1/endpoints/break_glass.py`. Multi-channel alerts, 4-hour session, mandatory review. |
| Automatic Logoff (A) | ✅ Addressable — Implemented | JWT expiry: 60 min access token, 7-day refresh. Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`. |
| Encryption & Decryption (A) | ✅ Addressable — Implemented | AES-256-GCM via pgcrypto for data at rest. TLS 1.3 in transit. |

**R = Required, A = Addressable**

---

## §164.312(a)(2)(ii) — Emergency Access (Break-Glass)

Implemented in `services/api/app/api/v1/endpoints/break_glass.py`.

Procedure:
1. Physician activates Break-Glass with reason code + justification
2. System grants 4-hour elevated access
3. Immediate alerts: email to Admin + Compliance Officer
4. All actions tagged `[BREAK-GLASS]` in audit log
5. Mandatory post-event review required within 48 hours
6. Compliance Officer reviews all break-glass events monthly

---

## §164.312(b) — Audit Controls

Implemented in `services/api/app/core/audit.py`.

| Requirement | Implementation |
|-------------|---------------|
| Hardware/software activity recording | Tamper-evident NDJSON audit log, one file per day |
| Tamper detection | SHA-256 Merkle-tree hash chain — any modification detectable |
| Retention | 6-year minimum (2,190 days), configurable via `AUDIT_LOG_RETENTION_DAYS` |
| Export format | FHIR R4 AuditEvent bundle, digitally signed |
| Events logged | Auth, PHI access, inference, overrides, break-glass, admin, FL |

---

## §164.312(c)(1) — Integrity

| Specification | Implementation |
|---------------|---------------|
| Authenticate PHI (A) | All inference inputs/outputs hash-verified. Audit log hash chain detects tampering. Model weights verified by SHA-256 on download. |

---

## §164.312(d) — Person Authentication

All users authenticated via Keycloak OIDC with:
- JWT RS256 signature verification against Keycloak JWKS
- Clinic-ID claim validation (cross-clinic token reuse blocked)
- Role verification on every request
- 2FA configurable in Keycloak admin console (recommended for Admin and Compliance roles)

---

## §164.312(e)(1) — Transmission Security

| Specification | Implementation |
|---------------|---------------|
| Encryption in Transit (A) | TLS 1.3 enforced on all services. Certificate pinning for FL coordinator connection. Nginx terminates TLS in production. |
| Internal network isolation | `securedx-internal` Docker network is `internal: true` — no direct external access. Only Nginx is on the external network. |

---

## PHI Boundary Verification Checklist

Run before each production deployment:

- [ ] Confirm `securedx-internal` network has `internal: true` in docker-compose.yml
- [ ] Verify FL client only submits to `FL_COORDINATOR_URL`, not to any other external endpoint
- [ ] Confirm FHIR ingestion API listens on `localhost:8443` only (not `0.0.0.0`)
- [ ] Verify audit log directory is on encrypted volume (LUKS or equivalent)
- [ ] Confirm model weights downloaded from coordinator are SHA-256 verified before deployment
- [ ] Verify `PSEUDONYM_SALT` is set and patient UUIDs are not reversible to raw MRNs
- [ ] Confirm no PHI appears in application logs (search for MRN, DOB, SSN patterns in log output)

---

## Business Associate Agreements (BAA) Register

| Vendor | Service | BAA Status | BAA Expiry |
|--------|---------|------------|------------|
| Cloud Host (FL Coordinator) | FL gradient aggregation server | Required | Review annually |
| Audit Log Backup Provider | Encrypted off-site log backup | Required | Review annually |
| Error Monitoring (if Sentry) | Application error tracking | Required | Review annually |

**Note:** The FL coordinator receives only DP-protected gradients, not PHI. BAA is required as defense-in-depth.
