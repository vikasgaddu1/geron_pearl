# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

R Shiny admin frontend for PEARL research data management system. Provides real-time CRUD interface for managing studies, database releases, reporting efforts, packages, and text elements via REST API and WebSocket connections to FastAPI backend.

**Stack**: R Shiny + bslib (Bootstrap 5) + httr2 + DT + shinyvalidate + dual WebSocket clients (JS primary, R secondary)

## Essential Commands

```bash
# First-time setup
Rscript setup_environment.R

# Run application
Rscript run_app.R

# Package management (from R console)
renv::install("package_name")  # Add package
renv::snapshot()               # Save state
renv::restore()                # Restore for new devs

# Debug mode (R console)
options(shiny.reactlog = TRUE)
options(shiny.trace = TRUE)
```

**URLs**: Frontend http://localhost:3838 | Backend http://localhost:8000 | API Docs http://localhost:8000/docs

## Architecture

### Module Pattern
All functionality uses UI/Server module separation:
- `modules/*_ui.R` - Interface components
- `modules/*_server.R` - Business logic + API integration
- `modules/api_client.R` - Centralized HTTP client
- `modules/utils/crud_base.R` - Shared CRUD utilities (DataTable config, modal helpers, validation)
- `www/websocket_client.js` - Primary WebSocket client

### Key Modules
- **study_tree**: Hierarchical Study → Database Release → Reporting Effort (consolidated view)
- **tnfp**: Text elements (title, footnote, population_set, acronyms_set)
- **packages/package_items**: Package registry with TLF/Dataset items
- **reporting_effort_tracker**: Tracker management with comments
- **users**: User management

### Source Order (Critical)
In `app.R`, modules must be sourced in this order:
```r
source("modules/utils/crud_base.R")
source("modules/utils/api_utils.R")
source("modules/websocket_client.R")  # First - provides WEBSOCKET_URL
source("modules/api_client.R")
# Then UI/Server modules...
```

## Critical Constraints

### Environment Variables (Mandatory)
```r
# Correct - dynamic loading
API_BASE_URL <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")

# Wrong - hardcoded URLs break deployment
ENDPOINT <- "http://localhost:8000/api/v1/studies"
```

Required: `PEARL_API_URL`, `PEARL_API_HEALTH_PATH`, `PEARL_API_STUDIES_PATH`, `PEARL_API_WEBSOCKET_PATH`

### Notification Types
```r
# Valid types only: "default", "message", "warning", "error"
showNotification("Success", type = "message")  # Correct
showNotification("Success", type = "success")  # WRONG - causes match.arg error
```

### Deferred Form Validation
```r
iv <- InputValidator$new()
iv$add_rule("field_name", sv_required())

observeEvent(input$save_button, {
  iv$enable()  # Enable only on save
  if (!iv$is_valid()) return()
  # ... save logic ...
  iv$disable()  # Disable after
})
```

### Deletion Protection
Always check for dependent entities before deletion:
```r
releases_result <- get_database_releases()
study_releases <- filter_releases_by_study(releases_result, study_id)
if (length(study_releases) > 0) {
  # Show modal, prevent deletion
}
```

## WebSocket Integration

### Message Flow
1. Backend broadcasts `{type: "entity_action", data: {...}}`
2. JavaScript client detects module from type, routes to `{module}-websocket_event`
3. R module observer triggers and refreshes data

### Cross-Browser Sync (Universal CRUD Manager)
```r
# In module server - NO module prefix (Shiny strips it)
observeEvent(input$crud_refresh, {
  if (!is.null(input$crud_refresh)) {
    load_data()
  }
})
```

### Event Types by Module
- Studies: `study_*`, `studies_update` → `study_tree`
- Database Releases: `database_release_*` → `study_tree`
- Reporting Efforts: `reporting_effort_*` → `study_tree`
- Trackers: `reporting_effort_tracker_*` → `reporting_effort_tracker`
- Text Elements: `text_element_*` → `tnfp`
- Packages: `package_*` → `packages`
- Package Items: `package_item_*` → `package_items`
- Comments: `comment_*` → `reporting_effort_tracker`

## Common Patterns

### DataTable Configuration
Use `create_standard_datatable()` from `crud_base.R`:
```r
create_standard_datatable(
  data,
  actions_column = TRUE,
  search_placeholder = "Search (regex supported):",
  page_length = 25
)
```

### Action Buttons
```r
display_df$Actions <- sapply(items$ID, function(id) {
  sprintf(
    '<button class="btn btn-primary btn-sm me-1" data-action="edit" data-id="%s">
       <i class="bi bi-pencil"></i></button>
     <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s">
       <i class="bi bi-trash"></i></button>',
    id, id
  )
})
```

### Modal Helpers
```r
# From crud_base.R
create_edit_modal(title, content, save_button_id = "save_btn")
create_create_modal(title, content, save_button_id = "create_btn")
create_delete_confirmation_modal(entity_type, entity_name, confirm_button_id)
```

### API Error Handling
```r
api_function <- function() {
  tryCatch({
    response <- httr2::request(url) |> httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}
```

## UI Standards

- **Card Dimensions**: 1200px max-width, 700px height
- **Sidebar Width**: 450px for form sidebars
- **Icons**: Use `bsicons` - `bs_icon("icon-name")`
- **Bootstrap Classes**: Modern BS5 (`d-flex`, `gap-2`, `text-primary`)
- **Dark Mode**: Automatic via `input_dark_mode()`

## Testing

### Manual WebSocket Testing
1. Start backend: `cd ../backend && uv run python run.py`
2. Start frontend: `Rscript run_app.R`
3. Open multiple browser tabs to http://localhost:3838
4. Test CRUD operations, verify real-time sync

### Debugging WebSocket
- Browser console: Check for `📨 WebSocket message received:` logs
- R console: Add `cat()` statements for event tracking
- Network tab: Monitor WebSocket connection and messages

## Study Tree Module

Hierarchical view of Study → Database Release → Reporting Effort using `shinyTree`.

**Selection**: Uses `find_selected_paths()` helper with path-based selection (handles duplicate names).

Node type by depth:
- Depth 1: Study
- Depth 2: Database Release
- Depth 3: Reporting Effort

## TNFP Module

Unified interface for text element types: `title`, `footnote`, `population_set`, `acronyms_set`.

**Duplicate Validation**: Space/case-insensitive checking. "Test Title" == "test title" == "TestTitle".

**API**: Single endpoint `/api/v1/text-elements/` with trailing slash required for collection operations.

## Claude Code Agents

- **rshiny-modern-builder**: R Shiny development with bslib, httr2, WebSocket integration
- **fastapi-crud-builder**: Backend CRUD operations with async PostgreSQL
- **fastapi-model-validator**: Validate Pydantic/SQLAlchemy model alignment
- **fastapi-simple-tester**: curl-based endpoint testing

## Quick Reference

| Task | Command/Pattern |
|------|-----------------|
| Add package | `renv::install("pkg"); renv::snapshot()` |
| Run app | `Rscript run_app.R` |
| Debug | `options(shiny.reactlog = TRUE)` |
| Valid notification types | `"default"`, `"message"`, `"warning"`, `"error"` |
| Module refresh input | `input$crud_refresh` (no prefix in module) |
| Standard DataTable | `create_standard_datatable(data)` |
