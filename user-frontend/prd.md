## **PEARL User Frontend Implementation Plan (Combined Approach)**

### **Current System Analysis**

The PEARL system has:
- **Backend**: FastAPI with async PostgreSQL, real-time WebSocket broadcasting
- **Admin Frontend**: R Shiny with modular architecture (25+ modules), API client, WebSocket sync
- **User Roles**: ADMIN/EDITOR/VIEWER with department assignments (PROGRAMMING, BIOSTATISTICS, MANAGEMENT)
- **Core Entities**: Study → Database Release → Reporting Effort → Reporting Effort Items → Trackers
- **Existing Search**: Basic text search for text elements (PostgreSQL ready for full-text search)
- **Authentication**: User model exists, no session management implemented yet

### **Optimal Architecture Strategy (Combined Approach)**

This plan combines the best of both approaches:
- **Phase 1-2**: PostgreSQL full-text search for quick MVP delivery
- **Phase 3-4**: Client-side semantic search for intelligent querying
- **Throughout**: Shared module approach to eliminate code duplication

#### **1. Shared Module Library Approach** 
*Maximize code reuse without duplication*

**Create `shared/` directory structure:**
```
PEARL/
├── shared/                          # NEW: Common modules
│   ├── api/                        # Shared API clients
│   │   ├── client.R               # Core API client
│   │   ├── auth.R                 # Authentication handling
│   │   ├── trackers.R             # Tracker-specific endpoints
│   │   ├── search.R               # Search endpoints (PostgreSQL)
│   │   └── websocket.R            # WebSocket utilities
│   ├── ui/                        # Shared UI components  
│   │   ├── dashboard_cards.R      # Reusable dashboard components
│   │   ├── data_tables.R          # Configured DT datatables
│   │   ├── search_components.R    # Search UI elements
│   │   └── theme.R                # Common bslib theme
│   ├── utils/                     # Business logic utilities
│   │   ├── data_processing.R      # Common data transforms
│   │   ├── user_context.R         # Role/department logic
│   │   ├── postgres_search.R      # PostgreSQL search utilities
│   │   └── semantic_search.R      # Client-side semantic search (Phase 2)
│   └── models/                    # Data models/schemas
│       └── entities.R             # Common entity structures
├── admin-frontend/                # Keep existing (will migrate to shared/)
├── user-frontend/                 # New focused version
│   ├── modules/                   # User-specific modules
│   ├── www/                       # User-specific assets (symlinks to shared)
│   └── app.R                      # User app entry point
└── backend/                       # Add search endpoints
```

#### **2. User Frontend Module Architecture**
*Role-based, task-focused modules*

**Core User Modules:**
```
user-frontend/modules/
├── auth_ui.R                      # Login/session management UI
├── auth_server.R                  # Authentication logic
├── user_dashboard_ui.R            # Dashboard interface
├── user_dashboard_server.R        # Dashboard logic
├── my_assignments_ui.R            # Assignment view UI
├── my_assignments_server.R        # Assignment logic
├── search_ui.R                    # Search interface
├── search_server.R                # Search logic (PostgreSQL first)
├── tracker_view_ui.R              # Read-only tracker UI
├── tracker_view_server.R          # Tracker display logic
├── tracker_updates_ui.R           # Edit interface (EDITOR+)
├── tracker_updates_server.R       # Update logic
├── notifications_ui.R             # Notification display
└── notifications_server.R         # Real-time notification logic
```

---

## **DETAILED TASK BREAKDOWN FOR JUNIOR DEVELOPERS**

### **PHASE 1: Foundation & Backend Search (Week 1)**

#### **Task 1: Create Shared Directory Structure**
**Goal**: Set up the folder structure for shared code that both admin and user frontends will use.

**Subtasks:**

**1.1 Create Directory Structure**
```bash
# Instructions for Junior Developer:
# 1. Open terminal/command prompt
# 2. Navigate to PEARL root directory: cd C:/python/PEARL
# 3. Run these commands one by one:

mkdir shared
mkdir shared/api
mkdir shared/ui
mkdir shared/utils
mkdir shared/models

# 4. Create placeholder files (copy-paste each command):
echo "# Shared API Client" > shared/api/client.R
echo "# Authentication Module" > shared/api/auth.R
echo "# Tracker API Endpoints" > shared/api/trackers.R
echo "# Search API Endpoints" > shared/api/search.R
echo "# WebSocket Utilities" > shared/api/websocket.R
echo "# Dashboard Cards" > shared/ui/dashboard_cards.R
echo "# Data Table Configs" > shared/ui/data_tables.R
echo "# Search Components" > shared/ui/search_components.R
echo "# Theme Configuration" > shared/ui/theme.R
echo "# Data Processing" > shared/utils/data_processing.R
echo "# User Context" > shared/utils/user_context.R
echo "# PostgreSQL Search" > shared/utils/postgres_search.R
echo "# Entity Models" > shared/models/entities.R
```

**1.2 Extract API Client from Admin Frontend**
```r
# Instructions:
# 1. Open admin-frontend/modules/api_client.R
# 2. Copy lines 1-100 (basic HTTP functions)
# 3. Paste into shared/api/client.R
# 4. Add this header at the top:

# shared/api/client.R
# Core HTTP client functions shared between admin and user frontends
# Extracted from admin-frontend/modules/api_client.R
# Last updated: [TODAY'S DATE]

library(httr2)
library(jsonlite)

# Get the API base URL from environment
get_api_base_url <- function() {
  url <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  # Remove trailing slash if present
  gsub("/$", "", url)
}

# Generic GET request function
api_get <- function(endpoint, params = NULL) {
  url <- paste0(get_api_base_url(), endpoint)
  
  tryCatch({
    request <- httr2::request(url)
    
    # Add query parameters if provided
    if (!is.null(params)) {
      request <- httr2::req_url_query(request, !!!params)
    }
    
    response <- httr2::req_perform(request)
    
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Generic POST request function
api_post <- function(endpoint, body = NULL) {
  url <- paste0(get_api_base_url(), endpoint)
  
  tryCatch({
    request <- httr2::request(url) |>
      httr2::req_method("POST")
    
    if (!is.null(body)) {
      request <- httr2::req_body_json(request, body)
    }
    
    response <- httr2::req_perform(request)
    
    if (httr2::resp_status(response) %in% c(200, 201)) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Add similar functions for PUT and DELETE...
```

