# Universal CRUD Update System - Implementation Plan

## Overview
This document provides step-by-step instructions for implementing a universal cross-browser CRUD update system that provides consistent behavior across ALL entity types in the PEARL application.

## Prerequisites
- Current branch: `feature/universal-crud-updates`
- Backend running on port 8000
- Frontend running on port 3838
- Playwright MCP available for testing

## Implementation Phases

### Phase 1: Foundation Setup (Days 1-2)
**Goal**: Create the core activity manager and establish basic infrastructure

#### Task 1.1: Create Core Activity Manager
- **File**: `admin-frontend/www/crud_activity_manager.js`
- **Responsibility**: Central coordination of all CRUD updates
- **Key Components**:
  - User context tracking (modals, forms, active elements)
  - Update strategy determination
  - Queue management for deferred updates
  - Conflict detection and resolution

#### Task 1.2: Implement Basic User Context Detection
- **Focus**: Detect when user is actively working
- **Detect**:
  - Open modals (any type: edit, create, delete confirm)
  - Focused form elements (input, textarea, select)
  - Recent activity (mouse, keyboard within 5 seconds)
  - Dirty form state (unsaved changes)

#### Task 1.3: Create Update Strategy Engine
- **Strategies**:
  - `APPLY_IMMEDIATELY`: Safe updates (badges, status)
  - `APPLY_WITH_NOTIFICATION`: Non-conflicting updates
  - `QUEUE_FOR_IDLE`: User active but not conflicting
  - `QUEUE_FOR_MODAL_CLOSE`: Modal open, queue until close
  - `SHOW_CONFLICT_DIALOG`: Direct conflict detected

#### Testing Checkpoint 1.A
- [ ] Activity manager loads without errors
- [ ] User context detection works (console logging)
- [ ] Strategy determination logic functional
- [ ] Basic queue management operational

### Phase 2: WebSocket Integration (Days 2-3)
**Goal**: Route all WebSocket events through the universal manager

#### Task 2.1: Update WebSocket Client Router
- **File**: `admin-frontend/www/websocket_client.js`
- **Changes**:
  - Route ALL CRUD events to activity manager
  - Remove entity-specific handling logic
  - Maintain backward compatibility during transition

#### Task 2.2: Standardize WebSocket Message Format
- **Backend Files**: All `backend/app/api/v1/*.py` endpoints
- **Standard Format**:
```json
{
  "type": "{entity}_{operation}",
  "operation": "create|update|delete",
  "entity": {
    "type": "study|tracker|comment|etc",
    "id": 123,
    "data": {...}
  },
  "context": {
    "user": {...},
    "timestamp": "2025-01-01T12:00:00Z",
    "affected_entities": [...]
  }
}
```

#### Task 2.3: Create Universal Event Processor
- **Function**: Process any CRUD event consistently
- **Logic**:
  1. Determine user context
  2. Check for conflicts
  3. Apply appropriate strategy
  4. Update UI accordingly

#### Testing Checkpoint 2.A
- [ ] All WebSocket events route through manager
- [ ] Strategy determination works for real events
- [ ] No regression in existing functionality
- [ ] Console shows unified event processing

### Phase 3: Legacy Code Removal (Days 3-4)
**Goal**: Remove entity-specific handlers and consolidate logic

#### Task 3.1: Identify and Document Legacy Code
**Files with legacy handlers to remove/replace**:

##### `admin-frontend/www/websocket_client.js`
- **Lines 397-752**: Remove `removeTrackerRowSurgically` and related functions
- **Lines 107-176**: Remove entity-specific routing logic
- **Keep**: Basic WebSocket connection management

##### `admin-frontend/www/shiny_handlers.js`
- **Lines 29-83**: Remove `refreshCommentsHandler`
- **Lines 89-226**: Remove `syncTrackerDeletionHandler`
- **Lines 236-416**: Remove activity tracking (move to manager)
- **Keep**: Shiny message handlers that aren't CRUD-specific

