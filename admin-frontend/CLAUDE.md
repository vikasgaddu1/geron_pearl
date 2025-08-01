# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **📖 For comprehensive project documentation, features, installation, and usage instructions, see [README.md](README.md)**

## Project Overview

This is the R Shiny admin frontend for the PEARL research data management system. It provides a modern, real-time CRUD interface for managing studies, database releases, reporting efforts, and text elements that communicates with the FastAPI backend via REST API and WebSocket connections.

**Key Features**: Real-time WebSocket updates, modern Bootstrap 5 UI, multi-user synchronization, comprehensive data management
**Technology Stack**: R Shiny + bslib + httr2 + WebSocket (JavaScript/R dual clients) + renv

## Essential Commands

### Environment Setup
```bash
# First-time setup (installs all dependencies with latest versions)
Rscript setup_environment.R

# Restore existing environment (for other developers)
renv::restore()
```

### Running the Application
```bash
# Primary method - using runner script
Rscript run_app.R

# From R console
shiny::runApp(".", port = 3838, host = "0.0.0.0")
```

### Development Commands
```r
# Add new package
renv::install("package_name")
renv::snapshot()

# Update packages
renv::update()
renv::snapshot()

# Enable debugging
options(shiny.reactlog = TRUE)
options(shiny.trace = TRUE)
```

### Environment Configuration
```bash
# Copy template and configure
cp config.env.template .env
# Edit .env with your API endpoints
```

### Testing Commands
```bash
# Test WebSocket real-time updates
cd ../backend && uv run python tests/integration/test_websocket_broadcast.py

# Health check
curl http://localhost:8000/health

# Manual testing: Open multiple browser tabs to http://localhost:3838
```

## Core Architecture

### Module-Based Design Pattern
All functionality follows a strict UI/Server module pattern:
- **UI Module** (`*_ui.R`): Interface components and layout
- **Server Module** (`*_server.R`): Business logic and API integration
- **API Client** (`api_client.R`): Centralized HTTP client functions

### Entity Management Modules
- **Studies** (`studies_*.R`): Core research study management
- **Database Releases** (`database_releases_*.R`): Version control for data releases
- **Reporting Efforts** (`reporting_efforts_*.R`): Reporting workflow management
- **TNFP** (`tnfp_*.R`): Text/Note/Footnote/Population elements (unified interface)

### Real-time WebSocket Architecture
- **Dual Client Design**: JavaScript (primary) + R (secondary) WebSocket clients
- **Message Routing**: Backend broadcasts → JavaScript client → Shiny modules
- **Event Namespacing**: `{module}-websocket_event` pattern for module isolation
- **Auto-reconnection**: Exponential backoff with connection health monitoring

### Technology Integration
- **bslib + Bootstrap 5**: Modern responsive UI with dark mode support
- **httr2**: Modern HTTP client for robust API communication
- **shinyvalidate**: Form validation with real-time feedback
- **DT**: Interactive data tables with search, filtering, and pagination
- **renv**: Reproducible package management

## Critical Development Constraints

### Environment Variable System
**⚠️ MANDATORY**: All API endpoints MUST use environment variables
```r
# Correct pattern - dynamic loading in modules
API_BASE_URL <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")

# Wrong - hardcoded URLs will break deployment
ENDPOINT <- "http://localhost:8000/api/v1/studies"
```

**Required Variables**:
- `PEARL_API_URL`: Base API URL
- `PEARL_API_HEALTH_PATH`, `PEARL_API_STUDIES_PATH`: Endpoint paths
- `PEARL_API_WEBSOCKET_PATH`: WebSocket endpoint path

### Module Source Order Dependencies
Critical file loading sequence in `app.R`:
```r
# MUST be loaded first - provides WEBSOCKET_URL to other modules
source("modules/websocket_client.R")
source("modules/api_client.R")
# Then UI/Server modules...
```

### WebSocket Message Format Constraints
**⚠️ CRITICAL**: Backend and frontend have specific message format expectations

**Backend Sends**:
```json
{"type": "study_created", "data": {...}}
```

**JavaScript Client Processing**:
- Automatically detects module from message type
- Routes to appropriate Shiny module: `{module}-websocket_event`
- **DO NOT** modify `www/websocket_client.js` message handling without verifying backend format

