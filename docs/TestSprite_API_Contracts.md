# PEARL API Contracts for TestSprite

This document provides exact API specifications for TestSprite to generate accurate tests.

## Critical Testing Requirements

### Environment Setup
- **Required Python Package**: `websocket-client` must be installed for WebSocket tests
- **Test Environment**: Python 3.11+, requests library, websocket-client library
- **Base URL**: `http://0.0.0.0:8000` (or configurable)

## API Endpoints and Exact Field Names

### 1. Health Endpoint

**GET /health**
- **Response Codes**: 
  - `200` - Service and database healthy
  - `503` - Service or database unhealthy
- **Response Body**: May be empty or contain health details

### 2. Studies API

**POST /api/v1/studies**
```json
Request Body:
{
  "study_label": "string"  // NOT "label" - must be "study_label"
}

Response (201 Created):
{
  "id": 1,
  "study_label": "string",
  "created_at": "2025-08-07T10:00:00",
  "updated_at": "2025-08-07T10:00:00"
}

Error Response (400 - Duplicate):
{
  "detail": "Study with this label already exists"
}
```

**PUT /api/v1/studies/{id}**
```json
Request Body:
{
  "study_label": "string"  // NOT "label"
}
```

**DELETE /api/v1/studies/{id}**
```json
Error Response (400 - Has Dependencies):
{
  "detail": "Cannot delete study 'StudyName': N associated database release(s) exist: release1, release2. Please delete all associated database releases first."
}
```

### 3. Database Releases API

**POST /api/v1/database-releases**
```json
Request Body:
{
  "database_release_label": "string",  // NOT "label"
  "study_id": 1
}

Response (201 Created):
{
  "id": 1,
  "database_release_label": "string",
  "study_id": 1,
  "created_at": "2025-08-07T10:00:00",
  "updated_at": "2025-08-07T10:00:00"
}

Error Response (400 - Duplicate in Same Study):
{
  "detail": "Database release with this label already exists for this study"
}
```

**PUT /api/v1/database-releases/{id}**
```json
Request Body:
{
  "database_release_label": "string",  // NOT "label"
  "study_id": 1
}
```

**DELETE /api/v1/database-releases/{id}**
```json
Error Response (400 - Has Dependencies):
{
  "detail": "Cannot delete database release 'ReleaseName': N associated reporting effort(s) exist: effort1, effort2. Please delete all associated reporting efforts first."
}
```

### 4. Reporting Efforts API

**POST /api/v1/reporting-efforts**
```json
Request Body:
{
  "database_release_label": "string",  // NOT "label"
  "study_id": 1,
  "database_release_id": 1
}

Response (201 Created):
{
  "id": 1,
  "database_release_label": "string",
  "study_id": 1,
  "database_release_id": 1,
  "created_at": "2025-08-07T10:00:00",
  "updated_at": "2025-08-07T10:00:00"
}
```

**PUT /api/v1/reporting-efforts/{id}**
```json
Request Body:
{
  "database_release_label": "string"  // ONLY this field can be updated
}
// NOTE: study_id and database_release_id are IMMUTABLE after creation
```

### 5. Text Elements API

**POST /api/v1/text-elements**
```json
Request Body:
{
  "label": "string",  // This one IS "label", not "text_element_label"
  "type": "title" | "footnote" | "population_set" | "acronyms_set"
}

Response (201 Created):
{
  "id": 1,
  "label": "string",
  "type": "title",
  "created_at": "2025-08-07T10:00:00",
  "updated_at": "2025-08-07T10:00:00"
}

Error Response (400 - Duplicate):
{
  "detail": "A title with similar content already exists: 'ExistingLabel'. Duplicate text elements are not allowed (comparison ignores spaces and case)."
}
```

