# PEARL - Product Requirements Document

**Version:** 3.0  
**Date:** January 2025  
**Status:** 🚧 In Development (Phase 4 - Universal CRUD System Implementation)

## Executive Summary

PEARL (Package, Effort, and Analysis Reporting Library) is a comprehensive research data management system designed to streamline clinical study package management and reporting effort tracking. The system provides real-time collaboration capabilities through WebSocket integration and maintains complete audit trails for regulatory compliance.

### Current Development Status
- ✅ **Phase 1:** Database Foundation - COMPLETED
- ✅ **Phase 2:** Backend API - COMPLETED  
- ✅ **Phase 3:** Admin Frontend - COMPLETED
- 🚧 **Phase 4:** Universal CRUD System - IN PROGRESS (Feature branch: universal-crud-updates)
- 📋 **Phase 5:** User Frontend - PLANNED
- 📋 **Phase 6:** Advanced Features - PLANNED

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
**Status:** ✅ Fully Implemented (Admin), 📋 Planned (User Interface)

**Admin Features (Completed):**
- Complete item lifecycle management (create, edit, delete)
- Auto-tracker creation with assignment workflows
- Bulk TLF/Dataset upload with validation and error reporting
- Copy from packages and other efforts with conflict resolution
- Comprehensive deletion protection based on assignments
- Real-time WebSocket updates across all browsers

**User Features (Planned for Phase 5):**
- View assigned items with filtering
- Update tracker status and progress
- Advanced search and sort capabilities
- Inline editing for editors with role validation

#### FR-5: Tracker Management
**Status:** ✅ Fully Implemented (Admin), 📋 User Interface Planned

**Implemented (Complete):**
- Programmer assignment system (production/QC programmers)
- Status and priority management with validation
- Export/import operations (JSON format with validation)
- Workload tracking and assignment analytics
- Comment badge system with real-time cross-browser updates
- Comprehensive audit trail for all tracker operations

**Planned (Phase 5 - User Interface):**
- Excel export format for end users
- Advanced filtering and search for large datasets
- Timeline/Gantt chart visualization for project planning

#### FR-6: Comment System
**Status:** ✅ Backend Complete, ✅ Admin UI Complete, 📋 User UI Planned

**Backend & Admin UI (Fully Implemented):**
- Complete comment CRUD with role-based access control
- Threaded discussions with parent-child relationships
- Comment badge system with real-time cross-browser updates
- Soft delete with comprehensive audit trail
- Moderation capabilities (resolve/unresolve, pin/unpin)
- WebSocket-powered real-time comment synchronization
- Modal-based comment interface integrated with tracker management

**User Interface (Planned for Phase 5):**
- Blog-style comment display optimized for end users
- @mentions functionality
- Rich text formatting support
- Mobile-optimized comment threading

### Administrative Features

#### FR-7: User Management
**Status:** ✅ Fully Implemented

- Complete user CRUD operations with validation
- Role-based access control (Admin, Editor, Viewer) with enforcement
- Department assignment (Programming, Biostatistics, Management)
- Comprehensive activity tracking and audit logs
- Real-time WebSocket updates for user changes
- Bulk user management capabilities

#### FR-8: Audit Trail
**Status:** ✅ Fully Implemented

- Comprehensive action logging for all CRUD operations
- Complete user attribution with IP/User-agent tracking
- Searchable audit viewer with advanced filtering (Admin UI)
- Retention policies and automatic cleanup
- Real-time audit log updates via WebSocket
- Export capabilities for compliance reporting

#### FR-9: Database Backup
**Status:** ✅ Implemented

**Completed Features:**
- Manual backup API endpoint with validation
- PostgreSQL pg_dump integration with compression
- Admin UI for backup management
- Backup file management and organization
- Error handling and notification system

**Future Enhancements (Phase 6):**
- Scheduled automated backups
- Advanced retention policies with archival
- One-click restore functionality
- Cloud storage integration

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

**Future Technologies (Phase 5):**
- Transformers.js for client-side semantic search
- IndexedDB for embedding cache storage
- WebAssembly for ML model execution

For detailed technical patterns and constraints, see [backend/CLAUDE.md](../backend/CLAUDE.md).

## Implementation Phases

