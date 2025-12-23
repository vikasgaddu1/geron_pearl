# PEARL - Research Data Management System

A full-stack research data management platform with real-time collaboration features.

## Overview

PEARL is a comprehensive system for managing clinical study packages and reporting efforts, featuring:

- **Backend**: FastAPI with async PostgreSQL and real-time WebSocket broadcasting
- **Frontend**: Modern React with TypeScript, Tailwind CSS, and shadcn/ui components
- **Real-time**: Live data synchronization across multiple users and browser sessions
- **Enterprise Features**: Audit logging, role-based access, bulk operations

## Quick Start

### Prerequisites
- Python 3.11+ with [UV package manager](https://docs.astral.sh/uv/)
- Node.js 18+ with npm
- PostgreSQL 13+

### 1. Start Backend (Terminal 1)
```bash
cd backend
uv pip install -r requirements.txt
uv run python -m app.db.init_db
uv run python run.py
```

### 2. Start Frontend (Terminal 2)
```bash
cd react-frontend
npm install
npm run dev
```

### 3. Access Applications
- **Frontend UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Architecture

```
PEARL/
├── backend/                    # FastAPI + PostgreSQL + WebSocket
│   ├── app/api/v1/            # REST endpoints + real-time broadcasting  
│   ├── tests/                 # Individual test scripts
│   └── [README.md, CLAUDE.md] # Backend documentation
├── react-frontend/            # React + TypeScript + Tailwind CSS
│   ├── src/api/               # API client and endpoints
│   ├── src/components/        # Reusable UI components
│   ├── src/features/          # Feature modules
│   └── README.md              # Frontend documentation
└── CLAUDE.md                  # Primary development guide
```

## Core Entities

- **Study**: Research studies container with hierarchical management
- **Package**: Collections of deliverables (TLFs/datasets) within studies  
- **ReportingEffort**: Effort tracking with real-time status updates
- **TextElement**: Reusable text components (titles, footnotes, acronyms)
- **User**: Role-based access control (admin, analyst, viewer)

## Key Features

### Real-time Collaboration
- **Cross-browser synchronization**: Changes appear instantly across all open sessions
- **Universal CRUD Manager**: Intelligent conflict detection and resolution
- **WebSocket broadcasting**: All create/update/delete operations trigger real-time events
- **Context-aware updates**: User activity detection prevents disrupting active work

### Modern UI/UX
- **Bootstrap 5**: Modern responsive design with dark/light mode support
- **Interactive tables**: Sortable, filterable data tables with inline actions
- **Form validation**: Deferred validation with shinyvalidate
- **Status indicators**: Always-visible WebSocket and API health monitoring

### Enterprise Grade
- **Audit logging**: Complete change tracking with user context and timestamps
- **Deletion protection**: Comprehensive dependency checking before destructive operations
- **Bulk operations**: High-performance batch processing for large datasets
- **CASCADE DELETE migration**: Ready-to-deploy solution for referential integrity

## Development Guide

### Essential Commands

**Backend Development:**
```bash
cd backend
uv run python run.py                     # Start development server
./test_crud_simple.sh                    # Run functional tests
make format && make lint                 # Code quality
uv run alembic upgrade head              # Apply migrations
```

**Frontend Development:**
```bash
cd react-frontend  
npm run dev                              # Start development server
npm install                              # Install dependencies
npm run build                            # Build for production
npm run lint                             # Lint code
```

### Critical Development Constraints

⚠️ **SQLAlchemy Async Sessions**: Individual tests work perfectly; batch test execution will fail due to session conflicts. This is an architectural constraint, not a bug.

🛡️ **Deletion Protection**: ALL entity deletions must implement dependency checking to prevent orphaned records.

📡 **WebSocket Broadcasting**: ALL CRUD operations must trigger real-time broadcasts for cross-browser synchronization.

### Testing Strategy
- **Backend**: Use individual test scripts (`./test_crud_simple.sh`, etc.)
- **Frontend**: Open multiple browser sessions to test real-time sync
- **Integration**: Run `test_websocket_broadcast.py` for end-to-end testing

## Component Documentation

For detailed information, see component-specific documentation:

- **[CLAUDE.md](CLAUDE.md)** - Primary development guide with patterns and constraints
- **[Backend](backend/README.md)** - FastAPI setup, API endpoints, database schema
- **[Frontend](react-frontend/README.md)** - React setup, component architecture, WebSocket integration
- **[Testing](backend/tests/README.md)** - Test suite setup and troubleshooting

## Technology Stack

### Backend
- **FastAPI** 0.111+ with async/await patterns
- **SQLAlchemy** 2.0 async ORM with PostgreSQL
- **Pydantic** v2 for request/response validation
- **UV** for fast Python package management
- **Alembic** for database migrations

### Frontend  
- **React 18** with TypeScript for type-safe development
- **Vite** for fast development and optimized builds
- **Tailwind CSS** with shadcn/ui for modern component design
- **TanStack Query** for data fetching and caching
- **TanStack Table** for advanced data tables with filtering
- **WebSocket** client for real-time updates

### Database Schema
```
Study (1) ↔ (N) DatabaseRelease (1) ↔ (N) ReportingEffort (1) ↔ (N) ReportingEffortItem
  ↑                                              ↓                          ↓
  └────────────── (1) ↔ (N) ──────────────────┘                   ReportingEffortItemTracker

Package (1) ↔ (N) PackageItem (polymorphic: TLF/Dataset)
  ↑                     ↓
  └─── TextElement ────┘ (footnotes, acronyms via junction tables)
```

## Getting Help

1. **Development Issues**: Check [CLAUDE.md](CLAUDE.md) for patterns and constraints
2. **API Problems**: Verify backend health at http://localhost:8000/health  
3. **WebSocket Issues**: Check browser console and backend logs for connection errors
4. **Database Issues**: Run model validator after schema changes
5. **Testing Problems**: Use individual test scripts due to async session constraints

## Recent Achievements

✅ **Cross-browser WebSocket synchronization** - Complete solution implemented  
✅ **Universal CRUD Manager** - Intelligent conflict detection and resolution  
✅ **CASCADE DELETE migration** - Comprehensive referential integrity solution ready  
✅ **Deletion protection** - Dependency checking across all entities  
✅ **Audit logging** - Complete change tracking with user context  
✅ **Deferred validation** - Improved UX with validation only on Save/Submit  

---

**For comprehensive development guidance, patterns, and troubleshooting, see [CLAUDE.md](CLAUDE.md)**
