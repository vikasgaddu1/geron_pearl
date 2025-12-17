# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PEARL is a **full-stack research data management system** with real-time WebSocket updates:
- **Backend**: FastAPI + async PostgreSQL + WebSocket broadcasting
- **Frontend**: Modern R Shiny + bslib + dual WebSocket clients
- **Real-time**: Live data synchronization across multiple users and browsers

## Quick Start

```bash
# Backend (Terminal 1)
cd backend
uv pip install -r requirements.txt
uv run python -m app.db.init_db
uv run python run.py

# Frontend (Terminal 2)
cd admin-frontend
Rscript setup_environment.R
Rscript run_app.R

# Access: Backend http://localhost:8000 | Frontend http://localhost:3838 | Docs http://localhost:8000/docs
```

## Critical Constraints

### SQLAlchemy Async Session Conflicts
**⚠️ CRITICAL**: Batch tests fail due to async session management. This is architectural, not a bug.
- ✅ Individual tests work perfectly
- ❌ Batch test execution fails
- Always test individually: `./test_crud_simple.sh` or `pytest single_test.py -v`

### Mandatory Patterns

**Deletion Protection** - ALL deletions must check dependencies:
```python
dependent_entities = await dependent_crud.get_by_parent_id(db, parent_id=entity_id)
if dependent_entities:
    raise HTTPException(status_code=400, detail=f"Cannot delete: {len(dependent_entities)} dependent entities exist")
```

**WebSocket Broadcasting** - ALL CRUD operations must broadcast:
```python
created_entity = await entity_crud.create(db, obj_in=entity_in)
await broadcast_entity_created(created_entity)
```

## Essential Commands

### Backend
```bash
cd backend
uv run python run.py                      # Start server
./test_crud_simple.sh                     # Run functional tests
make format && make lint                  # Code quality (required before commits)
uv run alembic revision --autogenerate -m "msg"  # Create migration
uv run alembic upgrade head               # Apply migrations
uv run python tests/validator/run_model_validation.py  # Validate models (run after model changes)
```

### Frontend
```bash
cd admin-frontend
Rscript run_app.R                         # Start app
renv::restore()                           # Restore packages
renv::install("package") && renv::snapshot()  # Add new package
```

### Stop Processes (Windows)
```bash
netstat -ano | findstr :8000              # Find backend PID
netstat -ano | findstr :3838              # Find frontend PID
powershell -Command "Stop-Process -Id <PID> -Force"
```

## Architecture

```
PEARL/
├── backend/
│   ├── app/api/v1/     # REST endpoints + WebSocket broadcasting
│   ├── app/crud/       # Business logic (never bypass this layer)
│   ├── app/models/     # SQLAlchemy ORM models
│   ├── app/schemas/    # Pydantic validation schemas
│   └── tests/          # Individual test scripts
├── admin-frontend/
│   ├── modules/        # UI (*_ui.R) + Server (*_server.R) modules
│   ├── www/            # JavaScript WebSocket client
│   └── app.R           # Main application entry
```

### Database Schema
```
Study (1) ↔ (N) DatabaseRelease (1) ↔ (N) ReportingEffort (1) ↔ (N) ReportingEffortItem
                                                                         ↓
Package (1) ↔ (N) PackageItem (TLF/Dataset)                    ReportingEffortItemTracker
                      ↓                                            (with TrackerComment)
              TextElement (title, footnote, population_set, acronyms_set)
User (admin, analyst, viewer roles)
```

## Key Development Patterns

### Backend (FastAPI)
- **Clean Architecture**: API → CRUD → Models (never bypass CRUD layer)
- **Model Changes**: Always run model validator after changes
- **WebSocket**: SQLAlchemy models require Pydantic conversion for broadcasts
- **UV Package Manager**: Use `uv run` for all Python operations

### Frontend (R Shiny)
- **Environment Variables**: All API endpoints use `Sys.getenv()`
- **Form Validation**: Use shinyvalidate with deferred validation (only on Save/Submit)
- **Module Pattern**: UI/Server separation for all components
- **WebSocket Events**: Module observers listen for `input$crud_refresh`

### Cross-Browser WebSocket Sync (Universal CRUD Manager)
```r
# In module server - Shiny strips module prefix automatically
observeEvent(input$crud_refresh, {  # NOT input$module-crud_refresh
  load_data()
})
```

### Database Migrations
```bash
# After modifying models
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head
uv run python tests/validator/run_model_validation.py
```

## Adding a New Entity

1. **Backend**: Create model → schema → CRUD class → API endpoints with WebSocket broadcasts
2. **Frontend**: Create UI module → server module → add to api_client.R
3. **WebSocket**: Add broadcast functions and event types
4. **Testing**: Create functional test script like `test_crud_simple.sh`

## Common Issues

| Issue | Solution |
|-------|----------|
| WebSocket not updating | Check browser console; verify message type matches module pattern |
| Module observer not triggering | Shiny strips module prefix; use `input$crud_refresh` not `input$module-crud_refresh` |
| Batch tests failing | Expected behavior; use individual test scripts |
| Model validation errors | Run `uv run python tests/validator/run_model_validation.py` |
| JavaScript timing errors | Always check `window.Shiny && window.Shiny.setInputValue` before use |

## Technology Stack

### Backend
- Python 3.11+ with UV package manager
- FastAPI 0.111+ with async/await
- SQLAlchemy 2.0 async + PostgreSQL
- Pydantic v2, Alembic migrations
- Black + isort + flake8 + mypy

### Frontend
- R 4.2.2 with renv
- Shiny + bslib (Bootstrap 5)
- httr2, shinyvalidate, DT
- Dual WebSocket clients (JS primary, R secondary)

## Component Documentation

- **Backend**: [backend/CLAUDE.md](backend/CLAUDE.md) and [backend/README.md](backend/README.md)
- **Frontend**: [admin-frontend/CLAUDE.md](admin-frontend/CLAUDE.md) and [admin-frontend/README.md](admin-frontend/README.md)
- **Testing**: [backend/tests/README.md](backend/tests/README.md)
