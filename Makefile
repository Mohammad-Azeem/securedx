# =============================================================================
# SecureDx AI — Developer Makefile
# =============================================================================
# Usage: make <target>
# Run `make help` to see all available commands.
# =============================================================================

.PHONY: help dev-up dev-down dev-logs dev-rebuild \
        prod-up prod-down prod-logs \
        test test-api test-frontend test-fl test-inference \
        lint lint-api lint-frontend format \
        db-migrate db-rollback db-seed db-reset db-shell \
        api-shell fl-shell inference-shell \
        health-check audit-verify \
        docs-serve clean

# Detect OS for open command
UNAME := $(shell uname)

# Docker Compose files
DC_DEV  = docker compose -f docker-compose.yml -f docker-compose.dev.yml
DC_PROD = docker compose -f docker-compose.yml -f docker-compose.prod.yml

# Colors
CYAN  = \033[0;36m
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED   = \033[0;31m
NC    = \033[0m

# Default service filter (used with `make dev-logs s=api`)
s ?=

# =============================================================================
# HELP
# =============================================================================
help: ## Show this help message
	@echo ""
	@echo "$(CYAN)SecureDx AI — Available Commands$(NC)"
	@echo "================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-22s$(NC) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# DEVELOPMENT
# =============================================================================
dev-up: check-env ## Start all services in development mode (hot reload)
	@echo "$(CYAN)Starting SecureDx AI in development mode...$(NC)"
	$(DC_DEV) up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "  UI:        http://localhost:3000"
	@echo "  API:       http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  Keycloak:  http://localhost:8080"
	@echo ""
	@echo "Run $(CYAN)make dev-logs$(NC) to tail all logs"

dev-down: ## Stop all development services
	@echo "$(YELLOW)Stopping services...$(NC)"
	$(DC_DEV) down
	@echo "$(GREEN)✓ Stopped$(NC)"

dev-restart: ## Restart all services
	$(DC_DEV) restart

dev-rebuild: ## Rebuild and restart all services (use after dependency changes)
	@echo "$(CYAN)Rebuilding all services...$(NC)"
	$(DC_DEV) build --no-cache
	$(DC_DEV) up -d
	@echo "$(GREEN)✓ Rebuilt and started$(NC)"

dev-logs: ## Tail service logs (use s=api to filter: make dev-logs s=api)
	@if [ -n "$(s)" ]; then \
		$(DC_DEV) logs -f $(s); \
	else \
		$(DC_DEV) logs -f; \
	fi

# =============================================================================
# PRODUCTION
# =============================================================================
prod-up: check-env check-tls ## Start all services in production mode
	@echo "$(CYAN)Starting SecureDx AI in production mode...$(NC)"
	$(DC_PROD) up -d
	@echo "$(GREEN)✓ Production services started$(NC)"

prod-down: ## Stop production services
	$(DC_PROD) down

prod-logs: ## Tail production logs
	$(DC_PROD) logs -f $(s)

# =============================================================================
# DATABASE
# =============================================================================
db-migrate: ## Run pending database migrations
	@echo "$(CYAN)Running database migrations...$(NC)"
	$(DC_DEV) exec api alembic upgrade head
	@echo "$(GREEN)✓ Migrations complete$(NC)"

db-rollback: ## Rollback last database migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	$(DC_DEV) exec api alembic downgrade -1

db-seed: ## Seed database with default admin accounts and initial data
	@echo "$(CYAN)Seeding database...$(NC)"
	$(DC_DEV) exec api alembic upgrade head
	$(DC_DEV) exec api python -m app.scripts.seed_db
	@echo "$(GREEN)✓ Database seeded$(NC)"
	@echo "  Admin:     admin@clinic.local / ChangeMe123!"
	@echo "  Physician: physician@clinic.local / ChangeMe123!"
	@echo "$(RED)  ⚠ Change these passwords immediately!$(NC)"

db-reset: ## DANGER: Drop and recreate database (dev only)
	@echo "$(RED)WARNING: This will destroy all data!$(NC)"
	@read -p "Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ]
	$(DC_DEV) exec api alembic downgrade base
	$(DC_DEV) exec api alembic upgrade head
	$(MAKE) db-seed

db-shell: ## Open interactive PostgreSQL shell
	$(DC_DEV) exec postgres psql -U securedx_app -d securedx

# =============================================================================
# SERVICE SHELLS
# =============================================================================
api-shell: ## Open shell in API container
	$(DC_DEV) exec api /bin/bash

fl-shell: ## Open shell in FL client container
	$(DC_DEV) exec fl-client /bin/bash

inference-shell: ## Open shell in inference container
	$(DC_DEV) exec inference /bin/bash

# =============================================================================
# TESTING
# =============================================================================
test: ## Run all tests
	@echo "$(CYAN)Running all tests...$(NC)"
	$(MAKE) test-api
	$(MAKE) test-frontend
	$(MAKE) test-fl
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-api: ## Run API tests
	@echo "$(CYAN)Running API tests...$(NC)"
	$(DC_DEV) exec api pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=80

test-frontend: ## Run frontend tests
	@echo "$(CYAN)Running frontend tests...$(NC)"
	$(DC_DEV) exec frontend npm test -- --watchAll=false --coverage

test-fl: ## Run FL client tests
	@echo "$(CYAN)Running FL client tests...$(NC)"
	$(DC_DEV) exec fl-client pytest tests/ -v

test-inference: ## Run inference engine tests
	@echo "$(CYAN)Running inference tests...$(NC)"
	$(DC_DEV) exec inference pytest tests/ -v

test-watch: ## Run API tests in watch mode
	$(DC_DEV) exec api ptw tests/ -- -v

# =============================================================================
# LINTING & FORMATTING
# =============================================================================
lint: lint-api lint-frontend ## Run all linters

lint-api: ## Lint Python code (ruff + mypy)
	@echo "$(CYAN)Linting API (ruff + mypy)...$(NC)"
	$(DC_DEV) exec api ruff check app/ tests/
	$(DC_DEV) exec api mypy app/ --ignore-missing-imports

lint-frontend: ## Lint TypeScript/React code (ESLint)
	@echo "$(CYAN)Linting frontend (ESLint)...$(NC)"
	$(DC_DEV) exec frontend npm run lint

format: ## Auto-format all code
	@echo "$(CYAN)Formatting code...$(NC)"
	$(DC_DEV) exec api ruff format app/ tests/
	$(DC_DEV) exec api ruff check --fix app/ tests/
	$(DC_DEV) exec frontend npm run format
	@echo "$(GREEN)✓ Code formatted$(NC)"

# =============================================================================
# HEALTH & COMPLIANCE
# =============================================================================
health-check: ## Check health of all services
	@echo "$(CYAN)Checking service health...$(NC)"
	@$(DC_DEV) exec api python -m app.scripts.health_check

audit-verify: ## Verify audit log integrity (hash chain check)
	@echo "$(CYAN)Verifying audit log integrity...$(NC)"
	$(DC_DEV) exec api python -m app.scripts.verify_audit_log
	@echo "$(GREEN)✓ Audit log integrity verified$(NC)"

audit-export: ## Export audit log as FHIR AuditEvent bundle
	@echo "$(CYAN)Exporting audit log...$(NC)"
	$(DC_DEV) exec api python -m app.scripts.export_audit_log
	@echo "$(GREEN)✓ Exported to ./exports/audit_$(shell date +%Y%m%d).json$(NC)"

# =============================================================================
# DOCS
# =============================================================================
docs-serve: ## Serve documentation locally
	@echo "$(CYAN)Serving docs at http://localhost:8888$(NC)"
	cd docs && python3 -m http.server 8888

# =============================================================================
# SETUP CHECKS
# =============================================================================
check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)ERROR: .env file not found$(NC)"; \
		echo "Run: cp .env.example .env && edit .env"; \
		exit 1; \
	fi
	@if grep -q "CHANGE_ME" .env; then \
		echo "$(RED)ERROR: .env contains CHANGE_ME placeholders$(NC)"; \
		echo "Edit .env and replace all CHANGE_ME values"; \
		exit 1; \
	fi

check-tls:
	@if [ ! -f infrastructure/nginx/certs/clinic.crt ]; then \
		echo "$(RED)ERROR: TLS certificate not found$(NC)"; \
		echo "Place your TLS cert at: infrastructure/nginx/certs/clinic.crt"; \
		echo "And private key at: infrastructure/nginx/certs/clinic.key"; \
		exit 1; \
	fi

# =============================================================================
# CLEANUP
# =============================================================================
clean: ## Remove build artifacts and Docker volumes (PRESERVES data volumes)
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -prune 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-all: ## DANGER: Remove everything including Docker volumes (destroys data)
	@echo "$(RED)WARNING: This will destroy ALL data including the database!$(NC)"
	@read -p "Type 'destroy' to confirm: " confirm && [ "$$confirm" = "destroy" ]
	$(DC_DEV) down -v --remove-orphans
	$(MAKE) clean
	@echo "$(YELLOW)All data destroyed$(NC)"