**GET /api/v1/text-elements/search?q={query}**
- Search is case-insensitive
- Search does NOT work with spaces in the middle of words (e.g., "uni que" won't find "unique")

**Known Issue**: Duplicate prevention on UPDATE doesn't work for case/space variations (only on CREATE)

### 6. Packages API

**POST /api/v1/packages**
```json
Request Body:
{
  "package_name": "string"  // NOT "name"
}

Response (201 Created):
{
  "id": 1,
  "package_name": "string",
  "created_at": "2025-08-07T10:00:00",
  "updated_at": "2025-08-07T10:00:00"
}

Error Response (400 - Duplicate):
{
  "detail": "Package with this name already exists"
}
```

**PUT /api/v1/packages/{id}**
```json
Request Body:
{
  "package_name": "string"  // NOT "name"
}
```

**DELETE /api/v1/packages/{id}**
```json
Error Response (400 - Has Dependencies):
{
  "detail": "Cannot delete package 'PackageName': has dependent package items: TBL001, TBL002, ... (showing first 5). Please delete all package items first."
}
```

### 7. Package Items API

**POST /api/v1/packages/{package_id}/items**
```json
Request Body:
{
  "package_id": 1,
  "study_id": 1,
  "item_type": "TLF" | "Dataset",
  "item_subtype": "Table" | "Listing" | "Figure" (for TLF) OR "SDTM" | "ADaM" (for Dataset),
  "item_code": "string"  // e.g., "TBL001"
}

Response (201 Created):
{
  "id": 1,
  "package_id": 1,
  "study_id": 1,
  "item_type": "TLF",
  "item_subtype": "Table",
  "item_code": "TBL001",
  "created_at": "2025-08-07T10:00:00",
  "updated_at": "2025-08-07T10:00:00"
}

Error Response (400 - Duplicate Composite Key):
{
  "detail": "Package item with type=TLF, subtype=Table, code=TBL001 already exists in this package"
}
```

**PUT /api/v1/packages/items/{item_id}**
```json
Request Body:
{
  "item_code": "string"  // Limited fields can be updated
}
```

### 8. WebSocket Endpoint

**WebSocket /api/v1/ws/studies**

**Initial Connection Message:**
```json
{
  "type": "studies_update",  // NOT "initial_snapshot"
  "data": [
    {
      "id": 1,
      "study_label": "string",  // NOT "label"
      "created_at": "2025-08-07T10:00:00",
      "updated_at": "2025-08-07T10:00:00"
    }
  ]
}
```

**Create Event:**
```json
{
  "type": "study_created",  // NOT "event": "create"
  "data": {
    "id": 1,
    "study_label": "string",
    "created_at": "2025-08-07T10:00:00",
    "updated_at": "2025-08-07T10:00:00"
  }
}
```

**Update Event:**
```json
{
  "type": "study_updated",  // NOT "event": "update"
  "data": {
    "id": 1,
    "study_label": "string",
    "created_at": "2025-08-07T10:00:00",
    "updated_at": "2025-08-07T10:00:00"
  }
}
```

**Delete Event:**
```json
{
  "type": "study_deleted",  // NOT "event": "delete"
  "data": {
    "id": 1
  }
}
```

## Error Message Patterns

### Duplicate Detection
- Studies: `"Study with this label already exists"`
- Database Releases: `"Database release with this label already exists for this study"`
- Packages: `"Package with this name already exists"`
- Package Items: `"Package item with type=X, subtype=Y, code=Z already exists in this package"`
- Text Elements: `"A {type} with similar content already exists: '{existing_label}'. Duplicate text elements are not allowed (comparison ignores spaces and case)."`

### Deletion Protection
- Studies: `"Cannot delete study '{label}': {count} associated database release(s) exist: {list}. Please delete all associated database releases first."`
- Database Releases: `"Cannot delete database release '{label}': {count} associated reporting effort(s) exist: {list}. Please delete all associated reporting efforts first."`
- Packages: `"Cannot delete package '{name}': has dependent package items: {list} (showing first 5). Please delete all package items first."`

### Foreign Key Validation
- Invalid Study ID: Returns 404 or 422
- Invalid Database Release ID: Returns 404 or 422
- Mismatched Database Release (not belonging to specified Study): Returns 400

## Important Testing Notes

1. **Field Names Are Critical**: Each API uses specific field names that must match exactly
2. **Error Assertions**: Don't look for "duplicate" or "unique" - look for "already exists"
3. **Immutable Fields**: Some fields cannot be changed after creation (e.g., study_id and database_release_id in reporting efforts)
4. **WebSocket Structure**: Messages use `type` field with specific event names, not generic `event`/`entity` structure
5. **Case Sensitivity**: Most duplicate checks are case-insensitive
6. **Timestamps**: All entities include created_at and updated_at in responses

## Test Setup Requirements

```python
import requests
import websocket  # from websocket-client package
import json
import time
import threading

BASE_URL = "http://0.0.0.0:8000"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 30
```

## Common Test Patterns

### Creating Unique Labels
```python
unique_label = f"test-entity-{int(time.time()*1000)}"
```

### WebSocket Connection
```python
ws_url = "ws://0.0.0.0:8000/api/v1/ws/studies"
ws = websocket.WebSocketApp(ws_url, 
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close,
                            on_open=on_open)
```

### Cleanup Pattern
```python
try:
    # Test operations
    pass
finally:
    # Always cleanup created resources
    if resource_id:
        requests.delete(f"{BASE_URL}/api/v1/resource/{resource_id}", timeout=TIMEOUT)
```