# PEARL Backend Makefile

.PHONY: help install test format lint typecheck run migrate clean check-all

help:
	@echo "PEARL Backend Development Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup:"
	@echo "  install          Install dependencies"
	@echo ""
	@echo "Testing (curl-based scripts in tests/scripts/):"
	@echo "  test             Run core CRUD tests"
	@echo "  test-all         Run all test scripts"
	@echo ""
	@echo "Code Quality:"
	@echo "  format           Format code with black and isort"
	@echo "  lint             Run flake8 linting"
	@echo "  typecheck        Run mypy type checking"
	@echo "  check-all        Run all code quality checks"
	@echo ""
	@echo "Development:"
	@echo "  run              Start development server"
	@echo "  migrate          Apply database migrations"
	@echo "  validate-models  Run model validation"
	@echo "  clean            Clean generated files"

# Installation
install:
	uv pip install -r requirements.txt -r requirements-dev.txt

# Testing (curl-based - server must be running)
test:
	@echo "Running core CRUD tests (server must be running)..."
	cd tests/scripts && ./test_crud_simple.sh

test-all:
	@echo "Running all test scripts (server must be running)..."
	@for script in tests/scripts/*.sh; do \
		echo "Running $$script..."; \
		bash "$$script"; \
	done

# Code quality
format:
	black app
	isort app

lint:
	flake8 app

typecheck:
	mypy app

check-all: format lint typecheck

# Development
run:
	uv run python run.py

migrate:
	uv run alembic upgrade head

validate-models:
	uv run python tests/validator/run_model_validation.py

# Cleanup
clean:
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

# Docker
docker-build:
	docker build -t pearl-backend .

docker-run:
	docker-compose up --build

docker-down:
	docker-compose down -v
