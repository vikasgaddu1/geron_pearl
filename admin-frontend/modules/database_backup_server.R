# Database Backup Server Module

database_backup_server <- function(id, api_client, user_info) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Reactive values
    rv <- reactiveValues(
      backups = list(),
      status = list(),
      selected_backup = NULL,
      selected_for_delete = NULL,
      selected_for_restore = NULL,
      last_refresh = NULL
    )
    
    # Helper function to format file size
    format_file_size <- function(bytes) {
      if (is.null(bytes) || is.na(bytes)) return("N/A")
      
      if (bytes < 1024) {
        return(paste0(bytes, " B"))
      } else if (bytes < 1024^2) {
        return(paste0(round(bytes / 1024, 1), " KB"))
      } else if (bytes < 1024^3) {
        return(paste0(round(bytes / 1024^2, 1), " MB"))
      } else {
        return(paste0(round(bytes / 1024^3, 2), " GB"))
      }
    }
    
    # Helper function to format date
    format_date <- function(date_str) {
      if (is.null(date_str) || is.na(date_str)) return("N/A")
      
      tryCatch({
        dt <- as.POSIXct(date_str, format = "%Y-%m-%dT%H:%M:%S", tz = "UTC")
        format(dt, "%Y-%m-%d %H:%M:%S")
      }, error = function(e) {
        return(date_str)
      })
    }
    
    # Helper function to format relative time
    format_relative_time <- function(date_str) {
      if (is.null(date_str) || is.na(date_str)) return("Never")
      
      tryCatch({
        dt <- as.POSIXct(date_str, format = "%Y-%m-%dT%H:%M:%S", tz = "UTC")
        diff <- difftime(Sys.time(), dt, units = "auto")
        
        if (diff < 1) {
          return("Just now")
        } else if (diff < 60) {
          return(paste0(round(diff), " min ago"))
        } else if (diff < 1440) {
          hours <- round(as.numeric(diff) / 60)
          return(paste0(hours, " hour", ifelse(hours > 1, "s", ""), " ago"))
        } else {
          days <- round(as.numeric(diff) / 1440)
          return(paste0(days, " day", ifelse(days > 1, "s", ""), " ago"))
        }
      }, error = function(e) {
        return("Unknown")
      })
    }
    
    # Load backup list
    load_backups <- function() {
      result <- list_database_backups()
      
      if (result$success) {
        rv$backups <- result$data
        rv$last_refresh <- Sys.time()
      } else {
        show_error_notification(
          paste("Failed to load backups:", result$error),
          duration = 5000
        )
      }
    }
    
    # Load backup status
    load_status <- function() {
      result <- get_database_backup_status()
      
      if (result$success) {
        rv$status <- result$data
      }
    }
    
    # Initial load
    observe({
      load_backups()
      load_status()
    })
    
    # Refresh button
    observeEvent(input$refresh_list, {
      load_backups()
      load_status()
      show_success_notification(
        "Backup list refreshed",
        duration = 2000
      )
    })
    
    # Auto-refresh every 30 seconds if there are pending backups
    observe({
      invalidateLater(30000, session)
      
      if (length(rv$backups) > 0) {
        pending_backups <- Filter(function(b) b$status == "pending", rv$backups)
        if (length(pending_backups) > 0) {
          load_backups()
        }
      }
    })
    
    # Statistics outputs
    output$total_backups <- renderText({
      as.character(length(rv$backups))
    })
    
    output$total_size <- renderText({
      if (length(rv$status) > 0 && !is.null(rv$status$total_size_mb)) {
        paste0(round(rv$status$total_size_mb, 1), " MB")
      } else {
        "0 MB"
      }
    })
    
    output$latest_backup_time <- renderText({
      if (length(rv$backups) > 0) {
        latest <- rv$backups[[1]]  # Already sorted by date
        format_relative_time(latest$created_at)
      } else {
        "Never"
      }
    })
    
    output$backup_status <- renderText({
      if (length(rv$status) > 0 && !is.null(rv$status$pg_dump_available)) {
        if (rv$status$pg_dump_available) {
          "Ready"
        } else {
          "Error"
        }
      } else {
        "Unknown"
      }
    })
    
    # Render backup table
    output$backup_table <- DT::renderDataTable({
      req(length(rv$backups) > 0)
      
      # Create data frame
      df <- data.frame(
        Status = sapply(rv$backups, function(b) {
          status <- b$status %||% "unknown"
          badge_class <- switch(status,
            "completed" = "status-completed",
            "pending" = "status-pending",
            "failed" = "status-failed",
            "status-unknown"
          )
          icon_name <- switch(status,
            "completed" = "check-circle",
            "pending" = "spinner fa-spin",
            "failed" = "exclamation-circle",
            "question-circle"
          )
          paste0(
            '<span class="backup-status-badge ', badge_class, '">',
            '<i class="fas fa-', icon_name, '"></i> ',
            toupper(status),
            '</span>'
          )
        }),
        Filename = sapply(rv$backups, function(b) b$filename %||% "Unknown"),
        Description = sapply(rv$backups, function(b) b$description %||% ""),
        Size = sapply(rv$backups, function(b) format_file_size(b$size_bytes)),
        Created = sapply(rv$backups, function(b) format_date(b$created_at)),
        Actions = sapply(seq_along(rv$backups), function(i) {
          b <- rv$backups[[i]]
          buttons <- character(0)
          
          # Download button (only for completed backups)
          if (!is.null(b$status) && b$status == "completed" && !is.null(b$file_exists) && b$file_exists) {
            buttons <- c(buttons, paste0(
              '<button class="btn btn-sm btn-outline-primary download-btn" data-index="', i, '" ',
              'title="Download backup">',
              '<i class="fas fa-download"></i>',
              '</button>'
            ))
          }
          
          # Restore button (only for completed backups)
          if (!is.null(b$status) && b$status == "completed" && !is.null(b$file_exists) && b$file_exists) {
            buttons <- c(buttons, paste0(
              '<button class="btn btn-sm btn-outline-warning restore-btn" data-index="', i, '" ',
              'title="Restore from backup">',
              '<i class="fas fa-database"></i>',
              '</button>'
            ))
          }
          
          # Delete button
          buttons <- c(buttons, paste0(
            '<button class="btn btn-sm btn-outline-danger delete-btn" data-index="', i, '" ',
            'title="Delete backup">',
            '<i class="fas fa-trash"></i>',
            '</button>'
          ))
          
          paste0('<div class="btn-group" role="group">', paste(buttons, collapse = " "), '</div>')
        }),
        stringsAsFactors = FALSE
      )
      
      DT::datatable(
        df,
        escape = FALSE,
        selection = "none",
        options = list(
          dom = 'Bfrtip',
          pageLength = 10,
          ordering = TRUE,
          order = list(list(4, 'desc')),  # Sort by Created column
          columnDefs = list(
            list(className = 'text-center', targets = c(0, 5)),
            list(width = '100px', targets = 0),
            list(width = '180px', targets = 5)
          ),
          language = list(
            emptyTable = "No backups found",
            zeroRecords = "No matching backups"
          )
        ),
        rownames = FALSE
      )
    }, server = FALSE)
    
    # Handle table button clicks
    observeEvent(input$backup_table_cell_clicked, {
      info <- input$backup_table_cell_clicked
      
      if (!is.null(info$value)) {
        # Parse the clicked element
        if (grepl("download-btn", info$value)) {
          # Extract index from data-index attribute
          index <- as.numeric(gsub(".*data-index=\"([0-9]+)\".*", "\\1", info$value))
          if (!is.na(index) && index <= length(rv$backups)) {
            download_backup(rv$backups[[index]])
          }
        } else if (grepl("restore-btn", info$value)) {
          # Extract index from data-index attribute
          index <- as.numeric(gsub(".*data-index=\"([0-9]+)\".*", "\\1", info$value))
          if (!is.na(index) && index <= length(rv$backups)) {
            show_restore_dialog(rv$backups[[index]])
          }
        } else if (grepl("delete-btn", info$value)) {
          # Extract index from data-index attribute
          index <- as.numeric(gsub(".*data-index=\"([0-9]+)\".*", "\\1", info$value))
          if (!is.na(index) && index <= length(rv$backups)) {
            show_delete_dialog(rv$backups[[index]])
          }
        }
      }
    })
    
    # Create backup
    observeEvent(input$create_backup, {
      # Modal content
      content <- div(
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
      )
      
      showModal(
        create_create_modal(
          title = "Create Database Backup",
          content = content,
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
          )
        )
      )
    })
    
    observeEvent(input$cancel_create, {
      removeModal()
    })
    
    observeEvent(input$confirm_create, {
      description <- trimws(input$backup_description)
      if (description == "") {
        description <- NULL
      }
      
      # Call API to create backup
      result <- create_database_backup(description = description)
      
      if (result$success) {
        show_success_notification(
          "Backup creation initiated. It will run in the background.",
          duration = 5000
        )
        removeModal()
        
        # Refresh list after a short delay
        shinyjs::delay(2000, {
          load_backups()
          load_status()
        })
      } else {
        show_error_notification(
          paste("Failed to create backup:", result$error),
          duration = 5000
        )
      }
    })
    
    # Download backup
    download_backup <- function(backup) {
      if (is.null(backup$filename)) return()
      
      # Trigger download through API
      api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
      download_url <- paste0(
        api_base,
        "/api/v1/database-backup/download/",
        backup$filename
      )
      
      # Use JavaScript to trigger download
      shinyjs::runjs(sprintf(
        "window.open('%s', '_blank');",
        download_url
      ))
    }
    
    # Delete backup
    show_delete_dialog <- function(backup) {
      rv$selected_for_delete <- backup
      
      # Modal content
      content <- div(
        class = "alert alert-warning",
        icon("exclamation-triangle"),
        "Are you sure you want to delete this backup?",
        br(),
        br(),
        tags$strong("Filename: "),
        backup$filename,
        br(),
        tags$strong("Created: "),
        format_date(backup$created_at),
        br(),
        br(),
        "This action cannot be undone."
      )
      
      showModal(
        create_delete_confirmation_modal(
          title = "Confirm Deletion",
          content = content,
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
          )
        )
      )
    }
    
    output$delete_filename <- renderText({
      if (!is.null(rv$selected_for_delete)) {
        rv$selected_for_delete$filename
      } else {
        "Unknown"
      }
    })
    
    output$delete_created <- renderText({
      if (!is.null(rv$selected_for_delete)) {
        format_date(rv$selected_for_delete$created_at)
      } else {
        "Unknown"
      }
    })
    
    observeEvent(input$cancel_delete, {
      rv$selected_for_delete <- NULL
      removeModal()
    })
    
    observeEvent(input$confirm_delete, {
      req(rv$selected_for_delete)
      
      result <- delete_database_backup(rv$selected_for_delete$filename)
      
      if (result$success) {
        show_success_notification(
          "Backup deleted successfully",
          duration = 3000
        )
        removeModal()
        rv$selected_for_delete <- NULL
        load_backups()
        load_status()
      } else {
        show_error_notification(
          paste("Failed to delete backup:", result$error),
          duration = 5000
        )
      }
    })
    
    # Restore backup
    show_restore_dialog <- function(backup) {
      rv$selected_for_restore <- backup
      
      # Modal content
      content <- div(
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
          backup$filename,
          br(),
          tags$strong("Created: "),
          format_date(backup$created_at)
        ),
        div(
          class = "form-check mb-3",
          checkboxInput(
            ns("confirm_understand"),
            "I understand that this will permanently replace all current data",
            value = FALSE
          )
        )
      )
      
      showModal(
        create_delete_confirmation_modal(
          title = "Restore Database - CRITICAL WARNING",
          content = content,
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
          )
        )
      )
    }
    
    output$restore_filename <- renderText({
      if (!is.null(rv$selected_for_restore)) {
        rv$selected_for_restore$filename
      } else {
        "Unknown"
      }
    })
    
    output$restore_created <- renderText({
      if (!is.null(rv$selected_for_restore)) {
        format_date(rv$selected_for_restore$created_at)
      } else {
        "Unknown"
      }
    })
    
    observeEvent(input$cancel_restore, {
      rv$selected_for_restore <- NULL
      removeModal()
    })
    
    observeEvent(input$confirm_restore, {
      req(rv$selected_for_restore)
      
      # Check if user confirmed understanding
      if (!input$confirm_understand) {
        show_warning_notification(
          "Please confirm that you understand the consequences",
          duration = 3000
        )
        return()
      }
      
      result <- restore_database_backup(rv$selected_for_restore$filename)
      
      if (result$success) {
        show_warning_notification(
          HTML(paste(
            "<strong>Database restore initiated!</strong><br>",
            "The application may be unavailable during the restore process.<br>",
            "This may take several minutes depending on the backup size."
          )),
          duration = 10000
        )
        removeModal()
        rv$selected_for_restore <- NULL
      } else {
        show_error_notification(
          paste("Failed to initiate restore:", result$error),
          duration = 5000
        )
      }
    })
    
    # Universal CRUD Manager integration (Phase 2)
    # Replaces entity-specific WebSocket observer with standardized refresh trigger
    observeEvent(input$crud_refresh, {
      if (!is.null(input$crud_refresh)) {
        cat("💾 Universal CRUD refresh triggered for database backup\n")
        load_backups()
        load_status()
      }
    })
    
    # Legacy WebSocket observer (kept for backward compatibility during transition)
    observeEvent(input$`database-backup-websocket_event`, {
      # Reload backups when we receive a WebSocket event
      load_backups()
      load_status()
    })
    
    # Return module interface
    return(list(
      refresh = function() {
        load_backups()
        load_status()
      }
    ))
  })
}