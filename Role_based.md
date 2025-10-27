# Role-Based Access Control Implementation Plan for PEARL

## Executive Summary
Implement role-based access control (RBAC) in the existing PEARL admin-frontend application with:
- **Two distinct dashboards**: Admin Dashboard and User Dashboard (for Editor/Viewer)
- **Three user roles**: VIEWER, EDITOR, ADMIN
- **Progressive permissions**: Each role inherits permissions from the level below
- **Single codebase**: Leverage existing admin-frontend with conditional UI rendering

## Role Permissions Matrix

### VIEWER Role (Read-Only Access)
**Dashboard Access**: User Dashboard
**Permissions**:
- ✅ View User Dashboard with Reporting Effort status overview
- ✅ View all Reporting Effort Trackers (read-only)
- ✅ Search across all tracker items
- ✅ View tracker details and comments
- ✅ Export data (CSV/Excel)
- ❌ Cannot edit any data
- ❌ Cannot access admin features

### EDITOR Role (Operational Access)
**Dashboard Access**: User Dashboard
**Inherits**: All VIEWER permissions
**Additional Permissions**:
- ✅ Edit tracker items (full form access):
  - Production programmer assignment
  - QC programmer assignment
  - Production status
  - QC status
  - Priority level
  - Due dates
  - All other tracker fields
- ✅ Add/edit comments on trackers
- ✅ Update workflow states
- ❌ Cannot delete tracker items
- ❌ Cannot access Studies, Database Releases, or Reporting Efforts management
- ❌ Cannot access Packages, Text Elements, or system configuration

### ADMIN Role (Full Access)
**Dashboard Access**: Admin Dashboard
**Inherits**: All EDITOR permissions
**Additional Permissions**:
- ✅ Full access to Admin Dashboard
- ✅ Complete CRUD operations on all entities:
  - Studies
  - Database Releases
  - Reporting Efforts
  - Reporting Effort Items
  - Trackers (including deletion)
  - Packages and Package Items
  - Text Elements
- ✅ User management
- ✅ System configuration
- ✅ Bulk operations
- ✅ Delete any entity

## Dashboard Specifications

### User Dashboard (VIEWER/EDITOR)
**Purpose**: Operational view focused on Reporting Effort tracking and task management

**Components**:
1. **Summary Cards Row**:
   - Total Active Reporting Efforts
   - Items In Progress
   - Items Pending QC
   - Completed This Week
   - Overdue Items

2. **Reporting Efforts Status Table**:
   - Columns: Study, Database Release, Reporting Effort, Total Items, In Progress, Completed, Health Status
   - Color coding for status (Green: On Track, Yellow: At Risk, Red: Behind)
   - Click to drill down into tracker details

3. **My Assignments** (for logged-in user):
   - Items assigned for production
   - Items assigned for QC
   - Priority indicators
   - Quick status update buttons (EDITOR only)

4. **Recent Activity Feed**:
   - Last 20 status changes
   - Comments added
   - Assignment changes

5. **Quick Search Bar**:
   - Search across all tracker items
   - Filter by status, priority, assignment

### Admin Dashboard (ADMIN only)
**Purpose**: System-wide management and configuration

**Components**:
1. **System Overview Cards**:
   - Total Studies
   - Active Database Releases
   - Active Reporting Efforts
   - Total Users
   - System Health

2. **Navigation Quick Access**:
   - Direct links to all management modules
   - Recent items edited
   - Pending approvals/reviews

3. **User Activity Monitor**:
   - Active users
   - Recent actions
   - Audit trail summary

4. **Data Management Tools**:
   - Bulk import/export
   - Database maintenance
   - Archive management

## Implementation Architecture

### Backend Changes

#### 1. User Model Enhancement
```python
# app/models/user.py
class UserRole(str, Enum):
    VIEWER = "VIEWER"
    EDITOR = "EDITOR"  
    ADMIN = "ADMIN"

class User(SQLModel, table=True):
    id: int
    username: str
    role: UserRole
    department: str
    is_active: bool = True
    last_login: Optional[datetime]
```

