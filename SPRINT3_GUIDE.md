# SecureDx AI — Sprint 3 Deployment Guide

## What's New in Sprint 3

✅ **Database Models** - SQLAlchemy ORM for patients, feedback, audit, break-glass  
✅ **Alembic Migrations** - Version-controlled schema with rollback support  
✅ **Repository Pattern** - Clean data access layer  
✅ **Real Patient API** - Endpoint now returns actual data from PostgreSQL  
✅ **Seed Script** - 20 realistic test patients  
✅ **Type Safety** - Pydantic schemas for all API boundaries  

---

## Installation Steps

### 1. Copy Sprint 3 Files to Your Project

```bash
cd securedx

# Database models
mkdir -p services/api/app/models
cp models/__init__.py services/api/app/models/
cp models/patient.py services/api/app/models/
cp models/feedback.py services/api/app/models/
cp models/audit_event.py services/api/app/models/
cp models/break_glass.py services/api/app/models/

# Alembic migration
mkdir -p services/api/alembic/versions
cp alembic/versions/001_initial_schema.py services/api/alembic/versions/

# Seed script
mkdir -p services/api/app/scripts
cp scripts/seed_db.py services/api/app/scripts/

# Repositories
mkdir -p services/api/app/repositories
cp repositories/patient.py services/api/app/repositories/
touch services/api/app/repositories/__init__.py

# Schemas
mkdir -p services/api/app/schemas
cp schemas/patient.py services/api/app/schemas/
touch services/api/app/schemas/__init__.py

# API endpoint (replace existing stub)
cp api/patients_endpoint.py services/api/app/api/v1/endpoints/patients.py
```

### 2. Install Additional Dependencies

```bash
# Add to services/api/requirements.txt if not already present:
cat >> services/api/requirements.txt << 'EOF'
faker==22.6.0  # For seed script
EOF

# Rebuild API container
docker compose down
docker compose -f docker-compose.yml -f docker-compose.dev.yml build api
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 3. Run Database Migrations

```bash
# Apply the new schema
make db-migrate

# Or manually:
docker compose exec api alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema, Initial schema migration
```

### 4. Seed the Database

```bash
# Populate test patients
make db-seed

# Or manually:
docker compose exec api python -m app.scripts.seed_db
```

**Expected output:**
```
🌱 Seeding SecureDx database...

✓ Seeded 20 patients:
  - Patient A001: 7y male, Status: active
  - Patient A002: 45y female, Status: active
  - Patient A003: 72y male, Status: active
  - Patient A004: 23y other, Status: active
  - Patient A005: 89y female, Status: inactive
  ... and 15 more

✓ Created genesis audit event: a3f8b9e2c4d1f5a7...

✅ Database seeding complete!
```

### 5. Verify Installation

```bash
# Test patient API endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost/api/v1/patients

# Or use the health check
make health-check
```

**Expected response:**
```json
[
  {
    "pseudo_id": "123e4567-e89b-12d3-a456-426614174000",
    "display_name": "Patient A001",
    "age_years": 45,
    "sex": "female",
    "last_visit_date": "2026-02-15T10:30:00Z",
    "status": "active"
  },
  ...
]
```

---

## Architecture Deep-Dive

### For a 15-Year-Old

**The Patient Journey:**

1. **Doctor opens app** → Frontend loads
2. **Clicks "View Patients"** → API request sent
3. **API checks security badge** → "Is this person a doctor?"
4. **Repository asks database** → "Show me active patients"
5. **Database returns rows** → But encrypted names stay encrypted!
6. **API converts to safe format** → Only pseudo IDs and age
7. **Frontend shows list** → Doctor sees "Patient A001, 45y female"

**Why so many layers?**

Imagine mailing a letter:
- **Frontend** = You writing the letter
- **API** = Post office (checks address is valid)
- **Repository** = Sorting facility (knows where to find the mailbox)
- **Database** = Mailbox (stores the actual letter)

Each layer has ONE job. If you want to change how letters are sorted, you only fix the sorting facility — you don't need to rebuild the entire post office!

---

### For an Interviewer

**Layered Architecture Rationale:**

```
┌─────────────────────────────────────────┐
│  Frontend (React + TypeScript)          │  ← Presentation layer
└──────────────┬──────────────────────────┘
               │ HTTP + JWT
