# PEARL - Product Requirements Document

**Version:** 4.0  
**Date:** December 2024  
**Status:** 🚀 Production Ready

## Executive Summary

PEARL (Package, Effort, and Analysis Reporting Library) is a comprehensive clinical research data management system that streamlines package management and reporting effort tracking. The system provides real-time collaboration capabilities through WebSocket integration and maintains complete audit trails for regulatory compliance.

### Technology Stack

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL 13+
- SQLAlchemy 2.0 (async)
- Pydantic v2
- Alembic migrations
- UV package manager
- WebSocket real-time communication

**Frontend:**
- React 18+
- TypeScript
- Vite build tool
- TanStack Query (data fetching)
- Zustand (state management)
- Tailwind CSS
- Shadcn/ui components

**Infrastructure:**
- Docker containerization
- PostgreSQL with connection pooling
- WebSocket real-time updates

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

## Core Features

### 1. Study Management

**Purpose:** Hierarchical organization of clinical studies and their data releases.

**Features:**
- **Study Creation:** Unique study labels with validation
- **Study Tree View:** Hierarchical display (Study → Database Release → Reporting Effort)
- **CRUD Operations:** Create, read, update, delete with validation
- **Deletion Protection:** Cannot delete studies with associated database releases
- **Real-time Updates:** WebSocket synchronization across all users

**User Interface:**
- Tree navigation component
- Filter and search capabilities
- Quick actions (edit, delete, add child entities)

### 2. Database Release Management

**Purpose:** Track database locks and releases for each study.

**Features:**
- **Release Creation:** Associate releases with studies
- **Release Dating:** Track when database was locked
- **Label Management:** Unique labels per study
- **Deletion Protection:** Cannot delete releases with reporting efforts
- **Timeline View:** Visual representation of releases over time

**User Interface:**
- Calendar view for release dates
- Quick filters by study
- Status indicators

### 3. Reporting Effort Management

**Purpose:** Organize reporting activities for each database release.

**Features:**
- **Effort Creation:** Link efforts to specific releases
- **Item Management:** Track TLFs (Tables, Listings, Figures) and datasets
- **Status Tracking:** Monitor progress of each effort
- **Deletion Protection:** Cannot delete efforts with items
- **Batch Operations:** Bulk item creation and updates

**User Interface:**
- Card-based effort display
- Progress indicators
- Quick filters and sorting

### 4. Package System

**Purpose:** Template library for reusable TLF and dataset specifications.

**Features:**

#### Package Management
- **Package Creation:** Define reusable package templates
- **Metadata:** Study indication and therapeutic area
- **Item Organization:** Group related TLFs and datasets
- **Deletion Protection:** Cannot delete packages with items
- **Copy Operations:** Reuse packages across studies

#### Package Items
- **Polymorphic Items:** Support for TLF and Dataset types
- **Item Codes:** Unique identifiers for each item
- **Descriptions:** Detailed item specifications
- **Type Management:** Distinguish between TLFs and datasets
- **Bulk Upload:** Excel template-based import

**User Interface:**
- Package library view
- Item editor with validation
- Template download functionality
- Drag-and-drop reordering

### 5. Text Elements (TNFP)

**Purpose:** Centralized management of reusable text components.

**Features:**

#### Element Types
- **Titles:** Table and figure titles
- **Footnotes:** Table and figure footnotes
- **Population Sets:** Analysis population definitions
- **Acronyms:** Abbreviation definitions

#### Management Features
- **Duplicate Detection:** Case and space-insensitive matching
- **Full-text Search:** Find elements by content
- **Category Filtering:** Filter by element type
- **Bulk Import:** Excel/CSV template upload
- **Validation:** Content uniqueness verification

**User Interface:**
- Multi-tab interface by element type
- Rich text editor
- Search and filter toolbar
- Import/export functionality

### 6. Reporting Effort Tracker

**Purpose:** Track progress of individual TLFs and datasets through production and QC.

**Features:**

#### Tracker Management
- **Auto-creation:** Trackers created with effort items
- **Programmer Assignment:** Primary and QC programmer roles
- **Status Tracking:** Independent primary and QC status
- **Progress Monitoring:** Visual status indicators
- **Workload Analytics:** Assignment distribution reports

#### Status Workflow
- **Primary Statuses:** NOT_STARTED → IN_PROGRESS → COMPLETED
- **QC Statuses:** NOT_STARTED → IN_PROGRESS → QC_PASS/QC_FAIL
- **Status History:** Track status changes over time
- **Notifications:** Alert on status changes

