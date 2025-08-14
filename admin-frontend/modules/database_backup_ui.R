# Database Backup UI Module

database_backup_ui <- function(id) {
  ns <- NS(id)
  
  tagList(
    # Custom CSS for this module
    tags$style(HTML(paste0("
      #", ns("backup_table"), " .btn-sm {
        padding: 0.25rem 0.5rem;
        font-size: 0.875rem;
      }
      
      .backup-status-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
      }
      
      .status-completed {
        background-color: #d4edda;
        color: #155724;
      }
      
      .status-pending {
        background-color: #fff3cd;
        color: #856404;
      }
      
      .status-failed {
        background-color: #f8d7da;
        color: #721c24;
      }
      
      .backup-stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
      }
      
      .stat-value {
        font-size: 2rem;
        font-weight: bold;
      }
      
      .stat-label {
        font-size: 0.875rem;
        opacity: 0.9;
      }
    "))),
    
    # Main container
    div(
      class = "container-fluid px-4",
      
      # Header with title and action buttons
      div(
        class = "row mb-4",
        div(
          class = "col-12",
          div(
            class = "d-flex justify-content-between align-items-center",
            h3("Database Backup Management", class = "mb-0"),
            div(
              class = "btn-group",
              actionButton(
                ns("refresh_list"),
                "Refresh",
                icon = icon("sync-alt"),
                class = "btn-outline-primary"
              ),
              actionButton(
                ns("create_backup"),
                "Create Backup",
                icon = icon("plus-circle"),
                class = "btn-primary"
              )
            )
          )
        )
      ),
      
      # Statistics Cards
      div(
        class = "row mb-4",
        div(
          class = "col-md-3",
          div(
            class = "backup-stats-card",
            div(class = "stat-value", textOutput(ns("total_backups"), inline = TRUE)),
            div(class = "stat-label", "Total Backups")
          )
        ),
        div(
          class = "col-md-3",
          div(
            class = "backup-stats-card",
            div(class = "stat-value", textOutput(ns("total_size"), inline = TRUE)),
            div(class = "stat-label", "Total Size")
          )
        ),
        div(
          class = "col-md-3",
          div(
            class = "backup-stats-card",
            div(class = "stat-value", textOutput(ns("latest_backup_time"), inline = TRUE)),
            div(class = "stat-label", "Latest Backup")
          )
        ),
        div(
          class = "col-md-3",
          div(
            class = "backup-stats-card",
            div(class = "stat-value", textOutput(ns("backup_status"), inline = TRUE)),
            div(class = "stat-label", "System Status")
          )
        )
      ),
      
      # Backup Table Card
      div(
        class = "card shadow-sm",
        div(
          class = "card-header bg-white",
          h5("Backup History", class = "mb-0")
        ),
        div(
          class = "card-body",
          # DataTable output
          DT::dataTableOutput(ns("backup_table"))
        )
      ),
      
      # Hidden download handler
      tags$div(
        style = "display: none;",
        downloadButton(ns("download_trigger"), "")
      )
    ),
    
    # Create Backup Modal
    bslib::modal(
      id = ns("create_backup_modal"),
      title = "Create Database Backup",
      size = "m",
      footer = tagList(
        actionButton(
          ns("cancel_create"),
          "Cancel",
          class = "btn-secondary"
        ),
        actionButton(
          ns("confirm_create"),
          "Create Backup",
          class = "btn-primary",
          icon = icon("save")
        )
      ),
      
      # Modal content
      div(
        class = "mb-3",
        tags$label("Backup Description", class = "form-label"),
        textInput(
          ns("backup_description"),
          label = NULL,
          placeholder = "e.g., Before major update, Weekly backup, etc.",
          width = "100%"
        )
      ),
      div(
        class = "alert alert-info",
        icon("info-circle"),
        "The backup will be created in the background. You can continue working while it processes."
      )
    ),
    
    # Delete Confirmation Modal
    bslib::modal(
      id = ns("delete_backup_modal"),
      title = "Confirm Deletion",
      size = "m",
      footer = tagList(
        actionButton(
          ns("cancel_delete"),
          "Cancel",
          class = "btn-secondary"
        ),
        actionButton(
          ns("confirm_delete"),
          "Delete",
          class = "btn-danger",
          icon = icon("trash")
        )
      ),
      
      # Modal content
      div(
        class = "alert alert-warning",
        icon("exclamation-triangle"),
        "Are you sure you want to delete this backup?",
        br(),
        br(),
        tags$strong("Filename: "),
        textOutput(ns("delete_filename"), inline = TRUE),
        br(),
        tags$strong("Created: "),
        textOutput(ns("delete_created"), inline = TRUE),
        br(),
        br(),
        "This action cannot be undone."
      )
    ),
    
    # Restore Confirmation Modal
    bslib::modal(
      id = ns("restore_backup_modal"),
      title = "Restore Database - CRITICAL WARNING",
      size = "m",
      footer = tagList(
        actionButton(
          ns("cancel_restore"),
          "Cancel",
          class = "btn-secondary"
        ),
        actionButton(
          ns("confirm_restore"),
          "Restore Database",
          class = "btn-danger",
          icon = icon("database")
        )
      ),
      
      # Modal content
      div(
        class = "alert alert-danger",
        icon("exclamation-triangle"),
        tags$strong("CRITICAL WARNING:"),
        br(),
        "Restoring a backup will COMPLETELY REPLACE the current database!",
        br(),
        br(),
        "All current data will be lost and replaced with the backup data."
      ),
      div(
        class = "mb-3",
        tags$strong("Backup to restore: "),
        textOutput(ns("restore_filename"), inline = TRUE),
        br(),
        tags$strong("Created: "),
        textOutput(ns("restore_created"), inline = TRUE)
      ),
      div(
        class = "form-check mb-3",
        tags$input(
          type = "checkbox",
          class = "form-check-input",
          id = ns("confirm_understand"),
          value = ""
        ),
        tags$label(
          class = "form-check-label text-danger",
          `for` = ns("confirm_understand"),
          "I understand that this will permanently replace all current data"
        )
      )
    )
  )
}