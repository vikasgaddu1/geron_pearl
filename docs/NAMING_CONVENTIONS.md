# Naming Conventions Documentation

**PEARL Full-Stack Research Data Management System**  
**Formal Naming Standards and Conventions**

This document formalizes the agreed-upon naming standards from CLAUDE.md and establishes consistent naming conventions across the PEARL system for maintainability and clarity.

## Table of Contents

- [General Principles](#general-principles)
- [Backend Naming Conventions](#backend-naming-conventions)
- [Frontend Naming Conventions](#frontend-naming-conventions)
- [Database Naming Conventions](#database-naming-conventions)
- [API Naming Conventions](#api-naming-conventions)
- [WebSocket Event Naming](#websocket-event-naming)
- [File and Directory Naming](#file-and-directory-naming)
- [Variable and Function Naming](#variable-and-function-naming)
- [Documentation Naming](#documentation-naming)

---

## General Principles

### Core Guidelines

1. **Consistency**: Use the same naming pattern throughout the project
2. **Clarity**: Names should be self-documenting and unambiguous
3. **Context**: Include enough context to avoid confusion
4. **Standards**: Follow language/framework conventions (Python PEP 8, R conventions)
5. **Brevity**: Be concise but not at the expense of clarity

### Case Conventions by Context

- **Python**: `snake_case` for variables, functions, modules
- **Python Classes**: `PascalCase` for class names
- **R Functions**: `snake_case` preferred, `camelCase` acceptable
- **JavaScript**: `camelCase` for variables/functions, `PascalCase` for classes
- **Database**: `snake_case` for tables and columns
- **URLs/Endpoints**: `kebab-case` with hyphens
- **Environment Variables**: `UPPER_SNAKE_CASE`

---

## Backend Naming Conventions

### Python Files and Modules

#### File Naming Pattern
```
# Models (singular, snake_case)
study.py
database_release.py
reporting_effort.py
reporting_effort_item.py
reporting_effort_item_tracker.py
package_item.py
tracker_comment.py
text_element.py
user.py

# CRUD classes (singular, snake_case)
study.py
database_release.py
package.py
crud_user.py  # Exception: avoid conflict with user.py model

# API routers (plural, snake_case)
studies.py
database_releases.py
reporting_efforts.py
reporting_effort_items.py
reporting_effort_tracker.py  # Singular: only one tracker per item
packages.py
package_items.py
text_elements.py
users.py
tracker_comments.py

# Schemas (singular, snake_case)
study.py
database_release.py
package.py
user.py
```

### Python Class Names

#### Model Classes (PascalCase, Singular)
```python
class Study(Base):
    __tablename__ = "studies"

class DatabaseRelease(Base):
    __tablename__ = "database_releases"

class ReportingEffort(Base):
    __tablename__ = "reporting_efforts"

class ReportingEffortItem(Base):
    __tablename__ = "reporting_effort_items"

class ReportingEffortItemTracker(Base):
    __tablename__ = "reporting_effort_item_trackers"

class PackageItem(Base):
    __tablename__ = "package_items"

class TrackerComment(Base):
    __tablename__ = "tracker_comments"

class TextElement(Base):
    __tablename__ = "text_elements"
```

#### CRUD Classes (PascalCase + "CRUD")
```python
class StudyCRUD(BaseCRUD[Study, StudyCreate, StudyUpdate]):
    pass

class DatabaseReleaseCRUD(BaseCRUD[DatabaseRelease, DatabaseReleaseCreate, DatabaseReleaseUpdate]):
    pass

class ReportingEffortItemTrackerCRUD(BaseCRUD[ReportingEffortItemTracker, ReportingEffortItemTrackerCreate, ReportingEffortItemTrackerUpdate]):
    pass
```

#### Schema Classes (PascalCase + Purpose)
```python
# Base schemas (no suffix)
class Study(BaseModel):
    """Response schema"""

# Create schemas
class StudyCreate(BaseModel):
    """Create request schema"""

# Update schemas  
class StudyUpdate(BaseModel):
    """Update request schema"""

# Enhanced schemas (descriptive suffix)
class TrackerCommentWithUserInfo(BaseModel):
    """Comment with user details"""

class ReportingEffortItemTrackerWithDetails(BaseModel):
    """Tracker with item and user details"""
```

### Python Function Names

#### CRUD Methods (snake_case, descriptive verbs)
```python
# Standard CRUD operations
async def get(self, db: AsyncSession, *, id: int)
async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100)
async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType)
async def update(self, db: AsyncSession, *, db_obj: ModelType, obj_in: UpdateSchemaType)
async def delete(self, db: AsyncSession, *, id: int)

# Relationship queries (get_by_[relationship])
async def get_by_study_id(self, db: AsyncSession, *, study_id: int)
async def get_by_package_id(self, db: AsyncSession, *, package_id: int)
async def get_by_tracker_id(self, db: AsyncSession, *, tracker_id: int)
async def get_by_username(self, db: AsyncSession, *, username: str)

# Business logic methods (descriptive action)
async def assign_primary_programmer(self, db: AsyncSession, *, tracker_id: int, programmer_id: int)
async def assign_qc_programmer(self, db: AsyncSession, *, tracker_id: int, programmer_id: int)
async def resolve_comment(self, db: AsyncSession, *, comment_id: int)
async def create_reply(self, db: AsyncSession, *, parent_comment_id: int, comment_in: TrackerCommentCreate)
```

#### WebSocket Broadcast Functions (broadcast_[entity]_[action])
```python
# Standard pattern: broadcast_[entity]_[action]
async def broadcast_study_created(study_data)
async def broadcast_study_updated(study_data)
async def broadcast_study_deleted(study_id: int)

async def broadcast_package_item_created(package_item_data)
async def broadcast_package_item_updated(package_item_data)
async def broadcast_package_item_deleted(package_item_data)

async def broadcast_comment_created(tracker_id: int, comment_data, unresolved_count: int)
async def broadcast_comment_replied(tracker_id: int, parent_comment_id: int, comment_data, unresolved_count: int)
async def broadcast_comment_resolved(tracker_id: int, comment_id: int, unresolved_count: int)

# Enhanced broadcasts (with context)
async def broadcast_reporting_effort_tracker_deleted(tracker_data, user_info=None, item_info=None)
```

#### Utility Functions (descriptive_action)
```python
# Validation utilities
def raise_not_found_exception(entity_type: str, entity_id: int)
def raise_business_logic_exception(message: str, status_code: int = 400)
def raise_dependency_conflict_exception(entity_type, entity_label, dependent_count, dependent_type, dependent_names)

# Conversion utilities
def sqlalchemy_to_dict(obj)
def convert_models_for_broadcast(models: List) -> List[Dict]

# WebSocket utilities
async def broadcast_entity_change(entity_data, event_type: str)
async def enhanced_broadcast_with_context(entity_data, event_type: str, context: Dict = None)

# Endpoint factory functions
def create_get_endpoint(crud_class, response_model, entity_type)
def create_post_endpoint(crud_class, create_model, response_model, entity_type, broadcast_func)
def create_delete_endpoint(crud_class, entity_type, broadcast_func, dependency_checks)
```

### Python Variable Names

#### Instance Variables (snake_case)
```python
# CRUD instances (lowercase entity name)
study = StudyCRUD(Study)
database_release = DatabaseReleaseCRUD(DatabaseRelease)
reporting_effort_item_tracker = ReportingEffortItemTrackerCRUD(ReportingEffortItemTracker)
user = UserCRUD(User)  # Note: not user_crud to avoid import conflicts

# Database session
db: AsyncSession
async_session: AsyncSessionLocal

# Request/response objects
study_data: StudyCreate
updated_study: Study
db_study: Study  # Database object
```

---

## Frontend Naming Conventions

### R File Names

#### Module Files (snake_case + purpose)
```r
# UI modules (entity_ui.R)
admin_dashboard_ui.R
study_tree_ui.R
users_ui.R
packages_ui.R
package_items_ui.R
reporting_effort_tracker_ui.R
tnfp_ui.R  # TextElement = TNFP (Title, Note, Footnote, Population)
database_backup_ui.R
audit_trail_ui.R

# Server modules (entity_server.R)
admin_dashboard_server.R
study_tree_server.R
users_server.R
packages_server.R
package_items_server.R
reporting_effort_tracker_server.R
tnfp_server.R
database_backup_server.R
audit_trail_server.R

# Utility modules (purpose.R)
api_client.R
websocket_client.R
comment_expansion.R  # Special UI helper

# Utility subdirectory (utils/purpose.R)
utils/crud_base.R
utils/api_utils.R
```

### R Function Names

#### Module Functions (snake_case + purpose)
```r
# UI functions (entity_ui)
study_tree_ui <- function(id)
users_ui <- function(id) 
packages_ui <- function(id)
package_items_ui <- function(id)
reporting_effort_tracker_ui <- function(id)

# Server functions (entity_server)
study_tree_server <- function(id)
users_server <- function(id)
packages_server <- function(id)
package_items_server <- function(id)
reporting_effort_tracker_server <- function(id)

# API client functions (action_entity or get_entity_action)
get_studies <- function()
create_study <- function(study_data)
update_study <- function(study_id, study_data)
delete_study <- function(study_id)

get_package_items_by_package <- function(package_id)
get_tracker_comments <- function(tracker_id)
assign_primary_programmer <- function(tracker_id, programmer_id)

# Utility functions (purpose_action or action_purpose)
create_standard_datatable <- function(...)
setup_enhanced_form_validation <- function(...)
show_success_notification <- function(...)
extract_error_message <- function(...)
build_endpoint_url <- function(...)
```

#### Modal Functions (action_entity_modal or create_purpose_modal)
```r
# Standard modal creators
create_edit_modal <- function(...)
create_create_modal <- function(...)
create_delete_confirmation_modal <- function(...)
create_bulk_upload_modal <- function(...)
create_export_modal <- function(...)

# Entity-specific modal functions  
show_edit_user_modal <- function(user_data)
show_create_study_modal <- function()
show_delete_package_confirmation <- function(package_data)
```

### R Variable Names

#### Reactive Values (snake_case + "_data" suffix for collections)
```r
# Data collections (plural + _data)
users_data <- reactiveVal(NULL)
studies_data <- reactiveVal(NULL)
packages_data <- reactiveVal(NULL)
package_items_data <- reactiveVal(NULL)
tracker_comments_data <- reactiveVal(NULL)

# Selected items (selected_ + entity)
selected_user <- reactiveVal(NULL)
selected_study <- reactiveVal(NULL)
selected_package <- reactiveVal(NULL)
selected_tracker <- reactiveVal(NULL)

# State variables (descriptive purpose)
loading_state <- reactiveVal(FALSE)
validation_errors <- reactiveVal(list())
current_page <- reactiveVal(1)
```

#### API Endpoints (entity + "_endpoint")
```r
# Environment-based endpoint configuration
api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")

studies_endpoint <- build_endpoint_url("PEARL_STUDIES_ENDPOINT", "/api/v1/studies")
users_endpoint <- build_endpoint_url("PEARL_USERS_ENDPOINT", "/api/v1/users")
packages_endpoint <- build_endpoint_url("PEARL_PACKAGES_ENDPOINT", "/api/v1/packages")
package_items_endpoint <- build_endpoint_url("PEARL_PACKAGE_ITEMS_ENDPOINT", "/api/v1/package-items")
trackers_endpoint <- build_endpoint_url("PEARL_TRACKERS_ENDPOINT", "/api/v1/reporting-effort-tracker")
```

### JavaScript Naming

#### WebSocket Client (camelCase)
```javascript
class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000;
    }

    // Methods (camelCase)
    connect() {}
    disconnect() {}
    handleMessage(event) {}
    notifyShiny(eventType, data, moduleId) {}
    notifyShinyGlobal(eventType, data, globalId) {}
}

// Instance (camelCase)
const wsClient = new WebSocketClient();

// Event handlers (camelCase)
function bindActionButtons() {}
function bindUserActionButtons() {}
function bindPackageActionButtons() {}

// Shiny handlers (camelCase)
Shiny.addCustomMessageHandler('triggerPackageRefresh', function(message) {});
Shiny.addCustomMessageHandler('triggerUserRefresh', function(message) {});
```

---

## Database Naming Conventions

### Table Names (snake_case, plural)
```sql
-- Core entities
studies
database_releases  
reporting_efforts
reporting_effort_items
reporting_effort_item_trackers

-- Package system  
packages
package_items
package_tlf_details
package_dataset_details

-- Text elements
text_elements

-- Comment system
tracker_comments

-- Support tables
users
audit_logs
```

### Column Names (snake_case)
```sql
-- Primary keys (always "id")
id SERIAL PRIMARY KEY

-- Foreign keys (entity_id)
study_id INTEGER REFERENCES studies(id)
database_release_id INTEGER REFERENCES database_releases(id)
reporting_effort_id INTEGER REFERENCES reporting_efforts(id)
package_id INTEGER REFERENCES packages(id)
user_id INTEGER REFERENCES users(id)
tracker_id INTEGER REFERENCES reporting_effort_item_trackers(id)
parent_comment_id INTEGER REFERENCES tracker_comments(id)

-- Descriptive columns (snake_case)
study_label VARCHAR NOT NULL
database_release_label VARCHAR NOT NULL
database_release_date DATE NOT NULL
item_code VARCHAR NOT NULL
item_description TEXT
item_type VARCHAR NOT NULL
item_status VARCHAR NOT NULL
package_name VARCHAR NOT NULL
study_indication VARCHAR
therapeutic_area VARCHAR
comment_text TEXT NOT NULL
comment_type VARCHAR NOT NULL
is_resolved BOOLEAN DEFAULT FALSE

-- Timestamps (standard pattern)
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
```

### Index Names (idx_table_purpose)
```sql
-- Primary key indexes (automatic)
-- Format: table_pkey

-- Unique indexes (idx_table_column or idx_table_unique_purpose)
CREATE UNIQUE INDEX idx_studies_label ON studies(study_label);
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE UNIQUE INDEX idx_packages_name ON packages(package_name);
CREATE UNIQUE INDEX idx_db_releases_study_label ON database_releases(study_id, database_release_label);

-- Foreign key indexes (idx_table_fk_column)
CREATE INDEX idx_database_releases_study_id ON database_releases(study_id);
CREATE INDEX idx_reporting_efforts_db_release_id ON reporting_efforts(database_release_id);
CREATE INDEX idx_package_items_package_id ON package_items(package_id);
CREATE INDEX idx_comments_tracker_id ON tracker_comments(tracker_id);

-- Query optimization indexes (idx_table_purpose)
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_comments_resolved ON tracker_comments(is_resolved, tracker_id);
CREATE INDEX idx_trackers_status ON reporting_effort_item_trackers(primary_status, qc_status);
```

### Constraint Names (table_column_constraint_type)
```sql
-- Foreign key constraints
CONSTRAINT database_releases_study_id_fkey FOREIGN KEY (study_id) REFERENCES studies(id)
CONSTRAINT reporting_efforts_database_release_id_fkey FOREIGN KEY (database_release_id) REFERENCES database_releases(id)
CONSTRAINT package_items_package_id_fkey FOREIGN KEY (package_id) REFERENCES packages(id)
CONSTRAINT tracker_comments_tracker_id_fkey FOREIGN KEY (tracker_id) REFERENCES reporting_effort_item_trackers(id)

-- Unique constraints  
CONSTRAINT studies_study_label_key UNIQUE (study_label)
CONSTRAINT users_username_key UNIQUE (username)
CONSTRAINT packages_package_name_key UNIQUE (package_name)
```

---

## API Naming Conventions

### Endpoint Paths (kebab-case, RESTful)
```
# Base pattern: /api/v1/entity-name

# Core entities
/api/v1/studies
/api/v1/database-releases
/api/v1/reporting-efforts  
/api/v1/reporting-effort-items
/api/v1/reporting-effort-tracker  # Singular: one tracker per item

# Package system
/api/v1/packages
/api/v1/package-items

# Support entities
/api/v1/text-elements
/api/v1/users
/api/v1/tracker-comments

# System endpoints
/api/v1/audit-trail
/api/v1/database-backup
```

### HTTP Methods (Standard REST)
```
GET    /api/v1/studies           # List all studies
GET    /api/v1/studies/{id}      # Get specific study
POST   /api/v1/studies           # Create new study
PUT    /api/v1/studies/{id}      # Update study
DELETE /api/v1/studies/{id}      # Delete study

# Relationship endpoints
GET    /api/v1/database-releases/by-study/{study_id}
GET    /api/v1/package-items/by-package/{package_id}
GET    /api/v1/tracker-comments/by-tracker/{tracker_id}

# Action endpoints (POST for actions)
POST   /api/v1/tracker-comments/{parent_id}/reply
PUT    /api/v1/tracker-comments/{id}/resolve
PUT    /api/v1/reporting-effort-tracker/{id}/assign-primary/{programmer_id}
PUT    /api/v1/reporting-effort-tracker/{id}/assign-qc/{programmer_id}
```

### Query Parameters (snake_case)
```
# Pagination
?skip=0&limit=100

# Filtering
?entity_type=study&action=CREATE&user_id=1
?type=TITLE&search=demographics
?status=PENDING&primary_programmer_id=1

# Date ranges  
?start_date=2024-01-01&end_date=2024-12-31

# Search
?q=search_term&limit=50
```

### Request/Response Fields (snake_case, match database)
```json
{
  "id": 1,
  "study_label": "ONCOLOGY-2024-001",
  "created_at": "2024-12-01T10:00:00Z",
  "updated_at": "2024-12-01T10:00:00Z"
}

{
  "database_release_id": 1,
  "database_release_label": "DB_LOCK_20241201",
  "database_release_date": "2024-12-01"
}

{
  "reporting_effort_item_id": 1,
  "primary_programmer_id": 1,
  "qc_programmer_id": 2,
  "primary_status": "IN_PROGRESS",
  "qc_status": "NOT_STARTED"
}
```

---

## WebSocket Event Naming

### Event Types ([entity]_[action])
```javascript
// Standard CRUD events
"study_created"
"study_updated"  
"study_deleted"

"database_release_created"
"database_release_updated"
"database_release_deleted"

"package_item_created"
"package_item_updated"
"package_item_deleted"

"reporting_effort_tracker_updated"
"reporting_effort_tracker_deleted"

// Special action events
"tracker_assignment_updated"
"comment_created"
"comment_replied"
"comment_resolved"
"comment_updated"
"comment_deleted"

// System events
"refresh_needed"
"error"
"pong"
```

### WebSocket Message Structure
```json
{
  "type": "study_created",
  "data": {
    "id": 1,
    "study_label": "ONCOLOGY-2024-001",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
  },
  "timestamp": "2024-12-01T10:00:00Z"
}

// Enhanced messages with context
{
  "type": "reporting_effort_tracker_deleted",
  "data": {
    "tracker": { /* tracker data */ },
    "deleted_at": "2024-12-01T15:30:00Z",
    "deleted_by": {
      "user_id": 1,
      "username": "johndoe"
    },
    "item": {
      "item_code": "T-14.1.1",
      "effort_id": 1
    }
  },
  "timestamp": "2024-12-01T15:30:00Z"
}
```

### Shiny Input Names (module-websocket_event or crud_refresh)
```r
# Universal CRUD Manager (recommended)
input$crud_refresh  # Within module (prefix automatically stripped)

# Legacy pattern (module-specific)
input$`users-websocket_event`
input$`packages-websocket_event`
input$`study_tree-websocket_event`

# Global observer pattern
input$`package_update-websocket_event`
input$`user_update-websocket_event`

# Custom refresh inputs (for JavaScript handlers)
input$`packages_simple-crud_refresh`
input$`users_module-crud_refresh`
```

---

## File and Directory Naming

### Backend Directory Structure
```
backend/
├── app/
│   ├── api/
│   │   ├── health.py                    # System endpoint
│   │   └── v1/
│   │       ├── studies.py               # Entity endpoints (plural)
│   │       ├── database_releases.py
│   │       ├── package_items.py
│   │       ├── reporting_effort_tracker.py  # Singular: one per item
│   │       ├── websocket.py             # System WebSocket
│   │       └── utils/
│   │           ├── validation.py        # Purpose-based naming
│   │           ├── websocket_utils.py
│   │           └── endpoint_factory.py
│   ├── crud/
│   │   ├── study.py                     # Entity CRUD (singular)
│   │   ├── database_release.py
│   │   ├── crud_user.py                 # Avoid conflicts
│   │   └── base.py                      # Base classes
│   ├── models/
│   │   ├── study.py                     # Entity models (singular)
│   │   ├── database_release.py
│   │   ├── package_item.py
│   │   └── enums.py                     # Shared enums
│   ├── schemas/
│   │   ├── study.py                     # Entity schemas (singular)
│   │   ├── database_release.py
│   │   └── package_item.py
│   └── db/
│       ├── session.py                   # Database connection
│       ├── init_db.py                   # Database initialization  
│       └── base.py                      # Base model class
```

### Frontend Directory Structure
```
admin-frontend/
├── modules/
│   ├── admin_dashboard_ui.R             # Module UI (entity_ui.R)
│   ├── admin_dashboard_server.R         # Module server (entity_server.R)
│   ├── study_tree_ui.R
│   ├── study_tree_server.R
│   ├── users_ui.R
│   ├── users_server.R
│   ├── api_client.R                     # Purpose-based utility
│   ├── websocket_client.R
│   ├── comment_expansion.R              # Special UI helper
│   └── utils/                           # Utility subdirectory
│       ├── crud_base.R                  # Purpose_base.R
│       └── api_utils.R                  # Purpose_utils.R
├── www/                                 # Static web assets
│   ├── websocket_client.js              # Purpose_client.js
│   ├── shiny_handlers.js                # Purpose_handlers.js
│   ├── datatable_utils.js               # Purpose_utils.js
│   ├── crud_activity_manager.js         # Purpose_manager.js
│   └── style.css                        # Standard CSS
└── tests/
    ├── study-tree.spec.ts               # Entity-test.spec.ts
    └── console-errors.spec.ts           # Purpose-test.spec.ts
```

### Test File Naming
```
# Backend test files (test_purpose.py)
test_crud_simple.py
test_api_endpoints.py
test_websocket_broadcast.py
test_validation.py

# Backend test scripts (test_purpose.sh)
test_crud_simple.sh
test_packages_crud.sh
test_reporting_effort_tracker_crud.sh
test_tracker_delete_simple.sh

# Frontend test files (purpose-test.spec.ts)
study-tree.spec.ts
cross-browser-comment-sync.spec.ts
console-errors.spec.ts
```

### Documentation Files
```
# Main documentation (PURPOSE.md)
README.md
API_REFERENCE.md
WEBSOCKET_EVENTS.md
DATABASE_SCHEMA.md
NAMING_CONVENTIONS.md
CODE_PATTERNS.md

# Component documentation (CLAUDE.md per directory)
backend/CLAUDE.md
admin-frontend/CLAUDE.md
docs/CLAUDE.md

# Specialized documentation (PURPOSE_DETAIL.md)
CASCADE_DELETE_MIGRATION_PLAN.md
FK_CASCADE_ANALYSIS.md
MODEL_VALIDATOR_README.md
```

---

## Variable and Function Naming

### Python Variables

#### Local Variables (snake_case, descriptive)
```python
# Entity instances (from database)
db_study = await study.get(db, id=study_id)
existing_user = await user.get_by_username(db, username=username)
tracker_comments = await tracker_comment.get_by_tracker_id(db, tracker_id=tracker_id)

# Request data (input suffix for clarity)
study_data_in = StudyCreate(study_label="ONCOLOGY-2024-001")
update_data_in = StudyUpdate(study_label="ONCOLOGY-2024-001-UPDATED")

# Response data (clear purpose)
created_study = await study.create(db, obj_in=study_data_in)
updated_tracker = await tracker.assign_primary_programmer(db, tracker_id=1, programmer_id=2)
deleted_package = await package.delete(db, id=package_id)

# Collections (plural)
all_studies = await study.get_multi(db)
dependent_releases = await database_release.get_by_study_id(db, study_id=study.id)
release_labels = [r.database_release_label for r in dependent_releases]

# Configuration and constants
api_base_url = Sys.getenv("PEARL_API_URL", "http://localhost:8000")
max_retries = 3
timeout_seconds = 30
```

#### Function Parameters (snake_case, clear purpose)
```python
# Database operations
async def get_by_study_id(self, db: AsyncSession, *, study_id: int)
async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType)
async def update(self, db: AsyncSession, *, db_obj: ModelType, obj_in: UpdateSchemaType)

# API endpoints
async def create_study_endpoint(
    study_data: StudyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
)

# WebSocket functions
async def broadcast_entity_change(entity_data, event_type: str)
async def enhanced_broadcast_with_context(entity_data, event_type: str, context: Dict = None)

# Utility functions
def raise_dependency_conflict_exception(
    entity_type: str,
    entity_label: str, 
    dependent_count: int,
    dependent_type: str,
    dependent_names: List[str]
)
```

### R Variables

#### Data Variables (snake_case + descriptive suffix)
```r
# Reactive data (entity + _data for collections)
studies_data <- reactiveVal(NULL)
users_data <- reactiveVal(NULL)
package_items_data <- reactiveVal(NULL)
tracker_comments_data <- reactiveVal(NULL)

# Selected items (selected_ + entity)
selected_study <- reactiveVal(NULL)
selected_user <- reactiveVal(NULL)
selected_package_item <- reactiveVal(NULL)

# Form data (descriptive purpose)
create_form_data <- reactiveValues()
edit_form_data <- reactiveValues()
filter_criteria <- reactiveValues()

# State variables (purpose + _state or is_ prefix for boolean)
loading_state <- reactiveVal(FALSE)
validation_state <- reactiveVal(list())
is_modal_open <- reactiveVal(FALSE)
current_page <- reactiveVal(1)
```

#### Function Parameters (snake_case, clear types)
```r
# Module functions  
study_tree_ui <- function(id)
users_server <- function(id)

# Utility functions
create_standard_datatable <- function(
  data, 
  actions_column = TRUE,
  search_placeholder = "Search (regex supported):",
  page_length = 25,
  empty_message = "No data available"
)

show_operation_notification <- function(
  operation, 
  entity, 
  success = TRUE, 
  entity_name = NULL
)

# API functions
get_package_items_by_package <- function(package_id)
create_tracker_comment <- function(comment_data)
assign_primary_programmer <- function(tracker_id, programmer_id)
```

### JavaScript Variables

#### WebSocket Client (camelCase)
```javascript
// Class properties
class WebSocketClient {
    constructor() {
        this.ws = null;                     // Connection object
        this.reconnectAttempts = 0;         // Counter
        this.maxReconnectAttempts = 10;     // Configuration
        this.reconnectDelay = 1000;         // Time in milliseconds
        this.connectionState = 'disconnected'; // State tracking
    }
    
    // Method parameters (camelCase)
    handleMessage(messageEvent) {
        const eventData = JSON.parse(messageEvent.data);
        const eventType = eventData.type;
        const payloadData = eventData.data;
    }
    
    notifyShiny(eventType, eventData, moduleId) {
        const inputName = `${moduleId}-websocket_event`;
        const inputValue = {
            type: eventType,
            data: eventData,
            timestamp: Date.now()
        };
    }
}

// Instance variables (camelCase)
const wsClient = new WebSocketClient();
const reconnectTimer = null;
const eventQueue = [];

// DOM event handlers (camelCase)  
function bindActionButtons() {
    const editButtons = document.querySelectorAll('[data-action="edit"]');
    const deleteButtons = document.querySelectorAll('[data-action="delete"]');
}

function bindUserActionButtons() {
    // User-specific button bindings
}
```

---

## Documentation Naming

### File Names (PURPOSE.md or PURPOSE_DETAIL.md)
```
# Primary documentation (single word + .md)
README.md
CHANGELOG.md
LICENSE.md

# Comprehensive documentation (CATEGORY_REFERENCE.md)
API_REFERENCE.md
DATABASE_SCHEMA.md
WEBSOCKET_EVENTS.md
FRONTEND_MODULES.md
UTILITY_FUNCTIONS.md
NAMING_CONVENTIONS.md
CODE_PATTERNS.md

# Detailed documentation (PURPOSE_DETAIL.md)  
CASCADE_DELETE_MIGRATION_PLAN.md
FK_CASCADE_ANALYSIS.md
CRUD_OPERATION_ANALYSIS_SUMMARY.md

# Component documentation (CLAUDE.md in each directory)
backend/CLAUDE.md
admin-frontend/CLAUDE.md
scripts/CLAUDE.md

# Special documentation (descriptive names)
MODEL_VALIDATOR_README.md
REFACTOR.md
PRD.md (Product Requirements Document)
```

### Section Headers (Title Case with Consistent Hierarchy)
```markdown
# Main Title

## Major Section

### Subsection  

#### Detail Section

##### Implementation Notes
```

### Code Examples (Clear context labels)
```markdown
#### Usage Example
```python
# Code example with clear context
```

#### Configuration Pattern
```r
# R configuration example
```

#### API Request Format
```json
{
  "example": "json data"
}
```

#### Expected Response
```json
{
  "response": "example"
}
```

#### Database Schema
```sql
-- SQL schema example
```
```

---

## Environment Variables

### Standard Pattern (PEARL_PURPOSE_DETAIL)
```bash
# API Configuration (PEARL_API_*)
PEARL_API_URL=http://localhost:8000
PEARL_WEBSOCKET_URL=ws://localhost:8000

# Database Configuration (PEARL_DB_*)
PEARL_DB_HOST=localhost
PEARL_DB_PORT=5432
PEARL_DB_NAME=pearl
PEARL_DB_USER=pearl_user
PEARL_DB_PASSWORD=pearl_password

# API Endpoints (PEARL_ENTITY_ENDPOINT)
PEARL_STUDIES_ENDPOINT=/api/v1/studies
PEARL_USERS_ENDPOINT=/api/v1/users
PEARL_PACKAGES_ENDPOINT=/api/v1/packages
PEARL_PACKAGE_ITEMS_ENDPOINT=/api/v1/package-items
PEARL_TRACKERS_ENDPOINT=/api/v1/reporting-effort-tracker
PEARL_COMMENTS_ENDPOINT=/api/v1/tracker-comments
PEARL_TEXT_ELEMENTS_ENDPOINT=/api/v1/text-elements

# Feature Flags (PEARL_ENABLE_*)
PEARL_ENABLE_WEBSOCKET=true
PEARL_ENABLE_AUDIT_LOGGING=true
PEARL_DEBUG_MODE=false
PEARL_ENABLE_CASCADE_MIGRATION=false

# System Configuration (PEARL_SYSTEM_*)
PEARL_SYSTEM_NAME=PEARL Research Data Management
PEARL_VERSION=2.0.0
PEARL_ENVIRONMENT=development
```

---

## Validation and Enforcement

### Automated Checks

#### Pre-commit Hooks
- **Python**: Black (formatting), isort (imports), flake8 (style), mypy (types)
- **R**: styler package for code formatting
- **JavaScript**: ESLint for consistent naming

#### Code Review Checklist
- [ ] File names follow established patterns
- [ ] Function names are descriptive and follow case conventions  
- [ ] Variable names provide clear context
- [ ] Database schema follows snake_case conventions
- [ ] API endpoints use kebab-case
- [ ] WebSocket events follow entity_action pattern
- [ ] Documentation follows established structure

#### Naming Validation Tools
```python
# Example validation script
def validate_naming_conventions():
    """Validate project follows naming conventions."""
    
    # Check Python files
    python_files = glob.glob("**/*.py", recursive=True)
    for file in python_files:
        if not file.islower() or " " in file:
            print(f"❌ Python file naming issue: {file}")
    
    # Check R files  
    r_files = glob.glob("**/*.R", recursive=True)
    for file in r_files:
        if not (file.endswith("_ui.R") or file.endswith("_server.R") or file.endswith(".R")):
            print(f"⚠️  R file naming check: {file}")
    
    # Check API endpoints
    # Check database table names
    # Check WebSocket event types
```

### Documentation Updates

When adding new components, ensure naming follows these conventions:
1. **File Creation**: Follow directory-specific patterns
2. **Function Names**: Use descriptive verbs and clear context
3. **Variable Names**: Include purpose and type hints in names
4. **Database Changes**: Follow snake_case with descriptive names
5. **API Changes**: Use RESTful patterns with kebab-case
6. **Documentation**: Update relevant documentation files

---

## Related Documentation

- [CODE_PATTERNS.md](CODE_PATTERNS.md) - Common code patterns that use these naming conventions
- [API_REFERENCE.md](API_REFERENCE.md) - API endpoints following these naming standards
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Database schema with naming conventions applied
- [FRONTEND_MODULES.md](FRONTEND_MODULES.md) - Frontend modules following R naming conventions