#### Bulk Operations
- **Mass Assignment:** Assign multiple items to programmers
- **Status Updates:** Bulk status changes
- **Excel Import/Export:** Template-based updates
- **Copy Operations:** Copy items between efforts

**User Interface:**
- Kanban board view
- Table view with filters
- Programmer workload dashboard
- Status timeline visualization

### 7. Comment System

**Purpose:** Threaded discussions on tracker items with moderation.

**Features:**

#### Comment Features
- **Threaded Discussions:** Parent-child comment relationships
- **Comment Types:** GENERAL, QUESTION, ISSUE, RESPONSE
- **User Attribution:** Username and timestamp tracking
- **Rich Text:** Markdown support for formatting
- **Soft Delete:** Maintain audit trail for deleted comments

#### Moderation
- **Resolve/Unresolve:** Mark questions/issues as resolved
- **Pin Comments:** Highlight important comments
- **Badge Counts:** Unresolved comment indicators
- **Real-time Updates:** WebSocket-powered comment sync

#### Integration
- **Tracker Association:** Comments linked to specific trackers
- **Notification Badges:** Visual indicators for new comments
- **Search:** Find comments by content or user
- **Export:** Download comment threads

**User Interface:**
- Modal comment interface
- Inline comment badges
- Threaded comment display
- Resolve/unresolve toggles

### 8. User Management

**Purpose:** Role-based access control and user administration.

**Features:**

#### User Administration
- **User Creation:** Add users with roles and departments
- **Role Assignment:** ADMIN, EDITOR, VIEWER permissions
- **Department Assignment:** PROGRAMMING, BIOSTATISTICS, MANAGEMENT
- **Bulk Import:** Excel template for user upload
- **Activity Tracking:** Monitor user actions

#### Access Control
- **Permission Enforcement:** Role-based feature access
- **Read-only Mode:** Viewer restrictions
- **Edit Permissions:** Editor capabilities
- **Admin Functions:** Full system control

**User Interface:**
- User management table
- Role/department filters
- Quick edit functionality
- Activity log viewer

### 9. Audit Trail

**Purpose:** Complete compliance logging for all system operations.

**Features:**

#### Audit Logging
- **Comprehensive Tracking:** All CRUD operations logged
- **User Attribution:** Track who performed actions
- **Change History:** Before/after state capture
- **IP/User-agent:** Technical attribution details
- **Timestamp Precision:** Millisecond-accurate timestamps

#### Audit Viewer
- **Advanced Filtering:** By entity, action, user, date range
- **Search:** Full-text search of changes
- **Export:** Download audit logs for compliance
- **Retention:** Configurable retention policies

**User Interface:**
- Filterable audit log table
- Change diff viewer
- Export functionality
- Real-time log updates

### 10. Database Backup

**Purpose:** Database backup and recovery for business continuity.

**Features:**

#### Backup Management
- **Manual Backups:** On-demand backup creation
- **PostgreSQL Integration:** Native pg_dump support
- **Compression:** Automatic backup compression
- **File Management:** Organized backup storage
- **Backup History:** Track all backup operations

#### Planned Enhancements
- **Scheduled Backups:** Automated backup scheduling
- **Retention Policies:** Automatic old backup cleanup
- **One-click Restore:** Simplified recovery process
- **Cloud Storage:** S3/Azure integration

**User Interface:**
- Backup management dashboard
- Create backup button
- Backup history table
- Download functionality

### 11. Real-time Synchronization

**Purpose:** WebSocket-powered real-time updates across all users.

**Features:**

#### WebSocket Integration
- **Automatic Broadcasting:** All CRUD operations broadcast
- **Connection Management:** Auto-reconnection with backoff
- **Health Monitoring:** Connection status indicators
- **Message Routing:** Entity-specific event handling
- **Cross-browser Sync:** Instant updates for all users

#### Event Types
- Study events (created, updated, deleted)
- Package events (created, updated, deleted)
- Tracker events (updated, deleted, assignment changed)
- Comment events (created, replied, resolved)
- User events (created, updated, deleted)

**User Experience:**
- No manual refresh needed
- Toast notifications for updates
- Conflict resolution dialogs
- Optimistic UI updates

## Data Model

### Core Entities

#### Study
- `id`: Primary key
- `study_label`: Unique study identifier
- `created_at`, `updated_at`: Audit timestamps

#### Database Release
- `id`: Primary key
- `study_id`: Foreign key to Study
- `database_release_label`: Release identifier
- `database_release_date`: Lock date
- `created_at`, `updated_at`: Audit timestamps

#### Reporting Effort
- `id`: Primary key
- `database_release_id`: Foreign key to Database Release
- `database_release_label`: Effort identifier
- `created_at`, `updated_at`: Audit timestamps

