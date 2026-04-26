# =============================================================================
# SecureDx API — Production Dockerfile
# Multi-stage build: keeps final image lean and free of build tools
# =============================================================================

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim AS production

# Security: run as non-root user
RUN groupadd -r securedx && useradd -r -g securedx -d /app -s /sbin/nologin securedx

# Install runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment for venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Copy application code
COPY --chown=securedx:securedx app/ ./app/
COPY --chown=securedx:securedx migrations/ ./migrations/
COPY --chown=securedx:securedx alembic.ini .

# Create audit log directory with correct permissions
RUN mkdir -p /var/log/securedx/audit && \
    chown -R securedx:securedx /var/log/securedx

USER securedx

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fs http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--no-access-log"]
