# securedx



# 🔒 SecureDx AI

> **Privacy-First Clinical Decision Support for Small-to-Medium Healthcare Clinics**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![HIPAA Compliant Architecture](https://img.shields.io/badge/HIPAA-Compliant%20Architecture-green.svg)]()
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)]()
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)]()
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)]()

SecureDx AI is an on-device, federated learning diagnostic assistant that delivers AI-powered clinical decision support without ever exposing raw Protected Health Information (PHI) outside the clinic's local network.

---

## ⚡ Quick Start (5 minutes)

```bash
# 1. Clone and enter the project
git clone https://github.com/your-org/securedx-ai.git
cd securedx-ai

# 2. Copy and configure environment variables
cp .env.example .env
# Edit .env — minimum required: CLINIC_ID, SECRET_KEY, DB_PASSWORD

# 3. Start all services
make dev-up

# 4. Open the physician UI
open http://localhost:3000

# Default credentials (change immediately):
# Admin:     admin@clinic.local / ChangeMe123!
# Physician: physician@clinic.local / ChangeMe123!
```

---

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Services](#services)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Security & Compliance](#security--compliance)
- [Contributing](#contributing)
- [License](#license)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLINIC LOCAL NETWORK (PHI BOUNDARY)             │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   React UI   │───▶│  FastAPI     │───▶│  ONNX Inference      │  │
│  │  (Port 3000) │    │  (Port 8000) │    │  Engine              │  │
│  └──────────────┘    └──────┬───────┘    └──────────────────────┘  │
│                             │                                        │
│                    ┌────────▼────────┐    ┌──────────────────────┐  │
│                    │  PostgreSQL 16  │    │  Keycloak (RBAC)     │  │
│                    │  + pgcrypto    │    │  (Port 8080)         │  │
│                    └─────────────────┘    └──────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Federated Learning Client                                    │  │
│  │  • DP gradient computation (OpenDP, ε=1.0)                   │  │
│  │  • Krum BFT aggregation guard                                 │  │
│  │  • Offline queue + retry                                      │  │
│  └──────────────────────┬───────────────────────────────────────┘  │
└─────────────────────────┼───────────────────────────────────────────┘
                          │  ONLY DP-PROTECTED GRADIENTS (no PHI)
                          ▼
              ┌───────────────────────┐
              │  Flower FL Coordinator │  ← Optional private cloud
              │  (your-server.com)    │
              └───────────────────────┘
```

**Key privacy guarantee:** Raw PHI never crosses the clinic boundary. Only ε-differentially private gradient updates leave the device.

---

## Services

| Service | Port | Description |
|---------|------|-------------|
| `api` | 8000 | FastAPI backend — FHIR ingestion, inference orchestration, audit logging |
| `frontend` | 3000 | React + TypeScript physician/admin/compliance UI |
| `inference` | 8001 | ONNX Runtime inference microservice |
| `fl-client` | — | Background Flower FL client (no HTTP port, async worker) |
| `postgres` | 5432 | PostgreSQL 16 + pgcrypto (encrypted at rest) |
| `keycloak` | 8080 | Keycloak 23 RBAC / OIDC identity provider |
| `nginx` | 443 | TLS termination + reverse proxy |

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Docker | 24.0+ | With BuildKit enabled |
| Docker Compose | 2.20+ | Plugin style (`docker compose`) |
| Make | Any | For convenience commands |
| Git | 2.40+ | |
| **Hardware (production)** | | |
| RAM | 16GB+ | 32GB recommended |
| Storage | 256GB+ NVMe | Encrypted (LUKS) |
| GPU | NVIDIA (optional) | CUDA 12+ for GPU inference |

> **No cloud account required.** Everything runs locally.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/securedx-ai.git
cd securedx-ai
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your clinic's values. At minimum, set:

```env
CLINIC_ID=your-unique-clinic-id       # e.g., clinic-boston-001
SECRET_KEY=<64-char random string>     # generate: openssl rand -hex 32
DB_PASSWORD=<strong password>
KEYCLOAK_ADMIN_PASSWORD=<strong password>
```

See [docs/setup/CONFIGURATION.md](docs/setup/CONFIGURATION.md) for all options.

### 3. Start Development Environment

```bash
make dev-up
```

This starts all services with hot-reload enabled. First run downloads Docker images (~3GB).

### 4. Initialize the Database

```bash
make db-migrate
make db-seed      # Creates default admin account
```

### 5. Verify Health

```bash
make health-check
# All services should show: ✓ healthy
```

---

## Development

```bash
make dev-up          # Start all services (hot reload)
make dev-down        # Stop all services
make dev-logs        # Tail all service logs
make dev-logs s=api  # Tail specific service logs

make api-shell       # Open shell in API container
make db-shell        # Open psql shell

make test            # Run all tests
make test-api        # Run API tests only
make test-frontend   # Run frontend tests only
make lint            # Run all linters
make format          # Auto-format all code
```

See [docs/setup/DEVELOPMENT.md](docs/setup/DEVELOPMENT.md) for full development guide.

---

## Security & Compliance

- **HIPAA:** Technical safeguards implemented per §164.312. See [docs/architecture/HIPAA_CONTROLS.md](docs/architecture/HIPAA_CONTROLS.md)
- **GDPR:** Data minimization, consent flow, erasure pipeline. See [docs/architecture/GDPR_COMPLIANCE.md](docs/architecture/GDPR_COMPLIANCE.md)
- **Audit Logs:** Tamper-evident, hash-chained, FHIR AuditEvent exportable
- **Encryption:** AES-256-GCM at rest, TLS 1.3 in transit, DP on gradients
- **PHI Boundary:** Raw PHI never leaves `CLINIC LOCAL NETWORK` zone

To report a security vulnerability, see [SECURITY.md](SECURITY.md).

---

## License

AGPL-3.0 — see [LICENSE](LICENSE). Commercial licenses available for closed-source clinic deployments.
