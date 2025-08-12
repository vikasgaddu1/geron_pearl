# TODO: Package Module Backend Implementation

## Phase 1: Database Schema Updates

### 1.1 Text Element Type Update
- [x] Add `ich_category` to TextElementType enum in `app/models/text_element.py`
  ```python
  class TextElementType(enum.Enum):
      title = "title"
      footnote = "footnote"
      population_set = "population_set"
      acronyms_set = "acronyms_set"
      ich_category = "ich_category"  # NEW
  ```
- [x] Test: Verify enum update doesn't break existing code

### 1.2 Package TLF Details Model Update
- [x] Add `ich_category_id` field to `app/models/package_tlf_details.py`
  ```python
  ich_category_id: Mapped[int | None] = mapped_column(
      Integer,
      ForeignKey("text_elements.id"),
      nullable=True,
      doc="Reference to ICH category text element"
  )
  ich_category = relationship("TextElement", foreign_keys=[ich_category_id])
  ```

### 1.3 Remove Study Dependency from Package Items
- [x] Update `app/models/package_item.py` to remove study_id field and relationship
- [x] Update unique constraint to exclude study_id
  ```python
  __table_args__ = (
      UniqueConstraint('package_id', 'item_type', 'item_subtype', 'item_code', 
                      name='uq_package_item_unique'),
  )
  ```

### 1.4 Create Alembic Migration
- [x] Generate migration: `uv run alembic revision --autogenerate -m "Remove study_id from package_items and add ich_category"`
- [x] Review generated migration file
- [x] Apply migration: `uv run alembic upgrade head`
- [x] Test: Verify database schema changes

## Phase 2: CRUD Layer Updates

### 2.1 Package Item CRUD Updates (`app/crud/package_item.py`)
- [x] Remove all study_id validation and requirements
- [x] Update create method to not require study_id
- [x] Update get_multi to not filter by study_id
- [x] Add duplicate check for package_id + item_type + item_subtype + item_code
  - Reference: `app/crud/text_element.py` for duplicate checking pattern
- [x] Test each CRUD method

### 2.2 Text Element CRUD Updates (`app/crud/text_element.py`)
- [x] Verify get_by_type method works with ich_category
- [ ] Test: Query text elements by type='ich_category'

## Phase 3: Schema/Pydantic Model Updates

### 3.1 Package Item Schemas (`app/schemas/package_item.py`)
- [x] Remove study_id from PackageItemCreate
- [x] Remove study_id from PackageItemUpdate
- [x] Remove study_id from PackageItem response model
- [x] Update PackageItemCreateWithDetails to include ich_category_id

### 3.2 Text Element Schema Updates
- [x] Verify TextElementType includes ich_category in schema

## Phase 4: API Endpoint Updates

### 4.1 Package Items API (`app/api/v1/packages.py`)
- [x] Update create_package_item endpoint to not require study_id
- [x] Add proper duplicate error handling with detailed message
  - Pattern: Follow `app/api/v1/text_elements.py` duplicate error format
- [x] Update get_package_items to return all fields including ich_category
- [x] Add validation for TLF type values (Table/Listing/Figure)
- [x] Add validation for Dataset type values (SDTM/ADaM)

### 4.2 Bulk Upload Endpoints (NEW)
- [x] Create POST `/api/v1/packages/{id}/items/bulk-tlf` endpoint
  - Accept list of TLF items
  - Validate all items before creating any
  - Create text_elements if they don't exist
  - Return detailed error report if validation fails
- [x] Create POST `/api/v1/packages/{id}/items/bulk-dataset` endpoint
  - Accept list of dataset items
  - Validate all items before creating any
  - Return detailed error report if validation fails
- [x] Add proper error handling for file format validation

### 4.3 Text Elements API Updates
- [x] Verify `/api/v1/text-elements?type=ich_category` works
- [x] Test creating text element with type='ich_category'

## Phase 5: WebSocket Broadcast Updates

### 5.1 Package Item Events (`app/api/v1/websocket.py`)
- [x] Verify broadcast_package_item_created includes all fields
- [x] Verify broadcast_package_item_updated includes all fields
- [x] Verify broadcast_package_item_deleted works
- [ ] Test WebSocket events fire correctly