#### Reporting Effort Item
- `id`: Primary key
- `reporting_effort_id`: Foreign key to Reporting Effort
- `item_code`: Unique item code
- `item_description`: Item specification
- `item_type`: TLF or DATASET
- `item_status`: PENDING, IN_PROGRESS, COMPLETED
- `created_at`, `updated_at`: Audit timestamps

#### Reporting Effort Item Tracker
- `id`: Primary key
- `reporting_effort_item_id`: Foreign key to Reporting Effort Item
- `primary_programmer_id`: Foreign key to User
- `qc_programmer_id`: Foreign key to User
- `primary_status`: NOT_STARTED, IN_PROGRESS, COMPLETED
- `qc_status`: NOT_STARTED, IN_PROGRESS, QC_PASS, QC_FAIL
- `created_at`, `updated_at`: Audit timestamps

### Package Entities

#### Package
- `id`: Primary key
- `package_name`: Unique package name
- `study_indication`: Indication area
- `therapeutic_area`: Therapeutic category
- `created_at`, `updated_at`: Audit timestamps

#### Package Item
- `id`: Primary key
- `package_id`: Foreign key to Package
- `item_code`: Item identifier
- `item_description`: Item specification
- `item_type`: TLF or DATASET
- `created_at`, `updated_at`: Audit timestamps

### Support Entities

#### Text Element
- `id`: Primary key
- `type`: TITLE, FOOTNOTE, POPULATION_SET, ACRONYMS_SET
- `label`: Element identifier
- `content`: Element text
- `created_at`, `updated_at`: Audit timestamps

#### Tracker Comment
- `id`: Primary key
- `tracker_id`: Foreign key to Tracker
- `user_id`: Foreign key to User
- `comment_text`: Comment content
- `comment_type`: GENERAL, QUESTION, ISSUE, RESPONSE
- `is_resolved`: Resolution status
- `parent_comment_id`: Self-referencing foreign key for threading
- `created_at`, `updated_at`: Audit timestamps

#### User
- `id`: Primary key
- `username`: Unique username
- `role`: ADMIN, EDITOR, VIEWER
- `department`: PROGRAMMING, BIOSTATISTICS, MANAGEMENT
- `created_at`, `updated_at`: Audit timestamps

#### Audit Log
- `id`: Primary key
- `entity_type`: Entity being audited
- `entity_id`: ID of audited entity
- `action`: CREATE, UPDATE, DELETE
- `user_id`: Foreign key to User
- `changes`: JSON field with before/after state
- `timestamp`: Audit timestamp

## API Endpoints

### Study Management
- `GET /api/v1/studies` - List all studies
- `GET /api/v1/studies/{id}` - Get specific study
- `POST /api/v1/studies` - Create new study
- `PUT /api/v1/studies/{id}` - Update study
- `DELETE /api/v1/studies/{id}` - Delete study

### Database Releases
- `GET /api/v1/database-releases` - List all releases
- `GET /api/v1/database-releases/by-study/{study_id}` - Get releases for study
- `POST /api/v1/database-releases` - Create release
- `PUT /api/v1/database-releases/{id}` - Update release
- `DELETE /api/v1/database-releases/{id}` - Delete release

### Reporting Efforts
- `GET /api/v1/reporting-efforts` - List all efforts
- `GET /api/v1/reporting-efforts/by-database-release/{db_release_id}` - Get efforts for release
- `POST /api/v1/reporting-efforts` - Create effort
- `PUT /api/v1/reporting-efforts/{id}` - Update effort
- `DELETE /api/v1/reporting-efforts/{id}` - Delete effort

### Reporting Effort Items
- `GET /api/v1/reporting-effort-items` - List all items
- `GET /api/v1/reporting-effort-items/by-reporting-effort/{effort_id}` - Get items for effort
- `POST /api/v1/reporting-effort-items` - Create item
- `PUT /api/v1/reporting-effort-items/{id}` - Update item
- `DELETE /api/v1/reporting-effort-items/{id}` - Delete item

### Tracker Management
- `GET /api/v1/reporting-effort-tracker` - List all trackers
- `GET /api/v1/reporting-effort-tracker/{id}` - Get tracker
- `POST /api/v1/reporting-effort-tracker` - Create tracker
- `PUT /api/v1/reporting-effort-tracker/{id}` - Update tracker
- `DELETE /api/v1/reporting-effort-tracker/{id}` - Delete tracker
- `PUT /api/v1/reporting-effort-tracker/{id}/assign-primary/{programmer_id}` - Assign primary programmer
- `PUT /api/v1/reporting-effort-tracker/{id}/assign-qc/{programmer_id}` - Assign QC programmer