**Event Types by Module**:
- Studies: `study_*`, `studies_update`
- Database Releases: `database_release_*`
- Reporting Efforts: `reporting_effort_*`
- TNFP: `text_element_*`

### Referential Integrity Validation
All deletion operations MUST check for dependencies:
```r
# Example: Check for database releases before deleting study
releases_result <- get_database_releases()
study_releases <- filter_releases_by_study(releases_result, study_id)
if (length(study_releases) > 0) {
  # Show informative modal, prevent deletion
}
```

### Form Validation Patterns
Use `shinyvalidate` for all forms:
```r
iv <- InputValidator$new()
iv$add_rule("field_name", sv_required())
iv$add_rule("field_name", function(value) {
  if (nchar(trimws(value)) < 3) "Content must be at least 3 characters"
})
iv$enable()
```

### Notification Type Constraints
**⚠️ CRITICAL**: Only use valid Shiny notification types
```r
# Correct
showNotification("Success message", type = "message")  # not "success"
showNotification("Error occurred", type = "error")

# Wrong - will cause match.arg errors
showNotification("Message", type = "success")  # Invalid type
```

Valid types: `"default"`, `"message"`, `"warning"`, `"error"`

## Common Development Patterns

### DataTable Configuration Standard
```r
DT::datatable(
  data,
  filter = 'top',
  options = list(
    dom = 'frtip',  # Proper search box display
    search = list(regex = TRUE, caseInsensitive = TRUE),
    pageLength = 25,
    searching = TRUE
  )
)
```

### Action Button Implementation
```r
# In display data preparation
display_df$Actions <- sapply(items$ID, function(item_id) {
  sprintf(
    '<button class="btn btn-primary btn-sm me-1" data-action="edit" data-id="%s">
       <i class="bi bi-pencil"></i></button>
     <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s">
       <i class="bi bi-trash"></i></button>',
    item_id, item_id
  )
})
```

### WebSocket Event Handling
```r
# In server modules
observeEvent(input$websocket_event, {
  if (!is.null(input$websocket_event)) {
    event_data <- input$websocket_event
    if (startsWith(event_data$type, "entity_")) {
      load_entity_data()  # Refresh data
    }
  }
})
```

### API Client Error Handling
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

## UI/UX Standards

### Card Layout Consistency
**Standard Dimensions**: All modules use consistent card sizing
- **Max Width**: 1200px for main cards
- **Height**: 700px for main content cards
- **Sidebar Width**: 450px for form sidebars

### Bootstrap 5 Integration
- **Icons**: Use `bsicons` package - `bs_icon("icon-name")`
- **Classes**: Modern Bootstrap 5 classes (`d-flex`, `gap-2`, `text-primary`)
- **Components**: Cards, modals, forms follow bslib patterns

### Theme System
- **Dark Mode**: Automatic toggle with `input_dark_mode()`
- **Custom Theme**: Defined in `app.R` with consistent colors and shadows
- **Responsive**: All layouts adapt to mobile/tablet/desktop

### Design System Guidelines
1. **Card Dimensions**: Always use 1200px max-width and 700px height for main cards
2. **Sidebar Width**: Always use 450px width for form sidebars
3. **Content Height**: Use 500px+ for main content areas to minimize scrolling
4. **Icon Consistency**: Match sidebar navigation icons in card headers
5. **Spacing**: Use consistent padding (20px outer, c(3,3,3,4) sidebar)
6. **Color Scheme**: text-primary for headers, text-muted for descriptions

## Testing and Debugging

### Real-time WebSocket Testing
```bash
# 1. Start backend
cd ../backend && uv run python run.py

# 2. Start frontend
Rscript run_app.R

# 3. Open multiple browser sessions to http://localhost:3838
# 4. Test CRUD operations and verify real-time sync across sessions

# 5. Run automated WebSocket test
cd ../backend && uv run python tests/integration/test_websocket_broadcast.py
```

### Common Issues and Solutions

**"WebSocket not working"**: 
- Check browser console for connection errors
- Verify backend WebSocket endpoint is running
- Ensure message routing matches expected format

**"Modal not opening"**:
- Check JavaScript console for errors
- Ensure proper modal dialog structure with Bootstrap 5

