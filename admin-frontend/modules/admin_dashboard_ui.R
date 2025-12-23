# Dashboard UI Module - Role-Based Dashboards
# Provides Lead Dashboard and Programmer Dashboard views

admin_dashboard_ui <- function(id) {
  ns <- NS(id)
  
  tagList(
    # Custom CSS for dashboard
    tags$style(HTML("
      .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
      }
      
      .user-selector-container {
        background: rgba(255,255,255,0.15);
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
      }
      
      .user-selector-container label {
        margin-bottom: 0;
        font-weight: 500;
      }
      
      .user-selector-container .form-select {
        max-width: 250px;
      }
      
      .metric-card {
        background: white;
        border-radius: 0.5rem;
        padding: 1.25rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        height: 100%;
        transition: transform 0.2s;
      }
      
      .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
      }
      
      .metric-value {
        font-size: 2.25rem;
        font-weight: bold;
        color: #667eea;
      }
      
      .metric-value.warning {
        color: #ffc107;
      }
      
      .metric-value.danger {
        color: #dc3545;
      }
      
      .metric-value.success {
        color: #28a745;
      }
      
      .metric-label {
        font-size: 0.875rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.5rem;
      }
      
      .assignment-card {
        background: white;
        border-radius: 0.5rem;
        padding: 1.25rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        margin-bottom: 1rem;
      }
      
      .deadline-item {
        padding: 0.75rem;
        border-bottom: 1px solid #e9ecef;
        display: flex;
        align-items: center;
        gap: 1rem;
      }
      
      .deadline-item:last-child {
        border-bottom: none;
      }
      
      .deadline-item.overdue {
        background: rgba(220, 53, 69, 0.1);
        border-left: 3px solid #dc3545;
      }
      
      .deadline-item.due-soon {
        background: rgba(255, 193, 7, 0.1);
        border-left: 3px solid #ffc107;
      }
      
      .deadline-badge {
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
      }
      
      .priority-badge {
        font-size: 0.7rem;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        text-transform: uppercase;
      }
      
      .priority-critical { background: #dc3545; color: white; }
      .priority-high { background: #fd7e14; color: white; }
      .priority-medium { background: #ffc107; color: #212529; }
      .priority-low { background: #6c757d; color: white; }
      
      .status-badge {
        font-size: 0.7rem;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
      }
      
      .status-not_started { background: #e9ecef; color: #495057; }
      .status-in_progress { background: #0dcaf0; color: #212529; }
      .status-completed { background: #198754; color: white; }
      .status-on_hold { background: #6c757d; color: white; }
      .status-failed { background: #dc3545; color: white; }
      
      .workload-progress {
        height: 8px;
        background: #e9ecef;
        border-radius: 4px;
        overflow: hidden;
      }
      
      .workload-bar {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transition: width 0.5s ease;
      }
      
      .empty-state {
        text-align: center;
        padding: 3rem;
        color: #6c757d;
      }
      
      .empty-state i {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
      }
      
      .nav-tabs .nav-link {
        font-weight: 500;
      }
      
      .nav-tabs .nav-link.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
      }

      /* Highlight row for navigation from dashboard */
      .highlight-row {
        background-color: rgba(102, 126, 234, 0.25) !important;
        animation: highlight-pulse 1s ease-in-out 3;
      }

      @keyframes highlight-pulse {
        0%, 100% { background-color: rgba(102, 126, 234, 0.25); }
        50% { background-color: rgba(102, 126, 234, 0.4); }
      }

      /* Quick status button styles */
      .quick-status-btn {
        padding: 0.25rem 0.4rem;
        line-height: 1;
      }

      .go-to-tracker-btn {
        padding: 0.25rem 0.4rem;
        line-height: 1;
      }
    ")),
    
    # Main container
    div(
      class = "container-fluid px-4",
      
      # Dashboard Header with User Selector
      div(
        class = "dashboard-header",
        div(
          class = "d-flex justify-content-between align-items-center flex-wrap gap-3",
          div(
            h1("Dashboard", class = "mb-0 h3"),
            p("View assignments and track progress", class = "mb-0 mt-1 small opacity-75")
          ),
          div(
            class = "d-flex align-items-center gap-3",
            div(
              class = "user-selector-container",
              tags$label(icon("user"), " View As:"),
              uiOutput(ns("user_selector_ui"))
            ),
            actionButton(
              ns("refresh_dashboard"),
              tagList(icon("sync-alt"), " Refresh"),
              class = "btn btn-light btn-sm"
            )
          )
        )
      ),
      
      # Dashboard Tabs
      tabsetPanel(
        id = ns("dashboard_tabs"),
        type = "tabs",
        
        # Programmer Dashboard Tab
        tabPanel(
          "Programmer Dashboard",
          value = "programmer_tab",
          icon = icon("code"),
          div(
            class = "py-3",
            
            # Summary Metrics Row (5 columns)
            div(
              class = "row mb-4 row-cols-2 row-cols-md-3 row-cols-lg-5",
              div(
                class = "col mb-3",
                div(
                  class = "metric-card",
                  div(class = "metric-value", textOutput(ns("prog_total_assignments"), inline = TRUE)),
                  div(class = "metric-label", "Total Assignments")
                )
              ),
              div(
                class = "col mb-3",
                div(
                  class = "metric-card",
                  uiOutput(ns("prog_not_started_value")),
                  div(class = "metric-label", "Not Started")
                )
              ),
              div(
                class = "col mb-3",
                div(
                  class = "metric-card",
                  div(class = "metric-value", textOutput(ns("prog_in_production"), inline = TRUE)),
                  div(class = "metric-label", "In Production")
                )
              ),
              div(
                class = "col mb-3",
                div(
                  class = "metric-card",
                  uiOutput(ns("prog_overdue_value")),
                  div(class = "metric-label", "Overdue Items")
                )
              ),
              div(
                class = "col mb-3",
                div(
                  class = "metric-card",
                  uiOutput(ns("prog_due_soon_value")),
                  div(class = "metric-label", "Due Within 7 Days")
                )
              )
            ),
            
            # Main Content Row
            div(
              class = "row",
              # My Assignments Section
              div(
                class = "col-lg-8 mb-4",
                div(
                  class = "card",
                  div(
                    class = "card-header bg-white d-flex justify-content-between align-items-center",
                    h5(tagList(icon("clipboard-list"), " My Assignments"), class = "mb-0"),
                    div(
                      class = "btn-group btn-group-sm",
                      actionButton(ns("filter_all"), "All", class = "btn btn-outline-primary active"),
                      actionButton(ns("filter_production"), "Production", class = "btn btn-outline-primary"),
                      actionButton(ns("filter_qc"), "QC", class = "btn btn-outline-primary")
                    )
                  ),
                  div(
                    class = "card-body p-0",
                    DT::dataTableOutput(ns("my_assignments_table"))
                  )
                )
              ),
              
              # Upcoming Deadlines Section
              div(
                class = "col-lg-4 mb-4",
                div(
                  class = "card",
                  div(
                    class = "card-header bg-white",
                    h5(tagList(icon("calendar-alt"), " Upcoming Deadlines"), class = "mb-0")
                  ),
                  div(
                    class = "card-body p-0",
                    style = "max-height: 500px; overflow-y: auto;",
                    uiOutput(ns("upcoming_deadlines_list"))
                  )
                )
              )
            ),
            
            # Status Breakdown
            div(
              class = "row",
              div(
                class = "col-md-6 mb-4",
                div(
                  class = "card",
                  div(
                    class = "card-header bg-white",
                    h5(tagList(icon("tasks"), " Production Status"), class = "mb-0")
                  ),
                  div(
                    class = "card-body",
                    uiOutput(ns("production_status_breakdown"))
                  )
                )
              ),
              div(
                class = "col-md-6 mb-4",
                div(
                  class = "card",
                  div(
                    class = "card-header bg-white",
                    h5(tagList(icon("check-double"), " QC Status"), class = "mb-0")
                  ),
                  div(
                    class = "card-body",
                    uiOutput(ns("qc_status_breakdown"))
                  )
                )
              )
            )
          )
        ),
        
        # Tracker Dashboard Tab
        tabPanel(
          "Tracker Dashboard",
          value = "lead_tab",
          icon = icon("chart-line"),
          div(
            class = "py-3",
            
            # Reporting Effort Selector Row
            div(
              class = "row mb-4",
              div(
                class = "col-12",
                div(
                  class = "card border-primary",
                  div(
                    class = "card-header bg-primary text-white d-flex justify-content-between align-items-center",
                    h5(tagList(icon("filter"), " Select Reporting Effort"), class = "mb-0"),
                    div(
                      class = "d-flex gap-2",
                      actionButton(
                        ns("tracker_dashboard_refresh"),
                        tagList(icon("rotate"), " Refresh Data"),
                        class = "btn btn-light btn-sm"
                      )
                    )
                  ),
                  div(
                    class = "card-body",
                    div(
                      class = "row",
                      div(
                        class = "col-md-8",
                        selectInput(
                          ns("tracker_dashboard_re_selector"),
                          label = NULL,
                          choices = c("Select a Reporting Effort" = ""),
                          selected = "",
                          width = "100%"
                        )
                      ),
                      div(
                        class = "col-md-4",
                        # Summary info
                        uiOutput(ns("tracker_dashboard_summary_info"))
                      )
                    )
                  )
                )
              )
            ),
            
            # Key Metrics Row (for selected RE)
            div(
              class = "row mb-4",
              div(
                class = "col-md-3 mb-3",
                div(
                  class = "metric-card",
                  div(class = "metric-value", textOutput(ns("total_studies"), inline = TRUE)),
                  div(class = "metric-label", "Total Studies")
                )
              ),
              div(
                class = "col-md-3 mb-3",
                div(
                  class = "metric-card",
                  div(class = "metric-value", textOutput(ns("total_trackers"), inline = TRUE)),
                  div(class = "metric-label", "Active Trackers")
                )
              ),
              div(
                class = "col-md-3 mb-3",
                div(
                  class = "metric-card",
                  div(class = "metric-value", textOutput(ns("total_items"), inline = TRUE)),
                  div(class = "metric-label", "Total Items")
                )
              ),
              div(
                class = "col-md-3 mb-3",
                div(
                  class = "metric-card",
                  div(class = "metric-value", textOutput(ns("completion_rate"), inline = TRUE)),
                  div(class = "metric-label", "Completion Rate")
                )
              )
            ),
            
            # Selected RE Summary Section
            div(
              class = "row mb-4",
              div(
                class = "col-12",
                div(
                  class = "card",
                  div(
                    class = "card-header bg-white d-flex justify-content-between align-items-center",
                    h5(tagList(icon("chart-bar"), " Task Type Breakdown"), class = "mb-0"),
                    tags$small(class = "text-muted", "Status by SDTM, ADaM, Table, Listing, Figure")
                  ),
                  div(
                    class = "card-body",
                    # Summary metrics for filtered data
                    div(
                      class = "row mb-3",
                      div(
                        class = "col-md-3",
                        div(
                          class = "p-2 bg-light rounded text-center",
                          div(class = "h4 mb-0 text-primary", textOutput(ns("filtered_total"), inline = TRUE)),
                          div(class = "small text-muted", "Total Items")
                        )
                      ),
                      div(
                        class = "col-md-3",
                        div(
                          class = "p-2 bg-light rounded text-center",
                          div(class = "h4 mb-0 text-success", textOutput(ns("filtered_completed"), inline = TRUE)),
                          div(class = "small text-muted", "Completed")
                        )
                      ),
                      div(
                        class = "col-md-3",
                        div(
                          class = "p-2 bg-light rounded text-center",
                          div(class = "h4 mb-0 text-info", textOutput(ns("filtered_in_progress"), inline = TRUE)),
                          div(class = "small text-muted", "In Progress")
                        )
                      ),
                      div(
                        class = "col-md-3",
                        div(
                          class = "p-2 bg-light rounded text-center",
                          div(class = "h4 mb-0 text-danger", textOutput(ns("filtered_overdue"), inline = TRUE)),
                          div(class = "small text-muted", "Overdue")
                        )
                      )
                    ),
                    # Task Type Breakdown Charts
                    div(
                      class = "row",
                      div(
                        class = "col-md-6",
                        h6(tagList(icon("chart-bar"), " Status by Task Type"), class = "mb-2"),
                        div(
                          style = "height: 280px;",
                          plotly::plotlyOutput(ns("task_type_breakdown_chart"), height = "100%")
                        )
                      ),
                      div(
                        class = "col-md-6",
                        h6(tagList(icon("table"), " Task Type Summary"), class = "mb-2"),
                        DT::dataTableOutput(ns("task_type_summary_table"))
                      )
                    )
                  )
                )
              )
            ),
            
            # Status Distribution Charts Row
            div(
              class = "row mb-4",
              div(
                class = "col-md-6 mb-3",
                div(
                  class = "card",
                  div(
                    class = "card-header bg-white",
                    h5(tagList(icon("chart-pie"), " Production Status"), class = "mb-0")
                  ),
                  div(
                    class = "card-body",
                    style = "height: 280px;",
                    plotly::plotlyOutput(ns("lead_production_status_chart"), height = "100%")
                  )
                )
              ),
              div(
                class = "col-md-6 mb-3",
                div(
                  class = "card",
                  div(
                    class = "card-header bg-white",
                    h5(tagList(icon("chart-pie"), " QC Status"), class = "mb-0")
                  ),
                  div(
                    class = "card-body",
                    style = "height: 280px;",
                    plotly::plotlyOutput(ns("lead_qc_status_chart"), height = "100%")
                  )
                )
              )
            ),
            
            # Programmer Workload Section
            div(
              class = "row mb-4",
              div(
                class = "col-12",
                div(
                  class = "card",
                  div(
                    class = "card-header bg-white d-flex justify-content-between align-items-center",
                    h5(tagList(icon("users"), " Programmer Workload"), class = "mb-0"),
                    tags$small(class = "text-muted", "Assignments for selected reporting effort")
                  ),
                  div(
                    class = "card-body",
                    DT::dataTableOutput(ns("programmer_workload_table"))
                  )
                )
              )
            ),
            
            # Deadlines for Selected RE
            div(
              class = "row",
              div(
                class = "col-md-6 mb-4",
                div(
                  class = "card",
                  div(
                    class = "card-header bg-white",
                    h5(tagList(icon("exclamation-triangle"), " Overdue Items"), class = "mb-0")
                  ),
                  div(
                    class = "card-body",
                    uiOutput(ns("system_overdue_list"))
                  )
                )
              ),
              div(
                class = "col-md-6 mb-4",
                div(
                  class = "card",
                  div(
                    class = "card-header bg-white",
                    h5(tagList(icon("clock"), " Items Due This Week"), class = "mb-0")
                  ),
                  div(
                    class = "card-body",
                    uiOutput(ns("system_due_soon_list"))
                  )
                )
              )
            )
          )
        )
      ),
      
      # Last update indicator
      div(
        class = "text-center text-muted mt-3 small",
        icon("clock"),
        " Last updated: ",
        textOutput(ns("last_update"), inline = TRUE)
      )
    )
  )
}