#### **Task 2: Add PostgreSQL Full-Text Search to Backend**
**Goal**: Enable fast text search across all tracker fields in the database.

**2.1 Create Search Migration**
```python
# Instructions:
# 1. Open terminal in backend directory: cd backend
# 2. Create new migration:
# uv run alembic revision --autogenerate -m "add_fulltext_search"
# 3. Open the new migration file in backend/migrations/versions/
# 4. Add this code to the upgrade() function:

def upgrade():
    # Add search vector column to reporting_effort_item_tracker table
    op.execute("""
        ALTER TABLE reporting_effort_item_tracker 
        ADD COLUMN IF NOT EXISTS search_vector tsvector;
    """)
    
    # Create function to update search vector
    op.execute("""
        CREATE OR REPLACE FUNCTION update_tracker_search_vector() 
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := 
                setweight(to_tsvector('english', coalesce(NEW.production_status, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.qc_status, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.priority, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.qc_level, '')), 'C');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger to auto-update search vector
    op.execute("""
        CREATE TRIGGER tracker_search_vector_update 
        BEFORE INSERT OR UPDATE ON reporting_effort_item_tracker
        FOR EACH ROW EXECUTE FUNCTION update_tracker_search_vector();
    """)
    
    # Create GIN index for fast searching
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_tracker_search_vector 
        ON reporting_effort_item_tracker USING GIN(search_vector);
    """)
    
    # Update existing rows
    op.execute("""
        UPDATE reporting_effort_item_tracker 
        SET search_vector = 
            setweight(to_tsvector('english', coalesce(production_status, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(qc_status, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(priority, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(qc_level, '')), 'C');
    """)

def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_tracker_search_vector;")
    op.execute("DROP TRIGGER IF EXISTS tracker_search_vector_update ON reporting_effort_item_tracker;")
    op.execute("DROP FUNCTION IF EXISTS update_tracker_search_vector();")
    op.execute("ALTER TABLE reporting_effort_item_tracker DROP COLUMN IF EXISTS search_vector;")

# 5. Run the migration:
# uv run alembic upgrade head
```

**2.2 Create Search API Endpoint**
```python
# Instructions:
# 1. Create new file: backend/app/api/v1/tracker_search.py
# 2. Copy this code exactly:

"""Tracker search API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.schemas.reporting_effort_item_tracker import ReportingEffortItemTrackerWithDetails

router = APIRouter()

@router.get("/search", response_model=List[ReportingEffortItemTrackerWithDetails])
async def search_trackers(
    q: str = Query(..., description="Search query"),
    user_id: Optional[int] = Query(None, description="Filter by assigned user"),
    limit: int = Query(100, description="Maximum results"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search trackers using PostgreSQL full-text search.
    
    Instructions for understanding this endpoint:
    - Takes a search query string 'q'
    - Optionally filters by user_id (for assigned items only)
    - Returns matching trackers with relevance ranking
    """
    
    # Build the base query with full-text search
    query_sql = """
        SELECT t.*, 
               ts_rank(t.search_vector, plainto_tsquery('english', :search_query)) as rank,
               i.item_code, i.item_type, i.item_subtype
        FROM reporting_effort_item_tracker t
        JOIN reporting_effort_items i ON t.reporting_effort_item_id = i.id
        WHERE t.search_vector @@ plainto_tsquery('english', :search_query)
    """
    
    # Add user filter if provided
    if user_id:
        query_sql += """
            AND (t.production_programmer_id = :user_id 
                 OR t.qc_programmer_id = :user_id)
        """
    
    # Order by relevance and limit
    query_sql += """
        ORDER BY rank DESC
        LIMIT :limit
    """
    
    # Execute query
    result = await db.execute(
        text(query_sql),
        {"search_query": q, "user_id": user_id, "limit": limit}
    )
    
    # Convert to response models
    trackers = []
    for row in result:
        tracker_dict = {
            "id": row.id,
            "reporting_effort_item_id": row.reporting_effort_item_id,
            "production_status": row.production_status,
            "qc_status": row.qc_status,
            "priority": row.priority,
            "item_code": row.item_code,
            "item_type": row.item_type,
            "item_subtype": row.item_subtype,
            "relevance_score": row.rank
        }
        trackers.append(tracker_dict)
    
    return trackers

# 3. Register this router in backend/app/api/v1/__init__.py:
# Add this line:
# from app.api.v1 import tracker_search
# And in the api_router section:
# api_router.include_router(tracker_search.router, prefix="/tracker-search", tags=["search"])
```

#### **Task 3: Create Authentication Module**
**Goal**: Set up user authentication and session management.

**3.1 Create Shared Authentication Module**
```r
# Instructions:
# 1. Open shared/api/auth.R
# 2. Add this complete authentication module:

# shared/api/auth.R
# Authentication and session management
# For both development and production (RConnect) environments

library(httr2)
library(jsonlite)

# Source the base API client
source("shared/api/client.R")

# Check if running in development mode
is_dev_mode <- function() {
  Sys.getenv("PEARL_DEV_MODE", "false") == "true"
}

# Get current user (dev mode or RConnect)
get_current_user <- function(session = NULL) {
  if (is_dev_mode()) {
    # Development mode: return mock user
    return(list(
      id = as.integer(Sys.getenv("PEARL_DEV_USER_ID", "1")),
      username = Sys.getenv("PEARL_DEV_USERNAME", "dev_user"),
      role = Sys.getenv("PEARL_DEV_ROLE", "EDITOR"),
      department = Sys.getenv("PEARL_DEV_DEPARTMENT", "programming")
    ))
  } else if (!is.null(session) && !is.null(session$user)) {
    # RConnect production mode
    # Fetch user details from backend based on username
    response <- api_get(paste0("/api/v1/users/by-username/", session$user))
    
    if ("error" %in% names(response)) {
      # User not found - create with default VIEWER role
      new_user <- api_post("/api/v1/users/", list(
        username = session$user,
        role = "VIEWER",
        department = "programming"
      ))
      return(new_user)
    }
    
    return(response)
  } else {
    # Fallback to anonymous viewer
    return(list(
      id = 0,
      username = "anonymous",
      role = "VIEWER",
      department = NULL
    ))
  }
}

# Check if user has permission for an action
has_permission <- function(user, action) {
  if (is.null(user) || is.null(user$role)) {
    return(FALSE)
  }
  
  permissions <- list(
    VIEWER = c("view", "search", "export"),
    EDITOR = c("view", "search", "export", "edit", "comment", "update_status"),
    ADMIN = c("view", "search", "export", "edit", "comment", "update_status", 
              "delete", "bulk_update", "manage_users")
  )
  
  user_permissions <- permissions[[user$role]]
  return(action %in% user_permissions)
}

# Filter data based on user access
filter_by_user_access <- function(data, user) {
  if (is.null(user)) return(data.frame())
  
  # Admins see everything
  if (user$role == "ADMIN") return(data)
  
  # Others see only their assigned items
  if (!is.null(data$production_programmer_id) || !is.null(data$qc_programmer_id)) {
    filtered <- data[
      data$production_programmer_id == user$id | 
      data$qc_programmer_id == user$id,
    ]
    return(filtered)
  }
  
  return(data)
}

# Create user context object
create_user_context <- function(session = NULL) {
  user <- get_current_user(session)
  
  list(
    user = user,
    is_authenticated = user$id > 0,
    can_edit = has_permission(user, "edit"),
    can_delete = has_permission(user, "delete"),
    can_comment = has_permission(user, "comment"),
    filter_function = function(data) filter_by_user_access(data, user)
  )
}
```

