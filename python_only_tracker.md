# Python-Only Research Tracker System - Complete Specification

**Document Version:** 2.0
**Last Updated:** 2025-01-03
**Target Audience:** AI Agent / Junior Developer with no prior context

## Executive Summary

Build a **full-stack Python web application** for tracking research data analysis tasks across multiple studies. The system supports multi-user collaboration with near-real-time updates, hierarchical data organization, workflow management, role-based access control, interactive dashboards, and comprehensive audit logging.

**Key Requirements:**
- Multi-user web application (5-20 concurrent users)
- Python-only stack (no R, no Node.js, no separate database server)
- **DuckDB embedded database** (better concurrency than SQLite, zero installation)
- Near-real-time synchronization (1-2 second update latency acceptable)
- Complete audit trail for regulatory compliance
- Role-based access control (Admin, Editor, Viewer)
- Interactive dashboard with charts and metrics
- Hierarchical data model: Study → Database Release → Reporting Effort → Items → Tracker

---

## Technology Stack

### Backend
- **Framework:** FastAPI 0.111+ (synchronous endpoints - simpler than async)
- **Database:** **DuckDB 0.9+** (embedded OLAP database with better concurrency)
- **ORM:** SQLAlchemy 2.0+ (synchronous with duckdb-engine driver)
- **Validation:** Pydantic 2.0+
- **Authentication:** Simple session-based auth with HTTP-only cookies (perfect for internal apps)
- **Testing:** pytest 8.0+

### Frontend
- **Framework:** Reflex 0.4+ (formerly Pynecone - pure Python reactive UI)
- **Charts:** Plotly (via reflex-plotly for interactive graphs)
- **HTTP Client:** httpx (async)
- **State Management:** Reflex built-in state system
- **UI Components:** Reflex Chakra UI components (modern, accessible)

### Development Tools
- **Package Manager:** uv (preferred) or pip
- **Migrations:** Alembic
- **Code Quality:** black, isort, flake8, mypy
- **Environment:** Python 3.11+

---

## Why DuckDB Over SQLite?

**DuckDB is specifically designed for analytical workloads with better concurrency:**

| Feature | SQLite | DuckDB |
|---------|--------|--------|
| **Concurrent Writers** | 1 (database-level lock) | Multiple (MVCC like PostgreSQL) |
| **Best For** | 1-5 users | 5-50 users |
| **Installation** | None | None (pip install) |
| **Async Complexity** | Requires async/await + retry logic | Works great synchronously |
| **SQL Features** | Basic | PostgreSQL-compatible |
| **Analytics** | Slow on large datasets | Columnar storage (fast) |
| **JSON Support** | Limited (JSON1 extension) | Native JSON columns |
| **Full-Text Search** | FTS5 extension | Built-in |
| **Concurrency Model** | Write locks + WAL mode | MVCC (no locks for reads) |

**For your use case (5-20 concurrent users, research tracking):**
- ✅ DuckDB handles concurrent access better
- ✅ No retry logic needed for locked database
- ✅ No async/await complexity
- ✅ PostgreSQL-compatible (easier migration later)
- ✅ Better performance for analytics queries

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Browser (Multiple Users)                      │
│                   http://localhost:3000                          │
│  Roles: ADMIN (full access) | EDITOR (CRUD) | VIEWER (read-only)│
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP + CORS
                            │ (REST API calls + polling)
┌───────────────────────────▼─────────────────────────────────────┐
│                    Reflex Frontend Application                   │
│                         Port 3000                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Pages & Components                                      │  │
│  │  - Dashboard (charts, KPIs, workload summary)           │  │
│  │  - Studies (hierarchical tree view)                      │  │
│  │  - Tracker (Kanban board, workload, comments)           │  │
│  │  - Packages (template library)                           │  │
│  │  - Text Elements (footnotes, titles)                     │  │
│  │  - Users (admin only)                                    │  │
│  │  - Audit Log (compliance view)                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  State Management (rx.State subclasses)                  │  │
│  │  - AuthState (login, current user, permissions)         │  │
│  │  - DashboardState (metrics, charts data)                │  │
│  │  - StudyState, PackageState, TrackerState               │  │
│  │  - SyncState (polling logic - every 2 seconds)          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Reusable Components                                     │  │
│  │  - DataTable (sortable, filterable, pagination)         │  │
│  │  - TreeView (hierarchical Study structure)              │  │
│  │  - KanbanBoard (drag-and-drop tracker workflow)         │  │
│  │  - Charts (Plotly: bar, pie, timeline, workload)        │  │
│  │  - Forms (validation, error handling)                   │  │
│  │  - Modals (create/edit dialogs)                         │  │
│  │  - RoleBadge (visual role indicators)                   │  │
│  │  - StatusBadge (production/QC status colors)            │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP API calls
                            │ (GET/POST/PUT/DELETE + JWT header)