##### Server-side handlers (Multiple `*_server.R` files)
Remove entity-specific WebSocket observers:
- `reporting_effort_tracker_server.R`: `observeEvent(input$websocket_event)`
- `packages_simple_server.R`: `observeEvent(input$packages-websocket_event)`
- `users_server.R`: `observeEvent(input$websocket_event)`
- Similar patterns in: `tnfp_server.R`, `package_items_server.R`, etc.

#### Task 3.2: Create Universal Shiny Handler
- **File**: New function in `shiny_handlers.js`
- **Purpose**: Single point to receive ALL CRUD events from R
- **Handler**: `Shiny.addCustomMessageHandler('universal_crud_event', ...)`

#### Task 3.3: Update R Server Modules
- **Pattern**: Replace entity-specific observers with universal pattern
- **Before**: `observeEvent(input$websocket_event, { ... entity specific logic ... })`
- **After**: `session$sendCustomMessage('universal_crud_event', standardized_data)`

#### Task 3.4: Remove Legacy Functions
**JavaScript functions to remove**:
- `removeTrackerRowSurgically()`
- `refreshCommentsHandler()`
- `syncTrackerDeletionHandler()`
- `removeCrossBrowserTrackerRow()`
- Entity-specific update functions

#### Testing Checkpoint 3.A
- [ ] Legacy code successfully removed
- [ ] No JavaScript console errors
- [ ] All CRUD operations still work
- [ ] Universal handler receives all events

### Phase 4: Backend Standardization (Days 4-5)
**Goal**: Ensure all backend endpoints use consistent broadcasting

#### Task 4.1: Create Universal Broadcast Helper
- **File**: `backend/app/api/v1/crud_broadcast_helper.py`
- **Functions**:
  - `broadcast_crud_event(operation, entity_type, entity_data, user_context)`
  - `standardize_crud_message()`
  - `extract_affected_entities()`

#### Task 4.2: Update All API Endpoints
**Endpoints to standardize** (use same broadcast pattern):
- Studies: `studies.py`
- Database Releases: `database_releases.py`
- Reporting Efforts: `reporting_efforts.py`
- Reporting Effort Items: `reporting_effort_items.py`
- Trackers: `reporting_effort_tracker.py`
- Comments: `tracker_comments.py`
- TNFP: `text_elements.py`
- Packages: `packages.py`
- Users: `users.py`

#### Task 4.3: Implement Consistent Error Handling
- **Standard Pattern**: All endpoints handle WebSocket broadcast failures gracefully
- **Fallback**: If broadcast fails, operation still succeeds
- **Logging**: Consistent error logging for debugging

#### Testing Checkpoint 4.A
- [ ] All endpoints use standardized broadcasting
- [ ] Message format is consistent across all entity types
- [ ] Error handling works properly
- [ ] No breaking changes to existing API contracts

### Phase 5: UI Enhancement (Days 5-6)
**Goal**: Create consistent visual feedback and conflict resolution

#### Task 5.1: Universal Update Animations
- **File**: Add CSS to `crud_activity_manager.js` or separate CSS file
- **Animations**:
  - `crud-create`: Green slide-in for new items
  - `crud-update`: Yellow flash for updated items
  - `crud-delete`: Red fade-out for deleted items
  - `crud-pending`: Subtle indicator for queued updates

#### Task 5.2: Conflict Resolution Dialog
- **UI Component**: Modal dialog for edit conflicts
- **Features**:
  - Side-by-side comparison of changes
  - Options: Keep mine / Take theirs / Merge
  - Entity-agnostic (works for any type)

#### Task 5.3: Universal Notification System
- **Types**:
  - Silent updates (badges, counts)
  - Info notifications (non-conflicting updates)
  - Warning notifications (queued updates)
  - Error notifications (conflicts requiring attention)

#### Task 5.4: Update Queue Indicator
- **Visual**: Small, non-intrusive indicator showing pending updates
- **Location**: Corner of screen or near action buttons
- **Interactive**: Click to apply queued updates immediately

