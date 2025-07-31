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

### Debugging Session Lessons Learned (Latest Session)

#### JavaScript sprintf Formatting Issues
- **Problem**: Edit buttons not working due to sprintf formatting errors
- **Root Cause**: Mismatch between number of `%s` placeholders (4) and arguments (5) in JavaScript callbacks
- **Solution**: Carefully count placeholders and arguments in `sprintf()` calls
- **Lesson**: Always validate sprintf formatting - R will give warnings but continue execution with broken JavaScript
- **Detection**: Look for warnings like "one argument not used by format" in R console

#### Custom Message Handler Syntax
- **Problem**: `session$onCustomMessage()` causing "attempt to apply non-function" error
- **Root Cause**: Incorrect Shiny syntax - this method doesn't exist in standard Shiny
- **Solution**: Use `observeEvent(input$custom_input, {...})` pattern instead
- **Implementation**: Trigger with `shinyjs::runjs("Shiny.setInputValue('module-input_name', value)")` from main app
- **Lesson**: Always verify Shiny API methods - custom message handling requires input-based approach

#### Modal Dropdown Population Issues
- **Problem**: Database release dropdown not populated correctly in edit modal
- **Root Cause**: Pre-filtering choices before modal creation prevented proper selection
- **Solution**: Load all choices initially, then use `shinyjs::delay()` to filter after modal renders
- **Pattern**: 
  ```r
  # Create modal with all choices
  selectInput(..., choices = all_choices, selected = current_value)
  # Then filter after rendering
  shinyjs::delay(100, {
    updateSelectInput(session, ..., choices = filtered_choices, selected = current_value)
  })
  ```
- **Lesson**: Modal rendering is asynchronous - use delays for post-modal operations

#### Edit Functionality Missing Variables
- **Problem**: "object 'current_id' not found" error in edit save handlers
- **Root Cause**: Missing variable assignment from reactive value
- **Solution**: Always add `current_id <- editing_[entity]_id()` at start of save handlers
- **Pattern**: Every edit save function needs to retrieve the ID from the reactive value before use
- **Lesson**: Reactive values must be explicitly called and assigned to variables within observers

#### Systematic Debugging Approach
1. **JavaScript Console**: Add console.log statements to debug button click handlers
2. **R Console Logging**: Add cat() statements to track R-side event processing  
3. **Sprintf Validation**: Count placeholders vs arguments carefully
4. **Modal Timing**: Use delays for operations that depend on rendered modals
5. **Reactive Value Access**: Always assign reactive values to variables before use in complex logic

### UI Layout Standardization (Latest Updates)

#### Card Dimension Consistency
- **Problem**: Inconsistent card sizes causing poor visual hierarchy and usability issues
- **Before**: Studies (900px/600px), Database Releases (1000px/600px), Reporting Efforts (1200px/650px)
- **Solution**: Standardized all modules to consistent dimensions
- **Standard Dimensions**: 
  ```r
  style = "width: 100%; max-width: 1200px;"
  height = "700px"
  ```
- **Benefits**: Professional appearance, consistent navigation experience, better responsive design

#### Sidebar Form Usability
- **Problem**: Narrow sidebars (320-350px) causing form cramping and poor UX
- **Solution**: Increased all sidebar widths to 450px (28% wider)
- **Pattern**: 
  ```r
  sidebar(
    width = 450,  # Standard width for all modules
    position = "right",
    padding = c(3, 3, 3, 4)
  )
  ```
- **Benefits**: Better form field visibility, reduced horizontal scrolling, improved data entry experience

#### Content Area Optimization
- **Problem**: Small content areas requiring scrolling to access key functionality
- **Solution**: Increased main content heights for better data visibility
- **Reporting Efforts**: Increased from 400px to 500px content area height
- **Pattern**: 
  ```r
  div(
    class = "p-3",
    style = "height: 500px; overflow-y: auto;",
    DT::dataTableOutput(...)
  )
  ```
- **Benefits**: More data rows visible, reduced scrolling, better user productivity

#### Visual Consistency Standards
- **Card Headers**: All modules use same icon + title pattern with `text-primary` styling
- **Action Buttons**: Consistent placement and styling across all modules
- **Form Elements**: Standardized padding, gaps, and responsive behavior
- **Empty States**: Consistent messaging and layout for tables with no data

#### Design System Guidelines
1. **Card Dimensions**: Always use 1200px max-width and 700px height for main cards
2. **Sidebar Width**: Always use 450px width for form sidebars
3. **Content Height**: Use 500px+ for main content areas to minimize scrolling
4. **Icon Consistency**: Match sidebar navigation icons in card headers
5. **Spacing**: Use consistent padding (20px outer, c(3,3,3,4) sidebar)
6. **Color Scheme**: text-primary for headers, text-muted for descriptions

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

### WebSocket Reporting Efforts Implementation (Latest Session)

#### Problem: Reporting Efforts WebSocket Not Working
- **Issue**: User reported "websocket not working for reporting effort, they are working for studies and database release"
- **Investigation**: Backend had all broadcast functions but JavaScript client was missing event handling

