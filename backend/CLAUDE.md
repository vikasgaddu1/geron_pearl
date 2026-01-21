# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PEARL Backend is a FastAPI application with async PostgreSQL CRUD operations and real-time WebSocket updates for research data management.

**Tech Stack**: FastAPI + async SQLAlchemy 2.0 + PostgreSQL + WebSocket broadcasting + UV package manager

## Essential Commands

```bash
# Install dependencies
uv pip install -r requirements.txt

# Initialize database
uv run python -m app.db.init_db

# Start development server
uv run python run.py

# Database migrations
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head

# Code quality (run before commits)
make format   # Black + isort
make lint     # flake8 + mypy

# Functional testing (server must be running)
./tests/scripts/test_crud_simple.sh
./tests/scripts/test_packages_crud.sh
./tests/scripts/test_reporting_effort_tracker_crud.sh
./tests/scripts/test_comments_crud.sh

# Model validation (required after model/schema changes)
uv run python tests/validator/run_model_validation.py
```

## Critical Constraint: Testing

**SQLAlchemy async session conflicts prevent reliable batch test execution.**

- Individual tests work perfectly
- Batch test execution frequently fails
- This is NOT a bug but an architectural constraint

**Testing approach**:
- Use curl-based test scripts (`./tests/scripts/*.sh`) - they test real HTTP endpoints
- For pytest, run individual files only: `pytest tests/specific_test.py -v`
- Success metric: Individual test reliability, not batch pass rates

## Architecture

**Clean Architecture layers** (never bypass CRUD layer):
```
API Layer (app/api/v1/)     → FastAPI endpoints with dependency injection
CRUD Layer (app/crud/)       → Business logic and database operations
Models Layer (app/models/)   → SQLAlchemy ORM models with relationships
Schemas Layer (app/schemas/) → Pydantic models for validation/serialization
DB Layer (app/db/)           → Database configuration and session management
```

### Data Model Hierarchy

```
Study (1) ←→ (N) DatabaseRelease (1) ←→ (N) ReportingEffort (1) ←→ (N) ReportingEffortItem
                                                                           ↓
                                                              ReportingEffortItemTracker
                                                                           ↓
                                                                   TrackerComment

Package (1) ←→ (N) PackageItem (polymorphic: TLF/Dataset)
                        ↓
              PackageTlfDetails / PackageDatasetDetails
              PackageItemFootnotes / PackageItemAcronyms

TextElement (standalone: title, footnote, population_set, acronyms_set, ich_category)
User (admin, analyst, viewer roles)
Notification (user_id, tracker_id, type: assignment_prod/assignment_qc/comment_added)
AuditLog (tracks all entity changes)

# Multi-tenant entities
Tenant (organization isolation)
Subscription (billing, Stripe integration)
SuperAdmin (platform-level administration)
```

### API Endpoints

| Prefix | Entity | Notes |
|--------|--------|-------|
| `/api/v1/auth` | Authentication | Login, logout, OAuth2, password reset |
| `/api/v1/studies` | Studies | Root entity, deletion protected |
| `/api/v1/database-releases` | Database Releases | Linked to studies |
| `/api/v1/reporting-efforts` | Reporting Efforts | Linked to database releases, lock system |
| `/api/v1/reporting-effort-items` | Reporting Effort Items | TLFs/Datasets in efforts |
| `/api/v1/reporting-effort-tracker` | Tracker Assignments | Production/QC tracking |
| `/api/v1/tracker-comments` | Comments | Thread support, resolution status |
| `/api/v1/tracker-tags` | Tracker Tags | Tag management for trackers |
| `/api/v1/milestones` | Milestones | Phases and milestones for efforts |
| `/api/v1/use-cases` | Use Cases | Use case assignments |
| `/api/v1/packages` | Packages | TLF/Dataset organization |
| `/api/v1/text-elements` | Text Elements | Titles, footnotes, populations, acronyms |
| `/api/v1/users` | Users | Role-based access |
| `/api/v1/notifications` | Notifications | User alerts for assignments/comments |
| `/api/v1/audit-trail` | Audit Logs | Change tracking (admin-only) |
| `/api/v1/analytics` | Analytics | Director dashboard metrics |
| `/api/v1/billing` | Billing | Subscription management, Stripe webhooks |
| `/api/v1/super-admin` | Super Admin | Platform admin (MFA, impersonation) |
| `/api/v1/tenant` | Tenant Data | Tenant management, sample data |
| `/api/v1/system` | System | Health, version, tenant info |
| `/api/v1/error-logs` | Error Logs | Error log viewing (admin-only) |
| `/api/v1/ws` | WebSocket | Real-time updates |

## Mandatory Patterns

### Deletion Protection

All entity deletions MUST check for dependent relationships:

```python
# In API endpoint before deletion
associated_items = await dependent_crud.get_by_parent_id(db, parent_id=entity_id)
if associated_items:
    raise HTTPException(
        status_code=400,
        detail=f"Cannot delete {entity}: {len(associated_items)} associated {dependent_type}(s) exist. Delete them first."
    )
```

### WebSocket Broadcasting

All CRUD operations MUST trigger WebSocket broadcasts:

```python
# After successful CRUD operation
created_entity = await entity_crud.create(db, obj_in=entity_in)
await broadcast_entity_created(created_entity)  # Required for real-time sync
```

**WebSocket data conversion**: SQLAlchemy models don't have `model_dump()`. Convert in broadcast functions:
```python
Schema.model_validate(sqlalchemy_model).model_dump(mode='json')
```

### Authorization