### Package Management
- `GET /api/v1/packages` - List all packages
- `GET /api/v1/packages/{id}` - Get package
- `POST /api/v1/packages` - Create package
- `PUT /api/v1/packages/{id}` - Update package
- `DELETE /api/v1/packages/{id}` - Delete package

### Package Items
- `GET /api/v1/package-items` - List all items
- `GET /api/v1/package-items/by-package/{package_id}` - Get items for package
- `POST /api/v1/package-items` - Create item
- `PUT /api/v1/package-items/{id}` - Update item
- `DELETE /api/v1/package-items/{id}` - Delete item

### Text Elements
- `GET /api/v1/text-elements` - List all elements
- `GET /api/v1/text-elements/by-type/{type}` - Get elements by type
- `POST /api/v1/text-elements` - Create element
- `PUT /api/v1/text-elements/{id}` - Update element
- `DELETE /api/v1/text-elements/{id}` - Delete element

### Comments
- `GET /api/v1/tracker-comments/by-tracker/{tracker_id}` - Get comments for tracker
- `POST /api/v1/tracker-comments` - Create comment
- `POST /api/v1/tracker-comments/{parent_id}/reply` - Reply to comment
- `PUT /api/v1/tracker-comments/{id}` - Update comment
- `PUT /api/v1/tracker-comments/{id}/resolve` - Mark comment as resolved
- `DELETE /api/v1/tracker-comments/{id}` - Delete comment

### User Management
- `GET /api/v1/users` - List all users
- `GET /api/v1/users/{id}` - Get user
- `POST /api/v1/users` - Create user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Audit Trail
- `GET /api/v1/audit-trail` - Get audit logs with filtering

### Database Backup
- `POST /api/v1/database-backup` - Create backup
- `GET /api/v1/database-backup/list` - List backups

### WebSocket
- `WS /api/v1/ws/studies` - Real-time updates endpoint

### Health Check
- `GET /api/health` - Service health check

## Non-Functional Requirements

### Performance
- **Response Time:** < 200ms for API calls (95th percentile)
- **Concurrent Users:** Support 100+ simultaneous users
- **Data Volume:** Handle 10,000+ items per reporting effort
- **WebSocket Latency:** < 100ms message propagation
- **Page Load Time:** < 2 seconds initial load
- **Data Table Rendering:** < 500ms for 1000 rows

### Security
- **Authentication:** Posit Connect integration (planned)
- **Authorization:** Role-based access control
- **Data Protection:** PostgreSQL with encrypted connections
- **Audit:** Complete action logging with retention
- **Input Validation:** Server-side validation for all inputs
- **SQL Injection Prevention:** Parameterized queries only
- **XSS Prevention:** Sanitized user inputs

### Reliability
- **Uptime:** 99.9% availability during business hours
- **Data Integrity:** ACID compliance via PostgreSQL
- **Backup:** Daily automated backups with 30-day retention
- **Recovery:** RPO < 24 hours, RTO < 4 hours
- **Error Handling:** Graceful degradation for service failures

### Usability
- **Browser Support:** Chrome, Firefox, Edge (latest versions)
- **Responsive Design:** Mobile-friendly interfaces
- **Accessibility:** WCAG 2.1 Level AA compliance (planned)
- **Documentation:** Comprehensive user guides
- **Keyboard Navigation:** Full keyboard accessibility
- **Screen Reader Support:** ARIA labels and descriptions

### Scalability
- **Horizontal Scaling:** Stateless backend design
- **Database:** PostgreSQL with connection pooling
- **WebSocket:** Redis pub/sub for multi-instance (future)
- **Storage:** Support for cloud object storage (future)
- **Caching:** Client-side caching with React Query
- **Load Balancing:** Multi-instance deployment ready

## Implementation Status

### ✅ Completed (Production Ready)

**Backend:**
- Complete CRUD API for all entities
- WebSocket real-time synchronization
- Comprehensive audit logging
- Role-based access control
- Database backup and restore
- Health check endpoints
- Error handling and validation

**Database:**
- Complete schema with relationships
- Cascade delete constraints
- Indexes for performance
- Audit log tables
- Migration system (Alembic)

### 🚧 In Progress

**Frontend (React):**
- Component library setup
- API integration with TanStack Query
- State management with Zustand
- Basic CRUD interfaces
- WebSocket client integration

### 📋 Planned

**Authentication:**
- Posit Connect integration
- Session management
- Token refresh handling

