# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PEARL is a **full-stack research data management system** with real-time WebSocket updates:
- **Backend**: FastAPI + async PostgreSQL + WebSocket broadcasting
- **Frontend**: Modern R Shiny + bslib + dual WebSocket clients
- **Real-time**: Live data synchronization across multiple users and browsers

## Quick Start

```bash
# 1. Backend (Terminal 1)
cd backend
uv pip install -r requirements.txt
uv run python -m app.db.init_db
uv run python run.py

# 2. Frontend (Terminal 2)  
cd admin-frontend
Rscript setup_environment.R
Rscript run_app.R

# 3. Access Applications
# Backend API: http://localhost:8000
# Frontend UI: http://localhost:3838
# API Docs: http://localhost:8000/docs
```

## Essential Commands

### Backend Commands
```bash
cd backend

# Development
uv run python run.py                      # Start development server
uv run python -m app.db.init_db           # Initialize database

# Testing
./test_crud_simple.sh                     # Run functional CRUD tests
./test_packages_crud.sh                   # Test packages system
./test_reporting_effort_tracker_crud.sh   # Test tracker CRUD operations
./test_study_deletion_protection_fixed.sh # Test deletion protection
./test_tracker_delete_simple.sh           # Test tracker deletion functionality
uv run python tests/integration/test_websocket_broadcast.py  # Test WebSocket

# Code Quality
make format                               # Format with black + isort
make lint                                 # Run flake8 + mypy
make typecheck                            # Type checking only

# Database
uv run alembic upgrade head               # Apply migrations
uv run alembic revision --autogenerate -m "Description"  # Create migration

# Cascade Migration (for orphaned records fix)
uv run python execute_cascade_migration.py  # Execute CASCADE DELETE migration
uv run python analyze_orphaned_records.py   # Analyze orphaned records
```

### Frontend Commands
```bash
cd admin-frontend

# Development
Rscript run_app.R                         # Start R Shiny app
Rscript setup_environment.R               # First-time setup

# Package Management (renv)
renv::restore()                           # Restore packages
renv::install("package")                  # Add new package
renv::snapshot()                          # Save package state

# Playwright Testing
npm test                                  # Run Playwright tests
npm run install:browsers                  # Install test browsers
```

### Stopping Running Processes (Windows)

```bash
# Find processes using specific ports
netstat -ano | findstr :8000     # Backend port
netstat -ano | findstr :3838     # Frontend port

# Kill processes by PID (use PowerShell for reliability)
powershell -Command "Stop-Process -Id <PID> -Force"

# Alternative: Kill all Python/R processes
powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force"
powershell -Command "Get-Process Rscript -ErrorAction SilentlyContinue | Stop-Process -Force"

# Quick utility scripts (from scripts/ directory)
./scripts/kill_backend.bat                # Kill backend only
./scripts/kill3838.bat                    # Kill frontend only  
./scripts/kill_all_services.bat           # Kill both services
```

## Critical System Constraints

### SQLAlchemy Async Session Conflicts
**⚠️ CRITICAL**: This system cannot reliably run batch tests due to async session management issues.
- ✅ Individual tests work perfectly
- ❌ Batch test execution frequently fails  
- 📋 **MANDATORY**: Read `backend/tests/README.md` before creating ANY tests
- 🎯 **Success Metric**: Individual test reliability, not batch pass rates

### Database Integrity & Orphaned Records
**🛡️ CASCADE DELETE MIGRATION AVAILABLE**: The system has comprehensive migration scripts ready to implement CASCADE DELETE constraints to prevent orphaned records.
- **Current State**: 31 foreign key constraints lack proper CASCADE behavior
- **Migration Ready**: `execute_cascade_migration.py` script provides complete solution
- **Analysis Available**: `analyze_orphaned_records.py` identifies current orphaned data
- **Risk Mitigation**: Automatic backup creation and rollback procedures included
- **Documentation**: See `CASCADE_DELETE_MIGRATION_PLAN.md` for complete migration strategy

