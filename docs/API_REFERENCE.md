# API Reference

**PEARL Full-Stack Research Data Management System**  
**FastAPI Backend API Documentation**

This document catalogs all FastAPI endpoints with their parameters, request/response formats, and examples. This is a comprehensive reference for the PEARL system post-Phase 2 implementation.

## Table of Contents

- [Base Configuration](#base-configuration)
- [Authentication & Users](#authentication--users)
- [Studies Management](#studies-management)
- [Database Releases](#database-releases)
- [Reporting Efforts](#reporting-efforts)
- [Reporting Effort Items](#reporting-effort-items)
- [Reporting Effort Trackers](#reporting-effort-trackers)
- [Packages](#packages)
- [Package Items](#package-items)
- [Text Elements (TNFP)](#text-elements-tnfp)
- [Tracker Comments](#tracker-comments)
- [Audit Trail](#audit-trail)
- [Database Backup](#database-backup)
- [WebSocket](#websocket)
- [Health Check](#health-check)

---

## Base Configuration

**Base URL**: `http://localhost:8000` (development)  
**API Prefix**: `/api/v1`  
**Documentation**: `http://localhost:8000/docs` (Swagger UI)  
**Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)

### Standard Response Format

All endpoints follow consistent response patterns:
- **Success**: HTTP 2xx with entity data or confirmation message
- **Not Found**: HTTP 404 with `{"detail": "Entity not found"}`
- **Validation Error**: HTTP 422 with detailed field errors
- **Conflict**: HTTP 400 with descriptive error message
- **Server Error**: HTTP 500 with error details

### Common Query Parameters

- `skip: int = 0` - Number of records to skip (pagination)
- `limit: int = 100` - Maximum records to return (max 1000)
- `q: str` - Search query term (where applicable)

---

## Authentication & Users

### POST `/api/v1/users/`
Create a new user.

**Request Body** (`UserCreate`):
```json
{
    "username": "johndoe",
    "role": "ANALYST",
    "department": "Clinical Research"
}
```

**Response** (`User`):
```json
{
    "id": 1,
    "username": "johndoe",
    "role": "ANALYST",
    "department": "Clinical Research",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

**Status Codes**:
- `201` - User created successfully
- `400` - Username already exists or validation error
- `422` - Invalid input data

---

### GET `/api/v1/users/`
Retrieve all users with pagination.

**Query Parameters**:
- `skip: int = 0` - Records to skip
- `limit: int = 100` - Max records (1-1000)

**Response** (`List[User]`):
```json
[
    {
        "id": 1,
        "username": "johndoe",
        "role": "ANALYST",
        "department": "Clinical Research",
        "created_at": "2024-12-01T10:00:00Z",
        "updated_at": "2024-12-01T10:00:00Z"
    }
]
```

---

### GET `/api/v1/users/{id}`
Get a specific user by ID.

**Path Parameters**:
- `id: int` - User ID

**Response** (`User`):
```json
{
    "id": 1,
    "username": "johndoe",
    "role": "ANALYST",
    "department": "Clinical Research",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

**Status Codes**:
- `200` - User found
- `404` - User not found

---

### PUT `/api/v1/users/{id}`
Update an existing user.

**Path Parameters**:
- `id: int` - User ID

**Request Body** (`UserUpdate`):
```json
{
    "username": "johnsmith",
    "role": "ADMIN",
    "department": "Data Management"
}
```

**Response** (`User`):
```json
{
    "id": 1,
    "username": "johnsmith",
    "role": "ADMIN",
    "department": "Data Management",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T15:30:00Z"
}
```

**Status Codes**:
- `200` - User updated successfully
- `400` - Username already exists or validation error
- `404` - User not found
- `422` - Invalid input data

---

### DELETE `/api/v1/users/{id}`
Delete a user.

**Path Parameters**:
- `id: int` - User ID

**Response** (`User`):
Returns the deleted user data.

**Status Codes**:
- `200` - User deleted successfully
- `404` - User not found

---

## Studies Management

### POST `/api/v1/studies/`
Create a new study.

**Request Body** (`StudyCreate`):
```json
{
    "study_label": "ONCOLOGY-2024-001"
}
```

**Response** (`Study`):
```json
{
    "id": 1,
    "study_label": "ONCOLOGY-2024-001",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

**WebSocket Event**: Broadcasts `study_created` event.

**Status Codes**:
- `201` - Study created successfully
- `400` - Study label already exists
- `422` - Invalid input data

---

### GET `/api/v1/studies/`
Retrieve all studies with pagination.

**Query Parameters**:
- `skip: int = 0` - Records to skip
- `limit: int = 100` - Max records (1-1000)

**Response** (`List[Study]`):
```json
[
    {
        "id": 1,
        "study_label": "ONCOLOGY-2024-001",
        "created_at": "2024-12-01T10:00:00Z",
        "updated_at": "2024-12-01T10:00:00Z"
    }
]
```

---

### GET `/api/v1/studies/{id}`
Get a specific study by ID.

**Path Parameters**:
- `id: int` - Study ID

**Response** (`Study`):
```json
{
    "id": 1,
    "study_label": "ONCOLOGY-2024-001",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

**Status Codes**:
- `200` - Study found
- `404` - Study not found

---

### PUT `/api/v1/studies/{id}`
Update an existing study.

**Path Parameters**:
- `id: int` - Study ID

**Request Body** (`StudyUpdate`):
```json
{
    "study_label": "ONCOLOGY-2024-001-UPDATED"
}
```

**Response** (`Study`):
```json
{
    "id": 1,
    "study_label": "ONCOLOGY-2024-001-UPDATED",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T15:30:00Z"
}
```

**WebSocket Event**: Broadcasts `study_updated` event.

**Status Codes**:
- `200` - Study updated successfully
- `400` - Study label already exists
- `404` - Study not found
- `422` - Invalid input data

---

### DELETE `/api/v1/studies/{id}`
Delete a study (with dependency checking).

**Path Parameters**:
- `id: int` - Study ID

**Response**:
```json
{
    "message": "Study deleted successfully"
}
```

**WebSocket Event**: Broadcasts `study_deleted` event.

**Status Codes**:
- `200` - Study deleted successfully
- `400` - Cannot delete: dependent database releases exist
- `404` - Study not found

**Deletion Protection**: Checks for dependent database releases before deletion.

---

## Database Releases

### POST `/api/v1/database-releases/`
Create a new database release.

**Request Body** (`DatabaseReleaseCreate`):
```json
{
    "study_id": 1,
    "database_release_label": "DB_LOCK_20241201",
    "database_release_date": "2024-12-01"
}
```

**Response** (`DatabaseRelease`):
```json
{
    "id": 1,
    "study_id": 1,
    "database_release_label": "DB_LOCK_20241201",
    "database_release_date": "2024-12-01",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

**WebSocket Event**: Broadcasts `database_release_created` event.

---

### GET `/api/v1/database-releases/`
Retrieve all database releases with pagination.

**Response** (`List[DatabaseRelease]`):
```json
[
    {
        "id": 1,
        "study_id": 1,
        "database_release_label": "DB_LOCK_20241201",
        "database_release_date": "2024-12-01",
        "created_at": "2024-12-01T10:00:00Z",
        "updated_at": "2024-12-01T10:00:00Z"
    }
]
```

---

### GET `/api/v1/database-releases/by-study/{study_id}`
Get database releases for a specific study.

**Path Parameters**:
- `study_id: int` - Study ID

**Response** (`List[DatabaseRelease]`):
Returns all database releases for the specified study.

---

### PUT `/api/v1/database-releases/{id}`
Update a database release.

**WebSocket Event**: Broadcasts `database_release_updated` event.

---

### DELETE `/api/v1/database-releases/{id}`
Delete a database release (with dependency checking).

**WebSocket Event**: Broadcasts `database_release_deleted` event.

**Deletion Protection**: Checks for dependent reporting efforts before deletion.

---

## Reporting Efforts

### POST `/api/v1/reporting-efforts/`
Create a new reporting effort.

**Request Body** (`ReportingEffortCreate`):
```json
{
    "database_release_id": 1,
    "database_release_label": "INTERIM_ANALYSIS_20241201"
}
```

**Response** (`ReportingEffort`):
```json
{
    "id": 1,
    "database_release_id": 1,
    "database_release_label": "INTERIM_ANALYSIS_20241201",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

**WebSocket Event**: Broadcasts `reporting_effort_created` event.

---

### GET `/api/v1/reporting-efforts/`
Retrieve all reporting efforts.

---

### GET `/api/v1/reporting-efforts/by-database-release/{database_release_id}`
Get reporting efforts for a specific database release.

**Path Parameters**:
- `database_release_id: int` - Database release ID

---

### PUT `/api/v1/reporting-efforts/{id}`
Update a reporting effort.

**WebSocket Event**: Broadcasts `reporting_effort_updated` event.

---

### DELETE `/api/v1/reporting-efforts/{id}`
Delete a reporting effort (with dependency checking).

**WebSocket Event**: Broadcasts `reporting_effort_deleted` event.

**Deletion Protection**: Checks for dependent reporting effort items before deletion.

---

## Reporting Effort Items

### POST `/api/v1/reporting-effort-items/`
Create a new reporting effort item.

**Request Body** (`ReportingEffortItemCreate`):
```json
{
    "reporting_effort_id": 1,
    "item_code": "T-14.1.1",
    "item_description": "Demographics and Baseline Characteristics",
    "item_type": "TLF",
    "item_status": "PENDING"
}
```

**Response** (`ReportingEffortItem`):
```json
{
    "id": 1,
    "reporting_effort_id": 1,
    "item_code": "T-14.1.1",
    "item_description": "Demographics and Baseline Characteristics",
    "item_type": "TLF",
    "item_status": "PENDING",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

**WebSocket Event**: Broadcasts `reporting_effort_item_created` event.

---

### GET `/api/v1/reporting-effort-items/`
Retrieve all reporting effort items.

---

### GET `/api/v1/reporting-effort-items/by-reporting-effort/{reporting_effort_id}`
Get items for a specific reporting effort.

**Path Parameters**:
- `reporting_effort_id: int` - Reporting effort ID

---

### PUT `/api/v1/reporting-effort-items/{id}`
Update a reporting effort item.

**WebSocket Event**: Broadcasts `reporting_effort_item_updated` event.

---

### DELETE `/api/v1/reporting-effort-items/{id}`
Delete a reporting effort item (with dependency checking).

**WebSocket Event**: Broadcasts `reporting_effort_item_deleted` event.

**Deletion Protection**: Checks for dependent trackers before deletion.

---

## Reporting Effort Trackers

### POST `/api/v1/reporting-effort-tracker/`
Create a new tracker for a reporting effort item.

**Request Body** (`ReportingEffortItemTrackerCreate`):
```json
{
    "reporting_effort_item_id": 1,
    "primary_programmer_id": 1,
    "qc_programmer_id": 2,
    "primary_status": "IN_PROGRESS",
    "qc_status": "NOT_STARTED"
}
```

**Response** (`ReportingEffortItemTracker`):
```json
{
    "id": 1,
    "reporting_effort_item_id": 1,
    "primary_programmer_id": 1,
    "qc_programmer_id": 2,
    "primary_status": "IN_PROGRESS",
    "qc_status": "NOT_STARTED",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

**WebSocket Event**: Broadcasts `reporting_effort_tracker_created` event.

---

### GET `/api/v1/reporting-effort-tracker/`
Retrieve all trackers with pagination.

---

### GET `/api/v1/reporting-effort-tracker/{id}`
Get a specific tracker by ID.

---

### PUT `/api/v1/reporting-effort-tracker/{id}`
Update an existing tracker.

**WebSocket Event**: Broadcasts `reporting_effort_tracker_updated` event.

---

### DELETE `/api/v1/reporting-effort-tracker/{id}` ⭐
Delete a reporting effort tracker.

**Path Parameters**:
- `id: int` - Tracker ID

**Response**:
```json
{
    "message": "Reporting effort tracker deleted successfully"
}
```

**WebSocket Event**: Broadcasts `reporting_effort_tracker_deleted` event with enhanced context:
```json
{
    "type": "reporting_effort_tracker_deleted",
    "data": {
        "tracker": {...},
        "deleted_at": "2024-12-01T15:30:00Z",
        "deleted_by": {"user_id": 1, "username": "johndoe"},
        "item": {"item_code": "T-14.1.1", "effort_id": 1}
    }
}
```

**Status Codes**:
- `204` - Tracker deleted successfully
- `404` - Tracker not found
- `422` - Validation error

**Features**:
- ✅ **Production Ready**: Thoroughly tested with comprehensive error handling
- ✅ **WebSocket Broadcasting**: Real-time updates across all connected clients
- ✅ **Audit Logging**: Complete deletion audit trail
- ✅ **Enhanced Context**: Provides user and item context in broadcast messages

---

### PUT `/api/v1/reporting-effort-tracker/{id}/assign-primary/{programmer_id}`
Assign primary programmer to a tracker.

**Path Parameters**:
- `id: int` - Tracker ID
- `programmer_id: int` - User ID of programmer

**WebSocket Event**: Broadcasts `tracker_assignment_updated` event.

---

### PUT `/api/v1/reporting-effort-tracker/{id}/assign-qc/{programmer_id}`
Assign QC programmer to a tracker.

**Path Parameters**:
- `id: int` - Tracker ID
- `programmer_id: int` - User ID of programmer

**WebSocket Event**: Broadcasts `tracker_assignment_updated` event.

---

## Packages

### POST `/api/v1/packages/`
Create a new package.

**Request Body** (`PackageCreate`):
```json
{
    "package_name": "Safety Analysis Package",
    "study_indication": "Oncology",
    "therapeutic_area": "Solid Tumors"
}
```

**Response** (`Package`):
```json
{
    "id": 1,
    "package_name": "Safety Analysis Package",
    "study_indication": "Oncology",
    "therapeutic_area": "Solid Tumors",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

**WebSocket Event**: Broadcasts `package_created` event.

---

### GET `/api/v1/packages/`
Retrieve all packages.

---

### GET `/api/v1/packages/{id}`
Get a specific package by ID.

---

### PUT `/api/v1/packages/{id}`
Update an existing package.

**WebSocket Event**: Broadcasts `package_updated` event.

---

### DELETE `/api/v1/packages/{id}`
Delete a package (with dependency checking).

**WebSocket Event**: Broadcasts `package_deleted` event.

**Deletion Protection**: Checks for dependent package items before deletion.

---

## Package Items

### POST `/api/v1/package-items/`
Create a new package item.

**Request Body** (`PackageItemCreate`):
```json
{
    "package_id": 1,
    "item_code": "T-14.1.1",
    "item_description": "Demographics and Baseline Characteristics",
    "item_type": "TLF"
}
```

**Response** (`PackageItem`):
```json
{
    "id": 1,
    "package_id": 1,
    "item_code": "T-14.1.1",
    "item_description": "Demographics and Baseline Characteristics",
    "item_type": "TLF",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

**WebSocket Event**: Broadcasts `package_item_created` event.

---

### GET `/api/v1/package-items/`
Retrieve all package items.

---

### GET `/api/v1/package-items/by-package/{package_id}`
Get items for a specific package.

**Path Parameters**:
- `package_id: int` - Package ID

---

### PUT `/api/v1/package-items/{id}`
Update a package item.

**WebSocket Event**: Broadcasts `package_item_updated` event.

---

### DELETE `/api/v1/package-items/{id}`
Delete a package item.

**WebSocket Event**: Broadcasts `package_item_deleted` event.

---

## Text Elements (TNFP)

### POST `/api/v1/text-elements/`
Create a new text element.

**Request Body** (`TextElementCreate`):
```json
{
    "type": "TITLE",
    "label": "Demographics Table",
    "content": "Table 14.1.1: Demographics and Baseline Characteristics"
}
```

**Response** (`TextElement`):
```json
{
    "id": 1,
    "type": "TITLE",
    "label": "Demographics Table",
    "content": "Table 14.1.1: Demographics and Baseline Characteristics",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

**WebSocket Event**: Broadcasts `text_element_created` event.

**Text Element Types**:
- `TITLE` - Table/Figure titles
- `FOOTNOTE` - Table/Figure footnotes
- `POPULATION_SET` - Analysis population definitions
- `ACRONYMS_SET` - Acronym definitions

---

### GET `/api/v1/text-elements/`
Retrieve all text elements with optional type filtering.

**Query Parameters**:
- `type: str` - Filter by text element type (optional)
- `skip: int = 0` - Records to skip
- `limit: int = 100` - Max records

---

### GET `/api/v1/text-elements/by-type/{type}`
Get text elements by type.

**Path Parameters**:
- `type: str` - Text element type (TITLE, FOOTNOTE, POPULATION_SET, ACRONYMS_SET)

---

### PUT `/api/v1/text-elements/{id}`
Update a text element.

**WebSocket Event**: Broadcasts `text_element_updated` event.

---

### DELETE `/api/v1/text-elements/{id}`
Delete a text element.

**WebSocket Event**: Broadcasts `text_element_deleted` event.

---

## Tracker Comments

### POST `/api/v1/tracker-comments/`
Create a new comment on a tracker.

**Request Body** (`TrackerCommentCreate`):
```json
{
    "tracker_id": 1,
    "user_id": 1,
    "comment_text": "Need clarification on the analysis population",
    "comment_type": "QUESTION"
}
```

**Response** (`TrackerCommentWithUserInfo`):
```json
{
    "id": 1,
    "tracker_id": 1,
    "user_id": 1,
    "username": "johndoe",
    "comment_text": "Need clarification on the analysis population",
    "comment_type": "QUESTION",
    "is_resolved": false,
    "parent_comment_id": null,
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

**WebSocket Event**: Broadcasts `comment_created` event with unresolved count.

---

### GET `/api/v1/tracker-comments/by-tracker/{tracker_id}`
Get all comments for a tracker.

**Path Parameters**:
- `tracker_id: int` - Tracker ID

**Response** (`List[TrackerCommentWithUserInfo]`):
Returns hierarchical comment structure with replies.

---

### POST `/api/v1/tracker-comments/{parent_comment_id}/reply`
Reply to an existing comment.

**Path Parameters**:
- `parent_comment_id: int` - Parent comment ID

**WebSocket Event**: Broadcasts `comment_replied` event.

---

### PUT `/api/v1/tracker-comments/{comment_id}/resolve`
Mark a comment as resolved.

**Path Parameters**:
- `comment_id: int` - Comment ID

**WebSocket Event**: Broadcasts `comment_resolved` event with updated unresolved count.

---

### PUT `/api/v1/tracker-comments/{id}`
Update an existing comment.

**WebSocket Event**: Broadcasts `comment_updated` event.

---

### DELETE `/api/v1/tracker-comments/{id}`
Delete a comment.

**WebSocket Event**: Broadcasts `comment_deleted` event.

---

## Audit Trail

### GET `/api/v1/audit-trail/`
Retrieve audit log entries.

**Query Parameters**:
- `entity_type: str` - Filter by entity type (optional)
- `action: str` - Filter by action (CREATE, UPDATE, DELETE) (optional)
- `user_id: int` - Filter by user (optional)
- `start_date: str` - Filter from date (ISO format) (optional)
- `end_date: str` - Filter to date (ISO format) (optional)
- `skip: int = 0` - Records to skip
- `limit: int = 100` - Max records

**Response** (`List[AuditLog]`):
```json
[
    {
        "id": 1,
        "entity_type": "study",
        "entity_id": 1,
        "action": "CREATE",
        "user_id": 1,
        "changes": {"study_label": "ONCOLOGY-2024-001"},
        "timestamp": "2024-12-01T10:00:00Z"
    }
]
```

---

## Database Backup

### POST `/api/v1/database-backup/`
Create a database backup.

**Response**:
```json
{
    "message": "Database backup created successfully",
    "backup_file": "pearl_backup_20241201_100000.sql",
    "timestamp": "2024-12-01T10:00:00Z"
}
```

---

### GET `/api/v1/database-backup/list`
List available backup files.

**Response**:
```json
{
    "backups": [
        {
            "filename": "pearl_backup_20241201_100000.sql",
            "created_at": "2024-12-01T10:00:00Z",
            "size_mb": 125.4
        }
    ]
}
```

---

## WebSocket

### WS `/api/v1/ws/studies`
WebSocket endpoint for real-time updates.

**Connection URL**: `ws://localhost:8000/api/v1/ws/studies`

**Client Messages**:
```json
{"action": "ping"}        // Keep connection alive
{"action": "refresh"}     // Request data refresh
```

**Server Messages**:
```json
{"type": "pong"}                           // Connection alive response
{"type": "study_created", "data": {...}}   // Entity created
{"type": "study_updated", "data": {...}}   // Entity updated  
{"type": "study_deleted", "data": {...}}   // Entity deleted
{"type": "error", "message": "..."}        // Error occurred
```

**Connection Management**:
- Automatic reconnection with exponential backoff
- Keep-alive pings every 30 seconds
- Stale connection cleanup
- Cross-browser synchronization support

---

## Health Check

### GET `/api/health`
Basic health check endpoint.

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2024-12-01T10:00:00Z",
    "service": "PEARL API"
}
```

**Status Codes**:
- `200` - Service is healthy
- `503` - Service is unhealthy

---

## Phase 2 Enhancements

### Utility Functions Integration

All endpoints leverage Phase 2 utility functions:

1. **Validation Utils** (`backend/app/api/v1/utils/validation.py`):
   - Standardized error handling with `@handle_validation_error` decorator
   - Consistent HTTP exception patterns
   - Business logic validation helpers

2. **WebSocket Utils** (`backend/app/api/v1/utils/websocket_utils.py`):
   - Automatic SQLAlchemy → Pydantic conversion
   - Enhanced broadcasting with context
   - Batch model conversion utilities

3. **Endpoint Factory** (`backend/app/api/v1/utils/endpoint_factory.py`):
   - Generic CRUD endpoint generators
   - Standardized dependency checking
   - Consistent response patterns

### Cross-Browser Synchronization

All CRUD operations trigger WebSocket broadcasts for real-time synchronization:
- Create operations → `{entity}_created` events
- Update operations → `{entity}_updated` events  
- Delete operations → `{entity}_deleted` events with enhanced context

### Error Handling Patterns

Consistent error handling across all endpoints:
- Validation errors include field-level details
- Dependency conflicts provide specific entity names
- Database constraint violations are user-friendly
- WebSocket broadcasting never breaks API operations

---

## Testing

Individual test scripts are available in `backend/tests/scripts/`:
- `test_crud_simple.sh` - Basic CRUD functionality
- `test_packages_crud.sh` - Package system testing
- `test_reporting_effort_tracker_crud.sh` - Tracker system testing
- `test_tracker_delete_simple.sh` - Tracker deletion testing

**Note**: This system uses individual test execution due to SQLAlchemy async session constraints.

---

## Related Documentation

- [WEBSOCKET_EVENTS.md](WEBSOCKET_EVENTS.md) - WebSocket message types and routing
- [CRUD_METHODS.md](CRUD_METHODS.md) - Detailed CRUD operation documentation  
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Database schema and relationships
- [UTILITY_FUNCTIONS.md](UTILITY_FUNCTIONS.md) - Phase 2 utility documentation