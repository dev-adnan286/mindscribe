.PHONY: help setup backend-install frontend-install backend-dev frontend-dev dev seed \
        test backend-test frontend-test lint backend-lint frontend-lint migrate \
        compose-up compose-down clean

PYTHON ?= python
VENV   := backend/.venv
ifeq ($(OS),Windows_NT)
  VENV_BIN := $(VENV)/Scripts
else
  VENV_BIN := $(VENV)/bin
endif

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

setup: backend-install frontend-install ## Install backend + frontend dependencies

backend-install: ## Create venv and install backend with dev extras
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/python -m pip install --upgrade pip
	$(VENV_BIN)/python -m pip install -e "backend[dev]"

frontend-install: ## Install frontend dependencies
	cd frontend && npm install

backend-dev: ## Run the API with reload on :8000
	cd backend && ../$(VENV_BIN)/python -m uvicorn app.main:app --reload --port 8000

frontend-dev: ## Run the Next.js dev server on :3000
	cd frontend && npm run dev

seed: ## Seed a demo user with sample notes
	cd backend && ../$(VENV_BIN)/python -m scripts.seed

migrate: ## Apply Alembic migrations
	cd backend && ../$(VENV_BIN)/python -m alembic upgrade head

backend-test: ## Run pytest (SQLite)
	cd backend && ../$(VENV_BIN)/python -m pytest -q

frontend-test: ## Run vitest
	cd frontend && npm test

test: backend-test frontend-test ## Run all tests

backend-lint: ## Ruff lint + format check
	cd backend && ../$(VENV_BIN)/python -m ruff check app tests scripts alembic && ../$(VENV_BIN)/python -m ruff format --check app tests scripts alembic

frontend-lint: ## ESLint + TypeScript
	cd frontend && npm run lint && npx tsc --noEmit

lint: backend-lint frontend-lint ## Lint everything

compose-up: ## Start postgres + backend + frontend with docker compose
	docker compose up --build -d

compose-down: ## Stop docker compose services
	docker compose down

clean: ## Remove build artefacts
	rm -rf backend/.pytest_cache backend/.ruff_cache frontend/.next
