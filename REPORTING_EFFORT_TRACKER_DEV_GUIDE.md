# Reporting Effort Tracker - Developer Guide

## Architecture Overview

The system follows a three-tier architecture with separation between:
1. **Item Definition**: What needs to be done (reporting_effort_items)
2. **Workflow Tracking**: Who's doing it and status (tracker)
3. **Communication**: Comments and feedback (comments)

## Database Design

### Why Separate Tracker Table?
- Clean separation of concerns
- Easy extensibility for new tracking fields
- Better query performance
- No nullable columns in items table

### Core Tables Structure

```sql
-- Main item table
CREATE TABLE reporting_effort_items (
    id SERIAL PRIMARY KEY,
    reporting_effort_id INTEGER NOT NULL REFERENCES reporting_efforts(id),
    source_type VARCHAR(50),
    source_id INTEGER,
    source_item_id INTEGER,
    item_type VARCHAR(50) NOT NULL,
    item_subtype VARCHAR(50) NOT NULL,
    item_code VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(reporting_effort_id, item_type, item_subtype, item_code)
);

-- Tracker table (auto-created for each item)
CREATE TABLE reporting_effort_item_tracker (
    id SERIAL PRIMARY KEY,
    reporting_effort_item_id INTEGER NOT NULL UNIQUE REFERENCES reporting_effort_items(id),
    production_programmer_id INTEGER REFERENCES users(id),
    production_status VARCHAR(50) DEFAULT 'not_started',
    due_date DATE,
    priority VARCHAR(50) DEFAULT 'medium',
    qc_level VARCHAR(50),
    qc_programmer_id INTEGER REFERENCES users(id),
    qc_status VARCHAR(50) DEFAULT 'not_started',
    qc_completion_date DATE,
    in_production_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comments table with role-based types
CREATE TABLE reporting_effort_tracker_comments (
    id SERIAL PRIMARY KEY,
    tracker_id INTEGER NOT NULL REFERENCES reporting_effort_item_tracker(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    parent_comment_id INTEGER REFERENCES reporting_effort_tracker_comments(id),
    comment_text TEXT NOT NULL,
    comment_type VARCHAR(50),  -- programmer_comment or biostat_comment
    comment_category VARCHAR(50) DEFAULT 'general',
    is_pinned BOOLEAN DEFAULT FALSE,
    is_edited BOOLEAN DEFAULT FALSE,
    edited_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Audit Trail Implementation

Simple audit log table that captures all changes:

```sql
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    changes_json TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_table_record (table_name, record_id),
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_created (created_at)
);
```

Implementation approach:
- Use SQLAlchemy event listeners for automatic logging
- Decorator pattern for API endpoints
- Store before/after values in JSON
- Queryable by table, user, or time range

### Database Backup Strategy

For PostgreSQL on production:

1. **Automated Backups**: 
   - Use pg_dump via subprocess
   - Schedule with APScheduler
   - Store locally and/or upload to S3

2. **Admin UI Backup**:
   - Trigger manual backup via API
   - Download backup file
   - View backup history

## Key Implementation Patterns

### Auto-create Tracker Entry
When an item is created, automatically create its tracker:
- Set default statuses to 'not_started'
- Leave programmers unassigned
- Set default priority to 'medium'

### Role-Based Comment Types
- VIEWER role → can only create biostat_comment
- EDITOR/ADMIN → can create programmer_comment
- Auto-determine based on user.department

### Dynamic Excel Export
Generate Excel from current tracker state:
- Columns 1-4: Read-only item info (grey background)
- Columns 5+: Editable tracker fields
- Sheet 2: Valid values for dropdowns

### Bulk Upload Validation
1. Pre-validate all rows before any creation
2. Check for duplicates
3. Validate enum values
4. Return detailed error report
5. Only create if all rows valid

### Deletion Protection
- Cannot delete item if production_programmer_id is set
- Cannot delete item if qc_programmer_id is set
- Return informative error message with programmer names

### WebSocket Broadcasting
Every CRUD operation must broadcast:
- Use consistent message types
- Convert SQLAlchemy models to dict
- Include operation type in message
- Handle connection cleanup

### Session Management for Posit Connect

Production environment variables:
- `RSTUDIO_CONNECT_USER`: Username
- `RSTUDIO_CONNECT_EMAIL`: Email
- `RSTUDIO_CONNECT_GROUPS`: Groups

Development switching via environment variable:
- `DEV_USER=admin` for admin testing
- `DEV_USER=editor` for programmer testing  
- `DEV_USER=viewer` for biostat testing

## Testing Strategy

### Automated Testing
- Bash scripts for API testing (similar to test_packages_crud.sh)
- Python unit tests for CRUD operations
- WebSocket broadcast testing

### Manual Testing Scenarios
1. Role switching - test all three roles
2. Bulk upload - test with large Excel files
3. Comment threading - test interaction flow
4. Dashboard accuracy - verify calculations
5. Deletion protection - verify cannot delete assigned items

### Test Data Generation
Create scripts to generate:
- 100+ items for bulk testing
- Multiple users with different roles
- Comments with threading
- Various tracker statuses

## Performance Considerations

### Database Indexes
- Foreign key columns
- Frequently queried fields (status, programmer_id)
- Comment filtering (tracker_id, comment_type)
- Audit log queries (table_name, user_id, created_at)

### Query Optimization
- Use selectinload for relationships
- Paginate large result sets
- Cache dashboard calculations
- Async operations throughout

## Security Considerations

### Role Enforcement
- Check at API level (FastAPI dependencies)
- Check at UI level (conditional rendering)
- Validate in CRUD operations
- Log authorization failures

### Data Protection
- Deletion protection for assigned items
- Audit trail for compliance
- Backup encryption
- Session timeout handling

## Common Pitfalls to Avoid

1. **Don't forget tracker auto-creation** when adding items
2. **Validate user roles** at multiple levels
3. **Test with real data volumes** not just few records
4. **Handle WebSocket disconnections** gracefully
5. **Include audit logging** from the start
6. **Plan for backup/restore** early
7. **Check deletion protection** before removing items

## Reference Implementation

Look at these existing files for patterns:
- `backend/app/api/v1/packages.py` - Bulk upload pattern
- `backend/app/crud/package_item.py` - Complex CRUD with details
- `admin-frontend/modules/package_items_server.R` - UI patterns
- `backend/app/api/v1/websocket.py` - WebSocket implementation

## Quick Commands

```bash
# Create feature branch
git checkout -b feature/reporting-effort-tracker

# Run backend tests
cd backend && ./test_reporting_effort_tracker_crud.sh

# Test as different users
DEV_USER=admin Rscript run_app.R
DEV_USER=editor Rscript run_app.R
DEV_USER=viewer Rscript run_app.R

# Create database backup
pg_dump -U postgres pearl > backup_$(date +%Y%m%d).sql

# Restore database
psql -U postgres pearl < backup_20240101.sql
```