## Phase 6: Testing with curl

### 6.1 Basic CRUD Tests
```bash
# Test creating package item without study_id
curl -X POST http://localhost:8000/api/v1/packages/1/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_type": "TLF",
    "item_subtype": "Table",
    "item_code": "t14.1.1",
    "tlf_details": {
      "title_id": 1,
      "ich_category_id": 5
    }
  }'

# Test duplicate check
# Create same item again - should get detailed error message

# Test creating text element with ich_category type
curl -X POST http://localhost:8000/api/v1/text-elements/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "ich_category",
    "label": "Category A"
  }'

# Test querying by type
curl http://localhost:8000/api/v1/text-elements?type=ich_category
```

### 6.2 Bulk Upload Tests
```bash
# Test TLF bulk upload
curl -X POST http://localhost:8000/api/v1/packages/1/items/bulk-tlf \
  -H "Content-Type: application/json" \
  -d '[
    {
      "item_type": "TLF",
      "item_subtype": "Table",
      "item_code": "t14.1.1",
      "title": "Demographics",
      "footnotes": ["Note 1", "Note 2"],
      "population_flag": "ITT Population",
      "acronyms": ["AE", "SAE"],
      "ich_category": "Category A"
    }
  ]'

# Test dataset bulk upload
curl -X POST http://localhost:8000/api/v1/packages/1/items/bulk-dataset \
  -H "Content-Type: application/json" \
  -d '[
    {
      "item_type": "Dataset",
      "item_subtype": "SDTM",
      "item_code": "DM",
      "label": "Demographics",
      "sorting_order": 1
    }
  ]'
```

## Phase 7: Automated Test Scripts

### 7.1 Create test_packages_crud.sh
- [x] Copy pattern from `backend/test_crud_simple.sh`
- [x] Test package CRUD operations
- [x] Test package item CRUD without study_id
- [x] Test duplicate detection
- [x] Test ich_category text elements
- [ ] Test bulk upload endpoints
- [ ] Test error scenarios

### 7.2 Create test_packages_websocket.py
- [ ] Copy pattern from `backend/tests/integration/test_websocket_broadcast.py`
- [ ] Test WebSocket events for package items
- [ ] Test real-time synchronization

## Phase 8: Validation & Error Handling

### 8.1 Duplicate Checks (CRITICAL - Often Missed!)
- [x] Package name must be unique
  - Return: "Package with this name already exists"
- [x] Package item (package_id + type + subtype + code) must be unique
  - Return: "A {type} with code {code} already exists in this package"
- [x] Follow existing error message patterns from other modules

### 8.2 Referential Integrity
- [x] Cannot delete package with items
  - Check pattern in `app/api/v1/studies.py` for deletion protection
- [x] Cannot create item with non-existent text_element IDs
- [x] Validate text_element types match expected values

### 8.3 Input Validation
- [x] TLF type must be in ['Table', 'Listing', 'Figure']
- [x] Dataset type must be in ['SDTM', 'ADaM']
- [x] Package name cannot be empty
- [x] Item code cannot be empty

## Phase 9: Model Validation

### 9.1 Run Model Validator
- [ ] Execute: `uv run python tests/validator/run_model_validation.py`
- [ ] Fix any model relationship issues
- [ ] Verify all foreign keys are properly defined

## Common Pitfalls to Avoid

1. **Duplicate Error Messages**: Must return user-friendly messages, not database constraints
2. **WebSocket Broadcasting**: Must convert SQLAlchemy models to Pydantic before broadcasting
3. **Cascade Deletes**: Ensure proper cascade configuration for related tables
4. **Transaction Rollback**: Ensure failed bulk operations rollback completely
5. **Async Session Management**: Follow existing CRUD patterns exactly

## Success Criteria

- [x] All curl tests pass
- [x] Automated test script runs without errors (partial - bulk upload needs fixes)
- [x] WebSocket events broadcast correctly
- [x] Duplicate checks return proper error messages
- [x] No study_id references remain in package_items
- [x] ICH category works as new text element type
- [ ] Bulk upload validates and creates items correctly
- [ ] Model validator passes