### Phase 1: Database Foundation ✅ COMPLETED
- Core schema design with CASCADE DELETE constraints
- Migration system with Alembic
- Model validation and comprehensive relationships
- Audit logging infrastructure

### Phase 2: Backend API ✅ COMPLETED  
- Complete CRUD operations for all entities
- WebSocket broadcasting with real-time updates
- Comprehensive audit logging
- Role-based access control foundation
- Database backup and restore capabilities

### Phase 3: Admin Frontend ✅ COMPLETED
- **Study Management**: Full hierarchical tree view (Study → Database Release → Reporting Effort)
- **Package Management**: Complete CRUD with bulk operations and copy functionality
- **TNFP (Text Elements)**: Full management with intelligent duplicate detection
- **Reporting Effort Tracker**: Complete tracker system with programmer assignments
- **Users Management**: Full user CRUD with role and department assignment
- **Database Backup**: Manual backup with PostgreSQL integration
- **Admin Dashboard**: Comprehensive admin overview and monitoring
- **Audit Trail**: Searchable audit viewer with filtering
- **Real-time WebSocket**: Cross-browser synchronization for all operations

### Phase 4: Universal CRUD System 🚧 IN PROGRESS (Current Focus)
- **Status**: Active development on `feature/universal-crud-updates` branch
- **Goal**: Standardize all cross-browser CRUD updates with intelligent conflict resolution
- **Components**:
  - Universal Activity Manager (✅ Implemented - `crud_activity_manager.js`)
  - Context-aware update strategies (user modals, active forms, conflicts)
  - Standardized WebSocket message format across all entities
  - Intelligent update queuing and conflict resolution
  - Legacy code removal and consolidation

### Phase 5: User Frontend 📋 PLANNED (Q2-Q3 2025)
- **Authentication**: Posit Connect integration
- **User Interface**: Read-only tracker views for viewers, edit capabilities for editors
- **Dashboard**: Task-focused dashboards with visualizations
- **Comments**: Blog-style comment system with threading
- **Mobile**: Responsive design for mobile access

