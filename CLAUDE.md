# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PEARL (Package, Effort and Analysis Reporting Library) is a **full-stack research data management system** with real-time WebSocket updates:
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
              TextElement (title, footnote, population_set, acronyms_set, ich_category)
User (admin, analyst, viewer roles) | AuditLog (change tracking) | Notification (user alerts)
```

**TextElement Field Meanings** (TFL Properties):
| Type | `label` = | `content` = |
|------|-----------|-------------|
| title/footnote | Category (Safety, Efficacy) | Actual text |
| population_set | Short form (SAFFL, ITTFL) | Full name |
| acronyms_set | Abbreviation (AE, SD) | Full form |
| ich_category | ICH Code (ICH_11.4) | Description |

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
**⚠️ MANDATORY**: Always use Alembic migrations when adding or deleting columns in existing tables. This ensures Railway deployment automatically picks up schema changes.

```bash
# After modifying models (adding/removing columns)
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head
uv run python tests/validator/run_model_validation.py
```

**Never** modify model columns without creating a migration - the deployed database won't update otherwise.

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

## Railway Deployment

### Current Production URLs
- **Backend**: `https://backend-production-2cc8.up.railway.app`
- **Frontend**: `https://frontend-production-9345.up.railway.app`

### Default Admin User
On fresh database initialization, a default admin user is created:
- **Username**: `admin`
- **Password**: `admin123`
- **⚠️ Change this password after first login!**

### Fresh Railway Setup Steps

1. **Create PostgreSQL** service first
2. **Create Backend** service:
   - Root Directory: `/backend`
   - Link PostgreSQL (creates `DATABASE_URL` automatically)
   - Add variables: `JWT_SECRET`, `ALLOWED_ORIGINS`, `FRONTEND_URL`
3. **Create Frontend** service:
   - Root Directory: `/react-frontend`
   - Add `BACKEND_URL` (with `https://` prefix!)
4. **Update nginx.railway.conf** with new backend hostname, commit & push
5. **Update backend** `ALLOWED_ORIGINS` with frontend URL

### Backend Environment Variables (5 Service Variables)

| Variable | Current Value | Notes |
|----------|---------------|-------|
| `ALLOWED_ORIGINS` | `["https://frontend-production-9345.up.railway.app"]` | **Must be valid JSON with double quotes!** |
| `DATABASE_URL` | `postgresql://postgres:...@postgres.railway.internal:5432/railway` | Auto-linked from PostgreSQL service |
| `FRONTEND_URL` | `https://frontend-production-9345.up.railway.app` | For password reset links |
| `JWT_SECRET` | `dev-secret-key-change-in-production` | **⚠️ Change in production!** |
| `POSTGRES_DB` | `railway` | Auto-set by Railway (not used by app) |

*Plus 8 variables auto-added by Railway (PGHOST, PGPORT, etc.)*

### Frontend Environment Variables (1 Service Variable)

| Variable | Current Value | Notes |
|----------|---------------|-------|
| `BACKEND_URL` | `https://backend-production-2cc8.up.railway.app` | **Must include `https://` prefix!** |

*Plus 8 variables auto-added by Railway*

**Note**: `PORT` is auto-set by Railway - don't set it manually.

### Critical Configuration Notes

**Backend PORT**: The `start.sh` uses `${PORT:-8000}` to listen on Railway's dynamic port:
```bash
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**DATABASE_URL Auto-Conversion**: The config automatically converts `postgresql://` to `postgresql+asyncpg://` for async SQLAlchemy.

**nginx Host Header**: Must match your backend's Railway hostname in `nginx.railway.conf`:
```nginx
proxy_set_header Host your-backend-name.up.railway.app;
```

### Frontend Deployment (Docker-based)
**⚠️ DO NOT use nixpacks** - it has reliability issues on Railway. Use Dockerfile instead.

**Key files:**
- `react-frontend/Dockerfile` - Multi-stage build (node:20-alpine → nginx:alpine)
- `react-frontend/nginx.railway.conf` - nginx config with API proxy
- `react-frontend/.dockerignore` - Must NOT exclude `package-lock.json`

