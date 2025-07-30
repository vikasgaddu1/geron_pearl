# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **📖 For comprehensive project documentation, features, installation, and usage instructions, see [README.md](README.md)**

## Project Overview

This is the R Shiny admin frontend for the PEARL research data management system. It provides a modern, real-time CRUD interface for managing studies that communicates with the FastAPI backend via REST API and WebSocket connections.

**Key Features**: Real-time WebSocket updates, modern Bootstrap 5 UI, multi-user synchronization
**Technology Stack**: R Shiny + bslib + WebSocket (JavaScript/R dual clients)

## Development Memories

- Read the claude.md and readme.md file to get understanding of the project

### Recent UI Enhancements (Session Context)

#### Database Releases DataTable Improvements
- **Search Box Display Fix**: Changed DOM configuration from 'ft' to 'frtip' to properly display search functionality
- **Duplicate Label Fix**: Set `search = ""` to remove duplicate "Search" labels
- **Enhanced Search**: Added regex search with `search = list(regex = TRUE, caseInsensitive = TRUE)`
- **Column Filtering**: Added `filter = 'top'` for individual column filters on Study Label and Release Label
- **Sorting**: Added sorting by Study ID and Release ID with `releases[order(releases$\`Study ID\`, releases$ID), ]`

#### Study Deletion Validation
- **Frontend Validation**: Added comprehensive check for associated database releases before allowing study deletion
- **User-Friendly Error Messages**: Modal dialog shows specific database releases preventing deletion
- **Integration**: Uses `get_database_releases()` API to check for dependencies
- **Prevention Logic**: Shows informative modal with list of blocking releases instead of allowing deletion

#### Reporting Efforts Implementation
- **New Tab**: Added "Reporting Efforts" tab following Database Releases pattern
- **Clean UI**: Removed redundant filter controls (DataTable column filters are sufficient)
- **Cascading Form**: Study selection in add form filters available database releases
- **API Integration**: Complete CRUD operations with `/api/v1/reporting-efforts` endpoint
- **Enhanced Table**: Displays Study Label, Database Release Label, and Effort Label with regex search
- **Action Buttons**: Edit and Delete buttons with confirmation dialogs (edit is placeholder for now)
- **Empty State**: Proper empty dataframe with helpful message when no records exist

### Key Implementation Patterns

#### DataTable Configuration
```r
DT::datatable(
  display_df,
  filter = 'top',  # Column filters
  options = list(
    dom = 'frtip',   # Proper search box display
    search = list(regex = TRUE, caseInsensitive = TRUE),  # Enhanced search
    searching = TRUE,
    pageLength = 25
  )
)
```

#### Referential Integrity Validation
```r
# Check for dependencies before deletion
releases_result <- get_database_releases()
study_releases <- if (length(releases_result) > 0) {
  releases_for_study <- sapply(releases_result, function(x) x$study_id == study_id)
  releases_result[releases_for_study]
} else {
  list()
}
```

#### Cascading Form Dropdowns (Reporting Efforts)
```r
# Cascading dropdown update based on study selection in add form
update_database_release_choices <- function(selected_study_id = NULL) {
  current_releases <- database_releases_data()
  
  if (!is.null(selected_study_id) && selected_study_id != "") {
    filtered_releases <- current_releases[current_releases$`Study ID` == as.numeric(selected_study_id), ]
  } else {
    filtered_releases <- current_releases
  }
  
  # Update form dropdown with filtered releases
  choices <- setNames(filtered_releases$ID, 
                     paste(filtered_releases$`Release Label`, 
                          "(Study:", filtered_releases$`Study ID`, ")"))
  updateSelectInput(session, "new_database_release_id", 
                   choices = c("Select a database release..." = "", choices))
}

# DataTable with action buttons and empty state handling
output$efforts_table <- DT::renderDataTable({
  current_efforts <- efforts_data()
  
  if (nrow(current_efforts) == 0) {
    # Proper empty dataframe structure
    empty_df <- data.frame(
      `Study Label` = character(0),
      `Database Release Label` = character(0),
      `Effort Label` = character(0),
      `Actions` = character(0),
      stringsAsFactors = FALSE, check.names = FALSE
    )
    
    DT::datatable(empty_df, filter = 'top',
      options = list(
        language = list(emptyTable = "No reporting efforts found. Click 'Add Effort' to create your first reporting effort.")
      ))
  } else {
    # Add action buttons to display dataframe
    display_df$Actions <- sapply(current_efforts$ID, function(effort_id) {
      paste0('<button class="btn btn-primary btn-sm me-1" data-action="edit" data-id="', effort_id, '">',
             '<i class="bi bi-pencil"></i></button>',
             '<button class="btn btn-danger btn-sm" data-action="delete" data-id="', effort_id, '">',
             '<i class="bi bi-trash"></i></button>')
    })
  }
})
```

## Critical Development Constraints

> **🚨 IMPORTANT**: These constraints prevent breaking core functionality

### Environment Variable Integration
- **All URLs MUST use environment variables**: Never hardcode `localhost:8000` or API paths
- **Dynamic Loading Pattern**: Use `Sys.getenv()` with fallbacks in modules, not global variables
- **Correct Variables**: `PEARL_API_URL`, `PEARL_API_HEALTH_PATH`, `PEARL_API_STUDIES_PATH`, `PEARL_API_WEBSOCKET_PATH`

### WebSocket Integration Constraints
- **⚠️ CRITICAL**: Do NOT modify `www/websocket_client.js` message handling without checking backend format
- **Backend Message Format**: `{"type": "study_created", "data": {...}}` - no `module` property
- **Shiny Event Routing**: JavaScript sends to `'studies-websocket_event'`, Shiny receives `input$websocket_event`
- **Required Message Types**: `studies_update`, `study_created`, `study_updated`, `study_deleted`, `refresh_needed`
- **Status Updates**: Go to main app (`'websocket_status'`), not studies module

### Module Integration Rules
- **Source Order Matters**: `websocket_client.R` must be sourced BEFORE other modules that use WebSocket URLs
- **Environment Loading**: Call `load_dot_env()` BEFORE defining any endpoint URLs
- **Self-Contained Modules**: Each module should read environment variables directly, not depend on globals

## Architecture

> **📋 See [README.md - Architecture](README.md#architecture) for detailed file structure and module descriptions**

### Modern R Shiny Stack
- **Framework**: R Shiny with modern bslib Bootstrap 5 theming
- **UI Library**: bslib + bsicons for contemporary design
- **HTTP Client**: httr2 for REST API communication  
- **Real-time**: WebSocket integration (JavaScript primary, R secondary)
- **Package Management**: renv for reproducible environments