### Phase 6: Advanced Features 📋 PLANNED (Q4 2025 - Q1 2026)
- Analytics dashboard with advanced reporting
- Excel/PDF export capabilities
- Email notification system
- Advanced Semantic Search (Vector Embeddings) - See [FR-11](#fr-11-cross-database-semantic-search) below

**Current Focus**: The Universal CRUD Update System is being implemented to standardize cross-browser real-time updates across all entities, replacing legacy entity-specific handlers with a unified, intelligent conflict resolution system.

## Current Priority: Universal CRUD System

### Universal CRUD Update System (Phase 4 - In Progress)
**Branch:** `feature/universal-crud-updates`  
**Status:** Active Development  
**Priority:** HIGH - Foundation for all future user-facing features

**Overview:**  
The Universal CRUD System standardizes all cross-browser real-time updates with intelligent context awareness and conflict resolution. This replaces the current patchwork of entity-specific update handlers with a unified, maintainable system.

**Key Components:**

1. **Universal Activity Manager** (✅ Implemented)
   - Context-aware user activity detection (modals, forms, typing)
   - Intelligent update strategy determination
   - Queue management for deferred updates
   - Conflict detection and resolution

2. **Standardized WebSocket Integration** (🚧 In Progress)
   - Unified message format across all entities
   - Centralized event routing and processing
   - Legacy handler removal and consolidation

3. **Conflict Resolution System** (📋 Planned)
   - Visual conflict resolution dialogs
   - Side-by-side change comparison
   - User choice preservation (keep mine/take theirs/merge)

**Benefits:**
- Consistent behavior across all entity types
- Reduced maintenance burden (single update system vs. 9+ entity-specific handlers)
- Better user experience with intelligent update deferral
- Foundation for advanced collaboration features

### Phase 6 Feature Detail: Advanced Semantic Search

#### FR-11: Cross-Database Semantic Search
**Status:** 📋 PLANNED (Q1 2026)  
**Priority:** Medium  
**Location:** User Frontend - Dedicated Search Page

**Overview:**  
Implement a dedicated search page in the user-frontend application that provides intelligent, meaning-based search across all tracker data in the database using vector embeddings.

**Technical Approach:**
- Client-side vector embeddings using Transformers.js
- Model: Xenova/all-MiniLM-L6-v2 (~30MB, 384-dimension embeddings)
- IndexedDB for embedding cache persistence
- Real-time semantic similarity scoring

**Key Features:**

1. **Universal Search Interface**
   - Single search box for all tracker types (TLF, SDTM, ADaM)
   - Search across all reporting efforts simultaneously
   - Filter results by effort, type, status, or assignment

2. **Semantic Understanding**
   - Understands meaning and context, not just keywords
   - Examples:
     - "quality issues" → finds "QC Fail", "QC Started", quality-related items
     - "programmer assignments" → finds all programmer-related fields
     - "timeline" → finds "Due Date", "QC Completion", time-related fields
     - "failed validation" → finds "QC Fail", validation errors, issues

3. **Search Modes**
   - **Semantic Mode**: Meaning-based search using embeddings
   - **Fuzzy Mode**: Typo-tolerant character matching
   - **Regex Mode**: Pattern-based technical search
   - **Hybrid Mode**: Combines all three for best results

4. **Performance Features**
   - Progressive loading during model download
   - Batch embedding generation on initial load
   - Cached embeddings in browser storage
   - Similarity threshold adjustment (0.5-1.0)
   - Result ranking by relevance score

5. **User Experience**
   - Real-time search-as-you-type
   - Relevance scores displayed for each result
   - Highlighted matching context in results
   - Direct navigation to source tracker items
   - Search history and saved searches

**Benefits:**
- **Zero ongoing costs**: Runs entirely in browser after model download
- **Privacy-compliant**: No data sent to external servers
- **Offline capable**: Works without internet after initial setup
- **Fast**: <200ms search latency for thousands of items
- **Intelligent**: Understands synonyms, abbreviations, and context

**Implementation Considerations:**
- Initial model download: 3-5 seconds (cached for future)
- Memory usage: ~150MB including model and embeddings
- Requires modern browser with WebAssembly support
- Progressive enhancement for older browsers

## Success Metrics

### Adoption Metrics
- **User Adoption:** 80% of target users actively using within 3 months
- **Data Migration:** 100% of existing packages migrated
- **Training Completion:** 90% of users complete training

### Efficiency Metrics
- **Time Savings:** 75% reduction in manual tracking time
- **Error Reduction:** 90% decrease in data entry errors
- **Collaboration:** 2x increase in cross-team interactions
- **Search Efficiency:** 80% reduction in time to find relevant tracker items
- **Search Accuracy:** 95% relevant results in top 10 search results

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

## Current Development Timeline

### Immediate (Q1 2025)
- **Universal CRUD System**: Complete implementation and testing
- **Legacy Code Removal**: Clean up entity-specific handlers
- **Performance Optimization**: WebSocket and UI improvements

### Short-term (Q2 2025)
- **Authentication System**: Posit Connect integration
- **User Frontend**: Basic read-only interface
- **Mobile Optimization**: Responsive design improvements

### Medium-term (Q3-Q4 2025)
- **User Frontend**: Complete editor capabilities
- **Advanced Analytics**: Dashboard enhancements
- **Export Systems**: Excel/PDF generation

### Long-term (2026)
- **Advanced Search**: Vector embeddings and semantic search
- **Advanced Analytics**: Machine learning insights
- **Integration**: Third-party system integrations

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
- [Universal CRUD Updates - UNIVERSAL_CRUD_UPDATE_PLAN.md](../UNIVERSAL_CRUD_UPDATE_PLAN.md)

### B. Glossary
- **TLF:** Tables, Listings, and Figures
- **TNFP:** Text, Notes, Footnotes, and Populations
- **SDTM:** Study Data Tabulation Model
- **ADaM:** Analysis Data Model
- **CRUD:** Create, Read, Update, Delete
- **WebSocket:** Protocol for real-time bidirectional communication

### C. Version History
- v3.0 (Jan 2025): Updated to reflect current implementation status - Admin Frontend complete, Universal CRUD system in progress
- v2.0 (Aug 2025): Complete rewrite using BMAD-METHOD
- v1.0 (Aug 2025): Initial PRD creation

---

*This PRD is maintained using the BMAD-METHOD and serves as the single source of truth for product requirements. Technical implementation details are referenced in the respective CLAUDE.md documentation files.*