### Common Railway Deployment Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 500 on login "invalid URL prefix" | `BACKEND_URL` missing `https://` | Add `https://` prefix to `BACKEND_URL` |
| 500 on login "JSONDecodeError" | `ALLOWED_ORIGINS` not valid JSON | Use `["https://..."]` with quotes |
| 502 "connection refused" | Backend not listening on Railway's PORT | Use `${PORT:-8000}` in start.sh |
| Database connection to localhost | `DATABASE_URL` not set or wrong name | Must be named exactly `DATABASE_URL` |
| bcrypt version error | passlib incompatible with bcrypt 4.1+ | Pin `bcrypt==4.0.1` in requirements.txt |
| Missing column errors | Model has columns not in database | Add columns to `repair_missing_columns.py` migration |
| nixpacks "context canceled" | Railway infrastructure issue | Use Dockerfile instead of nixpacks |
| 502 on API proxy | Can't resolve backend hostname | Add `resolver 8.8.8.8 8.8.4.4` to nginx |
| 502 on HTTPS proxy | SNI not enabled | Add `proxy_ssl_server_name on` |

## Authentication & Authorization

### JWT Authentication
- Access token: 15-minute expiry, sent in `Authorization: Bearer` header
- Refresh token: 7-day expiry, used to obtain new access tokens
- Token contains user identity; permissions checked from database on each request

### Role System
**Global roles** (user.is_admin flag):
- `admin`: Full system access (user management, settings, backup, all studies)

**Study-scoped roles** (user_study_roles table):
- `LEAD`: Near-admin for assigned studies - can manage releases, efforts, members, packages, TFL properties
- `EDITOR`: Can edit tracker data within assigned studies
- `VIEWER`: Read-only access to assigned studies

### Authorization Pattern
```python
# Admin-only: user management, settings, backup, study create/delete
current_user: User = Depends(require_admin())

# Study-scoped: user must be admin OR LEAD for the specific study
await require_study_lead_access(db, current_user, study_id)

# Global resources: user must be admin OR LEAD in any study
current_user: User = Depends(require_admin_or_lead())
```

**⚠️ CRITICAL**: All mutating endpoints MUST have backend authorization. Frontend restrictions alone are NOT sufficient.

## Tracker Validation Rules

**⚠️ CRITICAL**: Tracker validation rules must be applied to ALL endpoints that can modify tracker data. There are multiple ways to update trackers:

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/reporting-effort-tracker/` | Create tracker |
| `PUT /api/v1/reporting-effort-tracker/{id}` | Update single tracker |
| `POST /api/v1/reporting-effort-tracker/{id}/assign-programmer` | Assign programmer |
| `POST /api/v1/reporting-effort-tracker/bulk-assign` | Bulk assign programmers |
| `POST /api/v1/reporting-effort-tracker/bulk-status-update` | Bulk status update |
| `POST /api/v1/reporting-effort-tracker/bulk-assign-status` | Bulk assign and status |
| `POST /api/v1/reporting-effort-tracker/import/{id}` | Import trackers |

### Current Validation Rules

1. **Same Programmer Check**: Production and QC programmer cannot be the same person
2. **Due Date Check**: Due date cannot be prior to today's date for tasks that are not completed (both production and QC)
3. **Programmer Required for Status**: Cannot change production/QC status without assigned programmer (except `not_started`)
4. **QC Completion Requires No Unresolved Comments**: Cannot mark QC as completed if there are unresolved comments
5. **Production Completed Auto-Set**: Production status is auto-set to `completed` when QC marks it as completed

### Adding New Validation Rules

When adding a new validation rule:
1. Identify ALL endpoints that can modify the affected field(s)
2. Add validation to each backend endpoint (with consistent error messages)
3. Add frontend validation for immediate user feedback
4. Document the rule in this section

### LEAD Permissions
| Can Access | Cannot Access |
|------------|---------------|
| Study Management (own studies) | Director Dashboard |
| Database Releases (own studies) | User Management |
| Reporting Efforts (own studies) | Global Settings |
| Packages & TFL Properties | Database Backup |
| Study Member Management | Other users' studies |

## Notification System

Real-time notifications for user assignments and comments:

**Notification Types:**
- `assignment_prod` - Assigned as production programmer
- `assignment_qc` - Assigned as QC programmer  
- `comment_added` - New comment on items user is assigned to

**States:**
- `is_read` - User has seen the notification
- `is_acknowledged` - User has dismissed the notification (no longer shown)

**WebSocket Events:**
- `notification_created` - New notification for a user
- `notification_count_updated` - Updated unread count for a user