**3.2 Create Development Mode Configuration**
```bash
# Instructions:
# 1. Create file: user-frontend/.env.development
# 2. Add these environment variables:

# Development Mode Settings
PEARL_DEV_MODE=true
PEARL_DEV_USER_ID=1
PEARL_DEV_USERNAME=john_doe
PEARL_DEV_ROLE=EDITOR
PEARL_DEV_DEPARTMENT=programming

# API Settings
PEARL_API_URL=http://localhost:8000
PEARL_WEBSOCKET_URL=ws://localhost:8000/ws

# 3. Create file: user-frontend/.env.production
# 4. Add production settings:

# Production Mode Settings
PEARL_DEV_MODE=false

# API Settings (update with your production URLs)
PEARL_API_URL=https://api.pearl.company.com
PEARL_WEBSOCKET_URL=wss://api.pearl.company.com/ws
```

---

### **PHASE 2: User Dashboard & Core UI (Week 2)**

#### **Task 4: Create User Frontend Application Structure**
**Goal**: Set up the main user frontend application with proper module loading.

**4.1 Create Main App File**
```r
# Instructions:
# 1. Create file: user-frontend/app.R
# 2. Copy this complete application code:

# PEARL User Frontend Application
# Task-focused interface for assigned tracker management

library(shiny)
library(bslib)
library(DT)
library(plotly)

# Load environment variables
if (file.exists(".env.development") && Sys.getenv("PEARL_ENV") != "production") {
  readRenviron(".env.development")
} else if (file.exists(".env.production")) {
  readRenviron(".env.production")
}

# Source shared modules
source("../shared/api/client.R")
source("../shared/api/auth.R")
source("../shared/api/trackers.R")
source("../shared/api/search.R")
source("../shared/ui/theme.R")
source("../shared/ui/dashboard_cards.R")
source("../shared/utils/user_context.R")

# Source user-specific modules
source("modules/auth_ui.R")
source("modules/auth_server.R")
source("modules/user_dashboard_ui.R")
source("modules/user_dashboard_server.R")
source("modules/my_assignments_ui.R")
source("modules/my_assignments_server.R")
source("modules/search_ui.R")
source("modules/search_server.R")

# Define UI
ui <- page_navbar(
  title = "PEARL Tracker",
  theme = get_pearl_theme(),  # From shared/ui/theme.R
  
  # Dashboard tab
  nav_panel(
    title = "Dashboard",
    icon = icon("dashboard"),
    user_dashboard_ui("dashboard")
  ),
  
  # My Assignments tab
  nav_panel(
    title = "My Assignments",
    icon = icon("tasks"),
    my_assignments_ui("assignments")
  ),
  
  # Search tab
  nav_panel(
    title = "Search",
    icon = icon("search"),
    search_ui("search")
  ),
  
  # User menu (top right)
  nav_spacer(),
  nav_menu(
    title = "User",
    icon = icon("user"),
    nav_item(
      auth_ui("auth")
    )
  )
)

# Define Server
server <- function(input, output, session) {
  # Create user context
  user_context <- reactive({
    create_user_context(session)
  })
  
  # Initialize modules with user context
  auth_server("auth", user_context)
  user_dashboard_server("dashboard", user_context)
  my_assignments_server("assignments", user_context)
  search_server("search", user_context)
  
  # Development mode: show user switcher
  if (is_dev_mode()) {
    showModal(modalDialog(
      title = "Development Mode - Select User",
      selectInput("dev_user_select", "Test As User:",
                  choices = list(
                    "John (Editor/Programming)" = "1",
                    "Jane (Viewer/Biostatistics)" = "2",
                    "Admin (Admin/Management)" = "3"
                  )),
      footer = modalButton("Continue"),
      easyClose = FALSE
    ))
    
    observeEvent(input$dev_user_select, {
      # Update environment variables
      Sys.setenv(PEARL_DEV_USER_ID = input$dev_user_select)
      # Reload context
      session$reload()
    })
  }
}

# Run the application
shinyApp(ui = ui, server = server)
```

**4.2 Create Theme Configuration**
```r
# Instructions:
# 1. Create file: shared/ui/theme.R
# 2. Add this theme configuration:

# shared/ui/theme.R
# Consistent theme for all PEARL applications

library(bslib)

get_pearl_theme <- function() {
  bs_theme(
    version = 5,
    primary = "#0062cc",
    secondary = "#6c757d",
    success = "#28a745",
    info = "#17a2b8",
    warning = "#ffc107",
    danger = "#dc3545",
    base_font = font_google("Inter"),
    heading_font = font_google("Poppins"),
    code_font = font_google("JetBrains Mono"),
    "enable-rounded" = TRUE,
    "enable-shadows" = TRUE
  )
}

# Card styles for dashboard
get_card_style <- function(type = "default") {
  styles <- list(
    default = "border-left: 4px solid var(--bs-primary);",
    success = "border-left: 4px solid var(--bs-success);",
    warning = "border-left: 4px solid var(--bs-warning);",
    danger = "border-left: 4px solid var(--bs-danger);",
    info = "border-left: 4px solid var(--bs-info);"
  )
  
  styles[[type]]
}
```