**"Environment variables not loading"**:
- Confirm `.env` file exists and has correct format
- Check `load_dot_env()` called before variable usage
- Verify file sourcing order in `app.R`

### Debugging Workflow
1. **JavaScript Console**: Add console.log statements to debug button click handlers
2. **R Console Logging**: Add cat() statements to track R-side event processing  
3. **Network Tab**: Monitor HTTP requests and WebSocket messages
4. **Modal Timing**: Use delays for operations that depend on rendered modals
5. **Reactive Value Access**: Always assign reactive values to variables before use

## Package Management

### renv Workflow
- **New Packages**: `renv::install("package")` → `renv::snapshot()`
- **Updates**: `renv::update()` → `renv::snapshot()`
- **Collaboration**: New developers run `renv::restore()`
- **Version Control**: `renv.lock` tracks exact package versions

### Key Dependencies
- **shiny** (≥1.8.0): Core framework with modern features
- **bslib** (≥0.6.0): Bootstrap 5 theming and modern UI
- **httr2** (≥1.0.0): Modern HTTP client with better error handling
- **shinyvalidate** (≥0.1.3): Form validation
- **DT** (≥0.30): Interactive data tables

## Integration Points

### Backend API Coordination
- All CRUD operations trigger WebSocket broadcasts
- SQLAlchemy models require Pydantic conversion for WebSocket
- API responses follow consistent JSON structure
- Error handling provides user-friendly messages

### Multi-User Synchronization
- WebSocket broadcasts ensure data consistency
- UI updates happen immediately across all sessions
- Connection status indicators provide user feedback
- Automatic reconnection maintains reliability

## Critical Implementation Notes

### WebSocket Message Routing System

#### Complete Message Flow
1. **Backend API** calls `broadcast_*()` function with message type only
2. **WebSocket Server** broadcasts to all connected clients
3. **JavaScript Client** receives message, detects module from type, adds module property
4. **notifyShinyModule()** sends to `{module}-websocket_event` Shiny input
5. **R Shiny Module** `observeEvent()` triggers and refreshes data via HTTP

#### Module-Based Routing Solution
The JavaScript WebSocket client (`websocket_client.js`) implements automatic module detection:

```javascript
// handleMessage() automatically assigns modules based on message type
if (data.type === 'studies_update' || data.type.startsWith('study_')) {
    data.module = 'studies';
} else if (data.type.startsWith('reporting_effort_')) {
    data.module = 'reporting_efforts';
} else if (data.type.startsWith('database_release_')) {
    data.module = 'database_releases';
} else if (data.type.startsWith('text_element_')) {
    data.module = 'tnfp';
}
```

### TNFP (Text/Note/Footnote/Population) Module
**📝 SIMPLIFIED MODULE**: Unified TNFP management interface for all text element types stored in a single database table.

#### Key Features
- **Unified Interface**: Single form for all text element types: `title`, `footnote`, `population_set`, `acronyms_set`
- **Simplified Database Schema**: All TNFP data stored as `text_elements` with `type` field
- **Single API Endpoint**: `/api/v1/text-elements/` handles all element types
- **WebSocket Integration**: Only `text_element_*` events, no separate acronym events
- **Duplicate Prevention**: Advanced validation prevents duplicate content within each type

#### Duplicate Validation System
**⚠️ CRITICAL**: The TNFP module implements sophisticated duplicate detection to prevent similar content within each text element type.

**Validation Logic**:
- **Normalization**: Content is normalized by removing all spaces and converting to uppercase
- **Type-Specific**: Duplicates are checked only within the same element type (title, footnote, etc.)
- **Case-Insensitive**: "Test Title" and "test title" are considered duplicates
- **Space-Insensitive**: "Test Title" and "TestTitle" are considered duplicates

**Frontend Implementation**:
```r
# Error message parsing for duplicate validation
format_error_message <- function(error_string) {
  if (grepl("HTTP 400 -", error_string)) {
    json_part <- sub(".*HTTP 400 - ", "", error_string)
    error_data <- jsonlite::fromJSON(json_part)
    return(error_data$detail)  # Returns backend's detailed message
  }
  return(error_string)
}

# Enhanced error notifications for duplicates
if (grepl("Duplicate text elements are not allowed", formatted_error)) {
  showNotification(
    tagList(
      tags$strong("Duplicate Content Detected"),
      tags$br(),
      formatted_error,  # Shows existing element content
      tags$br(),
      tags$small("Tip: The system compares content ignoring spaces and letter case.")
    ),
    type = "error",
    duration = 8000
  )
}
```

