# PEARL - Product Requirements Document

**Version:** 2.0  
**Date:** August 2025  
**Status:** 🚧 In Development (Phase 3 - Admin Frontend 95% Complete)

## Executive Summary

PEARL (Package, Effort, and Analysis Reporting Library) is a comprehensive research data management system designed to streamline clinical study package management and reporting effort tracking. The system provides real-time collaboration capabilities through WebSocket integration and maintains complete audit trails for regulatory compliance.

### Current Development Status
- ✅ **Phase 1:** Database Foundation - COMPLETED
- ✅ **Phase 2:** Backend API - COMPLETED  
- 🚧 **Phase 3:** Admin Frontend - 95% COMPLETE
- 📋 **Phase 4:** User Frontend - PLANNED
- 📋 **Phase 5:** Advanced Features - PLANNED

For detailed setup and development instructions, see [CLAUDE.md](../CLAUDE.md).

## Product Vision & Goals

### Vision Statement
To provide a unified, real-time platform for managing clinical research data packages and tracking reporting efforts, enabling efficient collaboration between biostatisticians, programmers, and data managers.

### Key Goals
1. **Centralize Data Management** - Single source of truth for all study packages and reporting efforts
2. **Enable Real-time Collaboration** - WebSocket-powered instant updates across all users
3. **Ensure Regulatory Compliance** - Complete audit trails and data integrity
4. **Improve Efficiency** - Reduce manual tracking and duplicate data entry by 75%
5. **Scale Gracefully** - Support multiple concurrent studies and hundreds of users

## Users & Personas

### System Roles
The system implements three user roles with department assignments:

**User Roles:**
- **ADMIN** - Full system access and control
- **EDITOR** - Can create, edit, and manage content
- **VIEWER** - Read-only access

**Departments:**
- **PROGRAMMING** - Development team members
- **BIOSTATISTICS** - Statistical analysis team
- **MANAGEMENT** - Project management and oversight

### Primary User Personas

#### 1. Admin Data Manager
- **System Role:** ADMIN
- **Department:** MANAGEMENT
- **Responsibilities:** System administration, user management, audit oversight
- **Access:** Full CRUD operations, bulk imports, system configuration

#### 2. Programming Team Member
- **System Role:** EDITOR
- **Department:** PROGRAMMING
- **Responsibilities:** Implement TLFs, manage tracker items, update status
- **Access:** Create/edit items, update tracker status, comment on items

#### 3. Biostatistician
- **System Role:** EDITOR or VIEWER
- **Department:** BIOSTATISTICS
- **Responsibilities:** Review specifications, provide feedback, validate results
- **Access:** View all items, comment on items, update status (if EDITOR)

#### 4. Management Reviewer
- **System Role:** VIEWER
- **Department:** MANAGEMENT
- **Responsibilities:** Monitor progress, review reports, track metrics
- **Access:** Read-only access to all data, view dashboards and reports

## Functional Requirements

### Core Entity Management

#### FR-1: Study Management
**Status:** ✅ Implemented

- Hierarchical tree view (Study → Database Release → Reporting Effort)
- CRUD operations with deletion protection
- Unique study labels with validation
- Real-time WebSocket synchronization

#### FR-2: Package Management
**Status:** ✅ Implemented

- Package creation with unique names
- Polymorphic item support (TLF and Dataset types)
- Bulk operations for package items
- Deletion protection when items exist
- Copy operations between packages

#### FR-3: Text Elements (TNFP)
**Status:** ✅ Implemented, 📋 Bulk Upload Planned

**Implemented:**
- Four element types: title, footnote, population_set, acronyms_set
- Intelligent duplicate detection (case/space insensitive)
- Full-text search capabilities
- WebSocket real-time updates
- CRUD operations with validation

**Planned - Bulk Upload:**
- Excel/CSV template for bulk text element import
- Support for all four element types in single upload
- Duplicate detection during import with conflict resolution options
- Validation report showing success/errors
- Transaction-based import (all or nothing)
- Import history and rollback capability

### Reporting Effort Tracker