### WebSocket Real-time Implementation
**📡 CRITICAL**: WebSocket integration requires specific data conversion patterns.
- SQLAlchemy models → Pydantic conversion required in broadcast functions
- Dual WebSocket clients (JavaScript primary, R secondary)
- Shiny module namespacing: `{module}-websocket_event` format
- Manual session management in WebSocket endpoints

## High-Level Architecture

```
PEARL/
├── backend/                    # FastAPI + PostgreSQL + WebSocket
│   ├── app/api/v1/            # REST endpoints + WebSocket broadcasting  
│   ├── tests/                 # Individual tests + validator
│   └── [README.md, CLAUDE.md] # Component documentation
├── admin-frontend/            # R Shiny + bslib + dual WebSocket clients
│   ├── modules/               # UI/server + API client + WebSocket
│   ├── www/                   # JavaScript WebSocket client
│   └── [README.md, CLAUDE.md] # Component documentation
└── test_websocket*.py         # Real-time testing scripts
```

## Key Development Patterns

### Backend Development (FastAPI)
- **Clean Architecture**: API → CRUD → Models with clear separation
- **Deletion Protection**: Check for dependent entities before deletion
- **WebSocket Broadcasting**: All CRUD operations trigger real-time events
- **Model Validation**: Run validator after model changes: `uv run python tests/validator/run_model_validation.py`

### Frontend Development (R Shiny)
- **Module Pattern**: UI/Server separation for all components
- **Environment Variables**: All API endpoints use Sys.getenv()
- **WebSocket Events**: Observes `{module}-websocket_event` inputs
- **Form Validation**: Use shinyvalidate with deferred validation (only on Save/Submit)

### Testing Strategy
- **Backend**: Use `./test_crud_simple.sh` for functional testing
- **Frontend**: Open multiple browser sessions to test real-time sync
- **Integration**: Run `test_websocket_broadcast.py` for end-to-end testing

## Common Development Tasks

### Adding a New Entity Type
1. **Backend**: Create model, schema, CRUD, and API endpoints
2. **Frontend**: Create UI and server modules following existing patterns  
3. **WebSocket**: Add broadcast functions and event types
4. **Testing**: Create functional test script like `test_crud_simple.sh`

### Debugging WebSocket Issues
1. Check browser console for connection errors
2. Verify backend WebSocket endpoint is running
3. Ensure message type matches expected format
4. Test with `test_websocket_broadcast.py`

### Database Schema Changes
1. Modify SQLAlchemy models in `backend/app/models/`
2. Run: `uv run alembic revision --autogenerate -m "Description"`
3. Review generated migration in `backend/migrations/versions/`
4. Apply: `uv run alembic upgrade head`
5. Run model validator: `uv run python tests/validator/run_model_validation.py`

## Git Workflow

