# Reporting Effort Tracker UI Module - Tracker assignments and status management

reporting_effort_tracker_ui <- function(id) {
  ns <- NS(id)
  
  # Helper function for hidden elements (if not already loaded)
  if (!exists("hidden")) {
    hidden <- function(...) {
      shinyjs::hidden(...)
    }
  }
  
  # Fluid page as container
  page_fluid(
    # Center content using d-flex
    div(
      style = "display: flex; justify-content: center; padding: 20px;",
      div(
        style = "width: 100%; max-width: 1400px;",
        
        # Main card
        card(
          class = "border border-2",
          full_screen = FALSE,
          height = "750px",
          
          # Header
          card_header(
            class = "d-flex justify-content-between align-items-center",
            div(
              tags$h4(bs_icon("clipboard-check"), " Tracker Management", class = "mb-0 text-primary"),
              tags$small("Manage programmer assignments and status tracking", class = "text-muted")
            ),
            div(
              class = "d-flex gap-2",
              # Filter controls
              div(
                style = "min-width: 150px;",
                selectInput(
                  ns("filter_status"),
                  NULL,
                  choices = list(
                    "All Status" = "",
                    "Not Started" = "not_started",
                    "In Progress" = "in_progress", 
                    "Review" = "review",
                    "Complete" = "complete",
                    "On Hold" = "on_hold"
                  ),
                  width = "100%"
                )
              ),
              div(
                style = "min-width: 150px;",
                selectInput(
                  ns("filter_priority"),
                  NULL,
                  choices = list(
                    "All Priority" = "",
                    "Low" = "low",
                    "Medium" = "medium",
                    "High" = "high",
                    "Critical" = "critical"
                  ),
                  width = "100%"
                )
              ),
              div(
                style = "min-width: 150px;",
                selectInput(
                  ns("filter_programmer"),
                  NULL,
                  choices = NULL,
                  width = "100%"
                )
              ),
              actionButton(
                ns("refresh_btn"),
                "Refresh",
                icon = icon("sync"),
                class = "btn btn-primary btn-sm",
                title = "Refresh tracker data"
              ),
              # Dropdown for actions
              div(
                class = "dropdown",
                tags$button(
                  class = "btn btn-info btn-sm dropdown-toggle",
                  type = "button",
                  `data-bs-toggle` = "dropdown",
                  `aria-expanded` = "false",
                  title = "Bulk operations and utilities",
                  tagList(icon("tools"), " Actions")
                ),
                tags$ul(
                  class = "dropdown-menu",
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("bulk_assign_btn"),
                    tagList(icon("users"), " Bulk Assign")
                  )),
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("bulk_status_btn"),
                    tagList(icon("clipboard-check"), " Bulk Status Update")
                  )),
                  tags$li(tags$hr(class = "dropdown-divider")),
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("workload_summary_btn"),
                    tagList(icon("chart-bar"), " Workload Summary")
                  )),
                  tags$li(tags$hr(class = "dropdown-divider")),
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("export_tracker_btn"),
                    tagList(icon("download"), " Export Tracker Data")
                  )),
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("import_tracker_btn"),
                    tagList(icon("upload"), " Import Tracker Data")
                  ))
                )
              )
            )
          ),
          
          # Body with sidebar
          card_body(
            class = "p-0",
            style = "height: 100%;",
            
            layout_sidebar(
              fillable = TRUE,
              sidebar = sidebar(
                id = ns("tracker_sidebar"),
                width = 450,
                position = "right",
                padding = c(3, 3, 3, 4),
                open = "closed",
                
                # Tracker Form
                div(
                  id = ns("tracker_form"),
                  tags$h6("Tracker Details", class = "text-center fw-bold mb-3"),
                  
                  # Item Information (read-only)
                  div(
                    class = "border rounded p-3 mb-3 bg-light",
                    tags$h6("Item Information", class = "text-muted mb-2"),
                    textOutput(ns("item_info")),
                    tags$hr(class = "my-2"),
                    textOutput(ns("effort_info"))
                  ),
                  
                  # Assignment Section
                  tags$h6("Assignments", class = "text-primary mb-2"),
                  
                  # Production Programmer
                  selectInput(
                    ns("production_programmer"),
                    "Production Programmer",
                    choices = NULL,
                    width = "100%"
                  ),
                  
                  # QC Programmer
                  selectInput(
                    ns("qc_programmer"),
                    "QC Programmer", 
                    choices = NULL,
                    width = "100%"
                  ),
                  
                  tags$hr(),
                  
                  # Status Section
                  tags$h6("Status & Progress", class = "text-primary mb-2"),
                  
                  # Production Status
                  selectInput(
                    ns("production_status"),
                    "Production Status",
                    choices = list(
                      "Not Started" = "not_started",
                      "In Progress" = "in_progress",
                      "Review" = "review", 
                      "Complete" = "complete",
                      "On Hold" = "on_hold"
                    ),
                    selected = "not_started"
                  ),
                  
                  # QC Status
                  selectInput(
                    ns("qc_status"),
                    "QC Status",
                    choices = list(
                      "Not Started" = "not_started",
                      "In Progress" = "in_progress",
                      "Review" = "review",
                      "Complete" = "complete", 
                      "On Hold" = "on_hold"
                    ),
                    selected = "not_started"
                  ),
                  
                  tags$hr(),
                  
                  # Planning Section
                  tags$h6("Planning", class = "text-primary mb-2"),
                  
                  # Priority
                  selectInput(
                    ns("priority"),
                    "Priority",
                    choices = list(
                      "Low" = "low",
                      "Medium" = "medium",
                      "High" = "high",
                      "Critical" = "critical"
                    ),
                    selected = "medium"
                  ),
                  
                  # Due Date
                  dateInput(
                    ns("due_date"),
                    "Due Date",
                    value = NULL,
                    width = "100%"
                  ),
                  
                  # Estimated Hours
                  numericInput(
                    ns("estimated_hours"),
                    "Estimated Hours",
                    value = NULL,
                    min = 0,
                    step = 0.5,
                    width = "100%"
                  ),
                  
                  # Notes
                  textAreaInput(
                    ns("notes"),
                    "Notes",
                    placeholder = "Add notes about this item...",
                    rows = 3
                  ),
                  
                  # Hidden ID field for editing
                  hidden(
                    numericInput(ns("edit_tracker_id"), "ID", value = NA)
                  ),
                  
                  # Action buttons
                  layout_columns(
                    col_widths = c(6, 6),
                    gap = 2,
                    actionButton(
                      ns("save_tracker"),
                      "Update",
                      icon = icon("check"),
                      class = "btn btn-success w-100",
                      title = "Save tracker changes"
                    ),
                    actionButton(
                      ns("cancel_tracker"),
                      "Cancel",
                      icon = icon("times"),
                      class = "btn btn-secondary w-100",
                      title = "Cancel and close"
                    )
                  )
                )
              ),
              
              # Main content area
              div(
                style = "padding: 10px 0;",
                uiOutput(ns("tracker_error_msg")),
                
                # DataTable container with fixed height
                div(
                  style = "height: 600px; overflow-y: auto;",
                  DTOutput(ns("tracker_table"))
                )
              )
            )
          )
        )
      )
    ),
    
    # JavaScript for dropdown clicks
    tags$script(HTML(sprintf("
      document.addEventListener('DOMContentLoaded', function() {
        document.getElementById('%s').addEventListener('click', function(e) {
          e.preventDefault();
          Shiny.setInputValue('%s', Math.random(), {priority: 'event'});
        });
        document.getElementById('%s').addEventListener('click', function(e) {
          e.preventDefault();
          Shiny.setInputValue('%s', Math.random(), {priority: 'event'});
        });
        document.getElementById('%s').addEventListener('click', function(e) {
          e.preventDefault();
          Shiny.setInputValue('%s', Math.random(), {priority: 'event'});
        });
        document.getElementById('%s').addEventListener('click', function(e) {
          e.preventDefault();
          Shiny.setInputValue('%s', Math.random(), {priority: 'event'});
        });
        document.getElementById('%s').addEventListener('click', function(e) {
          e.preventDefault();
          Shiny.setInputValue('%s', Math.random(), {priority: 'event'});
        });
      });
    ", 
    ns("bulk_assign_btn"), ns("bulk_assign_clicked"),
    ns("bulk_status_btn"), ns("bulk_status_clicked"),
    ns("workload_summary_btn"), ns("workload_summary_clicked"),
    ns("export_tracker_btn"), ns("export_tracker_clicked"),
    ns("import_tracker_btn"), ns("import_tracker_clicked")
    )))
  )
}