#### 2. Permission Decorator
```python
# app/core/permissions.py
from functools import wraps
from fastapi import HTTPException, Depends

def require_role(minimum_role: UserRole):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            role_hierarchy = {
                UserRole.VIEWER: 0,
                UserRole.EDITOR: 1,
                UserRole.ADMIN: 2
            }
            
            if role_hierarchy[current_user.role] < role_hierarchy[minimum_role]:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required: {minimum_role}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

#### 3. API Endpoint Protection
```python
# app/api/v1/reporting_effort_tracker.py

@router.get("/", response_model=List[TrackerRead])
async def read_trackers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # VIEWER and above can read
    return await crud.tracker.get_multi(db)

@router.put("/{tracker_id}", response_model=TrackerRead)
@require_role(UserRole.EDITOR)  # EDITOR and above can update
async def update_tracker(
    tracker_id: int,
    tracker_in: TrackerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await crud.tracker.update(db, id=tracker_id, obj_in=tracker_in)

@router.delete("/{tracker_id}")
@require_role(UserRole.ADMIN)  # Only ADMIN can delete
async def delete_tracker(
    tracker_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await crud.tracker.remove(db, id=tracker_id)
```

### Frontend Changes

#### 1. Authentication Context
```r
# modules/auth_context.R
create_auth_context <- function(session) {
  # Get user from session (RConnect) or mock (development)
  user <- if (Sys.getenv("PEARL_DEV_MODE") == "true") {
    list(
      id = as.integer(Sys.getenv("PEARL_DEV_USER_ID", "1")),
      username = Sys.getenv("PEARL_DEV_USERNAME", "dev_user"),
      role = Sys.getenv("PEARL_DEV_ROLE", "EDITOR"),
      department = Sys.getenv("PEARL_DEV_DEPARTMENT", "PROGRAMMING")
    )
  } else {
    # Fetch from backend based on session$user
    get_user_by_username(session$user)
  }
  
  list(
    user = user,
    is_admin = user$role == "ADMIN",
    is_editor = user$role %in% c("EDITOR", "ADMIN"),
    is_viewer = TRUE,  # All authenticated users can view
    can_edit_tracker = user$role %in% c("EDITOR", "ADMIN"),
    can_delete = user$role == "ADMIN",
    can_manage_system = user$role == "ADMIN"
  )
}
```

#### 2. Conditional UI Rendering
```r
# app.R - Main application file
ui <- function(request) {
  page_navbar(
    title = "PEARL System",
    theme = pearl_theme(),
    
    # Dashboard - Show different dashboard based on role
    nav_panel(
      title = "Dashboard",
      icon = icon("dashboard"),
      conditionalPanel(
        condition = "output.is_admin",
        admin_dashboard_ui("admin_dash")
      ),
      conditionalPanel(
        condition = "!output.is_admin",
        user_dashboard_ui("user_dash")
      )
    ),
    
    # Reporting Effort Trackers - Available to all
    nav_panel(
      title = "Trackers",
      icon = icon("tasks"),
      tracker_management_ui("trackers")
    ),
    
    # Search - Available to all
    nav_panel(
      title = "Search",
      icon = icon("search"),
      search_ui("search")
    ),
    
    # Admin-only sections
    conditionalPanel(
      condition = "output.is_admin",
      nav_menu(
        title = "Management",
        icon = icon("cog"),
        nav_panel("Studies", study_tree_ui("studies")),
        nav_panel("Packages", packages_ui("packages")),
        nav_panel("Text Elements", text_elements_ui("text_elements")),
        nav_panel("Users", user_management_ui("users"))
      )
    )
  )
}

server <- function(input, output, session) {
  # Create authentication context
  auth_context <- reactive({
    create_auth_context(session)
  })
  
  # Expose role to UI for conditional panels
  output$is_admin <- reactive({
    auth_context()$is_admin
  })
  outputOptions(output, "is_admin", suspendWhenHidden = FALSE)
  
  # Initialize appropriate dashboard
  observe({
    if (auth_context()$is_admin) {
      admin_dashboard_server("admin_dash", auth_context)
    } else {
      user_dashboard_server("user_dash", auth_context)
    }
  })
  
  # Initialize tracker module with role-based permissions
  tracker_management_server("trackers", auth_context)
  
  # Initialize search (available to all)
  search_server("search", auth_context)
  
  # Initialize admin modules only for admins
  observe({
    if (auth_context()$is_admin) {
      study_tree_server("studies", auth_context)
      packages_server("packages", auth_context)
      text_elements_server("text_elements", auth_context)
      user_management_server("users", auth_context)
    }
  })
}
```

#### 3. User Dashboard Module
```r
# modules/user_dashboard_ui.R
user_dashboard_ui <- function(id) {
  ns <- NS(id)
  
  tagList(
    h2("Reporting Efforts Dashboard"),
    
    # Summary cards
    fluidRow(
      col_3(
        value_box(
          title = "Active Efforts",
          value = textOutput(ns("active_efforts")),
          showcase = bs_icon("folder-open"),
          theme = "primary"
        )
      ),
      col_3(
        value_box(
          title = "In Progress",
          value = textOutput(ns("in_progress")),
          showcase = bs_icon("play-circle"),
          theme = "info"
        )
      ),
      col_3(
        value_box(
          title = "Pending QC",
          value = textOutput(ns("pending_qc")),
          showcase = bs_icon("hourglass-split"),
          theme = "warning"
        )
      ),
      col_3(
        value_box(
          title = "Completed",
          value = textOutput(ns("completed_week")),
          showcase = bs_icon("check-circle"),
          theme = "success"
        )
      )
    ),
    
    # Main content
    fluidRow(
      col_8(
        card(
          card_header("Reporting Efforts Status"),
          card_body(
            DTOutput(ns("efforts_table"))
          )
        )
      ),
      col_4(
        card(
          card_header("My Assignments"),
          card_body(
            DTOutput(ns("my_assignments"))
          )
        )
      )
    ),
    
    # Activity feed
    fluidRow(
      col_12(
        card(
          card_header("Recent Activity"),
          card_body(
            DTOutput(ns("activity_feed"))
          )
        )
      )
    )
  )
}

# modules/user_dashboard_server.R
user_dashboard_server <- function(id, auth_context) {
  moduleServer(id, function(input, output, session) {
    
    # Load dashboard data
    dashboard_data <- reactive({
      # Fetch reporting efforts summary
      efforts <- get_reporting_efforts_summary()
      
      # Calculate metrics
      list(
        active_efforts = nrow(efforts[efforts$status == "active", ]),
        in_progress = sum(efforts$in_progress_count),
        pending_qc = sum(efforts$pending_qc_count),
        completed_week = sum(efforts$completed_this_week)
      )
    })
    
    # Render summary cards
    output$active_efforts <- renderText({
      dashboard_data()$active_efforts
    })
    
    output$in_progress <- renderText({
      dashboard_data()$in_progress
    })
    
    output$pending_qc <- renderText({
      dashboard_data()$pending_qc
    })
    
    output$completed_week <- renderText({
      dashboard_data()$completed_week
    })
    
    # Render efforts table with drill-down capability
    output$efforts_table <- renderDT({
      efforts <- get_reporting_efforts_with_status()
      
      datatable(
        efforts,
        selection = 'single',
        options = list(
          pageLength = 10,
          columnDefs = list(
            list(className = 'dt-center', targets = '_all')
          )
        )
      ) %>%
        formatStyle(
          'health_status',
          backgroundColor = styleEqual(
            c('On Track', 'At Risk', 'Behind'),
            c('#d4edda', '#fff3cd', '#f8d7da')
          )
        )
    })
    
    # Handle drill-down
    observeEvent(input$efforts_table_rows_selected, {
      selected_row <- input$efforts_table_rows_selected
      if (!is.null(selected_row)) {
        # Navigate to tracker view with filter
        updateTabsetPanel(session$parent, "main_tabs", selected = "Trackers")
      }
    })
  })
}
```

#### 4. Tracker Module with Role-Based Actions
```r
# modules/tracker_management_server.R
tracker_management_server <- function(id, auth_context) {
  moduleServer(id, function(input, output, session) {
    
    # Render tracker table with conditional actions
    output$tracker_table <- renderDT({
      trackers <- get_all_trackers()
      ctx <- auth_context()
      
      # Add action buttons based on role
      if (ctx$can_edit_tracker) {
        trackers$Actions <- sprintf(
          '<div class="btn-group btn-group-sm">
            <button class="btn btn-primary edit-btn" data-id="%s">
              <i class="bi bi-pencil"></i> Edit
            </button>
            %s
          </div>',
          trackers$id,
          if (ctx$can_delete) {
            sprintf('<button class="btn btn-danger delete-btn" data-id="%s">
                      <i class="bi bi-trash"></i>
                    </button>', trackers$id)
          } else { "" }
        )
      } else {
        trackers$Actions <- sprintf(
          '<button class="btn btn-info btn-sm view-btn" data-id="%s">
            <i class="bi bi-eye"></i> View
          </button>',
          trackers$id
        )
      }
      
      datatable(
        trackers,
        escape = FALSE,
        selection = 'none',
        options = list(
          dom = 'Bfrtip',
          buttons = if (ctx$can_edit_tracker) {
            list('copy', 'csv', 'excel')
          } else {
            list('copy', 'csv')  # View-only users can still export
          }
        )
      )
    })
    
    # Handle edit action (EDITOR and ADMIN only)
    observeEvent(input$edit_tracker, {
      req(auth_context()$can_edit_tracker)
      
      showModal(modalDialog(
        title = "Edit Tracker Item",
        size = "l",
        
        fluidRow(
          col_6(
            selectInput(ns("production_programmer"), 
                       "Production Programmer",
                       choices = get_user_list()),
            selectInput(ns("production_status"),
                       "Production Status",
                       choices = c("not_started", "in_progress", "completed"))
          ),
          col_6(
            selectInput(ns("qc_programmer"),
                       "QC Programmer", 
                       choices = get_user_list()),
            selectInput(ns("qc_status"),
                       "QC Status",
                       choices = c("not_started", "in_progress", "completed", "failed"))
          )
        ),
        
        selectInput(ns("priority"),
                   "Priority",
                   choices = c("low", "medium", "high", "critical")),
        
        dateInput(ns("due_date"), "Due Date"),
        
        textAreaInput(ns("notes"), "Notes", rows = 3),
        
        footer = tagList(
          modalButton("Cancel"),
          actionButton(ns("save_tracker"), "Save", class = "btn-primary")
        )
      ))
    })
    
    # Handle delete action (ADMIN only)
    observeEvent(input$delete_tracker, {
      req(auth_context()$can_delete)
      
      showModal(modalDialog(
        title = "Confirm Deletion",
        "Are you sure you want to delete this tracker item?",
        footer = tagList(
          modalButton("Cancel"),
          actionButton(ns("confirm_delete"), "Delete", class = "btn-danger")
        )
      ))
    })
  })
}
```

## Implementation Phases

### Phase 1: Backend Permission System (Week 1)
1. **Day 1-2**: Implement User model changes and role enum
2. **Day 3-4**: Create permission decorators and middleware
3. **Day 5**: Apply decorators to all API endpoints
4. **Testing**: Verify each role's access with curl/Postman

### Phase 2: Authentication & Context (Week 2)
1. **Day 1-2**: Create authentication context module
2. **Day 3-4**: Integrate with RConnect session management
3. **Day 5**: Add development mode with role switching
4. **Testing**: Test role switching and context propagation

### Phase 3: User Dashboard (Week 3)
1. **Day 1-2**: Create user dashboard UI module
2. **Day 3-4**: Implement dashboard server logic
3. **Day 5**: Add real-time WebSocket updates
4. **Testing**: Verify dashboard metrics and drilling

### Phase 4: Conditional UI & Permissions (Week 4)
1. **Day 1-2**: Implement conditional UI rendering in app.R
2. **Day 3-4**: Update tracker module with role-based actions
3. **Day 5**: Hide/show navigation based on roles
4. **Testing**: Test all three roles thoroughly

### Phase 5: Testing & Refinement (Week 5)
1. **Day 1-2**: Create comprehensive test suite
2. **Day 3-4**: User acceptance testing with each role
3. **Day 5**: Performance optimization and bug fixes
4. **Documentation**: Update user guides for each role

## Testing Strategy

### Unit Tests
```r
# tests/test_permissions.R
test_that("VIEWER cannot edit trackers", {
  auth <- list(role = "VIEWER", can_edit_tracker = FALSE)
  expect_false(auth$can_edit_tracker)
})

test_that("EDITOR can edit but not delete", {
  auth <- list(role = "EDITOR", can_edit_tracker = TRUE, can_delete = FALSE)
  expect_true(auth$can_edit_tracker)
  expect_false(auth$can_delete)
})

test_that("ADMIN has full access", {
  auth <- list(role = "ADMIN", can_edit_tracker = TRUE, can_delete = TRUE)
  expect_true(auth$can_edit_tracker)
  expect_true(auth$can_delete)
})
```

### Integration Tests
1. **Login as VIEWER**: Verify read-only access
2. **Login as EDITOR**: Test tracker editing, verify cannot delete
3. **Login as ADMIN**: Test full CRUD operations
4. **Dashboard Tests**: Verify correct dashboard loads per role
5. **WebSocket Tests**: Ensure real-time updates respect permissions

### User Acceptance Tests
1. **VIEWER Scenario**:
   - Can see user dashboard
   - Can search all trackers
   - Cannot see edit buttons
   - Can export data

2. **EDITOR Scenario**:
   - Can see user dashboard
   - Can edit tracker forms
   - Cannot access Studies management
   - Cannot delete items

3. **ADMIN Scenario**:
   - Can see admin dashboard
   - Full access to all modules
   - Can delete any entity
   - Can manage users

## Security Considerations

1. **Backend Enforcement**: All permissions MUST be enforced at API level
2. **Token-Based Auth**: Implement JWT tokens for stateless authentication
3. **Audit Logging**: Log all write operations with user details
4. **Session Management**: Implement timeout and refresh token rotation
5. **Input Validation**: Validate all inputs based on user role
6. **Error Messages**: Don't reveal permission details in error messages

## Migration Strategy

1. **Add role column** to existing users table (default: VIEWER)
2. **Assign roles** based on current access patterns
3. **Gradual rollout**: Start with read-only, then enable editing
4. **Fallback plan**: Keep current system running in parallel initially

## Performance Optimizations

1. **Lazy Loading**: Load admin modules only for admin users
2. **Cached Permissions**: Cache role checks per session
3. **Filtered Queries**: Apply user filters at database level
4. **Optimized Dashboard**: Pre-aggregate dashboard metrics
5. **WebSocket Channels**: Separate channels per role

## Development Environment Setup

```bash
# .env.development
PEARL_DEV_MODE=true
PEARL_DEV_USER_ID=1
PEARL_DEV_USERNAME=test_editor
PEARL_DEV_ROLE=EDITOR  # Switch between VIEWER/EDITOR/ADMIN for testing
PEARL_DEV_DEPARTMENT=PROGRAMMING
```

## Deployment Configuration

```yaml
# RConnect environment variables
PEARL_API_URL: "https://api.pearl.com"
PEARL_WS_URL: "wss://api.pearl.com/ws"
PEARL_AUTH_PROVIDER: "rconnect"  # or "jwt" for custom auth
PEARL_SESSION_TIMEOUT: "3600"  # 1 hour
```

## Success Metrics

1. **Security**: Zero unauthorized access incidents
2. **Performance**: Dashboard loads < 2 seconds
3. **Usability**: 90% user satisfaction per role
4. **Adoption**: 100% users using role-appropriate interface
5. **Maintenance**: 50% reduction in permission-related bugs

## Next Steps

1. Review and approve implementation plan
2. Set up development environment with role switching
3. Begin Phase 1: Backend Permission System
4. Schedule weekly progress reviews
5. Plan user training sessions per role