#### Root Cause Analysis  
- **Backend**: ✅ All broadcast functions existed (`broadcast_reporting_effort_*`)
- **Backend API**: ✅ All CRUD endpoints were calling broadcast functions correctly  
- **Frontend R**: ✅ WebSocket event handling already implemented in `reporting_efforts_server.R`
- **Frontend JS**: ❌ Missing event handlers and routing in `websocket_client.js`

#### JavaScript WebSocket Client Fixes
1. **Added Missing Event Handlers** in `handleMessage()`:
   ```javascript
   case 'reporting_effort_created':
   case 'reporting_effort_updated': 
   case 'reporting_effort_deleted':
   ```

2. **Added Event Routing** in `notifyShiny()`:
   ```javascript
   // Send to reporting_efforts module for reporting effort events and related reference data updates
   if (eventType.startsWith('reporting_effort') || eventType === 'studies_update' || eventType.startsWith('database_release')) {
     Shiny.setInputValue('reporting_efforts-websocket_event', {
       type: eventType, data: data, timestamp: Date.now()
     });
   }
   ```

#### Backend WebSocket Connection Management Improvements
- **Problem**: Stale connection errors: "Unexpected ASGI message 'websocket.send', after sending 'websocket.close'"
- **Solution**: Enhanced `ConnectionManager.broadcast()` method with:
  - **Proactive Cleanup**: Call `cleanup_stale_connections()` before broadcasting
  - **Connection State Checking**: Verify `client_state.name == "CONNECTED"` before sending
  - **Error Level Adjustment**: Changed frequent broadcast logs from INFO to DEBUG to reduce noise
  - **Better Error Handling**: Gracefully handle and remove stale connections during broadcast

#### WebSocket Implementation Pattern
```javascript
// Complete flow for reporting efforts WebSocket events:
// 1. Backend CRUD → broadcast_reporting_effort_*() 
// 2. WebSocket server → all connected clients
// 3. JavaScript client → handleMessage() → notifyShiny()
// 4. R Shiny → observeEvent(input$websocket_event) → refresh data
```

#### Testing & Validation
- **Backend Test Script**: Created `/test_websocket_fix.py` for connection management testing
- **Connection Cleanup**: Now properly removes stale WebSocket connections
- **Error Reduction**: Eliminated "websocket.send after websocket.close" errors
- **Real-time Updates**: Reporting efforts now have same real-time functionality as studies/database releases

### WebSocket Message Routing System

#### Message Format Mismatch Issue
The WebSocket system had a critical routing issue where backend and frontend expected different message formats:

**Backend sends (from FastAPI):**
```json
{
  "type": "reporting_effort_updated",
  "data": {...}
}
```

**Frontend expected (in websocket_client.js):**
```json
{
  "module": "reporting_efforts",
  "type": "reporting_effort_updated", 
  "data": {...}
}
```

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
}
```

#### Shiny Event Routing
Messages are routed to Shiny modules using the pattern `{module}-websocket_event`:
- `studies-websocket_event` → handled by `studies_server.R`
- `reporting_efforts-websocket_event` → handled by `reporting_efforts_server.R`
- `database_releases-websocket_event` → handled by `database_releases_server.R`

#### Complete Message Flow
1. **Backend API** calls `broadcast_reporting_effort_updated()` with message type only
2. **WebSocket Server** broadcasts to all connected clients
3. **JavaScript Client** receives message, detects module from type, adds module property
4. **notifyShinyModule()** sends to `reporting_efforts-websocket_event` Shiny input
5. **R Shiny Module** `observeEvent()` triggers and refreshes data via HTTP

This architecture allows the backend to remain simple (only sending type + data) while the frontend intelligently routes messages to the appropriate Shiny modules.

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

**Example Usage**:
```bash
# Use the Task tool to spawn the rshiny-modern-builder agent for:
# - Adding a new entity module (e.g., "participants")
# - Implementing complex form interactions
# - Creating advanced DataTable configurations
# - Building responsive dashboard layouts
```

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

**CSS and Responsive Design Debugging**:
- Capture screenshots at different viewport sizes (mobile: 375px, tablet: 768px, desktop: 1200px)
- Test Bootstrap 5 responsive breakpoints and bslib theme consistency
- Debug modal positioning and form layout issues
- Validate action button styling and hover states

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

### Agent and MCP Tool Coordination

**For New Feature Development**:
1. Use `rshiny-modern-builder` agent to implement R Shiny components
2. Use `general-purpose` agent to coordinate backend API changes
3. Use Playwright MCP to test the complete user workflow
4. Use Context7 MCP to validate against R Shiny best practices

**For Debugging Complex Issues**:
1. Use Sequential MCP for systematic problem analysis
2. Use `general-purpose` agent for cross-system debugging
3. Use Playwright MCP for browser-specific testing and validation
4. Use `rshiny-modern-builder` agent for R Shiny-specific fixes

## Development Best Practices

- Use `rshiny-modern-builder` agent for all R Shiny-specific development tasks
- Leverage `general-purpose` agent for system-wide analysis and multi-technology coordination
- Use environment variables for all configuration (see `config.env.template`)
- Follow the established modular pattern for consistency across entities
- Test WebSocket functionality with multiple browser sessions using Playwright MCP
- Validate referential integrity before allowing deletions
- Keep DataTable configurations consistent across all modules
- Coordinate agent usage with MCP tools for comprehensive development workflows