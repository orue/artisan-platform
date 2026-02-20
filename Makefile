# ============================================================================
# Artisan Platform — Makefile
# ============================================================================
# Usage: make <target>
# Run `make help` to see all available targets.
# ============================================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash

# ── Variables ──────────────────────────────────────────────────────────────

PROJECT_NAME   := artisan-platform
PYTHON_VERSION := 3.13
SERVICES       := auth-service gallery-service order-service notification-service ai-service

# ── Help ───────────────────────────────────────────────────────────────────

.PHONY: help
help: ## Show this help message
	@echo ""
	@echo "  $(PROJECT_NAME) — Development Commands"
	@echo "  ────────────────────────────────────────"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Setup ──────────────────────────────────────────────────────────────────

.PHONY: init
init: ## First-time project setup (install hooks, shared lib)
	@echo "→ Installing pre-commit hooks..."
	pre-commit install
	@echo "→ Installing shared library in development mode..."
	cd shared/python-common && uv venv && uv pip install -e ".[dev]"
	@echo "→ Setup complete!"

.PHONY: install
install: ## Install dependencies for a service (usage: make install service=gallery-service)
	@if [ -z "$(service)" ]; then \
		echo "Error: specify a service. Usage: make install service=gallery-service"; \
		exit 1; \
	fi
	cd services/$(service) && uv venv && \
		uv pip install -e ".[dev]" && \
		uv pip install -e ../../shared/python-common
	@echo "→ $(service) dependencies installed"

.PHONY: install-all
install-all: ## Install dependencies for all services
	@for svc in $(SERVICES); do \
		echo "→ Installing $$svc..."; \
		$(MAKE) install service=$$svc; \
	done

# ── Development ────────────────────────────────────────────────────────────

.PHONY: dev
dev: ## Run a service locally with hot reload (usage: make dev service=gallery-service port=8001)
	@if [ -z "$(service)" ]; then \
		echo "Error: specify a service. Usage: make dev service=gallery-service"; \
		exit 1; \
	fi
	cd services/$(service) && \
		uv run uvicorn src.main:app --reload --host 0.0.0.0 --port $(or $(port),8000)

# ── Infrastructure (Tier 1 — Local) ───────────────────────────────────────

.PHONY: infra-up
infra-up: ## Start local infrastructure (Postgres, Redis, NATS, Keycloak)
	docker compose -f infrastructure/local/docker-compose.yaml up -d
	@echo "→ Infrastructure running"
	@echo "  Postgres:  localhost:5432"
	@echo "  Redis:     localhost:6379"
	@echo "  NATS:      localhost:4222"
	@echo "  Keycloak:  localhost:8080"

.PHONY: infra-down
infra-down: ## Stop local infrastructure
	docker compose -f infrastructure/local/docker-compose.yaml down

.PHONY: infra-reset
infra-reset: ## Stop infrastructure and remove all data volumes
	docker compose -f infrastructure/local/docker-compose.yaml down -v
	@echo "→ Infrastructure stopped and volumes removed"

# ── Infrastructure (Tier 2 — Full Stack) ──────────────────────────────────

.PHONY: full-stack-up
full-stack-up: ## Start all services + infrastructure in Docker
	docker compose -f infrastructure/local/docker-compose.yaml \
		-f infrastructure/local/docker-compose.full.yaml up -d --build
	@echo "→ Full stack running"

.PHONY: full-stack-down
full-stack-down: ## Stop full stack
	docker compose -f infrastructure/local/docker-compose.yaml \
		-f infrastructure/local/docker-compose.full.yaml down

# ── Infrastructure (Tier 3 — Kubernetes) ──────────────────────────────────

.PHONY: k8s-deploy-local
k8s-deploy-local: ## Deploy Helm charts to local K8s (OrbStack or Kind)
	@echo "→ Deploying to local Kubernetes..."
	kubectl apply -f infrastructure/kubernetes/base/namespaces.yaml
	@echo "→ Helm chart deployment — implemented in Step 11"

.PHONY: k8s-teardown-local
k8s-teardown-local: ## Remove all deployments from local K8s
	@echo "→ Tearing down local Kubernetes deployments..."
	kubectl delete namespace artisan-apps artisan-infra artisan-obs --ignore-not-found