### Commit Regularly
- Make frequent commits to track progress
- Use descriptive commit messages
- Follow conventional commit format: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`

### Before Committing
1. **Backend**: Run `make format` and `make lint`
2. **Frontend**: Ensure app runs without errors
3. **Tests**: Run relevant test scripts
4. **Documentation**: Update CLAUDE.md if patterns change

## Important Development Guidelines

### Backend Guidelines
- **Never bypass CRUD layer** - All database operations must go through CRUD classes
- **Implement deletion protection** - Check for dependent entities before deletion
- **Use UV for all Python operations** - Faster and more reliable than pip
- **Run model validator** after any model/schema changes
- **Test individually** - Use `./test_crud_simple.sh` for functional testing

### Frontend Guidelines  
- **Use environment variables** for all API endpoints
- **Follow module pattern** - UI/Server separation for all components
- **Implement deferred validation** - Only validate on Save/Submit actions
- **Test WebSocket sync** - Open multiple browser sessions
- **Use renv** for package management - Ensures reproducibility

### Testing Guidelines
- **Backend**: Focus on functional endpoint testing with curl/HTTP
- **Frontend**: Test real-time synchronization across sessions
- **Individual tests only** - Batch tests will fail due to async session conflicts
- **Use test scripts** - `test_crud_simple.sh`, `test_packages_crud.sh`, etc.

## Recent Changes

### December 2024 - Frontend Module Consolidation
- Removed individual Studies, Database Releases, and Reporting Efforts modules
- All functionality now handled by Study Tree module with hierarchical view
- Fixed Study Tree selection ambiguity with path-based selection

### January 2025 - Form Validation UX Improvements
- Form validation now only triggers when Save/Create buttons clicked
- Implemented deferred validation pattern across all modules
- Fixed TNFP Edit modal Save button issue

## MCP Tools Integration

### Playwright MCP for UI Testing
- Navigate and interact with the R Shiny application
- Test shinyTree expand/collapse and selection
- Verify WebSocket real-time synchronization
- Take screenshots for documentation

### Context7 MCP for Documentation
- Access up-to-date library documentation
- Research best practices for R Shiny and FastAPI
- Find code examples and implementation patterns

### IDE MCP Integration
- Get language diagnostics from VS Code
- Execute Python code in Jupyter kernels
- Test notebook files and data analysis workflows

## Available Claude Code Agents

### rshiny-modern-builder
Use for creating modern, API-driven R Shiny applications with modular architecture, bslib UI, httr2 API calls, and real-time WebSocket integration.

### fastapi-crud-builder
Use for building or enhancing FastAPI applications with async PostgreSQL CRUD operations, particularly for data science environments with R Shiny integration.

### fastapi-model-validator
Use for validating Pydantic and SQLAlchemy model alignment in FastAPI applications, especially after making changes to data models, schemas, or database structures.

### fastapi-simple-tester
Use for creating simple, reliable endpoint testing for FastAPI applications using curl commands that avoid complex test frameworks and database session conflicts.

## Essential Development Constraints

### File Creation Guidelines
- **NEVER create files** unless absolutely necessary for achieving your goal
- **ALWAYS prefer editing** an existing file to creating a new one  
- **NEVER proactively create** documentation files (*.md) or README files
- Only create documentation files if explicitly requested by the User

### Path Conventions (Windows)
- Use forward slashes `/` in all file paths (even on Windows)
- Backend paths: `backend/app/models/`, `backend/tests/`
- Frontend paths: `admin-frontend/modules/`, `admin-frontend/www/`

### Critical Testing Constraint
**⚠️ ABSOLUTE CRITICAL**: This codebase has documented SQLAlchemy async session conflicts that prevent reliable batch test execution. This is **NOT a bug** - it's an architectural constraint.
- Individual tests work perfectly ✅
- Batch test execution frequently fails ❌
- Always test individually: `pytest single_test.py -v`
- Success metric: Individual test reliability, not batch pass rates

### Deletion Protection Pattern (Mandatory)
**🛡️ ALL entity deletions MUST implement dependency checking**:
```python
# Pattern: Check for dependent entities before deletion
dependent_entities = await dependent_crud.get_by_parent_id(db, parent_id=entity_id)
if dependent_entities:
    entity_names = [e.label for e in dependent_entities]
    raise HTTPException(
        status_code=400,
        detail=f"Cannot delete {entity_type} '{entity.label}': {len(dependent_entities)} associated {dependent_type}(s) exist: {', '.join(entity_names)}. Please delete all associated {dependent_type}s first."
    )
