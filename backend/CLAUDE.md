# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PEARL Backend is a FastAPI application with async PostgreSQL CRUD operations for study management. This is a **production-like development environment** with specific constraints around testing and database management.

### Technology Stack
- **FastAPI 0.111+** with async/await patterns and lifespan management
- **PostgreSQL** with SQLAlchemy 2.0 async ORM
- **UV package manager** for fast dependency management
- **Alembic** for database migrations
- **Pytest** with async support for testing

## Critical Testing Constraints

### Database Session Management Issues

**⚠️ CRITICAL LIMITATION**: This project has SQLAlchemy async session management conflicts that prevent reliable batch test execution. This is NOT a bug but an architectural constraint of running tests against real PostgreSQL without transaction isolation.

**Symptoms**:
```
sqlalchemy.exc.InterfaceError: cannot perform operation: another operation is in progress
```

**Impact**:
- ✅ Individual tests work perfectly
- ❌ Batch test execution frequently fails
- ✅ CRUD functionality is fully working
- ✅ API endpoints work correctly
- ⚠️ Test coverage reports may show failures despite working code

### Test Development Guidelines

1. **Read `tests/README.md` FIRST** - Contains essential constraints and patterns
2. **Prefer individual test files** - One test per file for database operations
3. **Favor non-database tests** - Validation, schema, and logic tests work reliably
4. **Test individually** - Always test with `pytest single_test.py` before batch
5. **Expect batch failures** - This is normal and documented behavior

### Safe Test Patterns

```python
# ✅ SAFE: Non-database validation
async def test_input_validation(self, client):
    response = await client.post("/api/v1/studies/", json={"study_label": ""})
    assert response.status_code == 422

# ✅ SAFE: Single database read (non-existent)
async def test_get_not_found(self, db_session):
    result = await study.get(db_session, id=999999)
    assert result is None

# ❌ UNSAFE: Multiple database operations
async def test_create_and_retrieve(self, db_session):
    created = await study.create(db_session, data)  # Conflicts with other tests
    retrieved = await study.get(db_session, created.id)  # May fail in batch
```

### Unsafe Test Patterns (Avoid)

- Tests using `sample_study` or `multiple_studies` fixtures
- Multiple tests in same file accessing database
- Tests that create database records
- Concurrent database operations
- Tests requiring database state setup

## Development Commands

### Server Management
```bash
# Start development server (recommended)
uv run python run.py

# Alternative server start
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Available at: http://localhost:8000
# API docs: http://localhost:8000/docs
# Health check: http://localhost:8000/health
```

### Package Management
```bash
# Install all dependencies (including dev)
make install
# OR
pip install -e ".[dev]"

# Install production dependencies only
make install-prod
# OR
pip install -e .

# Using UV (recommended)
uv pip install -r requirements.txt
```

### Database Operations
```bash
# Initialize database (creates DB + tables)
uv run python -m app.db.init_db

# Create migration
uv run alembic revision --autogenerate -m "Description"

# Run migrations
make migrate
# OR
uv run alembic upgrade head

# Reset database (with Docker)
make db-reset
```

### Testing Commands
```bash
# Simple CRUD test script (recommended for functional testing)
./test_crud_simple.sh

# Makefile shortcuts
make test              # Run all tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-security     # Security tests only
make test-coverage     # With coverage report
make test-fast         # Exclude slow tests

# Direct pytest (expect session conflicts in batch mode)
pytest tests/specific_test.py -v    # Individual test file
pytest tests/ --cov=app --cov-report=html    # Coverage report
```

### Code Quality
```bash
# Format code
make format
# OR
uv run black app/ tests/
uv run isort app/ tests/

# Lint code
make lint
# OR
uv run flake8 app/ tests/

# Type checking
make typecheck
# OR
uv run mypy app/

# All quality checks
make check-all    # lint + typecheck + test-fast
make validate     # format + lint + typecheck + test-coverage
```

### Model Validation
```bash
# Validate SQLAlchemy/Pydantic model alignment
uv run python tests/validator/run_model_validation.py
```

### Docker Commands (if available)
```bash
make docker-build     # Build Docker image
make docker-run       # Run with docker-compose
make docker-test      # Run tests in Docker
make docker-down      # Stop containers
```

## Architecture Notes

- **FastAPI**: Modern async web framework with lifespan management
- **PostgreSQL**: Real production database (no test isolation)
- **SQLAlchemy 2.0**: Async ORM with session management limitations
- **Pydantic**: Data validation and serialization
- **UV**: Modern Python package manager
- **Pytest**: Testing framework with async support

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── health.py          # Health check endpoint
│   │   └── v1/
│   │       ├── __init__.py    # API router aggregation
│   │       ├── studies.py     # CRUD endpoints + WebSocket broadcasting
│   │       └── websocket.py   # WebSocket connection manager
│   ├── core/
│   │   ├── config.py          # Application settings
│   │   └── security.py        # Security utilities
│   ├── crud/
│   │   └── study.py           # Database operations
│   ├── db/
│   │   ├── base.py            # SQLAlchemy declarative base
│   │   ├── init_db.py         # Database initialization
│   │   └── session.py         # Async session factory
│   ├── models/
│   │   └── study.py           # SQLAlchemy models
│   ├── schemas/
│   │   └── study.py           # Pydantic schemas
│   └── main.py                # FastAPI application with lifespan
├── tests/
│   ├── README.md              # Testing constraints documentation
│   └── validator/             # Model validation system
├── migrations/                # Alembic migration files
├── Makefile                   # Development commands
├── pyproject.toml             # UV project configuration
├── run.py                     # Development server runner
└── test_crud_simple.sh        # Simple CRUD testing script
```

## Key Architecture Patterns

### Clean Architecture Layers
- **API Layer** (`api/`): FastAPI routers and WebSocket endpoints
- **Business Logic** (`crud/`): Database operations and business rules
- **Data Layer** (`models/`, `schemas/`): SQLAlchemy models and Pydantic schemas
- **Core** (`core/`): Configuration, security, and cross-cutting concerns

### Async Session Management
- Database sessions use async context managers
- No connection pooling in tests (source of session conflicts)
- Real PostgreSQL database for all environments

### WebSocket Integration
- All CRUD operations broadcast WebSocket events
- Connection manager handles client lifecycle
- Real-time synchronization across multiple clients

## Development Workflow

### Recommended Development Process
1. **Start Development Server**: `uv run python run.py`
2. **Make Code Changes**: Follow existing patterns in respective layers
3. **Test Individually**: Use `./test_crud_simple.sh` for endpoint validation
4. **Validate Models**: Run `uv run python tests/validator/run_model_validation.py`
5. **Code Quality**: Use `make check-all` before committing
6. **Database Changes**: Create migrations with `alembic revision --autogenerate`

### Working with Tests
1. **Functional Testing**: Use `./test_crud_simple.sh` (reliable HTTP testing)
2. **Individual Pytest**: `pytest tests/specific_test.py -v` (works perfectly)
3. **Batch Pytest**: Expect session conflicts, focus on individual test reliability
4. **Coverage Reports**: Use `make test-coverage` but expect some batch failures

## For Test Architect Agents

**MANDATORY**: Before creating ANY tests, read:
1. `/mnt/c/python/PEARL/backend/tests/README.md` - Complete testing constraints
2. This `CLAUDE.md` file - Project-specific limitations

**Key Constraint**: This project cannot support traditional test isolation patterns. Design tests accordingly or they will fail in batch execution due to async session conflicts.

**Success Metric**: Individual test reliability, not batch test pass rates.