#### **Task 5: Create Dashboard Module**
**Goal**: Build the main dashboard showing user's task summary.

**5.1 Create Dashboard UI**
```r
# Instructions:
# 1. Create file: user-frontend/modules/user_dashboard_ui.R
# 2. Add this UI code:

# user_dashboard_ui.R
# Dashboard interface showing task summary and metrics

user_dashboard_ui <- function(id) {
  ns <- NS(id)
  
  tagList(
    # Page header
    div(
      class = "d-flex justify-content-between align-items-center mb-4",
      h2("My Dashboard"),
      textOutput(ns("last_update"), inline = TRUE)
    ),
    
    # Summary cards row
    fluidRow(
      col_3(
        value_box(
          title = "Total Assigned",
          value = textOutput(ns("total_assigned")),
          showcase = bs_icon("list-task"),
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
          title = "Awaiting QC",
          value = textOutput(ns("awaiting_qc")),
          showcase = bs_icon("hourglass-split"),
          theme = "warning"
        )
      ),
      col_3(
        value_box(
          title = "Completed",
          value = textOutput(ns("completed")),
          showcase = bs_icon("check-circle"),
          theme = "success"
        )
      )
    ),
    
    # Main content area
    fluidRow(
      # Priority items table
      col_8(
        card(
          card_header(
            class = "d-flex justify-content-between",
            span("Priority Items", class = "fw-bold"),
            actionButton(ns("refresh_priority"), "Refresh", 
                        class = "btn-sm btn-outline-primary")
          ),
          card_body(
            DTOutput(ns("priority_table"))
          )
        )
      ),
      
      # Recent activity feed
      col_4(
        card(
          card_header("Recent Activity"),
          card_body(
            style = "max-height: 500px; overflow-y: auto;",
            uiOutput(ns("activity_feed"))
          )
        )
      )
    ),
    
    # Charts row
    fluidRow(
      col_6(
        card(
          card_header("Status Distribution"),
          card_body(
            plotlyOutput(ns("status_chart"), height = "300px")
          )
        )
      ),
      col_6(
        card(
          card_header("Weekly Progress"),
          card_body(
            plotlyOutput(ns("progress_chart"), height = "300px")
          )
        )
      )
    )
  )
}
```

**5.2 Create Dashboard Server Logic**
```r
# Instructions:
# 1. Create file: user-frontend/modules/user_dashboard_server.R
# 2. Add this server logic:

# user_dashboard_server.R
# Dashboard server logic with data processing

user_dashboard_server <- function(id, user_context) {
  moduleServer(id, function(input, output, session) {
    
    # Reactive values for dashboard data
    dashboard_data <- reactiveVal(list(
      total = 0,
      in_progress = 0,
      awaiting_qc = 0,
      completed = 0,
      priority_items = data.frame(),
      recent_activity = list()
    ))
    
    # Load dashboard data
    load_dashboard_data <- function() {
      ctx <- user_context()
      if (!ctx$is_authenticated) return()
      
      # Get user's assigned trackers
      trackers <- get_user_trackers(ctx$user$id)
      
      if ("error" %in% names(trackers)) {
        showNotification("Error loading dashboard", type = "error")
        return()
      }
      
      # Calculate summary statistics
      total <- length(trackers)
      in_progress <- sum(trackers$production_status == "in_progress")
      awaiting_qc <- sum(trackers$qc_status == "in_progress")
      completed <- sum(trackers$production_status == "completed" & 
                      trackers$qc_status == "completed")
      
      # Get priority items (high priority or overdue)
      priority_items <- trackers[trackers$priority == "high" | 
                                 (!is.na(trackers$due_date) & 
                                  trackers$due_date < Sys.Date()), ]
      
      # Update reactive value
      dashboard_data(list(
        total = total,
        in_progress = in_progress,
        awaiting_qc = awaiting_qc,
        completed = completed,
        priority_items = priority_items,
        recent_activity = get_recent_activity(ctx$user$id)
      ))
    }
    
    # Initial load
    observe({
      load_dashboard_data()
    })
    
    # Refresh button
    observeEvent(input$refresh_priority, {
      load_dashboard_data()
      showNotification("Dashboard refreshed", type = "message")
    })
    
    # Output: Summary cards
    output$total_assigned <- renderText({
      dashboard_data()$total
    })
    
    output$in_progress <- renderText({
      dashboard_data()$in_progress
    })
    
    output$awaiting_qc <- renderText({
      dashboard_data()$awaiting_qc
    })
    
    output$completed <- renderText({
      dashboard_data()$completed
    })
    
    # Output: Last update time
    output$last_update <- renderText({
      paste("Last updated:", format(Sys.time(), "%H:%M:%S"))
    })
    
    # Output: Priority items table
    output$priority_table <- renderDT({
      data <- dashboard_data()$priority_items
      
      if (nrow(data) == 0) {
        datatable(
          data.frame(Message = "No priority items"),
          options = list(dom = 't', paging = FALSE)
        )
      } else {
        # Format for display
        display_data <- data.frame(
          Item = data$item_code,
          Type = data$item_type,
          Status = paste(data$production_status, "/", data$qc_status),
          Priority = data$priority,
          Due = format(data$due_date, "%Y-%m-%d"),
          stringsAsFactors = FALSE
        )
        
        datatable(
          display_data,
          options = list(
            pageLength = 10,
            dom = 'tp',
            order = list(list(3, 'desc')),  # Sort by priority
            columnDefs = list(
              list(className = 'dt-center', targets = '_all')
            )
          ),
          selection = 'single',
          rownames = FALSE
        ) %>%
          formatStyle(
            'Priority',
            backgroundColor = styleEqual(
              c('high', 'critical'),
              c('#fff3cd', '#f8d7da')
            )
          )
      }
    })
    
    # Output: Activity feed
    output$activity_feed <- renderUI({
      activities <- dashboard_data()$recent_activity
      
      if (length(activities) == 0) {
        return(p("No recent activity", class = "text-muted"))
      }
      
      # Create activity items
      activity_items <- lapply(activities, function(activity) {
        div(
          class = "border-bottom pb-2 mb-2",
          div(
            class = "d-flex justify-content-between",
            strong(activity$title),
            small(activity$time, class = "text-muted")
          ),
          p(activity$description, class = "mb-0 small")
        )
      })
      
      do.call(tagList, activity_items)
    })
    
    # Output: Status distribution chart
    output$status_chart <- renderPlotly({
      data <- dashboard_data()
      
      status_counts <- c(
        "Not Started" = data$total - data$in_progress - data$completed,
        "In Progress" = data$in_progress,
        "Awaiting QC" = data$awaiting_qc,
        "Completed" = data$completed
      )
      
      plot_ly(
        labels = names(status_counts),
        values = status_counts,
        type = 'pie',
        hole = 0.4,
        marker = list(
          colors = c('#6c757d', '#17a2b8', '#ffc107', '#28a745')
        )
      ) %>%
        layout(
          showlegend = TRUE,
          margin = list(t = 0, b = 0)
        )
    })
    
    # Output: Weekly progress chart
    output$progress_chart <- renderPlotly({
      # Generate sample weekly data (replace with real data)
      dates <- seq(Sys.Date() - 6, Sys.Date(), by = "day")
      completed <- cumsum(sample(0:3, 7, replace = TRUE))
      
      plot_ly(
        x = dates,
        y = completed,
        type = 'scatter',
        mode = 'lines+markers',
        line = list(color = '#0062cc', width = 2),
        marker = list(size = 8, color = '#0062cc')
      ) %>%
        layout(
          xaxis = list(title = ""),
          yaxis = list(title = "Completed Items"),
          margin = list(t = 0)
        )
    })
  })
}
```

