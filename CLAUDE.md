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

**Audit Logging** - ALL CRUD operations on major entities must log to audit trail:
```python
from app.crud import audit_log

# After successful CRUD operation
await audit_log.log_action(
    db,
    table_name="entity_name",
    record_id=entity.id,
    action="CREATE",  # or "UPDATE", "DELETE"
    user_id=current_user.id,
    changes={"field": "value"},
    ip_address=request.client.host if request.client else None,
    user_agent=request.headers.get("user-agent")
)
```
**Entities with audit logging**: Studies, Database Releases, Reporting Efforts, Users, Packages, Text Elements, Reporting Effort Items, Reporting Effort Trackers

## Essential Commands

### Backend
```bash
cd backend
uv run python run.py                                   # Start server (port 8000)
uv run alembic upgrade head                            # Apply migrations
uv run alembic revision --autogenerate -m "msg"        # Create migration
uv run python tests/validator/run_model_validation.py  # Validate models after changes
make format && make lint                               # Code quality (required before commits)
make check-all                                         # Format + lint + typecheck
make clean                                             # Remove __pycache__ and generated files
```

### Backend Testing (curl-based, run from `backend/`)

**Automated API Tests** (requires Git Bash or WSL on Windows):
```bash
# Pre-requisite: Server must be running
uv run python run.py

# Run from backend/ directory using Git Bash or WSL:
./tests/scripts/test_crud_simple.sh                    # Core CRUD for studies
./tests/scripts/test_packages_crud.sh                  # Package management  
./tests/scripts/test_reporting_effort_tracker_crud.sh  # Tracker operations
./tests/scripts/test_comments_crud.sh                  # Comment system
./tests/scripts/test_users_crud.sh                     # User management
./tests/scripts/test_audit_logging.sh                  # Audit trail
./tests/scripts/test_study_deletion_protection.sh      # Deletion protection
./tests/scripts/test_database_releases_crud.sh         # Database releases
./tests/scripts/test_role_based_permissions.sh         # Role access control
./tests/scripts/test_preflight_comprehensive.sh        # Full pre-flight suite
```

**Run All Automated Tests (Pre-flight)**:
```bash
# Using Git Bash or WSL on Windows
cd backend
bash ./tests/scripts/test_preflight_comprehensive.sh
```

**Note**: All test scripts require bash. On Windows, use Git Bash or WSL.

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
# Recommended: Use stop_all.bat to stop servers and clear Python cache
./stop_all.bat

# Manual process termination
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
│       ├── features/     # Feature modules (dashboard, packages, reporting, audit-logs, etc.)
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
- **Date Formatting**: Use `formatDateTime()` from `@/lib/utils` - handles UTC timestamps from backend

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
| Code changes not taking effect | Clear Python cache: run `stop_all.bat` or manually delete `__pycache__` dirs |
| New endpoints return 404 | Hot-reload limitation - do full server restart (see below) |
| API returns old data after code changes | Kill ALL Python processes and restart (see below) |
| Frontend API calls fail with ERR_CONNECTION_REFUSED | Ensure frontend dev server is running: `.\start_react_frontend.bat` |

### ⚠️ Uvicorn Hot-Reload Limitation (Windows)

**Problem**: When adding NEW endpoints or modifying module-level functions (like `serialize_*` functions), uvicorn's hot-reload may NOT pick up the changes properly.

**Root Cause**: 
- When `reporting_efforts.py` changes, WatchFiles reimports that module (new `router` object created)
- BUT `__init__.py` is NOT reimported, so `api_router` still references the **old** router
- Result: New endpoints return 404, modified functions return old data

**Symptoms**:
- Module-level print statements appear in logs (module is reimported)
- Function-level print statements do NOT appear (old function still in use)
- New endpoints return 404 even though code exists
- Modified serialize functions return old field structure

**Solution**:
1. For structural changes (new endpoints, new fields in serialize functions), do a **full server restart**
2. Kill ALL Python processes: `Get-Process python* | Stop-Process -Force`
3. Clear cache and restart: `.\stop_all.bat` then `.\start_backend.bat`

**Hot-reload DOES work for**: Changes inside existing endpoint functions (e.g., modifying query logic)

## Claude Code Skills

Two custom skills are available for feature development:

| Skill | Description | Use When |
|-------|-------------|----------|
| `/pearl-backend-dev` | FastAPI backend development patterns | Creating endpoints, CRUD classes, models, schemas |
| `/pearl-frontend-dev` | React frontend development patterns | Creating components, forms, tables, API integration |

These skills provide detailed code templates following project standards.

## Testing Strategy

### Automated vs Manual Testing

