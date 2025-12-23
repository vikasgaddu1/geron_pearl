# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PEARL is a **full-stack research data management system** with real-time WebSocket updates:
- **Backend**: FastAPI + async PostgreSQL + WebSocket broadcasting
- **Frontend**: Modern React + TypeScript + Tailwind CSS + shadcn/ui
- **Real-time**: Live data synchronization across multiple users and browsers

## Quick Start

```bash
# Backend (Terminal 1)
cd backend
uv pip install -r requirements.txt
uv run python -m app.db.init_db
uv run python run.py

# Frontend (Terminal 2)
cd react-frontend
npm install
npm run dev

# Access: Backend http://localhost:8000 | Frontend http://localhost:5173 | Docs http://localhost:8000/docs
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
cd react-frontend
npm run dev                               # Start development server
npm install                               # Install dependencies
npm run build                             # Build for production
npm run lint                              # Lint code
```

### Stop Processes (Windows)
```bash
netstat -ano | findstr :8000              # Find backend PID
netstat -ano | findstr :5173              # Find frontend PID
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
├── react-frontend/
│   ├── src/api/        # API client and endpoints
│   ├── src/components/ # Reusable UI components
│   ├── src/features/   # Feature modules
│   └── src/stores/     # Zustand state management
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

### Frontend (React)
- **Environment Variables**: Use `VITE_` prefix for environment variables
- **Form Validation**: React Hook Form + Zod for type-safe validation
- **Component Pattern**: Functional components with custom hooks
- **State Management**: Zustand for global state, TanStack Query for server state
- **WebSocket Events**: Real-time updates via WebSocket manager

### Database Migrations
```bash
# After modifying models
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head
uv run python tests/validator/run_model_validation.py
```

## Adding a New Entity

1. **Backend**: Create model → schema → CRUD class → API endpoints with WebSocket broadcasts
2. **Frontend**: Create API endpoint → feature component → add to routing
3. **WebSocket**: Add broadcast functions and event types
4. **Testing**: Create functional test script like `test_crud_simple.sh`

## Common Issues

| Issue | Solution |
|-------|----------|
| WebSocket not updating | Check browser console; verify WebSocket connection and message types |
| React component not re-rendering | Check TanStack Query cache invalidation and dependencies |
| Batch tests failing | Expected behavior; use individual test scripts |
| Model validation errors | Run `uv run python tests/validator/run_model_validation.py` |
| TypeScript errors | Run `npm run build` to check type errors |

## Technology Stack

### Backend
- Python 3.11+ with UV package manager
- FastAPI 0.111+ with async/await
- SQLAlchemy 2.0 async + PostgreSQL
- Pydantic v2, Alembic migrations
- Black + isort + flake8 + mypy

### Frontend
- React 18 with TypeScript
- Vite for development and builds
- Tailwind CSS + shadcn/ui components
- TanStack Query + TanStack Table
- WebSocket client for real-time updates

## Component Documentation

- **Backend**: [backend/CLAUDE.md](backend/CLAUDE.md) and [backend/README.md](backend/README.md)
- **Frontend**: [react-frontend/README.md](react-frontend/README.md)
- **Testing**: [backend/tests/README.md](backend/tests/README.md)