┌──────────────▼──────────────────────────┐
│  API Layer (FastAPI)                    │  ← Request validation, auth
│  - Pydantic schemas (DTOs)              │
│  - Dependency injection                 │
│  - RBAC enforcement                     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Business Logic (Services/Repositories) │  ← Domain logic
│  - Repository pattern                   │
│  - Audit logging                        │
│  - Encryption/decryption                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Data Access (SQLAlchemy ORM)           │  ← Persistence
│  - Async PostgreSQL                     │
│  - Connection pooling                   │
│  - Transaction management               │
└─────────────────────────────────────────┘
```

**Benefits:**
1. **Testability:** Mock repositories without touching database
2. **Maintainability:** Change data access without touching business logic
3. **Type safety:** Pydantic validation at API boundary, SQLAlchemy at DB boundary
4. **Performance:** Async all the way through (no blocking I/O)

**Repository Pattern Example:**

```python
# WITHOUT repository (business logic mixed with data access)
@router.get("/patients")
async def list_patients(session: AsyncSession):
    result = await session.execute(
        select(Patient).where(Patient.status == 'active').limit(100)
    )
    patients = result.scalars().all()
    # Business logic mixed in here...
    return patients

# WITH repository (clean separation)
@router.get("/patients")
async def list_patients(session: AsyncSession):
    repo = PatientRepository(session)
    patients = await repo.list(status='active', limit=100)
    # Business logic stays clean
    return patients
```

**Advantages:**
- Testing: `mock_repo.list.return_value = [fake_patient]`
- Optimization: Change query strategy in one place
- Refactoring: Swap PostgreSQL for MongoDB without touching endpoints

---

## Database Schema

```sql
-- Patients (de-identified)
CREATE TABLE patients (
    pseudo_id UUID PRIMARY KEY,
    encrypted_mrn TEXT,           -- AES-256 encrypted
    encrypted_name TEXT,          -- AES-256 encrypted
    encrypted_ssn TEXT,           -- AES-256 encrypted
    display_name VARCHAR(100),    -- "Patient A001" (safe)
    age_years INTEGER,            -- Derived (safe for analytics)
    sex VARCHAR(20),              -- Derived (safe)
    last_visit_date TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ
);

-- Feedback (for federated learning)
CREATE TABLE feedback_events (
    id UUID PRIMARY KEY,
    patient_pseudo_id UUID REFERENCES patients(pseudo_id),
    physician_id_hash VARCHAR(64),  -- SHA-256(physician_id)
    decision VARCHAR(20),           -- accept/modify/reject/flag
    modified_diagnosis_code VARCHAR(50),
    original_suggestions JSON,      -- AI's suggestion
    feature_vector JSON,            -- De-identified features
    submitted_at TIMESTAMPTZ DEFAULT now(),
    queued_for_fl BOOLEAN DEFAULT true
);

