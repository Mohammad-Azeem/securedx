# Development Setup Guide

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker Desktop | 4.27+ | https://docker.com/products/docker-desktop |
| Docker Compose | 2.20+ | Included with Docker Desktop |
| Node.js | 20 LTS | https://nodejs.org |
| Python | 3.11+ | https://python.org |
| Make | Any | `xcode-select --install` (macOS) |

---
 Configuration Reference

This file documents the `.env` variables used by SecureDx AI.

## Required variables

- `CLINIC_ID`: Unique clinic identifier, e.g. `clinic-delhi-001`.
- `CLINIC_NAME`: Human-readable clinic name.
- `SECRET_KEY`: 64-char hex key (`openssl rand -hex 32`).
- `DB_PASSWORD`: PostgreSQL password for `securedx_app`.
- `DB_ENCRYPTION_KEY`: 64-char hex key for encryption (`openssl rand -hex 32`).
- `PSEUDONYM_SALT`: 32-char hex salt (`openssl rand -hex 16`).
- `KEYCLOAK_ADMIN_PASSWORD`: Admin password for Keycloak.

## Common development defaults

- `KEYCLOAK_SERVER_URL=http://keycloak:8080`
- `KEYCLOAK_REALM=securedx`
- `KEYCLOAK_CLIENT_ID=securedx-api`
- `INFERENCE_SERVICE_URL=http://inference:8001`
- `CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]`

## Timezone format

Use standard IANA timezone names, for example:

- `Asia/Kolkata`
- `America/New_York`
- `Europe/Berlin`

---

## First-Time Setup

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/securedx-ai.git
cd securedx-ai

# Create your local environment file
cp .env.example .env
```

Open `.env` and set the required values. Every `CHANGE_ME` placeholder must be replaced:

```bash
# Generate secure keys
SECRET_KEY=$(openssl rand -hex 32)
DB_ENCRYPTION_KEY=$(openssl rand -hex 32)
PSEUDONYM_SALT=$(openssl rand -hex 16)

# Set your clinic ID
CLINIC_ID=clinic-my-clinic-001
```

### 2. Start Services

```bash
make dev-up
```

First run downloads ~2GB of Docker images. Subsequent starts take ~20 seconds.

### 3. Initialize Database

```bash
make db-migrate   # Run Alembic migrations
make db-seed      # Create default accounts
```

### 4. Verify Everything Works

```bash
make health-check
```

Expected output:
```
✓ postgres    healthy
✓ keycloak    healthy
✓ api         healthy (v1.0.0)
✓ inference   healthy (model: stub-0.0.1)
✓ frontend    healthy
```

### 5. Open the App

| Service | URL | Credentials |
|---------|-----|-------------|
| Physician UI | http://localhost:3000 | physician@clinic.local / ChangeMe123! |
| Admin UI | http://localhost:3000/admin | admin@clinic.local / ChangeMe123! |
| API Docs | http://localhost:8000/docs | (no auth needed for Swagger) |
| Keycloak Admin | http://localhost:8080 | admin / (from KEYCLOAK_ADMIN_PASSWORD in .env) |

Service URL
Frontend http://localhost/
API Docs http://localhost/api/v1/docsKeycloak Admin http://localhost:8080/ (direct, not via nginx)
**Change the default passwords immediately after first login.**

---

## Development Workflow

### Hot Reload

All services support hot reload in dev mode:
- **API**: File changes in `services/api/app/` restart uvicorn automatically
- **Frontend**: Vite HMR reloads the browser instantly
- **Inference**: File changes in `services/inference/engine/` auto-restart

### Running Tests

```bash
make test             # All services
make test-api         # API tests only (pytest)
make test-frontend    # Frontend tests (vitest)
```

### Linting

```bash
make lint             # Run all linters
make format           # Auto-fix formatting
```

### Viewing Logs

```bash
make dev-logs          # All services
make dev-logs s=api    # API only
make dev-logs s=inference  # Inference engine
```

---

## Project Structure

```
securedx-ai/
├── services/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/v1/
│   │   │   │   ├── endpoints/  # Route handlers
│   │   │   │   └── router.py   # Route registration
│   │   │   ├── core/           # Config, DB, security, audit
│   │   │   ├── models/         # SQLAlchemy ORM models
│   │   │   ├── schemas/        # Pydantic request/response schemas
│   │   │   ├── services/       # Business logic
│   │   │   ├── repositories/   # Database access layer
│   │   │   └── middleware/     # Audit logging, request ID
│   │   ├── migrations/         # Alembic migration files
│   │   └── tests/
│   │
│   ├── frontend/               # React + TypeScript UI
│   │   └── src/
│   │       ├── components/
│   │       │   ├── physician/  # DiagnosisCard, ShapChart, FeedbackDrawer
│   │       │   ├── admin/      # System health, user management
│   │       │   ├── compliance/ # Audit log viewer, export
│   │       │   └── shared/     # AppLayout, LoadingScreen
│   │       ├── pages/          # Route-level page components
│   │       ├── hooks/          # useAuth, useInference, useFeedback
│   │       ├── api/            # Typed API client functions
│   │       └── types/          # Shared TypeScript interfaces
│   │
│   ├── inference/              # ONNX Runtime inference microservice
│   │   └── engine/model.py     # Model loader, SHAP, NLG narrative
│   │
│   └── fl-client/              # Federated learning sync worker
│       └── client/fl_client.py # Flower client, DP, Krum validator
│
├── infrastructure/
│   ├── docker/                 # PostgreSQL init SQL
│   ├── nginx/                  # Dev and prod nginx configs
│   └── keycloak/               # Keycloak realm export JSON
│
├── docs/
│   ├── architecture/           # HIPAA controls, GDPR compliance
│   ├── api/                    # API reference
│   └── setup/                  # This file and others
│
├── docker-compose.yml          # Base Compose config
├── docker-compose.dev.yml      # Dev overrides (hot reload, ports)
├── docker-compose.prod.yml     # Prod overrides (TLS, resource limits)
├── Makefile                    # Developer commands
├── .env.example                # Environment template
└── README.md                   # Project overview
```

---

## Common Issues

### `make dev-up` fails with "port already in use"

```bash
# Check what's using port 5432 (PostgreSQL)
lsof -i :5432
# Stop local PostgreSQL if running
brew services stop postgresql
```

### Keycloak takes too long to start

Keycloak can take 60-90 seconds on first boot as it imports the realm configuration. This is normal. Run `make dev-logs s=keycloak` to watch progress.

### "CHANGE_ME" error when running make dev-up

Edit your `.env` file and replace all `CHANGE_ME` values with real secrets. See step 1 of First-Time Setup above.

### Frontend can't reach the API

Ensure the API is healthy: `make dev-logs s=api`. Check CORS_ORIGINS in `.env` includes `http://localhost:3000`.