**Advanced Features:**
- Analytics dashboard
- Advanced semantic search
- Email notifications
- Excel/PDF export
- Timeline/Gantt visualizations
- Machine learning insights

## User Workflows

### Study Setup Workflow
1. Admin creates new study with unique label
2. Admin adds database release with lock date
3. Admin creates reporting effort for the release
4. Effort is ready for item management

### Package Template Workflow
1. Admin creates package with metadata
2. Admin adds TLF/dataset items to package
3. Admin associates text elements (titles, footnotes)
4. Package becomes reusable template
5. Users copy package items to reporting efforts

### Tracker Management Workflow
1. Effort items automatically create trackers
2. Admin/Editor assigns primary programmer
3. Primary programmer updates status to IN_PROGRESS
4. Primary programmer completes work, updates to COMPLETED
5. Admin/Editor assigns QC programmer
6. QC programmer reviews and updates QC status
7. If QC fails, item returns to primary programmer
8. If QC passes, item is finalized

### Comment Workflow
1. User views tracker item
2. User adds question comment
3. Other users receive real-time notifications
4. Users reply to comment thread
5. Original commenter marks question as resolved
6. Resolved count updates across all browsers

## Success Metrics

### Adoption Metrics
- **User Adoption:** 80% of target users actively using within 3 months
- **Data Migration:** 100% of existing packages migrated
- **Training Completion:** 90% of users complete training
- **Daily Active Users:** 70% of registered users
- **Feature Usage:** 90% of features used weekly

### Efficiency Metrics
- **Time Savings:** 75% reduction in manual tracking time
- **Error Reduction:** 90% decrease in data entry errors
- **Collaboration:** 2x increase in cross-team interactions
- **Search Efficiency:** 80% reduction in time to find items
- **Task Completion:** 50% faster item completion rates

### Quality Metrics
- **System Uptime:** Achieve 99.9% availability
- **User Satisfaction:** NPS score > 8
- **Bug Resolution:** Critical bugs fixed within 24 hours
- **API Response Time:** 95th percentile < 200ms
- **Zero Data Loss:** 100% audit trail coverage

## Deployment Strategy

### Development Environment
- Local Docker containers
- Development database
- Hot reload for frontend and backend
- Debug logging enabled

### Staging Environment
- Posit Connect staging instance
- Staging database with anonymized data
- Real-time monitoring
- User acceptance testing

### Production Environment
- Posit Connect production instance
- PostgreSQL RDS with backups
- Performance monitoring
- Error tracking and alerting
- Automated health checks

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|---------|------------|
| WebSocket connection stability | User experience | Auto-reconnection with exponential backoff |
| Database performance | System slowdown | Connection pooling, query optimization, indexes |
| Browser compatibility | User access | Progressive enhancement, fallback options |
| Data migration errors | Data integrity | Automated validation, rollback procedures |

### Business Risks

| Risk | Impact | Mitigation |
|------|---------|------------|
| User adoption resistance | ROI impact | Phased rollout with training |
| Data migration complexity | Timeline delay | Automated migration scripts |
| Regulatory compliance | Legal risk | Complete audit trails, validation |
| Concurrent editing conflicts | Data integrity | Optimistic locking, conflict resolution UI |

## Future Enhancements

### Phase 1 (Q1 2025)
- Complete React frontend
- Posit Connect authentication
- Mobile-responsive design
- Excel import/export
- Advanced filtering

### Phase 2 (Q2 2025)
- Analytics dashboard
- Timeline visualizations
- Email notifications
- Scheduled backups
- Cloud storage integration

### Phase 3 (Q3 2025)
- Advanced semantic search
- Vector embeddings (Transformers.js)
- Machine learning insights
- Third-party integrations
- Advanced reporting

## Glossary

- **TLF:** Tables, Listings, and Figures
- **TNFP:** Text, Notes, Footnotes, and Populations (Text Elements)
- **SDTM:** Study Data Tabulation Model
- **ADaM:** Analysis Data Model
- **CRUD:** Create, Read, Update, Delete
- **WebSocket:** Protocol for real-time bidirectional communication
- **QC:** Quality Control
- **Primary Programmer:** Programmer responsible for initial development
- **QC Programmer:** Programmer responsible for quality control review

## Version History

- v4.0 (Dec 2024): React frontend focus, comprehensive feature documentation
- v3.0 (Jan 2025): Updated to reflect admin frontend complete, universal CRUD system
- v2.0 (Aug 2025): Complete rewrite using BMAD-METHOD
- v1.0 (Aug 2025): Initial PRD creation

---

*This PRD serves as the single source of truth for PEARL product requirements and features.*