#### **Task 6: Create Tracker API Functions**
**Goal**: Create functions to interact with tracker endpoints.

**6.1 Create Tracker API Client**
```r
# Instructions:
# 1. Create file: shared/api/trackers.R
# 2. Add these API functions:

# shared/api/trackers.R
# Tracker-specific API endpoints

source("shared/api/client.R")

# Get all trackers for a user
get_user_trackers <- function(user_id) {
  api_get(paste0("/api/v1/reporting-effort-tracker/assigned/", user_id))
}

# Get tracker by ID
get_tracker <- function(tracker_id) {
  api_get(paste0("/api/v1/reporting-effort-tracker/", tracker_id))
}

# Update tracker status
update_tracker_status <- function(tracker_id, production_status = NULL, qc_status = NULL) {
  body <- list()
  
  if (!is.null(production_status)) {
    body$production_status <- production_status
  }
  
  if (!is.null(qc_status)) {
    body$qc_status <- qc_status
  }
  
  api_put(paste0("/api/v1/reporting-effort-tracker/", tracker_id), body)
}

# Get recent activity for user
get_recent_activity <- function(user_id, limit = 10) {
  # This would call a backend endpoint for activity feed
  # For now, return sample data
  list(
    list(
      title = "Status Updated",
      description = "TLF T14.1.1 moved to In Progress",
      time = "5 minutes ago"
    ),
    list(
      title = "Comment Added",
      description = "New comment on SDTM DM dataset",
      time = "1 hour ago"
    ),
    list(
      title = "QC Completed",
      description = "ADaM ADSL passed QC",
      time = "2 hours ago"
    )
  )
}

# Search trackers
search_trackers <- function(query, user_id = NULL) {
  params <- list(q = query)
  
  if (!is.null(user_id)) {
    params$user_id <- user_id
  }
  
  api_get("/api/v1/tracker-search/search", params)
}
```

---

### **PHASE 3: My Assignments Module (Week 3)**

#### **Task 7: Create My Assignments View**
**Goal**: Show user's assigned items with inline editing capabilities.

**7.1 Create Assignments UI**
```r
# Instructions:
# 1. Create file: user-frontend/modules/my_assignments_ui.R
# 2. Add this code:

# my_assignments_ui.R
# Interface for viewing and managing assigned trackers

my_assignments_ui <- function(id) {
  ns <- NS(id)
  
  tagList(
    # Header with filters
    div(
      class = "mb-4",
      fluidRow(
        col_6(
          h2("My Assignments")
        ),
        col_6(
          class = "text-end",
          div(
            class = "btn-group",
            role = "group",
            actionButton(ns("filter_all"), "All", 
                        class = "btn-outline-secondary btn-sm"),
            actionButton(ns("filter_production"), "Production", 
                        class = "btn-outline-secondary btn-sm"),
            actionButton(ns("filter_qc"), "QC", 
                        class = "btn-outline-secondary btn-sm")
          )
        )
      )
    ),
    
    # Status filter pills
    div(
      class = "mb-3",
      tags$label("Filter by Status:", class = "me-2"),
      div(
        class = "btn-group",
        role = "group",
        checkboxGroupButtons(
          inputId = ns("status_filter"),
          label = NULL,
          choices = c(
            "Not Started" = "not_started",
            "In Progress" = "in_progress",
            "Completed" = "completed",
            "On Hold" = "on_hold"
          ),
          selected = c("not_started", "in_progress"),
          status = "primary",
          size = "sm",
          checkIcon = list(
            yes = icon("check")
          )
        )
      )
    ),
    
    # Main assignments table
    card(
      card_header(
        class = "d-flex justify-content-between",
        span(textOutput(ns("assignment_count"), inline = TRUE)),
        actionButton(ns("refresh_assignments"), 
                    icon("refresh"), 
                    class = "btn-sm btn-outline-primary")
      ),
      card_body(
        DTOutput(ns("assignments_table"))
      )
    ),
    
    # Quick action modal (hidden initially)
    div(
      id = ns("quick_action_modal"),
      style = "display: none;"
    )
  )
}
```

