# Code Patterns Documentation

**PEARL Full-Stack Research Data Management System**  
**Common Code Patterns for Reuse and Consistency**

This document catalogs established code patterns in the PEARL system for validation, error handling, modal dialogs, and other common operations that should be reused across the application.

## Table of Contents

- [Backend Code Patterns](#backend-code-patterns)
- [Frontend Code Patterns](#frontend-code-patterns)
- [WebSocket Integration Patterns](#websocket-integration-patterns)
- [Database Interaction Patterns](#database-interaction-patterns)
- [Error Handling Patterns](#error-handling-patterns)
- [Validation Patterns](#validation-patterns)
- [Testing Patterns](#testing-patterns)
- [Performance Patterns](#performance-patterns)

---

## Backend Code Patterns

### Standard CRUD Endpoint Pattern

**Purpose**: Consistent FastAPI endpoint structure with error handling and WebSocket broadcasting.

**Pattern**:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.crud import entity_crud
from app.schemas.entity import EntityCreate, EntityUpdate, Entity
from app.db.session import get_db
from app.api.v1.utils.validation import handle_validation_error, raise_not_found_exception
from app.api.v1.utils.websocket_utils import broadcast_entity_change

router = APIRouter()

@router.post("/", response_model=Entity, status_code=201)
@handle_validation_error
async def create_entity(
    entity_data: EntityCreate,
    db: AsyncSession = Depends(get_db)
) -> Entity:
    """Create new entity with validation and WebSocket broadcasting."""
    created_entity = await entity_crud.create(db, obj_in=entity_data)
    await broadcast_entity_change(created_entity, "entity_created")
    return created_entity

@router.get("/{entity_id}", response_model=Entity)
async def get_entity(
    entity_id: int,
    db: AsyncSession = Depends(get_db)
) -> Entity:
    """Get entity by ID with proper error handling."""
    db_entity = await entity_crud.get(db, id=entity_id)
    if not db_entity:
        raise_not_found_exception("Entity", entity_id)
    return db_entity

@router.get("/", response_model=List[Entity])
async def list_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
) -> List[Entity]:
    """List entities with pagination."""
    return await entity_crud.get_multi(db, skip=skip, limit=limit)

@router.put("/{entity_id}", response_model=Entity)
@handle_validation_error
async def update_entity(
    entity_id: int,
    entity_data: EntityUpdate,
    db: AsyncSession = Depends(get_db)
) -> Entity:
    """Update entity with validation and broadcasting."""
    db_entity = await entity_crud.get(db, id=entity_id)
    if not db_entity:
        raise_not_found_exception("Entity", entity_id)
    
    updated_entity = await entity_crud.update(db, db_obj=db_entity, obj_in=entity_data)
    await broadcast_entity_change(updated_entity, "entity_updated")
    return updated_entity

@router.delete("/{entity_id}")
async def delete_entity(
    entity_id: int,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Delete entity with dependency checking."""
    db_entity = await entity_crud.get(db, id=entity_id)
    if not db_entity:
        raise_not_found_exception("Entity", entity_id)
    
    # Check for dependencies (customize per entity)
    # dependent_entities = await dependent_crud.get_by_parent_id(db, parent_id=entity_id)
    # if dependent_entities:
    #     raise_dependency_conflict_exception(...)
    
    await entity_crud.delete(db, id=entity_id)
    await broadcast_entity_change({"id": entity_id}, "entity_deleted")
    return {"message": "Entity deleted successfully"}
```

**Usage**: Use this pattern for all new entity endpoints. Customize dependency checking and validation as needed.

---

### Dependency Checking Pattern

**Purpose**: Prevent deletion of entities that have dependent records.

**Pattern**:
```python
from app.api.v1.utils.validation import raise_dependency_conflict_exception

async def delete_with_dependency_check(
    entity_id: int,
    db: AsyncSession,
    entity_crud,
    entity_type: str,
    dependency_checks: List[dict]
) -> dict:
    """
    Delete entity with comprehensive dependency checking.
    
    Args:
        entity_id: ID of entity to delete
        db: Database session
        entity_crud: CRUD class for entity
        entity_type: Human-readable entity type
        dependency_checks: List of dependency configurations
            [
                {
                    "crud": dependent_crud_class,
                    "method": "get_by_parent_id", 
                    "dependent_type": "database release",
                    "label_field": "database_release_label",
                    "entity_label_field": "study_label"
                }
            ]
    """
    # Get entity to delete
    db_entity = await entity_crud.get(db, id=entity_id)
    if not db_entity:
        raise_not_found_exception(entity_type, entity_id)
    
    # Check each dependency
    for check in dependency_checks:
        dependent_crud = check["crud"]
        method_name = check["method"]
        dependent_type = check["dependent_type"]
        label_field = check.get("label_field", "label")
        entity_label_field = check.get("entity_label_field", "label")
        
        # Get dependent entities
        method = getattr(dependent_crud, method_name)
        param_name = check.get("param_name", f"{entity_type.lower()}_id")
        dependent_entities = await method(db, **{param_name: entity_id})
        
        if dependent_entities:
            dependent_names = [getattr(entity, label_field) for entity in dependent_entities]
            entity_label = getattr(db_entity, entity_label_field, str(entity_id))
            
            raise_dependency_conflict_exception(
                entity_type=entity_type,
                entity_label=entity_label,
                dependent_count=len(dependent_entities),
                dependent_type=dependent_type,
                dependent_names=dependent_names
            )
    
    # Safe to delete
    deleted_entity = await entity_crud.delete(db, id=entity_id)
    return {"message": f"{entity_type} deleted successfully"}

# Usage Example
@router.delete("/{study_id}")
async def delete_study(study_id: int, db: AsyncSession = Depends(get_db)):
    dependency_checks = [{
        "crud": database_release,
        "method": "get_by_study_id",
        "dependent_type": "database release",
        "label_field": "database_release_label", 
        "entity_label_field": "study_label"
    }]
    
    return await delete_with_dependency_check(
        entity_id=study_id,
        db=db,
        entity_crud=study,
        entity_type="Study",
        dependency_checks=dependency_checks
    )
```

**Usage**: Apply this pattern to all deletion endpoints that need to check for dependent records.

---

### Enhanced WebSocket Broadcasting Pattern

**Purpose**: WebSocket broadcasting with contextual information.

**Pattern**:
```python
from app.api.v1.utils.websocket_utils import enhanced_broadcast_with_context
from app.utils import sqlalchemy_to_dict

async def enhanced_delete_with_broadcast(
    entity_id: int,
    db: AsyncSession,
    entity_crud,
    entity_type: str,
    current_user: dict = None,
    additional_context: dict = None
):
    """Delete entity with enhanced WebSocket broadcasting."""
    
    # Get entity and related data for context
    db_entity = await entity_crud.get(db, id=entity_id)
    if not db_entity:
        raise_not_found_exception(entity_type, entity_id)
    
    # Prepare context information
    context = {
        "deleted_at": datetime.utcnow().isoformat(),
    }
    
    if current_user:
        context["deleted_by"] = {
            "user_id": current_user.get("id"),
            "username": current_user.get("username")
        }
    
    if additional_context:
        context.update(additional_context)
    
    # Delete entity
    deleted_entity = await entity_crud.delete(db, id=entity_id)
    
    # Enhanced broadcast with context
    await enhanced_broadcast_with_context(
        entity_data=sqlalchemy_to_dict(deleted_entity),
        event_type=f"{entity_type.lower()}_deleted",
        context=context
    )
    
    return {"message": f"{entity_type} deleted successfully"}

# Usage Example - Tracker deletion with context
@router.delete("/reporting-effort-tracker/{tracker_id}")
async def delete_tracker(
    tracker_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get additional context
    tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
    if not tracker:
        raise_not_found_exception("Tracker", tracker_id)
    
    item = await reporting_effort_item.get(db, id=tracker.reporting_effort_item_id)
    
    additional_context = {
        "item": {
            "item_code": item.item_code,
            "effort_id": item.reporting_effort_id
        }
    }
    
    return await enhanced_delete_with_broadcast(
        entity_id=tracker_id,
        db=db,
        entity_crud=reporting_effort_item_tracker,
        entity_type="Tracker",
        current_user={"id": current_user.id, "username": current_user.username},
        additional_context=additional_context
    )
```

**Usage**: Use for deletions that need to broadcast contextual information to frontend clients.

---

### Async Session Management Pattern

**Purpose**: Consistent database session handling with proper error handling.

**Pattern**:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal

# Pattern 1: Using dependency injection (preferred for endpoints)
from fastapi import Depends
from app.db.session import get_db

@router.get("/")
async def endpoint_with_dependency(db: AsyncSession = Depends(get_db)):
    """Endpoint using dependency injection for session management."""
    return await some_crud.get_multi(db)

# Pattern 2: Manual session management (for utility functions)
async def utility_function_with_session():
    """Utility function with manual session management."""
    async with AsyncSessionLocal() as db:
        try:
            # Database operations
            result = await some_crud.get_multi(db)
            
            # Explicit commit if needed (CRUD methods handle this automatically)
            # await db.commit()
            
            return result
        except Exception as e:
            # Rollback is automatic on exception
            await db.rollback()
            raise

# Pattern 3: Session context manager (for complex operations)
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_session():
    """Context manager for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

# Usage of context manager
async def complex_operation():
    async with get_db_session() as db:
        # Multiple operations in single transaction
        study = await study_crud.create(db, obj_in=study_data)
        release = await database_release_crud.create(db, obj_in=release_data)
        # All operations succeed or all fail together
```

**Usage**: Use dependency injection for endpoints, manual session management for utilities, and context managers for complex multi-step operations.

---

## Frontend Code Patterns

### Standard Shiny Module Pattern

**Purpose**: Consistent structure for all Shiny modules with API integration and WebSocket handling.

**Pattern**:
```r
# entity_ui.R
entity_ui <- function(id) {
  ns <- NS(id)
  
  tagList(
    # Header with action buttons
    div(class = "d-flex justify-content-between align-items-center mb-3",
      h3("Entity Management"),
      div(
        actionButton(ns("create_btn"), "Create Entity", 
                    icon = bs_icon("plus"), class = "btn btn-success"),
        actionButton(ns("refresh_btn"), "Refresh", 
                    icon = bs_icon("arrow-clockwise"), class = "btn btn-secondary")
      )
    ),
    
    # Main content area
    card(
      card_header("Entities"),
      card_body(
        DT::dataTableOutput(ns("data_table"))
      )
    )
  )
}

# entity_server.R
entity_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # Reactive data storage
    entity_data <- reactiveVal(NULL)
    selected_entity <- reactiveVal(NULL)
    
    # API endpoint configuration
    api_endpoint <- build_endpoint_url("ENTITY_ENDPOINT", "/api/v1/entities")
    
    # Data loading function
    load_entity_data <- function() {
      show_loading_notification("Loading entities...")
      
      result <- crud_operations$get_all(api_endpoint)
      if (!"error" %in% names(result)) {
        entity_data(result)
      } else {
        show_error_notification("Failed to load entities")
      }
    }
    
    # Initial data load
    load_entity_data()
    
    # WebSocket integration (Universal CRUD Manager pattern)
    setup_universal_crud_observer(
      input = input,
      load_data_func = load_entity_data,
      module_name = "entity"
    )
    
    # DataTable output
    output$data_table <- DT::renderDataTable({
      create_standard_datatable(
        entity_data(),
        actions_column = TRUE,
        search_placeholder = "Search entities...",
        draw_callback = JS("function(settings) { bindEntityActionButtons(); }")
      )
    })
    
    # Form validation
    create_validator <- InputValidator$new()
    edit_validator <- InputValidator$new()
    
    validation_config <- list(
      name = list(type = "text", required = TRUE, min_length = 3),
      type = list(type = "dropdown", required = TRUE, choices = c("Type1", "Type2"))
    )
    
    create_validator <- setup_enhanced_form_validation(create_validator, validation_config)
    edit_validator <- setup_enhanced_form_validation(edit_validator, validation_config)
    
    create_validator$enable()
    edit_validator$enable()
    
    # CRUD operations
    observeEvent(input$create_btn, {
      showModal(create_entity_modal())
    })
    
    observeEvent(input$save_create, {
      if (create_validator$is_valid()) {
        entity_data <- list(
          name = input$create_name,
          type = input$create_type
        )
        
        result <- crud_operations$create(api_endpoint, entity_data)
        success <- show_api_notification(result, "Entity created successfully")
        
        if (success) {
          load_entity_data()
          removeModal()
        }
      }
    })
    
    # Additional CRUD handlers...
  })
}
```

**Usage**: Use this pattern as the foundation for all new Shiny modules. Customize the fields, validation, and API calls as needed.

---

### Modal Dialog Pattern

**Purpose**: Consistent modal dialogs for CRUD operations.

**Pattern**:
```r
# Create modal pattern
create_entity_modal <- function() {
  create_create_modal(
    title = "Create New Entity",
    content = tagList(
      create_text_input_field("create_name", "Name", required = TRUE),
      create_select_input_field("create_type", "Type", 
                               choices = c("Type1", "Type2"), required = TRUE),
      create_textarea_input_field("create_description", "Description", rows = 3)
    ),
    save_button_id = "save_create"
  )
}

# Edit modal pattern  
show_edit_entity_modal <- function(entity_data) {
  showModal(
    create_edit_modal(
      title = paste("Edit Entity:", entity_data$name),
      content = tagList(
        create_text_input_field("edit_name", "Name", 
                               value = entity_data$name, required = TRUE),
        create_select_input_field("edit_type", "Type", 
                                 choices = c("Type1", "Type2"), 
                                 selected = entity_data$type, required = TRUE),
        create_textarea_input_field("edit_description", "Description",
                                   value = entity_data$description, rows = 3)
      ),
      save_button_id = "save_edit"
    )
  )
}

# Delete confirmation pattern
show_delete_entity_confirmation <- function(entity_data) {
  showModal(
    create_delete_confirmation_modal(
      entity_type = "Entity",
      entity_name = entity_data$name,
      confirm_button_id = "confirm_delete",
      additional_info = tagList(
        tags$p(tags$strong("Type: "), entity_data$type),
        tags$p(tags$strong("Description: "), entity_data$description)
      ),
      warning_message = "This action cannot be undone and may affect related records."
    )
  )
}

# Bulk upload modal pattern
show_bulk_upload_modal <- function() {
  showModal(
    create_bulk_upload_modal(
      upload_type = "Entity",
      file_input_id = "bulk_file",
      template_download_id = "download_template",
      process_button_id = "process_upload"
    )
  )
}

# Export completion modal pattern
show_export_completion_modal <- function(filename) {
  showModal(
    create_export_modal(
      filename = filename,
      download_button_id = "download_export",
      entity_type = "entity",
      success_message = "Your entity export is ready for download."
    )
  )
}
```

**Usage**: Use these modal patterns for consistent user interface across all modules.

---

### Form Validation Pattern

**Purpose**: Deferred validation that only triggers on save/submit actions.

**Pattern**:
```r
# Standard validation setup
setup_module_validation <- function() {
  # Create validators for different forms
  create_validator <- InputValidator$new()
  edit_validator <- InputValidator$new()
  
  # Define validation configuration
  base_validation_config <- list(
    name = list(type = "text", required = TRUE, min_length = 3),
    email = list(type = "email", required = FALSE),
    type = list(type = "dropdown", required = TRUE, choices = c("Type1", "Type2"))
  )
  
  # Setup validation rules
  create_validator <- setup_enhanced_form_validation(create_validator, base_validation_config)
  edit_validator <- setup_enhanced_form_validation(edit_validator, base_validation_config)
  
  # Enable deferred validation (only validates on trigger)
  create_validator$enable()
  edit_validator$enable()
  
  return(list(create = create_validator, edit = edit_validator))
}

# Validation trigger pattern
observeEvent(input$save_create, {
  if (validators$create$is_valid()) {
    # Process form
    form_data <- get_form_data()
    submit_form(form_data)
  } else {
    # Validation errors are automatically displayed
    show_error_notification("Please correct the form errors before saving")
  }
})

# Custom validation rule pattern
add_custom_validation_rule <- function(validator, field_id, rule_func) {
  validator$add_rule(field_id, rule_func)
}

# Example custom validation
custom_name_validation <- function(value) {
  if (!is.null(value) && grepl("^[A-Z]", value)) {
    return(NULL)  # Valid
  } else {
    return("Name must start with a capital letter")
  }
}

# Usage
validators$create <- add_custom_validation_rule(
  validators$create, 
  "name", 
  custom_name_validation
)
```

**Usage**: Use this pattern for all forms to ensure consistent validation behavior and user experience.

---

### API Error Handling Pattern

**Purpose**: Consistent handling of API responses and errors.

**Pattern**:
```r
# Standard API call with error handling
make_api_call_with_handling <- function(api_func, success_message = NULL, error_message = NULL) {
  tryCatch({
    result <- api_func()
    
    if ("error" %in% names(result)) {
      # Handle API error
      error_msg <- error_message %||% extract_error_message(result)
      show_validation_error_notification(result)
      return(list(success = FALSE, error = error_msg))
    } else {
      # Handle success
      success_msg <- success_message %||% "Operation completed successfully"
      show_success_notification(success_msg)
      return(list(success = TRUE, data = result))
    }
  }, error = function(e) {
    # Handle network/system error
    error_msg <- paste("Network error:", e$message)
    show_error_notification(error_msg)
    return(list(success = FALSE, error = error_msg))
  })
}

# CRUD operation pattern with error handling
perform_crud_operation <- function(operation_type, api_endpoint, data = NULL, entity_id = NULL) {
  switch(operation_type,
    "create" = make_api_call_with_handling(
      api_func = function() crud_operations$create(api_endpoint, data),
      success_message = "Entity created successfully",
      error_message = "Failed to create entity"
    ),
    "update" = make_api_call_with_handling(
      api_func = function() crud_operations$update(api_endpoint, entity_id, data),
      success_message = "Entity updated successfully",
      error_message = "Failed to update entity"
    ),
    "delete" = make_api_call_with_handling(
      api_func = function() crud_operations$delete(api_endpoint, entity_id),
      success_message = "Entity deleted successfully", 
      error_message = "Failed to delete entity"
    ),
    "get" = make_api_call_with_handling(
      api_func = function() crud_operations$get_all(api_endpoint),
      success_message = NULL,  # No notification for data loading
      error_message = "Failed to load entities"
    )
  )
}

# Usage example
observeEvent(input$save_create, {
  if (create_validator$is_valid()) {
    form_data <- list(
      name = input$create_name,
      type = input$create_type
    )
    
    result <- perform_crud_operation("create", api_endpoint, data = form_data)
    
    if (result$success) {
      load_entity_data()  # Refresh data
      removeModal()       # Close modal
    }
    # Error handling is automatic via the pattern
  }
})
```

**Usage**: Use this pattern for all API interactions to ensure consistent error handling and user feedback.

---

## WebSocket Integration Patterns

### Universal CRUD Manager Pattern (Recommended)

**Purpose**: Streamlined WebSocket event handling with automatic module routing.

**Pattern**:
```r
# Module server integration
entity_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    
    # Data loading function
    load_entity_data <- function() {
      # API call to refresh data
      result <- crud_operations$get_all(api_endpoint)
      if (!"error" %in% names(result)) {
        entity_data(result)
      }
    }
    
    # Universal CRUD Manager observer
    setup_universal_crud_observer(
      input = input,
      load_data_func = load_entity_data,
      module_name = "entity",
      debug = TRUE
    )
    
    # Alternative manual observer (same effect)
    observeEvent(input$crud_refresh, {
      if (!is.null(input$crud_refresh)) {
        cat("🔄 Entity refresh triggered\n")
        load_entity_data()
      }
    })
  })
}
```

**JavaScript WebSocket Client Integration**:
```javascript
// In websocket_client.js
class WebSocketClient {
  handleMessage(event) {
    const data = JSON.parse(event.data);
    console.log('📨 WebSocket message received:', data.type);
    
    // Universal CRUD Manager routing
    if (this.shouldRouteToUniversalCRUD(data.type)) {
      this.notifyUniversalCRUDManager(data);
    }
  }
  
  shouldRouteToUniversalCRUD(eventType) {
    // Route entity events to Universal CRUD Manager
    const universalPatterns = [
      'entity_created', 'entity_updated', 'entity_deleted',
      'package_item_', 'tracker_', 'comment_'
    ];
    
    return universalPatterns.some(pattern => eventType.startsWith(pattern));
  }
  
  notifyUniversalCRUDManager(data) {
    if (window.Shiny && window.Shiny.setInputValue) {
      console.log('🎯 Routing to Universal CRUD Manager');
      Shiny.setInputValue('crud_refresh', Math.random(), {priority: 'event'});
    }
  }
}
```

**Usage**: Use this pattern for all new modules as it provides the simplest and most consistent WebSocket integration.

---

### Legacy WebSocket Pattern (For Reference)

**Purpose**: Legacy pattern using global observers and custom messages (being phased out).

**Pattern**:
```r
# Global observer in app.R
observeEvent(input$`entity_update-websocket_event`, {
  if (!is.null(input$`entity_update-websocket_event`)) {
    event_data <- input$`entity_update-websocket_event`
    session$sendCustomMessage("triggerEntityRefresh", list(
      timestamp = as.numeric(Sys.time()),
      event_type = event_data$type
    ))
  }
})

# Custom message handler in JavaScript
Shiny.addCustomMessageHandler('triggerEntityRefresh', function(message) {
  if (window.Shiny && window.Shiny.setInputValue) {
    Shiny.setInputValue('entity_module-crud_refresh', Math.random(), {priority: 'event'});
  }
});

# Module observer
observeEvent(input$`entity_module-crud_refresh`, {
  if (!is.null(input$`entity_module-crud_refresh`)) {
    load_entity_data()
  }
})
```

**Usage**: Don't use this pattern for new development. It's documented here for understanding existing code that may need maintenance.

---

## Database Interaction Patterns

### Transaction Management Pattern

**Purpose**: Proper handling of database transactions for complex operations.

**Pattern**:
```python
# Pattern 1: Automatic transaction (recommended for simple operations)
async def simple_crud_operation(db: AsyncSession):
    """Simple CRUD operation with automatic transaction management."""
    # Each CRUD method handles its own transaction
    created_entity = await entity_crud.create(db, obj_in=entity_data)
    # Transaction is automatically committed
    return created_entity

# Pattern 2: Manual transaction (for complex operations)
async def complex_operation(db: AsyncSession):
    """Complex operation requiring manual transaction control."""
    try:
        # Multiple operations in single transaction
        study = await study_crud.create(db, obj_in=study_data)
        release = await database_release_crud.create(db, obj_in=release_data)
        effort = await reporting_effort_crud.create(db, obj_in=effort_data)
        
        # Explicit commit
        await db.commit()
        
        return {"study": study, "release": release, "effort": effort}
        
    except Exception as e:
        # Automatic rollback on exception
        await db.rollback()
        raise HTTPException(500, f"Transaction failed: {str(e)}")

# Pattern 3: Nested transaction (for rollback points)
from sqlalchemy import text

async def operation_with_savepoints(db: AsyncSession):
    """Operation using savepoints for partial rollback."""
    try:
        # Main operation
        entity1 = await crud1.create(db, obj_in=data1)
        
        # Create savepoint
        savepoint = await db.begin_nested()
        
        try:
            # Risky operation
            entity2 = await crud2.create(db, obj_in=data2)
            await savepoint.commit()
        except Exception:
            # Rollback to savepoint only
            await savepoint.rollback()
            entity2 = None  # Continue without entity2
        
        # Final commit
        await db.commit()
        
        return {"entity1": entity1, "entity2": entity2}
        
    except Exception as e:
        await db.rollback()
        raise
```

**Usage**: Use automatic transactions for simple CRUD operations, manual transactions for complex multi-step operations, and savepoints when partial rollback is needed.

---

### Relationship Loading Pattern

**Purpose**: Efficient loading of related entities.

**Pattern**:
```python
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select

# Pattern 1: Eager loading with selectinload (for one-to-many)
async def get_study_with_releases(db: AsyncSession, study_id: int):
    """Get study with all database releases loaded."""
    result = await db.execute(
        select(Study)
        .options(selectinload(Study.database_releases))
        .where(Study.id == study_id)
    )
    return result.scalar_one_or_none()

# Pattern 2: Eager loading with joinedload (for many-to-one)
async def get_release_with_study(db: AsyncSession, release_id: int):
    """Get database release with study loaded."""
    result = await db.execute(
        select(DatabaseRelease)
        .options(joinedload(DatabaseRelease.study))
        .where(DatabaseRelease.id == release_id)
    )
    return result.scalar_one_or_none()

# Pattern 3: Nested eager loading
async def get_study_full_hierarchy(db: AsyncSession, study_id: int):
    """Get study with full hierarchy loaded."""
    result = await db.execute(
        select(Study)
        .options(
            selectinload(Study.database_releases)
            .selectinload(DatabaseRelease.reporting_efforts)
            .selectinload(ReportingEffort.reporting_effort_items)
        )
        .where(Study.id == study_id)
    )
    return result.scalar_one_or_none()

# Pattern 4: Lazy loading with separate queries (when needed)
async def get_study_with_lazy_loading(db: AsyncSession, study_id: int):
    """Get study and load relations as needed."""
    study = await study_crud.get(db, id=study_id)
    if not study:
        return None
    
    # Load relations only if needed
    releases = await database_release_crud.get_by_study_id(db, study_id=study.id)
    
    return {
        "study": study,
        "releases": releases
    }
```

**Usage**: Use eager loading for data that's always needed together, lazy loading when relations are conditionally needed.

---

## Error Handling Patterns

### Comprehensive Error Handling Pattern

**Purpose**: Consistent error handling across the application with proper logging and user feedback.

**Pattern**:
```python
import logging
from typing import Any, Dict
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling for the application."""
    
    @staticmethod
    def handle_database_error(e: Exception, operation: str, entity_type: str) -> HTTPException:
        """Handle database-related errors."""
        logger.error(f"Database error in {operation} {entity_type}: {str(e)}")
        
        if isinstance(e, IntegrityError):
            error_msg = str(e.orig)
            
            if "unique constraint" in error_msg.lower():
                return HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A {entity_type.lower()} with this information already exists"
                )
            elif "foreign key constraint" in error_msg.lower():
                return HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Referenced record does not exist"
                )
            elif "not null constraint" in error_msg.lower():
                return HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Required field is missing"
                )
            else:
                return HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Database constraint violation"
                )
        
        elif isinstance(e, SQLAlchemyError):
            return HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error occurred"
            )
        
        else:
            return HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error in {operation} {entity_type}"
            )
    
    @staticmethod
    def handle_business_logic_error(message: str, status_code: int = 400) -> HTTPException:
        """Handle business logic errors."""
        logger.warning(f"Business logic error: {message}")
        return HTTPException(status_code=status_code, detail=message)
    
    @staticmethod
    def handle_not_found_error(entity_type: str, entity_id: Any) -> HTTPException:
        """Handle entity not found errors."""
        logger.info(f"{entity_type} not found: {entity_id}")
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_type} with ID {entity_id} not found"
        )

# Usage in endpoints
@router.post("/", response_model=Entity)
async def create_entity(entity_data: EntityCreate, db: AsyncSession = Depends(get_db)):
    try:
        created_entity = await entity_crud.create(db, obj_in=entity_data)
        return created_entity
    except Exception as e:
        raise ErrorHandler.handle_database_error(e, "creating", "Entity")

# Decorator pattern for automatic error handling
from functools import wraps

def handle_errors(entity_type: str):
    """Decorator for automatic error handling in endpoints."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise  # Re-raise HTTP exceptions
            except Exception as e:
                operation = func.__name__.replace("_", " ")
                raise ErrorHandler.handle_database_error(e, operation, entity_type)
        return wrapper
    return decorator

# Usage with decorator
@router.post("/")
@handle_errors("Entity")
async def create_entity(entity_data: EntityCreate, db: AsyncSession = Depends(get_db)):
    return await entity_crud.create(db, obj_in=entity_data)
```

**Frontend Error Handling Pattern**:
```r
# Comprehensive error handling in R
handle_api_error <- function(result, operation = "operation", entity_type = "item") {
  if ("error" %in% names(result)) {
    error_message <- extract_error_message(result)
    
    # Log error for debugging
    cat("❌ API Error in", operation, entity_type, ":", error_message, "\n")
    
    # Categorize error types
    if (grepl("already exists|duplicate", error_message, ignore.case = TRUE)) {
      show_validation_error_notification(result, duration = 6000)
    } else if (grepl("not found|404", error_message, ignore.case = TRUE)) {
      show_error_notification(paste(entity_type, "not found. It may have been deleted."))
    } else if (grepl("network error|timeout", error_message, ignore.case = TRUE)) {
      show_error_notification("Network error. Please check your connection and try again.")
    } else {
      show_error_notification(paste("Error:", error_message))
    }
    
    return(FALSE)
  }
  return(TRUE)
}

# Usage in module
observeEvent(input$save_entity, {
  if (validator$is_valid()) {
    result <- crud_operations$create(api_endpoint, form_data)
    
    success <- handle_api_error(result, "creating", "entity")
    if (success) {
      show_success_notification("Entity created successfully")
      load_entity_data()
      removeModal()
    }
  }
})
```

**Usage**: Use these patterns to ensure consistent error handling across both backend and frontend components.

---

## Validation Patterns

### Backend Validation Pattern

**Purpose**: Comprehensive validation with custom business logic.

**Pattern**:
```python
from pydantic import BaseModel, validator, root_validator
from typing import Optional
import re

class EntityCreate(BaseModel):
    name: str
    email: Optional[str] = None
    type: str
    status: str = "ACTIVE"
    
    @validator('name')
    def validate_name(cls, v):
        """Validate name field."""
        if not v or len(v.strip()) < 3:
            raise ValueError('Name must be at least 3 characters long')
        
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Name contains invalid characters')
        
        return v.strip()
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email field."""
        if v is None:
            return v
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        
        return v.lower()
    
    @validator('type')
    def validate_type(cls, v):
        """Validate type field."""
        allowed_types = ['TYPE1', 'TYPE2', 'TYPE3']
        if v not in allowed_types:
            raise ValueError(f'Type must be one of: {", ".join(allowed_types)}')
        
        return v
    
    @root_validator
    def validate_business_rules(cls, values):
        """Validate business logic rules."""
        name = values.get('name')
        entity_type = values.get('type')
        
        # Business rule: TYPE1 entities must have specific naming
        if entity_type == 'TYPE1' and name and not name.startswith('SPECIAL_'):
            raise ValueError('TYPE1 entities must have names starting with "SPECIAL_"')
        
        return values

# Custom validation in CRUD operations
class EntityCRUD(BaseCRUD):
    async def create(self, db: AsyncSession, *, obj_in: EntityCreate) -> Entity:
        """Create with additional validation."""
        
        # Check for business logic constraints
        existing = await self.get_by_name(db, name=obj_in.name)
        if existing:
            raise ValueError(f"Entity with name '{obj_in.name}' already exists")
        
        # Check related entity constraints
        if obj_in.parent_id:
            parent = await parent_crud.get(db, id=obj_in.parent_id)
            if not parent:
                raise ValueError("Parent entity does not exist")
            
            if parent.status != "ACTIVE":
                raise ValueError("Cannot create entity under inactive parent")
        
        return await super().create(db, obj_in=obj_in)
```

**Frontend Validation Pattern**:
```r
# Comprehensive form validation in R
setup_entity_validation <- function() {
  validator <- InputValidator$new()
  
  # Name validation
  validator$add_rule("name", sv_required())
  validator$add_rule("name", function(value) {
    if (nchar(trimws(value)) < 3) {
      return("Name must be at least 3 characters")
    }
    if (!grepl("^[a-zA-Z0-9\\s\\-_]+$", value)) {
      return("Name contains invalid characters")
    }
    NULL
  })
  
  # Email validation
  validator$add_rule("email", function(value) {
    if (is.null(value) || trimws(value) == "") {
      return(NULL)  # Optional field
    }
    email_pattern <- "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    if (!grepl(email_pattern, value)) {
      return("Invalid email format")
    }
    NULL
  })
  
  # Type validation
  validator$add_rule("type", sv_required())
  validator$add_rule("type", function(value) {
    allowed_types <- c("TYPE1", "TYPE2", "TYPE3")
    if (!value %in% allowed_types) {
      return(paste("Type must be one of:", paste(allowed_types, collapse = ", ")))
    }
    NULL
  })
  
  # Business logic validation
  validator$add_rule("name", function(value) {
    type_value <- input$type  # Access other form fields
    if (!is.null(type_value) && type_value == "TYPE1" && !startsWith(value, "SPECIAL_")) {
      return("TYPE1 entities must have names starting with 'SPECIAL_'")
    }
    NULL
  })
  
  validator$enable()
  return(validator)
}
```

**Usage**: Use these validation patterns to ensure data integrity at both the API level and user interface level.

---

## Testing Patterns

### Backend Testing Pattern

**Purpose**: Consistent testing approach for API endpoints and business logic.

**Pattern**:
```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.db.session import get_db
from app.tests.utils import create_test_user, create_test_entity

class TestEntityEndpoints:
    """Test class for entity endpoints."""
    
    @pytest.fixture
    async def test_entity_data(self):
        """Fixture for test entity data."""
        return {
            "name": "Test Entity",
            "type": "TYPE1",
            "status": "ACTIVE"
        }
    
    async def test_create_entity_success(self, async_client: AsyncClient, test_entity_data: dict):
        """Test successful entity creation."""
        response = await async_client.post("/api/v1/entities/", json=test_entity_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == test_entity_data["name"]
        assert data["type"] == test_entity_data["type"]
        assert "id" in data
        assert "created_at" in data
    
    async def test_create_entity_validation_error(self, async_client: AsyncClient):
        """Test entity creation with validation errors."""
        invalid_data = {
            "name": "",  # Empty name should fail
            "type": "INVALID_TYPE"
        }
        
        response = await async_client.post("/api/v1/entities/", json=invalid_data)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
    
    async def test_get_entity_success(self, async_client: AsyncClient, db: AsyncSession):
        """Test successful entity retrieval."""
        # Create test entity
        test_entity = await create_test_entity(db, name="Test Entity")
        
        response = await async_client.get(f"/api/v1/entities/{test_entity.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_entity.id
        assert data["name"] == test_entity.name
    
    async def test_get_entity_not_found(self, async_client: AsyncClient):
        """Test entity retrieval with non-existent ID."""
        response = await async_client.get("/api/v1/entities/99999")
        
        assert response.status_code == 404
        error_data = response.json()
        assert "not found" in error_data["detail"].lower()
    
    async def test_update_entity_success(self, async_client: AsyncClient, db: AsyncSession):
        """Test successful entity update."""
        test_entity = await create_test_entity(db, name="Original Name")
        
        update_data = {"name": "Updated Name"}
        response = await async_client.put(f"/api/v1/entities/{test_entity.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
    
    async def test_delete_entity_success(self, async_client: AsyncClient, db: AsyncSession):
        """Test successful entity deletion."""
        test_entity = await create_test_entity(db, name="To Delete")
        
        response = await async_client.delete(f"/api/v1/entities/{test_entity.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
    
    async def test_delete_entity_with_dependencies(self, async_client: AsyncClient, db: AsyncSession):
        """Test entity deletion with dependencies."""
        parent_entity = await create_test_entity(db, name="Parent")
        child_entity = await create_test_child(db, parent_id=parent_entity.id)
        
        response = await async_client.delete(f"/api/v1/entities/{parent_entity.id}")
        
        assert response.status_code == 400
        error_data = response.json()
        assert "associated" in error_data["detail"].lower()
```

**Frontend Testing Pattern** (Playwright):
```typescript
// Entity CRUD testing pattern
import { test, expect } from '@playwright/test';

test.describe('Entity Management', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to entity management page
    await page.goto('/entity-management');
    await expect(page.locator('h3')).toContainText('Entity Management');
  });

  test('should create new entity', async ({ page }) => {
    // Click create button
    await page.click('[data-testid="create-entity-btn"]');
    
    // Fill form
    await page.fill('[data-testid="entity-name"]', 'Test Entity');
    await page.selectOption('[data-testid="entity-type"]', 'TYPE1');
    
    // Submit form
    await page.click('[data-testid="save-entity"]');
    
    // Verify success
    await expect(page.locator('.notification.success')).toBeVisible();
    await expect(page.locator('table')).toContainText('Test Entity');
  });

  test('should validate required fields', async ({ page }) => {
    // Click create button
    await page.click('[data-testid="create-entity-btn"]');
    
    // Try to submit without filling required fields
    await page.click('[data-testid="save-entity"]');
    
    // Verify validation errors
    await expect(page.locator('.validation-error')).toBeVisible();
  });

  test('should edit existing entity', async ({ page }) => {
    // Click edit button for first entity
    await page.click('[data-testid="edit-entity"]:first-child');
    
    // Update name
    await page.fill('[data-testid="entity-name"]', 'Updated Entity');
    
    // Save changes
    await page.click('[data-testid="save-entity"]');
    
    // Verify update
    await expect(page.locator('table')).toContainText('Updated Entity');
  });
});
```

**Usage**: Use these testing patterns to ensure comprehensive coverage of both backend API functionality and frontend user interactions.

---

## Performance Patterns

### Database Query Optimization Pattern

**Purpose**: Efficient database queries with proper indexing and loading strategies.

**Pattern**:
```python
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload, contains_eager

class OptimizedEntityCRUD:
    """CRUD class with optimized query patterns."""
    
    async def get_entities_with_counts(self, db: AsyncSession, skip: int = 0, limit: int = 100):
        """Get entities with related counts in single query."""
        result = await db.execute(
            select(
                Entity,
                func.count(RelatedEntity.id).label('related_count')
            )
            .outerjoin(RelatedEntity)
            .group_by(Entity.id)
            .offset(skip)
            .limit(limit)
        )
        return result.all()
    
    async def get_entities_filtered(self, db: AsyncSession, filters: dict):
        """Get entities with dynamic filtering."""
        query = select(Entity)
        
        # Apply filters dynamically
        if filters.get('name'):
            query = query.where(Entity.name.ilike(f"%{filters['name']}%"))
        
        if filters.get('type'):
            query = query.where(Entity.type == filters['type'])
        
        if filters.get('status'):
            query = query.where(Entity.status == filters['status'])
        
        if filters.get('created_after'):
            query = query.where(Entity.created_at >= filters['created_after'])
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_entities_paginated(self, db: AsyncSession, page: int, page_size: int, search: str = None):
        """Get paginated entities with search."""
        # Base query
        query = select(Entity)
        
        # Apply search if provided
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Entity.name.ilike(search_pattern),
                    Entity.description.ilike(search_pattern)
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        entities = result.scalars().all()
        
        return {
            "entities": entities,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    async def bulk_update_status(self, db: AsyncSession, entity_ids: List[int], new_status: str):
        """Efficiently update multiple entities."""
        query = (
            update(Entity)
            .where(Entity.id.in_(entity_ids))
            .values(status=new_status, updated_at=func.now())
        )
        await db.execute(query)
        await db.commit()
```

**Frontend Performance Pattern**:
```r
# Efficient data handling in R Shiny
entity_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # Use debouncing for search to reduce API calls
    search_term <- reactive({
      input$search_input
    }) %>% 
      debounce(500)  # Wait 500ms after user stops typing
    
    # Reactive data with caching
    entities_data <- reactive({
      # Cache key based on search and filters
      cache_key <- paste(search_term(), input$type_filter, input$status_filter, sep = "_")
      
      if (!is.null(entities_cache[[cache_key]])) {
        return(entities_cache[[cache_key]])
      }
      
      # Make API call
      filters <- list()
      if (!is.null(search_term()) && search_term() != "") {
        filters$search <- search_term()
      }
      if (!is.null(input$type_filter) && input$type_filter != "") {
        filters$type <- input$type_filter
      }
      
      result <- get_entities_filtered(filters)
      
      if (!"error" %in% names(result)) {
        entities_cache[[cache_key]] <- result
        return(result)
      } else {
        return(NULL)
      }
    })
    
    # Paginated DataTable
    output$entities_table <- DT::renderDataTable({
      create_standard_datatable(
        entities_data(),
        actions_column = TRUE,
        page_length = 50,  # Larger page size for performance
        extra_options = list(
          deferRender = TRUE,  # Render rows only when visible
          scrollY = "500px",   # Virtual scrolling for large datasets
          scrollCollapse = TRUE
        )
      )
    })
    
    # Batch operations
    observeEvent(input$bulk_update_btn, {
      selected_ids <- input$entities_table_rows_selected
      if (length(selected_ids) > 0) {
        # Process in chunks for large selections
        chunk_size <- 50
        chunks <- split(selected_ids, ceiling(seq_along(selected_ids) / chunk_size))
        
        for (chunk in chunks) {
          bulk_update_entities(chunk, input$new_status)
        }
      }
    })
  })
}
```

**Usage**: Use these patterns when dealing with large datasets or when performance optimization is needed.

---

## Related Documentation

- [API_REFERENCE.md](API_REFERENCE.md) - API endpoints that implement these patterns
- [FRONTEND_MODULES.md](FRONTEND_MODULES.md) - Frontend modules that use these patterns
- [WEBSOCKET_EVENTS.md](WEBSOCKET_EVENTS.md) - WebSocket patterns for real-time updates
- [UTILITY_FUNCTIONS.md](UTILITY_FUNCTIONS.md) - Utility functions that implement common patterns
- [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md) - Naming standards used in these patterns