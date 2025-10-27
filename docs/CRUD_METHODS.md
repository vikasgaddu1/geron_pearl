# CRUD Methods Documentation

**PEARL Full-Stack Research Data Management System**  
**Complete CRUD Operations Catalog with Method Signatures**

This document catalogs all CRUD operations available in each class with detailed method signatures, parameters, and usage patterns for the PEARL system post-Phase 2 implementation.

## Table of Contents

- [Base CRUD Class](#base-crud-class)
- [Study CRUD](#study-crud)
- [Database Release CRUD](#database-release-crud)
- [Reporting Effort CRUD](#reporting-effort-crud)
- [Reporting Effort Item CRUD](#reporting-effort-item-crud)
- [Reporting Effort Tracker CRUD](#reporting-effort-tracker-crud)
- [Package CRUD](#package-crud)
- [Package Item CRUD](#package-item-crud)
- [Text Element CRUD](#text-element-crud)
- [Tracker Comment CRUD](#tracker-comment-crud)
- [User CRUD](#user-crud)
- [Audit Log CRUD](#audit-log-crud)
- [Common Patterns](#common-patterns)
- [Error Handling](#error-handling)

---

## Base CRUD Class

**Location**: `backend/app/crud/base.py`

All CRUD classes inherit from `BaseCRUD` which provides standard operations for any SQLAlchemy model.

### Class Definition

```python
class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
```

### Base Methods

#### get(db, *, id: int) -> Optional[ModelType]
Get a single entity by ID.

**Parameters**:
- `db: AsyncSession` - Database session
- `id: int` - Entity primary key ID

**Returns**: Entity instance or `None` if not found

**Usage**:
```python
async def get_study_example():
    async with AsyncSessionLocal() as db:
        study = await study_crud.get(db, id=1)
        if not study:
            raise HTTPException(404, "Study not found")
        return study
```

---

#### get_multi(db, *, skip: int = 0, limit: int = 100) -> List[ModelType]
Get multiple entities with pagination.

**Parameters**:
- `db: AsyncSession` - Database session
- `skip: int = 0` - Number of records to skip
- `limit: int = 100` - Maximum records to return

**Returns**: List of entity instances

**Usage**:
```python
async def list_studies_example():
    async with AsyncSessionLocal() as db:
        studies = await study_crud.get_multi(db, skip=0, limit=50)
        return studies
```

---

#### create(db, *, obj_in: CreateSchemaType) -> ModelType
Create a new entity.

**Parameters**:
- `db: AsyncSession` - Database session
- `obj_in: CreateSchemaType` - Pydantic create schema instance

**Returns**: Created entity instance

**Usage**:
```python
async def create_study_example():
    study_data = StudyCreate(study_label="ONCOLOGY-2024-001")
    async with AsyncSessionLocal() as db:
        study = await study_crud.create(db, obj_in=study_data)
        return study
```

---

#### update(db, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType
Update an existing entity.

**Parameters**:
- `db: AsyncSession` - Database session
- `db_obj: ModelType` - Existing entity instance to update
- `obj_in: UpdateSchemaType | Dict` - Update data

**Returns**: Updated entity instance

**Usage**:
```python
async def update_study_example():
    study_update = StudyUpdate(study_label="ONCOLOGY-2024-001-UPDATED")
    async with AsyncSessionLocal() as db:
        existing_study = await study_crud.get(db, id=1)
        updated_study = await study_crud.update(db, db_obj=existing_study, obj_in=study_update)
        return updated_study
```

---

#### delete(db, *, id: int) -> Optional[ModelType]
Delete an entity by ID.

**Parameters**:
- `db: AsyncSession` - Database session
- `id: int` - Entity ID to delete

**Returns**: Deleted entity instance or `None` if not found

**Usage**:
```python
async def delete_study_example():
    async with AsyncSessionLocal() as db:
        deleted_study = await study_crud.delete(db, id=1)
        return deleted_study
```

---

#### count(db) -> int
Count total entities.

**Parameters**:
- `db: AsyncSession` - Database session

**Returns**: Total count of entities

**Usage**:
```python
async def count_studies_example():
    async with AsyncSessionLocal() as db:
        total_studies = await study_crud.count(db)
        return total_studies
```

---

## Study CRUD

**Location**: `backend/app/crud/study.py`  
**Model**: `app.models.study.Study`  
**Schemas**: `StudyCreate`, `StudyUpdate`, `Study`

### Class Definition

```python
class StudyCRUD(BaseCRUD[Study, StudyCreate, StudyUpdate]):
    pass

study = StudyCRUD(Study)
```

### Available Methods

**Inherited from BaseCRUD**:
- `get(db, *, id: int) -> Optional[Study]`
- `get_multi(db, *, skip: int = 0, limit: int = 100) -> List[Study]`
- `create(db, *, obj_in: StudyCreate) -> Study`
- `update(db, *, db_obj: Study, obj_in: Union[StudyUpdate, Dict[str, Any]]) -> Study`
- `delete(db, *, id: int) -> Optional[Study]`
- `count(db) -> int`

### Schema Examples

```python
# Create schema
study_create = StudyCreate(study_label="ONCOLOGY-2024-001")

# Update schema
study_update = StudyUpdate(study_label="ONCOLOGY-2024-001-UPDATED")

# Response schema
{
    "id": 1,
    "study_label": "ONCOLOGY-2024-001",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

---

## Database Release CRUD

**Location**: `backend/app/crud/database_release.py`  
**Model**: `app.models.database_release.DatabaseRelease`  
**Schemas**: `DatabaseReleaseCreate`, `DatabaseReleaseUpdate`, `DatabaseRelease`

### Class Definition

```python
class DatabaseReleaseCRUD(BaseCRUD[DatabaseRelease, DatabaseReleaseCreate, DatabaseReleaseUpdate]):
    async def get_by_study_id(self, db: AsyncSession, *, study_id: int) -> List[DatabaseRelease]:
        """Get all database releases for a specific study."""

database_release = DatabaseReleaseCRUD(DatabaseRelease)
```

### Custom Methods

#### get_by_study_id(db, *, study_id: int) -> List[DatabaseRelease]
Get all database releases for a specific study.

**Parameters**:
- `db: AsyncSession` - Database session
- `study_id: int` - Study ID to filter by

**Returns**: List of database releases for the study

**Usage**:
```python
async def get_releases_for_study():
    async with AsyncSessionLocal() as db:
        releases = await database_release.get_by_study_id(db, study_id=1)
        return releases
```

### Schema Examples

```python
# Create schema
release_create = DatabaseReleaseCreate(
    study_id=1,
    database_release_label="DB_LOCK_20241201",
    database_release_date="2024-12-01"
)

# Update schema
release_update = DatabaseReleaseUpdate(
    database_release_label="DB_LOCK_20241201_FINAL",
    database_release_date="2024-12-01"
)
```

---

## Reporting Effort CRUD

**Location**: `backend/app/crud/reporting_effort.py`  
**Model**: `app.models.reporting_effort.ReportingEffort`  
**Schemas**: `ReportingEffortCreate`, `ReportingEffortUpdate`, `ReportingEffort`

### Class Definition

```python
class ReportingEffortCRUD(BaseCRUD[ReportingEffort, ReportingEffortCreate, ReportingEffortUpdate]):
    async def get_by_database_release_id(self, db: AsyncSession, *, database_release_id: int) -> List[ReportingEffort]:
        """Get all reporting efforts for a specific database release."""

reporting_effort = ReportingEffortCRUD(ReportingEffort)
```

### Custom Methods

#### get_by_database_release_id(db, *, database_release_id: int) -> List[ReportingEffort]
Get all reporting efforts for a specific database release.

**Parameters**:
- `db: AsyncSession` - Database session  
- `database_release_id: int` - Database release ID to filter by

**Returns**: List of reporting efforts for the database release

**Usage**:
```python
async def get_efforts_for_release():
    async with AsyncSessionLocal() as db:
        efforts = await reporting_effort.get_by_database_release_id(db, database_release_id=1)
        return efforts
```

### Schema Examples

```python
# Create schema
effort_create = ReportingEffortCreate(
    database_release_id=1,
    database_release_label="INTERIM_ANALYSIS_20241201"
)

# Update schema
effort_update = ReportingEffortUpdate(
    database_release_label="INTERIM_ANALYSIS_20241201_FINAL"
)
```

---

## Reporting Effort Item CRUD

**Location**: `backend/app/crud/reporting_effort_item.py`  
**Model**: `app.models.reporting_effort_item.ReportingEffortItem`  
**Schemas**: `ReportingEffortItemCreate`, `ReportingEffortItemUpdate`, `ReportingEffortItem`

### Class Definition

```python
class ReportingEffortItemCRUD(BaseCRUD[ReportingEffortItem, ReportingEffortItemCreate, ReportingEffortItemUpdate]):
    async def get_by_reporting_effort_id(self, db: AsyncSession, *, reporting_effort_id: int) -> List[ReportingEffortItem]:
        """Get all items for a specific reporting effort."""
        
    async def get_by_item_code(self, db: AsyncSession, *, item_code: str) -> Optional[ReportingEffortItem]:
        """Get item by unique item code."""

reporting_effort_item = ReportingEffortItemCRUD(ReportingEffortItem)
```

### Custom Methods

#### get_by_reporting_effort_id(db, *, reporting_effort_id: int) -> List[ReportingEffortItem]
Get all items for a specific reporting effort.

**Parameters**:
- `db: AsyncSession` - Database session
- `reporting_effort_id: int` - Reporting effort ID to filter by

**Returns**: List of items for the reporting effort

---

#### get_by_item_code(db, *, item_code: str) -> Optional[ReportingEffortItem]
Get item by unique item code.

**Parameters**:
- `db: AsyncSession` - Database session
- `item_code: str` - Unique item code to search for

**Returns**: Item instance or `None` if not found

### Schema Examples

```python
# Create schema
item_create = ReportingEffortItemCreate(
    reporting_effort_id=1,
    item_code="T-14.1.1",
    item_description="Demographics and Baseline Characteristics",
    item_type="TLF",
    item_status="PENDING"
)

# Update schema
item_update = ReportingEffortItemUpdate(
    item_description="Demographics and Baseline Characteristics (Updated)",
    item_status="IN_PROGRESS"
)
```

---

## Reporting Effort Tracker CRUD

**Location**: `backend/app/crud/reporting_effort_item_tracker.py`  
**Model**: `app.models.reporting_effort_item_tracker.ReportingEffortItemTracker`  
**Schemas**: `ReportingEffortItemTrackerCreate`, `ReportingEffortItemTrackerUpdate`, `ReportingEffortItemTracker`

### Class Definition

```python
class ReportingEffortItemTrackerCRUD(BaseCRUD[ReportingEffortItemTracker, ReportingEffortItemTrackerCreate, ReportingEffortItemTrackerUpdate]):
    async def get_by_reporting_effort_item_id(self, db: AsyncSession, *, reporting_effort_item_id: int) -> List[ReportingEffortItemTracker]:
        """Get all trackers for a specific reporting effort item."""
        
    async def get_by_programmer_id(self, db: AsyncSession, *, programmer_id: int) -> List[ReportingEffortItemTracker]:
        """Get all trackers assigned to a specific programmer."""
        
    async def assign_primary_programmer(self, db: AsyncSession, *, tracker_id: int, programmer_id: int) -> ReportingEffortItemTracker:
        """Assign primary programmer to tracker."""
        
    async def assign_qc_programmer(self, db: AsyncSession, *, tracker_id: int, programmer_id: int) -> ReportingEffortItemTracker:
        """Assign QC programmer to tracker."""

reporting_effort_item_tracker = ReportingEffortItemTrackerCRUD(ReportingEffortItemTracker)
```

### Custom Methods

#### get_by_reporting_effort_item_id(db, *, reporting_effort_item_id: int) -> List[ReportingEffortItemTracker]
Get all trackers for a specific reporting effort item.

**Parameters**:
- `db: AsyncSession` - Database session
- `reporting_effort_item_id: int` - Reporting effort item ID

**Returns**: List of trackers for the item

---

#### get_by_programmer_id(db, *, programmer_id: int) -> List[ReportingEffortItemTracker]
Get all trackers assigned to a specific programmer.

**Parameters**:
- `db: AsyncSession` - Database session
- `programmer_id: int` - User ID of programmer

**Returns**: List of trackers assigned to the programmer

---

#### assign_primary_programmer(db, *, tracker_id: int, programmer_id: int) -> ReportingEffortItemTracker
Assign primary programmer to tracker.

**Parameters**:
- `db: AsyncSession` - Database session
- `tracker_id: int` - Tracker ID
- `programmer_id: int` - User ID to assign as primary programmer

**Returns**: Updated tracker instance

**Usage**:
```python
async def assign_primary():
    async with AsyncSessionLocal() as db:
        updated_tracker = await reporting_effort_item_tracker.assign_primary_programmer(
            db, tracker_id=1, programmer_id=2
        )
        return updated_tracker
```

---

#### assign_qc_programmer(db, *, tracker_id: int, programmer_id: int) -> ReportingEffortItemTracker
Assign QC programmer to tracker.

**Parameters**:
- `db: AsyncSession` - Database session
- `tracker_id: int` - Tracker ID
- `programmer_id: int` - User ID to assign as QC programmer

**Returns**: Updated tracker instance

### Schema Examples

```python
# Create schema
tracker_create = ReportingEffortItemTrackerCreate(
    reporting_effort_item_id=1,
    primary_programmer_id=1,
    qc_programmer_id=2,
    primary_status="IN_PROGRESS",
    qc_status="NOT_STARTED"
)

# Update schema
tracker_update = ReportingEffortItemTrackerUpdate(
    primary_status="COMPLETED",
    qc_status="IN_PROGRESS"
)
```

---

## Package CRUD

**Location**: `backend/app/crud/package.py`  
**Model**: `app.models.package.Package`  
**Schemas**: `PackageCreate`, `PackageUpdate`, `Package`

### Class Definition

```python
class PackageCRUD(BaseCRUD[Package, PackageCreate, PackageUpdate]):
    async def get_by_package_name(self, db: AsyncSession, *, package_name: str) -> Optional[Package]:
        """Get package by unique package name."""

package = PackageCRUD(Package)
```

### Custom Methods

#### get_by_package_name(db, *, package_name: str) -> Optional[Package]
Get package by unique package name.

**Parameters**:
- `db: AsyncSession` - Database session
- `package_name: str` - Package name to search for

**Returns**: Package instance or `None` if not found

### Schema Examples

```python
# Create schema
package_create = PackageCreate(
    package_name="Safety Analysis Package",
    study_indication="Oncology",
    therapeutic_area="Solid Tumors"
)

# Update schema
package_update = PackageUpdate(
    package_name="Safety Analysis Package - Updated",
    therapeutic_area="Hematologic Malignancies"
)
```

---

## Package Item CRUD

**Location**: `backend/app/crud/package_item.py`  
**Model**: `app.models.package_item.PackageItem`  
**Schemas**: `PackageItemCreate`, `PackageItemUpdate`, `PackageItem`

### Class Definition

```python
class PackageItemCRUD(BaseCRUD[PackageItem, PackageItemCreate, PackageItemUpdate]):
    async def get_by_package_id(self, db: AsyncSession, *, package_id: int) -> List[PackageItem]:
        """Get all items for a specific package."""
        
    async def get_by_item_code(self, db: AsyncSession, *, item_code: str) -> Optional[PackageItem]:
        """Get item by unique item code."""

package_item = PackageItemCRUD(PackageItem)
```

### Custom Methods

#### get_by_package_id(db, *, package_id: int) -> List[PackageItem]
Get all items for a specific package.

**Parameters**:
- `db: AsyncSession` - Database session
- `package_id: int` - Package ID to filter by

**Returns**: List of items for the package

---

#### get_by_item_code(db, *, item_code: str) -> Optional[PackageItem]
Get item by unique item code.

**Parameters**:
- `db: AsyncSession` - Database session
- `item_code: str` - Item code to search for

**Returns**: Item instance or `None` if not found

### Schema Examples

```python
# Create schema
item_create = PackageItemCreate(
    package_id=1,
    item_code="T-14.1.1",
    item_description="Demographics and Baseline Characteristics",
    item_type="TLF"
)

# Update schema
item_update = PackageItemUpdate(
    item_description="Demographics and Baseline Characteristics (Revised)",
    item_type="DATASET"
)
```

---

## Text Element CRUD

**Location**: `backend/app/crud/text_element.py`  
**Model**: `app.models.text_element.TextElement`  
**Schemas**: `TextElementCreate`, `TextElementUpdate`, `TextElement`

### Class Definition

```python
class TextElementCRUD(BaseCRUD[TextElement, TextElementCreate, TextElementUpdate]):
    async def get_by_type(self, db: AsyncSession, *, element_type: TextElementType) -> List[TextElement]:
        """Get all text elements of a specific type."""
        
    async def search_by_label(self, db: AsyncSession, *, search_term: str, limit: int = 50) -> List[TextElement]:
        """Search text elements by label."""

text_element = TextElementCRUD(TextElement)
```

### Custom Methods

#### get_by_type(db, *, element_type: TextElementType) -> List[TextElement]
Get all text elements of a specific type.

**Parameters**:
- `db: AsyncSession` - Database session
- `element_type: TextElementType` - Type to filter by (TITLE, FOOTNOTE, POPULATION_SET, ACRONYMS_SET)

**Returns**: List of text elements of the specified type

---

#### search_by_label(db, *, search_term: str, limit: int = 50) -> List[TextElement]
Search text elements by label.

**Parameters**:
- `db: AsyncSession` - Database session
- `search_term: str` - Search term to match against labels
- `limit: int = 50` - Maximum results to return

**Returns**: List of matching text elements

### Schema Examples

```python
# Create schema
element_create = TextElementCreate(
    type="TITLE",
    label="Demographics Table",
    content="Table 14.1.1: Demographics and Baseline Characteristics"
)

# Update schema
element_update = TextElementUpdate(
    label="Demographics Table (Updated)",
    content="Table 14.1.1: Demographics and Baseline Characteristics (Revised)"
)
```

---

## Tracker Comment CRUD

**Location**: `backend/app/crud/tracker_comment.py`  
**Model**: `app.models.tracker_comment.TrackerComment`  
**Schemas**: `TrackerCommentCreate`, `TrackerCommentUpdate`, `TrackerComment`

### Class Definition

```python
class TrackerCommentCRUD(BaseCRUD[TrackerComment, TrackerCommentCreate, TrackerCommentUpdate]):
    async def get_by_tracker_id(self, db: AsyncSession, *, tracker_id: int) -> List[TrackerCommentWithUserInfo]:
        """Get all comments for a specific tracker with user information."""
        
    async def create_comment(self, db: AsyncSession, *, comment_in: TrackerCommentCreate) -> TrackerCommentWithUserInfo:
        """Create a new comment with user info response."""
        
    async def create_reply(self, db: AsyncSession, *, parent_comment_id: int, comment_in: TrackerCommentCreate) -> TrackerCommentWithUserInfo:
        """Create a reply to an existing comment."""
        
    async def resolve_comment(self, db: AsyncSession, *, comment_id: int) -> TrackerComment:
        """Mark a comment as resolved."""
        
    async def get_unresolved_count_by_tracker(self, db: AsyncSession, *, tracker_id: int) -> int:
        """Get count of unresolved comments for a tracker."""

tracker_comment = TrackerCommentCRUD(TrackerComment)
```

### Custom Methods

#### get_by_tracker_id(db, *, tracker_id: int) -> List[TrackerCommentWithUserInfo]
Get all comments for a specific tracker with user information.

**Parameters**:
- `db: AsyncSession` - Database session
- `tracker_id: int` - Tracker ID to filter by

**Returns**: List of comments with user info (username, etc.)

---

#### create_comment(db, *, comment_in: TrackerCommentCreate) -> TrackerCommentWithUserInfo
Create a new comment with user info response.

**Parameters**:
- `db: AsyncSession` - Database session
- `comment_in: TrackerCommentCreate` - Comment creation data

**Returns**: Created comment with user information

---

#### create_reply(db, *, parent_comment_id: int, comment_in: TrackerCommentCreate) -> TrackerCommentWithUserInfo
Create a reply to an existing comment.

**Parameters**:
- `db: AsyncSession` - Database session
- `parent_comment_id: int` - Parent comment ID
- `comment_in: TrackerCommentCreate` - Reply data

**Returns**: Created reply with user information

---

#### resolve_comment(db, *, comment_id: int) -> TrackerComment
Mark a comment as resolved.

**Parameters**:
- `db: AsyncSession` - Database session
- `comment_id: int` - Comment ID to resolve

**Returns**: Updated comment instance

---

#### get_unresolved_count_by_tracker(db, *, tracker_id: int) -> int
Get count of unresolved comments for a tracker.

**Parameters**:
- `db: AsyncSession` - Database session
- `tracker_id: int` - Tracker ID

**Returns**: Count of unresolved comments

### Schema Examples

```python
# Create schema
comment_create = TrackerCommentCreate(
    tracker_id=1,
    user_id=1,
    comment_text="Need clarification on analysis population",
    comment_type="QUESTION"
)

# Update schema  
comment_update = TrackerCommentUpdate(
    comment_text="Updated: Need clarification on analysis population",
    is_resolved=True
)

# Response schema (with user info)
{
    "id": 1,
    "tracker_id": 1,
    "user_id": 1,
    "username": "johndoe",
    "comment_text": "Need clarification on analysis population",
    "comment_type": "QUESTION",
    "is_resolved": false,
    "parent_comment_id": null,
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

---

## User CRUD

**Location**: `backend/app/crud/crud_user.py`  
**Model**: `app.models.user.User`  
**Schemas**: `UserCreate`, `UserUpdate`, `User`

### Class Definition

```python
class UserCRUD(BaseCRUD[User, UserCreate, UserUpdate]):
    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """Get user by unique username."""
        
    async def get_by_role(self, db: AsyncSession, *, role: str) -> List[User]:
        """Get all users with a specific role."""

user = UserCRUD(User)
```

### Custom Methods

#### get_by_username(db, *, username: str) -> Optional[User]
Get user by unique username.

**Parameters**:
- `db: AsyncSession` - Database session
- `username: str` - Username to search for

**Returns**: User instance or `None` if not found

---

#### get_by_role(db, *, role: str) -> List[User]
Get all users with a specific role.

**Parameters**:
- `db: AsyncSession` - Database session
- `role: str` - Role to filter by (ADMIN, ANALYST, VIEWER)

**Returns**: List of users with the specified role

### Schema Examples

```python
# Create schema
user_create = UserCreate(
    username="johndoe",
    role="ANALYST",
    department="Clinical Research"
)

# Update schema
user_update = UserUpdate(
    username="johnsmith",
    role="ADMIN",
    department="Data Management"
)

# Response schema
{
    "id": 1,
    "username": "johndoe",
    "role": "ANALYST", 
    "department": "Clinical Research",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
}
```

---

## Audit Log CRUD

**Location**: `backend/app/crud/audit_log.py`  
**Model**: `app.models.audit_log.AuditLog`  
**Schemas**: `AuditLogCreate`, `AuditLog`

### Class Definition

```python
class AuditLogCRUD(BaseCRUD[AuditLog, AuditLogCreate, dict]):
    async def get_by_entity_type(self, db: AsyncSession, *, entity_type: str, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a specific entity type."""
        
    async def get_by_user_id(self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a specific user."""
        
    async def get_by_action(self, db: AsyncSession, *, action: str, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a specific action type."""

audit_log = AuditLogCRUD(AuditLog)
```

### Custom Methods

#### get_by_entity_type(db, *, entity_type: str, skip: int = 0, limit: int = 100) -> List[AuditLog]
Get audit logs for a specific entity type.

**Parameters**:
- `db: AsyncSession` - Database session
- `entity_type: str` - Entity type to filter by
- `skip: int = 0` - Records to skip  
- `limit: int = 100` - Maximum records

**Returns**: List of audit logs for the entity type

---

#### get_by_user_id(db, *, user_id: int, skip: int = 0, limit: int = 100) -> List[AuditLog]
Get audit logs for a specific user.

**Parameters**:
- `db: AsyncSession` - Database session
- `user_id: int` - User ID to filter by
- `skip: int = 0` - Records to skip
- `limit: int = 100` - Maximum records  

**Returns**: List of audit logs for the user

---

#### get_by_action(db, *, action: str, skip: int = 0, limit: int = 100) -> List[AuditLog]
Get audit logs for a specific action type.

**Parameters**:
- `db: AsyncSession` - Database session  
- `action: str` - Action type to filter by (CREATE, UPDATE, DELETE)
- `skip: int = 0` - Records to skip
- `limit: int = 100` - Maximum records

**Returns**: List of audit logs for the action type

### Schema Examples

```python
# Create schema
audit_create = AuditLogCreate(
    entity_type="study",
    entity_id=1,
    action="CREATE",
    user_id=1,
    changes={"study_label": "ONCOLOGY-2024-001"}
)

# Response schema
{
    "id": 1,
    "entity_type": "study",
    "entity_id": 1,
    "action": "CREATE",
    "user_id": 1,
    "changes": {"study_label": "ONCOLOGY-2024-001"},
    "timestamp": "2024-12-01T10:00:00Z"
}
```

---

## Common Patterns

### Standard CRUD Usage Pattern

```python
from app.crud import study, database_release, package
from app.db.session import AsyncSessionLocal

async def example_crud_operations():
    async with AsyncSessionLocal() as db:
        # Create
        study_data = StudyCreate(study_label="EXAMPLE-2024-001")
        new_study = await study.create(db, obj_in=study_data)
        
        # Read
        retrieved_study = await study.get(db, id=new_study.id)
        all_studies = await study.get_multi(db, skip=0, limit=10)
        
        # Update
        update_data = StudyUpdate(study_label="EXAMPLE-2024-001-UPDATED")
        updated_study = await study.update(db, db_obj=retrieved_study, obj_in=update_data)
        
        # Delete
        deleted_study = await study.delete(db, id=updated_study.id)
        
        return {
            "created": new_study,
            "updated": updated_study,
            "deleted": deleted_study
        }
```

### Relationship Queries Pattern

```python
async def example_relationship_queries():
    async with AsyncSessionLocal() as db:
        # Get study with all its database releases
        study_instance = await study.get(db, id=1)
        releases = await database_release.get_by_study_id(db, study_id=study_instance.id)
        
        # Get database release with all its reporting efforts
        release_instance = releases[0] if releases else None
        if release_instance:
            efforts = await reporting_effort.get_by_database_release_id(
                db, database_release_id=release_instance.id
            )
        
        return {
            "study": study_instance,
            "releases": releases,
            "efforts": efforts if release_instance else []
        }
```

### Search and Filter Pattern

```python
async def example_search_operations():
    async with AsyncSessionLocal() as db:
        # Search by specific criteria
        user_by_username = await user.get_by_username(db, username="johndoe")
        admin_users = await user.get_by_role(db, role="ADMIN")
        
        # Search text elements
        title_elements = await text_element.get_by_type(db, element_type="TITLE")
        search_results = await text_element.search_by_label(db, search_term="Demographics")
        
        # Get tracker comments
        tracker_comments = await tracker_comment.get_by_tracker_id(db, tracker_id=1)
        unresolved_count = await tracker_comment.get_unresolved_count_by_tracker(db, tracker_id=1)
        
        return {
            "user": user_by_username,
            "admins": admin_users,
            "titles": title_elements,
            "search": search_results,
            "comments": tracker_comments,
            "unresolved": unresolved_count
        }
```

---

## Error Handling

### Common Error Scenarios

#### Entity Not Found

```python
async def handle_not_found():
    async with AsyncSessionLocal() as db:
        study_instance = await study.get(db, id=999)
        if not study_instance:
            raise HTTPException(
                status_code=404,
                detail="Study not found"
            )
        return study_instance
```

#### Constraint Violations

```python
async def handle_constraints():
    try:
        async with AsyncSessionLocal() as db:
            # This might violate unique constraint
            study_data = StudyCreate(study_label="DUPLICATE-LABEL")
            new_study = await study.create(db, obj_in=study_data)
            return new_study
    except Exception as e:
        if "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Study label already exists"
            )
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

#### Dependency Conflicts

```python
async def handle_dependencies():
    async with AsyncSessionLocal() as db:
        # Check for dependent entities before deletion
        study_to_delete = await study.get(db, id=1)
        if not study_to_delete:
            raise HTTPException(404, "Study not found")
            
        # Check for dependent database releases
        dependent_releases = await database_release.get_by_study_id(
            db, study_id=study_to_delete.id
        )
        
        if dependent_releases:
            release_labels = [r.database_release_label for r in dependent_releases]
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete study '{study_to_delete.study_label}': "
                       f"{len(dependent_releases)} associated database release(s) exist: "
                       f"{', '.join(release_labels)}. Please delete all associated database releases first."
            )
        
        # Safe to delete
        deleted_study = await study.delete(db, id=study_to_delete.id)
        return deleted_study
```

### Transaction Management

```python
async def transaction_example():
    async with AsyncSessionLocal() as db:
        try:
            # Start transaction (implicit)
            study_data = StudyCreate(study_label="TRANSACTION-TEST")
            new_study = await study.create(db, obj_in=study_data)
            
            release_data = DatabaseReleaseCreate(
                study_id=new_study.id,
                database_release_label="DB_LOCK_TRANSACTION_TEST",
                database_release_date="2024-12-01"
            )
            new_release = await database_release.create(db, obj_in=release_data)
            
            # If we get here, both operations succeeded
            # Transaction is committed automatically by CRUD methods
            return {"study": new_study, "release": new_release}
            
        except Exception as e:
            # Transaction is rolled back automatically
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Transaction failed: {str(e)}"
            )
```

---

## Related Documentation

- [API_REFERENCE.md](API_REFERENCE.md) - FastAPI endpoints that use these CRUD methods
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Database models and relationships
- [UTILITY_FUNCTIONS.md](UTILITY_FUNCTIONS.md) - Phase 2 utility functions that wrap CRUD operations
- [WEBSOCKET_EVENTS.md](WEBSOCKET_EVENTS.md) - WebSocket events triggered by CRUD operations