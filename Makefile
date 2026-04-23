.PHONY: help install setup test test-fast test-pre-commit test-pr test-performance test-smoke test-with-timing lint format security clean

# Default target
.DEFAULT_GOAL := help

# Python interpreter
PYTHON := python3.11
POETRY := poetry

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies with Poetry
	$(POETRY) install --sync

setup: install ## Complete development setup
	$(POETRY) run pre-commit install
	@echo "Development environment ready!"

test: ## Run tests with coverage
	$(POETRY) run pytest -v --cov=src --cov-report=html --cov-report=term-missing

test-fast: ## Run fast tests for development (< 1 minute)
	$(POETRY) run pytest tests/unit/ -m "not slow and not performance and not stress" --maxfail=3 --tb=short

test-pre-commit: ## Run pre-commit validation tests (< 2 minutes)
	$(POETRY) run pytest tests/unit/ tests/integration/ -m "not performance and not stress and not contract" --maxfail=5

test-pr: ## Run PR validation tests (< 5 minutes)
	$(POETRY) run pytest -m "not performance and not stress" --maxfail=10

test-performance: ## Run performance tests only
	$(POETRY) run pytest tests/performance/ -m "performance or stress" --tb=line

test-smoke: ## Run smoke tests for basic functionality
	$(POETRY) run pytest tests/unit/ -m "smoke or fast" --maxfail=1 -x

test-with-timing: ## Run tests with detailed timing analysis
	$(POETRY) run pytest --durations=20 --tb=short

lint: ## Run linting checks
	$(POETRY) run ruff format --check .
	$(POETRY) run ruff check .
	$(POETRY) run basedpyright
	markdownlint **/*.md
	yamllint .
	$(POETRY) run darglint src/
	$(POETRY) run interrogate src/ --fail-under 70
	$(POETRY) run interrogate scripts/ --fail-under 85

format: ## Format code
	$(POETRY) run ruff format .
	$(POETRY) run ruff check --fix .

security: ## Run security checks
	$(POETRY) run pip-audit
	$(POETRY) run bandit -r src

db-migrate: ## Run database migrations
	$(POETRY) run alembic upgrade head

db-reset: ## Reset database (development only)
	$(POETRY) run alembic downgrade base
	$(POETRY) run alembic upgrade head

pre-commit: ## Run all pre-commit hooks manually
	$(POETRY) run pre-commit run --all-files

clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .coverage htmlcov coverage.xml
	rm -rf .pytest_cache .basedpyright .ruff_cache
	rm -rf dist build *.egg-info