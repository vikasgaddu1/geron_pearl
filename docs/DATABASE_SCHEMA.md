# Database Schema Documentation

**PEARL Full-Stack Research Data Management System**  
**Database Schema with Relationships and Constraints**

This document describes the current database schema with all relationships, constraints, and entity definitions for the PEARL system post-Phase 2 implementation.

## Table of Contents

- [Schema Overview](#schema-overview)
- [Entity Relationship Diagram](#entity-relationship-diagram)
- [Core Entities](#core-entities)
- [Package System Entities](#package-system-entities)
- [Tracking System Entities](#tracking-system-entities)
- [Comment System Entities](#comment-system-entities)
- [Support Entities](#support-entities)
- [Polymorphic Relationships](#polymorphic-relationships)
- [Indexes and Constraints](#indexes-and-constraints)
- [Migration History](#migration-history)
- [CASCADE DELETE Analysis](#cascade-delete-analysis)

---

## Schema Overview

The PEARL database schema is designed around a hierarchical structure for clinical research data management:

**Primary Hierarchy**:
```
Study (1) ←→ (N) DatabaseRelease (1) ←→ (N) ReportingEffort (1) ←→ (N) ReportingEffortItem
                                                ↓
                                        ReportingEffortItemTracker
                                                ↓
                                          TrackerComment (threaded)
```

**Package System**:
```
Package (1) ←→ (N) PackageItem (polymorphic: TLF/Dataset)
   ↑                     ↓
   └─── Text Elements ───┘ (footnotes, acronyms via junction tables)
```

**Database**: PostgreSQL with async SQLAlchemy 2.0  
**Migration System**: Alembic  
**Key Features**: Soft deletes, audit timestamps, referential integrity, polymorphic associations

---

## Entity Relationship Diagram

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│    Study    │ 1:N  │ DatabaseRelease  │ 1:N  │ ReportingEffort │
│             │◄────►│                  │◄────►│                 │
│ id (PK)     │      │ id (PK)          │      │ id (PK)         │
│ study_label │      │ study_id (FK)    │      │ db_release_id   │
│ created_at  │      │ release_label    │      │ release_label   │
│ updated_at  │      │ release_date     │      │ created_at      │
└─────────────┘      │ created_at       │      │ updated_at      │
                     │ updated_at       │      └─────────────────┘
                     └──────────────────┘               │ 1:N
                                                         ▼
                     ┌──────────────────┐      ┌─────────────────┐
                     │    Package       │      │ReportingEffort  │
                     │                  │      │Item             │
                     │ id (PK)          │      │                 │
                     │ package_name     │      │ id (PK)         │
                     │ study_indication │      │ effort_id (FK)  │
                     │ therapeutic_area │      │ item_code       │
                     │ created_at       │      │ item_description│
                     │ updated_at       │      │ item_type       │
                     └──────────────────┘      │ item_status     │
                              │ 1:N            │ created_at      │
                              ▼                │ updated_at      │
                     ┌──────────────────┐      └─────────────────┘
                     │  PackageItem     │               │ 1:1
                     │                  │               ▼
                     │ id (PK)          │      ┌─────────────────┐
                     │ package_id (FK)  │      │ReportingEffort  │
                     │ item_code        │      │ItemTracker      │
                     │ item_description │      │                 │
                     │ item_type        │      │ id (PK)         │
                     │ created_at       │      │ item_id (FK)    │
                     │ updated_at       │      │ primary_prog_id │
                     └──────────────────┘      │ qc_prog_id      │
                              │                │ primary_status  │
                              ▼                │ qc_status       │
                     ┌──────────────────┐      │ created_at      │
                     │  TextElement     │      │ updated_at      │
                     │                  │      └─────────────────┘
                     │ id (PK)          │               │ 1:N
                     │ type             │               ▼
                     │ label            │      ┌─────────────────┐
                     │ content          │      │ TrackerComment  │
                     │ created_at       │      │                 │
                     │ updated_at       │      │ id (PK)         │
                     └──────────────────┘      │ tracker_id (FK) │
                                               │ user_id (FK)    │
         ┌──────────────────┐                │ comment_text    │
         │      User        │                │ comment_type    │
         │                  │                │ is_resolved     │
         │ id (PK)          │                │ parent_id (FK)  │
         │ username         │                │ created_at      │
         │ role             │                │ updated_at      │
         │ department       │                └─────────────────┘
         │ created_at       │
         │ updated_at       │                ┌─────────────────┐
         └──────────────────┘                │   AuditLog      │
                                               │                 │
                                               │ id (PK)         │
                                               │ entity_type     │
                                               │ entity_id       │
                                               │ action          │
                                               │ user_id (FK)    │
                                               │ changes (JSON)  │
                                               │ timestamp       │
                                               └─────────────────┘
```

---

## Core Entities

### Study

**Table**: `studies`  
**Model**: `app.models.study.Study`  
**Purpose**: Top-level entity representing clinical studies.

```sql
CREATE TABLE studies (
    id SERIAL PRIMARY KEY,
    study_label VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Constraints**:
- `UNIQUE(study_label)` - Study labels must be unique
- `NOT NULL` constraints on required fields

**Relationships**:
- `1:N` with `database_releases` (study_id)

**Indexes**:
- Primary key index on `id`
- Unique index on `study_label`

---

### DatabaseRelease

**Table**: `database_releases`  
**Model**: `app.models.database_release.DatabaseRelease`  
**Purpose**: Database releases/locks associated with studies.

```sql
CREATE TABLE database_releases (
    id SERIAL PRIMARY KEY,
    study_id INTEGER NOT NULL REFERENCES studies(id),
    database_release_label VARCHAR NOT NULL,
    database_release_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(study_id, database_release_label)
);
```

**Constraints**:
- Foreign key to `studies(id)`
- `UNIQUE(study_id, database_release_label)` - No duplicate labels per study
- `NOT NULL` constraints on required fields

**Relationships**:
- `N:1` with `studies` (study_id)
- `1:N` with `reporting_efforts` (database_release_id)

---

### ReportingEffort

**Table**: `reporting_efforts`  
**Model**: `app.models.reporting_effort.ReportingEffort`  
**Purpose**: Reporting efforts within database releases.

```sql
CREATE TABLE reporting_efforts (
    id SERIAL PRIMARY KEY,
    database_release_id INTEGER NOT NULL REFERENCES database_releases(id),
    database_release_label VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Constraints**:
- Foreign key to `database_releases(id)`
- `NOT NULL` constraints on required fields

**Relationships**:
- `N:1` with `database_releases` (database_release_id)
- `1:N` with `reporting_effort_items` (reporting_effort_id)

---

### ReportingEffortItem

**Table**: `reporting_effort_items`  
**Model**: `app.models.reporting_effort_item.ReportingEffortItem`  
**Purpose**: Individual items (TLFs, datasets) within reporting efforts.

```sql
CREATE TABLE reporting_effort_items (
    id SERIAL PRIMARY KEY,
    reporting_effort_id INTEGER NOT NULL REFERENCES reporting_efforts(id),
    item_code VARCHAR NOT NULL UNIQUE,
    item_description TEXT,
    item_type VARCHAR NOT NULL,
    item_status VARCHAR NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Enums**:
- `item_type`: TLF, DATASET
- `item_status`: PENDING, IN_PROGRESS, COMPLETED

**Constraints**:
- Foreign key to `reporting_efforts(id)`
- `UNIQUE(item_code)` - Item codes must be globally unique
- `NOT NULL` constraints on required fields

**Relationships**:
- `N:1` with `reporting_efforts` (reporting_effort_id)
- `1:1` with `reporting_effort_item_trackers` (reporting_effort_item_id)

---

## Package System Entities

### Package

**Table**: `packages`  
**Model**: `app.models.package.Package`  
**Purpose**: Template packages for TLFs and datasets.

```sql
CREATE TABLE packages (
    id SERIAL PRIMARY KEY,
    package_name VARCHAR NOT NULL UNIQUE,
    study_indication VARCHAR,
    therapeutic_area VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Constraints**:
- `UNIQUE(package_name)` - Package names must be unique
- `NOT NULL` constraints on required fields

**Relationships**:
- `1:N` with `package_items` (package_id)

---

### PackageItem

**Table**: `package_items`  
**Model**: `app.models.package_item.PackageItem`  
**Purpose**: Individual items within packages.

```sql
CREATE TABLE package_items (
    id SERIAL PRIMARY KEY,
    package_id INTEGER NOT NULL REFERENCES packages(id),
    item_code VARCHAR NOT NULL,
    item_description TEXT,
    item_type VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(package_id, item_code)
);
```

**Enums**:
- `item_type`: TLF, DATASET

**Constraints**:
- Foreign key to `packages(id)`
- `UNIQUE(package_id, item_code)` - No duplicate codes per package
- `NOT NULL` constraints on required fields

**Relationships**:
- `N:1` with `packages` (package_id)

---

## Tracking System Entities

### ReportingEffortItemTracker

**Table**: `reporting_effort_item_trackers`  
**Model**: `app.models.reporting_effort_item_tracker.ReportingEffortItemTracker`  
**Purpose**: Progress tracking for reporting effort items with programmer assignments.

```sql
CREATE TABLE reporting_effort_item_trackers (
    id SERIAL PRIMARY KEY,
    reporting_effort_item_id INTEGER NOT NULL REFERENCES reporting_effort_items(id),
    primary_programmer_id INTEGER REFERENCES users(id),
    qc_programmer_id INTEGER REFERENCES users(id),
    primary_status VARCHAR NOT NULL DEFAULT 'NOT_STARTED',
    qc_status VARCHAR NOT NULL DEFAULT 'NOT_STARTED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Enums**:
- `primary_status`: NOT_STARTED, IN_PROGRESS, COMPLETED
- `qc_status`: NOT_STARTED, IN_PROGRESS, COMPLETED

**Constraints**:
- Foreign key to `reporting_effort_items(id)`
- Foreign keys to `users(id)` for programmers (nullable)
- `NOT NULL` constraints on status fields

**Relationships**:
- `1:1` with `reporting_effort_items` (reporting_effort_item_id)
- `N:1` with `users` (primary_programmer_id, qc_programmer_id)
- `1:N` with `tracker_comments` (tracker_id)

---

## Comment System Entities

### TrackerComment

**Table**: `tracker_comments`  
**Model**: `app.models.tracker_comment.TrackerComment`  
**Purpose**: Threaded comment system for trackers.

```sql
CREATE TABLE tracker_comments (
    id SERIAL PRIMARY KEY,
    tracker_id INTEGER NOT NULL REFERENCES reporting_effort_item_trackers(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    comment_text TEXT NOT NULL,
    comment_type VARCHAR NOT NULL DEFAULT 'GENERAL',
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    parent_comment_id INTEGER REFERENCES tracker_comments(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Enums**:
- `comment_type`: GENERAL, QUESTION, ISSUE, RESPONSE

**Constraints**:
- Foreign key to `reporting_effort_item_trackers(id)`
- Foreign key to `users(id)`
- Self-referencing foreign key for threading (parent_comment_id)
- `NOT NULL` constraints on required fields

**Relationships**:
- `N:1` with `reporting_effort_item_trackers` (tracker_id)
- `N:1` with `users` (user_id)
- Self-referencing `1:N` for threading (parent_comment_id)

**Threading Structure**:
```sql
-- Parent comment (parent_comment_id = NULL)
INSERT INTO tracker_comments (tracker_id, user_id, comment_text, parent_comment_id)
VALUES (1, 1, 'This is a parent comment', NULL);

-- Reply to parent (parent_comment_id = parent.id)
INSERT INTO tracker_comments (tracker_id, user_id, comment_text, parent_comment_id)  
VALUES (1, 2, 'This is a reply', 1);
```

---

## Support Entities

### User

**Table**: `users`  
**Model**: `app.models.user.User`  
**Purpose**: System users with role-based access.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL UNIQUE,
    role VARCHAR NOT NULL,
    department VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Enums**:
- `role`: ADMIN, ANALYST, VIEWER

**Constraints**:
- `UNIQUE(username)` - Usernames must be unique
- `NOT NULL` constraints on required fields

**Relationships**:
- `1:N` with `reporting_effort_item_trackers` (primary_programmer_id, qc_programmer_id)
- `1:N` with `tracker_comments` (user_id)
- `1:N` with `audit_logs` (user_id)

---

### TextElement

**Table**: `text_elements`  
**Model**: `app.models.text_element.TextElement`  
**Purpose**: Reusable text elements (titles, footnotes, populations, acronyms).

```sql
CREATE TABLE text_elements (
    id SERIAL PRIMARY KEY,
    type VARCHAR NOT NULL,
    label VARCHAR NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(type, label)
);
```

**Enums**:
- `type`: TITLE, FOOTNOTE, POPULATION_SET, ACRONYMS_SET

**Constraints**:
- `UNIQUE(type, label)` - No duplicate labels per type
- `NOT NULL` constraints on required fields

**Relationships**:
- Used via junction tables with packages and items (future enhancement)

---

### AuditLog

**Table**: `audit_logs`  
**Model**: `app.models.audit_log.AuditLog`  
**Purpose**: System audit trail for all operations.

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR NOT NULL,
    entity_id INTEGER NOT NULL,
    action VARCHAR NOT NULL,
    user_id INTEGER REFERENCES users(id),
    changes JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Enums**:
- `action`: CREATE, UPDATE, DELETE

**Constraints**:
- Foreign key to `users(id)` (nullable for system actions)
- `NOT NULL` constraints on required fields

**Relationships**:
- `N:1` with `users` (user_id)

**JSONB Changes Structure**:
```json
{
  "before": {"field1": "old_value", "field2": "old_value"},
  "after": {"field1": "new_value", "field2": "new_value"},
  "changed_fields": ["field1", "field2"]
}
```

---

## Polymorphic Relationships

### Package Item Details

The system supports polymorphic associations for different item types:

#### PackageTLFDetails

**Table**: `package_tlf_details`  
**Model**: `app.models.package_tlf_details.PackageTLFDetails`  
**Purpose**: TLF-specific attributes.

```sql
CREATE TABLE package_tlf_details (
    id SERIAL PRIMARY KEY,
    package_item_id INTEGER NOT NULL REFERENCES package_items(id),
    tlf_type VARCHAR,
    primary_endpoint BOOLEAN DEFAULT FALSE,
    analysis_population VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### PackageDatasetDetails

**Table**: `package_dataset_details`  
**Model**: `app.models.package_dataset_details.PackageDatasetDetails`  
**Purpose**: Dataset-specific attributes.

```sql
CREATE TABLE package_dataset_details (
    id SERIAL PRIMARY KEY,
    package_item_id INTEGER NOT NULL REFERENCES package_items(id),
    dataset_type VARCHAR,
    data_source VARCHAR,
    record_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Reporting Effort Item Details

Similar polymorphic structure for reporting effort items:

#### ReportingEffortTLFDetails

**Table**: `reporting_effort_tlf_details`  
**Model**: `app.models.reporting_effort_tlf_details.ReportingEffortTLFDetails`

#### ReportingEffortDatasetDetails

**Table**: `reporting_effort_dataset_details`  
**Model**: `app.models.reporting_effort_dataset_details.ReportingEffortDatasetDetails`

---

## Indexes and Constraints

### Primary Indexes

All tables have primary key indexes:
```sql
-- Automatically created for PRIMARY KEY constraints
CREATE INDEX idx_studies_pkey ON studies(id);
CREATE INDEX idx_users_pkey ON users(id);
-- ... etc for all tables
```

### Unique Indexes

```sql
-- Unique constraints create implicit indexes
CREATE UNIQUE INDEX idx_studies_label ON studies(study_label);
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE UNIQUE INDEX idx_packages_name ON packages(package_name);
CREATE UNIQUE INDEX idx_db_releases_study_label ON database_releases(study_id, database_release_label);
CREATE UNIQUE INDEX idx_package_items_code ON package_items(package_id, item_code);
CREATE UNIQUE INDEX idx_text_elements_type_label ON text_elements(type, label);
```

### Foreign Key Indexes

```sql
-- Improve JOIN performance
CREATE INDEX idx_database_releases_study_id ON database_releases(study_id);
CREATE INDEX idx_reporting_efforts_db_release_id ON reporting_efforts(database_release_id);
CREATE INDEX idx_reporting_effort_items_effort_id ON reporting_effort_items(reporting_effort_id);
CREATE INDEX idx_trackers_item_id ON reporting_effort_item_trackers(reporting_effort_item_id);
CREATE INDEX idx_comments_tracker_id ON tracker_comments(tracker_id);
CREATE INDEX idx_comments_user_id ON tracker_comments(user_id);
CREATE INDEX idx_comments_parent_id ON tracker_comments(parent_comment_id);
```

### Query Optimization Indexes

```sql
-- Audit log queries
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);

-- Comment system queries
CREATE INDEX idx_comments_resolved ON tracker_comments(is_resolved, tracker_id);
CREATE INDEX idx_comments_type ON tracker_comments(comment_type);

-- Tracker queries  
CREATE INDEX idx_trackers_primary_programmer ON reporting_effort_item_trackers(primary_programmer_id);
CREATE INDEX idx_trackers_qc_programmer ON reporting_effort_item_trackers(qc_programmer_id);
CREATE INDEX idx_trackers_status ON reporting_effort_item_trackers(primary_status, qc_status);
```

---

## Migration History

### Key Migrations (Chronological Order)

#### Initial Schema Creation
- `72383a245505_add_users_table_with_username_and_role_.py`
- `9210364e4641_add_reporting_efforts_table.py`
- `a0b65bfec576_add_database_releases_table.py`

#### Package System
- `d3f89a2c4b56_add_packages_system_tables.py`
- `473053e83a5b_create_new_tnfp_and_acronym_tables_with_.py`

#### Tracker System
- `0b87c8f59a0e_add_reporting_effort_tracker_tables.py`
- `ccff86bd596b_create_new_tracker_comment_system.py`

#### Comment System Evolution
- `686b7f37d8ad_remove_comment_system_for_redesign.py`
- `07fb820f6a75_create_simplified_comment_system.py`
- `f29030561d08_merge_comment_system_branches.py`

#### Schema Refinements
- `c22f57d3ab22_add_timestamps_to_existing_tables_and_.py`
- `ce4a91039756_remove_study_id_from_package_items_and_.py`
- `add_unique_study_label_constraint.py`

#### Cleanup Operations
- `7a7096093ce9_drop_acronym_related_tables_and_fix_.py`
- `b086f9116d6d_remove_population_set_from_.py`
- `f5a535fcf5e5_remove_is_deleted_column_from_tracker_.py`

### Migration Patterns

#### Adding New Table
```python
def upgrade():
    op.create_table(
        'new_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

def downgrade():
    op.drop_table('new_table')
```

#### Adding Foreign Key Relationship
```python
def upgrade():
    op.add_column('child_table', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_child_parent', 'child_table', 'parent_table', ['parent_id'], ['id'])

def downgrade():
    op.drop_constraint('fk_child_parent', 'child_table', type_='foreignkey')
    op.drop_column('child_table', 'parent_id')
```

---

## CASCADE DELETE Analysis

### Current State

The database currently has **31 foreign key constraints** that lack proper CASCADE DELETE behavior. This can lead to orphaned records when parent entities are deleted.

### Available Migration

A comprehensive CASCADE DELETE migration is ready for implementation:

**Migration Script**: `backend/execute_cascade_migration.py`  
**Analysis Script**: `backend/analyze_orphaned_records.py`  
**Documentation**: `backend/CASCADE_DELETE_MIGRATION_PLAN.md`

### Current Orphaned Records Analysis

Based on recent analysis (August 2024):
- **No orphaned records currently exist** in the database
- All foreign key relationships are currently intact
- Migration is safe to execute

### Constraints to be Updated

#### High Priority CASCADE DELETE Constraints:
```sql
-- Study deletion should cascade to database releases
ALTER TABLE database_releases 
DROP CONSTRAINT IF EXISTS database_releases_study_id_fkey,
ADD CONSTRAINT database_releases_study_id_fkey 
FOREIGN KEY (study_id) REFERENCES studies(id) ON DELETE CASCADE;

-- Database release deletion should cascade to reporting efforts  
ALTER TABLE reporting_efforts
DROP CONSTRAINT IF EXISTS reporting_efforts_database_release_id_fkey,
ADD CONSTRAINT reporting_efforts_database_release_id_fkey
FOREIGN KEY (database_release_id) REFERENCES database_releases(id) ON DELETE CASCADE;

-- Reporting effort deletion should cascade to items
ALTER TABLE reporting_effort_items
DROP CONSTRAINT IF EXISTS reporting_effort_items_reporting_effort_id_fkey,
ADD CONSTRAINT reporting_effort_items_reporting_effort_id_fkey
FOREIGN KEY (reporting_effort_id) REFERENCES reporting_efforts(id) ON DELETE CASCADE;

-- Item deletion should cascade to trackers
ALTER TABLE reporting_effort_item_trackers
DROP CONSTRAINT IF EXISTS reporting_effort_item_trackers_reporting_effort_item_id_fkey,
ADD CONSTRAINT reporting_effort_item_trackers_reporting_effort_item_id_fkey
FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id) ON DELETE CASCADE;

-- Tracker deletion should cascade to comments
ALTER TABLE tracker_comments
DROP CONSTRAINT IF EXISTS tracker_comments_tracker_id_fkey,
ADD CONSTRAINT tracker_comments_tracker_id_fkey
FOREIGN KEY (tracker_id) REFERENCES reporting_effort_item_trackers(id) ON DELETE CASCADE;
```

#### Package System CASCADE:
```sql
-- Package deletion should cascade to items
ALTER TABLE package_items
DROP CONSTRAINT IF EXISTS package_items_package_id_fkey,
ADD CONSTRAINT package_items_package_id_fkey
FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE;
```

### Migration Safety Features

1. **Pre-migration Backup**: Automatic database backup creation
2. **Validation**: Checks for existing orphaned records
3. **Rollback Script**: Automated rollback to original constraints
4. **Testing**: Post-migration integrity verification

---

## Database Performance Considerations

### Query Optimization

#### Common Query Patterns:
```sql
-- Hierarchical data loading (Study Tree)
SELECT s.*, dr.*, re.* 
FROM studies s
LEFT JOIN database_releases dr ON s.id = dr.study_id
LEFT JOIN reporting_efforts re ON dr.id = re.database_release_id
ORDER BY s.study_label, dr.database_release_date, re.id;

-- Tracker with comments count
SELECT t.*, COUNT(c.id) as comment_count,
       COUNT(CASE WHEN c.is_resolved = FALSE THEN 1 END) as unresolved_count
FROM reporting_effort_item_trackers t
LEFT JOIN tracker_comments c ON t.id = c.tracker_id
GROUP BY t.id;

-- Package items with details (polymorphic)
SELECT pi.*, 
       ptd.tlf_type, ptd.primary_endpoint,
       pdd.dataset_type, pdd.record_count
FROM package_items pi
LEFT JOIN package_tlf_details ptd ON pi.id = ptd.package_item_id
LEFT JOIN package_dataset_details pdd ON pi.id = pdd.package_item_id
WHERE pi.package_id = ?;
```

#### Performance Indexes:
- All foreign keys have corresponding indexes
- Composite indexes on frequently queried combinations
- Partial indexes for filtered queries (e.g., unresolved comments)

### Connection Management

```python
# Async session configuration
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/pearl"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)

AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)
```

---

## Related Documentation

- [API_REFERENCE.md](API_REFERENCE.md) - API endpoints that interact with these database entities
- [CRUD_METHODS.md](CRUD_METHODS.md) - CRUD operations for each entity
- [MIGRATION_GUIDE.md](../backend/CASCADE_DELETE_MIGRATION_PLAN.md) - CASCADE DELETE migration documentation
- [WEBSOCKET_EVENTS.md](WEBSOCKET_EVENTS.md) - Real-time events triggered by database changes