#### FR-4: Reporting Effort Items
**Status:** 🚧 Partially Implemented (Admin), 📋 Planned (User)

**Admin Features (Implemented):**
- Create/manage reporting effort items
- Auto-tracker creation
- Bulk TLF/Dataset upload
- Copy from packages/other efforts
- Deletion protection based on assignments

**User Features (Planned):**
- View assigned items
- Update tracker status
- Filter and sort capabilities
- Inline editing for editors

#### FR-5: Tracker Management
**Status:** 🚧 Partially Implemented

**Implemented:**
- Programmer assignment (production/QC)
- Status and priority management
- Export/import operations (JSON format)
- Workload tracking

**Planned:**
- Excel export format
- Advanced filtering
- Gantt chart visualization

#### FR-6: Comment System
**Status:** ✅ Implemented (Backend), 📋 Planned (Frontend)

**Backend (Implemented):**
- Role-based comment types (programmer/biostatistician)
- Threaded discussions
- Soft delete with audit trail
- Moderation capabilities (pin/unpin)

**Frontend (Planned):**
- Blog-style display
- Real-time updates
- @mentions functionality
- Rich text formatting

### Administrative Features

#### FR-7: User Management
**Status:** ✅ Implemented

- CRUD operations for users
- Role-based access control (Admin, Editor, Viewer)
- Department assignment
- Activity tracking

#### FR-8: Audit Trail
**Status:** ✅ Implemented

- Comprehensive action logging
- User attribution
- IP/User-agent tracking
- Searchable audit viewer (Admin UI)
- Retention policies

#### FR-9: Database Backup
**Status:** 🚧 Partially Implemented

**Implemented:**
- Manual backup API endpoint
- PostgreSQL pg_dump integration

**Planned:**
- Scheduled backups UI
- Retention policies
- Download functionality
- Restore operations

### Real-time Features

#### FR-10: WebSocket Integration
**Status:** ✅ Implemented

- Automatic broadcasting on all CRUD operations
- Dual client architecture (JavaScript primary, R secondary)
- Auto-reconnection with exponential backoff
- Connection health monitoring
- Message routing by entity type

