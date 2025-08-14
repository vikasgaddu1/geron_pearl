# Admin Dashboard UI Module

admin_dashboard_ui <- function(id) {
  ns <- NS(id)
  
  tagList(
    # Custom CSS for dashboard
    tags$style(HTML(paste0("
      .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
      }
      
      .metric-card {
        background: white;
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        height: 100%;
        transition: transform 0.2s;
      }
      
      .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
      }
      
      .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #667eea;
      }
      
      .metric-label {
        font-size: 0.875rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.5rem;
      }
      
      .metric-change {
        font-size: 0.875rem;
        margin-top: 0.5rem;
      }
      
      .change-positive {
        color: #28a745;
      }
      
      .change-negative {
        color: #dc3545;
      }
      
      .chart-card {
        background: white;
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        height: 400px;
      }
      
      .activity-card {
        background: white;
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
      }
      
      .activity-item {
        padding: 0.75rem 0;
        border-bottom: 1px solid #e9ecef;
      }
      
      .activity-item:last-child {
        border-bottom: none;
      }
      
      .workload-bar {
        background: #e9ecef;
        border-radius: 0.25rem;
        height: 8px;
        position: relative;
        overflow: hidden;
      }
      
      .workload-fill {
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transition: width 0.5s ease;
      }
      
      .team-member-card {
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
      }
      
      .progress-ring {
        transform: rotate(-90deg);
      }
      
      .progress-ring-circle {
        fill: transparent;
        stroke-width: 4;
        stroke-dasharray: 251.2;
        stroke-dashoffset: 251.2;
        transition: stroke-dashoffset 1s ease;
      }
      
      .status-indicator {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 0.5rem;
      }
      
      .status-active {
        background: #28a745;
        animation: pulse 2s infinite;
      }
      
      .status-pending {
        background: #ffc107;
      }
      
      .status-completed {
        background: #6c757d;
      }
      
      @keyframes pulse {
        0% {
          box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.4);
        }
        70% {
          box-shadow: 0 0 0 10px rgba(40, 167, 69, 0);
        }
        100% {
          box-shadow: 0 0 0 0 rgba(40, 167, 69, 0);
        }
      }
      
      .export-menu {
        position: absolute;
        top: 1rem;
        right: 1rem;
      }
    "))),
    
    # Main container
    div(
      class = "container-fluid px-4",
      
      # Dashboard Header
      div(
        class = "dashboard-header",
        div(
          class = "d-flex justify-content-between align-items-center",
          div(
            h1("Admin Dashboard", class = "mb-0"),
            p("Real-time overview of PEARL system activity", class = "mb-0 mt-2")
          ),
          div(
            class = "btn-group",
            actionButton(
              ns("refresh_dashboard"),
              "Refresh",
              icon = icon("sync-alt"),
              class = "btn btn-light"
            ),
            dropdown(
              actionButton(
                ns("export_pdf"),
                "Export as PDF",
                icon = icon("file-pdf"),
                class = "btn btn-link text-dark w-100 text-start"
              ),
              actionButton(
                ns("export_excel"),
                "Export as Excel",
                icon = icon("file-excel"),
                class = "btn btn-link text-dark w-100 text-start"
              ),
              actionButton(
                ns("export_csv"),
                "Export as CSV",
                icon = icon("file-csv"),
                class = "btn btn-link text-dark w-100 text-start"
              ),
              icon = icon("download"),
              status = "light",
              width = "200px"
            )
          )
        )
      ),
      
      # Key Metrics Row
      div(
        class = "row mb-4",
        div(
          class = "col-md-3 mb-3",
          div(
            class = "metric-card",
            div(class = "metric-value", textOutput(ns("total_studies"), inline = TRUE)),
            div(class = "metric-label", "Active Studies"),
            div(
              class = "metric-change change-positive",
              uiOutput(ns("studies_change"))
            )
          )
        ),
        div(
          class = "col-md-3 mb-3",
          div(
            class = "metric-card",
            div(class = "metric-value", textOutput(ns("total_trackers"), inline = TRUE)),
            div(class = "metric-label", "Active Trackers"),
            div(
              class = "metric-change",
              uiOutput(ns("trackers_change"))
            )
          )
        ),
        div(
          class = "col-md-3 mb-3",
          div(
            class = "metric-card",
            div(class = "metric-value", textOutput(ns("total_items"), inline = TRUE)),
            div(class = "metric-label", "Total Items"),
            div(
              class = "metric-change",
              uiOutput(ns("items_change"))
            )
          )
        ),
        div(
          class = "col-md-3 mb-3",
          div(
            class = "metric-card",
            div(class = "metric-value", textOutput(ns("completion_rate"), inline = TRUE)),
            div(class = "metric-label", "Completion Rate"),
            div(
              class = "metric-change",
              uiOutput(ns("completion_change"))
            )
          )
        )
      ),
      
      # Charts Row
      div(
        class = "row mb-4",
        # Team Workload Chart
        div(
          class = "col-md-6 mb-3",
          div(
            class = "chart-card",
            h5("Team Workload Overview"),
            div(
              id = ns("workload_chart"),
              plotOutput(ns("team_workload_plot"), height = "320px")
            )
          )
        ),
        # Progress Tracking Chart
        div(
          class = "col-md-6 mb-3",
          div(
            class = "chart-card",
            h5("Progress Tracking"),
            div(
              id = ns("progress_chart"),
              plotOutput(ns("progress_tracking_plot"), height = "320px")
            )
          )
        )
      ),
      
      # Bottom Row - Activity and Resources
      div(
        class = "row",
        # Recent Activity
        div(
          class = "col-md-4 mb-3",
          div(
            class = "activity-card",
            h5("Recent Activity"),
            div(
              id = ns("recent_activity"),
              uiOutput(ns("activity_list"))
            )
          )
        ),
        # Resource Allocation
        div(
          class = "col-md-4 mb-3",
          div(
            class = "chart-card",
            h5("Resource Allocation"),
            plotOutput(ns("resource_allocation_plot"), height = "320px")
          )
        ),
        # Bottleneck Identification
        div(
          class = "col-md-4 mb-3",
          div(
            class = "activity-card",
            h5("Bottleneck Analysis"),
            uiOutput(ns("bottleneck_list"))
          )
        )
      ),
      
      # Team Members Workload Details
      div(
        class = "row mt-4",
        div(
          class = "col-12",
          div(
            class = "card",
            div(
              class = "card-header bg-white",
              h5("Team Member Details", class = "mb-0")
            ),
            div(
              class = "card-body",
              DT::dataTableOutput(ns("team_details_table"))
            )
          )
        )
      ),
      
      # Auto-refresh indicator
      div(
        class = "text-center text-muted mt-4",
        icon("clock"),
        " Last updated: ",
        textOutput(ns("last_update"), inline = TRUE),
        " (Auto-refreshes every 30 seconds)"
      )
    )
  )
}