# SecureDx Critical Fixes

## Root Cause
API container can't reach postgres - missing network configuration in docker-compose.dev.yml

## Files to Update

### 1. docker-compose.dev.yml
Add networks to ALL services:

```yaml
services:
  postgres:
    ports:
      - "5432:5432"
    networks:                    # ADD THIS
      - securedx-internal

  keycloak:
    ports:
      - "8080:8080"
    networks:                    # ADD THIS
      - securedx-internal

  api:
    build:
      context: ./services/api
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./services/api:/app:cached
      - audit_logs:/var/log/securedx/audit
    environment:
      ENVIRONMENT: development
      LOG_LEVEL: DEBUG
      RELOAD: "true"
    networks:                    # ADD THIS
      - securedx-internal

  inference:
    build:
      context: ./services/inference
      dockerfile: Dockerfile.dev
    ports:
      - "8001:8001"
    volumes:
      - ./services/inference:/app:cached
      - model_weights:/models
    environment:
      ENVIRONMENT: development
      LOG_LEVEL: DEBUG
    networks:                    # ADD THIS
      - securedx-internal

  frontend:
    build:
      context: ./services/frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./services/frontend/src:/app/src:cached
      - ./services/frontend/public:/app/public:cached
      - /app/node_modules
    environment:
      VITE_API_BASE_URL: http://localhost:8000/api/v1
      VITE_KEYCLOAK_URL: http://localhost:8080
      VITE_KEYCLOAK_REALM: securedx
      VITE_KEYCLOAK_CLIENT_ID: securedx-frontend
      VITE_FL_ENABLED: "true"
    networks:                    # ADD THIS
      - securedx-internal

  fl-client:
    build:
      context: ./services/fl-client
      dockerfile: Dockerfile.dev
    volumes:
      - ./services/fl-client:/app:cached
      - model_weights:/models
      - fl_queue:/var/securedx/fl-queue
    environment:
      ENVIRONMENT: development
      LOG_LEVEL: DEBUG
      FL_ENABLED: "false"
    networks:                    # ADD THIS
      - securedx-internal

  nginx:
    ports:
      - "80:80"
    volumes:
      - ./infrastructure/nginx/nginx.dev.conf:/etc/nginx/nginx.conf:ro
    networks:                    # ADD THIS
      - securedx-internal
      - securedx-external
```

### 2. Your .env file
Confirm CORS_ORIGINS has quotes:
```
CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
```

## Commands to Run

```bash
# 1. Stop everything
docker compose down

# 2. Rebuild (should be fast, images cached)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 3. Check API logs
docker logs securedx-api

# 4. Should see: "Database connection pool initialized"
```

## Expected Result
API will connect to postgres successfully and start properly.