For detailed WebSocket implementation patterns, see [admin-frontend/CLAUDE.md](../admin-frontend/CLAUDE.md#websocket-message-routing-system).

## Non-Functional Requirements

### Performance
- **Response Time:** < 200ms for API calls (95th percentile)
- **Concurrent Users:** Support 100+ simultaneous users
- **Data Volume:** Handle 10,000+ items per reporting effort
- **WebSocket Latency:** < 100ms message propagation

### Security
- **Authentication:** Posit Connect integration (planned)
- **Authorization:** Role-based access control
- **Data Protection:** PostgreSQL with encrypted connections
- **Audit:** Complete action logging with retention

### Reliability
- **Uptime:** 99.9% availability during business hours
- **Data Integrity:** ACID compliance via PostgreSQL
- **Backup:** Daily automated backups with 30-day retention
- **Recovery:** RPO < 24 hours, RTO < 4 hours

### Usability
- **Browser Support:** Chrome, Firefox, Edge (latest versions)
- **Responsive Design:** Mobile-friendly interfaces
- **Accessibility:** WCAG 2.1 Level AA compliance (planned)
- **Documentation:** Comprehensive user guides and API docs

### Scalability
- **Horizontal Scaling:** Stateless backend design
- **Database:** PostgreSQL with connection pooling
- **WebSocket:** Redis pub/sub for multi-instance (future)
- **Storage:** Support for cloud object storage (future)

## Technical Architecture

### Technology Stack

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL 13+
- SQLAlchemy 2.0 (async)
- Pydantic v2
- Alembic migrations
- UV package manager

**Frontend:**
- R Shiny
- bslib (Bootstrap 5)
- httr2 (API client)
- DT (data tables)
- renv (package management)

**Infrastructure:**
- WebSocket (real-time)
- Docker (containerization)
- Posit Connect (deployment)

For detailed technical patterns and constraints, see [backend/CLAUDE.md](../backend/CLAUDE.md).

## Implementation Phases

### Phase 1: Database Foundation ✅ COMPLETED
- Core schema design
- Migration system
- Model validation

### Phase 2: Backend API ✅ COMPLETED  
- CRUD operations
- WebSocket broadcasting
- Audit logging
- Test suite

### Phase 3: Admin Frontend 🚧 95% COMPLETE
- Entity management modules
- Bulk operations
- Audit viewer
- **Remaining:** Database backup UI, Admin dashboard

### Phase 4: User Frontend 📋 PLANNED (Q4 2025)
- Authentication integration
- User tracker interface
- Comment system UI
- User dashboard

### Phase 5: Advanced Features 📋 PLANNED (Q1-Q2 2026)
- Analytics dashboard
- Export capabilities (Excel, PDF)
- Notification system
- Advanced search

For detailed implementation status, see [REPORTING_EFFORT_TRACKER_TODO.md](../REPORTING_EFFORT_TRACKER_TODO.md).

## Success Metrics

### Adoption Metrics
- **User Adoption:** 80% of target users actively using within 3 months
- **Data Migration:** 100% of existing packages migrated
- **Training Completion:** 90% of users complete training

### Efficiency Metrics
- **Time Savings:** 75% reduction in manual tracking time
- **Error Reduction:** 90% decrease in data entry errors
- **Collaboration:** 2x increase in cross-team interactions

### Quality Metrics
- **System Uptime:** Achieve 99.9% availability
- **User Satisfaction:** NPS score > 8
- **Bug Resolution:** Critical bugs fixed within 24 hours

## Risks & Mitigations

### Technical Risks

| Risk | Impact | Mitigation |
|------|---------|------------|
| SQLAlchemy async session conflicts | Test reliability | Use individual test scripts, documented constraint |
| WebSocket connection stability | User experience | Auto-reconnection with exponential backoff |
| Enum serialization issues | Data integrity | Custom serialization handlers (resolved) |
| Browser compatibility | User access | Progressive enhancement, fallback options |

### Business Risks

| Risk | Impact | Mitigation |
|------|---------|------------|
| User adoption resistance | ROI impact | Phased rollout with training |
| Data migration complexity | Timeline delay | Automated migration scripts |
| Regulatory compliance | Legal risk | Complete audit trails, validation |

## Testing Strategy

### Testing Approach
- **Unit Tests:** Individual test files (async session constraint)
- **Integration Tests:** WebSocket broadcast validation
- **Functional Tests:** Shell script test suites
- **User Acceptance:** Phased rollout with feedback loops

For testing constraints and patterns, see [backend/tests/README.md](../backend/tests/README.md).

## Deployment & Operations

### Deployment Strategy
- **Development:** Local Docker environment
- **Staging:** Posit Connect staging instance
- **Production:** Posit Connect with PostgreSQL RDS

### Monitoring
- **Health Checks:** /health endpoint monitoring
- **Metrics:** Application performance monitoring
- **Logs:** Centralized logging with retention
- **Alerts:** Critical error notifications

## Appendices

### A. References
- [Project Overview - CLAUDE.md](../CLAUDE.md)
- [Backend Documentation - backend/CLAUDE.md](../backend/CLAUDE.md)
- [Frontend Documentation - admin-frontend/CLAUDE.md](../admin-frontend/CLAUDE.md)
- [Implementation Tracker - REPORTING_EFFORT_TRACKER_TODO.md](../REPORTING_EFFORT_TRACKER_TODO.md)

### B. Glossary
- **TLF:** Tables, Listings, and Figures
- **TNFP:** Text, Notes, Footnotes, and Populations
- **SDTM:** Study Data Tabulation Model
- **ADaM:** Analysis Data Model
- **CRUD:** Create, Read, Update, Delete
- **WebSocket:** Protocol for real-time bidirectional communication

### C. Version History
- v2.0 (Aug 2025): Complete rewrite using BMAD-METHOD
- v1.0 (Aug 2025): Initial PRD creation

---

*This PRD is maintained using the BMAD-METHOD and serves as the single source of truth for product requirements. Technical implementation details are referenced in the respective CLAUDE.md documentation files.*