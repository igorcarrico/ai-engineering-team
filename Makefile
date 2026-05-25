# AI Engineering Team — developer shortcuts
# Works in bash/zsh (macOS, Linux, Git Bash, WSL).

BACKEND := backend
FRONTEND := frontend
PY := $(BACKEND)/.venv/Scripts/python.exe   # Windows venv path; see `make venv-unix` for *nix

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---- Setup ----
.PHONY: setup
setup: backend-install frontend-install ## Install all dependencies

.PHONY: backend-install
backend-install: ## Create backend venv and install deps
	cd $(BACKEND) && python -m venv .venv && \
	  ./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt

.PHONY: frontend-install
frontend-install: ## Install frontend deps
	cd $(FRONTEND) && npm install

# ---- Dev ----
.PHONY: dev-backend
dev-backend: ## Run the FastAPI backend (reload)
	cd $(BACKEND) && ./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000

.PHONY: dev-frontend
dev-frontend: ## Run the Next.js frontend
	cd $(FRONTEND) && npm run dev

# ---- Quality ----
.PHONY: test
test: ## Run backend tests
	cd $(BACKEND) && ./.venv/Scripts/python.exe -m pytest

.PHONY: lint
lint: ## Lint backend (ruff) and frontend (next lint)
	cd $(BACKEND) && ./.venv/Scripts/python.exe -m ruff check app tests
	cd $(FRONTEND) && npm run lint

.PHONY: typecheck
typecheck: ## Type-check both sides
	cd $(BACKEND) && ./.venv/Scripts/python.exe -m mypy app
	cd $(FRONTEND) && npm run typecheck

# ---- Demo ----
.PHONY: run-cli
run-cli: ## Run a full workflow in the terminal (mock mode)
	cd $(BACKEND) && ./.venv/Scripts/python.exe scripts/run_workflow.py "Build a SaaS platform for AI-powered financial analytics"

# ---- Docker ----
.PHONY: up
up: ## Start the full stack with docker-compose
	docker compose up --build

.PHONY: down
down: ## Stop the stack
	docker compose down
