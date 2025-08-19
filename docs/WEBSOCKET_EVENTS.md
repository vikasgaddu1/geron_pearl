# WebSocket Events Documentation

**PEARL Full-Stack Research Data Management System**  
**WebSocket Message Types, Handlers, and Routing Patterns**

This document catalogs all WebSocket event types, their handlers, and routing patterns for real-time cross-browser synchronization in the PEARL system post-Phase 2 implementation.

## Table of Contents

- [Overview](#overview)
- [Connection Management](#connection-management)
- [Message Format](#message-format)
- [Event Types by Entity](#event-types-by-entity)
- [Frontend WebSocket Clients](#frontend-websocket-clients)
- [Cross-Browser Synchronization Patterns](#cross-browser-synchronization-patterns)
- [Event Routing Architecture](#event-routing-architecture)
- [Universal CRUD Manager](#universal-crud-manager)
- [Debugging WebSocket Issues](#debugging-websocket-issues)

---

## Overview

The PEARL system uses WebSocket connections for real-time data synchronization across multiple browsers and users. All CRUD operations trigger WebSocket events that are broadcast to connected clients.

**WebSocket Endpoint**: `ws://localhost:8000/api/v1/ws/studies`

**Key Features**:
- Real-time cross-browser synchronization
- Automatic connection recovery
- Dual client architecture (JavaScript + R)
- Universal CRUD Manager for streamlined handling
- Enhanced error handling and debugging

---

## Connection Management

### Connection Lifecycle

**Backend** (`backend/app/api/v1/websocket.py`):
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        
    async def broadcast(self, message: str):
        # Broadcasts to all connected clients
```

**Connection Features**:
- Automatic stale connection cleanup
- Keep-alive pings every 30 seconds
- Exponential backoff reconnection
- Connection state monitoring

---

## Message Format

### Standard Message Structure

All WebSocket messages follow this JSON format:

```json
{
    "type": "event_type",
    "data": { /* event payload */ },
    "timestamp": "2024-12-01T10:00:00Z"
}
```

### Client-to-Server Messages

**Ping** (Keep-alive):
```json
{"action": "ping"}
```

**Data Refresh Request**:
```json
{"action": "refresh"}
```

### Server-to-Client Messages

**Pong Response**:
```json
{"type": "pong"}
```

**Error Message**:
```json
{
    "type": "error",
    "message": "Error description"
}
```

---

## Event Types by Entity

### Study Events

**study_created**:
```json
{
    "type": "study_created",
    "data": {
        "id": 1,
        "study_label": "ONCOLOGY-2024-001",
        "created_at": "2024-12-01T10:00:00Z",
        "updated_at": "2024-12-01T10:00:00Z"
    }
}
```

**study_updated**:
```json
{
    "type": "study_updated",
    "data": {
        "id": 1,
        "study_label": "ONCOLOGY-2024-001-UPDATED",
        "created_at": "2024-12-01T10:00:00Z",
        "updated_at": "2024-12-01T15:30:00Z"
    }
}
```

**study_deleted**:
```json
{
    "type": "study_deleted",
    "data": {"id": 1}
}
```

**Broadcasting Functions** (`backend/app/api/v1/websocket.py`):
- `broadcast_study_created(study_data)`
- `broadcast_study_updated(study_data)`
- `broadcast_study_deleted(study_id)`

---

### Database Release Events

**database_release_created**:
```json
{
    "type": "database_release_created",
    "data": {
        "id": 1,
        "study_id": 1,
        "database_release_label": "DB_LOCK_20241201",
        "database_release_date": "2024-12-01",
        "created_at": "2024-12-01T10:00:00Z",
        "updated_at": "2024-12-01T10:00:00Z"
    }
}
```

**database_release_updated**:
- Same structure as created event

**database_release_deleted**:
```json
{
    "type": "database_release_deleted",
    "data": {"id": 1}
}
```

**Broadcasting Functions**:
- `broadcast_database_release_created(database_release_data)`
- `broadcast_database_release_updated(database_release_data)`
- `broadcast_database_release_deleted(database_release_id)`

---

### Reporting Effort Events

**reporting_effort_created**:
```json
{
    "type": "reporting_effort_created",
    "data": {
        "id": 1,
        "database_release_id": 1,
        "database_release_label": "INTERIM_ANALYSIS_20241201",
        "created_at": "2024-12-01T10:00:00Z",
        "updated_at": "2024-12-01T10:00:00Z"
    }
}
```

**reporting_effort_updated**:
- Same structure as created event

**reporting_effort_deleted**:
```json
{
    "type": "reporting_effort_deleted",
    "data": {"id": 1}
}
```

**Broadcasting Functions**:
- `broadcast_reporting_effort_created(reporting_effort_data)`
- `broadcast_reporting_effort_updated(reporting_effort_data)`
- `broadcast_reporting_effort_deleted(reporting_effort_id)`

---

### Reporting Effort Item Events

**reporting_effort_item_created**:
```json
{
    "type": "reporting_effort_item_created",
    "data": {
        "id": 1,
        "reporting_effort_id": 1,
        "item_code": "T-14.1.1",
        "item_description": "Demographics and Baseline Characteristics",
        "item_type": "TLF",
        "item_status": "PENDING",
        "created_at": "2024-12-01T10:00:00Z",
        "updated_at": "2024-12-01T10:00:00Z"
    }
}
```

**reporting_effort_item_updated**:
- Same structure as created event

**reporting_effort_item_deleted**:
```json
{
    "type": "reporting_effort_item_deleted",
    "data": {
        "id": 1,
        "item_code": "T-14.1.1"
    }
}
```

**Broadcasting Functions**:
- `broadcast_reporting_effort_item_created(item_data)`
- `broadcast_reporting_effort_item_updated(item_data)`
- `broadcast_reporting_effort_item_deleted(item_data)`

---

### Reporting Effort Tracker Events

**reporting_effort_tracker_updated**:
```json
{
    "type": "reporting_effort_tracker_updated",
    "data": {
        "id": 1,
        "reporting_effort_item_id": 1,
        "primary_programmer_id": 1,
        "qc_programmer_id": 2,
        "primary_status": "COMPLETED",
        "qc_status": "IN_PROGRESS",
        "created_at": "2024-12-01T10:00:00Z",
        "updated_at": "2024-12-01T15:30:00Z"
    }
}
```

**reporting_effort_tracker_deleted** (Enhanced):
```json
{
    "type": "reporting_effort_tracker_deleted",
    "data": {
        "tracker": {
            "id": 1,
            "reporting_effort_item_id": 1,
            "primary_programmer_id": 1
        },
        "deleted_at": "2024-12-01T15:30:00Z",
        "deleted_by": {
            "user_id": 1,
            "username": "johndoe"
        },
        "item": {
            "item_code": "T-14.1.1",
            "effort_id": 1
        }
    }
}
```

**tracker_assignment_updated**:
```json
{
    "type": "tracker_assignment_updated",
    "data": {
        "tracker": { /* tracker data */ },
        "assignment_type": "primary",
        "programmer_id": 1
    }
}
```

**Broadcasting Functions**:
- `broadcast_reporting_effort_tracker_updated(tracker_data)`
- `broadcast_reporting_effort_tracker_deleted(tracker_data, user_info, item_info)`
- `broadcast_tracker_assignment_updated(tracker_data, assignment_type, programmer_id)`

---

### Package Events

**package_created**:
```json
{
    "type": "package_created",
    "data": {
        "id": 1,
        "package_name": "Safety Analysis Package",
        "study_indication": "Oncology",
        "therapeutic_area": "Solid Tumors",
        "created_at": "2024-12-01T10:00:00Z",
        "updated_at": "2024-12-01T10:00:00Z"
    }
}
```

**package_updated**:
- Same structure as created event

**package_deleted**:
```json
{
    "type": "package_deleted",
    "data": {
        "id": 1,
        "package_name": "Safety Analysis Package"
    }
}
```

**Broadcasting Functions**:
- `broadcast_package_created(package_data)`
- `broadcast_package_updated(package_data)`
- `broadcast_package_deleted(package_data)`

---

### Package Item Events

**package_item_created**:
```json
{
    "type": "package_item_created",
    "data": {
        "id": 1,
        "package_id": 1,
        "item_code": "T-14.1.1",
        "item_description": "Demographics and Baseline Characteristics",
        "item_type": "TLF",
        "created_at": "2024-12-01T10:00:00Z",
        "updated_at": "2024-12-01T10:00:00Z"
    }
}
```

**package_item_updated**:
- Same structure as created event

**package_item_deleted**:
```json
{
    "type": "package_item_deleted",
    "data": {
        "id": 1,
        "item_code": "T-14.1.1"
    }
}
```

**Broadcasting Functions**:
- `broadcast_package_item_created(package_item_data)`
- `broadcast_package_item_updated(package_item_data)`
- `broadcast_package_item_deleted(package_item_data)`

---

### Text Element Events

**text_element_created**:
```json
{
    "type": "text_element_created",
    "data": {
        "id": 1,
        "type": "TITLE",
        "label": "Demographics Table",
        "content": "Table 14.1.1: Demographics and Baseline Characteristics",
        "created_at": "2024-12-01T10:00:00Z",
        "updated_at": "2024-12-01T10:00:00Z"
    }
}
```

**text_element_updated**:
- Same structure as created event

**text_element_deleted**:
```json
{
    "type": "text_element_deleted",
    "data": {
        "id": 1,
        "type": "TITLE",
        "label": "Demographics Table"
    }
}
```

**Broadcasting Functions**:
- `broadcast_text_element_created(text_element_data)`
- `broadcast_text_element_updated(text_element_data)`
- `broadcast_text_element_deleted(text_element_data)`

---

### Comment Events

**comment_created** (Parent comment):
```json
{
    "type": "comment_created",
    "data": {
        "tracker_id": 1,
        "comment": {
            "id": 1,
            "user_id": 1,
            "username": "johndoe",
            "comment_text": "Need clarification on analysis population",
            "comment_type": "QUESTION",
            "is_resolved": false,
            "parent_comment_id": null,
            "created_at": "2024-12-01T10:00:00Z",
            "updated_at": "2024-12-01T10:00:00Z"
        },
        "unresolved_count": 1
    }
}
```

**comment_replied** (Reply to comment):
```json
{
    "type": "comment_replied",
    "data": {
        "tracker_id": 1,
        "parent_comment_id": 1,
        "reply": {
            "id": 2,
            "user_id": 2,
            "username": "janesmith",
            "comment_text": "The analysis population is defined in section 9.1",
            "comment_type": "RESPONSE",
            "is_resolved": false,
            "parent_comment_id": 1,
            "created_at": "2024-12-01T11:00:00Z",
            "updated_at": "2024-12-01T11:00:00Z"
        },
        "unresolved_count": 1
    }
}
```

**comment_resolved**:
```json
{
    "type": "comment_resolved",
    "data": {
        "tracker_id": 1,
        "comment_id": 1,
        "unresolved_count": 0
    }
}
```

**comment_updated**:
```json
{
    "type": "comment_updated",
    "data": {
        /* Updated comment data */
    }
}
```

**comment_deleted**:
```json
{
    "type": "comment_deleted",
    "data": {
        "id": 1,
        "tracker_id": 1
    }
}
```

**Broadcasting Functions**:
- `broadcast_comment_created(tracker_id, comment_data, unresolved_count)`
- `broadcast_comment_replied(tracker_id, parent_comment_id, comment_data, unresolved_count)`
- `broadcast_comment_resolved(tracker_id, comment_id, unresolved_count)`
- `broadcast_comment_updated(comment_data)`
- `broadcast_comment_deleted(comment_data)`

---

### User Events

**user_created**:
```json
{
    "type": "user_created",
    "data": {
        "id": 1,
        "username": "johndoe",
        "role": "ANALYST",
        "department": "Clinical Research",
        "created_at": "2024-12-01T10:00:00Z",
        "updated_at": "2024-12-01T10:00:00Z"
    }
}
```

**user_updated**:
- Same structure as created event

**user_deleted**:
```json
{
    "type": "user_deleted",
    "data": {
        "id": 1,
        "username": "johndoe"
    }
}
```

**Broadcasting Functions**:
- `broadcast_user_created(user_data)`
- `broadcast_user_updated(user_data)`
- `broadcast_user_deleted(user_data)`

---

## Frontend WebSocket Clients

### JavaScript WebSocket Client

**Location**: `admin-frontend/www/websocket_client.js`

**Key Features**:
- Automatic reconnection with exponential backoff
- Event routing to Shiny modules
- Connection state management
- Keep-alive ping handling

**Connection Management**:
```javascript
class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000; // Start with 1 second
    }

    connect() {
        try {
            this.ws = new WebSocket('ws://localhost:8000/api/v1/ws/studies');
            this.setupEventHandlers();
        } catch (error) {
            this.handleConnectionError(error);
        }
    }
}
```

**Event Routing**:
```javascript
handleMessage(event) {
    const data = JSON.parse(event.data);
    
    // Route to appropriate handler
    if (data.type.startsWith('package_')) {
        this.notifyShinyGlobal(data.type, data.data, 'package_update');
    } else if (data.type.startsWith('comment_')) {
        this.notifyShiny(data.type, data.data, 'reporting_effort_tracker');
    }
    // ... other routing logic
}
```

### R WebSocket Client

**Location**: `admin-frontend/modules/websocket_client.R`

**Integration with Shiny**:
```r
websocket_client_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # R-based WebSocket handling (secondary client)
    # Primarily for fallback and debugging
  })
}
```

---

## Cross-Browser Synchronization Patterns

### Approach A: Universal CRUD Manager (Recommended)

**Used by**: Package Items, Trackers (newer implementation)

**How it works**:
1. Backend broadcasts standard WebSocket events
2. JavaScript client routes events to Universal CRUD Manager
3. Universal CRUD Manager triggers module refresh via `crud_refresh` input

**JavaScript Routing**:
```javascript
// Route to Universal CRUD Manager
if (data.type.startsWith('package_item_')) {
    // Set input for Universal CRUD Manager
    Shiny.setInputValue('crud_refresh', Math.random(), {priority: 'event'});
}
```

**Module Observer** (Package Items):
```r
# In package_items_server.R
observeEvent(input$crud_refresh, {  # ⚠️ NO module prefix!
    if (!is.null(input$crud_refresh)) {
        load_package_items_data()  # Refresh the data
    }
})
```

**Advantages**:
- Automatic, no extra configuration needed
- Simpler code maintenance
- Consistent pattern across modules

---

### Approach B: Global Observer + Custom Messages

**Used by**: Packages, Studies (legacy implementation)

**How it works**:
1. JavaScript client routes to global observer
2. Global observer in `app.R` sends custom message
3. JavaScript handler sets module-specific input
4. Module observes full input name

**JavaScript to Global**:
```javascript
// websocket_client.js
if (data.type.startsWith('package_')) {
    this.notifyShinyGlobal(data.type, data.data, 'package_update');
}
```

**Global Observer** (`app.R`):
```r
observeEvent(input$`package_update-websocket_event`, {
    if (!is.null(input$`package_update-websocket_event`)) {
        session$sendCustomMessage("triggerPackageRefresh", list(
            timestamp = as.numeric(Sys.time()),
            event_type = event_data$type
        ))
    }
})
```

**JavaScript Handler** (`www/shiny_handlers.js`):
```javascript
Shiny.addCustomMessageHandler('triggerPackageRefresh', function(message) {
    if (window.Shiny && window.Shiny.setInputValue) {  // ⚠️ Check availability!
        Shiny.setInputValue('packages_simple-crud_refresh', Math.random(), {priority: 'event'});
    }
});
```

**Module Observer**:
```r
observeEvent(input$`packages_simple-crud_refresh`, {  # ⚠️ FULL name in observer!
    if (!is.null(input$`packages_simple-crud_refresh`)) {
        load_packages_data()
    }
})
```

---

## Event Routing Architecture

### Message Flow Diagram

```
Backend CRUD Operation
        ↓
WebSocket Broadcast Function
        ↓
ConnectionManager.broadcast()
        ↓
All Connected WebSocket Clients
        ↓
JavaScript WebSocket Client
        ↓
Event Type Routing Logic
        ↓
┌─────────────────────┬─────────────────────┐
│  Universal CRUD     │  Global Observer    │
│  Manager Route      │  Route              │
│  (Recommended)      │  (Legacy)           │
└─────────────────────┴─────────────────────┘
        ↓                       ↓
Module input$crud_refresh   Module input$module-crud_refresh
        ↓                       ↓
Module Observer             Module Observer
        ↓                       ↓
Data Refresh Function       Data Refresh Function
```

### Routing Configuration

**Universal CRUD Manager Routes** (Recommended):
```javascript
// Direct module routing
const universalRoutes = {
    'package_item_': 'package_items',
    'reporting_effort_tracker_': 'reporting_effort_tracker',
    'comment_': 'reporting_effort_tracker'  // Comments route to tracker module
};
```

**Global Observer Routes** (Legacy):
```javascript
// Global routing with custom messages
const globalRoutes = {
    'package_': 'package_update',
    'study_': 'study_update',
    'user_': 'user_update'
};
```

---

## Universal CRUD Manager

### Implementation

**Location**: `admin-frontend/www/websocket_client.js` (integrated)

**How it works**:
The Universal CRUD Manager automatically routes WebSocket events to the appropriate Shiny modules using a standardized `crud_refresh` input.

**Key Features**:
- Automatic event-to-module mapping
- No module-specific configuration needed
- Consistent refresh pattern
- Namespace handling built-in

**Module Integration**:
```r
# Standard pattern for all modules using Universal CRUD Manager
observeEvent(input$crud_refresh, {
    if (!is.null(input$crud_refresh)) {
        cat("🔄 Universal CRUD refresh triggered for", module_name, "\n")
        load_data()  # Call module's data loading function
    }
})
```

**Advantages**:
1. **Simplicity**: No custom JavaScript handlers needed
2. **Consistency**: Same pattern across all modules
3. **Maintainability**: Changes in one place affect all modules
4. **Reliability**: Less prone to timing issues

---

## Debugging WebSocket Issues

### Step-by-Step Debugging Guide

#### Step 1: Check Backend WebSocket Broadcasting

**What to check**:
- Backend logs for broadcast messages
- Active connection count
- WebSocket endpoint availability

**Commands**:
```bash
# Check backend logs
cd backend
uv run python run.py
# Look for: "Broadcasting [entity]_[action]" messages
```

**Expected Log Output**:
```
INFO:app.api.v1.websocket:Broadcasting package_item_created: T-14.1.1
DEBUG:app.api.v1.websocket:Broadcast completed to 2 connections
```

#### Step 2: Check JavaScript WebSocket Connection

**Browser Console (F12)**:
```javascript
// Check connection status
console.log(window.wsClient ? window.wsClient.ws.readyState : 'No client');

// Expected states:
// 0 = CONNECTING
// 1 = OPEN
// 2 = CLOSING  
// 3 = CLOSED
```

**Expected Console Output**:
```
📨 WebSocket message received: package_item_created
🎯 Routing package_item_ event to Universal CRUD Manager
📤 Triggering Shiny refresh: crud_refresh with value: 0.123456789
```

#### Step 3: Check Event Routing

**Browser Console Messages to Look For**:
```javascript
// Universal CRUD Manager routing (good):
"🎯 Routing package_item_ event to Universal CRUD Manager"
"📤 Triggering Shiny refresh: crud_refresh with value: [timestamp]"

// Global Observer routing (legacy):
"📡 Routing package_ event to global observer: package_update"
"📤 Triggering custom message: triggerPackageRefresh"
```

#### Step 4: Check R Module Input Reception

**Add Temporary Debug Observer**:
```r
# Add to module server function for debugging
observe({
    all_inputs <- reactiveValuesToList(input)
    crud_inputs <- names(all_inputs)[grepl("crud_refresh", names(all_inputs))]
    if (length(crud_inputs) > 0) {
        cat("🔍 DEBUG: CRUD inputs:", paste(crud_inputs, collapse=", "), "\n")
        cat("🔍 DEBUG: crud_refresh value:", input$crud_refresh, "\n")
    }
})
```

#### Step 5: Check Module Observer

**Expected R Console Output**:
```r
🔄 Universal CRUD refresh triggered for package_items
```

### Common Issues and Solutions

#### Issue 1: JavaScript Timing Errors

**Error**: `Shiny.setInputValue is not a function`

**Solution**: Always check availability before use:
```javascript
if (window.Shiny && window.Shiny.setInputValue) {
    Shiny.setInputValue('crud_refresh', Math.random(), {priority: 'event'});
} else {
    console.warn('Shiny not ready, queuing event');
    // Queue event for later
}
```

#### Issue 2: Module Observer Not Triggering

**Cause**: Input name mismatch - Shiny strips module prefix within modules

**Solution**: Use correct input names:
```r
# ✅ Correct (within module)
observeEvent(input$crud_refresh, {
    # Shiny automatically strips module prefix
})

# ❌ Wrong (within module)  
observeEvent(input$`module-crud_refresh`, {
    # This won't work inside the module
})
```

#### Issue 3: Race Conditions

**Cause**: Multiple systems setting same input simultaneously

**Solution**: Use either Universal CRUD Manager OR Global Observer, never both:
```javascript
// ❌ Don't do this
if (data.type.startsWith('package_')) {
    // Universal CRUD Manager
    Shiny.setInputValue('crud_refresh', Math.random());
    // AND Global Observer
    this.notifyShinyGlobal(data.type, data.data, 'package_update');
}

// ✅ Choose one approach
if (data.type.startsWith('package_')) {
    // Universal CRUD Manager only
    Shiny.setInputValue('crud_refresh', Math.random());
}
```

#### Issue 4: Module Not Loading

**Cause**: Syntax errors prevent observer registration

**Debug Command**:
```bash
# Test module syntax
cd admin-frontend
Rscript -e "source('modules/package_items_server.R')"
```

### Debugging Utilities

#### Browser Console Commands

```javascript
// Check WebSocket status
console.log('WebSocket ready state:', window.wsClient?.ws?.readyState);

// Manual event injection for testing
if (window.Shiny && window.Shiny.setInputValue) {
    Shiny.setInputValue('crud_refresh', Math.random(), {priority: 'event'});
}

// Check Shiny input values
console.log('Shiny inputs:', Object.keys(Shiny.shinyapp.$inputValues));
```

#### R Console Commands

```r
# Check active observers
.subset2(session, "userData")

# Manual input trigger for testing
session$sendInputMessage("crud_refresh", runif(1))

# Check module namespace
cat("Module namespace:", session$ns(""), "\n")
```

---

## Related Documentation

- [API_REFERENCE.md](API_REFERENCE.md) - FastAPI endpoints that trigger WebSocket events
- [FRONTEND_MODULES.md](FRONTEND_MODULES.md) - R Shiny modules and their WebSocket integration
- [CRUD_METHODS.md](CRUD_METHODS.md) - CRUD operations that broadcast events
- [UTILITY_FUNCTIONS.md](UTILITY_FUNCTIONS.md) - WebSocket utility functions and helpers