| Test Category | Automated | Manual | Notes |
|--------------|-----------|--------|-------|
| User CRUD | ✅ | Verify UI | `test_users_crud.sh` |
| Study Hierarchy CRUD | ✅ | Verify UI | `test_crud_simple.sh`, `test_database_releases_crud.sh` |
| Package Management | ✅ | Verify UI | `test_packages_crud.sh` |
| Tracker Workflow | ✅ | Verify status badges | `test_reporting_effort_tracker_crud.sh` |
| Comments | ✅ | Verify threading UI | `test_comments_crud.sh` |
| Deletion Protection | ✅ | Verify error messages | `test_study_deletion_protection.sh` |
| Role-Based Access | ✅ | Verify menu visibility | `test_role_based_permissions.sh` |
| Audit Logging | ✅ | Verify entries | `test_audit_logging.sh` |
| Duplicate Prevention | ✅ | Verify error messages | All CRUD scripts |
| WebSocket Real-time | ❌ | Two-browser test | Requires human verification |
| Notifications UI | ❌ | Check bell icon | Requires human verification |
| UI/UX Verification | ❌ | Visual inspection | Button states, menu visibility |

### Running Automated Tests

**Pre-requisites:**
1. Backend server running: `cd backend && uv run python run.py`
2. Bash shell (Git Bash or WSL on Windows)

**Run comprehensive pre-flight test:**
```bash
cd backend
bash ./tests/scripts/test_preflight_comprehensive.sh
```

**Run individual test suites:**
```bash
cd backend
bash ./tests/scripts/test_crud_simple.sh           # Studies
bash ./tests/scripts/test_users_crud.sh            # Users  
bash ./tests/scripts/test_packages_crud.sh         # Packages
bash ./tests/scripts/test_comments_crud.sh         # Comments
bash ./tests/scripts/test_audit_logging.sh         # Audit logs
```

### Manual Testing Guide

For comprehensive human testing, see:
- **Full Guide**: [docs/MANUAL_TESTING_GUIDE.md](docs/MANUAL_TESTING_GUIDE.md) - 145 test cases with detailed steps
- **Checklist**: [docs/MANUAL_TEST_CHECKLIST.md](docs/MANUAL_TEST_CHECKLIST.md) - Printable with automated/manual indicators

**Manual testing focuses on:**
1. WebSocket real-time sync (two browsers)
2. UI role permissions (menu/button visibility)
3. Notification bell UI
4. Complex multi-step workflows
5. Visual confirmations of state changes

### Test Data for Manual Testing

| Entity | Test Data |
|--------|-----------|
| Users | `test_lead` / `LeadPass123!`, `test_editor` / `EditorPass123!`, `test_viewer` / `ViewerPass123!` |
| Studies | `TEST-001`, `TEST-002` |
| DB Releases | `DBR-001` (2026-01-15), `DBR-002` (2026-02-15) |
| Packages | `PKG-SAFETY-001`, `PKG-EFFICACY-001` |
| Text Elements | Title: `Safety Summary`, Footnote: `AE Source`, Population: `SAFFL` |

## Component Documentation

- **Backend**: [backend/CLAUDE.md](backend/CLAUDE.md) - API patterns, CRUD interface, debugging
- **Frontend**: [react-frontend/CLAUDE.md](react-frontend/CLAUDE.md) - React patterns, TanStack Query, forms
- **Testing**: [backend/tests/README.md](backend/tests/README.md) - Curl-based test philosophy
- **Manual Testing**: [docs/MANUAL_TESTING_GUIDE.md](docs/MANUAL_TESTING_GUIDE.md) - Human tester guide

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
| Study Member Management | Audit Logs |
| | Other users' studies |

## Audit Log System

Admin-only feature for tracking all system changes:
- **Frontend**: `/audit-logs` route (admin-only, accessible from sidebar)
- **Backend**: `/api/v1/audit-trail/` endpoints
- **Features**: Filter by action type, entity type, user, date range; view detailed change history
- **Logged Actions**: CREATE, UPDATE, DELETE on all major entities

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

## WebSocket Message Types

All WebSocket messages follow the format `{type}_created`, `{type}_updated`, or `{type}_deleted`:

| Entity | Created | Updated | Deleted |
|--------|---------|---------|---------|
| Study | `study_created` | `study_updated` | `study_deleted` |
| Database Release | `database_release_created` | `database_release_updated` | `database_release_deleted` |
| Reporting Effort | `reporting_effort_created` | `reporting_effort_updated` | `reporting_effort_deleted` |
| Tracker | `reporting_effort_tracker_created` | `reporting_effort_tracker_updated` | `reporting_effort_tracker_deleted` |
| Package | `package_created` | `package_updated` | `package_deleted` |
| Text Element | `text_element_created` | `text_element_updated` | `text_element_deleted` |
| User | `user_created` | `user_updated` | `user_deleted` |
| Notification | `notification_created` | - | - |

Frontend components use `useWebSocketRefresh(['entity_prefix'], refetchCallback)` to listen for these events.