┌───────────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend Application                   │
│                         Port 8000                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  REST API Endpoints (/api/v1/*)                          │  │
│  │  - /auth/login, /auth/logout, /auth/me                   │  │
│  │  - /dashboard/metrics (KPIs, charts)                     │  │
│  │  - /studies, /packages, /trackers                        │  │
│  │  - /changes/check (polling for updates)                  │  │
│  │  All protected by @require_role() decorator              │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Authorization Middleware                                 │  │
│  │  - JWT token validation                                   │  │
│  │  - Role-based access control (RBAC)                      │  │
│  │  - Permission decorators (@admin_only, @editor_only)     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CRUD Layer (Business Logic)                             │  │
│  │  - BaseCRUD (no retry logic - DuckDB handles it!)       │  │
│  │  - Domain-specific CRUD classes                          │  │
│  │  - Deletion protection checks                            │  │
│  │  - Dashboard metrics aggregation                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SQLAlchemy Models + Pydantic Schemas                    │  │
│  │  - 21 database tables with relationships                 │  │
│  │  - Validation and serialization                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Utilities                                                │  │
│  │  - Change tracking (timestamp-based diff)                │  │
│  │  - Audit logging (all CRUD operations)                   │  │
│  │  - Password hashing (bcrypt)                             │  │
│  │  - JWT token generation/validation                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ SQLAlchemy ORM (synchronous)
┌───────────────────────────▼─────────────────────────────────────┐
│                      DuckDB Database File                        │
│                       tracker.duckdb                             │
│  - 21 tables with foreign key constraints                       │
│  - Full-text search indexes                                     │
│  - Automatic timestamps (created_at, updated_at)                │
│  - MVCC for concurrent reads/writes (no locks!)                 │
└─────────────────────────────────────────────────────────────────┘
```

### Real-Time Synchronization Flow (Without WebSocket)

```
User A (Browser 1) creates a Study
    ↓
Reflex Frontend → POST /api/v1/studies (with JWT token)
    ↓
FastAPI Backend → Validates JWT → Checks role (EDITOR or ADMIN)
    ↓
StudyCRUD.create() → DuckDB INSERT (no retry needed!)
    ↓
Update table_change_log.last_modified for 'studies'
    ↓
FastAPI returns created Study (HTTP 201)
    ↓
Reflex updates local state, refreshes UI immediately

Meanwhile (every 2 seconds):
User B (Browser 2) → Background polling task runs
    ↓
GET /api/v1/changes/check?tables=studies,packages&since=2025-01-03T10:00:00
    ↓
Backend checks table_change_log.last_modified > since timestamp
    ↓
Response: {"studies": {"has_changes": true, "last_modified": "2025-01-03T10:05:00"}}
    ↓
Reflex detects changes → GET /api/v1/studies
    ↓
Reflex updates local state, refreshes UI
    ↓
User B sees new Study appear (1-2 second delay)
```

---

## Database Schema

### Database Configuration (DuckDB)

**Connection Setup:**
```python
# No special pragmas needed - DuckDB handles everything!
from sqlalchemy import create_engine

engine = create_engine("duckdb:///tracker.duckdb", echo=False)

# That's it! No WAL mode, no foreign key pragmas, no busy timeout
# DuckDB handles concurrency, transactions, and constraints automatically
```

**Key DuckDB Benefits:**
- ✅ Automatic MVCC (Multi-Version Concurrency Control)
- ✅ Multiple concurrent writers (no database locks)
- ✅ PostgreSQL-compatible SQL dialect
- ✅ Better analytics performance (columnar storage)
- ✅ Built-in full-text search
- ✅ Native JSON support

### Complete Database Schema (21 Tables)

#### 1. `users` - User Authentication and Authorization

**Purpose:** Store user accounts with role-based access control

**Columns:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(20) NOT NULL DEFAULT 'VIEWER',  -- ADMIN, EDITOR, VIEWER
    department VARCHAR(50),                       -- programming, biostatistics, management
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (role IN ('ADMIN', 'EDITOR', 'VIEWER')),
    CHECK (department IN ('programming', 'biostatistics', 'management', NULL))
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_department ON users(department);
```

**Role Permissions:**

| Role | Permissions |
|------|-------------|
| **ADMIN** | Full access: CRUD all entities, manage users, view audit logs |
| **EDITOR** | CRUD studies, packages, trackers, comments. Cannot manage users or delete studies with data |
| **VIEWER** | Read-only access to all entities. Cannot create, update, or delete |

**Sample Data:**
```sql
INSERT INTO users (username, email, hashed_password, full_name, role, department) VALUES
('admin', 'admin@company.com', '$2b$12$hashed...', 'System Administrator', 'ADMIN', 'management'),
('john_prog', 'john@company.com', '$2b$12$hashed...', 'John Programmer', 'EDITOR', 'programming'),
('jane_qc', 'jane@company.com', '$2b$12$hashed...', 'Jane QC Lead', 'EDITOR', 'programming'),
('viewer1', 'viewer@company.com', '$2b$12$hashed...', 'External Viewer', 'VIEWER', NULL);
```

---

#### 2. `studies` - Top-Level Study Container

**Purpose:** Represent clinical trials or research studies

**Columns:**
```sql
CREATE TABLE studies (
    id INTEGER PRIMARY KEY,
    study_label VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',  -- active, on_hold, completed, archived
    start_date DATE,
    target_completion_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (status IN ('active', 'on_hold', 'completed', 'archived'))
);

CREATE INDEX idx_studies_label ON studies(study_label);
CREATE INDEX idx_studies_status ON studies(status);
CREATE INDEX idx_studies_updated_at ON studies(updated_at);
```

**Business Rules:**
- `study_label` must be unique (case-insensitive enforced in application layer)
- Cannot delete if dependent `database_releases` exist (deletion protection)

**Sample Data:**
```sql
INSERT INTO studies (study_label, description, status, start_date, target_completion_date) VALUES
('STUDY-001-ONCOLOGY', 'Phase 3 Cancer Trial', 'active', '2024-01-15', '2025-12-31'),
('STUDY-002-CARDIO', 'Cardiovascular Outcomes Study', 'active', '2024-03-01', '2026-06-30');
```

---

#### 3. `database_releases` - Data Snapshot Versions

**Purpose:** Track different database freeze dates for a study

**Columns:**
```sql
CREATE TABLE database_releases (
    id INTEGER PRIMARY KEY,
    study_id INTEGER NOT NULL,
    database_release_label VARCHAR(255) NOT NULL,
    description TEXT,
    release_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (study_id) REFERENCES studies(id) ON DELETE RESTRICT,
    UNIQUE (study_id, database_release_label)
);

CREATE INDEX idx_database_releases_study_id ON database_releases(study_id);
CREATE INDEX idx_database_releases_label ON database_releases(database_release_label);
CREATE INDEX idx_database_releases_updated_at ON database_releases(updated_at);
```

**Business Rules:**
- Each release label must be unique within a study
- Cannot delete if dependent `reporting_efforts` exist
- Parent study cannot be deleted while releases exist (ON DELETE RESTRICT)

**Sample Data:**
```sql
INSERT INTO database_releases (study_id, database_release_label, release_date) VALUES
(1, 'Database Lock 2024-Q1', '2024-03-31'),
(1, 'Database Lock 2024-Q2', '2024-06-30'),
(2, 'Interim Analysis 1', '2024-09-15');
```

---

#### 4. `reporting_efforts` - Analysis Projects

**Purpose:** Group deliverables (tables, listings, figures) for specific regulatory submissions

**Columns:**
```sql
CREATE TABLE reporting_efforts (
    id INTEGER PRIMARY KEY,
    study_id INTEGER NOT NULL,
    database_release_id INTEGER NOT NULL,
    reporting_effort_label VARCHAR(255) NOT NULL,
    description TEXT,
    submission_type VARCHAR(50),  -- CSR, IND, NDA, BLA, etc.
    due_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (study_id) REFERENCES studies(id) ON DELETE RESTRICT,
    FOREIGN KEY (database_release_id) REFERENCES database_releases(id) ON DELETE RESTRICT,
    UNIQUE (database_release_id, reporting_effort_label)
);

CREATE INDEX idx_reporting_efforts_study_id ON reporting_efforts(study_id);
CREATE INDEX idx_reporting_efforts_db_release_id ON reporting_efforts(database_release_id);
CREATE INDEX idx_reporting_efforts_updated_at ON reporting_efforts(updated_at);
```

**Sample Data:**
```sql
INSERT INTO reporting_efforts (study_id, database_release_id, reporting_effort_label, submission_type, due_date) VALUES
(1, 1, 'CSR Tables Package', 'CSR', '2024-05-15'),
(1, 2, 'Interim Safety Analysis', 'IND', '2024-08-01');
```

---

#### 5. `reporting_effort_items` - Individual Deliverables (Polymorphic)

**Purpose:** Track individual outputs (Tables, Listings, Figures, Datasets) within a reporting effort

**Columns:**
```sql
CREATE TABLE reporting_effort_items (
    id INTEGER PRIMARY KEY,
    reporting_effort_id INTEGER NOT NULL,
    item_type VARCHAR(20) NOT NULL,        -- TLF or DATASET
    item_subtype VARCHAR(20) NOT NULL,     -- TABLE, LISTING, FIGURE (TLF) or SDTM, ADAM (DATASET)
    item_code VARCHAR(50) NOT NULL,        -- e.g., "T-14.1.1", "DM", "ADAE"
    source_type VARCHAR(20),               -- package, reporting_effort, custom, bulk_upload
    source_id INTEGER,                     -- ID from source (package_id or parent reporting_effort_id)
    source_item_id INTEGER,                -- ID of source item (package_item_id if from package)
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (reporting_effort_id) REFERENCES reporting_efforts(id) ON DELETE CASCADE,
    UNIQUE (reporting_effort_id, item_type, item_subtype, item_code),
    CHECK (item_type IN ('TLF', 'DATASET')),
    CHECK (item_subtype IN ('TABLE', 'LISTING', 'FIGURE', 'SDTM', 'ADAM'))
);

CREATE INDEX idx_reporting_effort_items_effort_id ON reporting_effort_items(reporting_effort_id);
CREATE INDEX idx_reporting_effort_items_type ON reporting_effort_items(item_type, item_subtype);
CREATE INDEX idx_reporting_effort_items_code ON reporting_effort_items(item_code);
CREATE INDEX idx_reporting_effort_items_updated_at ON reporting_effort_items(updated_at);
```

**Sample Data:**
```sql
INSERT INTO reporting_effort_items (reporting_effort_id, item_type, item_subtype, item_code) VALUES
(1, 'TLF', 'TABLE', 'T-14.1.1'),
(1, 'TLF', 'TABLE', 'T-14.1.2'),
(1, 'TLF', 'LISTING', 'L-16.2.1'),
(1, 'DATASET', 'ADAM', 'ADSL');
```

---

#### 6. `reporting_effort_tlf_details` - TLF-Specific Attributes

**Purpose:** Store metadata unique to Tables/Listings/Figures

**Columns:**
```sql
CREATE TABLE reporting_effort_tlf_details (
    id INTEGER PRIMARY KEY,
    reporting_effort_item_id INTEGER NOT NULL UNIQUE,
    title_id INTEGER,                     -- FK to text_elements (type='title')
    population_flag_id INTEGER,           -- FK to text_elements (type='population_set')
    ich_category_id INTEGER,              -- FK to text_elements (type='ich_category')
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id) ON DELETE CASCADE,
    FOREIGN KEY (title_id) REFERENCES text_elements(id) ON DELETE SET NULL,
    FOREIGN KEY (population_flag_id) REFERENCES text_elements(id) ON DELETE SET NULL,
    FOREIGN KEY (ich_category_id) REFERENCES text_elements(id) ON DELETE SET NULL
);

CREATE INDEX idx_tlf_details_item_id ON reporting_effort_tlf_details(reporting_effort_item_id);
```

---

#### 7. `reporting_effort_dataset_details` - Dataset-Specific Attributes

**Purpose:** Store metadata unique to Datasets

**Columns:**
```sql
CREATE TABLE reporting_effort_dataset_details (
    id INTEGER PRIMARY KEY,
    reporting_effort_item_id INTEGER NOT NULL UNIQUE,
    label VARCHAR(255),
    sorting_order VARCHAR(255),
    acronyms JSON,  -- DuckDB native JSON support!
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id) ON DELETE CASCADE
);

CREATE INDEX idx_dataset_details_item_id ON reporting_effort_dataset_details(reporting_effort_item_id);
```

**Sample Data:**
```sql
INSERT INTO reporting_effort_dataset_details (reporting_effort_item_id, label, sorting_order, acronyms) VALUES
(4, 'Subject-Level Analysis Dataset', 'USUBJID', '["USUBJID", "SAFFL", "ITT"]'::JSON);
```

---

#### 8. `reporting_effort_item_trackers` - Workflow Management

**Purpose:** Track production and QC status, assignments, and progress for each item

**Columns:**
```sql
CREATE TABLE reporting_effort_item_trackers (
    id INTEGER PRIMARY KEY,
    reporting_effort_item_id INTEGER NOT NULL UNIQUE,
    production_programmer_id INTEGER,
    qc_programmer_id INTEGER,
    production_status VARCHAR(20) NOT NULL DEFAULT 'not_started',
    qc_status VARCHAR(20) NOT NULL DEFAULT 'not_started',
    due_date DATE,
    qc_completion_date DATE,
    priority INTEGER DEFAULT 3,           -- 1=High, 2=Medium, 3=Low
    qc_level VARCHAR(20),                 -- full, expedited, none
    in_production_flag BOOLEAN DEFAULT FALSE,
    unresolved_comment_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id) ON DELETE CASCADE,
    FOREIGN KEY (production_programmer_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (qc_programmer_id) REFERENCES users(id) ON DELETE SET NULL,
    CHECK (production_status IN ('not_started', 'in_progress', 'completed', 'on_hold')),
    CHECK (qc_status IN ('not_started', 'in_progress', 'completed', 'failed')),
    CHECK (priority IN (1, 2, 3)),
    CHECK (qc_level IN ('full', 'expedited', 'none', NULL))
);

CREATE INDEX idx_trackers_item_id ON reporting_effort_item_trackers(reporting_effort_item_id);
CREATE INDEX idx_trackers_production_programmer ON reporting_effort_item_trackers(production_programmer_id);
CREATE INDEX idx_trackers_qc_programmer ON reporting_effort_item_trackers(qc_programmer_id);
CREATE INDEX idx_trackers_status ON reporting_effort_item_trackers(production_status, qc_status);
CREATE INDEX idx_trackers_priority ON reporting_effort_item_trackers(priority);
CREATE INDEX idx_trackers_updated_at ON reporting_effort_item_trackers(updated_at);
```

**Sample Data:**
```sql
INSERT INTO reporting_effort_item_trackers (reporting_effort_item_id, production_programmer_id, production_status, priority, due_date) VALUES
(1, 2, 'in_progress', 1, '2024-04-15'),
(2, 2, 'completed', 2, '2024-04-20'),
(3, 3, 'not_started', 3, '2024-04-25');
```

---

#### 9. `tracker_comments` - Threaded Discussion System

**Purpose:** Allow programmers to discuss issues, ask questions, and track resolutions

**Columns:**
```sql
CREATE TABLE tracker_comments (
    id INTEGER PRIMARY KEY,
    tracker_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    parent_comment_id INTEGER,
    comment_text TEXT NOT NULL,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by_user_id INTEGER,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (tracker_id) REFERENCES reporting_effort_item_trackers(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_comment_id) REFERENCES tracker_comments(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_tracker_comments_tracker_id ON tracker_comments(tracker_id);
CREATE INDEX idx_tracker_comments_user_id ON tracker_comments(user_id);
CREATE INDEX idx_tracker_comments_parent_id ON tracker_comments(parent_comment_id);
CREATE INDEX idx_tracker_comments_resolved ON tracker_comments(is_resolved);
CREATE INDEX idx_tracker_comments_updated_at ON tracker_comments(updated_at);
```

**Sample Data:**
```sql
INSERT INTO tracker_comments (tracker_id, user_id, comment_text) VALUES
(1, 2, 'Started development. Need clarification on population set.'),
(1, 3, 'Population set should be Safety Population (SAFFL=Y)');

-- Reply to first comment
INSERT INTO tracker_comments (tracker_id, user_id, parent_comment_id, comment_text, is_resolved, resolved_by_user_id, resolved_at) VALUES
(1, 2, 1, 'Thanks, clarified. Issue resolved.', TRUE, 2, CURRENT_TIMESTAMP);
```

---

#### 10. `text_elements` - Centralized Text Storage

**Purpose:** Store reusable text snippets (titles, footnotes, acronyms, populations)

**Columns:**
```sql
CREATE TABLE text_elements (
    id INTEGER PRIMARY KEY,
    type VARCHAR(20) NOT NULL,
    label TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (type IN ('title', 'footnote', 'population_set', 'acronyms_set', 'ich_category'))
);

CREATE INDEX idx_text_elements_type ON text_elements(type);
CREATE INDEX idx_text_elements_updated_at ON text_elements(updated_at);

-- DuckDB full-text search (simpler than SQLite FTS5)
-- Use WHERE label LIKE '%search%' or implement custom FTS if needed
```

**Sample Data:**
```sql
INSERT INTO text_elements (type, label) VALUES
('title', 'Summary of Demographic and Baseline Characteristics'),
('title', 'Adverse Events by System Organ Class and Preferred Term'),
('footnote', 'Percentages are based on the number of subjects in each treatment group.'),
('population_set', 'Safety Population (SAFFL=Y)'),
('population_set', 'Intent-to-Treat Population (ITTFL=Y)'),
('ich_category', 'Efficacy'),
('acronyms_set', 'USUBJID'),
('acronyms_set', 'AVISIT');
```

---

#### 11-18. Junction Tables and Package Tables

**Complete schema follows same pattern as above. Key tables:**

- `reporting_effort_item_footnotes` (many-to-many)
- `reporting_effort_item_acronyms` (many-to-many)
- `packages` (template containers)
- `package_items` (polymorphic like reporting_effort_items)
- `package_tlf_details`
- `package_dataset_details`
- `package_item_footnotes`
- `package_item_acronyms`

---

#### 19. `audit_log` - Comprehensive Audit Trail

**Purpose:** Track all CRUD operations for regulatory compliance

**Columns:**
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,
    user_id INTEGER,
    user_email VARCHAR(255),
    changes_json JSON,  -- DuckDB native JSON!
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CHECK (action IN ('CREATE', 'UPDATE', 'DELETE'))
);

CREATE INDEX idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
```

---

#### 20. `table_change_log` - Polling Optimization Table

**Purpose:** Track last modification timestamp per table for efficient change detection

**Columns:**
```sql
CREATE TABLE table_change_log (
    id INTEGER PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL UNIQUE,
    last_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    change_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_table_change_log_table_name ON table_change_log(table_name);
CREATE INDEX idx_table_change_log_last_modified ON table_change_log(last_modified);
```

**Initialization:**
```sql
INSERT INTO table_change_log (table_name, last_modified, change_count) VALUES
('studies', CURRENT_TIMESTAMP, 0),
('database_releases', CURRENT_TIMESTAMP, 0),
('reporting_efforts', CURRENT_TIMESTAMP, 0),
('reporting_effort_items', CURRENT_TIMESTAMP, 0),
('reporting_effort_item_trackers', CURRENT_TIMESTAMP, 0),
('tracker_comments', CURRENT_TIMESTAMP, 0),
('packages', CURRENT_TIMESTAMP, 0),
('package_items', CURRENT_TIMESTAMP, 0),
('text_elements', CURRENT_TIMESTAMP, 0),
('users', CURRENT_TIMESTAMP, 0);
```

---

#### 21. `dashboard_metrics` - Cached Dashboard Data (Optional)

**Purpose:** Store pre-calculated metrics for fast dashboard loading

**Columns:**
```sql
CREATE TABLE dashboard_metrics (
    id INTEGER PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL UNIQUE,
    metric_value JSON NOT NULL,  -- Stores complex data structures
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP  -- NULL = never expires
);

CREATE INDEX idx_dashboard_metrics_name ON dashboard_metrics(metric_name);
CREATE INDEX idx_dashboard_metrics_expires ON dashboard_metrics(expires_at);
```

**Sample Cached Metrics:**
```sql
INSERT INTO dashboard_metrics (metric_name, metric_value, calculated_at) VALUES
('total_studies', '{"count": 15, "active": 10, "completed": 5}'::JSON, CURRENT_TIMESTAMP),
('tracker_summary', '{"not_started": 120, "in_progress": 45, "completed": 230}'::JSON, CURRENT_TIMESTAMP),
('programmer_workload', '[{"user_id": 2, "name": "John", "assigned": 25}, ...]'::JSON, CURRENT_TIMESTAMP);
```

---

## API Endpoints Specification

### Base URL: `http://localhost:8000/api/v1`

### Authentication Endpoints

#### POST `/auth/register`
**Purpose:** Register a new user account (ADMIN only)

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "role": "EDITOR",
  "department": "programming"
}
```

**Response:** 201 Created
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "EDITOR",
  "department": "programming",
  "is_active": true,
  "created_at": "2025-01-03T10:00:00"
}
```

---

#### POST `/auth/login`
**Purpose:** Authenticate and receive JWT token

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**Response:** 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "john_doe",
    "full_name": "John Doe",
    "role": "EDITOR",
    "department": "programming",
    "permissions": {
      "can_create": true,
      "can_edit": true,
      "can_delete": false,
      "can_manage_users": false,
      "can_view_audit": false
    }
  }
}
```

**Usage in subsequent requests:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

#### GET `/auth/me`
**Purpose:** Get current user info from JWT token

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** 200 OK
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "EDITOR",
  "department": "programming",
  "is_active": true,
  "permissions": {
    "can_create": true,
    "can_edit": true,
    "can_delete": false,
    "can_manage_users": false,
    "can_view_audit": false
  }
}
```

---

### Dashboard Endpoints

#### GET `/dashboard/metrics`
**Purpose:** Get key performance indicators and statistics for dashboard

**Query Parameters:**
- `refresh` (bool, optional): Force recalculation instead of using cache

**Response:** 200 OK
```json
{
  "studies": {
    "total": 15,
    "active": 10,
    "on_hold": 2,
    "completed": 3
  },
  "trackers": {
    "total": 450,
    "not_started": 120,
    "in_progress": 95,
    "completed": 230,
    "on_hold": 5
  },
  "workload": {
    "items_due_this_week": 25,
    "items_overdue": 8,
    "items_due_next_week": 40
  },
  "programmer_workload": [
    {
      "user_id": 2,
      "username": "john_prog",
      "full_name": "John Programmer",
      "assigned_production": 18,
      "assigned_qc": 12,
      "completed_this_month": 35
    },
    {
      "user_id": 3,
      "username": "jane_qc",
      "full_name": "Jane QC Lead",
      "assigned_production": 15,
      "assigned_qc": 20,
      "completed_this_month": 42
    }
  ],
  "recent_activity": [
    {
      "timestamp": "2025-01-03T14:30:00",
      "user": "john_prog",
      "action": "completed",
      "entity": "T-14.1.1 - Demographics Table"
    },
    {
      "timestamp": "2025-01-03T14:25:00",
      "user": "jane_qc",
      "action": "started_qc",
      "entity": "L-16.2.1 - Adverse Events Listing"
    }
  ],
  "calculated_at": "2025-01-03T15:00:00"
}
```

---

#### GET `/dashboard/charts/tracker-status-distribution`
**Purpose:** Get data for pie chart showing tracker status distribution

**Response:** 200 OK
```json
{
  "chart_type": "pie",
  "data": {
    "labels": ["Not Started", "In Progress", "Completed", "On Hold"],
    "values": [120, 95, 230, 5],
    "colors": ["#718096", "#3182CE", "#38A169", "#DD6B20"]
  }
}
```

---

#### GET `/dashboard/charts/programmer-workload`
**Purpose:** Get data for bar chart showing workload by programmer

**Response:** 200 OK
```json
{
  "chart_type": "bar",
  "data": {
    "x": ["John Programmer", "Jane QC Lead", "Bob Analyst"],
    "y": [30, 32, 25],
    "colors": ["#3182CE", "#805AD5", "#D69E2E"]
  }
}
```

---

#### GET `/dashboard/charts/items-timeline`
**Purpose:** Get data for Gantt chart showing items by due date

**Response:** 200 OK
```json
{
  "chart_type": "timeline",
  "data": [
    {
      "item_code": "T-14.1.1",
      "title": "Demographics Table",
      "programmer": "John Programmer",
      "start_date": "2024-04-01",
      "due_date": "2024-04-15",
      "status": "in_progress",
      "progress": 65
    },
    {
      "item_code": "L-16.2.1",
      "title": "Adverse Events Listing",
      "programmer": "Jane QC Lead",
      "start_date": "2024-04-05",
      "due_date": "2024-04-20",
      "status": "not_started",
      "progress": 0
    }
  ]
}
```

---

### Study Endpoints (with RBAC)

#### GET `/studies`
**Authorization:** All roles (ADMIN, EDITOR, VIEWER)

**Query Parameters:**
- `skip` (int, default=0): Pagination offset
- `limit` (int, default=100): Max results
- `search` (str, optional): Filter by study_label
- `status` (str, optional): Filter by status

**Response:** 200 OK
```json
[
  {
    "id": 1,
    "study_label": "STUDY-001-ONCOLOGY",
    "description": "Phase 3 Cancer Trial",
    "status": "active",
    "start_date": "2024-01-15",
    "target_completion_date": "2025-12-31",
    "database_releases_count": 2,
    "reporting_efforts_count": 5,
    "created_at": "2025-01-01T10:00:00",
    "updated_at": "2025-01-01T10:00:00"
  }
]
```

---

#### POST `/studies`
**Authorization:** ADMIN, EDITOR

**Request Body:**
```json
{
  "study_label": "STUDY-003-DIABETES",
  "description": "Type 2 Diabetes Treatment Study",
  "status": "active",
  "start_date": "2025-02-01",
  "target_completion_date": "2026-12-31"
}
```

**Response:** 201 Created

**Error Response (Insufficient Permissions):**
```json
{
  "detail": "Insufficient permissions. Required role: EDITOR or ADMIN"
}
```

---

#### DELETE `/studies/{study_id}`
**Authorization:** ADMIN only

**Response:** 204 No Content (success)

**Error:** 403 Forbidden (if EDITOR or VIEWER tries to delete)
```json
{
  "detail": "Insufficient permissions. Required role: ADMIN"
}
```

**Error:** 400 Bad Request (if dependent entities exist)
```json
{
  "detail": "Cannot delete study 'STUDY-001-ONCOLOGY': 2 database releases exist: Database Lock 2024-Q1, Database Lock 2024-Q2. Please delete all associated database releases first."
}
```

---

### Tracker Endpoints

#### GET `/trackers`
**Authorization:** All roles

**Query Parameters:**
- `reporting_effort_id` (int, optional)
- `production_programmer_id` (int, optional)
- `qc_programmer_id` (int, optional)
- `production_status` (str, optional)
- `qc_status` (str, optional)
- `priority` (int, optional)
- `overdue` (bool, optional): Show only overdue items

**Response:** 200 OK
```json
[
  {
    "id": 1,
    "reporting_effort_item_id": 1,
    "item": {
      "id": 1,
      "item_code": "T-14.1.1",
      "item_type": "TLF",
      "item_subtype": "TABLE",
      "reporting_effort": {
        "id": 1,
        "reporting_effort_label": "CSR Tables Package"
      }
    },
    "production_programmer": {
      "id": 2,
      "username": "john_prog",
      "full_name": "John Programmer"
    },
    "qc_programmer": {
      "id": 3,
      "username": "jane_qc",
      "full_name": "Jane QC Lead"
    },
    "production_status": "in_progress",
    "qc_status": "not_started",
    "due_date": "2024-04-15",
    "priority": 1,
    "qc_level": "full",
    "unresolved_comment_count": 2,
    "is_overdue": false,
    "days_until_due": 5
  }
]
```

---

#### GET `/trackers/my-workload`
**Purpose:** Get all items assigned to current user (production or QC)

**Authorization:** All roles (returns items for authenticated user)

**Response:** 200 OK
```json
{
  "production_items": [
    {
      "id": 1,
      "item_code": "T-14.1.1",
      "status": "in_progress",
      "due_date": "2024-04-15",
      "priority": 1
    }
  ],
  "qc_items": [
    {
      "id": 5,
      "item_code": "L-16.2.1",
      "status": "completed",
      "qc_status": "in_progress",
      "due_date": "2024-04-20"
    }
  ],
  "summary": {
    "production_total": 18,
    "production_completed": 12,
    "qc_total": 10,
    "qc_completed": 7,
    "overdue": 2
  }
}
```

---

#### PUT `/trackers/{tracker_id}`
**Authorization:** ADMIN, EDITOR

**Request Body (partial update allowed):**
```json
{
  "production_status": "completed",
  "qc_programmer_id": 3,
  "qc_status": "in_progress"
}
```

**Validation:** QC status cannot be "in_progress" or "completed" unless production_status = "completed"

**Response:** 200 OK (updated tracker)

---

#### POST `/trackers/bulk-assign`
**Purpose:** Assign multiple items to programmers at once

**Authorization:** ADMIN, EDITOR

**Request Body:**
```json
{
  "tracker_ids": [1, 2, 3, 4, 5],
  "production_programmer_id": 2,
  "qc_programmer_id": 3,
  "priority": 2
}
```

**Response:** 200 OK
```json
{
  "updated_count": 5,
  "tracker_ids": [1, 2, 3, 4, 5],
  "assignments": {
    "production_programmer": {
      "id": 2,
      "username": "john_prog",
      "full_name": "John Programmer"
    },
    "qc_programmer": {
      "id": 3,
      "username": "jane_qc",
      "full_name": "Jane QC Lead"
    }
  }
}
```

---

### Tracker Comment Endpoints

#### GET `/tracker-comments`
**Authorization:** All roles

**Query Parameters:**
- `tracker_id` (int, required)
- `include_resolved` (bool, default=true): Include resolved comments

**Response:** 200 OK (threaded structure)
```json
[
  {
    "id": 1,
    "tracker_id": 1,
    "user": {
      "id": 2,
      "username": "john_prog",
      "full_name": "John Programmer"
    },
    "parent_comment_id": null,
    "comment_text": "Need clarification on population set.",
    "is_resolved": false,
    "created_at": "2025-01-03T09:00:00",
    "updated_at": "2025-01-03T09:00:00",
    "replies": [
      {
        "id": 2,
        "parent_comment_id": 1,
        "user": {
          "id": 3,
          "username": "jane_qc",
          "full_name": "Jane QC Lead"
        },
        "comment_text": "Use Safety Population (SAFFL=Y).",
        "is_resolved": false,
        "created_at": "2025-01-03T09:15:00"
      },
      {
        "id": 3,
        "parent_comment_id": 1,
        "user": {
          "id": 2,
          "username": "john_prog",
          "full_name": "John Programmer"
        },
        "comment_text": "Thanks! Resolved.",
        "is_resolved": true,
        "resolved_by_user_id": 2,
        "resolved_at": "2025-01-03T09:30:00",
        "created_at": "2025-01-03T09:30:00"
      }
    ]
  }
]
```

---

#### POST `/tracker-comments`
**Authorization:** ADMIN, EDITOR

**Request Body:**
```json
{
  "tracker_id": 1,
  "comment_text": "Question about footnote placement.",
  "parent_comment_id": null
}
```

**Response:** 201 Created

**Side Effect:** Increments tracker's `unresolved_comment_count`

---

#### PUT `/tracker-comments/{comment_id}/resolve`
**Purpose:** Mark comment (and all replies) as resolved

**Authorization:** ADMIN, EDITOR, or comment author

**Request Body:**
```json
{
  "is_resolved": true
}
```

**Response:** 200 OK

**Side Effect:**
- Decrements tracker's `unresolved_comment_count`
- Sets `resolved_by_user_id` to current user
- Sets `resolved_at` to current timestamp

---

### Change Detection Endpoint (For Polling)

#### GET `/changes/check`
**Purpose:** Check which tables have been modified since a given timestamp

**Authorization:** All roles

**Query Parameters:**
- `tables` (str, required): Comma-separated table names
- `since` (datetime, optional): ISO format timestamp

**Response:** 200 OK
```json
{
  "current_timestamp": "2025-01-03T10:05:30",
  "changes": {
    "studies": {
      "has_changes": true,
      "last_modified": "2025-01-03T10:05:15",
      "change_count": 5
    },
    "packages": {
      "has_changes": false,
      "last_modified": "2025-01-03T09:30:00",
      "change_count": 2
    },
    "trackers": {
      "has_changes": true,
      "last_modified": "2025-01-03T10:04:00",
      "change_count": 12
    }
  }
}
```

---

## Backend Implementation Guide

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py          # Main API router
│   │       ├── auth.py            # Authentication endpoints
│   │       ├── dashboard.py       # Dashboard metrics and charts
│   │       ├── studies.py         # Study endpoints (RBAC protected)
│   │       ├── database_releases.py
│   │       ├── reporting_efforts.py
│   │       ├── reporting_effort_items.py
│   │       ├── trackers.py        # Tracker workflow endpoints
│   │       ├── tracker_comments.py
│   │       ├── packages.py
│   │       ├── package_items.py
│   │       ├── text_elements.py
│   │       ├── users.py           # User management (ADMIN only)
│   │       ├── audit_log.py       # Audit log viewer (ADMIN only)
│   │       └── changes.py         # Change detection endpoint
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── base.py                # BaseCRUD (NO retry logic needed!)
│   │   ├── study.py
│   │   ├── database_release.py
│   │   ├── reporting_effort.py
│   │   ├── reporting_effort_item.py
│   │   ├── tracker.py
│   │   ├── tracker_comment.py
│   │   ├── package.py
│   │   ├── text_element.py
│   │   ├── user.py
│   │   ├── audit_log.py
│   │   └── dashboard.py           # Dashboard metrics aggregation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                # SQLAlchemy Base and mixins
│   │   ├── user.py
│   │   ├── study.py
│   │   ├── database_release.py
│   │   ├── reporting_effort.py
│   │   ├── reporting_effort_item.py
│   │   ├── tracker.py
│   │   ├── tracker_comment.py
│   │   ├── package.py
│   │   ├── text_element.py
│   │   ├── audit_log.py
│   │   └── table_change_log.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py                # UserCreate, UserUpdate, UserResponse
│   │   ├── auth.py                # LoginRequest, TokenResponse, PermissionsResponse
│   │   ├── dashboard.py           # DashboardMetrics, ChartData
│   │   ├── study.py
│   │   ├── database_release.py
│   │   ├── reporting_effort.py
│   │   ├── reporting_effort_item.py
│   │   ├── tracker.py
│   │   ├── tracker_comment.py
│   │   ├── package.py
│   │   ├── text_element.py
│   │   └── change.py              # ChangeCheckResponse
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Settings (database URL, JWT secret, etc.)
│   │   ├── security.py            # Password hashing, JWT tokens
│   │   ├── permissions.py         # Role-based access control (RBAC)
│   │   └── dependencies.py        # FastAPI dependencies (get_db, get_current_user, require_role)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py             # DuckDB session factory (synchronous)
│   │   ├── init_db.py             # Database initialization script
│   │   └── change_tracker.py      # Utilities for table_change_log updates
│   └── utils/
│       ├── __init__.py
│       ├── normalization.py       # Case-insensitive label comparison
│       └── audit.py               # Audit logging helper functions
├── migrations/                    # Alembic migration files
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_auth.py               # Authentication and authorization tests
│   ├── test_dashboard.py          # Dashboard metrics tests
│   ├── test_studies.py
│   ├── test_trackers.py
│   ├── test_rbac.py               # Role-based access control tests
│   └── test_changes.py
├── alembic.ini
├── pyproject.toml                 # Dependencies (if using uv/poetry)
├── requirements.txt
└── README.md
```

---

### Key Implementation Patterns

#### 1. DuckDB Session Management (Much Simpler!)

**File:** `app/db/session.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create synchronous engine with DuckDB
engine = create_engine(
    settings.DATABASE_URL,  # "duckdb:///./tracker.duckdb"
    echo=settings.DEBUG,
    pool_size=10,  # DuckDB handles concurrency well
    max_overflow=20
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# Dependency for FastAPI (synchronous - much simpler!)
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

**Key Differences from SQLite:**
- ✅ No async/await complexity
- ✅ No WAL mode setup
- ✅ No foreign key pragmas
- ✅ No busy timeout
- ✅ No retry logic needed!

---

#### 2. BaseCRUD (Simplified - No Retry Logic!)

**File:** `app/crud/base.py`

```python
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Get a single record by ID"""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records with pagination"""
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record - NO RETRY LOGIC NEEDED!"""
        obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType:
        """Update an existing record"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else obj_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Delete a record by ID"""
        obj = self.get(db, id=id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
```

**Key Differences from SQLite Version:**
- ✅ All methods are synchronous (no `async`/`await`)
- ✅ No retry logic (DuckDB handles locks internally)
- ✅ No `BEGIN IMMEDIATE` needed
- ✅ Simpler, cleaner code

---

#### 3. Role-Based Access Control (RBAC)

**File:** `app/core/permissions.py`

```python
from enum import Enum
from typing import List
from fastapi import HTTPException, status

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"

class Permission:
    """Define permissions for each role"""

    ROLE_PERMISSIONS = {
        UserRole.ADMIN: {
            "can_create": True,
            "can_edit": True,
            "can_delete": True,
            "can_manage_users": True,
            "can_view_audit": True,
            "can_bulk_assign": True
        },
        UserRole.EDITOR: {
            "can_create": True,
            "can_edit": True,
            "can_delete": False,  # Can delete items but not studies
            "can_manage_users": False,
            "can_view_audit": False,
            "can_bulk_assign": True
        },
        UserRole.VIEWER: {
            "can_create": False,
            "can_edit": False,
            "can_delete": False,
            "can_manage_users": False,
            "can_view_audit": False,
            "can_bulk_assign": False
        }
    }

    @classmethod
    def get_permissions(cls, role: UserRole) -> dict:
        """Get permissions dictionary for a role"""
        return cls.ROLE_PERMISSIONS.get(role, cls.ROLE_PERMISSIONS[UserRole.VIEWER])

    @classmethod
    def can_access(cls, user_role: UserRole, required_role: UserRole) -> bool:
        """Check if user role has sufficient access"""
        role_hierarchy = {
            UserRole.ADMIN: 3,
            UserRole.EDITOR: 2,
            UserRole.VIEWER: 1
        }
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 99)

def require_role(allowed_roles: List[UserRole]):
    """Decorator to enforce role-based access control"""
    def decorator(func):
        def wrapper(current_user, *args, **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required role: {' or '.join([r.value for r in allowed_roles])}"
                )
            return func(current_user, *args, **kwargs)
        return wrapper
    return decorator
```

**File:** `app/core/dependencies.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.core.config import settings
from app.crud.user import user_crud
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate JWT token and return current user
    Raises 401 if token is invalid or user not found
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user = user_crud.get(db, id=user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require ADMIN role"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Required role: ADMIN"
        )
    return current_user

def require_editor_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require EDITOR or ADMIN role"""
    if current_user.role not in ["ADMIN", "EDITOR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Required role: EDITOR or ADMIN"
        )
    return current_user
```

---

#### 4. Protected API Endpoint Example

**File:** `app/api/v1/studies.py`

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user, require_editor_or_admin, require_admin
from app.crud.study import study_crud
from app.crud.database_release import database_release_crud
from app.schemas.study import StudyCreate, StudyUpdate, StudyResponse
from app.models.user import User
from app.db.change_tracker import track_table_change
from app.utils.audit import log_audit_event

router = APIRouter()

@router.get("/studies", response_model=List[StudyResponse])
def list_studies(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # All roles can view
):
    """List all studies with optional filters"""
    if search:
        studies = study_crud.search(db, search_term=search)
    elif status:
        studies = study_crud.get_by_status(db, status=status)
    else:
        studies = study_crud.get_multi(db, skip=skip, limit=limit)
    return studies

@router.post("/studies", response_model=StudyResponse, status_code=status.HTTP_201_CREATED)
def create_study(
    study_in: StudyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin)  # EDITOR or ADMIN only
):
    """Create a new study (EDITOR or ADMIN)"""
    # Check for case-insensitive duplicate
    existing = study_crud.check_duplicate_label(db, study_label=study_in.study_label)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A study with label '{study_in.study_label}' already exists "
                   f"(found: '{existing.study_label}'). Please use a different label."
        )

    # Create study
    study = study_crud.create(db, obj_in=study_in)

    # Track change for polling
    track_table_change(db, "studies")

    # Audit log
    log_audit_event(
        db,
        table_name="studies",
        record_id=study.id,
        action="CREATE",
        user_id=current_user.id,
        after_data=study.__dict__
    )

    return study

@router.delete("/studies/{study_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_study(
    study_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  # ADMIN only
):
    """
    Delete a study (ADMIN ONLY)
    DELETION PROTECTION: Blocks deletion if dependent database_releases exist
    """
    study = study_crud.get(db, id=study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    # Check for dependent database releases
    releases = database_release_crud.get_by_study_id(db, study_id=study_id)
    if releases:
        release_labels = [r.database_release_label for r in releases]
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete study '{study.study_label}': "
                   f"{len(releases)} database release(s) exist: {', '.join(release_labels)}. "
                   f"Please delete all associated database releases first."
        )

    # Audit before deletion
    log_audit_event(
        db, "studies", study.id, "DELETE", current_user.id,
        before_data=study.__dict__
    )

    # Delete
    study_crud.delete(db, id=study_id)
    track_table_change(db, "studies")

    return None
```

---

#### 5. Dashboard Metrics Calculation

**File:** `app/crud/dashboard.py`

```python
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.study import Study
from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
from app.models.user import User
from datetime import datetime, timedelta

class DashboardCRUD:
    def get_study_metrics(self, db: Session) -> dict:
        """Calculate study statistics"""
        total = db.query(Study).count()
        active = db.query(Study).filter(Study.status == 'active').count()
        on_hold = db.query(Study).filter(Study.status == 'on_hold').count()
        completed = db.query(Study).filter(Study.status == 'completed').count()

        return {
            "total": total,
            "active": active,
            "on_hold": on_hold,
            "completed": completed
        }

    def get_tracker_metrics(self, db: Session) -> dict:
        """Calculate tracker status distribution"""
        total = db.query(ReportingEffortItemTracker).count()

        not_started = db.query(ReportingEffortItemTracker).filter(
            ReportingEffortItemTracker.production_status == 'not_started'
        ).count()

        in_progress = db.query(ReportingEffortItemTracker).filter(
            ReportingEffortItemTracker.production_status == 'in_progress'
        ).count()

        completed = db.query(ReportingEffortItemTracker).filter(
            ReportingEffortItemTracker.production_status == 'completed'
        ).count()

        on_hold = db.query(ReportingEffortItemTracker).filter(
            ReportingEffortItemTracker.production_status == 'on_hold'
        ).count()

        return {
            "total": total,
            "not_started": not_started,
            "in_progress": in_progress,
            "completed": completed,
            "on_hold": on_hold
        }

    def get_workload_metrics(self, db: Session) -> dict:
        """Calculate workload metrics"""
        today = datetime.now().date()
        week_end = today + timedelta(days=7)

        due_this_week = db.query(ReportingEffortItemTracker).filter(
            ReportingEffortItemTracker.due_date >= today,
            ReportingEffortItemTracker.due_date <= week_end,
            ReportingEffortItemTracker.production_status != 'completed'
        ).count()

        overdue = db.query(ReportingEffortItemTracker).filter(
            ReportingEffortItemTracker.due_date < today,
            ReportingEffortItemTracker.production_status != 'completed'
        ).count()

        next_week_start = week_end + timedelta(days=1)
        next_week_end = next_week_start + timedelta(days=7)

        due_next_week = db.query(ReportingEffortItemTracker).filter(
            ReportingEffortItemTracker.due_date >= next_week_start,
            ReportingEffortItemTracker.due_date <= next_week_end,
            ReportingEffortItemTracker.production_status != 'completed'
        ).count()

        return {
            "items_due_this_week": due_this_week,
            "items_overdue": overdue,
            "items_due_next_week": due_next_week
        }

    def get_programmer_workload(self, db: Session) -> list:
        """Calculate workload by programmer"""
        programmers = db.query(User).filter(
            User.role.in_(['ADMIN', 'EDITOR']),
            User.is_active == True
        ).all()

        workload = []
        for programmer in programmers:
            assigned_production = db.query(ReportingEffortItemTracker).filter(
                ReportingEffortItemTracker.production_programmer_id == programmer.id,
                ReportingEffortItemTracker.production_status != 'completed'
            ).count()

            assigned_qc = db.query(ReportingEffortItemTracker).filter(
                ReportingEffortItemTracker.qc_programmer_id == programmer.id,
                ReportingEffortItemTracker.qc_status != 'completed'
            ).count()

            # Completed this month
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            completed_this_month = db.query(ReportingEffortItemTracker).filter(
                (ReportingEffortItemTracker.production_programmer_id == programmer.id) |
                (ReportingEffortItemTracker.qc_programmer_id == programmer.id),
                ReportingEffortItemTracker.updated_at >= month_start,
                (ReportingEffortItemTracker.production_status == 'completed') |
                (ReportingEffortItemTracker.qc_status == 'completed')
            ).count()

            workload.append({
                "user_id": programmer.id,
                "username": programmer.username,
                "full_name": programmer.full_name,
                "assigned_production": assigned_production,
                "assigned_qc": assigned_qc,
                "completed_this_month": completed_this_month
            })

        return workload

    def get_chart_data_tracker_distribution(self, db: Session) -> dict:
        """Get data for tracker status pie chart"""
        metrics = self.get_tracker_metrics(db)

        return {
            "chart_type": "pie",
            "data": {
                "labels": ["Not Started", "In Progress", "Completed", "On Hold"],
                "values": [
                    metrics["not_started"],
                    metrics["in_progress"],
                    metrics["completed"],
                    metrics["on_hold"]
                ],
                "colors": ["#718096", "#3182CE", "#38A169", "#DD6B20"]
            }
        }

    def get_chart_data_programmer_workload(self, db: Session) -> dict:
        """Get data for programmer workload bar chart"""
        workload = self.get_programmer_workload(db)

        return {
            "chart_type": "bar",
            "data": {
                "x": [w["full_name"] for w in workload],
                "y": [w["assigned_production"] + w["assigned_qc"] for w in workload],
                "colors": ["#3182CE"] * len(workload)
            }
        }

dashboard_crud = DashboardCRUD()
```

**File:** `app/api/v1/dashboard.py`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.crud.dashboard import dashboard_crud
from app.models.user import User

router = APIRouter()

@router.get("/dashboard/metrics")
def get_dashboard_metrics(
    refresh: bool = Query(False, description="Force recalculation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive dashboard metrics
    All roles can access
    """
    return {
        "studies": dashboard_crud.get_study_metrics(db),
        "trackers": dashboard_crud.get_tracker_metrics(db),
        "workload": dashboard_crud.get_workload_metrics(db),
        "programmer_workload": dashboard_crud.get_programmer_workload(db),
        "calculated_at": datetime.utcnow().isoformat()
    }

@router.get("/dashboard/charts/tracker-status-distribution")
def get_tracker_status_chart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pie chart data for tracker status distribution"""
    return dashboard_crud.get_chart_data_tracker_distribution(db)

@router.get("/dashboard/charts/programmer-workload")
def get_programmer_workload_chart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bar chart data for programmer workload"""
    return dashboard_crud.get_chart_data_programmer_workload(db)
```

---

## Frontend Implementation Guide (Reflex)

### Project Structure

```
frontend/
├── pearl_app/
│   ├── __init__.py
│   ├── pearl_app.py              # Main app entry, routing
│   ├── state/
│   │   ├── __init__.py
│   │   ├── base_state.py         # Shared state and API client
│   │   ├── auth_state.py         # Login/logout, current user, permissions
│   │   ├── dashboard_state.py    # Dashboard metrics and charts
│   │   ├── study_state.py        # Study management state
│   │   ├── package_state.py      # Package management state
│   │   ├── tracker_state.py      # Tracker workflow state
│   │   └── sync_state.py         # Polling background task
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── index.py              # Home redirect or public landing
│   │   ├── login.py              # Login page
│   │   ├── dashboard.py          # Main dashboard with charts/KPIs
│   │   ├── studies.py            # Study management (tree view)
│   │   ├── packages.py           # Package management
│   │   ├── tracker.py            # Tracker workflow (Kanban + workload)
│   │   ├── text_elements.py      # Text library
│   │   ├── users.py              # User management (ADMIN only)
│   │   └── audit.py              # Audit log viewer (ADMIN only)
│   ├── components/
│   │   ├── __init__.py
│   │   ├── layout.py             # Header, sidebar, footer
│   │   ├── sidebar.py            # Navigation sidebar (role-aware)
│   │   ├── tree_view.py          # Hierarchical tree component
│   │   ├── data_table.py         # Sortable, filterable table
│   │   ├── kanban_board.py       # Drag-and-drop Kanban board
│   │   ├── charts.py             # Plotly chart wrappers
│   │   ├── forms.py              # Reusable form components
│   │   ├── modals.py             # Modal dialogs
│   │   ├── badges.py             # Role, status, priority badges
│   │   └── protected_route.py    # Route wrapper for role checks
│   └── api_client/
│       ├── __init__.py
│       └── client.py             # HTTP client with retry logic
├── assets/
│   ├── styles.css                # Custom CSS
│   ├── logo.png
│   └── favicon.ico
├── rxconfig.py                   # Reflex configuration
└── requirements.txt
```

---

### Comprehensive Frontend Components

#### 1. Dashboard Page with Charts

**File:** `pearl_app/pages/dashboard.py`

```python
import reflex as rx
from pearl_app.state.dashboard_state import DashboardState
from pearl_app.components.charts import pie_chart, bar_chart, metric_card
from pearl_app.components.layout import page_layout

def dashboard_page() -> rx.Component:
    """
    Main dashboard with KPIs, charts, and recent activity
    Shows different views based on user role
    """

    return page_layout(
        rx.vstack(
            # Page Header
            rx.heading("Dashboard", size="2xl", margin_bottom="2rem"),

            # KPI Cards Row
            rx.hstack(
                metric_card(
                    title="Total Studies",
                    value=DashboardState.studies_metrics["total"],
                    subtitle=f"{DashboardState.studies_metrics['active']} active",
                    icon="📚",
                    color="blue"
                ),
                metric_card(
                    title="Total Trackers",
                    value=DashboardState.tracker_metrics["total"],
                    subtitle=f"{DashboardState.tracker_metrics['in_progress']} in progress",
                    icon="📊",
                    color="green"
                ),
                metric_card(
                    title="Due This Week",
                    value=DashboardState.workload_metrics["items_due_this_week"],
                    subtitle=f"{DashboardState.workload_metrics['items_overdue']} overdue",
                    icon="⏰",
                    color="orange",
                    alert=DashboardState.workload_metrics["items_overdue"] > 0
                ),
                metric_card(
                    title="My Workload",
                    value=DashboardState.my_workload_count,
                    subtitle="assigned items",
                    icon="👤",
                    color="purple"
                ),
                spacing="1rem",
                width="100%"
            ),

            # Charts Row
            rx.hstack(
                # Tracker Status Distribution (Pie Chart)
                rx.box(
                    rx.heading("Tracker Status Distribution", size="md", margin_bottom="1rem"),
                    rx.cond(
                        DashboardState.loading_charts,
                        rx.spinner(size="xl"),
                        pie_chart(
                            labels=DashboardState.tracker_chart_data["labels"],
                            values=DashboardState.tracker_chart_data["values"],
                            colors=DashboardState.tracker_chart_data["colors"]
                        )
                    ),
                    padding="1.5rem",
                    border="1px solid #E2E8F0",
                    border_radius="0.5rem",
                    width="50%"
                ),

                # Programmer Workload (Bar Chart)
                rx.box(
                    rx.heading("Programmer Workload", size="md", margin_bottom="1rem"),
                    rx.cond(
                        DashboardState.loading_charts,
                        rx.spinner(size="xl"),
                        bar_chart(
                            x=DashboardState.workload_chart_data["x"],
                            y=DashboardState.workload_chart_data["y"],
                            title="Active Assignments by Programmer"
                        )
                    ),
                    padding="1.5rem",
                    border="1px solid #E2E8F0",
                    border_radius="0.5rem",
                    width="50%"
                ),
                spacing="1rem",
                width="100%"
            ),

            # Recent Activity Feed
            rx.box(
                rx.heading("Recent Activity", size="md", margin_bottom="1rem"),
                rx.cond(
                    DashboardState.loading_activity,
                    rx.spinner(),
                    rx.vstack(
                        rx.foreach(
                            DashboardState.recent_activity,
                            lambda activity: rx.hstack(
                                rx.text(activity["timestamp"], font_size="0.875rem", color="gray.500"),
                                rx.badge(activity["user"], color_scheme="blue"),
                                rx.text(activity["action"]),
                                rx.text(activity["entity"], font_weight="bold"),
                                spacing="0.5rem",
                                padding="0.5rem",
                                border_bottom="1px solid #E2E8F0"
                            )
                        ),
                        width="100%"
                    )
                ),
                padding="1.5rem",
                border="1px solid #E2E8F0",
                border_radius="0.5rem",
                width="100%",
                margin_top="2rem"
            ),

            width="100%",
            spacing="2rem"
        ),

        # Load dashboard data on mount
        on_mount=DashboardState.load_dashboard_data()
    )
```

**File:** `pearl_app/state/dashboard_state.py`

```python
import reflex as rx
from typing import List, Dict
from datetime import datetime
from pearl_app.api_client.client import api_client

class DashboardState(rx.State):
    """State management for dashboard metrics and charts"""

    # Metrics
    studies_metrics: Dict = {
        "total": 0,
        "active": 0,
        "on_hold": 0,
        "completed": 0
    }

    tracker_metrics: Dict = {
        "total": 0,
        "not_started": 0,
        "in_progress": 0,
        "completed": 0,
        "on_hold": 0
    }

    workload_metrics: Dict = {
        "items_due_this_week": 0,
        "items_overdue": 0,
        "items_due_next_week": 0
    }

    programmer_workload: List[Dict] = []
    recent_activity: List[Dict] = []
    my_workload_count: int = 0

    # Chart data
    tracker_chart_data: Dict = {
        "labels": [],
        "values": [],
        "colors": []
    }

    workload_chart_data: Dict = {
        "x": [],
        "y": []
    }

    # Loading states
    loading_metrics: bool = False
    loading_charts: bool = False
    loading_activity: bool = False

    # Auto-refresh
    last_refresh: datetime = None

    async def load_dashboard_data(self):
        """Load all dashboard data"""
        self.loading_metrics = True
        self.loading_charts = True
        self.loading_activity = True

        try:
            # Fetch all dashboard data from backend
            metrics = await api_client.get("/dashboard/metrics")

            # Update metrics
            self.studies_metrics = metrics["studies"]
            self.tracker_metrics = metrics["trackers"]
            self.workload_metrics = metrics["workload"]
            self.programmer_workload = metrics["programmer_workload"]

            # Fetch my workload
            my_workload = await api_client.get("/trackers/my-workload")
            self.my_workload_count = my_workload["summary"]["production_total"] + my_workload["summary"]["qc_total"]

            # Fetch chart data
            tracker_chart = await api_client.get("/dashboard/charts/tracker-status-distribution")
            self.tracker_chart_data = tracker_chart["data"]

            workload_chart = await api_client.get("/dashboard/charts/programmer-workload")
            self.workload_chart_data = workload_chart["data"]

            # Recent activity (mock for now - implement in backend)
            self.recent_activity = [
                {
                    "timestamp": "2 minutes ago",
                    "user": "john_prog",
                    "action": "completed",
                    "entity": "T-14.1.1 - Demographics Table"
                },
                {
                    "timestamp": "15 minutes ago",
                    "user": "jane_qc",
                    "action": "started QC",
                    "entity": "L-16.2.1 - Adverse Events Listing"
                }
            ]

            self.last_refresh = datetime.now()

        except Exception as e:
            print(f"Error loading dashboard: {e}")
        finally:
            self.loading_metrics = False
            self.loading_charts = False
            self.loading_activity = False

    @rx.background
    async def auto_refresh_dashboard(self):
        """Background task to refresh dashboard every 30 seconds"""
        while True:
            await asyncio.sleep(30)
            async with self:
                await self.load_dashboard_data()
```

---

#### 2. Chart Components (Plotly Integration)

**File:** `pearl_app/components/charts.py`

```python
import reflex as rx
import plotly.graph_objects as go

def pie_chart(labels: list, values: list, colors: list) -> rx.Component:
    """
    Pie chart component using Plotly

    Args:
        labels: Category labels
        values: Numeric values
        colors: Hex color codes
    """
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.3,  # Donut chart
        textinfo='label+percent',
        textposition='auto'
    )])

    fig.update_layout(
        showlegend=True,
        height=350,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    return rx.plotly(data=fig)


def bar_chart(x: list, y: list, title: str = "") -> rx.Component:
    """
    Bar chart component using Plotly

    Args:
        x: X-axis labels
        y: Y-axis values
        title: Chart title
    """
    fig = go.Figure(data=[go.Bar(
        x=x,
        y=y,
        marker_color='#3182CE',
        text=y,
        textposition='auto'
    )])

    fig.update_layout(
        title=title,
        xaxis_title="Programmer",
        yaxis_title="Assigned Items",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return rx.plotly(data=fig)


def metric_card(
    title: str,
    value: int,
    subtitle: str = "",
    icon: str = "",
    color: str = "blue",
    alert: bool = False
) -> rx.Component:
    """
    Metric card component for KPI display

    Args:
        title: Card title
        value: Main numeric value
        subtitle: Additional context
        icon: Emoji or icon
        color: Color scheme (blue, green, orange, purple, red)
        alert: If True, use alert styling (red)
    """
    color_schemes = {
        "blue": {"bg": "#EBF8FF", "text": "#2C5282"},
        "green": {"bg": "#F0FFF4", "text": "#22543D"},
        "orange": {"bg": "#FFFAF0", "text": "#7C2D12"},
        "purple": {"bg": "#FAF5FF", "text": "#44337A"},
        "red": {"bg": "#FFF5F5", "text": "#742A2A"}
    }

    scheme = color_schemes.get("red" if alert else color, color_schemes["blue"])

    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(icon, font_size="2rem") if icon else rx.fragment(),
                rx.text(title, font_size="0.875rem", color="gray.600", font_weight="medium"),
                justify="space-between",
                width="100%"
            ),
            rx.text(
                str(value),
                font_size="2.5rem",
                font_weight="bold",
                color=scheme["text"]
            ),
            rx.text(subtitle, font_size="0.75rem", color="gray.500") if subtitle else rx.fragment(),
            spacing="0.5rem",
            align_items="flex-start"
        ),
        padding="1.5rem",
        background=scheme["bg"],
        border_radius="0.5rem",
        border=f"2px solid {scheme['text']}" if alert else "none",
        width="25%",
        min_width="200px"
    )
```

**Installation:**
```bash
pip install plotly reflex-plotly
```

---

#### 3. Tracker Kanban Board

**File:** `pearl_app/components/kanban_board.py`

```python
import reflex as rx
from typing import List, Dict

def kanban_column(
    title: str,
    items: List[Dict],
    status: str,
    color: str
) -> rx.Component:
    """
    Single Kanban column

    Args:
        title: Column title (e.g., "Not Started")
        items: List of tracker items
        status: Status filter value
        color: Column header color
    """
    return rx.box(
        rx.vstack(
            # Column Header
            rx.hstack(
                rx.heading(title, size="md", color="white"),
                rx.badge(
                    str(len(items)),
                    color_scheme="white",
                    variant="solid"
                ),
                justify="space-between",
                width="100%",
                padding="1rem",
                background=color,
                border_radius="0.5rem 0.5rem 0 0"
            ),

            # Column Items
            rx.vstack(
                rx.foreach(
                    items,
                    lambda item: kanban_card(item)
                ),
                spacing="0.75rem",
                padding="1rem",
                background="#F7FAFC",
                min_height="400px",
                overflow_y="auto",
                width="100%"
            ),

            spacing="0",
            width="100%"
        ),
        width="23%",
        min_width="280px",
        border="1px solid #E2E8F0",
        border_radius="0.5rem"
    )


def kanban_card(item: Dict) -> rx.Component:
    """
    Single Kanban card for a tracker item

    Args:
        item: Tracker item dictionary
    """
    return rx.box(
        rx.vstack(
            # Item Code and Type
            rx.hstack(
                rx.badge(
                    item["item"]["item_code"],
                    color_scheme="blue",
                    font_weight="bold"
                ),
                rx.badge(
                    item["item"]["item_subtype"],
                    color_scheme="gray",
                    variant="outline"
                ),
                justify="space-between",
                width="100%"
            ),

            # Title (if TLF)
            rx.text(
                item["item"]["tlf_details"]["title"]["label"][:50] + "..."
                if len(item["item"]["tlf_details"]["title"]["label"]) > 50
                else item["item"]["tlf_details"]["title"]["label"],
                font_size="0.875rem",
                font_weight="medium",
                color="gray.700"
            ) if item["item"]["item_type"] == "TLF" else rx.fragment(),

            # Programmer Assignment
            rx.hstack(
                rx.text("👤", font_size="0.75rem"),
                rx.text(
                    item["production_programmer"]["full_name"][:20]
                    if item["production_programmer"]
                    else "Unassigned",
                    font_size="0.75rem",
                    color="gray.600"
                ),
                spacing="0.25rem"
            ),

            # Due Date and Priority
            rx.hstack(
                rx.badge(
                    f"Priority {item['priority']}",
                    color_scheme="red" if item['priority'] == 1
                                else "orange" if item['priority'] == 2
                                else "green"
                ),
                rx.text(
                    f"Due: {item['due_date']}" if item['due_date'] else "No due date",
                    font_size="0.75rem",
                    color="red" if item.get("is_overdue") else "gray.600",
                    font_weight="bold" if item.get("is_overdue") else "normal"
                ),
                justify="space-between",
                width="100%"
            ),

            # Unresolved Comments Badge
            rx.cond(
                item["unresolved_comment_count"] > 0,
                rx.badge(
                    f"{item['unresolved_comment_count']} unresolved comments",
                    color_scheme="yellow"
                )
            ),

            spacing="0.5rem",
            align_items="flex-start"
        ),
        padding="1rem",
        background="white",
        border_radius="0.5rem",
        box_shadow="0 1px 3px rgba(0,0,0,0.1)",
        cursor="pointer",
        _hover={"box_shadow": "0 4px 6px rgba(0,0,0,0.1)"},
        on_click=lambda: TrackerState.open_tracker_detail(item["id"])
    )


def kanban_board(trackers: List[Dict]) -> rx.Component:
    """
    Complete Kanban board with all columns

    Args:
        trackers: List of all tracker items
    """
    # Filter items by status
    not_started = [t for t in trackers if t["production_status"] == "not_started"]
    in_progress = [t for t in trackers if t["production_status"] == "in_progress"]
    completed = [t for t in trackers if t["production_status"] == "completed"]
    on_hold = [t for t in trackers if t["production_status"] == "on_hold"]

    return rx.hstack(
        kanban_column("Not Started", not_started, "not_started", "#718096"),
        kanban_column("In Progress", in_progress, "in_progress", "#3182CE"),
        kanban_column("Completed", completed, "completed", "#38A169"),
        kanban_column("On Hold", on_hold, "on_hold", "#DD6B20"),
        spacing="1rem",
        width="100%",
        overflow_x="auto"
    )
```

**File:** `pearl_app/pages/tracker.py`

```python
import reflex as rx
from pearl_app.state.tracker_state import TrackerState
from pearl_app.components.kanban_board import kanban_board
from pearl_app.components.layout import page_layout

def tracker_page() -> rx.Component:
    """
    Tracker workflow page with Kanban board and filters
    """

    return page_layout(
        rx.vstack(
            # Page Header with Filters
            rx.hstack(
                rx.heading("Tracker Workflow", size="2xl"),
                rx.spacer(),
                rx.select(
                    ["All Studies", "STUDY-001-ONCOLOGY", "STUDY-002-CARDIO"],
                    placeholder="Filter by Study",
                    on_change=TrackerState.set_study_filter
                ),
                rx.select(
                    ["All Programmers", "My Items Only"],
                    placeholder="Filter by Programmer",
                    on_change=TrackerState.set_programmer_filter
                ),
                rx.button(
                    "Bulk Assign",
                    on_click=TrackerState.open_bulk_assign_modal,
                    color_scheme="blue"
                ),
                width="100%",
                padding="1rem"
            ),

            # Loading Spinner or Kanban Board
            rx.cond(
                TrackerState.loading,
                rx.center(
                    rx.spinner(size="xl"),
                    height="400px"
                ),
                kanban_board(TrackerState.filtered_trackers)
            ),

            # My Workload Summary (always visible at bottom)
            rx.box(
                rx.heading("My Workload", size="md", margin_bottom="1rem"),
                rx.hstack(
                    rx.stat(
                        rx.stat_label("Production"),
                        rx.stat_number(TrackerState.my_workload_summary["production_total"]),
                        rx.stat_help_text(
                            f"{TrackerState.my_workload_summary['production_completed']} completed"
                        )
                    ),
                    rx.stat(
                        rx.stat_label("QC"),
                        rx.stat_number(TrackerState.my_workload_summary["qc_total"]),
                        rx.stat_help_text(
                            f"{TrackerState.my_workload_summary['qc_completed']} completed"
                        )
                    ),
                    rx.stat(
                        rx.stat_label("Overdue"),
                        rx.stat_number(
                            TrackerState.my_workload_summary["overdue"],
                            color="red" if TrackerState.my_workload_summary["overdue"] > 0 else "green"
                        )
                    ),
                    spacing="2rem"
                ),
                padding="1.5rem",
                background="#F7FAFC",
                border_radius="0.5rem",
                margin_top="2rem",
                width="100%"
            ),

            width="100%",
            spacing="1rem"
        ),

        on_mount=TrackerState.load_trackers()
    )
```

---

#### 4. Role-Based Sidebar Navigation

**File:** `pearl_app/components/sidebar.py`

```python
import reflex as rx
from pearl_app.state.auth_state import AuthState

def nav_item(
    label: str,
    icon: str,
    route: str,
    badge: int = None,
    requires_admin: bool = False
) -> rx.Component:
    """
    Single navigation item with optional badge

    Args:
        label: Display label
        icon: Emoji or icon
        route: Navigation route
        badge: Optional badge count
        requires_admin: If True, only show for ADMIN role
    """
    item = rx.link(
        rx.hstack(
            rx.text(icon, font_size="1.5rem"),
            rx.text(label, font_size="1rem", font_weight="medium"),
            rx.spacer(),
            rx.badge(str(badge), color_scheme="red") if badge and badge > 0 else rx.fragment(),
            width="100%",
            padding="0.75rem 1rem",
            border_radius="0.5rem",
            _hover={"background": "#EDF2F7"},
            cursor="pointer"
        ),
        href=route,
        width="100%"
    )

    if requires_admin:
        return rx.cond(
            AuthState.current_user_role == "ADMIN",
            item
        )
    else:
        return item


def sidebar() -> rx.Component:
    """
    Main navigation sidebar with role-based menu items
    """

    return rx.box(
        rx.vstack(
            # Logo and User Info
            rx.vstack(
                rx.text("📊 PEARL Tracker", font_size="1.5rem", font_weight="bold", color="blue.600"),
                rx.divider(),
                rx.hstack(
                    rx.avatar(name=AuthState.current_user_name, size="md"),
                    rx.vstack(
                        rx.text(AuthState.current_user_name, font_weight="bold", font_size="0.875rem"),
                        rx.badge(AuthState.current_user_role, color_scheme="blue"),
                        spacing="0.25rem",
                        align_items="flex-start"
                    ),
                    spacing="0.75rem",
                    width="100%",
                    padding="1rem"
                ),
                rx.divider(),
                width="100%",
                spacing="1rem"
            ),

            # Navigation Items
            nav_item("Dashboard", "🏠", "/dashboard"),
            nav_item("Studies", "📚", "/studies"),
            nav_item("Tracker", "📊", "/tracker", badge=AuthState.my_workload_count),
            nav_item("Packages", "📦", "/packages"),
            nav_item("Text Library", "📝", "/text-elements"),

            # Admin-only items
            nav_item("Users", "👥", "/users", requires_admin=True),
            nav_item("Audit Log", "📜", "/audit", requires_admin=True),

            rx.spacer(),

            # Logout Button
            rx.button(
                "Logout",
                on_click=AuthState.logout,
                variant="outline",
                width="100%",
                color_scheme="red"
            ),

            width="100%",
            spacing="0.5rem",
            height="100vh",
            padding="1rem"
        ),
        width="280px",
        background="#FFFFFF",
        border_right="1px solid #E2E8F0",
        position="fixed",
        left="0",
        top="0",
        height="100vh",
        overflow_y="auto"
    )
```

---

#### 5. Protected Route Wrapper

**File:** `pearl_app/components/protected_route.py`

```python
import reflex as rx
from pearl_app.state.auth_state import AuthState

def protected_route(
    component: rx.Component,
    required_role: str = None
) -> rx.Component:
    """
    Wrapper for pages that require authentication
    Redirects to login if not authenticated
    Shows "Access Denied" if insufficient permissions

    Args:
        component: The page component to protect
        required_role: Optional required role (ADMIN, EDITOR, VIEWER)
    """

    if required_role:
        # Check role-specific access
        return rx.cond(
            AuthState.is_authenticated,
            rx.cond(
                AuthState.has_role(required_role),
                component,
                # Access Denied page
                rx.center(
                    rx.vstack(
                        rx.text("🚫", font_size="4rem"),
                        rx.heading("Access Denied", size="xl"),
                        rx.text(
                            f"This page requires {required_role} role.",
                            color="gray.600"
                        ),
                        rx.button(
                            "Go to Dashboard",
                            on_click=lambda: rx.redirect("/dashboard"),
                            color_scheme="blue",
                            margin_top="1rem"
                        ),
                        spacing="1rem"
                    ),
                    height="100vh"
                )
            ),
            rx.redirect("/login")
        )
    else:
        # Just check authentication
        return rx.cond(
            AuthState.is_authenticated,
            component,
            rx.redirect("/login")
        )
```

**Usage:**
```python
# In pearl_app.py
from pearl_app.components.protected_route import protected_route
from pearl_app.pages import dashboard, users, audit

app.add_page(
    protected_route(dashboard.dashboard_page()),
    route="/dashboard"
)

app.add_page(
    protected_route(users.users_page(), required_role="ADMIN"),
    route="/users"
)

app.add_page(
    protected_route(audit.audit_page(), required_role="ADMIN"),
    route="/audit"
)
```

---

#### 6. Authentication State

**File:** `pearl_app/state/auth_state.py`

```python
import reflex as rx
from typing import Optional, Dict
from datetime import datetime
from pearl_app.api_client.client import api_client

class AuthState(rx.State):
    """Authentication and authorization state"""

    # User info
    current_user_id: Optional[int] = None
    current_user_name: str = ""
    current_user_email: str = ""
    current_user_role: str = "VIEWER"
    current_user_department: Optional[str] = None

    # Permissions
    permissions: Dict = {
        "can_create": False,
        "can_edit": False,
        "can_delete": False,
        "can_manage_users": False,
        "can_view_audit": False,
        "can_bulk_assign": False
    }

    # Authentication state
    is_authenticated: bool = False
    token: Optional[str] = None
    token_expires_at: Optional[datetime] = None

    # UI state
    login_error: str = ""
    logging_in: bool = False

    # Workload badge
    my_workload_count: int = 0

    async def login(self, username: str, password: str):
        """
        Authenticate user and store token
        """
        self.logging_in = True
        self.login_error = ""

        try:
            response = await api_client.post("/auth/login", {
                "username": username,
                "password": password
            })

            # Store token
            self.token = response["access_token"]
            api_client.set_token(self.token)

            # Store user info
            user = response["user"]
            self.current_user_id = user["id"]
            self.current_user_name = user["full_name"]
            self.current_user_email = user.get("email", "")
            self.current_user_role = user["role"]
            self.current_user_department = user.get("department")
            self.permissions = user["permissions"]

            # Calculate token expiry
            self.token_expires_at = datetime.now() + timedelta(seconds=response["expires_in"])

            self.is_authenticated = True

            # Fetch my workload count for badge
            await self.fetch_my_workload_count()

            # Redirect to dashboard
            return rx.redirect("/dashboard")

        except Exception as e:
            self.login_error = str(e)
        finally:
            self.logging_in = False

    async def logout(self):
        """Clear authentication state and redirect to login"""
        self.is_authenticated = False
        self.token = None
        self.current_user_id = None
        self.current_user_name = ""
        self.current_user_role = "VIEWER"
        api_client.set_token(None)

        return rx.redirect("/login")

    async def fetch_my_workload_count(self):
        """Fetch current user's workload count for badge"""
        try:
            workload = await api_client.get("/trackers/my-workload")
            summary = workload["summary"]
            self.my_workload_count = summary["production_total"] + summary["qc_total"] - summary["production_completed"] - summary["qc_completed"]
        except Exception:
            self.my_workload_count = 0

    def has_role(self, required_role: str) -> bool:
        """Check if user has required role or higher"""
        role_hierarchy = {
            "ADMIN": 3,
            "EDITOR": 2,
            "VIEWER": 1
        }

        user_level = role_hierarchy.get(self.current_user_role, 0)
        required_level = role_hierarchy.get(required_role, 99)

        return user_level >= required_level

    def can_perform(self, action: str) -> bool:
        """Check if user can perform a specific action"""
        return self.permissions.get(action, False)
```

---

## Deployment Instructions

### Development Setup

#### Backend

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# Alternative: Use uv (faster)
pip install uv
uv pip install -r requirements.txt

# 4. Install DuckDB and related packages
pip install duckdb duckdb-engine sqlalchemy

# 5. Initialize database
python -m app.db.init_db

# 6. Run development server (synchronous - simpler!)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Key Dependencies (requirements.txt):**
```
fastapi==0.111.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.30
duckdb==0.9.2
duckdb-engine==0.10.0
pydantic==2.7.0
pydantic-settings==2.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
alembic==1.13.1
pytest==8.2.0
httpx==0.27.0
```

#### Frontend

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install Reflex
pip install reflex

# 3. Install chart dependencies
pip install plotly reflex-plotly

# 4. Install dependencies
pip install -r requirements.txt

# 5. Initialize Reflex project (first time only)
reflex init

# 6. Run development server
reflex run
```

**Key Dependencies (requirements.txt):**
```
reflex==0.4.0
httpx==0.27.0
plotly==5.20.0
reflex-plotly==0.1.0
```

### Access Applications
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Frontend UI:** http://localhost:3000

### Default Login Credentials (After init_db)
- **Username:** admin
- **Password:** admin123 (change immediately!)

---

## Testing Strategy

### Backend Testing

**Individual Test Scripts** (DuckDB-compatible):

```bash
# Test authentication and authorization
pytest tests/test_auth.py -v

# Test role-based access control
pytest tests/test_rbac.py -v

# Test dashboard metrics
pytest tests/test_dashboard.py -v

# Test studies CRUD
pytest tests/test_studies.py -v

# Test tracker workflow
pytest tests/test_trackers.py -v

# Test deletion protection
pytest tests/test_deletion_protection.py -v
```

**Example Test with RBAC:**

```python
# tests/test_rbac.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_admin_can_delete_study():
    """ADMIN role can delete studies"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Login as admin
        login_resp = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_resp.json()["access_token"]

        # Create study
        study_resp = await client.post(
            "/api/v1/studies",
            json={"study_label": "TEST-STUDY"},
            headers={"Authorization": f"Bearer {token}"}
        )
        study_id = study_resp.json()["id"]

        # Delete study (should succeed)
        delete_resp = await client.delete(
            f"/api/v1/studies/{study_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert delete_resp.status_code == 204


@pytest.mark.asyncio
async def test_editor_cannot_delete_study():
    """EDITOR role cannot delete studies"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Login as editor
        login_resp = await client.post("/api/v1/auth/login", json={
            "username": "editor_user",
            "password": "password123"
        })
        token = login_resp.json()["access_token"]

        # Try to delete study (should fail with 403)
        delete_resp = await client.delete(
            "/api/v1/studies/1",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert delete_resp.status_code == 403
        assert "Insufficient permissions" in delete_resp.json()["detail"]
```

---

## Summary of Key Improvements

### 1. **DuckDB Benefits**
- ✅ Better concurrency (multiple writers)
- ✅ No async complexity (synchronous code)
- ✅ No retry logic needed
- ✅ PostgreSQL-compatible SQL
- ✅ Faster analytics queries

### 2. **Frontend Enhancements**
- ✅ Interactive dashboard with KPIs and charts
- ✅ Kanban board for tracker workflow
- ✅ Role-based access control (RBAC)
- ✅ Programmer workload visualization
- ✅ Protected routes with permission checks
- ✅ Real-time activity feed
- ✅ My Workload summary

### 3. **Security & Access Control**
- ✅ JWT token authentication
- ✅ Role-based permissions (ADMIN, EDITOR, VIEWER)
- ✅ Protected API endpoints
- ✅ Frontend route protection
- ✅ Audit logging for compliance

### 4. **Simplified Architecture**
- ✅ Synchronous backend (easier to understand)
- ✅ No retry logic (DuckDB handles it)
- ✅ Clean separation of concerns
- ✅ Comprehensive testing strategy

---

## Conclusion

This updated specification provides everything needed to build a **production-ready Python-only research tracker system** with DuckDB and comprehensive frontend features:

✅ **Complete database schema** (21 tables with DuckDB)
✅ **Full API specification** (with RBAC)
✅ **Backend implementation** (simplified with synchronous code)
✅ **Frontend architecture** (dashboard, charts, Kanban, role-based UI)
✅ **Testing strategy** (RBAC tests, CRUD tests)
✅ **Deployment instructions** (development setup)

**Estimated Development Timeline:**
- Backend foundation (DuckDB + RBAC): 2 weeks
- API endpoints: 3 weeks
- Frontend dashboard & charts: 2 weeks
- Tracker Kanban board: 1 week
- Role-based UI & auth: 1 week
- Testing and refinement: 2 weeks
- **Total: 11-12 weeks**

**Next Steps:**
1. Set up development environment (Python 3.11+, DuckDB, Reflex)
2. Initialize backend with DuckDB
3. Implement authentication and RBAC
4. Build dashboard with charts
5. Create Kanban board for tracker workflow
6. Implement protected routes
7. Test end-to-end with role-based scenarios

Good luck with implementation! 🚀