-- Audit (tamper-evident)
CREATE TABLE audit_events (
    id UUID PRIMARY KEY,
    event_hash VARCHAR(64) UNIQUE,    -- SHA-256(previous_hash + payload)
    previous_hash VARCHAR(64),        -- Links to prior event
    action VARCHAR(100),              -- e.g., "patient_view"
    actor_id_hash VARCHAR(64),        -- SHA-256(user_id)
    outcome VARCHAR(20),              -- success/failure
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Revoke modification rights (append-only enforcement)
REVOKE UPDATE, DELETE ON audit_events FROM securedx_app;
```

---

## Security Considerations

### Encryption Strategy

**Column-level encryption** (not full-disk):
```python
# Application-layer encryption using pgcrypto
encrypted_name = pgp_sym_encrypt('John Doe', encryption_key)

# Only decrypt when absolutely necessary
decrypted = pgp_sym_decrypt(encrypted_name, encryption_key)
```

**Why column-level?**
- Granular access control (can query age without decrypting name)
- Performance (only decrypt what you need)
- Audit trail (know exactly which fields were accessed)

### Pseudonymization

**Consistent within clinic, random across clinics:**
```python
pseudo_id = uuid5(CLINIC_NAMESPACE, real_mrn)
```

This allows:
- ✅ Longitudinal analysis within clinic (same patient = same ID)
- ✅ Privacy across clinics (can't correlate patients between sites)
- ✅ De-identification (satisfies HIPAA Safe Harbor method)

### Audit Integrity

**Hash chain prevents tampering:**
```python
event_n_hash = SHA256(event_n-1_hash + event_n_payload)
```

**Attack scenarios mitigated:**
- ❌ Delete event #5 → Chain breaks at event #6
- ❌ Modify event #5 → Hash mismatch detected
- ❌ Insert fake event → Can't compute valid previous_hash

---

## Testing the API

### Using curl:

```bash
# Get auth token
TOKEN=$(curl -X POST http://localhost/auth/realms/securedx/protocol/openid-connect/token \
  -d "grant_type=password" \
  -d "client_id=securedx-frontend" \
  -d "username=physician@clinic.local" \
  -d "password=ChangeMe123!" \
  | jq -r '.access_token')

# List patients
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost/api/v1/patients

# Get specific patient
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost/api/v1/patients/123e4567-e89b-12d3-a456-426614174000
```

### Using Python:

```python
import requests

# Login
response = requests.post(
    "http://localhost/auth/realms/securedx/protocol/openid-connect/token",
    data={
        "grant_type": "password",
        "client_id": "securedx-frontend",
        "username": "physician@clinic.local",
        "password": "ChangeMe123!",
    }
)
token = response.json()["access_token"]

# List patients
headers = {"Authorization": f"Bearer {token}"}
patients = requests.get("http://localhost/api/v1/patients", headers=headers).json()

for p in patients:
    print(f"{p['display_name']}: {p['age_years']}y {p['sex']}")
```

---

## Next Steps

**Sprint 4: Complete Inference Workflow**
- Wire up real ONNX model
- SHAP visualization component
- Feedback submission flow
- Real-time confidence scores

**Sprint 5: Federated Learning**
- FL client picks up feedback from queue
- Differential privacy engine integration
- Krum aggregation
- Gradient submission to coordinator

**Sprint 6: Admin Dashboard**
- User management CRUD
- System health monitoring
- Break-glass session reviewer
- Audit log viewer with filtering

---

## Troubleshooting

**Migration fails with "relation already exists":**
```bash
# Reset migrations (DEV ONLY - destroys data)
docker compose exec postgres psql -U securedx_app -d securedx -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
make db-migrate
make db-seed
```

**Seed script says "already seeded":**
```bash
# Clear patients table
docker compose exec postgres psql -U securedx_app -d securedx -c "TRUNCATE patients CASCADE;"
make db-seed
```

**API returns 401 Unauthorized:**
- Check Keycloak is running: `docker compose ps keycloak`
- Verify token hasn't expired (60-minute lifespan)
- Ensure user has correct role (physician or admin)

**Frontend shows empty patient list:**
- Check API logs: `docker logs securedx-api --tail 50`
- Verify database has patients: `docker compose exec postgres psql -U securedx_app -d securedx -c "SELECT count(*) FROM patients;"`
- Test API directly: `curl -H "Authorization: Bearer TOKEN" http://localhost/api/v1/patients`

---

## Congratulations! 🎉

You now have:
- ✅ A working database with realistic test data
- ✅ Type-safe API endpoints with validation
- ✅ Tamper-evident audit logging
- ✅ Encrypted patient data at rest
- ✅ Repository pattern for clean architecture

**Next: Let's wire up the AI inference engine and make diagnoses!**
