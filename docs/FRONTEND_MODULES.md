# Frontend Modules Documentation

**PEARL Full-Stack Research Data Management System**  
**R Shiny Modules, Functions, and Patterns**

This document catalogs all R Shiny modules, their functions, API integration patterns, and WebSocket handling for the PEARL system post-Phase 2 implementation.

## Table of Contents

- [Module Architecture](#module-architecture)
- [Core Modules](#core-modules)
- [Utility Modules](#utility-modules)
- [Phase 2 Utility Functions](#phase-2-utility-functions)
- [WebSocket Integration](#websocket-integration)
- [API Client Patterns](#api-client-patterns)
- [Form Validation Patterns](#form-validation-patterns)
- [Modal Dialog Patterns](#modal-dialog-patterns)
- [DataTable Configuration](#datatable-configuration)
- [Environment Configuration](#environment-configuration)

---

## Module Architecture

### Standard Module Structure

All PEARL R Shiny modules follow a consistent pattern:

```
module_name_ui.R        # UI function definitions
module_name_server.R    # Server function definitions (includes API calls)
```

### Module Naming Convention

- **UI Function**: `module_name_ui(id, ...)`
- **Server Function**: `module_name_server(id, ...)`
- **Module ID Pattern**: Use descriptive, snake_case identifiers

### Standard Module Pattern

```r
# module_name_ui.R
module_name_ui <- function(id) {
  ns <- NS(id)
  # UI elements with ns() wrapped IDs
}

# module_name_server.R
module_name_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # Server logic, API calls, observers
  })
}
```

---

## Core Modules

### Admin Dashboard Module

**Files**: 
- `admin-frontend/modules/admin_dashboard_ui.R`
- `admin-frontend/modules/admin_dashboard_server.R`

**Purpose**: Main dashboard with navigation and system overview.

**Key Features**:
- Navigation menu
- System health checks
- User session management
- Quick access to all modules

**UI Components**:
```r
admin_dashboard_ui <- function(id) {
  ns <- NS(id)
  tagList(
    # Navigation sidebar
    bslib::sidebar(
      # Menu items
    ),
    # Main content area
    # Status indicators
  )
}
```

**Server Functions**:
```r
admin_dashboard_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # Health check monitoring
    # Navigation handling
    # Session management
  })
}
```

---

### Study Tree Module

**Files**: 
- `admin-frontend/modules/study_tree_ui.R`
- `admin-frontend/modules/study_tree_server.R`

**Purpose**: Hierarchical view of Studies → Database Releases → Reporting Efforts.

**Key Features**:
- Interactive tree structure using `shinyTree`
- Path-based selection to prevent ambiguity
- Real-time updates via WebSocket
- Expand/collapse state management

**API Endpoints Used**:
- `GET /api/v1/studies/` - Load all studies
- `GET /api/v1/database-releases/by-study/{study_id}` - Load releases for study
- `GET /api/v1/reporting-efforts/by-database-release/{db_release_id}` - Load efforts

**WebSocket Events**:
- `study_created`, `study_updated`, `study_deleted`
- `database_release_created`, `database_release_updated`, `database_release_deleted`
- `reporting_effort_created`, `reporting_effort_updated`, `reporting_effort_deleted`

**Key Server Logic**:
```r
study_tree_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # Load hierarchical data
    load_tree_data <- function() {
      # API calls to build tree structure
    }
    
    # Tree selection handler
    observeEvent(input$tree, {
      # Handle node selection with path-based logic
    })
    
    # WebSocket observer (Global Observer pattern)
    observeEvent(input$`study_tree-websocket_event`, {
      # Refresh on relevant events
    })
  })
}
```

---

### Users Module

**Files**: 
- `admin-frontend/modules/users_ui.R`
- `admin-frontend/modules/users_server.R`

**Purpose**: User management with CRUD operations.

**Key Features**:
- User listing with DataTable
- Create/Edit/Delete modals
- Role-based access control
- Bulk upload from Excel
- Form validation with `shinyvalidate`

**API Endpoints Used**:
- `GET /api/v1/users/` - List all users
- `POST /api/v1/users/` - Create new user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

**WebSocket Events**:
- `user_created`, `user_updated`, `user_deleted`

**Key Server Logic**:
```r
users_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # Data loading
    load_users_data <- function() {
      # API call to get users
    }
    
    # Create user modal
    observeEvent(input$create_user_btn, {
      showModal(create_user_modal())
    })
    
    # Form validation setup
    create_validator <- InputValidator$new()
    create_validator$add_rule("username", sv_required())
    
    # WebSocket observer (Global Observer pattern)
    observeEvent(input$`users-websocket_event`, {
      # Refresh on user events
    })
  })
}
```

---

### Packages Module

**Files**: 
- `admin-frontend/modules/packages_ui.R`
- `admin-frontend/modules/packages_server.R`

**Purpose**: Package management with CRUD operations.

**Key Features**:
- Package listing with search/filter
- Create/Edit/Delete operations
- Package item associations
- Export to Excel functionality

**API Endpoints Used**:
- `GET /api/v1/packages/` - List all packages
- `POST /api/v1/packages/` - Create new package
- `PUT /api/v1/packages/{id}` - Update package
- `DELETE /api/v1/packages/{id}` - Delete package

**WebSocket Events**:
- `package_created`, `package_updated`, `package_deleted`

**Cross-Browser Sync**: Uses Global Observer pattern (legacy implementation)

---

### Package Items Module

**Files**: 
- `admin-frontend/modules/package_items_ui.R`
- `admin-frontend/modules/package_items_server.R`

**Purpose**: Individual package item management.

**Key Features**:
- Item listing with filtering by package
- TLF/Dataset polymorphic handling
- Bulk operations
- Real-time cross-browser synchronization

**API Endpoints Used**:
- `GET /api/v1/package-items/` - List all items
- `GET /api/v1/package-items/by-package/{package_id}` - Items for package
- `POST /api/v1/package-items/` - Create new item
- `PUT /api/v1/package-items/{id}` - Update item
- `DELETE /api/v1/package-items/{id}` - Delete item

**WebSocket Events**:
- `package_item_created`, `package_item_updated`, `package_item_deleted`

**Cross-Browser Sync**: Uses Universal CRUD Manager (recommended implementation)

**Key Server Logic**:
```r
package_items_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # Load package items data
    load_package_items_data <- function() {
      # API call with package filtering
    }
    
    # Universal CRUD Manager observer
    observeEvent(input$crud_refresh, {  # ⚠️ NO module prefix!
      if (!is.null(input$crud_refresh)) {
        load_package_items_data()
      }
    })
  })
}
```

---

### Reporting Effort Items Module

**Files**: 
- `admin-frontend/modules/reporting_effort_items_ui.R`
- `admin-frontend/modules/reporting_effort_items_server.R`

**Purpose**: Reporting effort item management.

**Key Features**:
- Item listing filtered by reporting effort
- Status tracking
- Item type management (TLF/Dataset)
- Integration with tracker system

**API Endpoints Used**:
- `GET /api/v1/reporting-effort-items/` - List all items
- `GET /api/v1/reporting-effort-items/by-reporting-effort/{effort_id}` - Items for effort
- `POST /api/v1/reporting-effort-items/` - Create item
- `PUT /api/v1/reporting-effort-items/{id}` - Update item
- `DELETE /api/v1/reporting-effort-items/{id}` - Delete item

**WebSocket Events**:
- `reporting_effort_item_created`, `reporting_effort_item_updated`, `reporting_effort_item_deleted`

---

### Reporting Effort Tracker Module

**Files**: 
- `admin-frontend/modules/reporting_effort_tracker_ui.R`
- `admin-frontend/modules/reporting_effort_tracker_server.R`

**Purpose**: Tracker management with programmer assignments and comments.

**Key Features**:
- Tracker listing with status indicators
- Primary/QC programmer assignment
- Status updates (NOT_STARTED, IN_PROGRESS, COMPLETED)
- Comment system integration
- Real-time cross-browser synchronization

**API Endpoints Used**:
- `GET /api/v1/reporting-effort-tracker/` - List all trackers
- `POST /api/v1/reporting-effort-tracker/` - Create tracker
- `PUT /api/v1/reporting-effort-tracker/{id}` - Update tracker
- `DELETE /api/v1/reporting-effort-tracker/{id}` - Delete tracker
- `PUT /api/v1/reporting-effort-tracker/{id}/assign-primary/{programmer_id}` - Assign primary
- `PUT /api/v1/reporting-effort-tracker/{id}/assign-qc/{programmer_id}` - Assign QC
- `GET /api/v1/tracker-comments/by-tracker/{tracker_id}` - Get comments

**WebSocket Events**:
- `reporting_effort_tracker_updated`, `reporting_effort_tracker_deleted`
- `tracker_assignment_updated`
- `comment_created`, `comment_replied`, `comment_resolved`

**Cross-Browser Sync**: Uses Universal CRUD Manager

**Key Server Logic**:
```r
reporting_effort_tracker_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # Load tracker data
    load_tracker_data <- function() {
      # API calls for trackers and comments
    }
    
    # Comment system integration
    observeEvent(input$add_comment_btn, {
      # Show comment modal
    })
    
    # Universal CRUD Manager observer
    observeEvent(input$crud_refresh, {
      if (!is.null(input$crud_refresh)) {
        load_tracker_data()
      }
    })
  })
}
```

---

### TNFP (Text Elements) Module

**Files**: 
- `admin-frontend/modules/tnfp_ui.R`
- `admin-frontend/modules/tnfp_server.R`

**Purpose**: Text element management (Titles, Notes, Footnotes, Populations).

**Key Features**:
- Multi-tab interface for different text element types
- Rich text editing
- Search and filter capabilities
- Import/export functionality

**API Endpoints Used**:
- `GET /api/v1/text-elements/` - List all elements
- `GET /api/v1/text-elements/by-type/{type}` - Elements by type
- `POST /api/v1/text-elements/` - Create element
- `PUT /api/v1/text-elements/{id}` - Update element
- `DELETE /api/v1/text-elements/{id}` - Delete element

**WebSocket Events**:
- `text_element_created`, `text_element_updated`, `text_element_deleted`

**Text Element Types**:
- `TITLE` - Table/Figure titles
- `FOOTNOTE` - Table/Figure footnotes
- `POPULATION_SET` - Analysis population definitions
- `ACRONYMS_SET` - Acronym definitions

---

### Database Backup Module

**Files**: 
- `admin-frontend/modules/database_backup_ui.R`
- `admin-frontend/modules/database_backup_server.R`

**Purpose**: Database backup operations.

**Key Features**:
- Create new backups
- List existing backups
- Download backup files
- Backup scheduling (future feature)

**API Endpoints Used**:
- `POST /api/v1/database-backup/` - Create backup
- `GET /api/v1/database-backup/list` - List backups

---

### Audit Trail Module

**Files**: 
- `admin-frontend/modules/audit_trail_ui.R`
- `admin-frontend/modules/audit_trail_server.R`

**Purpose**: System audit trail viewing.

**Key Features**:
- Filterable audit log display
- Export audit data
- Search by entity, user, action, date range
- Real-time updates

**API Endpoints Used**:
- `GET /api/v1/audit-trail/` - Get audit logs with filtering

---

## Utility Modules

### API Client Module

**File**: `admin-frontend/modules/api_client.R`

**Purpose**: Centralized API client functions for all modules.

**Key Functions**:

#### Environment-based Endpoint URLs
```r
get_api_endpoint <- function(endpoint_env_var, default_path) {
  base_url <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  path <- Sys.getenv(endpoint_env_var, default_path)
  paste0(base_url, path)
}

# Usage examples
users_endpoint <- get_api_endpoint("PEARL_USERS_ENDPOINT", "/api/v1/users")
studies_endpoint <- get_api_endpoint("PEARL_STUDIES_ENDPOINT", "/api/v1/studies")
```

#### Standard CRUD Operations
```r
# Generic CRUD functions used by all modules
get_entities <- function(endpoint, skip = 0, limit = 100)
get_entity_by_id <- function(endpoint, id)
create_entity <- function(endpoint, data)
update_entity <- function(endpoint, id, data)
delete_entity <- function(endpoint, id)
```

#### Specialized API Functions
```r
# Study-specific functions
get_studies <- function()
create_study <- function(study_data)
update_study <- function(study_id, study_data)
delete_study <- function(study_id)

# User-specific functions  
get_users <- function()
create_user <- function(user_data)
update_user <- function(user_id, user_data)
delete_user <- function(user_id)

# Package-specific functions
get_packages <- function()
get_package_items_by_package <- function(package_id)
create_package <- function(package_data)

# Reporting effort functions
get_reporting_effort_trackers <- function()
assign_primary_programmer <- function(tracker_id, programmer_id)
assign_qc_programmer <- function(tracker_id, programmer_id)

# Comment system functions
get_tracker_comments <- function(tracker_id)
create_comment <- function(comment_data)
reply_to_comment <- function(parent_id, reply_data)
resolve_comment <- function(comment_id)
```

### WebSocket Client Module

**File**: `admin-frontend/modules/websocket_client.R`

**Purpose**: R-based WebSocket client (secondary to JavaScript client).

**Key Functions**:
```r
websocket_client_ui <- function(id) {
  ns <- NS(id)
  # WebSocket connection status UI
}

websocket_client_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # R WebSocket handling (fallback/debugging)
    # Connection status monitoring
    # Event logging
  })
}
```

---

## Phase 2 Utility Functions

### CRUD Base Utilities

**File**: `admin-frontend/modules/utils/crud_base.R`

**Purpose**: Common patterns for form validation, API calls, and DataTable configuration.

#### Standard DataTable Configuration
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
  # Comprehensive DataTable setup with consistent styling
  # Handles empty data cases
  # Configurable options for different use cases
}
```

#### Form Validation Patterns
```r
# Enhanced validation setup with common patterns
setup_enhanced_form_validation <- function(input_validator, validation_config) {
  # validation_config format:
  # list(
  #   field_id = list(type = "text", required = TRUE, min_length = 3),
  #   email_field = list(type = "email", required = FALSE),
  #   role_field = list(type = "dropdown", required = TRUE, choices = c("ADMIN", "EDITOR"))
  # )
}

# Standard validation functions
validate_required_text_input <- function(input_value, field_name, min_length = 1)
validate_numeric_input <- function(input_value, field_name, min_value = 0, max_value = NULL)
validate_email_input <- function(input_value, field_name)
validate_dropdown_selection <- function(input_value, field_name, valid_choices = NULL)
```

#### Modal Dialog Standardization
```r
# Standard edit modal for entity CRUD operations
create_edit_modal <- function(title, content, size = "m", save_button_id, cancel_button_id = NULL)

# Standard create modal for new entities
create_create_modal <- function(title, content, size = "m", save_button_id, cancel_button_id = NULL)

# Standard delete confirmation modal with enhanced warning
create_delete_confirmation_modal <- function(entity_type, entity_name, confirm_button_id)

# Standard bulk upload modal for Excel/CSV files
create_bulk_upload_modal <- function(upload_type, file_input_id, template_download_id, process_button_id)

# Standard export completion modal
create_export_modal <- function(filename, download_button_id, entity_type = "data")
```

#### WebSocket Observer Consolidation
```r
# Enhanced WebSocket observer setup that replaces all legacy patterns
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
      # Handle legacy WebSocket events
    })
  }
}

# Simplified WebSocket observer for modules using Universal CRUD Manager only
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
```

### API Utilities

**File**: `admin-frontend/modules/utils/api_utils.R`

**Purpose**: Standardized HTTP client operations with error handling.

#### Standard API Client
```r
make_api_request <- function(url, method = "GET", body = NULL, timeout = 30) {
  # Comprehensive HTTP client with error handling
  # Supports GET, POST, PUT, DELETE methods
  # JSON request/response handling
  # Timeout management
}

# Convenience functions
api_get <- function(url, timeout = 30)
api_post <- function(url, data, timeout = 30)
api_put <- function(url, data, timeout = 30)
api_delete <- function(url, timeout = 30)
```

#### CRUD Operations Helper
```r
crud_operations <- list(
  get_all = function(endpoint, skip = 0, limit = 100),
  get_by_id = function(endpoint, id),
  create = function(endpoint, data),
  update = function(endpoint, id, data),
  delete = function(endpoint, id),
  search = function(endpoint, query)
)
```

#### Notification Standardization
```r
# Standard notification functions
show_success_notification <- function(message, duration = 3000)
show_error_notification <- function(message, duration = 5000)
show_warning_notification <- function(message, duration = 4000)

# Enhanced validation error notification for API responses
show_validation_error_notification <- function(api_result, duration = 8000)

# Standard operation notification with entity context
show_operation_notification <- function(operation, entity, success = TRUE, entity_name = NULL)
```

#### Error Handling
```r
# Helper to extract error messages from API responses
extract_error_message <- function(api_result) {
  # Handles different error response formats
  # Extracts user-friendly messages from HTTP errors
  # JSON parsing with fallbacks
}

# Helper to show API response notifications
show_api_notification <- function(api_result, success_message = "Operation completed successfully") {
  # Combined error/success notification handling
}
```

---

## WebSocket Integration

### Two Approaches for Cross-Browser Synchronization

#### Approach A: Universal CRUD Manager (Recommended)
**Used by**: Package Items, Trackers (newer implementation)

**Module Implementation**:
```r
# In module server function
observeEvent(input$crud_refresh, {  # ⚠️ NO module prefix!
  if (!is.null(input$crud_refresh)) {
    load_data()  # Refresh the data
  }
})
```

**Advantages**:
- Automatic, no extra configuration needed
- Simpler code maintenance
- Consistent pattern across modules

#### Approach B: Global Observer + Custom Messages (Legacy)
**Used by**: Packages, Studies, Users (legacy implementation)

**Module Implementation**:
```r
# In module server function
observeEvent(input$`module_name-crud_refresh`, {  # ⚠️ FULL name in observer!
  if (!is.null(input$`module_name-crud_refresh`)) {
    load_data()
  }
})
```

**Note**: Requires additional JavaScript handlers and global observers in `app.R`.

### WebSocket Event Handling Pattern

```r
# Standard pattern for modules with WebSocket integration
moduleServer(id, function(input, output, session) {
  # Data loading function
  load_data <- function() {
    # API calls to refresh module data
  }
  
  # Initial data load
  load_data()
  
  # WebSocket observer (choose one approach)
  
  # Option 1: Universal CRUD Manager (recommended)
  observeEvent(input$crud_refresh, {
    if (!is.null(input$crud_refresh)) {
      load_data()
    }
  })
  
  # Option 2: Module-specific observer (legacy)
  observeEvent(input$`module_name-websocket_event`, {
    if (!is.null(input$`module_name-websocket_event`)) {
      event_data <- input$`module_name-websocket_event`
      if (event_data$type %in% c("entity_created", "entity_updated", "entity_deleted")) {
        load_data()
      }
    }
  })
})
```

---

## API Client Patterns

### Standard API Call Pattern

```r
# Standard pattern for API calls in modules
make_api_call <- function(endpoint, method = "GET", data = NULL) {
  tryCatch({
    if (method == "GET") {
      result <- api_get(endpoint)
    } else if (method == "POST") {
      result <- api_post(endpoint, data)
    } else if (method == "PUT") {
      result <- api_put(endpoint, data)
    } else if (method == "DELETE") {
      result <- api_delete(endpoint)
    }
    
    if ("error" %in% names(result)) {
      show_error_notification(extract_error_message(result))
      return(NULL)
    }
    
    return(result)
  }, error = function(e) {
    show_error_notification(paste("Network error:", e$message))
    return(NULL)
  })
}
```

### Environment-based Configuration

```r
# All modules use environment variables for API endpoints
# This allows easy configuration changes without code modifications

# Example configuration in config.env
PEARL_API_URL=http://localhost:8000
PEARL_STUDIES_ENDPOINT=/api/v1/studies
PEARL_USERS_ENDPOINT=/api/v1/users
PEARL_PACKAGES_ENDPOINT=/api/v1/packages

# Usage in modules
studies_endpoint <- Sys.getenv("PEARL_STUDIES_ENDPOINT", "/api/v1/studies")
api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
full_endpoint <- paste0(api_base, studies_endpoint)
```

---

## Form Validation Patterns

### Deferred Validation Pattern

All PEARL modules use deferred validation - validation only triggers when Save/Create buttons are clicked, not on every input change.

```r
# Standard validation setup
setup_form_validation <- function() {
  validator <- InputValidator$new()
  
  # Add validation rules
  validator$add_rule("username", sv_required())
  validator$add_rule("username", function(value) {
    if (nchar(value) < 3) "Username must be at least 3 characters"
  })
  
  # Enable deferred validation
  validator$enable()
  
  return(validator)
}

# Validation trigger on save
observeEvent(input$save_btn, {
  if (validator$is_valid()) {
    # Process form submission
    submit_form()
  } else {
    # Validation errors are automatically displayed
    show_error_notification("Please correct the form errors")
  }
})
```

### Enhanced Validation Configuration

```r
# Configuration-driven validation setup
validation_config <- list(
  username = list(type = "text", required = TRUE, min_length = 3),
  email = list(type = "email", required = FALSE),
  role = list(type = "dropdown", required = TRUE, choices = c("ADMIN", "ANALYST", "VIEWER")),
  department = list(type = "text", required = FALSE)
)

validator <- InputValidator$new()
validator <- setup_enhanced_form_validation(validator, validation_config)
```

---

## Modal Dialog Patterns

### Standard Modal Types

#### Create Modal
```r
show_create_modal <- function() {
  showModal(
    create_create_modal(
      title = "Create New User",
      content = tagList(
        create_text_input_field("username", "Username", required = TRUE),
        create_select_input_field("role", "Role", choices = role_choices, required = TRUE),
        create_text_input_field("department", "Department")
      ),
      save_button_id = "create_user_save"
    )
  )
}
```

#### Edit Modal
```r
show_edit_modal <- function(user_data) {
  showModal(
    create_edit_modal(
      title = paste("Edit User:", user_data$username),
      content = tagList(
        create_text_input_field("username", "Username", value = user_data$username, required = TRUE),
        create_select_input_field("role", "Role", choices = role_choices, selected = user_data$role, required = TRUE),
        create_text_input_field("department", "Department", value = user_data$department)
      ),
      save_button_id = "edit_user_save"
    )
  )
}
```

#### Delete Confirmation Modal
```r
show_delete_modal <- function(user_data) {
  showModal(
    create_delete_confirmation_modal(
      entity_type = "User",
      entity_name = user_data$username,
      confirm_button_id = "confirm_delete_user",
      additional_info = tagList(
        tags$p("Role:", user_data$role),
        tags$p("Department:", user_data$department)
      )
    )
  )
}
```

---

## DataTable Configuration

### Standard DataTable Pattern

```r
# Standard DataTable configuration used across all modules
output$data_table <- DT::renderDataTable({
  if (is.null(data()) || nrow(data()) == 0) {
    # Handle empty data case
    empty_data <- data.frame(Message = "No data available")
    return(create_standard_datatable(empty_data, actions_column = FALSE))
  }
  
  # Prepare data with actions column
  display_data <- data()
  display_data$Actions <- sapply(1:nrow(display_data), function(i) {
    generate_action_buttons(display_data[i, ]$id)
  })
  
  create_standard_datatable(
    display_data,
    actions_column = TRUE,
    search_placeholder = "Search users (regex supported):",
    page_length = 25,
    draw_callback = JS("function(settings) { bindActionButtons(); }")
  )
})
```

### DataTable with Custom Features

```r
# Enhanced DataTable with filtering and custom columns
create_custom_datatable <- function(data, module_type = "default") {
  extra_options <- list()
  
  if (module_type == "tracker") {
    # Tracker-specific configuration
    extra_options$columnDefs <- list(
      list(targets = c("Status"), render = JS("function(data, type, row) {
        return '<span class=\"badge badge-' + data.toLowerCase() + '\">' + data + '</span>';
      }"))
    )
  }
  
  create_standard_datatable(
    data,
    actions_column = TRUE,
    extra_options = extra_options
  )
}
```

---

## Environment Configuration

### Configuration File Pattern

**File**: `admin-frontend/config.env`

```bash
# API Configuration
PEARL_API_URL=http://localhost:8000
PEARL_WEBSOCKET_URL=ws://localhost:8000

# API Endpoints
PEARL_STUDIES_ENDPOINT=/api/v1/studies
PEARL_USERS_ENDPOINT=/api/v1/users
PEARL_PACKAGES_ENDPOINT=/api/v1/packages
PEARL_PACKAGE_ITEMS_ENDPOINT=/api/v1/package-items
PEARL_TRACKERS_ENDPOINT=/api/v1/reporting-effort-tracker
PEARL_COMMENTS_ENDPOINT=/api/v1/tracker-comments
PEARL_TEXT_ELEMENTS_ENDPOINT=/api/v1/text-elements

# Feature Flags
PEARL_ENABLE_WEBSOCKET=true
PEARL_ENABLE_AUDIT_LOGGING=true
PEARL_DEBUG_MODE=false
```

### Environment Loading

```r
# Standard environment loading in app.R
load_environment <- function() {
  if (file.exists("config.env")) {
    readRenviron("config.env")
    cat("✅ Loaded configuration from config.env\n")
  } else {
    cat("⚠️ config.env not found, using defaults\n")
  }
}

# Usage in modules
api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
enable_websocket <- Sys.getenv("PEARL_ENABLE_WEBSOCKET", "true") == "true"
debug_mode <- Sys.getenv("PEARL_DEBUG_MODE", "false") == "true"
```

---

## Common Module Patterns

### Standard Module Server Structure

```r
module_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # 1. Reactive data storage
    data <- reactiveVal(NULL)
    selected_item <- reactiveVal(NULL)
    
    # 2. API endpoint configuration
    api_endpoint <- Sys.getenv("MODULE_ENDPOINT", "/api/v1/default")
    
    # 3. Data loading function
    load_data <- function() {
      result <- api_get(paste0(Sys.getenv("PEARL_API_URL", "http://localhost:8000"), api_endpoint))
      if (!"error" %in% names(result)) {
        data(result)
      } else {
        show_error_notification("Failed to load data")
      }
    }
    
    # 4. Initial data load
    load_data()
    
    # 5. DataTable output
    output$data_table <- DT::renderDataTable({
      create_standard_datatable(data(), actions_column = TRUE)
    })
    
    # 6. Action button handlers
    observeEvent(input$create_btn, {
      show_create_modal()
    })
    
    # 7. Form submission handlers
    observeEvent(input$save_create, {
      # Validation and API call
    })
    
    # 8. WebSocket observer
    observeEvent(input$crud_refresh, {
      if (!is.null(input$crud_refresh)) {
        load_data()
      }
    })
  })
}
```

### Error Handling Pattern

```r
# Standard error handling in modules
handle_api_operation <- function(operation_func, success_message = NULL, error_message = NULL) {
  tryCatch({
    result <- operation_func()
    
    if ("error" %in% names(result)) {
      error_msg <- error_message %||% extract_error_message(result)
      show_error_notification(error_msg)
      return(FALSE)
    } else {
      success_msg <- success_message %||% "Operation completed successfully"
      show_success_notification(success_msg)
      load_data()  # Refresh data
      removeModal()  # Close modal if open
      return(TRUE)
    }
  }, error = function(e) {
    show_error_notification(paste("Unexpected error:", e$message))
    return(FALSE)
  })
}

# Usage example
observeEvent(input$save_user, {
  handle_api_operation(
    operation_func = function() {
      api_post(users_endpoint, get_form_data())
    },
    success_message = "User created successfully",
    error_message = "Failed to create user"
  )
})
```

---

## Testing Patterns

### Module Testing Strategy

Each module should be testable in isolation:

```r
# Test helper function
test_module <- function(module_name) {
  # Load module in isolation
  source(paste0("modules/", module_name, "_ui.R"))
  source(paste0("modules/", module_name, "_server.R"))
  
  # Create test app
  ui <- fluidPage(
    get(paste0(module_name, "_ui"))("test")
  )
  
  server <- function(input, output, session) {
    get(paste0(module_name, "_server"))("test")
  }
  
  shinyApp(ui, server)
}

# Usage
test_module("users")
```

### Integration Testing

```r
# Test WebSocket integration
test_websocket_integration <- function() {
  # Test WebSocket connection
  # Test event handling
  # Test data refresh
}

# Test API integration
test_api_integration <- function() {
  # Test all CRUD operations
  # Test error handling
  # Test timeout handling
}
```

---

## Related Documentation

- [API_REFERENCE.md](API_REFERENCE.md) - FastAPI endpoints used by these modules
- [WEBSOCKET_EVENTS.md](WEBSOCKET_EVENTS.md) - WebSocket events handled by modules
- [CRUD_METHODS.md](CRUD_METHODS.md) - Backend CRUD operations called by API client
- [UTILITY_FUNCTIONS.md](UTILITY_FUNCTIONS.md) - Phase 2 utility functions used by modules
- [CODE_PATTERNS.md](CODE_PATTERNS.md) - Common patterns for reuse across modules