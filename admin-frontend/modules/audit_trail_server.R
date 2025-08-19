# Audit Trail Viewer Server Module

library(httr2)
library(jsonlite)
library(DT)
library(dplyr)
library(lubridate)
library(openxlsx)

audit_trail_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Get API base URL
    api_base_url <- Sys.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
    
    # Reactive values
    values <- reactiveValues(
      audit_logs = NULL,
      filtered_logs = NULL,
      users_list = NULL,
      loading = FALSE,
      error_message = NULL
    )
    
    # Function to fetch audit logs
    fetch_audit_logs <- function(filters = list()) {
      tryCatch({
        values$loading <- TRUE
        values$error_message <- NULL
        
        # Build query parameters
        query_params <- list(limit = 1000)
        
        # Add filters if provided
        if (!is.null(filters$table_name) && filters$table_name != "") {
          query_params$table_name <- filters$table_name
        }
        
        if (!is.null(filters$action) && filters$action != "") {
          query_params$action <- filters$action
        }
        
        if (!is.null(filters$user_id) && filters$user_id != "") {
          query_params$user_id <- as.integer(filters$user_id)
        }
        
        if (!is.null(filters$start_date)) {
          query_params$start_date <- format(filters$start_date, "%Y-%m-%dT00:00:00")
        }
        
        if (!is.null(filters$end_date)) {
          query_params$end_date <- format(filters$end_date, "%Y-%m-%dT23:59:59")
        }
        
        # Make API request with admin header
        response <- request(paste0(api_base_url, "/audit-trail/")) %>%
          req_headers("X-User-Role" = "admin") %>%
          req_url_query(!!!query_params) %>%
          req_perform()
        
        if (resp_status(response) == 200) {
          logs_data <- resp_body_json(response)
          
          # Convert to data frame
          if (length(logs_data) > 0) {
            logs_df <- bind_rows(lapply(logs_data, function(log) {
              data.frame(
                id = log$id %||% NA,
                table_name = log$table_name %||% "",
                record_id = log$record_id %||% NA,
                action = log$action %||% "",
                user_id = log$user_id %||% NA,
                user_name = log$user_name %||% "System",
                user_email = log$user_email %||% "",
                changes_json = ifelse(
                  is.null(log$changes_json) || log$changes_json == "null",
                  "",
                  log$changes_json
                ),
                ip_address = log$ip_address %||% "",
                user_agent = log$user_agent %||% "",
                created_at = log$created_at %||% "",
                stringsAsFactors = FALSE
              )
            }))
            
            # Parse and format timestamps
            logs_df$created_at <- ymd_hms(logs_df$created_at, tz = "UTC")
            logs_df$created_at_formatted <- format(
              logs_df$created_at,
              "%Y-%m-%d %H:%M:%S"
            )
            
            # Format table names for display
            logs_df$table_display <- gsub("_", " ", logs_df$table_name)
            logs_df$table_display <- tools::toTitleCase(logs_df$table_display)
            
            # Add action icons
            logs_df$action_display <- ifelse(
              logs_df$action == "CREATE",
              '<span class="badge bg-success">CREATE</span>',
              ifelse(
                logs_df$action == "UPDATE",
                '<span class="badge bg-warning">UPDATE</span>',
                ifelse(
                  logs_df$action == "DELETE",
                  '<span class="badge bg-danger">DELETE</span>',
                  logs_df$action
                )
              )
            )
            
            values$audit_logs <- logs_df
            values$filtered_logs <- logs_df
          } else {
            values$audit_logs <- data.frame()
            values$filtered_logs <- data.frame()
          }
        } else {
          values$error_message <- "Failed to fetch audit logs"
        }
      }, error = function(e) {
        values$error_message <- paste("Error fetching audit logs:", e$message)
      }) %>%
        finally(function() {
          values$loading <- FALSE
        })
    }
    
    # Function to fetch users list
    fetch_users <- function() {
      tryCatch({
        response <- request(paste0(api_base_url, "/users/")) %>%
          req_perform()
        
        if (resp_status(response) == 200) {
          users_data <- resp_body_json(response)
          
          if (length(users_data) > 0) {
            users_df <- bind_rows(lapply(users_data, function(user) {
              data.frame(
                id = user$id,
                name = paste(user$first_name, user$last_name),
                stringsAsFactors = FALSE
              )
            }))
            
            values$users_list <- users_df
            
            # Update user filter choices
            user_choices <- c("All" = "")
            user_choices <- c(
              user_choices,
              setNames(as.character(users_df$id), users_df$name)
            )
            
            updateSelectInput(
              session,
              "filter_user",
              choices = user_choices
            )
          }
        }
      }, error = function(e) {
        # Silently fail - users list is not critical
      })
    }
    
    # Initial load
    observe({
      fetch_audit_logs()
      fetch_users()
    })
    
    # Apply filters
    observeEvent(input$apply_filters, {
      filters <- list()
      
      if (input$filter_table != "") {
        filters$table_name <- input$filter_table
      }
      
      if (input$filter_action != "") {
        filters$action <- input$filter_action
      }
      
      if (input$filter_user != "") {
        filters$user_id <- input$filter_user
      }
      
      # Handle time range
      if (input$filter_time_range != "" && input$filter_time_range != "custom") {
        if (input$filter_time_range == "1h") {
          filters$start_date <- Sys.time() - hours(1)
        } else if (input$filter_time_range == "24h") {
          filters$start_date <- Sys.time() - days(1)
        } else if (input$filter_time_range == "7d") {
          filters$start_date <- Sys.Date() - days(7)
        } else if (input$filter_time_range == "30d") {
          filters$start_date <- Sys.Date() - days(30)
        }
        filters$end_date <- Sys.Date()
      } else if (input$filter_time_range == "custom") {
        filters$start_date <- input$start_date
        filters$end_date <- input$end_date
      }
      
      fetch_audit_logs(filters)
    })
    
    # Reset filters
    observeEvent(input$reset_filters, {
      updateSelectInput(session, "filter_table", selected = "")
      updateSelectInput(session, "filter_action", selected = "")
      updateSelectInput(session, "filter_user", selected = "")
      updateSelectInput(session, "filter_time_range", selected = "24h")
      
      # Fetch last 24 hours by default
      filters <- list(
        start_date = Sys.time() - days(1),
        end_date = Sys.Date()
      )
      fetch_audit_logs(filters)
    })
    
    # Refresh logs
    observeEvent(input$refresh_logs, {
      # Re-apply current filters
      isolate({
        filters <- list()
        
        if (input$filter_table != "") {
          filters$table_name <- input$filter_table
        }
        
        if (input$filter_action != "") {
          filters$action <- input$filter_action
        }
        
        if (input$filter_user != "") {
          filters$user_id <- input$filter_user
        }
        
        if (input$filter_time_range != "" && input$filter_time_range != "custom") {
          if (input$filter_time_range == "1h") {
            filters$start_date <- Sys.time() - hours(1)
          } else if (input$filter_time_range == "24h") {
            filters$start_date <- Sys.time() - days(1)
          } else if (input$filter_time_range == "7d") {
            filters$start_date <- Sys.Date() - days(7)
          } else if (input$filter_time_range == "30d") {
            filters$start_date <- Sys.Date() - days(30)
          }
          filters$end_date <- Sys.Date()
        } else if (input$filter_time_range == "custom") {
          filters$start_date <- input$start_date
          filters$end_date <- input$end_date
        }
        
        fetch_audit_logs(filters)
      })
    })
    
    # Export to Excel
    observeEvent(input$export_logs, {
      if (!is.null(values$filtered_logs) && nrow(values$filtered_logs) > 0) {
        tryCatch({
          # Prepare data for export
          export_data <- values$filtered_logs %>%
            select(
              ID = id,
              Table = table_display,
              `Record ID` = record_id,
              Action = action,
              User = user_name,
              Email = user_email,
              `IP Address` = ip_address,
              Timestamp = created_at_formatted,
              Changes = changes_json
            )
          
          # Create workbook
          wb <- createWorkbook()
          addWorksheet(wb, "Audit Log")
          
          # Write data
          writeData(wb, "Audit Log", export_data)
          
          # Style the header
          headerStyle <- createStyle(
            fontSize = 12,
            fontColour = "#FFFFFF",
            halign = "center",
            fgFill = "#4472C4",
            border = "TopBottomLeftRight",
            borderColour = "#000000"
          )
          
          addStyle(
            wb,
            sheet = "Audit Log",
            headerStyle,
            rows = 1,
            cols = 1:ncol(export_data),
            gridExpand = TRUE
          )
          
          # Auto-size columns
          setColWidths(wb, "Audit Log", cols = 1:ncol(export_data), widths = "auto")
          
          # Save file
          filename <- paste0(
            "audit_log_",
            format(Sys.time(), "%Y%m%d_%H%M%S"),
            ".xlsx"
          )
          
          saveWorkbook(wb, filename, overwrite = TRUE)
          
          show_success_notification(
            paste("Audit log exported to", filename)
          )
        }, error = function(e) {
          show_error_notification(
            paste("Failed to export:", e$message)
          )
        })
      } else {
        show_warning_notification(
          "No data to export"
        )
      }
    })
    
    # Summary statistics
    output$total_changes <- renderText({
      if (!is.null(values$filtered_logs)) {
        format(nrow(values$filtered_logs), big.mark = ",")
      } else {
        "0"
      }
    })
    
    output$total_creates <- renderText({
      if (!is.null(values$filtered_logs)) {
        count <- sum(values$filtered_logs$action == "CREATE", na.rm = TRUE)
        format(count, big.mark = ",")
      } else {
        "0"
      }
    })
    
    output$total_updates <- renderText({
      if (!is.null(values$filtered_logs)) {
        count <- sum(values$filtered_logs$action == "UPDATE", na.rm = TRUE)
        format(count, big.mark = ",")
      } else {
        "0"
      }
    })
    
    output$total_deletes <- renderText({
      if (!is.null(values$filtered_logs)) {
        count <- sum(values$filtered_logs$action == "DELETE", na.rm = TRUE)
        format(count, big.mark = ",")
      } else {
        "0"
      }
    })
    
    # Render audit table
    output$audit_table <- DT::renderDataTable({
      if (!is.null(values$filtered_logs) && nrow(values$filtered_logs) > 0) {
        # Select columns to display
        display_data <- values$filtered_logs %>%
          select(
            ID = id,
            Table = table_display,
            `Record ID` = record_id,
            Action = action_display,
            User = user_name,
            Timestamp = created_at_formatted
          )
        
        datatable(
          display_data,
          options = list(
            pageLength = 25,
            lengthMenu = c(10, 25, 50, 100),
            searching = TRUE,
            ordering = TRUE,
            order = list(list(5, 'desc')),  # Sort by timestamp desc
            columnDefs = list(
              list(className = 'dt-center', targets = c(0, 2, 3)),
              list(width = '100px', targets = 3)
            ),
            dom = 'Bfrtip',
            buttons = list(),
            scrollX = TRUE
          ),
          escape = FALSE,  # Allow HTML in action_display column
          rownames = FALSE,
          selection = 'single'
        )
      } else {
        datatable(
          data.frame(Message = "No audit logs found"),
          options = list(
            dom = 't',
            language = list(
              emptyTable = "No audit logs found for the selected filters"
            )
          ),
          rownames = FALSE
        )
      }
    })
    
    # Show details on row click
    observeEvent(input$audit_table_rows_selected, {
      selected_row <- input$audit_table_rows_selected
      
      if (!is.null(selected_row) && !is.null(values$filtered_logs)) {
        log_entry <- values$filtered_logs[selected_row, ]
        
        # Parse changes JSON if available
        changes_html <- ""
        if (!is.null(log_entry$changes_json) && log_entry$changes_json != "") {
          tryCatch({
            changes <- fromJSON(log_entry$changes_json)
            
            if (is.list(changes)) {
              changes_html <- "<h5>Changes:</h5><pre class='bg-light p-2'>"
              changes_html <- paste0(
                changes_html,
                jsonlite::toJSON(changes, pretty = TRUE, auto_unbox = TRUE)
              )
              changes_html <- paste0(changes_html, "</pre>")
            }
          }, error = function(e) {
            changes_html <- paste0(
              "<h5>Raw Changes:</h5><pre class='bg-light p-2'>",
              log_entry$changes_json,
              "</pre>"
            )
          })
        }
        
        # Create details content
        details_content <- div(
          class = "container-fluid",
          div(
            class = "row mb-3",
            div(class = "col-md-6",
                strong("Table:"), log_entry$table_display),
            div(class = "col-md-6",
                strong("Record ID:"), log_entry$record_id)
          ),
          div(
            class = "row mb-3",
            div(class = "col-md-6",
                strong("Action:"), HTML(log_entry$action_display)),
            div(class = "col-md-6",
                strong("Timestamp:"), log_entry$created_at_formatted)
          ),
          div(
            class = "row mb-3",
            div(class = "col-md-6",
                strong("User:"), log_entry$user_name),
            div(class = "col-md-6",
                strong("Email:"), log_entry$user_email)
          ),
          div(
            class = "row mb-3",
            div(class = "col-md-6",
                strong("IP Address:"), log_entry$ip_address),
            div(class = "col-md-6",
                strong("User Agent:"), 
                div(
                  style = "word-break: break-all;",
                  log_entry$user_agent
                )
            )
          ),
          if (changes_html != "") {
            HTML(changes_html)
          }
        )
        
        showModal(
          create_view_modal(
            title = paste("Audit Log Details - ID:", log_entry$id),
            content = details_content,
            size = "l"
          )
        )
      }
    })
    
    # Universal CRUD Manager integration (Phase 2)
    # Replaces entity-specific WebSocket observer with standardized refresh trigger
    observeEvent(input$crud_refresh, {
      if (!is.null(input$crud_refresh)) {
        cat("📋 Universal CRUD refresh triggered for audit trail\n")
        # Apply current filters and refresh
        isolate({
          filters <- list()
          
          if (input$filter_table != "") {
            filters$table_name <- input$filter_table
          }
          
          if (input$filter_action != "") {
            filters$action <- input$filter_action
          }
          
          if (input$filter_user != "") {
            filters$user_id <- input$filter_user
          }
          
          if (input$filter_time_range != "" && input$filter_time_range != "custom") {
            if (input$filter_time_range == "1h") {
              filters$start_date <- Sys.time() - hours(1)
            } else if (input$filter_time_range == "24h") {
              filters$start_date <- Sys.time() - days(1)
            } else if (input$filter_time_range == "7d") {
              filters$start_date <- Sys.Date() - days(7)
            } else if (input$filter_time_range == "30d") {
              filters$start_date <- Sys.Date() - days(30)
            }
            filters$end_date <- Sys.Date()
          } else if (input$filter_time_range == "custom") {
            filters$start_date <- input$start_date
            filters$end_date <- input$end_date
          }
          
          fetch_audit_logs(filters)
        })
      }
    })
    
    # Legacy WebSocket observer (kept for backward compatibility during transition)
    observe({
      # Listen for audit log WebSocket events
      audit_event <- input$`audit-trail-websocket_event`
      
      if (!is.null(audit_event)) {
        # Refresh the audit logs when a new event is received
        isolate({
          # Apply current filters
          filters <- list()
          
          if (input$filter_table != "") {
            filters$table_name <- input$filter_table
          }
          
          if (input$filter_action != "") {
            filters$action <- input$filter_action
          }
          
          if (input$filter_user != "") {
            filters$user_id <- input$filter_user
          }
          
          if (input$filter_time_range != "" && input$filter_time_range != "custom") {
            if (input$filter_time_range == "1h") {
              filters$start_date <- Sys.time() - hours(1)
            } else if (input$filter_time_range == "24h") {
              filters$start_date <- Sys.time() - days(1)
            } else if (input$filter_time_range == "7d") {
              filters$start_date <- Sys.Date() - days(7)
            } else if (input$filter_time_range == "30d") {
              filters$start_date <- Sys.Date() - days(30)
            }
            filters$end_date <- Sys.Date()
          } else if (input$filter_time_range == "custom") {
            filters$start_date <- input$start_date
            filters$end_date <- input$end_date
          }
          
          fetch_audit_logs(filters)
        })
      }
    })
    
    # Error handling
    observe({
      if (!is.null(values$error_message)) {
        show_error_notification(
          values$error_message,
          duration = 5000
        )
        values$error_message <- NULL
      }
    })
    
    # Loading indicator
    observe({
      if (values$loading) {
        show_success_notification(
          "Loading audit logs...",
          duration = NULL
        )
      } else {
        removeNotification("loading_notification")
      }
    })
  })
}