#### Testing Checkpoint 5.A
- [ ] Animations work consistently across all entity types
- [ ] Conflict dialog displays properly
- [ ] Notification system provides clear feedback
- [ ] Queue indicator is visible but not annoying

### Phase 6: Comprehensive Testing (Days 6-7)
**Goal**: Verify system works reliably across all scenarios

#### Task 6.1: Single-User Testing
**Test Matrix**: Each entity type × Each CRUD operation
- [ ] Studies: Create, Read, Update, Delete
- [ ] Database Releases: Create, Read, Update, Delete
- [ ] Reporting Efforts: Create, Read, Update, Delete
- [ ] Trackers: Create, Read, Update, Delete
- [ ] Comments: Create, Read, Update, Delete, Resolve
- [ ] TNFP: Create, Read, Update, Delete
- [ ] Packages: Create, Read, Update, Delete
- [ ] Package Items: Create, Read, Update, Delete
- [ ] Users: Create, Read, Update, Delete

#### Task 6.2: Multi-User Conflict Testing
**Scenarios to test**:
- [ ] User A editing Study X, User B deletes Study X
- [ ] User A creating Tracker, User B updates same Reporting Effort
- [ ] User A has Comment modal open, User B adds comment to same tracker
- [ ] User A has Edit modal open, User B updates same entity
- [ ] Multiple users rapid-fire creating/deleting

#### Task 6.3: Performance Testing
- [ ] 100+ queued updates don't cause lag
- [ ] WebSocket reconnection works properly
- [ ] Memory usage stays reasonable over time
- [ ] Large datasets (1000+ rows) handle updates smoothly

#### Task 6.4: Browser Compatibility Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Edge (latest)
- [ ] Multiple tabs of same browser
- [ ] Mixed browsers (Chrome + Firefox simultaneously)

#### Testing Checkpoint 6.A
- [ ] All single-user tests pass
- [ ] Multi-user conflicts handled gracefully
- [ ] Performance is acceptable
- [ ] Works across different browsers

## Code Removal Checklist

### JavaScript Files

#### `admin-frontend/www/websocket_client.js`
**Remove these functions**:
```javascript
// Lines ~397-495
window.removeTrackerRowSurgically = function(trackerId, deleteContext = {}) { ... }

// Lines ~497-539
function showSurgicalSuccessIndicator(count) { ... }

// Lines ~541-571
function showDeleteNotification(deleteContext) { ... }

// Lines ~573-581
function getCurrentUsername() { ... }

// Lines ~583-596
window.refreshTrackersOptimized = function(reportingEffortId) { ... }

// Lines ~598-752
function addTrackerRowAnimations() { ... }
```

**Remove entity-specific routing** (Lines ~107-176):
```javascript
// Remove all the if/else chains for entity routing
if (data.type.startsWith('study_')) { ... }
else if (data.type.startsWith('reporting_effort_tracker_')) { ... }
// etc.
```

#### `admin-frontend/www/shiny_handlers.js`
**Remove these functions**:
```javascript
// Lines ~29-83
function refreshCommentsHandler(message) { ... }

// Lines ~89-226  
function syncTrackerDeletionHandler(message) { ... }
function removeCrossBrowserTrackerRow(trackerId, deletionData) { ... }

// Lines ~236-416
// Move activity tracking to crud_activity_manager.js
let deferredUpdates = [];
let lastUserActivity = Date.now();
function trackUserActivity() { ... }
function isUserActivelyWorking() { ... }
function queueDeferredUpdate(updateType, updateData) { ... }
function applyDeferredUpdates() { ... }
```

### R Server Files

#### Pattern to replace in ALL `*_server.R` files:
**Remove**:
```r
observeEvent(input$websocket_event, {
  # Entity-specific WebSocket handling
}, ignoreNULL = TRUE)

observeEvent(input$delete_notification, {
  # Entity-specific delete notifications  
}, ignoreNULL = TRUE)

observeEvent(input$surgical_removal_fallback, {
  # Entity-specific fallback handling
}, ignoreNULL = TRUE)
```

