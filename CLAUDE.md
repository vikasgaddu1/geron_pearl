# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **📖 For detailed component documentation, see:**  
> - **Backend**: [backend/CLAUDE.md](backend/CLAUDE.md) + [backend/README.md](backend/README.md)  
> - **Frontend**: [admin-frontend/CLAUDE.md](admin-frontend/CLAUDE.md) + [admin-frontend/README.md](admin-frontend/README.md)

## Recent Changes (December 2024)

### Frontend - Module Consolidation
- **Change**: Removed individual Studies, Database Releases, and Reporting Efforts modules
- **Reason**: All functionality is now handled by the Study Tree module with hierarchical view
- **Impact**: Cleaner codebase, unified interface for managing all three entity types
- **Files Removed**: `studies_*.R`, `database_releases_*.R`, `reporting_efforts_*.R`

### Frontend - Study Tree Selection Fix
- **Issue**: Study tree had selection ambiguity when study and database release had same name (e.g., "test")
- **Root Cause**: Previous implementation used formatted selection methods that couldn't distinguish node depth
- **Solution**: Implemented proper path-based selection using shinyTree's `stselected` attribute
- **Implementation**: Added `find_selected_paths()` helper function that recursively traverses tree structure
- **Impact**: Now correctly identifies node type (Study/DB Release/Effort) based on path depth, even with duplicate names

### Frontend - Form Validation UX Improvements (January 2025)
- **Issue**: Form validation triggered immediately when modals opened, showing errors before users could type
- **Root Cause**: `InputValidator$enable()` was called when modals opened instead of on save
- **Solution**: Implemented deferred validation pattern - only enable validation when Save/Create buttons clicked
- **Impact**: Better user experience with validation only when attempting to save
- **Modules Fixed**: Study Tree (Add Study, Add Child), TNFP (Edit modal)

## Project Overview

PEARL is a **full-stack research data management system** with real-time WebSocket updates:

### System Components
- **Backend**: FastAPI + async PostgreSQL + WebSocket broadcasting ([backend/](backend/))
- **Frontend**: Modern R Shiny + bslib + dual WebSocket clients ([admin-frontend/](admin-frontend/))  
- **Real-time**: WebSocket synchronization across multiple users and browsers

### Key Features
- **Modern Stack**: FastAPI 0.111+ + R Shiny with bslib + PostgreSQL + UV + renv
- **Real-time Updates**: Live data synchronization via WebSocket broadcasting
- **Production-like**: Real PostgreSQL database with specific testing constraints

## Quick Commands

### Backend Commands
```bash
cd backend

# Development
uv run python run.py                      # Start development server
uv run python -m app.db.init_db           # Initialize database

# Testing
./test_crud_simple.sh                     # Run functional CRUD tests
./test_packages_crud.sh                   # Test packages system
./test_study_deletion_protection_fixed.sh # Test deletion protection
uv run python tests/integration/test_websocket_broadcast.py  # Test WebSocket

# Code Quality
make format                               # Format with black + isort
make lint                                 # Run flake8 + mypy
make typecheck                            # Type checking only

# Database
uv run alembic upgrade head               # Apply migrations
uv run alembic revision --autogenerate -m "Description"  # Create migration
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
```

## Quick Start

### Full System Startup
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

### WebSocket Testing
```bash
# Test real-time updates (from backend directory)
cd backend && uv run python tests/integration/test_websocket_broadcast.py
```

## Critical System Constraints

### SQLAlchemy Async Session Conflicts
**⚠️ CRITICAL**: This system cannot reliably run batch tests due to async session management issues.
- ✅ Individual tests work perfectly
- ❌ Batch test execution frequently fails  
- 📋 **MANDATORY**: Read `backend/tests/README.md` before creating ANY tests
- 🎯 **Success Metric**: Individual test reliability, not batch pass rates

### WebSocket Real-time Implementation
**📡 CRITICAL**: WebSocket integration requires specific data conversion patterns.
- SQLAlchemy models → Pydantic conversion required in broadcast functions
- Dual WebSocket clients (JavaScript primary, R secondary)
- Shiny module namespacing: `studies-websocket_*` event format
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

### Critical Integration Points
- **API Gateway**: `backend/app/api/v1/studies.py` (CRUD + WebSocket broadcasting)
- **WebSocket Hub**: `backend/app/api/v1/websocket.py` (connection management)
- **Frontend Integration**: `admin-frontend/modules/studies_server.R` (WebSocket event handling)
- **Real-time Client**: `admin-frontend/www/websocket_client.js` (browser WebSocket)

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
- **Form Validation**: Use shinyvalidate for all user inputs

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