**7.2 Create Assignments Server Logic**
```r
# Instructions:
# 1. Create file: user-frontend/modules/my_assignments_server.R
# 2. Add this server code:

# my_assignments_server.R  
# Server logic for assignments management

my_assignments_server <- function(id, user_context) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Reactive values
    assignments <- reactiveVal(data.frame())
    filter_type <- reactiveVal("all")  # all, production, qc
    
    # Load assignments
    load_assignments <- function() {
      ctx <- user_context()
      if (!ctx$is_authenticated) return()
      
      # Get user's trackers
      trackers <- get_user_trackers(ctx$user$id)
      
      if ("error" %in% names(trackers)) {
        showNotification("Error loading assignments", type = "error")
        return()
      }
      
      # Filter based on assignment type
      if (filter_type() == "production") {
        trackers <- trackers[trackers$production_programmer_id == ctx$user$id, ]
      } else if (filter_type() == "qc") {
        trackers <- trackers[trackers$qc_programmer_id == ctx$user$id, ]
      }
      
      # Apply status filter
      if (length(input$status_filter) > 0) {
        trackers <- trackers[
          trackers$production_status %in% input$status_filter |
          trackers$qc_status %in% input$status_filter,
        ]
      }
      
      assignments(trackers)
    }
    
    # Initial load
    observe({
      load_assignments()
    })
    
    # Filter buttons
    observeEvent(input$filter_all, {
      filter_type("all")
      updateActionButton(session, "filter_all", class = "btn-secondary")
      updateActionButton(session, "filter_production", class = "btn-outline-secondary")
      updateActionButton(session, "filter_qc", class = "btn-outline-secondary")
      load_assignments()
    })
    
    observeEvent(input$filter_production, {
      filter_type("production")
      updateActionButton(session, "filter_all", class = "btn-outline-secondary")
      updateActionButton(session, "filter_production", class = "btn-secondary")
      updateActionButton(session, "filter_qc", class = "btn-outline-secondary")
      load_assignments()
    })
    
    observeEvent(input$filter_qc, {
      filter_type("qc")
      updateActionButton(session, "filter_all", class = "btn-outline-secondary")
      updateActionButton(session, "filter_production", class = "btn-outline-secondary")
      updateActionButton(session, "filter_qc", class = "btn-secondary")
      load_assignments()
    })
    
    # Status filter change
    observeEvent(input$status_filter, {
      load_assignments()
    })
    
    # Refresh button
    observeEvent(input$refresh_assignments, {
      load_assignments()
      showNotification("Assignments refreshed", type = "message")
    })
    
    # Output: Assignment count
    output$assignment_count <- renderText({
      count <- nrow(assignments())
      paste(count, "assignment(s)")
    })
    
    # Output: Assignments table
    output$assignments_table <- renderDT({
      data <- assignments()
      ctx <- user_context()
      
      if (nrow(data) == 0) {
        return(datatable(
          data.frame(Message = "No assignments found"),
          options = list(dom = 't', paging = FALSE)
        ))
      }
      
      # Prepare display data
      display_data <- data.frame(
        ID = data$id,
        Item = data$item_code,
        Type = paste(data$item_type, "-", data$item_subtype),
        Role = ifelse(data$production_programmer_id == ctx$user$id, 
                     "Production", "QC"),
        Status = ifelse(data$production_programmer_id == ctx$user$id,
                       data$production_status, data$qc_status),
        Priority = data$priority,
        Due = format(data$due_date, "%Y-%m-%d"),
        Actions = sprintf(
          '<div class="btn-group btn-group-sm">
            <button class="btn btn-primary update-status" data-id="%s">
              <i class="bi bi-pencil"></i> Update
            </button>
            <button class="btn btn-info view-details" data-id="%s">
              <i class="bi bi-eye"></i> View
            </button>
          </div>',
          data$id, data$id
        ),
        stringsAsFactors = FALSE
      )
      
      dt <- datatable(
        display_data,
        escape = FALSE,
        selection = 'none',
        rownames = FALSE,
        options = list(
          pageLength = 25,
          dom = 'ftip',
          order = list(list(5, 'desc')),  # Sort by priority
          columnDefs = list(
            list(visible = FALSE, targets = 0),  # Hide ID column
            list(className = 'dt-center', targets = '_all'),
            list(orderable = FALSE, targets = 7)  # Actions column
          ),
          drawCallback = JS(sprintf("
            function(settings) {
              // Add click handlers for buttons
              $('#%s button.update-status').off('click').on('click', function() {
                var id = $(this).attr('data-id');
                Shiny.setInputValue('%s', {id: id, action: 'update'}, {priority: 'event'});
              });
              
              $('#%s button.view-details').off('click').on('click', function() {
                var id = $(this).attr('data-id');
                Shiny.setInputValue('%s', {id: id, action: 'view'}, {priority: 'event'});
              });
            }
          ", ns("assignments_table"), ns("table_action"),
             ns("assignments_table"), ns("table_action")))
        )
      )
      
      # Add conditional formatting
      dt %>%
        formatStyle(
          'Priority',
          backgroundColor = styleEqual(
            c('high', 'critical'),
            c('#fff3cd', '#f8d7da')
          )
        ) %>%
        formatStyle(
          'Status',
          backgroundColor = styleEqual(
            c('completed', 'in_progress'),
            c('#d4edda', '#cce5ff')
          )
        )
    })
    
    # Handle table actions
    observeEvent(input$table_action, {
      action <- input$table_action
      
      if (action$action == "update") {
        # Show status update modal
        show_status_update_modal(action$id)
      } else if (action$action == "view") {
        # Show details modal
        show_details_modal(action$id)
      }
    })
    
    # Status update modal
    show_status_update_modal <- function(tracker_id) {
      tracker <- get_tracker(tracker_id)
      ctx <- user_context()
      
      # Determine which status to update
      is_production <- tracker$production_programmer_id == ctx$user$id
      current_status <- if (is_production) {
        tracker$production_status
      } else {
        tracker$qc_status
      }
      
      showModal(modalDialog(
        title = paste("Update Status -", tracker$item_code),
        size = "m",
        
        selectInput(
          ns("new_status"),
          label = paste("Current Status:", current_status),
          choices = if (is_production) {
            c("not_started", "in_progress", "completed", "on_hold")
          } else {
            c("not_started", "in_progress", "completed", "failed")
          },
          selected = current_status
        ),
        
        textAreaInput(
          ns("status_comment"),
          label = "Comment (optional):",
          placeholder = "Add a note about this status change...",
          rows = 3
        ),
        
        footer = tagList(
          modalButton("Cancel"),
          actionButton(ns("save_status"), "Save", class = "btn-primary")
        )
      ))
      
      # Store tracker ID for save action
      session$userData$current_tracker_id <- tracker_id
      session$userData$is_production <- is_production
    }
    
    # Save status update
    observeEvent(input$save_status, {
      tracker_id <- session$userData$current_tracker_id
      is_production <- session$userData$is_production
      
      # Update the appropriate status
      if (is_production) {
        result <- update_tracker_status(
          tracker_id, 
          production_status = input$new_status
        )
      } else {
        result <- update_tracker_status(
          tracker_id,
          qc_status = input$new_status
        )
      }
      
      if ("error" %in% names(result)) {
        showNotification(paste("Error:", result$error), type = "error")
      } else {
        showNotification("Status updated successfully", type = "success")
        removeModal()
        load_assignments()  # Refresh the table
      }
    })
  })
}
```

