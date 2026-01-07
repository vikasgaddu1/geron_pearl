# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PEARL (Pharmaceutical Execution And Reporting Landscape) is a **full-stack research data management system** with real-time WebSocket updates:
- **Backend**: FastAPI + async PostgreSQL + WebSocket broadcasting
- **Frontend**: React 18 + TypeScript + Tailwind CSS + shadcn/ui
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

# Access: Backend http://localhost:8000 | Frontend http://localhost:5173 | API Docs http://localhost:8000/docs
```

## Critical Constraints

### SQLAlchemy Async Session Conflicts
**⚠️ CRITICAL**: Batch pytest tests fail due to async session management. This is architectural, not a bug.
- ✅ Individual tests and curl-based scripts work perfectly
- ❌ Batch pytest execution fails with session conflicts
- Always use curl-based test scripts: `./tests/scripts/test_crud_simple.sh`

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

**WebSocket Data Conversion** - SQLAlchemy models don't have `model_dump()`:
```python
Schema.model_validate(sqlalchemy_model).model_dump(mode='json')
```

## Essential Commands

### Backend
```bash
cd backend
uv run python run.py                                   # Start server (port 8000)
uv run alembic upgrade head                            # Apply migrations
uv run alembic revision --autogenerate -m "msg"        # Create migration
uv run python tests/validator/run_model_validation.py  # Validate models after changes
make format && make lint                               # Code quality (required before commits)
```

### Backend Testing (curl-based, run from `backend/`)
```bash
./tests/scripts/test_crud_simple.sh                    # Core CRUD for studies
./tests/scripts/test_packages_crud.sh                  # Package management
./tests/scripts/test_reporting_effort_tracker_crud.sh  # Tracker operations
./tests/scripts/test_comments_crud.sh                  # Comment system
./tests/scripts/test_users_crud.sh                     # User management
./tests/scripts/test_audit_logging.sh                  # Audit trail
./tests/scripts/test_study_deletion_protection.sh      # Deletion protection
```
**Note**: Server must be running (`uv run python run.py`) before running tests.

### Frontend
```bash
cd react-frontend
npm run dev       # Start development server (port 5173)
npm run build     # Build for production (includes TypeScript check)
npm run lint      # ESLint
npm run preview   # Preview production build
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
│   ├── app/
│   │   ├── api/v1/       # REST endpoints + WebSocket broadcasting
│   │   ├── crud/         # Business logic (never bypass this layer)
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic validation schemas
│   │   └── db/           # Database config and session management
│   └── tests/scripts/    # Curl-based functional test scripts
├── react-frontend/
│   └── src/
│       ├── api/          # API client (axios) and endpoint functions
│       ├── components/   # Reusable UI (shadcn/ui primitives in ui/)
│       ├── features/     # Feature modules (dashboard, packages, reporting, etc.)
│       ├── stores/       # Zustand state management
│       └── types/        # TypeScript type definitions
```

### Database Schema
```
Study (1) ↔ (N) DatabaseRelease (1) ↔ (N) ReportingEffort (1) ↔ (N) ReportingEffortItem
                                                                         ↓
Package (1) ↔ (N) PackageItem (TLF/Dataset)                    ReportingEffortItemTracker
                      ↓                                            (with TrackerComment)
              TextElement (title, footnote, population_set, acronyms_set)
User (admin, analyst, viewer roles) | AuditLog (change tracking)
```

## Key Development Patterns

### Backend (FastAPI)
- **Clean Architecture**: API → CRUD → Models (never bypass CRUD layer)
- **Model Changes**: Always run model validator after schema/model changes
- **Enum Serialization**: Use `use_enum_values=True` in Pydantic ConfigDict
- **WebSocket Endpoints**: Use manual session management, not `Depends(get_db)`
- **UV Package Manager**: Use `uv run` for all Python commands

### Frontend (React)
- **Environment Variables**: Use `VITE_` prefix (e.g., `VITE_API_BASE_URL`)
- **Form Validation**: React Hook Form + Zod for type-safe validation
- **State Management**: Zustand for global state, TanStack Query for server state
- **Data Tables**: TanStack Table with filtering, sorting, pagination
- **Real-time Updates**: WebSocket manager with auto-reconnect

### Database Migrations
```bash
# After modifying models
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head
uv run python tests/validator/run_model_validation.py
```

## Adding a New Entity

1. **Backend**: Create model → schema → CRUD class → API endpoints with WebSocket broadcasts
2. **Frontend**: Create API endpoint in `src/api/endpoints/` → feature component → add to routing
3. **WebSocket**: Add broadcast functions for create/update/delete operations
4. **Testing**: Create curl-based test script in `tests/scripts/`

## Common Issues

| Issue | Solution |
|-------|----------|
| WebSocket not updating | Check browser console; verify connection and message types |
| HTTP 500 errors | Check schema-model alignment; run model validator |
| Batch tests failing | Expected behavior; use individual curl-based test scripts |
| Model validation errors | Run `uv run python tests/validator/run_model_validation.py` |
| TypeScript errors | Run `npm run build` to check type errors |
| Enum serialization error | Add `use_enum_values=True` to Pydantic ConfigDict |

## Component Documentation

- **Backend**: [backend/CLAUDE.md](backend/CLAUDE.md) - API patterns, CRUD interface, debugging
- **Frontend**: [react-frontend/CLAUDE.md](react-frontend/CLAUDE.md) - React patterns, TanStack Query, forms
- **Testing**: [backend/tests/README.md](backend/tests/README.md) - Curl-based test philosophy

## Authentication

JWT-based authentication with refresh tokens:
- Access token: Short-lived, sent in `Authorization: Bearer` header
- Refresh token: Long-lived, used to obtain new access tokens
- Roles: `admin` (full access), `analyst` (edit), `viewer` (read-only)
- Study-scoped roles: `LEAD`, `EDITOR`, `VIEWER` per study