# Kind — only for Linux (OrbStack handles K8s on Mac)
.PHONY: kind-up
kind-up: ## Create a Kind cluster (Linux only — Mac uses OrbStack K8s)
	kind create cluster --name artisan --config infrastructure/local/kind-config.yaml
	@echo "→ Kind cluster 'artisan' created"

.PHONY: kind-down
kind-down: ## Delete the Kind cluster
	kind delete cluster --name artisan

# ── Testing ────────────────────────────────────────────────────────────────

.PHONY: test
test: ## Run unit tests for a service (usage: make test service=gallery-service)
	@if [ -z "$(service)" ]; then \
		echo "Error: specify a service. Usage: make test service=gallery-service"; \
		exit 1; \
	fi
	cd services/$(service) && uv run pytest tests/unit/ -v --tb=short

.PHONY: test-integration
test-integration: ## Run integration tests (usage: make test-integration service=gallery-service)
	@if [ -z "$(service)" ]; then \
		echo "Error: specify a service. Usage: make test-integration service=gallery-service"; \
		exit 1; \
	fi
	cd services/$(service) && uv run pytest tests/integration/ -v --tb=short

.PHONY: test-all
test-all: ## Run all unit tests across all services
	@for svc in $(SERVICES); do \
		echo "→ Testing $$svc..."; \
		$(MAKE) test service=$$svc || exit 1; \
	done

.PHONY: coverage
coverage: ## Run tests with coverage report (usage: make coverage service=gallery-service)
	@if [ -z "$(service)" ]; then \
		echo "Error: specify a service. Usage: make coverage service=gallery-service"; \
		exit 1; \
	fi
	cd services/$(service) && uv run pytest tests/ --cov=src --cov-report=html --cov-report=term

# ── Code Quality ───────────────────────────────────────────────────────────

.PHONY: lint
lint: ## Run linting across the entire project
	uv run ruff check .
	uv run ruff format --check .

.PHONY: lint-fix
lint-fix: ## Auto-fix linting issues
	uv run ruff check --fix .
	uv run ruff format .

.PHONY: typecheck
typecheck: ## Run mypy type checking (usage: make typecheck service=gallery-service)
	@if [ -z "$(service)" ]; then \
		echo "Error: specify a service. Usage: make typecheck service=gallery-service"; \
		exit 1; \
	fi
	cd services/$(service) && uv run mypy src/

.PHONY: pre-commit-all
pre-commit-all: ## Run all pre-commit hooks on all files
	pre-commit run --all-files

# ── Docker ─────────────────────────────────────────────────────────────────

.PHONY: docker-build
docker-build: ## Build Docker image for a service (usage: make docker-build service=gallery-service)
	@if [ -z "$(service)" ]; then \
		echo "Error: specify a service. Usage: make docker-build service=gallery-service"; \
		exit 1; \
	fi
	docker build -t artisan/$(service):latest \
		-f services/$(service)/Dockerfile \
		.

# ── Cloud (AWS) ────────────────────────────────────────────────────────────

.PHONY: tf-plan
tf-plan: ## Run Terraform plan (usage: make tf-plan env=dev)
	@if [ -z "$(env)" ]; then \
		echo "Error: specify an environment. Usage: make tf-plan env=dev"; \
		exit 1; \
	fi
	cd infrastructure/terraform/environments/$(env) && terraform plan

.PHONY: tf-apply
tf-apply: ## Run Terraform apply (usage: make tf-apply env=dev)
	@if [ -z "$(env)" ]; then \
		echo "Error: specify an environment. Usage: make tf-apply env=dev"; \
		exit 1; \
	fi
	cd infrastructure/terraform/environments/$(env) && terraform apply

.PHONY: teardown
teardown: ## Destroy all cloud infrastructure (usage: make teardown env=prod)
	@echo "⚠️  This will destroy ALL cloud resources in $(env)!"
	@read -p "Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || exit 1
	cd infrastructure/terraform/environments/$(env) && terraform destroy

# ── Utilities ──────────────────────────────────────────────────────────────

.PHONY: clean
clean: ## Remove build artifacts, caches, virtual environments
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	@echo "→ Cleaned build artifacts"

.PHONY: tree
tree: ## Show project directory structure
	@find . -not -path './.git/*' -not -path '*/__pycache__/*' -not -path '*/.venv/*' \
		-not -path '*/.mypy_cache/*' -not -path '*/.ruff_cache/*' \
		-not -path '*/.pytest_cache/*' -not -name '*.pyc' | \
		sort | sed 's|[^/]*/|  |g'
