# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **📖 For detailed component documentation, see:**  
> - **Backend**: [backend/CLAUDE.md](backend/CLAUDE.md) + [backend/README.md](backend/README.md)  
> - **Frontend**: [admin-frontend/CLAUDE.md](admin-frontend/CLAUDE.md) + [admin-frontend/README.md](admin-frontend/README.md)

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

## Quick Start

> **🚀 For complete setup and development instructions, see component-specific documentation**

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

> **🚨 See [backend/CLAUDE.md - Critical Testing Constraints](backend/CLAUDE.md#critical-testing-constraints) for complete testing limitations and patterns**

### SQLAlchemy Async Session Conflicts
**⚠️ CRITICAL**: This system cannot reliably run batch tests due to async session management issues.

**Key Points**:
- ✅ Individual tests work perfectly
- ❌ Batch test execution frequently fails  
- 📋 **MANDATORY**: Read `backend/tests/README.md` before creating ANY tests
- 🎯 **Success Metric**: Individual test reliability, not batch pass rates

### WebSocket Real-time Implementation
**📡 CRITICAL**: WebSocket integration requires specific data conversion patterns.

**Key Points**:
- SQLAlchemy models → Pydantic conversion required in broadcast functions
- Dual WebSocket clients (JavaScript primary, R secondary)
- Shiny module namespacing: `studies-websocket_*` event format
- Manual session management in WebSocket endpoints

## System Architecture

> **🏗️ For detailed project structure, API endpoints, and file organization, see component README files**

### High-Level Structure
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

### Critical System Integration Points
- **API Gateway**: `backend/app/api/v1/studies.py` (CRUD + WebSocket broadcasting)
- **WebSocket Hub**: `backend/app/api/v1/websocket.py` (connection management)
- **Frontend Integration**: `admin-frontend/modules/studies_server.R` (WebSocket event handling)
- **Real-time Client**: `admin-frontend/www/websocket_client.js` (browser WebSocket)

## For AI Agents

### Component-Specific Development
- **Backend Development**: See [backend/CLAUDE.md](backend/CLAUDE.md) for FastAPI patterns, testing constraints, and WebSocket implementation
- **Frontend Development**: See [admin-frontend/CLAUDE.md](admin-frontend/CLAUDE.md) for R Shiny patterns, WebSocket integration, and real-time updates

### Critical AI Development Guidelines
1. **Testing**: Individual tests only - batch failures are expected due to async session conflicts
2. **WebSocket**: SQLAlchemy → Pydantic conversion required in all broadcast functions  
3. **Real-time**: Test with multiple browser sessions to verify WebSocket synchronization
4. **Model Validation**: Run `backend/tests/validator/` after any model changes
5. **Documentation**: Update component README.md files for user-facing changes, CLAUDE.md for technical patterns

### Multi-Component Integration Testing
```bash
# Full system integration test
cd backend && uv run python run.py &                                    # Start backend
cd admin-frontend && Rscript run_app.R &                               # Start frontend  
cd backend && uv run python tests/integration/test_websocket_broadcast.py  # Test real-time updates
```

### Development Best Practices
- Do git commit at regular interval, we don't want to make lot of updates and then unable to go back.