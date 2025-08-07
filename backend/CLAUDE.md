# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **📖 For comprehensive project documentation, setup instructions, API endpoints, and deployment guides, see [README.md](README.md)**

## Project Overview

PEARL Backend is a FastAPI application with async PostgreSQL CRUD operations and **real-time WebSocket updates**. This is a **production-like development environment** with specific constraints around testing and database management.

**Key Features**: FastAPI + async PostgreSQL + WebSocket broadcasting + UV package management  
**Critical Constraint**: SQLAlchemy async session conflicts prevent reliable batch test execution

**🔄 Recent Changes (2025-07-31)**:
- Reverted from key-value pairs system back to expanded text elements
- Updated TextElementType enum to support 4 categories: `title`, `footnote`, `population_set`, `acronyms_set`
- Removed all acronym-related entities and key-value-pair tables
- Simplified to single-table text element system for easier schema evolution

### Architecture Layers & Clean Code Patterns

**CRITICAL**: This project follows strict Clean Architecture patterns:
- **API Layer** (`app/api/v1/`): FastAPI endpoints with dependency injection
- **CRUD Layer** (`app/crud/`): Business logic and database operations
- **Models Layer** (`app/models/`): SQLAlchemy ORM models with relationships
- **Schemas Layer** (`app/schemas/`): Pydantic models for validation and serialization
- **DB Layer** (`app/db/`): Database configuration and session management

**Never bypass CRUD layer** - All database operations must go through CRUD classes

### CRUD Class Patterns

**Standard CRUD Interface**: All CRUD classes follow consistent patterns:
```python
class StudyCRUD:
    async def create(self, db: AsyncSession, *, obj_in: CreateSchema) -> Model
    async def get(self, db: AsyncSession, *, id: int) -> Optional[Model]
    async def get_multi(self, db: AsyncSession, *, skip: int, limit: int) -> List[Model]
    async def update(self, db: AsyncSession, *, db_obj: Model, obj_in: UpdateSchema) -> Model
    async def delete(self, db: AsyncSession, *, id: int) -> Optional[Model]
    async def get_by_label(self, db: AsyncSession, *, label: str) -> Optional[Model]  # Domain-specific
```

**Dependency Relationships**: Implement query methods for referential integrity:
```python
# In dependent entity CRUD (e.g., DatabaseReleaseCRUD)
async def get_by_study_id(self, db: AsyncSession, *, study_id: int) -> List[DatabaseRelease]
```

### Package Management with UV