---

### **PHASE 4: Search Implementation (Week 4)**

#### **Task 8: Create Search Module**
**Goal**: Implement PostgreSQL full-text search with results display.

**8.1 Create Search UI**
```r
# Instructions:
# 1. Create file: user-frontend/modules/search_ui.R
# 2. Add this search interface:

# search_ui.R
# Search interface with filters and results

search_ui <- function(id) {
  ns <- NS(id)
  
  tagList(
    # Search header
    div(
      class = "mb-4",
      h2("Search Trackers"),
      p("Search across all tracker fields using keywords", 
        class = "text-muted")
    ),
    
    # Search input area
    card(
      card_body(
        fluidRow(
          col_8(
            div(
              class = "input-group",
              textInput(
                ns("search_query"),
                label = NULL,
                placeholder = "Enter search terms (e.g., 'in progress high priority')",
                width = "100%"
              ),
              span(
                class = "input-group-text",
                icon("search")
              )
            )
          ),
          col_2(
            actionButton(
              ns("search_button"),
              "Search",
              class = "btn-primary w-100",
              icon = icon("search")
            )
          ),
          col_2(
            actionButton(
              ns("clear_search"),
              "Clear",
              class = "btn-outline-secondary w-100",
              icon = icon("times")
            )
          )
        ),
        
        # Search options
        div(
          class = "mt-3",
          checkboxInput(
            ns("my_items_only"),
            "Search only my assigned items",
            value = TRUE
          )
        )
      )
    ),
    
    # Results summary
    conditionalPanel(
      condition = sprintf("input['%s'] != ''", ns("search_query")),
      div(
        class = "mt-3 mb-3",
        textOutput(ns("results_summary"))
      )
    ),
    
    # Search results
    card(
      card_header("Search Results"),
      card_body(
        DTOutput(ns("search_results"))
      )
    )
  )
}
```

**8.2 Create Search Server Logic**
```r
# Instructions:
# 1. Create file: user-frontend/modules/search_server.R
# 2. Add search functionality:

# search_server.R
# Search functionality using PostgreSQL full-text search

search_server <- function(id, user_context) {
  moduleServer(id, function(input, output, session) {
    
    # Reactive values
    search_results <- reactiveVal(data.frame())
    
    # Perform search
    perform_search <- function() {
      query <- trimws(input$search_query)
      if (query == "") {
        search_results(data.frame())
        return()
      }
      
      ctx <- user_context()
      
      # Call search API
      results <- search_trackers(
        query = query,
        user_id = if (input$my_items_only) ctx$user$id else NULL
      )
      
      if ("error" %in% names(results)) {
        showNotification(paste("Search error:", results$error), type = "error")
        search_results(data.frame())
      } else {
        search_results(results)
      }
    }
    
    # Search button click
    observeEvent(input$search_button, {
      perform_search()
    })
    
    # Enter key in search box
    observeEvent(input$search_query, {
      if (nchar(trimws(input$search_query)) > 0) {
        perform_search()
      }
    })
    
    # Clear search
    observeEvent(input$clear_search, {
      updateTextInput(session, "search_query", value = "")
      search_results(data.frame())
    })
    
    # Output: Results summary
    output$results_summary <- renderText({
      results <- search_results()
      if (nrow(results) == 0) {
        "No results found"
      } else {
        paste("Found", nrow(results), "matching tracker(s)")
      }
    })
    
    # Output: Search results table
    output$search_results <- renderDT({
      results <- search_results()
      
      if (nrow(results) == 0) {
        return(datatable(
          data.frame(Message = "No search results. Try different keywords."),
          options = list(dom = 't', paging = FALSE)
        ))
      }
      
      # Format results for display
      display_data <- data.frame(
        Item = results$item_code,
        Type = paste(results$item_type, "-", results$item_subtype),
        Production = results$production_status,
        QC = results$qc_status,
        Priority = results$priority,
        Score = round(results$relevance_score, 2),
        Actions = sprintf(
          '<button class="btn btn-sm btn-info view-result" data-id="%s">
            <i class="bi bi-eye"></i> View
          </button>',
          results$id
        ),
        stringsAsFactors = FALSE
      )
      
      datatable(
        display_data,
        escape = FALSE,
        selection = 'none',
        rownames = FALSE,
        options = list(
          pageLength = 25,
          order = list(list(5, 'desc')),  # Sort by relevance score
          columnDefs = list(
            list(className = 'dt-center', targets = '_all')
          )
        )
      ) %>%
        formatStyle(
          'Score',
          background = styleColorBar(c(0, max(display_data$Score)), 'lightblue'),
          backgroundSize = '100% 90%',
          backgroundRepeat = 'no-repeat',
          backgroundPosition = 'center'
        )
    })
  })
}
```

---

### **PHASE 5: Testing & Deployment (Week 5-6)**

#### **Task 9: Create Test Scripts**
**Goal**: Set up testing for all modules.

