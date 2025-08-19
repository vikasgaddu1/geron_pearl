# Phase 2 Utility Functions Documentation

**PEARL Full-Stack Research Data Management System**  
**Phase 2 Utility Functions and Existing Helpers**

This document catalogs Phase 2 utility functions and existing helper functions that provide common patterns, standardization, and code reuse across the PEARL system.

## Table of Contents

- [Backend Phase 2 Utilities](#backend-phase-2-utilities)
- [Frontend Phase 2 Utilities](#frontend-phase-2-utilities)
- [Existing Helper Functions](#existing-helper-functions)
- [Usage Patterns](#usage-patterns)
- [Integration Examples](#integration-examples)
- [Best Practices](#best-practices)

---

## Backend Phase 2 Utilities

### Validation Utilities

**Location**: `backend/app/api/v1/utils/validation.py`  
**Purpose**: Standardized error handling with consistent HTTP exception patterns.

#### Core Functions

##### raise_not_found_exception(entity_type: str, entity_id: int)
Raises standardized 404 exceptions for missing entities.

```python
def raise_not_found_exception(entity_type: str, entity_id: int):
    """
    Raise a standardized 404 exception for missing entities.
    
    Args:
        entity_type: Human-readable entity type (e.g., "Study", "User")
        entity_id: Entity ID that was not found
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{entity_type} with ID {entity_id} not found"
    )

# Usage Example
async def get_study_endpoint(study_id: int, db: AsyncSession):
    study = await study_crud.get(db, id=study_id)
    if not study:
        raise_not_found_exception("Study", study_id)
    return study
```

##### raise_business_logic_exception(message: str, status_code: int = 400)
Raises business logic validation exceptions.

```python
def raise_business_logic_exception(message: str, status_code: int = 400):
    """
    Raise business logic validation exceptions.
    
    Args:
        message: User-friendly error message
        status_code: HTTP status code (default: 400)
    """
    raise HTTPException(status_code=status_code, detail=message)

# Usage Example
async def create_study_endpoint(study_data: StudyCreate, db: AsyncSession):
    existing = await study_crud.get_by_label(db, label=study_data.study_label)
    if existing:
        raise_business_logic_exception(f"Study '{study_data.study_label}' already exists")
    
    return await study_crud.create(db, obj_in=study_data)
```

##### raise_dependency_conflict_exception(entity_type, entity_label, dependent_count, dependent_type, dependent_names)
Raises detailed dependency conflict exceptions for deletion protection.

```python
def raise_dependency_conflict_exception(
    entity_type: str, 
    entity_label: str, 
    dependent_count: int,
    dependent_type: str, 
    dependent_names: List[str]
):
    """
    Raise detailed dependency conflict exceptions.
    
    Args:
        entity_type: Type of entity being deleted
        entity_label: Label/name of entity being deleted
        dependent_count: Number of dependent entities
        dependent_type: Type of dependent entities
        dependent_names: List of dependent entity names
    """
    names_str = ', '.join(dependent_names[:5])  # Limit to first 5
    if len(dependent_names) > 5:
        names_str += f", and {len(dependent_names) - 5} more"
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Cannot delete {entity_type} '{entity_label}': {dependent_count} "
               f"associated {dependent_type}(s) exist: {names_str}. "
               f"Please delete all associated {dependent_type}s first."
    )

# Usage Example
async def delete_study_endpoint(study_id: int, db: AsyncSession):
    study = await study_crud.get(db, id=study_id)
    if not study:
        raise_not_found_exception("Study", study_id)
    
    # Check for dependent database releases
    releases = await database_release_crud.get_by_study_id(db, study_id=study.id)
    if releases:
        release_names = [r.database_release_label for r in releases]
        raise_dependency_conflict_exception(
            entity_type="Study",
            entity_label=study.study_label,
            dependent_count=len(releases),
            dependent_type="database release",
            dependent_names=release_names
        )
    
    return await study_crud.delete(db, id=study_id)
```

#### Validation Decorators

##### @handle_validation_error
Decorator for automatic validation error handling.

```python
from functools import wraps

def handle_validation_error(func):
    """
    Decorator to handle common validation errors in endpoints.
    Converts SQLAlchemy exceptions to user-friendly HTTP exceptions.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            if "unique constraint" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A record with this information already exists"
                )
            elif "foreign key constraint" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Referenced record does not exist"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Database constraint violation"
                )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    return wrapper

# Usage Example
@handle_validation_error
async def create_user_endpoint(user_data: UserCreate, db: AsyncSession):
    return await user_crud.create(db, obj_in=user_data)
```

---

### WebSocket Utilities

**Location**: `backend/app/api/v1/utils/websocket_utils.py`  
**Purpose**: Enhanced broadcasting with automatic SQLAlchemy → Pydantic conversion.

#### Core Functions

##### broadcast_entity_change(entity_data, event_type: str)
Generic entity broadcasting with automatic model conversion.

```python
async def broadcast_entity_change(entity_data, event_type: str):
    """
    Generic entity broadcasting with automatic model conversion.
    
    Args:
        entity_data: SQLAlchemy model instance or Pydantic model
        event_type: Event type (e.g., "study_created", "user_updated")
    """
    from app.api.v1.websocket import manager
    
    # Convert SQLAlchemy to dict if needed
    if hasattr(entity_data, '__table__'):
        # SQLAlchemy model
        data_dict = sqlalchemy_to_dict(entity_data)
    elif hasattr(entity_data, 'model_dump'):
        # Pydantic v2 model
        data_dict = entity_data.model_dump(mode='json')
    elif hasattr(entity_data, 'dict'):
        # Pydantic v1 model
        data_dict = entity_data.dict()
    else:
        # Already a dict
        data_dict = entity_data
    
    message = {
        "type": event_type,
        "data": data_dict,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast(json.dumps(message))

# Usage Example
async def create_study_endpoint(study_data: StudyCreate, db: AsyncSession):
    new_study = await study_crud.create(db, obj_in=study_data)
    await broadcast_entity_change(new_study, "study_created")
    return new_study
```

##### convert_models_for_broadcast(models: List) -> List[Dict]
Batch convert SQLAlchemy models for WebSocket broadcasting.

```python
def convert_models_for_broadcast(models: List) -> List[Dict]:
    """
    Convert a list of SQLAlchemy models to dictionaries for broadcasting.
    
    Args:
        models: List of SQLAlchemy model instances
        
    Returns:
        List of dictionaries suitable for JSON serialization
    """
    return [
        sqlalchemy_to_dict(model) if hasattr(model, '__table__') 
        else model.model_dump(mode='json') if hasattr(model, 'model_dump')
        else model.dict() if hasattr(model, 'dict')
        else model
        for model in models
    ]

# Usage Example
async def list_studies_endpoint(db: AsyncSession):
    studies = await study_crud.get_multi(db)
    # Convert for potential broadcasting
    studies_data = convert_models_for_broadcast(studies)
    return studies_data
```

##### enhanced_broadcast_with_context(entity_data, event_type: str, context: Dict = None)
Enhanced broadcasting with additional context information.

```python
async def enhanced_broadcast_with_context(
    entity_data, 
    event_type: str, 
    context: Dict = None
):
    """
    Enhanced broadcasting with additional context.
    
    Args:
        entity_data: Entity data to broadcast
        event_type: WebSocket event type
        context: Additional context (user info, related entities, etc.)
    """
    from app.api.v1.websocket import manager
    
    # Convert entity data
    if hasattr(entity_data, '__table__'):
        data_dict = sqlalchemy_to_dict(entity_data)
    else:
        data_dict = entity_data
    
    message = {
        "type": event_type,
        "data": data_dict,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add context if provided
    if context:
        message["context"] = context
    
    await manager.broadcast(json.dumps(message))

# Usage Example - Enhanced tracker deletion
async def delete_tracker_endpoint(tracker_id: int, current_user_id: int, db: AsyncSession):
    tracker = await tracker_crud.get(db, id=tracker_id)
    if not tracker:
        raise_not_found_exception("Tracker", tracker_id)
    
    # Get additional context
    item = await reporting_effort_item_crud.get(db, id=tracker.reporting_effort_item_id)
    user = await user_crud.get(db, id=current_user_id)
    
    deleted_tracker = await tracker_crud.delete(db, id=tracker_id)
    
    # Enhanced broadcast with context
    await enhanced_broadcast_with_context(
        entity_data=deleted_tracker,
        event_type="reporting_effort_tracker_deleted",
        context={
            "deleted_by": {"user_id": user.id, "username": user.username},
            "item": {"item_code": item.item_code, "effort_id": item.reporting_effort_id}
        }
    )
    
    return {"message": "Tracker deleted successfully"}
```

---

### Endpoint Factory

**Location**: `backend/app/api/v1/utils/endpoint_factory.py`  
**Purpose**: Generic endpoint generators to reduce boilerplate code across FastAPI endpoints.

#### Core Factory Functions

##### create_get_endpoint(crud_class, response_model, entity_type)
Create standardized GET endpoint for retrieving a single entity by ID.

```python
def create_get_endpoint(
    crud_class: Any,
    response_model: Type[BaseModel],
    entity_type: str,
    dependencies: List[Callable] = None
) -> Callable:
    """
    Create a standardized GET endpoint for retrieving a single entity by ID.
    
    Args:
        crud_class: CRUD class instance with get() method
        response_model: Pydantic response model
        entity_type: Human-readable entity type for errors
        dependencies: Additional FastAPI dependencies
        
    Returns:
        FastAPI endpoint function
    """
    async def get_entity(
        entity_id: int,
        db: AsyncSession = Depends(get_db)
    ) -> response_model:
        """Get entity by ID."""
        db_entity = await crud_class.get(db, id=entity_id)
        if not db_entity:
            raise_not_found_exception(entity_type, entity_id)
        return db_entity
    
    return get_entity

# Usage Example
from app.crud import study
from app.schemas.study import Study

get_study = create_get_endpoint(study, Study, "Study")

# Add to router
router.add_api_route(
    "/{study_id}",
    get_study,
    methods=["GET"],
    response_model=Study
)
```

##### create_post_endpoint(crud_class, create_model, response_model, entity_type, broadcast_func)
Create standardized POST endpoint for creating entities.

```python
def create_post_endpoint(
    crud_class: Any,
    create_model: Type[BaseModel],
    response_model: Type[BaseModel],
    entity_type: str,
    broadcast_func: Optional[Callable] = None,
    dependencies: List[Callable] = None
) -> Callable:
    """
    Create a standardized POST endpoint for creating entities.
    
    Args:
        crud_class: CRUD class instance with create() method
        create_model: Pydantic model for request body
        response_model: Pydantic model for response
        entity_type: Human-readable entity type for broadcasting
        broadcast_func: Optional WebSocket broadcast function
        dependencies: Additional FastAPI dependencies
        
    Returns:
        FastAPI endpoint function
    """
    async def create_entity(
        entity_in: create_model,
        db: AsyncSession = Depends(get_db)
    ) -> response_model:
        """Create new entity."""
        try:
            created_entity = await crud_class.create(db, obj_in=entity_in)
            
            # Broadcast WebSocket event if function provided
            if broadcast_func:
                await broadcast_func(created_entity)
            
            return created_entity
            
        except Exception as e:
            # Handle common creation errors
            if "already exists" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            elif "constraint" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid {entity_type} data: {str(e)}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error creating {entity_type}"
                )
    
    return create_entity

# Usage Example
from app.crud import study
from app.schemas.study import StudyCreate, Study
from app.api.v1.websocket import broadcast_study_created

create_study = create_post_endpoint(
    study, StudyCreate, Study, "Study", broadcast_study_created
)

router.add_api_route(
    "/",
    create_study,
    methods=["POST"],
    response_model=Study,
    status_code=status.HTTP_201_CREATED
)
```

##### create_delete_endpoint(crud_class, entity_type, broadcast_func, dependency_checks)
Create standardized DELETE endpoint with dependency checking.

```python
def create_delete_endpoint(
    crud_class: Any,
    entity_type: str,
    broadcast_func: Optional[Callable] = None,
    dependency_checks: List[Dict[str, Any]] = None,
    dependencies: List[Callable] = None
) -> Callable:
    """
    Create a standardized DELETE endpoint with dependency checking.
    
    Args:
        crud_class: CRUD class instance with get() and delete() methods
        entity_type: Human-readable entity type for errors/broadcasting
        broadcast_func: Optional WebSocket broadcast function
        dependency_checks: List of dependency check configs
        dependencies: Additional FastAPI dependencies
        
    Returns:
        FastAPI endpoint function
    """
    checks = dependency_checks or []
    
    async def delete_entity(
        entity_id: int,
        db: AsyncSession = Depends(get_db)
    ) -> Dict[str, str]:
        """Delete entity by ID with dependency checking."""
        # Get existing entity
        db_entity = await crud_class.get(db, id=entity_id)
        if not db_entity:
            raise_not_found_exception(entity_type, entity_id)
        
        # Check for dependent entities
        for check in checks:
            dependent_crud = check["crud"]
            method_name = check["method"]
            dependent_type = check["dependent_type"]
            label_field = check.get("label_field", "label")
            
            # Get dependent entities
            method = getattr(dependent_crud, method_name)
            dependent_entities = await method(db, **{
                check.get("param_name", f"{entity_type.lower()}_id"): entity_id
            })
            
            if dependent_entities:
                dependent_names = [getattr(entity, label_field) for entity in dependent_entities]
                entity_label = getattr(db_entity, check.get("entity_label_field", "label"), str(entity_id))
                
                raise_dependency_conflict_exception(
                    entity_type=entity_type,
                    entity_label=entity_label,
                    dependent_count=len(dependent_entities),
                    dependent_type=dependent_type,
                    dependent_names=dependent_names
                )
        
        try:
            # Delete entity
            deleted_entity = await crud_class.delete(db, id=entity_id)
            
            # Broadcast WebSocket event if function provided
            if broadcast_func:
                await broadcast_func(entity_id)
            
            return {"message": f"{entity_type} deleted successfully"}
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting {entity_type}: {str(e)}"
            )
    
    return delete_entity

# Usage Example with dependency checking
from app.crud import study, database_release
from app.api.v1.websocket import broadcast_study_deleted

delete_study = create_delete_endpoint(
    crud_class=study,
    entity_type="Study", 
    broadcast_func=broadcast_study_deleted,
    dependency_checks=[{
        "crud": database_release,
        "method": "get_by_study_id",
        "dependent_type": "database release",
        "label_field": "database_release_label",
        "entity_label_field": "study_label"
    }]
)

router.add_api_route(
    "/{study_id}",
    delete_study,
    methods=["DELETE"],
    response_model=Dict[str, str]
)
```

#### EndpointFactory Class

```python
class EndpointFactory:
    """
    Factory class for creating standardized CRUD endpoints with consistent patterns.
    Reduces boilerplate code and ensures consistent error handling across all endpoints.
    """
    
    def __init__(self, crud_class: Any, entity_type: str):
        self.crud_class = crud_class
        self.entity_type = entity_type
        
    def create_full_crud_router(
        self,
        create_model: Type[BaseModel],
        update_model: Type[BaseModel], 
        response_model: Type[BaseModel],
        broadcast_functions: Dict[str, Callable] = None,
        dependency_checks: List[Dict[str, Any]] = None,
        search_enabled: bool = False,
        pagination: bool = True
    ) -> APIRouter:
        """
        Create a complete CRUD router with all standard endpoints.
        
        Returns:
            Configured APIRouter with all CRUD endpoints
        """
        router = APIRouter()
        broadcasts = broadcast_functions or {}
        
        # Create all standard CRUD endpoints
        get_func = create_get_endpoint(self.crud_class, response_model, self.entity_type)
        list_func = create_list_endpoint(self.crud_class, response_model, pagination)
        create_func = create_post_endpoint(
            self.crud_class, create_model, response_model, 
            self.entity_type, broadcasts.get('created')
        )
        update_func = create_put_endpoint(
            self.crud_class, update_model, response_model,
            self.entity_type, broadcasts.get('updated')
        )
        delete_func = create_delete_endpoint(
            self.crud_class, self.entity_type,
            broadcasts.get('deleted'), dependency_checks
        )
        
        # Add routes to router
        router.add_api_route("/{entity_id}", get_func, methods=["GET"], response_model=response_model)
        router.add_api_route("/", list_func, methods=["GET"], response_model=List[response_model])
        router.add_api_route("/", create_func, methods=["POST"], response_model=response_model, status_code=201)
        router.add_api_route("/{entity_id}", update_func, methods=["PUT"], response_model=response_model)
        router.add_api_route("/{entity_id}", delete_func, methods=["DELETE"], response_model=Dict[str, str])
        
        return router

# Usage Example - Complete CRUD router for Studies
from app.crud import study, database_release
from app.schemas.study import StudyCreate, StudyUpdate, Study
from app.api.v1.websocket import broadcast_study_created, broadcast_study_updated, broadcast_study_deleted

study_factory = EndpointFactory(study, "Study")

study_router = study_factory.create_full_crud_router(
    create_model=StudyCreate,
    update_model=StudyUpdate,
    response_model=Study,
    broadcast_functions={
        'created': broadcast_study_created,
        'updated': broadcast_study_updated,
        'deleted': broadcast_study_deleted
    },
    dependency_checks=[{
        "crud": database_release,
        "method": "get_by_study_id",
        "dependent_type": "database release",
        "label_field": "database_release_label",
        "entity_label_field": "study_label"
    }]
)

# Include in main router
main_router.include_router(study_router, prefix="/studies", tags=["studies"])
```

---

## Frontend Phase 2 Utilities

### CRUD Base Utilities

**Location**: `admin-frontend/modules/utils/crud_base.R`  
**Purpose**: Common patterns for form validation, API calls, and DataTable configuration.

#### Standard DataTable Configuration

##### create_standard_datatable()
Comprehensive DataTable setup with consistent styling.

```r
create_standard_datatable <- function(data, 
                                      actions_column = TRUE, 
                                      search_placeholder = "Search (regex supported):",
                                      page_length = 25,
                                      empty_message = "No data available",
                                      show_entries = TRUE,
                                      show_pagination = TRUE,
                                      draw_callback = NULL,
                                      extra_options = list()) {
  
  # Handle empty data case
  if (is.null(data) || nrow(data) == 0) {
    if (is.null(data)) {
      data <- data.frame(Message = empty_message)
    }
    
    return(DT::datatable(
      data,
      filter = 'top',
      options = list(
        dom = if (show_entries && show_pagination) 'frtip' else 'frt',
        pageLength = page_length,
        searching = TRUE,
        language = list(
          search = "",
          searchPlaceholder = search_placeholder,
          emptyTable = empty_message
        )
      ),
      escape = FALSE,
      rownames = FALSE,
      selection = 'none'
    ))
  }
  
  # Add Actions column if requested and not present
  if (actions_column && !"Actions" %in% names(data)) {
    data$Actions <- ""  # Will be populated by JavaScript drawCallback
  }
  
  # Standard options for non-empty tables
  options <- list(
    dom = if (show_entries && show_pagination) 'frtip' else 'frt',
    pageLength = page_length,
    searching = TRUE,
    autoWidth = FALSE,
    language = list(
      search = "",
      searchPlaceholder = search_placeholder,
      emptyTable = empty_message
    ),
    search = list(
      regex = TRUE,
      caseInsensitive = TRUE
    )
  )
  
  # Configure Actions column if present
  if (actions_column && "Actions" %in% names(data)) {
    actions_col_index <- which(names(data) == "Actions") - 1  # 0-indexed
    options$columnDefs <- list(list(
      targets = actions_col_index,
      searchable = FALSE,
      orderable = FALSE,
      width = "120px",
      className = "text-center"
    ))
  }
  
  # Add drawCallback if provided
  if (!is.null(draw_callback)) {
    options$drawCallback <- draw_callback
  }
  
  # Merge any extra options
  if (length(extra_options) > 0) {
    options <- modifyList(options, extra_options)
  }
  
  DT::datatable(
    data,
    filter = 'top',
    options = options,
    escape = FALSE,
    rownames = FALSE,
    selection = 'none'
  )
}

# Usage Example
output$users_table <- DT::renderDataTable({
  if (is.null(users_data()) || nrow(users_data()) == 0) {
    return(create_standard_datatable(NULL, empty_message = "No users found"))
  }
  
  display_data <- users_data()
  display_data$Actions <- sapply(1:nrow(display_data), function(i) {
    generate_action_buttons(display_data[i, ]$id, "Edit User", "Delete User")
  })
  
  create_standard_datatable(
    display_data,
    actions_column = TRUE,
    search_placeholder = "Search users (regex supported):",
    draw_callback = JS("function(settings) { bindUserActionButtons(); }")
  )
})
```

#### Form Validation Patterns

##### setup_enhanced_form_validation()
Configuration-driven validation setup with common patterns.

```r
setup_enhanced_form_validation <- function(input_validator, validation_config) {
  # validation_config format:
  # list(
  #   field_id = list(type = "text", required = TRUE, min_length = 3),
  #   email_field = list(type = "email", required = FALSE),
  #   role_field = list(type = "dropdown", required = TRUE, choices = c("ADMIN", "EDITOR"))
  # )
  
  for (field_id in names(validation_config)) {
    config <- validation_config[[field_id]]
    field_type <- config$type
    
    if (field_type == "text") {
      if (config$required %||% FALSE) {
        input_validator$add_rule(field_id, sv_required())
      }
      
      min_len <- config$min_length %||% 1
      input_validator$add_rule(field_id, function(value) {
        validate_required_text_input(value, field_id, min_len)
      })
      
    } else if (field_type == "email") {
      if (config$required %||% FALSE) {
        input_validator$add_rule(field_id, sv_required())
      }
      
      input_validator$add_rule(field_id, function(value) {
        validate_email_input(value, field_id)
      })
      
    } else if (field_type == "dropdown") {
      if (config$required %||% FALSE) {
        input_validator$add_rule(field_id, sv_required())
      }
      
      choices <- config$choices
      input_validator$add_rule(field_id, function(value) {
        validate_dropdown_selection(value, field_id, choices)
      })
    }
  }
  
  return(input_validator)
}

# Usage Example
create_user_validator <- InputValidator$new()

validation_config <- list(
  username = list(type = "text", required = TRUE, min_length = 3),
  email = list(type = "email", required = FALSE),
  role = list(type = "dropdown", required = TRUE, choices = c("ADMIN", "ANALYST", "VIEWER")),
  department = list(type = "text", required = FALSE)
)

create_user_validator <- setup_enhanced_form_validation(
  create_user_validator, 
  validation_config
)

# Enable deferred validation (only triggers on save)
create_user_validator$enable()

# Trigger validation on save
observeEvent(input$save_user, {
  if (create_user_validator$is_valid()) {
    # Process form
  } else {
    show_error_notification("Please correct the form errors")
  }
})
```

##### Standard Validation Functions
```r
validate_required_text_input <- function(input_value, field_name, min_length = 1) {
  if (is.null(input_value) || nchar(trimws(input_value)) < min_length) {
    return(paste(field_name, "must be at least", min_length, "characters"))
  }
  return(NULL)
}

validate_email_input <- function(input_value, field_name) {
  if (is.null(input_value) || trimws(input_value) == "") {
    return(NULL)  # Allow empty for optional email fields
  }
  
  email_pattern <- "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
  if (!grepl(email_pattern, input_value)) {
    return(paste(field_name, "must be a valid email address"))
  }
  
  return(NULL)
}

validate_dropdown_selection <- function(input_value, field_name, valid_choices = NULL) {
  if (is.null(input_value) || input_value == "") {
    return(paste(field_name, "must be selected"))
  }
  
  if (!is.null(valid_choices) && !input_value %in% valid_choices) {
    return(paste(field_name, "must be one of:", paste(valid_choices, collapse = ", ")))
  }
  
  return(NULL)
}
```

#### Modal Dialog Standardization

##### create_edit_modal()
Standard edit modal for entity CRUD operations.

```r
create_edit_modal <- function(title, content, size = "m", save_button_id, 
                             cancel_button_id = NULL, 
                             save_button_label = "Update", 
                             save_button_icon = "check", 
                             save_button_class = "btn-warning") {
  modalDialog(
    title = tagList(bs_icon("pencil"), " ", title),
    size = size,
    easyClose = FALSE,
    content,
    footer = div(
      class = "d-flex justify-content-end gap-2",
      if (!is.null(cancel_button_id)) {
        actionButton(cancel_button_id, "Cancel", class = "btn btn-secondary")
      } else {
        modalButton("Cancel")
      },
      actionButton(save_button_id, save_button_label,
                  icon = bs_icon(save_button_icon),
                  class = paste("btn", save_button_class))
    )
  )
}

# Usage Example
show_edit_user_modal <- function(user_data) {
  showModal(
    create_edit_modal(
      title = paste("Edit User:", user_data$username),
      content = tagList(
        create_text_input_field("edit_username", "Username", 
                               value = user_data$username, required = TRUE),
        create_select_input_field("edit_role", "Role", 
                                 choices = role_choices, 
                                 selected = user_data$role, required = TRUE),
        create_text_input_field("edit_department", "Department", 
                               value = user_data$department)
      ),
      save_button_id = "save_edit_user"
    )
  )
}
```

##### create_delete_confirmation_modal()
Standard delete confirmation modal with enhanced warning.

```r
create_delete_confirmation_modal <- function(entity_type, entity_name, 
                                           confirm_button_id, 
                                           additional_info = NULL, 
                                           warning_message = NULL) {
  default_warning <- "This action cannot be undone!"
  warning_text <- if (!is.null(warning_message)) warning_message else default_warning
  
  content <- tagList(
    tags$div(class = "alert alert-danger",
      tags$strong("Warning: "), warning_text
    ),
    tags$p(paste("Are you sure you want to delete this", tolower(entity_type), "?")),
    tags$hr(),
    tags$dl(
      tags$dt(paste(entity_type, "Name:")),
      tags$dd(tags$strong(entity_name))
    )
  )
  
  # Add additional info if provided
  if (!is.null(additional_info)) {
    content <- tagList(content, additional_info)
  }
  
  modalDialog(
    title = tagList(bs_icon("exclamation-triangle", class = "text-danger"), 
                   " Confirm Deletion"),
    content,
    footer = tagList(
      actionButton(confirm_button_id, paste("Delete", entity_type),
                  icon = bs_icon("trash"),
                  class = "btn-danger"),
      modalButton("Cancel")
    ),
    easyClose = FALSE,
    size = "m"
  )
}

# Usage Example
show_delete_user_confirmation <- function(user_data) {
  showModal(
    create_delete_confirmation_modal(
      entity_type = "User",
      entity_name = user_data$username,
      confirm_button_id = "confirm_delete_user",
      additional_info = tagList(
        tags$p(tags$strong("Role: "), user_data$role),
        tags$p(tags$strong("Department: "), user_data$department %||% "Not specified")
      )
    )
  )
}
```

#### WebSocket Observer Consolidation

##### setup_websocket_observers()
Enhanced WebSocket observer setup that replaces all legacy patterns.

```r
setup_websocket_observers <- function(input, load_data_func, module_name, event_types = NULL) {
  # Universal CRUD Manager refresh observer (Primary)
  observeEvent(input$crud_refresh, {
    if (!is.null(input$crud_refresh)) {
      cat("🔄 Universal CRUD refresh triggered for", module_name, "\n")
      load_data_func()
    }
  })
  
  # Legacy WebSocket observer (Fallback - will be deprecated)
  if (!is.null(event_types)) {
    observeEvent(input$websocket_event, {
      if (!is.null(input$websocket_event)) {
        event_data <- input$websocket_event
        cat("📡 Legacy WebSocket event received for", module_name, ":", event_data$type, "\n")
        
        # Check if event type matches this module
        if (any(sapply(event_types, function(pattern) startsWith(event_data$type, pattern)))) {
          load_data_func()
        }
      }
    })
  }
}

# Usage Example
users_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # Data loading function
    load_users_data <- function() {
      # API call to load users
    }
    
    # Setup WebSocket observers
    setup_websocket_observers(
      input = input,
      load_data_func = load_users_data,
      module_name = "users",
      event_types = c("user_created", "user_updated", "user_deleted")
    )
  })
}
```

##### setup_universal_crud_observer()
Simplified observer for modules using Universal CRUD Manager only.

```r
setup_universal_crud_observer <- function(input, load_data_func, module_name, debug = TRUE) {
  observeEvent(input$crud_refresh, {
    if (!is.null(input$crud_refresh)) {
      if (debug) {
        cat("🔄", module_name, "refresh triggered via Universal CRUD Manager\n")
      }
      load_data_func()
    }
  })
}

# Usage Example
package_items_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    load_package_items_data <- function() {
      # API call to load package items
    }
    
    # Universal CRUD Manager observer only
    setup_universal_crud_observer(
      input = input,
      load_data_func = load_package_items_data,
      module_name = "package_items"
    )
  })
}
```

---

### API Utilities

**Location**: `admin-frontend/modules/utils/api_utils.R`  
**Purpose**: Standardized HTTP client operations with error handling.

#### Standard API Client

##### make_api_request()
Comprehensive HTTP client with error handling.

```r
make_api_request <- function(url, method = "GET", body = NULL, timeout = 30) {
  tryCatch({
    # Build request
    req <- request(url)
    req <- req_timeout(req, timeout)
    
    # Add body for POST/PUT requests
    if (!is.null(body)) {
      req <- req_body_json(req, body)
    }
    
    # Set method
    if (method == "POST") {
      req <- req_method(req, "POST")
    } else if (method == "PUT") {
      req <- req_method(req, "PUT")
    } else if (method == "DELETE") {
      req <- req_method(req, "DELETE")
    }
    
    # Perform request
    response <- req_perform(req)
    
    # Check status and parse response
    if (resp_status(response) >= 200 && resp_status(response) < 300) {
      if (resp_has_body(response)) {
        content_type <- resp_content_type(response)
        if (grepl("application/json", content_type)) {
          return(resp_body_json(response))
        } else {
          return(resp_body_string(response))
        }
      } else {
        return(list(success = TRUE))
      }
    } else {
      # HTTP error handling
      error_body <- if (resp_has_body(response)) {
        tryCatch({
          error_data <- resp_body_json(response)
          if ("detail" %in% names(error_data)) {
            error_data$detail
          } else {
            error_data
          }
        }, error = function(e) {
          resp_body_string(response)
        })
      } else {
        paste("HTTP", resp_status(response))
      }
      
      return(list(error = paste("HTTP", resp_status(response), "-", error_body)))
    }
    
  }, error = function(e) {
    return(list(error = paste("Network error:", e$message)))
  })
}

# Convenience functions
api_get <- function(url, timeout = 30) {
  make_api_request(url, "GET", timeout = timeout)
}

api_post <- function(url, data, timeout = 30) {
  make_api_request(url, "POST", data, timeout = timeout)
}

api_put <- function(url, data, timeout = 30) {
  make_api_request(url, "PUT", data, timeout = timeout)
}

api_delete <- function(url, timeout = 30) {
  make_api_request(url, "DELETE", timeout = timeout)
}
```

##### CRUD Operations Helper
```r
crud_operations <- list(
  # Get all entities
  get_all = function(endpoint, skip = 0, limit = 100) {
    url <- paste0(endpoint, "?skip=", skip, "&limit=", limit)
    api_get(url)
  },
  
  # Get single entity
  get_by_id = function(endpoint, id) {
    url <- paste0(endpoint, "/", id)
    api_get(url)
  },
  
  # Create entity
  create = function(endpoint, data) {
    api_post(endpoint, data)
  },
  
  # Update entity
  update = function(endpoint, id, data) {
    url <- paste0(endpoint, "/", id)
    api_put(url, data)
  },
  
  # Delete entity
  delete = function(endpoint, id) {
    url <- paste0(endpoint, "/", id)
    api_delete(url)
  }
)

# Usage Example
users_endpoint <- build_endpoint_url("PEARL_USERS_ENDPOINT", "/api/v1/users")

# Get all users
users_result <- crud_operations$get_all(users_endpoint, skip = 0, limit = 50)

# Create new user
new_user_data <- list(
  username = "johndoe",
  role = "ANALYST",
  department = "Clinical Research"
)
create_result <- crud_operations$create(users_endpoint, new_user_data)

# Update user
update_data <- list(role = "ADMIN")
update_result <- crud_operations$update(users_endpoint, user_id, update_data)

# Delete user
delete_result <- crud_operations$delete(users_endpoint, user_id)
```

#### Notification Standardization

##### Notification Functions
```r
# Standard success notification
show_success_notification <- function(message, duration = 3000) {
  showNotification(
    message,
    type = "message",
    duration = duration
  )
}

# Standard error notification
show_error_notification <- function(message, duration = 5000) {
  showNotification(
    message,
    type = "error",
    duration = duration
  )
}

# Enhanced validation error notification for API responses
show_validation_error_notification <- function(api_result, duration = 8000) {
  error_msg <- extract_error_message(api_result)
  
  # Special handling for duplicate validation errors
  if (grepl("Duplicate.*are not allowed", error_msg)) {
    showNotification(
      tagList(
        tags$strong("Duplicate Content Detected"),
        tags$br(),
        error_msg,
        tags$br(),
        tags$small("Tip: The system compares content ignoring spaces and letter case.")
      ),
      type = "error",
      duration = duration
    )
  } else if (grepl("already exists", error_msg)) {
    showNotification(
      tagList(
        tags$strong("Duplicate Entry"),
        tags$br(),
        error_msg
      ),
      type = "error",
      duration = duration
    )
  } else {
    show_error_notification(error_msg, duration)
  }
}

# Standard operation notification with entity context
show_operation_notification <- function(operation, entity, success = TRUE, entity_name = NULL) {
  if (success) {
    if (!is.null(entity_name)) {
      message <- paste(entity, "'", entity_name, "'", operation, "successfully")
    } else {
      message <- paste(entity, operation, "successfully")
    }
    show_success_notification(message)
  } else {
    message <- paste("Failed to", operation, tolower(entity))
    show_error_notification(message)
  }
}

# Usage Examples
# Success notification
show_operation_notification("created", "User", success = TRUE, entity_name = "johndoe")
# Output: "User 'johndoe' created successfully"

# Error notification  
show_operation_notification("updated", "Study", success = FALSE)
# Output: "Failed to updated study"

# API response notification
api_result <- api_post(users_endpoint, user_data)
success <- show_api_notification(api_result, "User created successfully")
if (success) {
  load_users_data()
  removeModal()
}
```

---

## Existing Helper Functions

### Core Utility Functions

**Location**: `backend/app/utils.py`  
**Purpose**: Core utility functions for SQLAlchemy conversion and message formatting.

#### sqlalchemy_to_dict()
Convert SQLAlchemy model instances to dictionaries.

```python
def sqlalchemy_to_dict(obj):
    """
    Convert SQLAlchemy model instance to dictionary for JSON serialization.
    Handles datetime objects, relationships, and None values properly.
    """
    if obj is None:
        return None
        
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            result[column.name] = value.isoformat()
        else:
            result[column.name] = value
    return result
```

#### broadcast_message()
Create standardized WebSocket message format.

```python
def broadcast_message(message_type: str, data: Any) -> str:
    """
    Create standardized WebSocket message format.
    
    Args:
        message_type: Type of message (e.g., "study_created")
        data: Message payload data
        
    Returns:
        JSON string ready for WebSocket broadcasting
    """
    message = {
        "type": message_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    return json.dumps(message)
```

---

## Usage Patterns

### Backend Integration Pattern

```python
# Complete endpoint with Phase 2 utilities
from app.api.v1.utils.validation import handle_validation_error, raise_not_found_exception
from app.api.v1.utils.websocket_utils import broadcast_entity_change
from app.api.v1.utils.endpoint_factory import create_get_endpoint

@router.post("/", response_model=Study, status_code=201)
@handle_validation_error
async def create_study_endpoint(
    study_data: StudyCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new study with full Phase 2 integration."""
    # Create study
    new_study = await study_crud.create(db, obj_in=study_data)
    
    # Broadcast WebSocket event
    await broadcast_entity_change(new_study, "study_created")
    
    return new_study

# Using endpoint factory
get_study = create_get_endpoint(study_crud, Study, "Study")
router.add_api_route("/{study_id}", get_study, methods=["GET"])
```

### Frontend Integration Pattern

```r
# Complete module with Phase 2 utilities
users_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # Data storage
    users_data <- reactiveVal(NULL)
    
    # Load data function
    load_users_data <- function() {
      endpoint <- build_endpoint_url("PEARL_USERS_ENDPOINT", "/api/v1/users")
      result <- crud_operations$get_all(endpoint)
      
      if (!"error" %in% names(result)) {
        users_data(result)
      } else {
        show_error_notification("Failed to load users")
      }
    }
    
    # Initial load
    load_users_data()
    
    # Setup WebSocket observers
    setup_universal_crud_observer(
      input = input,
      load_data_func = load_users_data,
      module_name = "users"
    )
    
    # DataTable output
    output$users_table <- DT::renderDataTable({
      create_standard_datatable(
        users_data(),
        actions_column = TRUE,
        search_placeholder = "Search users..."
      )
    })
    
    # Form validation
    create_validator <- InputValidator$new()
    validation_config <- list(
      username = list(type = "text", required = TRUE, min_length = 3),
      role = list(type = "dropdown", required = TRUE, choices = c("ADMIN", "ANALYST", "VIEWER"))
    )
    create_validator <- setup_enhanced_form_validation(create_validator, validation_config)
    create_validator$enable()
    
    # Create user handler
    observeEvent(input$save_create_user, {
      if (create_validator$is_valid()) {
        user_data <- list(
          username = input$create_username,
          role = input$create_role,
          department = input$create_department
        )
        
        endpoint <- build_endpoint_url("PEARL_USERS_ENDPOINT", "/api/v1/users")
        result <- crud_operations$create(endpoint, user_data)
        
        success <- show_api_notification(result, "User created successfully")
        if (success) {
          load_users_data()
          removeModal()
        }
      }
    })
  })
}
```

---

## Integration Examples

### Complete CRUD Endpoint with All Phase 2 Utilities

```python
# backend/app/api/v1/studies.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.crud import study, database_release
from app.schemas.study import StudyCreate, StudyUpdate, Study
from app.db.session import get_db
from app.api.v1.utils.validation import (
    handle_validation_error, 
    raise_not_found_exception,
    raise_dependency_conflict_exception
)
from app.api.v1.utils.websocket_utils import broadcast_entity_change
from app.api.v1.utils.endpoint_factory import EndpointFactory

router = APIRouter()

# Method 1: Using EndpointFactory for complete automation
study_factory = EndpointFactory(study, "Study")
study_router = study_factory.create_full_crud_router(
    create_model=StudyCreate,
    update_model=StudyUpdate,
    response_model=Study,
    broadcast_functions={
        'created': lambda x: broadcast_entity_change(x, "study_created"),
        'updated': lambda x: broadcast_entity_change(x, "study_updated"),
        'deleted': lambda x: broadcast_entity_change(x, "study_deleted")
    },
    dependency_checks=[{
        "crud": database_release,
        "method": "get_by_study_id",
        "dependent_type": "database release",
        "label_field": "database_release_label",
        "entity_label_field": "study_label"
    }]
)

# Include the complete router
router.include_router(study_router)

# Method 2: Manual implementation with utilities for custom logic
@router.post("/custom", response_model=Study, status_code=201)
@handle_validation_error
async def create_study_custom(
    study_data: StudyCreate,
    db: AsyncSession = Depends(get_db)
):
    """Custom study creation with additional business logic."""
    # Custom validation
    if "test" in study_data.study_label.lower():
        raise HTTPException(
            status_code=400,
            detail="Test studies are not allowed in production"
        )
    
    # Create study
    new_study = await study.create(db, obj_in=study_data)
    
    # Enhanced broadcast with context
    await broadcast_entity_change(new_study, "study_created")
    
    return new_study
```

### Complete Frontend Module with All Phase 2 Utilities

```r
# admin-frontend/modules/studies_server.R
studies_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # Reactive data storage
    studies_data <- reactiveVal(NULL)
    selected_study <- reactiveVal(NULL)
    
    # API endpoint configuration
    studies_endpoint <- build_endpoint_url("PEARL_STUDIES_ENDPOINT", "/api/v1/studies")
    
    # Data loading function
    load_studies_data <- function() {
      result <- crud_operations$get_all(studies_endpoint)
      if (!"error" %in% names(result)) {
        studies_data(result)
      } else {
        show_error_notification("Failed to load studies")
      }
    }
    
    # Initial data load
    load_studies_data()
    
    # WebSocket integration
    setup_universal_crud_observer(
      input = input,
      load_data_func = load_studies_data,
      module_name = "studies"
    )
    
    # DataTable output
    output$studies_table <- DT::renderDataTable({
      if (is.null(studies_data()) || length(studies_data()) == 0) {
        return(create_standard_datatable(NULL, empty_message = "No studies found"))
      }
      
      # Prepare display data
      display_data <- data.frame(
        ID = sapply(studies_data(), function(x) x$id),
        `Study Label` = sapply(studies_data(), function(x) x$study_label),
        `Created` = sapply(studies_data(), function(x) x$created_at),
        stringsAsFactors = FALSE
      )
      
      # Add action buttons
      display_data$Actions <- sapply(1:nrow(display_data), function(i) {
        generate_action_buttons(
          display_data[i, "ID"], 
          edit_label = "Edit Study",
          delete_label = "Delete Study"
        )
      })
      
      create_standard_datatable(
        display_data,
        actions_column = TRUE,
        search_placeholder = "Search studies (regex supported):",
        draw_callback = JS("
          function(settings) {
            bindStudyActionButtons();
          }
        ")
      )
    })
    
    # Form validation setup
    create_validator <- InputValidator$new()
    edit_validator <- InputValidator$new()
    
    validation_config <- list(
      study_label = list(type = "text", required = TRUE, min_length = 3)
    )
    
    create_validator <- setup_enhanced_form_validation(create_validator, validation_config)
    edit_validator <- setup_enhanced_form_validation(edit_validator, validation_config)
    
    create_validator$enable()
    edit_validator$enable()
    
    # Create study modal
    observeEvent(input$create_study_btn, {
      showModal(
        create_create_modal(
          title = "Create New Study",
          content = tagList(
            create_text_input_field(
              "create_study_label", 
              "Study Label", 
              placeholder = "Enter study label (e.g., ONCOLOGY-2024-001)",
              required = TRUE
            )
          ),
          save_button_id = "save_create_study"
        )
      )
    })
    
    # Edit study modal
    observeEvent(input$edit_study_btn, {
      study_id <- input$edit_study_btn
      study_data <- Find(function(x) x$id == study_id, studies_data())
      
      if (!is.null(study_data)) {
        selected_study(study_data)
        showModal(
          create_edit_modal(
            title = paste("Edit Study:", study_data$study_label),
            content = tagList(
              create_text_input_field(
                "edit_study_label",
                "Study Label",
                value = study_data$study_label,
                required = TRUE
              )
            ),
            save_button_id = "save_edit_study"
          )
        )
      }
    })
    
    # Delete confirmation modal
    observeEvent(input$delete_study_btn, {
      study_id <- input$delete_study_btn
      study_data <- Find(function(x) x$id == study_id, studies_data())
      
      if (!is.null(study_data)) {
        selected_study(study_data)
        showModal(
          create_delete_confirmation_modal(
            entity_type = "Study",
            entity_name = study_data$study_label,
            confirm_button_id = "confirm_delete_study",
            additional_info = tagList(
              tags$p(tags$strong("Created: "), study_data$created_at),
              tags$div(class = "alert alert-warning mt-3",
                tags$strong("Note: "), 
                "This will also delete all associated database releases and reporting efforts."
              )
            )
          )
        )
      }
    })
    
    # Create study handler
    observeEvent(input$save_create_study, {
      if (create_validator$is_valid()) {
        study_data <- list(
          study_label = input$create_study_label
        )
        
        result <- crud_operations$create(studies_endpoint, study_data)
        success <- show_api_notification(
          result, 
          paste("Study '", input$create_study_label, "' created successfully", sep = "")
        )
        
        if (success) {
          load_studies_data()
          removeModal()
        }
      }
    })
    
    # Update study handler
    observeEvent(input$save_edit_study, {
      if (edit_validator$is_valid() && !is.null(selected_study())) {
        update_data <- list(
          study_label = input$edit_study_label
        )
        
        result <- crud_operations$update(
          studies_endpoint, 
          selected_study()$id, 
          update_data
        )
        
        success <- show_api_notification(
          result,
          paste("Study '", input$edit_study_label, "' updated successfully", sep = "")
        )
        
        if (success) {
          load_studies_data()
          removeModal()
          selected_study(NULL)
        }
      }
    })
    
    # Delete study handler
    observeEvent(input$confirm_delete_study, {
      if (!is.null(selected_study())) {
        result <- crud_operations$delete(studies_endpoint, selected_study()$id)
        success <- show_api_notification(
          result,
          paste("Study '", selected_study()$study_label, "' deleted successfully", sep = "")
        )
        
        if (success) {
          load_studies_data()
          removeModal()
          selected_study(NULL)
        }
      }
    })
  })
}
```

---

## Best Practices

### Backend Best Practices

1. **Always use validation utilities** for consistent error handling
2. **Use endpoint factories** for standard CRUD operations to reduce boilerplate
3. **Include WebSocket broadcasting** for real-time synchronization
4. **Implement dependency checking** for deletion protection
5. **Use the @handle_validation_error decorator** for automatic error conversion

### Frontend Best Practices

1. **Use create_standard_datatable()** for all data tables
2. **Setup WebSocket observers** with utility functions
3. **Use modal creation utilities** for consistent UI
4. **Implement deferred validation** for better UX
5. **Use environment variables** for all API endpoints
6. **Show appropriate notifications** for all user actions

### Integration Best Practices

1. **Consistent error handling** across frontend and backend
2. **Standardized message formats** for WebSocket events
3. **Proper data conversion** between SQLAlchemy and Pydantic models
4. **Comprehensive logging** for debugging and monitoring
5. **Graceful fallbacks** for network or system failures

---

## Related Documentation

- [API_REFERENCE.md](API_REFERENCE.md) - API endpoints that use these utility functions
- [FRONTEND_MODULES.md](FRONTEND_MODULES.md) - Frontend modules that integrate these utilities
- [WEBSOCKET_EVENTS.md](WEBSOCKET_EVENTS.md) - WebSocket events managed by utility functions
- [CODE_PATTERNS.md](CODE_PATTERNS.md) - Common patterns that use these utilities