**⚠️ CRITICAL**: All mutating endpoints (create/update/delete) MUST have backend authorization checks. Frontend restrictions alone are NOT sufficient - users can bypass the UI and call APIs directly.

```python
# 1. Admin-only endpoints (users, settings, backup, study create/delete)
from app.core.security import require_admin

@router.post("/")
async def create_user(
    ...,
    current_user: User = Depends(require_admin()),
):
    # Only global admins can access

# 2. Study-scoped resources (database releases, reporting efforts, items, trackers)
from app.core.study_permissions import require_study_lead_access
from app.core.security import get_current_user

@router.post("/")
async def create_entity(
    ...,
    current_user: User = Depends(get_current_user),
):
    # Check AFTER fetching entity to get study_id
    await require_study_lead_access(db, current_user, entity.study_id)
    # Requires: user is admin OR has LEAD role for this specific study

# 3. Global resources (packages, text elements)
from app.core.security import require_admin_or_lead

@router.post("/")
async def create_package(
    ...,
    current_user: User = Depends(require_admin_or_lead()),
):
    # Requires: user is admin OR has LEAD role in ANY study
```

**Authorization helpers** (in `app/core/`):
| Function | Location | Use Case |
|----------|----------|----------|
| `get_current_user` | `security.py` | Get authenticated user (required for all protected endpoints) |
| `require_admin()` | `security.py` | Admin-only endpoints (users, settings, backup, study create/delete) |
| `require_admin_or_lead()` | `security.py` | Global resources manageable by any LEAD (packages, text elements) |
| `require_study_lead_access()` | `study_permissions.py` | Study-scoped resources (releases, efforts, items, trackers) |

**Endpoint Authorization Matrix:**
| Endpoint | Authorization |
|----------|--------------|
| `/users/*` | `require_admin()` |
| `/studies` POST/DELETE | `require_admin()` |
| `/studies/{id}` PUT | `require_study_lead_access()` |
| `/database-releases/*` | `require_study_lead_access()` |
| `/reporting-efforts/*` | `require_study_lead_access()` |
| `/reporting-effort-items/*` | `require_study_lead_access()` |
| `/reporting-effort-tracker/*` | `get_current_user` (read), study role check (write) |
| `/tracker-comments/*` | `get_current_user` (all endpoints require auth) |
| `/tracker-tags/*` | `get_current_user` (read), `require_admin_or_lead()` (write) |
| `/use-cases/*` | `get_current_user` (read), `require_admin_or_lead()` (write) |
| `/milestones/*` | `get_current_user` (read), `require_admin_or_lead()` (write) |
| `/packages/*` | `require_admin_or_lead()` |
| `/text-elements/*` | `require_admin_or_lead()` |
| `/settings/*` | `require_admin()` |
| `/database-backup/*` | `require_admin()` |

### CRUD Class Interface

All CRUD classes follow this pattern:
```python
class EntityCRUD:
    async def create(self, db: AsyncSession, *, obj_in: CreateSchema) -> Model
    async def get(self, db: AsyncSession, *, id: int) -> Optional[Model]
    async def get_multi(self, db: AsyncSession, *, skip: int, limit: int) -> List[Model]
    async def update(self, db: AsyncSession, *, db_obj: Model, obj_in: UpdateSchema) -> Model
    async def delete(self, db: AsyncSession, *, id: int) -> Optional[Model]
    async def get_by_parent_id(self, db, *, parent_id: int) -> List[Model]  # For deletion checks
```

## Key Implementation Details

### Enum Handling

Enums must be serialized for WebSocket broadcasts:
```python
# In app/utils.py - json_serializer() and sqlalchemy_to_dict()
if isinstance(obj, Enum):
    return obj.value
```

### WebSocket Endpoints

Use manual session management (dependency injection unreliable with WebSocket):
```python
# CORRECT
async with AsyncSessionLocal() as db:
    data = await crud.get_multi(db, skip=0, limit=100)

# INCORRECT - don't use Depends(get_db) with WebSocket
```

### Schema-Model Alignment

Pydantic schemas MUST match SQLAlchemy model field types exactly. Run model validator after changes:
```bash
uv run python tests/validator/run_model_validation.py
```

Common issues:
- `priority` as `String` in model but `int` in schema → validation error
- Enum objects vs string values → use `use_enum_values=True` in ConfigDict
- Eager loading with detached instances → remove unnecessary `selectinload`

## Test Scripts Reference

All test scripts in `tests/scripts/`:

| Script | Purpose |
|--------|---------|
| `test_crud_simple.sh` | Core CRUD for studies |
| `test_packages_crud.sh` | Package management |
| `test_reporting_effort_tracker_crud.sh` | Tracker operations |
| `test_comments_crud.sh` | Comment system |
| `test_study_deletion_protection_fixed.sh` | Deletion protection |
| `test_users_crud.sh` | User management |
| `test_audit_logging.sh` | Audit trail |

## Debugging

### HTTP 500 Errors

1. Add verbose logging to endpoint
2. Test CRUD directly with `Schema.model_validate(result)`
3. Run model validator
4. Check for: ResponseValidationError, DetachedInstanceError, enum serialization

### WebSocket Issues

1. Check browser console for connection errors
2. Verify backend logs for broadcast messages
3. Test with `uv run python tests/integration/test_websocket_broadcast.py`

## Make Commands

```bash
make help           # Show all commands
make format         # Black + isort
make lint           # flake8 + mypy
make test-fast      # Fast tests (excludes slow)
make test-coverage  # Tests with coverage
make migrate        # Apply alembic migrations
make clean          # Remove generated files
make check-all      # lint + typecheck + test-fast
make validate       # Full validation pipeline
```