This project uses **[UV](https://docs.astral.sh/uv/)** as the modern Python package manager for fast, deterministic builds:

**Benefits**:
- ⚡ Faster dependency resolution than pip
- 🔒 Deterministic builds with `uv.lock`
- 🐍 Python version management
- 📦 Unified toolchain

**Key Commands**:
```bash
# Use uv for all Python operations
uv run python run.py           # Start development server
uv run alembic upgrade head    # Database migrations
uv run pytest tests/          # Run tests
uv pip install -r requirements.txt  # Install dependencies
```

> **🏗️ See [README.md - Features & Project Structure](README.md#features) for complete technology stack and architecture details**

## Critical Testing Constraints

### Database Session Management Issues

**⚠️ CRITICAL LIMITATION**: This project has SQLAlchemy async session management conflicts that prevent reliable batch test execution. This is NOT a bug but an architectural constraint of running tests against real PostgreSQL without transaction isolation.

**Symptoms**:
```
sqlalchemy.exc.InterfaceError: cannot perform operation: another operation is in progress
```

**Impact**:
- ✅ Individual tests work perfectly
- ❌ Batch test execution frequently fails
- ✅ CRUD functionality is fully working
- ✅ API endpoints work correctly
- ⚠️ Test coverage reports may show failures despite working code

### Test Development Guidelines

1. **Read `tests/README.md` FIRST** - Contains essential constraints and patterns
2. **Prefer individual test files** - One test per file for database operations
3. **Favor non-database tests** - Validation, schema, and logic tests work reliably
4. **Test individually** - Always test with `pytest single_test.py` before batch
5. **Expect batch failures** - This is normal and documented behavior

### Safe Test Patterns

```python
# ✅ SAFE: Non-database validation
async def test_input_validation(self, client):
    response = await client.post("/api/v1/studies/", json={"study_label": ""})
    assert response.status_code == 422

# ✅ SAFE: Single database read (non-existent)
async def test_get_not_found(self, db_session):
    result = await study.get(db_session, id=999999)
    assert result is None

# ❌ UNSAFE: Multiple database operations
async def test_create_and_retrieve(self, db_session):
    created = await study.create(db_session, data)  # Conflicts with other tests
    retrieved = await study.get(db_session, created.id)  # May fail in batch
```

### Unsafe Test Patterns (Avoid)

- Tests using `sample_study` or `multiple_studies` fixtures
- Multiple tests in same file accessing database
- Tests that create database records
- Concurrent database operations
- Tests requiring database state setup

## Development Commands

> **🚀 See [README.md - Setup & Development](README.md#setup) for complete installation, database setup, and development workflow**

### Quick Reference
```bash
# Install dependencies
uv pip install -r requirements.txt

# Initialize database
uv run python -m app.db.init_db

# Start development server
uv run python run.py
# Alternative: uv run uvicorn app.main:app --reload

# Access at: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Code Quality & Formatting
```bash
# Format code
make format             # Black + isort formatting
uv run black app tests  # Format with black
uv run isort app tests  # Sort imports

# Lint and type check
make lint               # flake8 + mypy
make typecheck          # mypy only
uv run mypy app        # Type checking
uv run flake8 app tests # Linting

# Clean up generated files
make clean              # Remove coverage, cache files
```

### Database Management
```bash
# Alembic migrations
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic current
uv run alembic history

# Make commands
make migrate            # Apply migrations (alembic upgrade head)
make db-reset          # Reset database with Docker
```

### Testing (Individual Files Only)
```bash
# Functional testing (recommended - must have server running)
./test_crud_simple.sh

# Individual pytest (works reliably)
pytest tests/specific_test.py -v

# Model validation (CRITICAL after model changes)
uv run python tests/validator/run_model_validation.py

# WebSocket integration test
uv run python tests/integration/test_websocket_broadcast.py

# Make commands (comprehensive testing)
make test-fast          # Fast tests excluding slow performance tests
make test-unit          # Unit tests only
make test-integration   # Integration tests only  
make test-security      # Security tests only
make test-coverage      # Tests with coverage report
```

## Key Architecture Notes

> **🏛️ See [README.md - Project Structure](README.md#project-structure) for complete directory structure and component descriptions**

### Critical Architecture Points
- **Real PostgreSQL**: No test isolation (source of async session conflicts)
- **WebSocket Broadcasting**: All CRUD operations broadcast real-time events via ConnectionManager
- **Clean Architecture**: API → CRUD → Models with clear separation (never bypass CRUD layer)
- **Async Session Management**: Context managers with session conflict limitations
- **Application Lifespan**: Automatic database initialization on startup, graceful shutdown
- **Health Checks**: Built-in health endpoint (`/health`) with database connectivity testing
- **CORS Configuration**: Pre-configured for frontend integration at `http://localhost:3838`
- **Global Exception Handling**: Comprehensive error handling with structured logging
- **Connection Management**: WebSocket ConnectionManager tracks active connections with cleanup

## Development Workflow

> **🛠️ See [README.md - Development](README.md#development) for complete development workflow, code formatting, and database migration instructions**

### Critical Development Points
1. **Individual Testing Only**: Use `./test_crud_simple.sh` or `pytest single_test.py -v`
2. **Model Validation**: Always run after model changes to catch SQLAlchemy/Pydantic misalignment
3. **WebSocket Broadcasting**: CRUD operations automatically broadcast events - test with multiple browser sessions
4. **Database Changes**: Use `alembic revision --autogenerate` for schema changes
5. **Referential Integrity**: Always implement deletion protection for related entities (see Deletion Patterns below)
6. **Clean Architecture**: Follow the API → CRUD → Models pattern, never bypass CRUD layer in endpoints
7. **Connection Manager Pattern**: WebSocket broadcasts use ConnectionManager for reliable message delivery
8. **Error Handling**: All endpoints use structured error responses with proper HTTP status codes

### FastAPI Model Validator Tool

**🎯 CRITICAL**: This project includes a specialized model validation tool that must be run after any model changes.

**Purpose**: Validates SQLAlchemy and Pydantic model alignment to prevent frontend integration issues

**Usage**:
```bash
# Run model validation (required after model changes)
uv run python tests/validator/run_model_validation.py

# Generate JSON report
uv run python tests/validator/fastapi_model_validator.py . --format json

# Save validation report
uv run python tests/validator/fastapi_model_validator.py . -o validation_report.txt
```

**When to Run**:
- After adding/modifying SQLAlchemy models (`app/models/*.py`)
- After updating Pydantic schemas (`app/schemas/*.py`)
- Before committing model-related changes
- When experiencing unexplained frontend/backend integration issues

**What it Validates**:
- Type compatibility between SQLAlchemy and Pydantic models
- Nullable/optional field consistency
- Field constraint alignment
- Missing field detection

### Deletion Patterns & Referential Integrity

> **🛡️ CRITICAL**: All entity deletions must check for dependent relationships to maintain data integrity**

#### Current Implementation Examples

**Study Deletion Protection** (`app/api/v1/studies.py:168-175`):
```python
# Check for associated database releases before deletion
associated_releases = await database_release.get_by_study_id(db, study_id=study_id)
if associated_releases:
    release_labels = [release.database_release_label for release in associated_releases]
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Cannot delete study '{db_study.study_label}': {len(associated_releases)} associated database release(s) exist: {', '.join(release_labels)}. Please delete all associated database releases first."
    )
```

**Database Release Deletion Protection** (`app/api/v1/database_releases.py:188-195`):
```python
# Check for associated reporting efforts before deletion
associated_efforts = await reporting_effort.get_by_database_release_id(db, database_release_id=database_release_id)
if associated_efforts:
    effort_labels = [effort.database_release_label for effort in associated_efforts]
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Cannot delete database release '{db_release.database_release_label}': {len(associated_efforts)} associated reporting effort(s) exist: {', '.join(effort_labels)}. Please delete all associated reporting efforts first."
    )
```

#### Required CRUD Methods for Deletion Protection

**For each dependent relationship, implement query methods**:
```python
# In dependent entity CRUD class
async def get_by_parent_id(self, db: AsyncSession, *, parent_id: int) -> List[DependentModel]:
    """Get all dependent entities for a specific parent (no pagination)."""
    result = await db.execute(
        select(DependentModel).where(DependentModel.parent_id == parent_id)
    )
    return list(result.scalars().all())
```

#### Deletion Protection Implementation Pattern

1. **Query for Dependents**: Use `get_by_parent_id()` method to find related entities
2. **Check Existence**: If dependents exist, block deletion with HTTP 400
3. **Descriptive Error**: List all dependent entities by name/label for user clarity  
4. **Clear Instructions**: Tell user exactly what needs to be deleted first
5. **Test Coverage**: Create comprehensive tests like `test_study_deletion_protection_fixed.sh`

#### Error Message Standards

**Format**: `"Cannot delete {entity} '{entity_label}': {count} associated {dependent_type}(s) exist: {list_of_names}. Please delete all associated {dependent_type}s first."`

**Example**: `"Cannot delete study 'Clinical Trial A': 3 associated database release(s) exist: jan_primary, feb_set, mar_final. Please delete all associated database releases first."`

#### Testing Deletion Protection

**Required Test Scenarios**:
1. ✅ Create parent entity
2. ✅ Create dependent entity(ies) 
3. ✅ Attempt parent deletion (should fail with HTTP 400)
4. ✅ Verify descriptive error message
5. ✅ Delete dependent entities first
6. ✅ Attempt parent deletion again (should succeed with HTTP 200)

**Test Script Pattern**: See `test_study_deletion_protection_fixed.sh` as reference implementation

#### Current Data Model & Relationships

**Three-tier hierarchical structure with cascading deletion protection**:

```
Study (1) ←→ (N) DatabaseRelease (1) ←→ (N) ReportingEffort
  ↑                                              ↓
  └────────────── (1) ←→ (N) ──────────────────┘
```

**Independent Entity**:
```
TextElement (standalone - four-category enum-based system)
```

**Deletion Order Requirements**:
1. **ReportingEffort** (leaf nodes - can be deleted freely)
2. **DatabaseRelease** (middle tier - blocked if ReportingEffort exists)  
3. **Study** (root - blocked if DatabaseRelease exists)
4. **TextElement** (independent - no relationships, can be deleted freely)

**Current Endpoints**:
- `/api/v1/studies/` - Study CRUD with DatabaseRelease deletion protection
- `/api/v1/database-releases/` - DatabaseRelease CRUD with ReportingEffort deletion protection
- `/api/v1/reporting-efforts/` - ReportingEffort CRUD (no dependent entities)
- `/api/v1/text-elements/` - TextElement CRUD with search functionality (title, footnote, population_set, acronyms_set)

**WebSocket Broadcasting**: All CRUD operations broadcast real-time events for each entity type

## Text Elements System (Current Implementation)

**📋 CURRENT FUNCTIONALITY**: Unified text element management system with four categories and real-time WebSocket updates.

### System Overview

**Purpose**: Flexible text element management for research data documentation with categorization
**Key Features**: 
- Text elements with four-category enum: `title`, `footnote`, `population_set`, `acronyms_set`
- Full-text search and filtering capabilities
- **Case-insensitive duplicate prevention**: Prevents duplicate text elements by comparing normalized content (ignoring spaces and case)
- Real-time WebSocket broadcasting for all CRUD operations
- Clean, unified data model with timestamp audit trails
- Designed for frequent database structure changes

### Database Schema

**Single entity with expanded enum support**:

**TextElement** (`text_elements` table)
- **ID**: Primary key, auto-increment
- **Type**: Enum constraint with four values:
  - `title` - Study titles and headings
  - `footnote` - Study methodology footnotes and references
  - `population_set` - Patient population definitions and criteria
  - `acronyms_set` - Collections of acronyms and abbreviations
- **Label**: Full-text searchable content
- **Created/Updated**: Timestamp audit trail with TimestampMixin

### API Endpoints (Complete CRUD)

**TextElement Management** (`/api/v1/text-elements/`):
- `POST /` - Create new text element with type validation
- `GET /` - List text elements with pagination
- `GET /search?q=term` - Search by label content across all types
- `GET /{id}` - Get specific text element
- `PUT /{id}` - Update text element with validation
- `DELETE /{id}` - Delete text element

### WebSocket Real-time Events

**Broadcast events for text element operations**:
- `text_element_created` - New text element added
- `text_element_updated` - Existing text element modified
- `text_element_deleted` - Text element removed

**JSON Serialization**: All WebSocket broadcasts use `model_dump(mode='json')` to properly serialize enums and datetime objects.

### CRUD Implementation Patterns

**Search Functionality**:
```python
# Text element search across all content with optional type filtering
async def search(self, db: AsyncSession, *, search_term: str, type_filter: Optional[TextElementType] = None) -> List[TextElement]

# Filter by specific type
async def get_by_type(self, db: AsyncSession, *, element_type: TextElementType) -> List[TextElement]
```

**Duplicate Prevention (Case-Insensitive)**:
```python
# Check for duplicate labels (implemented in TextElementCRUD)
async def check_duplicate_label(
    self, db: AsyncSession, *, label: str, type: TextElementType, exclude_id: Optional[int] = None
) -> Optional[TextElement]:
    """
    Check if a text element with the same normalized label already exists for the given type.
    Normalization: removes spaces and converts to uppercase for comparison.
    """
    
def _normalize_label(self, label: str) -> str:
    """Normalize label for duplicate checking: remove spaces and convert to uppercase."""
    return label.replace(" ", "").upper()
```

**Type Validation**:
```python
# Enum validation in Pydantic schemas
class TextElementCreate(BaseModel):
    type: TextElementType = Field(..., description="Type: title, footnote, population_set, or acronyms_set")
    label: str = Field(..., min_length=1, description="Text content")
```

### Frontend Integration

**R Shiny Module**: `admin-frontend/modules/tnfp_server.R` (may need updates)
- Interface for managing all four text element types
- Real-time WebSocket updates
- DataTable integration with search and filtering
- Type-based organization and display

**WebSocket Client**: Automatic refresh on entity changes via JavaScript WebSocket client

### Testing Patterns

**Individual Test Pattern**: Due to async session conflicts, test individually:
```bash
# Test text elements endpoint
pytest tests/test_text_elements_simple.py -v
```

**Validation Testing**: Run model validator after any schema changes:
```bash
uv run python tests/validator/run_model_validation.py
```

### Migration History & Database Evolution

**Recent Changes**:
1. **Migration c7087c378307**: Dropped `key_value_pairs` table and expanded `text_elements` enum
2. **Migration 7a7096093ce9**: Removed acronym-related tables (`acronyms`, `acronym_sets`, `acronym_set_members`)
3. **Current State**: Clean, unified text element system with four-category enum

**Future Migration Strategy**: 
- Database structure designed for frequent changes as requirements evolve
- Enum values can be easily added/removed via migrations
- Single-table approach minimizes complexity for schema changes

### Key Implementation Notes

1. **Enum Flexibility**: Four-value enum supports diverse content categorization while maintaining simplicity
2. **Migration-Friendly**: Single-table design makes structural changes easier to implement
3. **JSON Compatibility**: All WebSocket events use `mode='json'` for proper enum serialization
4. **Audit Trails**: TimestampMixin provides created_at/updated_at tracking
5. **Search Performance**: Database indexes on type and label fields for fast queries
6. **Type Safety**: Pydantic schemas ensure proper enum validation at API boundaries
7. **Duplicate Prevention**: Case-insensitive duplicate checking prevents entries like "Study Analysis Title" and "STUDY ANALYSIS TITLE" from coexisting within the same type

### Usage Examples

**Creating Text Elements**:
```bash
# Title
curl -X POST /api/v1/text-elements/ -d '{"type": "title", "label": "Study Analysis Title"}'

# Footnote
curl -X POST /api/v1/text-elements/ -d '{"type": "footnote", "label": "Study methodology footnote"}'

# Population Set
curl -X POST /api/v1/text-elements/ -d '{"type": "population_set", "label": "Adult patients aged 18-65"}'

# Acronyms Set
curl -X POST /api/v1/text-elements/ -d '{"type": "acronyms_set", "label": "Common medical abbreviations"}'
```

**Search and Filter**:
```bash
# Search across all types
curl "/api/v1/text-elements/search?q=medical"

# Get all text elements
curl "/api/v1/text-elements/"
```

**Duplicate Detection Examples**:
```bash
# These will be considered duplicates (ignoring spaces and case):
# "Study Analysis Title" vs "STUDY ANALYSIS TITLE" 
# "Adult patients aged 18-65" vs "ADULTPATIENTSAGED18-65"
# "NA = North America, EU = Europe" vs "na=northamerica,eu=europe"

# Example: First creation succeeds
curl -X POST /api/v1/text-elements/ -d '{"type": "title", "label": "Study Analysis Title"}'

# Second creation with similar content fails with HTTP 400
curl -X POST /api/v1/text-elements/ -d '{"type": "title", "label": "STUDY ANALYSIS TITLE"}'
# Returns: "A title with similar content already exists: 'Study Analysis Title'. Duplicate text elements are not allowed (comparison ignores spaces and case)."
```

## Packages System (Implemented August 2025)

**📦 CURRENT FUNCTIONALITY**: Comprehensive package management system for organizing TLFs (Tables, Listings, Figures) and Datasets with study associations.

### System Overview

**Purpose**: Organize and manage research outputs (TLFs and Datasets) into packages with full relationship tracking
**Key Features**:
- Polymorphic item system supporting TLF and Dataset types
- Detailed metadata storage for each item type
- Many-to-many relationships with text elements (footnotes, acronyms)
- Full CRUD operations with WebSocket real-time updates
- Deletion protection to maintain referential integrity

### Database Schema

**Six interconnected tables**:

1. **packages** - Main package table
   - ID: Primary key, auto-increment
   - package_name: VARCHAR(255), indexed
   - Created/Updated: Timestamp audit trail

2. **package_items** - Polymorphic items table
   - ID: Primary key
   - package_id: FK to packages
   - study_id: FK to studies
   - item_type: Enum (TLF, Dataset)
   - item_subtype: VARCHAR(50) - Table/Listing/Figure for TLF, SDTM/ADaM for Dataset
   - item_code: VARCHAR(255) - TLF ID or dataset name
   - UNIQUE: (package_id, item_type, item_subtype, item_code)

3. **package_tlf_details** - TLF-specific attributes
   - package_item_id: FK to package_items (unique)
   - title_id: FK to text_elements (optional)
   - population_flag_id: FK to text_elements (optional)

4. **package_dataset_details** - Dataset-specific attributes
   - package_item_id: FK to package_items (unique)
   - label: VARCHAR(255) - Dataset description
   - sorting_order: Integer for display ordering
   - acronyms: Text/JSON field for dataset-specific acronyms

5. **package_item_footnotes** - Junction table
   - package_item_id: FK to package_items (PK)
   - footnote_id: FK to text_elements (PK)
   - sequence_number: Integer for ordering

6. **package_item_acronyms** - Junction table
   - package_item_id: FK to package_items (PK)
   - acronym_id: FK to text_elements (PK)

### API Endpoints

**Package Management** (`/api/v1/packages/`):
- `POST /` - Create new package with duplicate name checking
- `GET /` - List packages with pagination
- `GET /{id}` - Get package with all items
- `PUT /{id}` - Update package with validation
- `DELETE /{id}` - Delete package (protected if items exist)

**Package Item Management**:
- `POST /packages/{id}/items` - Create item with all details
- `GET /packages/{id}/items` - Get all items for a package
- `GET /packages/items/{id}` - Get specific item with details
- `PUT /packages/items/{id}` - Update item
- `DELETE /packages/items/{id}` - Delete item and associations

### WebSocket Real-time Events

**Package events**:
- `package_created` - New package added
- `package_updated` - Package modified
- `package_deleted` - Package removed

**Package Item events**:
- `package_item_created` - New item added
- `package_item_updated` - Item modified
- `package_item_deleted` - Item removed

### CRUD Implementation Details

**Complex Creation Pattern** (`PackageItemCRUD.create_with_details`):
```python
# Creates item with all relationships in single transaction
# 1. Create main package_item
# 2. Create type-specific details (TLF or Dataset)
# 3. Create footnote associations
# 4. Create acronym associations
# Returns fully loaded item with all relationships
```

**Deletion Protection**:
- Packages cannot be deleted if package_items exist
- Error messages list first 5 dependent items
- Follow pattern from Study/DatabaseRelease deletion

### Testing

**Functional Test Script**: `test_packages_crud.sh`
- Complete CRUD operations for packages and items
- Tests both TLF and Dataset item types
- Validates deletion protection
- Verifies unique constraints
- Tests WebSocket broadcasting

### Key Implementation Notes

1. **Polymorphic Design**: Single package_items table with type discriminator
2. **Type Safety**: Pydantic validators ensure correct details for each item type
3. **Efficient Loading**: Uses SQLAlchemy selectinload for relationships
4. **Transaction Safety**: Complex operations use flush() for ID generation
5. **Enum Handling**: ItemType enum properly serialized in WebSocket events
6. **Migration**: Comprehensive migration with all indexes and constraints

## WebSocket Implementation Details

> **📡 Critical WebSocket patterns for Claude Code development**

### Data Type Conversion Issue
**Problem**: SQLAlchemy models don't have `model_dump()` method (Pydantic only)
**Solution**: Convert in broadcast functions: `Study.model_validate(sqlalchemy_model).model_dump()`

**Required in**:
- `app/api/v1/websocket.py` - WebSocket endpoint initial data + refresh responses
- `app/api/v1/websocket.py` - Broadcast functions (`broadcast_study_created`, etc.)

### WebSocket Endpoint Patterns
```python
# ✅ CORRECT: Manual session management for WebSocket
async with AsyncSessionLocal() as db:
    studies_data = await study.get_multi(db, skip=0, limit=100)
    studies_json = [Study.model_validate(item).model_dump(mode='json') for item in studies_data]

# ❌ INCORRECT: Dependency injection doesn't work reliably with WebSocket
@router.websocket("/studies")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
```

### ConnectionManager Pattern
```python
# WebSocket connection management with proper cleanup
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def cleanup_stale_connections(self):
        # Remove connections that are no longer in CONNECTED state
        for connection in self.active_connections.copy():
            if connection.client_state.name != "CONNECTED":
                self.active_connections.discard(connection)
```

### Broadcast Integration Pattern
```python
# In CRUD endpoints (app/api/v1/studies.py)
created_study = await study.create(db, obj_in=study_in)
await broadcast_study_created(created_study)  # SQLAlchemy model → conversion happens in broadcast function
```

### Testing WebSocket Functionality
```bash
# Test WebSocket broadcasting (from backend directory)
uv run python tests/integration/test_websocket_broadcast.py

# Manual test: Open multiple browser sessions and perform CRUD operations
# Server must be running: uv run python run.py
```

#### Recent Fixes (August 2025)

**WebSocket Enum Serialization Fixed**:
- **Issue**: `TextElementType` enum causing WebSocket broadcast failures: "Type <enum 'TextElementType'> not serializable"
- **Root Cause**: `sqlalchemy_to_dict()` and `json_serializer()` functions in `app/utils.py` didn't handle enum types
- **Solution**: Enhanced serialization functions to convert enums to their string values:
  ```python
  # Enhanced json_serializer()
  elif isinstance(obj, Enum):
      return obj.value
  
  # Enhanced sqlalchemy_to_dict()
  elif isinstance(value, Enum):
      d[column.name] = value.value
  ```
- **Impact**: Fixed database rollbacks and WebSocket broadcast errors for all text element operations
- **Status**: ✅ All WebSocket broadcasts now work correctly with enum types

## For Test Architect Agents

**MANDATORY**: Before creating ANY tests, read:
1. `/mnt/c/python/PEARL/backend/tests/README.md` - Complete testing constraints
2. This `CLAUDE.md` file - Project-specific limitations

**Key Constraint**: This project cannot support traditional test isolation patterns. Design tests accordingly or they will fail in batch execution due to async session conflicts.

**Success Metric**: Individual test reliability, not batch test pass rates.

## Current Project State & Debug Tools

### Available Debug Scripts
- `debug_apis.py` - API endpoint testing and debugging
- `debug_crud.py` - CRUD operation testing
- `debug_text_element.py` - Text element functionality testing
- `test_new_api_endpoints.py` - New endpoint validation

### Functional Test Scripts  
- `test_crud_simple.sh` - Main CRUD functionality testing (recommended)
- `test_database_releases_crud.sh` - Database release specific testing
- `test_study_deletion_protection.sh` - Deletion protection testing
- `test_study_deletion_protection_fixed.sh` - Updated deletion protection tests

### Usage
```bash
# Primary functional testing (server must be running)
./test_crud_simple.sh

# Individual debug scripts
uv run python debug_apis.py
uv run python debug_crud.py
uv run python debug_text_element.py
```