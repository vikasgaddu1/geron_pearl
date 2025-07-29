# PEARL Backend Makefile

.PHONY: help install test test-unit test-integration test-security test-performance test-contract test-coverage test-fast test-docker clean lint format

# Default target
help:
	@echo "PEARL Backend Development Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install          Install all dependencies including dev dependencies"
	@echo "  install-prod     Install production dependencies only"
	@echo ""
	@echo "Test Commands:"
	@echo "  test             Run all test suites"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-security    Run security tests only"
	@echo "  test-performance Run performance tests only"
	@echo "  test-contract    Run contract tests only"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  test-fast        Run tests excluding slow performance tests"
	@echo "  test-docker      Run tests in Docker environment"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  lint             Run linting checks"
	@echo "  format           Format code with black and isort"
	@echo "  typecheck        Run mypy type checking"
	@echo ""
	@echo "Development Commands:"
	@echo "  run              Start development server"
	@echo "  migrate          Run database migrations"
	@echo "  clean            Clean up generated files"
	@echo ""

# Installation
install:
	pip install -e ".[dev]"

install-prod:
	pip install -e .

# Test commands
test:
	python run_tests.py

test-unit:
	python run_tests.py --type unit

test-integration:
	python run_tests.py --type integration

test-security:
	python run_tests.py --type security

test-performance:
	python run_tests.py --type performance

test-contract:
	python run_tests.py --type contract

test-coverage:
	python run_tests.py --coverage

test-fast:
	python run_tests.py --fast

test-docker:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Alternative pytest commands
pytest-unit:
	pytest tests/unit/ -v

pytest-integration:
	pytest tests/integration/ -v

pytest-security:
	pytest tests/security/ -v

pytest-performance:
	pytest tests/performance/ -v --durations=10

pytest-contract:
	pytest tests/contract/ -v

pytest-coverage:
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

pytest-parallel:
	pytest tests/ -n auto

# Code quality
lint:
	flake8 app tests
	mypy app

format:
	black app tests
	isort app tests

typecheck:
	mypy app

# Development
run:
	python run.py

migrate:
	alembic upgrade head

# Utility
clean:
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete

# Docker commands
docker-build:
	docker build -t pearl-backend .

docker-run:
	docker-compose up --build

docker-down:
	docker-compose down -v

docker-test-build:
	docker-compose -f docker-compose.test.yml build

docker-test-clean:
	docker-compose -f docker-compose.test.yml down -v --remove-orphans

# Database commands
db-reset:
	docker-compose down -v
	docker-compose up -d postgres
	alembic upgrade head

# CI/CD helpers
ci-test:
	python run_tests.py --coverage --fast

ci-full-test:
	python run_tests.py --coverage

# Performance profiling
profile-tests:
	pytest tests/performance/ -v --durations=0

# Security audit
security-audit:
	python run_tests.py --type security --verbose

# Generate test report
test-report:
	pytest tests/ --html=test-report.html --self-contained-html --cov=app --cov-report=html

# Watch tests (requires pytest-watch)
test-watch:
	ptw -- tests/ -v

# Install development tools
install-dev-tools:
	pip install pytest-watch pytest-html pytest-xdist

# Check all
check-all: lint typecheck test-fast

# Full validation (for CI)
validate: format lint typecheck test-coverage