**Replace with**:
```r
# Universal CRUD event handler (same pattern for all modules)
observe({
  # Send any module updates to universal handler
  session$sendCustomMessage("universal_crud_event", list(
    module = "module_name",
    data = reactive_data(),
    timestamp = Sys.time()
  ))
})
```

## Testing Commands

### Backend Testing
```bash
# Test individual endpoints
curl -X POST http://localhost:8000/api/v1/studies/ -H "Content-Type: application/json" -d '{"label":"Test Study"}'
curl -X PUT http://localhost:8000/api/v1/studies/1 -H "Content-Type: application/json" -d '{"label":"Updated Study"}'
curl -X DELETE http://localhost:8000/api/v1/studies/1

# Check WebSocket broadcasting (watch console in browser)
```

### Frontend Testing with Playwright MCP
```javascript
// Test modal state detection
await page.click('[data-action="edit"]');
await page.evaluate(() => window.crudManager.getUserContext());

// Test update queuing
await page.evaluate(() => window.crudManager.queueUpdate('test_update', {}));
await page.waitForSelector('.crud-pending-indicator');

// Test cross-browser sync
// (Open second browser session and trigger updates)
```

## Rollback Plan

If any phase fails:

1. **Phase 1 failure**: 
   - Delete `crud_activity_manager.js`
   - Revert any changes to existing files
   - No WebSocket impact

2. **Phase 2 failure**:
   - Revert `websocket_client.js` changes
   - Keep activity manager for future use
   - System returns to current behavior

3. **Phase 3 failure**:
   - Restore removed legacy functions
   - Keep universal manager alongside legacy
   - Gradually migrate later

4. **Phase 4 failure**:
   - Revert backend endpoint changes
   - Frontend continues working with mixed message formats
   - Complete backend standardization later

5. **Phase 5-6 failure**:
   - Core functionality remains intact
   - Polish features can be added incrementally

## Success Criteria

### Functional Requirements
- [ ] All CRUD operations work consistently across entity types
- [ ] Cross-browser synchronization maintains data integrity
- [ ] User work is never lost due to updates
- [ ] Conflicts are detected and resolved appropriately
- [ ] Performance is equal or better than current system

### User Experience Requirements
- [ ] Updates are non-disruptive to active work
- [ ] Visual feedback is clear and consistent
- [ ] System behavior is predictable
- [ ] Error states are handled gracefully

### Technical Requirements
- [ ] Code is maintainable and well-documented
- [ ] Memory usage is reasonable
- [ ] WebSocket connections are stable
- [ ] System is extensible for new entity types

## Timeline

- **Week 1**: Phases 1-3 (Foundation and Integration)
- **Week 2**: Phases 4-6 (Standardization and Testing)
- **Week 3**: Bug fixes, optimization, documentation

## Notes for Implementation

### Pitfalls to Avoid

1. **Removing too much code at once**: Remove legacy code incrementally, test at each step
2. **Breaking WebSocket connections**: Keep connection management intact while changing handlers
3. **UI state inconsistency**: Ensure new system handles all edge cases that legacy code covered
4. **Performance regression**: Monitor memory usage and event processing times
5. **Cross-browser compatibility**: Test frequently across different browsers
6. **Database transaction issues**: Ensure backend changes don't affect database integrity

### Best Practices

1. **Test frequently**: After each major change, test basic functionality
2. **Keep backups**: Commit often, keep working versions available
3. **Document assumptions**: Write down any assumptions about how system should behave
4. **Monitor performance**: Use browser dev tools to watch for memory leaks or slow operations
5. **Log everything**: Add comprehensive logging during development, remove in production

This plan provides a structured approach to implementing the universal CRUD update system while minimizing risk and ensuring thorough testing at each stage.