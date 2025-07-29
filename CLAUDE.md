# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PEARL is a full-stack research data management system with:
- **Backend**: FastAPI with async PostgreSQL CRUD operations (`backend/`)
- **Frontend**: Python Shiny admin dashboard (`admin-frontend/`)  
- **Real-time Communication**: WebSocket support for live updates

## Architecture

### Backend (FastAPI)
- **Framework**: FastAPI 0.111+ with async/await patterns
- **Database**: PostgreSQL with SQLAlchemy 2.0 async ORM
- **Package Manager**: UV for fast dependency management
- **Structure**: Clean architecture with separate layers (models, schemas, crud, api)

### Frontend (R Shiny)
- **Framework**: R Shiny with shinydashboard theme
- **Architecture**: Modular UI/server separation in `modules/`
- **Communication**: HTTP API client via httr package for REST calls
- **Features**: CRUD operations, interactive data tables, form validation

### WebSocket Layer
- **Endpoint**: `ws://localhost:8000/api/v1/ws/studies`
- **Events**: `study_created`, `study_updated`, `study_deleted`
- **Client**: Auto-reconnecting WebSocket client in frontend
- **Purpose**: Real-time synchronization across multiple users

## Development Commands

### Backend Commands (from `backend/`)

#### Package Management (UV preferred)
```bash
# Install dependencies
uv pip install -r requirements.txt

# Development with auto-reload
uv run python run.py

# Alternative direct server start
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Database Operations
```bash
# Initialize database (creates DB + tables)
uv run python -m app.db.init_db

# Migrations
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head
```

#### Testing (see Critical Testing Constraints below)
```bash
# Individual test (RECOMMENDED)
uv run pytest tests/test_single.py -v

# Full test suite (expect session conflicts in batch mode)
uv run python run_tests.py

# Test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-security      # Security tests only
```

#### Code Quality
```bash
# Format and lint
uv run black app/ tests/
uv run isort app/ tests/
uv run mypy app/
uv run flake8 app/ tests/

# Or use Makefile shortcuts
make format
make lint
make typecheck
```

#### Model Validation
```bash
# Validate SQLAlchemy/Pydantic model alignment
uv run python tests/validator/run_model_validation.py
```

### Frontend Commands (from `admin-frontend/`)

```bash
# Environment setup (first-time or updates - consolidated script)
Rscript setup_environment.R

# Start R Shiny admin dashboard (port 3838)
Rscript run_app.R

# Alternative: Run from R console
R
> renv::restore()  # if needed
> shiny::runApp(".", port = 3838)
```

### WebSocket Testing
```bash
# From project root
python test_websocket.py
```

## Critical Testing Constraints

**⚠️ IMPORTANT**: This project has SQLAlchemy async session management constraints that prevent reliable batch test execution.

### The Issue
- **Symptom**: `sqlalchemy.exc.InterfaceError: cannot perform operation: another operation is in progress`
- **Cause**: Real PostgreSQL database without transaction isolation in test environment
- **Impact**: Individual tests work perfectly, batch execution frequently fails

### Required Testing Approach
1. **Read `backend/tests/README.md` FIRST** before creating any tests
2. **Test individually**: Always use `pytest single_test.py` for database tests
3. **Prefer non-database tests**: Validation, schema, logic tests are reliable
4. **Expect batch failures**: This is documented, expected behavior
5. **One test per file**: For database operations to avoid conflicts

### Safe Test Patterns
```python
# ✅ SAFE: Non-database validation
async def test_input_validation(client):
    response = await client.post("/api/v1/studies/", json={"study_label": ""})
    assert response.status_code == 422

# ✅ SAFE: Single database read (non-existent)
async def test_get_not_found(db_session):
    result = await study.get(db_session, id=999999)
    assert result is None

# ❌ UNSAFE: Multiple database operations in same test/file
```

## Project Structure

```
PEARL/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # API endpoints + WebSocket
│   │   ├── core/              # Configuration, security
│   │   ├── crud/              # Database operations
│   │   ├── db/                # Database session, init
│   │   ├── models/            # SQLAlchemy models
│   │   └── schemas/           # Pydantic schemas
│   ├── migrations/            # Alembic migrations
│   ├── tests/                 # Test suites + validator
│   ├── Makefile              # Development commands
│   ├── pyproject.toml        # UV project config
│   └── requirements.txt      # Dependencies
├── admin-frontend/            # R Shiny admin dashboard
│   ├── modules/              # R Shiny modules
│   │   ├── api_client.R     # HTTP API client functions
│   │   ├── studies_ui.R     # Studies UI components
│   │   └── studies_server.R # Studies server logic
│   ├── www/                 # Static web assets
│   ├── app.R                # Main R Shiny application
│   └── run_app.R            # Application runner script
└── WEBSOCKET_README.md       # WebSocket documentation
```

## API Endpoints

### REST API (`/api/v1/`)
- `POST /studies` - Create study
- `GET /studies` - List studies (paginated)
- `GET /studies/{id}` - Get study by ID
- `PUT /studies/{id}` - Update study
- `DELETE /studies/{id}` - Delete study

### WebSocket
- `ws://localhost:8000/api/v1/ws/studies` - Real-time updates

### Documentation
- `/docs` - Swagger UI
- `/redoc` - ReDoc documentation
- `/health` - Health check endpoint

## Key Files to Understand

### Backend Core
- `app/main.py` - FastAPI application with lifespan management
- `app/db/session.py` - Async SQLAlchemy session factory
- `app/api/v1/studies.py` - CRUD endpoints with WebSocket broadcasting
- `app/api/v1/websocket.py` - WebSocket connection manager

### Frontend Core  
- `admin-frontend/app.R` - Main R Shiny application
- `modules/studies_ui.R` - Studies UI components
- `modules/studies_server.R` - Studies server logic  
- `modules/api_client.R` - HTTP client for backend communication

### Testing & Validation
- `backend/tests/README.md` - Essential testing constraints documentation
- `tests/validator/` - Model validation system for SQLAlchemy/Pydantic alignment

## Environment Setup

### Prerequisites
- Python 3.11+ (backend)
- R 4.3.0+ (frontend)
- PostgreSQL 13+
- UV package manager (recommended for backend)

### Quick Start
```bash
# 1. Backend setup
cd backend
uv pip install -r requirements.txt
uv run python -m app.db.init_db
uv run python run.py

# 2. Frontend setup (new terminal)
cd admin-frontend  
Rscript setup_environment.R    # Environment setup (first-time or updates)
Rscript run_app.R

# 3. Access applications
# Backend API: http://localhost:8000
# Admin Dashboard: http://localhost:3838
# API Docs: http://localhost:8000/docs
```

## For AI Agents

### Test Agent Requirements
- **MANDATORY**: Read `backend/tests/README.md` before creating ANY tests
- **Pattern**: Use individual test files for database operations
- **Expectation**: Batch test failures are normal and documented

### Model Validator Usage
- Run `uv run python tests/validator/run_model_validation.py` after model changes
- Addresses SQLAlchemy/Pydantic alignment issues before they cause problems
- Critical for maintaining type safety across the API layer

### WebSocket Integration
- All CRUD operations automatically broadcast WebSocket events
- Frontend automatically refreshes on data changes
- Test WebSocket functionality with `python test_websocket.py`