```

### WebSocket Broadcasting Pattern (Required)
**📡 ALL CRUD operations MUST trigger WebSocket broadcasts**:
```python
# In API endpoints after successful operations
created_entity = await entity_crud.create(db, obj_in=entity_in)
await broadcast_entity_created(created_entity)  # Required for real-time sync
```

### Make Commands (Backend Code Quality)
```bash
# Run these commands before committing backend changes
make format     # Auto-format with black + isort (required)
make lint       # Check with flake8 + mypy (required)
make typecheck  # Type checking only
```

## Technology Stack Summary

### Backend (FastAPI)
- **Python**: 3.11+ with UV package manager
- **Framework**: FastAPI + uvicorn with async/await patterns
- **Database**: PostgreSQL with SQLAlchemy 2.0 async
- **Migrations**: Alembic for schema changes
- **Real-time**: WebSocket broadcasting via ConnectionManager
- **Validation**: Pydantic v2 for request/response schemas
- **Testing**: pytest with individual test execution only

### Frontend (R Shiny)
- **R Version**: 4.2.2 with renv for reproducible packages
- **Framework**: Shiny with bslib for modern Bootstrap 5 UI
- **HTTP Client**: httr2 for robust API communication
- **Validation**: shinyvalidate with deferred validation pattern
- **Tables**: DT for interactive data tables with search/filter
- **Real-time**: Dual WebSocket clients (JavaScript primary, R secondary)
- **Testing**: Playwright MCP for automated browser testing

### Database Schema Overview
**Hierarchical Entity Relationships**:
```
Study (1) ←→ (N) DatabaseRelease (1) ←→ (N) ReportingEffort (1) ←→ (N) ReportingEffortItem
  ↑                                              ↓                          ↓
  └────────────── (1) ←→ (N) ──────────────────┘                   ReportingEffortItemTracker
                                                                     (with TrackerComment support)

Package (1) ←→ (N) PackageItem (polymorphic: TLF/Dataset)
  ↑                     ↓
  └─── Text Elements ───┘ (footnotes, acronyms via junction tables)

TextElement (standalone: title, footnote, population_set, acronyms_set)
User (authentication: admin, analyst, viewer roles)
TrackerComment (workflow comments with threading and resolution status)
```

## For More Details

- **Backend**: See [backend/CLAUDE.md](backend/CLAUDE.md) and [backend/README.md](backend/README.md)
- **Frontend**: See [admin-frontend/CLAUDE.md](admin-frontend/CLAUDE.md) and [admin-frontend/README.md](admin-frontend/README.md)
- **Testing**: See [backend/tests/README.md](backend/tests/README.md)
- **Utility Scripts**: See [scripts/README.md](scripts/README.md) for service management
- **Database Migration**: See [backend/CASCADE_DELETE_MIGRATION_PLAN.md](backend/CASCADE_DELETE_MIGRATION_PLAN.md) for orphaned records solution
- **Tracker Delete Testing**: See [backend/TRACKER_DELETE_ENDPOINT_TESTING_RESULTS.md](backend/TRACKER_DELETE_ENDPOINT_TESTING_RESULTS.md) for delete endpoint validation
- **MCP Integration**: fastapi-mcp running at http://localhost:8000/mcp

## Recent Important Updates (August 2025)

### Tracker Delete Functionality
**✅ PRODUCTION READY**: DELETE endpoint for reporting effort tracker has been thoroughly tested
- **Endpoint**: `DELETE /api/v1/reporting-effort-tracker/{tracker_id}`
- **Features**: Comprehensive error handling, WebSocket broadcasting, audit logging
- **Testing**: Complete test coverage with `test_tracker_delete_simple.sh`
- **Status Codes**: 204 (success), 404 (not found), 422 (validation error)

### CASCADE DELETE Migration System
**🛠️ MIGRATION AVAILABLE**: Comprehensive solution for database referential integrity
- **Scripts Ready**: Complete migration with automatic backup and rollback
- **Analysis Complete**: No orphaned records currently exist in database
- **Constraints Updated**: 31 foreign key constraints need CASCADE DELETE implementation
- **Safety Features**: Pre-migration validation, post-migration testing, automated backups

### Enhanced Testing Infrastructure  
**📋 EXPANDED TEST COVERAGE**: Multiple specialized test scripts available
- **Core CRUD**: `test_crud_simple.sh` for basic functionality
- **Packages**: `test_packages_crud.sh` for package management
- **Tracker Operations**: `test_reporting_effort_tracker_crud.sh` and `test_tracker_delete_simple.sh`
- **Deletion Protection**: `test_study_deletion_protection_fixed.sh`
- **Individual Testing**: All scripts designed for individual execution due to async session constraints