**User Experience**:
- **Proactive Hints**: Form includes tip about duplicate validation rules
- **Detailed Error Messages**: Shows exactly which existing element conflicts
- **Clear Guidance**: Explains the normalization rules (spaces/case ignored)
- **Extended Duration**: Error notifications stay visible longer (8 seconds) for readability

**Backend Error Format**:
```
"A {type} with similar content already exists: '{existing_label}'. 
Duplicate text elements are not allowed (comparison ignores spaces and case)."
```

**Testing Duplicate Validation**:
1. Create a text element: "Test Title"
2. Try to create: "test title" → Should show duplicate error
3. Try to create: "TestTitle" → Should show duplicate error  
4. Try to create: "Test Title 2" → Should succeed (different content)

### Module Integration Rules
- **Source Order Matters**: `websocket_client.R` must be sourced BEFORE other modules that use WebSocket URLs
- **Environment Loading**: Call `load_dot_env()` BEFORE defining any endpoint URLs
- **Self-Contained Modules**: Each module should read environment variables directly, not depend on globals

## Using Claude Code Agents for Development

### rshiny-modern-builder Agent

This specialized agent is perfect for R Shiny development tasks in this codebase. Use it for:

**UI Component Development**:
- Creating new module UI components following the established bslib + Bootstrap 5 patterns
- Implementing responsive layouts and modern design components
- Adding new entity management interfaces (following studies/database releases/reporting efforts patterns)

**Real-time Features**:
- Implementing WebSocket integration for new modules
- Creating reactive data flows and state management
- Building real-time synchronization features

**API Integration**:
- Adding new CRUD endpoints to `modules/api_client.R`
- Implementing form validation with `shinyvalidate`
- Creating cascading dropdown functionality

### general-purpose Agent

Use for broader development tasks that span multiple technologies:

**System Integration**:
- Analyzing WebSocket message flows between R Shiny frontend and FastAPI backend
- Debugging environment variable configuration issues
- Setting up development workflows and testing procedures

**Cross-Platform Development**:
- Coordinating frontend-backend API contract changes
- Implementing end-to-end testing workflows
- Analyzing system architecture and identifying improvement opportunities

## MCP Tools for Development & Debugging

### Using Playwright MCP for Browser Testing

**UI/UX Testing and Debugging**:
```bash
# Start the R Shiny app first
Rscript run_app.R

# Then use Claude Code with Playwright MCP to:
# - Take screenshots of UI components at different screen sizes
# - Test responsive design breakpoints
# - Validate CSS styling and layout issues
# - Test form interactions and validations
# - Debug WebSocket connection status indicators
```

**WebSocket Real-time Testing**:
- Use Playwright to open multiple browser instances simultaneously
- Test real-time synchronization by creating/editing/deleting records in one window
- Verify updates appear instantly in other windows
- Monitor WebSocket connection status indicators across sessions

### Using Other MCP Tools

**Context7 MCP for Documentation**:
- Look up R Shiny best practices and modular patterns
- Find bslib theming examples and Bootstrap 5 component usage
- Research httr2 usage patterns for robust API integration
- Get WebSocket client implementation examples and error handling patterns

**Sequential MCP for Complex Analysis**:
- Systematic troubleshooting of WebSocket connection and message routing issues
- Step-by-step analysis of reactive value flows in Shiny modules
- Complex form validation debugging with interdependent fields
- Architecture analysis for scaling and performance optimization

## Development Best Practices

- Use `rshiny-modern-builder` agent for all R Shiny-specific development tasks
- Leverage `general-purpose` agent for system-wide analysis and multi-technology coordination
- Use environment variables for all configuration (see `config.env.template`)
- Follow the established modular pattern for consistency across entities
- Test WebSocket functionality with multiple browser sessions using Playwright MCP
- Validate referential integrity before allowing deletions
- Keep DataTable configurations consistent across all modules
- Coordinate agent usage with MCP tools for comprehensive development workflows
- Always use `setup_environment.R` for fresh installations to ensure latest package versions