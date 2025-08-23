# Makefile for Portfolio Performance Security Master

.PHONY: help setup clean lint test coverage format check install-dev

# Default target
help:
	@echo "Portfolio Performance Security Master Development Commands"
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup        - Full development environment setup"
	@echo "  install-dev  - Install development dependencies"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  format       - Format code with Black and isort"
	@echo "  lint         - Run linting with Ruff and MyPy"
	@echo "  check        - Run all quality checks (lint + format check)"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test         - Run all tests"
	@echo "  test-unit    - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  coverage     - Run tests with coverage report"
	@echo ""
	@echo "Database Commands:"
	@echo "  db-upgrade   - Run database migrations"
	@echo "  db-downgrade - Rollback one database migration"
	@echo "  db-reset     - Reset database to clean state"
	@echo ""
	@echo "Validation Commands:"
	@echo "  validate     - Run Phase 0 validation"
	@echo "  validate-env - Validate development environment"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean        - Clean up temporary files and caches"

setup: install-dev
	poetry run pre-commit install
	poetry run pre-commit install --hook-type commit-msg
	@echo "Development environment setup complete!"

install-dev:
	poetry install --with dev,test
	@echo "Dependencies installed"

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/

format:
	poetry run black src tests
	poetry run isort src tests
	@echo "Code formatted successfully"

lint:
	poetry run ruff check src tests
	poetry run mypy src
	@echo "Linting completed"

check: lint
	poetry run black --check src tests
	poetry run isort --check-only src tests
	@echo "All quality checks passed"

test:
	poetry run pytest

test-unit:
	poetry run pytest tests/unit/ -v

test-integration:
	poetry run pytest tests/integration/ -v --database

coverage:
	poetry run pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

# Database commands
db-upgrade:
	poetry run alembic upgrade head

db-downgrade:
	poetry run alembic downgrade -1

db-reset:
	poetry run alembic downgrade base
	poetry run alembic upgrade head

# Validation commands
validate:
	./scripts/validate_phase_0_complete.sh

validate-env:
	./scripts/validate_issue_P0-002.sh

# Development server (when implemented)
dev:
	poetry run python -m src.security_master.main

# Security scanning
security:
	poetry run safety check
	poetry run bandit -r src