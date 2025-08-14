# PEARL Project Context for BMAD-METHOD

## Project Overview
PEARL is a full-stack application for managing clinical study packages and reporting efforts.

## Technology Stack

### Backend (Python/FastAPI)
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Validation**: Pydantic
- **Database**: PostgreSQL
- **Migrations**: Alembic
- **Package Manager**: uv
- **Python Version**: 3.11+

### Frontend (R/Shiny)
- **Framework**: R Shiny
- **UI Library**: bslib (Bootstrap 5)
- **Package Manager**: renv
- **Real-time Updates**: WebSocket
- **Architecture**: Modular (separate UI/server files)

## Core Entities

1. **Study**: Research studies container
2. **Package**: Collections of deliverables within studies
3. **PackageItem**: Individual items (TLFs) within packages
4. **ReportingEffort**: Tracking effort for reporting activities
5. **User**: System users with roles and permissions
6. **TextElement**: Reusable text components (titles, footnotes, etc.)

## Key Features

- Study management with hierarchical structure
- Package and item management with bulk operations
- Reporting effort tracking with comments
- Real-time updates via WebSocket
- Audit trail for all operations
- Role-based access control
- Excel/CSV import/export capabilities

## API Structure

Base URL: `http://localhost:8000/api/v1/`

Key endpoints:
- `/studies` - Study CRUD operations
- `/packages` - Package management
- `/package-items` - Item operations including bulk
- `/reporting-efforts` - Effort tracking
- `/users` - User management
- `/websocket` - Real-time updates

## Current Development Branch
`feature/reporting-effort-tracker`

## Enhancement Opportunities

1. **Export Functionality**: Add comprehensive Excel/PDF export for all entities
2. **Dashboard Analytics**: Create visual analytics for packages and efforts
3. **Performance Optimization**: Improve WebSocket message handling
4. **Bulk Operations**: Extend bulk operations to more entities
5. **Advanced Filtering**: Add complex filtering and search capabilities
6. **Notification System**: Add email/in-app notifications for important events

## Getting Started with BMAD Agents

When using BMAD agents, provide this context and then specify:
1. What specific feature or fix you want to implement
2. Any constraints (timeline, compatibility requirements)
3. Preferred approach (incremental vs comprehensive)

Example agent commands:
- `@pm *create-brownfield-prd` - Create requirements for enhancements
- `@architect *document-project` - Document existing architecture
- `@dev *develop-story {story-name}` - Implement a specific story