**9.1 Create Test Runner**
```r
# Instructions:
# 1. Create file: user-frontend/tests/test_all.R
# 2. Add comprehensive tests:

# test_all.R
# Test suite for user frontend

library(testthat)
library(shiny)

# Test authentication module
test_that("Authentication works correctly", {
  # Test dev mode detection
  Sys.setenv(PEARL_DEV_MODE = "true")
  expect_true(is_dev_mode())
  
  # Test user context creation
  ctx <- create_user_context()
  expect_true(ctx$is_authenticated)
  expect_equal(ctx$user$role, "EDITOR")
  
  # Test permissions
  expect_true(has_permission(ctx$user, "edit"))
  expect_false(has_permission(ctx$user, "delete"))
})

# Test API functions
test_that("API client functions work", {
  # Test URL construction
  Sys.setenv(PEARL_API_URL = "http://test.com")
  expect_equal(get_api_base_url(), "http://test.com")
  
  # Test endpoint construction
  endpoint <- paste0(get_api_base_url(), "/api/v1/users")
  expect_equal(endpoint, "http://test.com/api/v1/users")
})

# Test search functionality
test_that("Search query validation works", {
  # Test empty query handling
  query <- ""
  expect_equal(trimws(query), "")
  
  # Test query trimming
  query <- "  test query  "
  expect_equal(trimws(query), "test query")
})

# Run all tests
test_results <- test_dir("tests")
print(test_results)
```

#### **Task 10: Deployment Configuration**
**Goal**: Prepare both apps for RConnect deployment.

**10.1 Create Deployment Manifest**
```yaml
# Instructions:
# 1. Create file: manifest.yml
# 2. Add deployment configuration:

# RConnect Deployment Manifest
version: 1
locale: en_US.UTF-8
metadata:
  appmode: shiny
  entrypoint: app.R

# Python configuration for reticulate (if using Python for semantic search)
python:
  version: "3.9"
  package_manager:
    name: pip
    version: "21.0"

# R configuration
r:
  version: "4.2.0"
  package_manager:
    name: renv
    version: "0.15.0"

# Environment variables
environment:
  PEARL_API_URL: "${API_URL}"
  PEARL_WEBSOCKET_URL: "${WS_URL}"
  PEARL_DEV_MODE: "false"

# Resource limits
resources:
  memory_limit: "2Gi"
  cpu_limit: "2"

# Applications
applications:
  - name: pearl-user
    path: user-frontend/
    title: "PEARL Tracker"
    description: "User interface for PEARL tracker management"
    
  - name: pearl-admin
    path: admin-frontend/
    title: "PEARL Admin"
    description: "Administrative interface for PEARL system"
```

**10.2 Create Deployment Script**
```bash
# Instructions:
# 1. Create file: deploy.sh
# 2. Make executable: chmod +x deploy.sh
# 3. Add this deployment script:

#!/bin/bash
# PEARL Deployment Script

echo "PEARL Deployment Script"
echo "======================="

# Check if rsconnect is configured
if ! command -v rsconnect &> /dev/null; then
    echo "Error: rsconnect CLI not found"
    echo "Install with: pip install rsconnect-python"
    exit 1
fi

# Get deployment environment
read -p "Deploy to which environment? (dev/staging/prod): " ENV

# Set API URLs based on environment
case $ENV in
    dev)
        API_URL="http://dev-api.pearl.com"
        WS_URL="ws://dev-api.pearl.com/ws"
        SERVER="dev-rconnect.company.com"
        ;;
    staging)
        API_URL="https://staging-api.pearl.com"
        WS_URL="wss://staging-api.pearl.com/ws"
        SERVER="staging-rconnect.company.com"
        ;;
    prod)
        API_URL="https://api.pearl.com"
        WS_URL="wss://api.pearl.com/ws"
        SERVER="rconnect.company.com"
        ;;
    *)
        echo "Invalid environment"
        exit 1
        ;;
esac

# Deploy user frontend
echo "Deploying user frontend to $ENV..."
cd user-frontend
rsconnect deploy shiny . \
    --server $SERVER \
    --name pearl-user-$ENV \
    --title "PEARL Tracker ($ENV)" \
    --environment API_URL=$API_URL \
    --environment WS_URL=$WS_URL

# Deploy admin frontend
echo "Deploying admin frontend to $ENV..."
cd ../admin-frontend
rsconnect deploy shiny . \
    --server $SERVER \
    --name pearl-admin-$ENV \
    --title "PEARL Admin ($ENV)" \
    --environment API_URL=$API_URL \
    --environment WS_URL=$WS_URL

echo "Deployment complete!"
```

---

## **Testing Checklist for Junior Developers**

### **Module Testing Steps**

1. **Test Authentication**:
   - Set `PEARL_DEV_MODE=true` in .env
   - Run app and verify user switcher appears
   - Test each user role (VIEWER, EDITOR, ADMIN)
   - Verify permissions work correctly

2. **Test Dashboard**:
   - Check all summary cards show correct counts
   - Verify priority items table loads
   - Test refresh button functionality
   - Confirm charts render properly

3. **Test Assignments**:
   - Filter by Production/QC role
   - Test status filters
   - Try updating a status
   - Verify table sorting works

4. **Test Search**:
   - Search for "in progress"
   - Search for "high priority"
   - Test "my items only" checkbox
   - Verify relevance scoring

5. **Test WebSocket**:
   - Open app in two browser tabs
   - Update status in one tab
   - Verify other tab updates automatically

---

## **Common Issues & Solutions**

### **Issue 1: "API connection failed"**
**Solution**: 
- Check backend is running: `cd backend && uv run python run.py`
- Verify API URL in .env file
- Test API directly: `curl http://localhost:8000/health`

### **Issue 2: "No assignments showing"**
**Solution**:
- Check user ID in dev mode settings
- Verify trackers exist in database
- Check API endpoint: `/api/v1/reporting-effort-tracker/assigned/{user_id}`

### **Issue 3: "Search returns no results"**
**Solution**:
- Check PostgreSQL search migration was applied
- Verify search_vector column exists
- Test search API: `curl "http://localhost:8000/api/v1/tracker-search/search?q=test"`

### **Issue 4: "WebSocket not connecting"**
**Solution**:
- Check WebSocket URL in .env
- Verify backend WebSocket endpoint is running
- Check browser console for errors

---

## **Final Notes**

This implementation plan provides:
1. **70% code reuse** through shared modules
2. **Quick MVP delivery** with PostgreSQL search
3. **Future-ready** for semantic search enhancement
4. **Role-based security** throughout
5. **Real-time updates** via WebSocket
6. **Production-ready** deployment configuration

The instructions are detailed enough for a junior developer to follow step-by-step, with clear explanations of what each piece does and how to test it.