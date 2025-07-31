# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **📖 For comprehensive project documentation, setup instructions, API endpoints, and deployment guides, see [README.md](README.md)**

## Project Overview

PEARL Backend is a FastAPI application with async PostgreSQL CRUD operations and **real-time WebSocket updates**. This is a **production-like development environment** with specific constraints around testing and database management.

**Key Features**: FastAPI + async PostgreSQL + WebSocket broadcasting + UV package management  
**Critical Constraint**: SQLAlchemy async session conflicts prevent reliable batch test execution

### Package Management with UV

This project uses **[UV](https://docs.astral.sh/uv/)** as the modern Python package manager for fast, deterministic builds:

**Benefits**:
- ⚡ Faster dependency resolution than pip
- 🔒 Deterministic builds with `uv.lock`
- 🐍 Python version management
- 📦 Unified toolchain

**Key Commands**:
```bash
# Use uv for all Python operations
uv run python run.py           # Start development server
uv run alembic upgrade head    # Database migrations
uv run pytest tests/          # Run tests
uv pip install -r requirements.txt  # Install dependencies
```

> **🏗️ See [README.md - Features & Project Structure](README.md#features) for complete technology stack and architecture details**

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

> **🚀 See [README.md - Setup & Development](README.md#setup) for complete installation, database setup, and development workflow**

### Quick Reference
```bash
# Install dependencies
uv pip install -r requirements.txt

# Initialize database
uv run python -m app.db.init_db

# Start development server
uv run python run.py

# Access at: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Code Quality & Formatting
```bash
# Format code
make format             # Black + isort formatting
uv run black app tests  # Format with black
uv run isort app tests  # Sort imports

# Lint and type check
make lint               # flake8 + mypy
make typecheck          # mypy only
uv run mypy app        # Type checking
uv run flake8 app tests # Linting

# Clean up generated files
make clean              # Remove coverage, cache files
```

### Database Management
```bash
# Alembic migrations
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic current
uv run alembic history

# Make commands
make migrate            # Apply migrations (alembic upgrade head)
make db-reset          # Reset database with Docker
```

### Testing (Individual Files Only)
```bash
# Functional testing (recommended)
./test_crud_simple.sh

# Individual pytest (works reliably)
pytest tests/specific_test.py -v

# Model validation (CRITICAL after model changes)
uv run python tests/validator/run_model_validation.py

# Make commands (comprehensive testing)
make test-fast          # Fast tests excluding slow performance tests
make test-unit          # Unit tests only
make test-integration   # Integration tests only  
make test-security      # Security tests only
make test-coverage      # Tests with coverage report
```

## Key Architecture Notes

> **🏛️ See [README.md - Project Structure](README.md#project-structure) for complete directory structure and component descriptions**

### Critical Architecture Points
- **Real PostgreSQL**: No test isolation (source of async session conflicts)
- **WebSocket Broadcasting**: All CRUD operations broadcast real-time events
- **Clean Architecture**: API → CRUD → Models with clear separation
- **Async Session Management**: Context managers with session conflict limitations
- **Application Lifespan**: Automatic database initialization on startup, graceful shutdown
- **Health Checks**: Built-in health endpoint (`/health`) with database connectivity testing
- **CORS Configuration**: Pre-configured for frontend integration
- **Global Exception Handling**: Comprehensive error handling with structured logging

## Development Workflow

> **🛠️ See [README.md - Development](README.md#development) for complete development workflow, code formatting, and database migration instructions**

### Critical Development Points
1. **Individual Testing Only**: Use `./test_crud_simple.sh` or `pytest single_test.py -v`
2. **Model Validation**: Always run after model changes to catch SQLAlchemy/Pydantic misalignment
3. **WebSocket Broadcasting**: CRUD operations automatically broadcast events - test with multiple browser sessions
4. **Database Changes**: Use `alembic revision --autogenerate` for schema changes
5. **Referential Integrity**: Always implement deletion protection for related entities (see Deletion Patterns below)

### FastAPI Model Validator Tool

**🎯 CRITICAL**: This project includes a specialized model validation tool that must be run after any model changes.

**Purpose**: Validates SQLAlchemy and Pydantic model alignment to prevent frontend integration issues

**Usage**:
```bash
# Run model validation (required after model changes)
uv run python tests/validator/run_model_validation.py

# Generate JSON report
uv run python tests/validator/fastapi_model_validator.py . --format json

# Save validation report
uv run python tests/validator/fastapi_model_validator.py . -o validation_report.txt
```

**When to Run**:
- After adding/modifying SQLAlchemy models (`app/models/*.py`)
- After updating Pydantic schemas (`app/schemas/*.py`)
- Before committing model-related changes
- When experiencing unexplained frontend/backend integration issues

**What it Validates**:
- Type compatibility between SQLAlchemy and Pydantic models
- Nullable/optional field consistency
- Field constraint alignment
- Missing field detection

### Deletion Patterns & Referential Integrity

> **🛡️ CRITICAL**: All entity deletions must check for dependent relationships to maintain data integrity**

#### Current Implementation Examples

**Study Deletion Protection** (`app/api/v1/studies.py:168-175`):
```python
# Check for associated database releases before deletion
associated_releases = await database_release.get_by_study_id(db, study_id=study_id)
if associated_releases:
    release_labels = [release.database_release_label for release in associated_releases]
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Cannot delete study '{db_study.study_label}': {len(associated_releases)} associated database release(s) exist: {', '.join(release_labels)}. Please delete all associated database releases first."
    )
```

**Database Release Deletion Protection** (`app/api/v1/database_releases.py:188-195`):
```python
# Check for associated reporting efforts before deletion
associated_efforts = await reporting_effort.get_by_database_release_id(db, database_release_id=database_release_id)
if associated_efforts:
    effort_labels = [effort.database_release_label for effort in associated_efforts]
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Cannot delete database release '{db_release.database_release_label}': {len(associated_efforts)} associated reporting effort(s) exist: {', '.join(effort_labels)}. Please delete all associated reporting efforts first."
    )
```

#### Required CRUD Methods for Deletion Protection

**For each dependent relationship, implement query methods**:
```python
# In dependent entity CRUD class
async def get_by_parent_id(self, db: AsyncSession, *, parent_id: int) -> List[DependentModel]:
    """Get all dependent entities for a specific parent (no pagination)."""
    result = await db.execute(
        select(DependentModel).where(DependentModel.parent_id == parent_id)
    )
    return list(result.scalars().all())
```

#### Deletion Protection Implementation Pattern

1. **Query for Dependents**: Use `get_by_parent_id()` method to find related entities
2. **Check Existence**: If dependents exist, block deletion with HTTP 400
3. **Descriptive Error**: List all dependent entities by name/label for user clarity  
4. **Clear Instructions**: Tell user exactly what needs to be deleted first
5. **Test Coverage**: Create comprehensive tests like `test_study_deletion_protection_fixed.sh`

#### Error Message Standards

**Format**: `"Cannot delete {entity} '{entity_label}': {count} associated {dependent_type}(s) exist: {list_of_names}. Please delete all associated {dependent_type}s first."`

**Example**: `"Cannot delete study 'Clinical Trial A': 3 associated database release(s) exist: jan_primary, feb_set, mar_final. Please delete all associated database releases first."`

#### Testing Deletion Protection

**Required Test Scenarios**:
1. ✅ Create parent entity
2. ✅ Create dependent entity(ies) 
3. ✅ Attempt parent deletion (should fail with HTTP 400)
4. ✅ Verify descriptive error message
5. ✅ Delete dependent entities first
6. ✅ Attempt parent deletion again (should succeed with HTTP 200)

**Test Script Pattern**: See `test_study_deletion_protection_fixed.sh` as reference implementation

#### Current Data Model & Relationships

**Three-tier hierarchical structure with cascading deletion protection**:

```
Study (1) ←→ (N) DatabaseRelease (1) ←→ (N) ReportingEffort
  ↑                                              ↓
  └────────────── (1) ←→ (N) ──────────────────┘
```

**Deletion Order Requirements**:
1. **ReportingEffort** (leaf nodes - can be deleted freely)
2. **DatabaseRelease** (middle tier - blocked if ReportingEffort exists)  
3. **Study** (root - blocked if DatabaseRelease exists)

**Current Endpoints**:
- `/api/v1/studies/` - Study CRUD with DatabaseRelease deletion protection
- `/api/v1/database-releases/` - DatabaseRelease CRUD with ReportingEffort deletion protection
- `/api/v1/reporting-efforts/` - ReportingEffort CRUD (no dependent entities)

**WebSocket Broadcasting**: All CRUD operations broadcast real-time events for each entity type

## WebSocket Implementation Details

> **📡 Critical WebSocket patterns for Claude Code development**

### Data Type Conversion Issue
**Problem**: SQLAlchemy models don't have `model_dump()` method (Pydantic only)
**Solution**: Convert in broadcast functions: `Study.model_validate(sqlalchemy_model).model_dump()`

**Required in**:
- `app/api/v1/websocket.py` - WebSocket endpoint initial data + refresh responses
- `app/api/v1/websocket.py` - Broadcast functions (`broadcast_study_created`, etc.)

### WebSocket Endpoint Patterns
```python
# ✅ CORRECT: Manual session management for WebSocket
async with AsyncSessionLocal() as db:
    studies_data = await study.get_multi(db, skip=0, limit=100)
    studies_json = [Study.model_validate(item).model_dump() for item in studies_data]

# ❌ INCORRECT: Dependency injection doesn't work reliably with WebSocket
@router.websocket("/studies")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
```

### Broadcast Integration Pattern
```python
# In CRUD endpoints (app/api/v1/studies.py)
created_study = await study.create(db, obj_in=study_in)
await broadcast_study_created(created_study)  # SQLAlchemy model → conversion happens in broadcast function
```

### Testing WebSocket Functionality
```bash
# Test WebSocket broadcasting (from project root)
uv run python test_websocket_broadcast.py

# Manual test: Open multiple browser sessions and perform CRUD operations
```

## For Test Architect Agents

**MANDATORY**: Before creating ANY tests, read:
1. `/mnt/c/python/PEARL/backend/tests/README.md` - Complete testing constraints
2. This `CLAUDE.md` file - Project-specific limitations

**Key Constraint**: This project cannot support traditional test isolation patterns. Design tests accordingly or they will fail in batch execution due to async session conflicts.

**Success Metric**: Individual test reliability, not batch test pass rates.