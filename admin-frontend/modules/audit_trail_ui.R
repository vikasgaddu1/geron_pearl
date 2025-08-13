# Audit Trail Viewer UI Module

audit_trail_ui <- function(id) {
  ns <- NS(id)
  
  div(
    class = "container-fluid",
    h2("Audit Trail Viewer", class = "mb-4"),
    
    # Admin access notice
    div(
      class = "alert alert-info",
      icon("shield-alt"),
      "This is an admin-only feature. All database changes are logged here for compliance and security purposes."
    ),
    
    # Filter controls
    div(
      class = "card mb-4",
      div(
        class = "card-header",
        h4("Filters", class = "mb-0")
      ),
      div(
        class = "card-body",
        fluidRow(
          column(
            3,
            selectInput(
              ns("filter_table"),
              "Table",
              choices = c(
                "All" = "",
                "Studies" = "studies",
                "Database Releases" = "database_releases",
                "Reporting Efforts" = "reporting_efforts",
                "Reporting Effort Items" = "reporting_effort_items",
                "Reporting Effort Tracker" = "reporting_effort_item_tracker",
                "Comments" = "reporting_effort_tracker_comments",
                "Packages" = "packages",
                "Package Items" = "package_items",
                "Text Elements" = "text_elements",
                "Users" = "users"
              ),
              selected = ""
            )
          ),
          column(
            3,
            selectInput(
              ns("filter_action"),
              "Action",
              choices = c(
                "All" = "",
                "Create" = "CREATE",
                "Update" = "UPDATE",
                "Delete" = "DELETE"
              ),
              selected = ""
            )
          ),
          column(
            3,
            selectInput(
              ns("filter_user"),
              "User",
              choices = c("All" = ""),
              selected = ""
            )
          ),
          column(
            3,
            selectInput(
              ns("filter_time_range"),
              "Time Range",
              choices = c(
                "All Time" = "",
                "Last Hour" = "1h",
                "Last 24 Hours" = "24h",
                "Last 7 Days" = "7d",
                "Last 30 Days" = "30d",
                "Custom" = "custom"
              ),
              selected = "24h"
            )
          )
        ),
        
        # Custom date range (hidden by default)
        conditionalPanel(
          condition = "input.filter_time_range == 'custom'",
          ns = ns,
          fluidRow(
            column(
              6,
              dateInput(
                ns("start_date"),
                "Start Date",
                value = Sys.Date() - 7,
                max = Sys.Date()
              )
            ),
            column(
              6,
              dateInput(
                ns("end_date"),
                "End Date",
                value = Sys.Date(),
                max = Sys.Date()
              )
            )
          )
        ),
        
        fluidRow(
          column(
            12,
            div(
              class = "mt-3",
              actionButton(
                ns("apply_filters"),
                "Apply Filters",
                class = "btn-primary",
                icon = icon("filter")
              ),
              actionButton(
                ns("reset_filters"),
                "Reset",
                class = "btn-secondary ms-2",
                icon = icon("undo")
              ),
              actionButton(
                ns("refresh_logs"),
                "Refresh",
                class = "btn-info ms-2",
                icon = icon("sync")
              ),
              actionButton(
                ns("export_logs"),
                "Export to Excel",
                class = "btn-success ms-2",
                icon = icon("file-excel")
              )
            )
          )
        )
      )
    ),
    
    # Summary statistics
    div(
      class = "row mb-3",
      div(
        class = "col-md-3",
        div(
          class = "card text-center",
          div(
            class = "card-body",
            h5(class = "card-title", "Total Changes"),
            h3(textOutput(ns("total_changes"), inline = TRUE))
          )
        )
      ),
      div(
        class = "col-md-3",
        div(
          class = "card text-center",
          div(
            class = "card-body",
            h5(class = "card-title", "Creates"),
            h3(class = "text-success", textOutput(ns("total_creates"), inline = TRUE))
          )
        )
      ),
      div(
        class = "col-md-3",
        div(
          class = "card text-center",
          div(
            class = "card-body",
            h5(class = "card-title", "Updates"),
            h3(class = "text-warning", textOutput(ns("total_updates"), inline = TRUE))
          )
        )
      ),
      div(
        class = "col-md-3",
        div(
          class = "card text-center",
          div(
            class = "card-body",
            h5(class = "card-title", "Deletes"),
            h3(class = "text-danger", textOutput(ns("total_deletes"), inline = TRUE))
          )
        )
      )
    ),
    
    # Audit log table
    div(
      class = "card",
      div(
        class = "card-header",
        h4("Audit Log Entries", class = "mb-0")
      ),
      div(
        class = "card-body",
        DT::dataTableOutput(ns("audit_table"))
      )
    ),
    
    # Detail modal placeholder
    uiOutput(ns("detail_modal"))
  )
}