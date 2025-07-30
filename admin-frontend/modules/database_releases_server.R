# Database Releases Server Module - CRUD operations with WebSocket support

database_releases_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Reactive values
    releases_data <- reactiveVal(data.frame())
    studies_data <- reactiveVal(data.frame())
    filtered_releases <- reactiveVal(data.frame())
    last_update <- reactiveVal(Sys.time())
    is_editing <- reactiveVal(FALSE)
    editing_release_id <- reactiveVal(NULL)
    
    # Set up validation for new release form
    iv_new <- InputValidator$new()
    iv_new$add_rule("new_study_id", sv_required())
    iv_new$add_rule("new_release_label", sv_required())
    iv_new$add_rule("new_release_label", function(value) {
      current_releases <- releases_data()
      current_study_id <- input$new_study_id
      if (nrow(current_releases) > 0 && !is.null(current_study_id) && current_study_id != "") {
        study_releases <- current_releases[current_releases$`Study ID` == as.numeric(current_study_id), ]
        if (nrow(study_releases) > 0 && trimws(value) %in% study_releases$`Release Label`) {
          "A database release with this label already exists for this study"
        }
      }
    })
    
    # Set up validation for edit release form
    iv_edit <- InputValidator$new()
    iv_edit$add_rule("edit_study_id", sv_required())
    iv_edit$add_rule("edit_release_label", sv_required())
    iv_edit$add_rule("edit_release_label", function(value) {
      current_releases <- releases_data()
      current_release_id <- editing_release_id()
      current_study_id <- input$edit_study_id
      if (nrow(current_releases) > 0 && !is.null(current_release_id) && !is.null(current_study_id)) {
        # Check for duplicates within the same study, excluding current release
        study_releases <- current_releases[current_releases$`Study ID` == as.numeric(current_study_id) & current_releases$ID != current_release_id, ]
        if (nrow(study_releases) > 0 && trimws(value) %in% study_releases$`Release Label`) {
          "A database release with this label already exists for this study"
        }
      }
    })
    
    # Note: Edit functionality not implemented yet - following studies module pattern
    
    # Convert API data to data frame
    convert_releases_to_df <- function(releases_list, current_studies = NULL) {
      if (length(releases_list) > 0) {
        df <- data.frame(
          ID = sapply(releases_list, function(x) x$id),
          `Study ID` = sapply(releases_list, function(x) x$study_id),
          `Study Label` = sapply(releases_list, function(x) {
            study_id <- x$study_id
            if (!is.null(current_studies) && nrow(current_studies) > 0) {
              study_row <- current_studies[current_studies$ID == study_id, ]
              if (nrow(study_row) > 0) {
                return(study_row$`Study Label`[1])
              }
            }
            return(paste("Study", study_id))
          }),
          `Release Label` = sapply(releases_list, function(x) x$database_release_label),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(df)
      } else {
        return(data.frame(
          ID = character(0),
          `Study ID` = numeric(0),
          `Study Label` = character(0),
          `Release Label` = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        ))
      }
    }
    
    # Load studies data
    load_studies_http <- function() {
      studies_result <- get_studies()
      if (!is.null(studies_result$error)) {
        cat("❌ Error loading studies:", studies_result$error, "\n")
        studies_data(data.frame())
      } else {
        studies_df <- data.frame(
          ID = sapply(studies_result, function(x) x$id),
          `Study Label` = sapply(studies_result, function(x) x$study_label),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        studies_data(studies_df)
        cat("✅ Studies loaded for reference:", nrow(studies_df), "studies\n")
      }
    }
    
    # Load database releases data
    load_releases_data <- function() {
      cat("🔄 Loading database releases data...\n")
      
      releases_result <- get_database_releases()
      if (!is.null(releases_result$error)) {
        cat("❌ Error loading database releases:", releases_result$error, "\n")
        cat("❌ Error loading database releases:", releases_result$error, "\n")
        releases_data(data.frame())
      } else {
        # Get current studies data safely
        current_studies <- isolate(studies_data())
        releases_df <- convert_releases_to_df(releases_result, current_studies)
        releases_data(releases_df)
        last_update(Sys.time())
        cat("✅ Database releases loaded successfully:", nrow(releases_df), "releases\n")
        cat("✅ Database releases loaded successfully:", nrow(releases_df), "releases\n")
      }
    }
    
    # Load data on module initialization
    load_studies_http()
    load_releases_data()
    
    # Initialize filtered_releases to show all releases by default
    observeEvent(releases_data(), {
      if (is.null(input$new_study_id) || input$new_study_id == "") {
        filtered_releases(releases_data())
      }
    }, ignoreInit = FALSE)
    
    # Update dropdown choices when studies data changes
    observeEvent(studies_data(), {
      current_studies <- studies_data()
      if (nrow(current_studies) > 0) {
        choices <- c("Select a study" = "", setNames(current_studies$ID, current_studies$`Study Label`))
        updateSelectInput(session, "new_study_id", choices = choices, selected = "")
        cat("✅ Studies data updated, refreshed dropdown with", nrow(current_studies), "studies\n")
      } else {
        updateSelectInput(session, "new_study_id", choices = list("No studies available" = ""), selected = "")
        cat("⚠️ No studies data available\n")
      }
    })
    
    # Note: WebSocket status is now handled in main app.R
    
    # Handle WebSocket events from JavaScript
    observeEvent(input$websocket_event, {
      event <- input$websocket_event
      cat("📥 WebSocket event observer triggered. Event:", if(is.null(event)) "NULL" else event$type, "\n")
      if (is.null(event)) return()
      
      cat("📊 Processing WebSocket event:", event$type, "with data length:", length(event$data), "\n")
      
      if (event$type == "database_release_created") {
        cat("➕ Database release created via WebSocket, refreshing data\n")
        load_releases_data()
      } else if (event$type == "database_release_updated") {
        cat("✏️ Database release updated via WebSocket, refreshing data\n")
        load_releases_data()
      } else if (event$type == "database_release_deleted") {
        cat("🗑️ Database release deleted via WebSocket, refreshing data\n")
        load_releases_data()
      } else if (event$type == "studies_update") {
        # Update studies data for dropdown
        cat("📚 Studies updated via WebSocket, updating reference data\n")
        studies_df <- convert_studies_to_df_simple(event$data)
        studies_data(studies_df)
        # Refresh releases to update study labels
        load_releases_data()
      }
    })
    
    # Helper function for studies data
    convert_studies_to_df_simple <- function(studies_list) {
      if (length(studies_list) > 0) {
        data.frame(
          ID = sapply(studies_list, function(x) x$id),
          `Study Label` = sapply(studies_list, function(x) x$study_label),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
      } else {
        data.frame(
          ID = numeric(0),
          `Study Label` = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
      }
    }
    
    # Refresh button
    observeEvent(input$refresh_btn, {
      cat("🔄 Manual refresh triggered\n")
      load_studies_http()
      load_releases_data()
    })
    
    
    # Data table output
    output$releases_table <- DT::renderDataTable({
      releases <- filtered_releases()
      
      if (nrow(releases) == 0) {
        # Determine appropriate empty message based on filter state
        current_studies <- studies_data()
        empty_message <- if (!is.null(input$new_study_id) && input$new_study_id != "") {
          # Filtered view - show study-specific message
          study_row <- current_studies[current_studies$ID == as.numeric(input$new_study_id), ]
          study_name <- if (nrow(study_row) > 0) study_row$`Study Label`[1] else "Selected Study"
          paste("No database releases found for", study_name, ". Click 'Create' to add the first release.")
        } else {
          # Default view - show general message
          "No database releases found. Click 'Add Release' to create your first database release."
        }
        
        # Return empty table with consistent structure (only visible columns)
        empty_df <- data.frame(
          `Study Label` = character(0),
          `Release Label` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(DT::datatable(
          empty_df,
          filter = 'top', # Add column filters on top
          options = list(
            dom = 'frtip', # Show filter, processing, table, info, pagination
            pageLength = 10,
            autoWidth = FALSE,
            search = list(regex = TRUE, caseInsensitive = TRUE), # Enable regex search
            columnDefs = list(
              list(targets = 0, width = "35%"), # Study Label column
              list(targets = 1, width = "35%"), # Release Label column
              list(targets = 2, width = "30%", orderable = FALSE, className = "text-center", searchable = FALSE) # Actions column - not searchable
            ),
            language = list(
              emptyTable = empty_message,
              search = "",
              searchPlaceholder = "Search (regex supported): e.g., MYF.*|jan_.*"
            ),
            searching = TRUE, # Explicitly enable searching
            info = TRUE # Show table info
          ),
          rownames = FALSE,
          escape = FALSE
        ))
      }
      
      # Add action buttons to the Actions column
      releases$Actions <- sapply(releases$ID, function(id) {
        as.character(div(
          class = "d-flex gap-2 justify-content-center",
          tags$button(
            class = "btn btn-warning btn-sm",
            `data-action` = "edit",
            `data-id` = id,
            title = paste("Edit database release", releases$`Release Label`[releases$ID == id]),
            tagList(bs_icon("pencil"), "Edit")
          ),
          tags$button(
            class = "btn btn-danger btn-sm",
            `data-action` = "delete",
            `data-id` = id,
            title = paste("Delete database release", releases$`Release Label`[releases$ID == id]),
            tagList(bs_icon("trash"), "Delete")
          )
        ))
      })
      
      # Sort releases by Study ID first, then by Release ID
      releases <- releases[order(releases$`Study ID`, releases$ID), ]
      
      # Hide ID and Study ID columns but keep for reference
      display_df <- releases[, c("Study Label", "Release Label", "Actions"), drop = FALSE]
      
      DT::datatable(
        display_df,
        filter = 'top', # Add column filters on top
        options = list(
          dom = 'frtip', # Show filter, processing, table, info, pagination
          pageLength = 10,
          autoWidth = FALSE,
          search = list(regex = TRUE, caseInsensitive = TRUE), # Enable regex search
          columnDefs = list(
            list(targets = 0, width = "35%"), # Study Label column
            list(targets = 1, width = "35%"), # Release Label column
            list(targets = 2, width = "30%", orderable = FALSE, className = "text-center", searchable = FALSE) # Actions column - not searchable
          ),
          language = list(
            search = "",
            searchPlaceholder = "Search (regex supported): e.g., MYF.*|jan_.*"
          ),
          searching = TRUE, # Explicitly enable searching
          info = TRUE, # Show table info
          drawCallback = JS(sprintf("
            function() {
              var table = this;
              $('#%s button[data-action=\"edit\"]').off('click').on('click', function() {
                var id = $(this).attr('data-id');
                Shiny.setInputValue('%s', id, {priority: 'event'});
              });
              $('#%s button[data-action=\"delete\"]').off('click').on('click', function() {
                var id = $(this).attr('data-id');
                Shiny.setInputValue('%s', id, {priority: 'event'});
              });
            }
          ", ns("releases_table"), ns("edit_release_id"), 
             ns("releases_table"), ns("delete_release_id")))
        ),
        rownames = FALSE,
        escape = FALSE, # Allow HTML in Actions column
        selection = 'none'
      )
    }, server = FALSE)
    
    
    # Filter releases based on selected study in add form dropdown
    observeEvent(input$new_study_id, {
      current_releases <- releases_data()
      if (!is.null(input$new_study_id) && input$new_study_id != "") {
        # Filter to show only releases for selected study
        should_show_all_releases(FALSE)
        filtered <- current_releases[current_releases$`Study ID` == as.numeric(input$new_study_id), ]
        filtered_releases(filtered)
        cat("🔍 Filtering table to show", nrow(filtered), "releases for study ID", input$new_study_id, "\n")
      } else {
        # Show all releases when no study is selected
        should_show_all_releases(TRUE)
        filtered_releases(current_releases)
        cat("📋 Showing all", nrow(current_releases), "releases\n")
      }
    }, ignoreInit = TRUE)
    
    # Update filtered data when releases data changes
    observeEvent(releases_data(), {
      current_releases <- releases_data()
      
      # Check if we should maintain "show all" state (after creation/reset)
      if (should_show_all_releases()) {
        filtered_releases(current_releases)
        cat("🔄 Data updated: Maintaining show all state (", nrow(current_releases), "releases)\n")
      } else if (!is.null(input$new_study_id) && input$new_study_id != "") {
        # Filter to show only releases for selected study
        filtered <- current_releases[current_releases$`Study ID` == as.numeric(input$new_study_id), ]
        filtered_releases(filtered)
        cat("🔍 Data updated: Maintaining filter for study ID", input$new_study_id, "(", nrow(filtered), "releases)\n")
      } else {
        # Show all releases when no study is selected
        filtered_releases(current_releases)
        cat("📋 Data updated: Showing all", nrow(current_releases), "releases\n")
      }
    })
    
    # Track sidebar state to detect when it closes
    sidebar_is_open <- reactiveVal(FALSE)
    
    # Track when we explicitly want to show all releases (not filtered)
    should_show_all_releases <- reactiveVal(TRUE)
    
    # Toggle add release sidebar
    observeEvent(input$toggle_add_form, {
      current_state <- sidebar_is_open()
      sidebar_toggle(id = "add_release_sidebar")
      
      if (!current_state) {
        # Sidebar is opening
        sidebar_is_open(TRUE)
        
        # Update study choices when opening with default "Select a study" option
        current_studies <- isolate(studies_data())
        if (nrow(current_studies) > 0) {
          choices <- c("Select a study" = "", setNames(current_studies$ID, current_studies$`Study Label`))
          updateSelectInput(session, "new_study_id", choices = choices, selected = "")
          cat("✅ Sidebar opening: Updated study dropdown with", nrow(current_studies), "studies\n")
        } else {
          updateSelectInput(session, "new_study_id", choices = list("No studies available" = ""), selected = "")
          cat("⚠️ No studies available for dropdown\n")
        }
        
        # Clear form when opening
        updateTextInput(session, "new_release_label", value = "")
        iv_new$disable()
      } else {
        # Sidebar is closing via toggle button
        sidebar_is_open(FALSE)
        reset_filter_and_form()
      }
    })
    
    # Function to reset filter and form (called from multiple places)
    reset_filter_and_form <- function() {
      # Reset dropdown to "Select a study" option
      current_studies <- isolate(studies_data())
      if (nrow(current_studies) > 0) {
        choices <- c("Select a study" = "", setNames(current_studies$ID, current_studies$`Study Label`))
        updateSelectInput(session, "new_study_id", choices = choices, selected = "")
      } else {
        updateSelectInput(session, "new_study_id", choices = list("No studies available" = ""), selected = "")
      }
      
      # Set flag to show all releases and update filter
      should_show_all_releases(TRUE)
      filtered_releases(releases_data())
      cat("🔄 Reset filter: Show all", nrow(releases_data()), "releases\n")
    }
    
    # Cancel new release
    observeEvent(input$cancel_new_release, {
      updateTextInput(session, "new_release_label", value = "")
      iv_new$disable()
      sidebar_toggle(id = "add_release_sidebar")
      sidebar_is_open(FALSE)
      
      # Reset filter and form
      reset_filter_and_form()
      cat("🗞️ Cancel button clicked\n")
    })
    
    # Save new release
    observeEvent(input$save_new_release, {
      # Enable validation and check form
      iv_new$enable()
      if (!iv_new$is_valid()) {
        return()
      }
      
      study_id <- as.numeric(input$new_study_id)
      release_label <- trimws(input$new_release_label)
      
      release_data <- list(
        study_id = study_id,
        database_release_label = release_label
      )
      
      result <- create_database_release(release_data)
      if (!is.null(result$error)) {
        showNotification(
          tagList(bs_icon("x-circle"), "Error creating database release:", result$error), 
          type = "error"
        )
      } else {
        showNotification(
          tagList(bs_icon("check"), "Database release created successfully"), 
          type = "message"
        )
        updateTextInput(session, "new_release_label", value = "")
        iv_new$disable()
        sidebar_toggle(id = "add_release_sidebar")
        sidebar_is_open(FALSE)
        
        # Reset filter first to ensure clean state
        reset_filter_and_form()
        cat("✅ Release created: Reset filter to show all releases\n")
        
        # Data will be updated via WebSocket events or fallback to HTTP
        load_releases_data()
      }
    })
    
    # Edit release handler
    observeEvent(input$edit_release_id, {
      release_id <- input$edit_release_id
      if (is.null(release_id)) return()
      
      # Get release data
      result <- get_database_release(release_id)
      if (!is.null(result$error)) {
        showNotification(
          tagList(bs_icon("x-circle"), "Error loading database release:", result$error), 
          type = "error"
        )
        return()
      }
      
      is_editing(TRUE)
      editing_release_id(release_id)
      
      # Get current studies for dropdown
      current_studies <- isolate(studies_data())
      study_choices <- if (nrow(current_studies) > 0) {
        setNames(current_studies$ID, current_studies$`Study Label`)
      } else {
        list("No studies available" = "")
      }
      
      showModal(modalDialog(
        title = tagList(bs_icon("pencil"), "Edit Database Release"),
        size = "m",
        easyClose = FALSE,
        
        div(
          class = "mb-3",
          tags$label("Study", class = "form-label fw-bold"),
          selectInput(
            ns("edit_study_id"),
            NULL,
            choices = study_choices,
            selected = result$study_id,
            width = "100%"
          )
        ),
        
        div(
          class = "mb-3",
          tags$label("Database Release Label", class = "form-label fw-bold"),
          textInput(
            ns("edit_release_label"), 
            NULL,
            value = result$database_release_label, 
            placeholder = "Enter database release label",
            width = "100%"
          ),
          tags$small(
            class = "form-text text-muted",
            "Database release labels must be unique within each study"
          )
        ),
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          actionButton(
            ns("cancel_edit"), 
            tagList(bs_icon("x"), "Cancel"),
            class = "btn btn-secondary"
          ),
          actionButton(
            ns("save_edit"), 
            tagList(bs_icon("check"), "Update Release"),
            class = "btn btn-warning"
          )
        )
      ))
    })
    
    # Cancel edit
    observeEvent(input$cancel_edit, {
      is_editing(FALSE)
      editing_release_id(NULL)
      iv_edit$disable()
      removeModal()
    })
    
    # Save edit
    observeEvent(input$save_edit, {
      # Enable validation and check form
      iv_edit$enable()
      if (!iv_edit$is_valid()) {
        return()
      }
      
      current_id <- editing_release_id()
      study_id <- as.numeric(input$edit_study_id)
      release_label <- trimws(input$edit_release_label)
      
      release_data <- list(
        study_id = study_id,
        database_release_label = release_label
      )
      
      result <- update_database_release(current_id, release_data)
      if (!is.null(result$error)) {
        # Parse error message for duplicate constraint violations
        error_msg <- result$error
        if (grepl("duplicate|unique|already exists", error_msg, ignore.case = TRUE)) {
          showNotification(
            tagList(bs_icon("exclamation-triangle"), "Database release label already exists for this study. Please choose a different label."), 
            type = "error"
          )
        } else {
          showNotification(
            tagList(bs_icon("x-circle"), "Error updating database release:", error_msg), 
            type = "error"
          )
        }
      } else {
        showNotification(
          tagList(bs_icon("check"), "Database release updated successfully"), 
          type = "message"
        )
        is_editing(FALSE)
        editing_release_id(NULL)
        iv_edit$disable()
        removeModal()
        # Data will be updated via WebSocket events or fallback to HTTP
        load_releases_data()
      }
    })
    
    # Delete release handler
    observeEvent(input$delete_release_id, {
      release_id <- input$delete_release_id
      if (is.null(release_id)) return()
      
      # Find release info for confirmation
      all_releases <- releases_data()
      release_row <- all_releases[all_releases$ID == release_id, ]
      if (nrow(release_row) == 0) return()
      
      release_label <- release_row$`Release Label`
      study_label <- release_row$`Study Label`
      
      # Check for associated reporting efforts before allowing deletion
      efforts_result <- get_reporting_efforts()
      if (!is.null(efforts_result$error)) {
        showNotification(
          tagList(bs_icon("x-circle"), "Error checking reporting efforts:", efforts_result$error), 
          type = "error"
        )
        return()
      }
      
      # Filter efforts for this database release
      release_efforts <- if (length(efforts_result) > 0) {
        efforts_for_release <- sapply(efforts_result, function(x) x$database_release_id == release_id)
        efforts_result[efforts_for_release]
      } else {
        list()
      }
      
      if (length(release_efforts) > 0) {
        # Has associated reporting efforts - show cannot delete modal
        effort_labels <- sapply(release_efforts, function(x) x$database_release_label)
        
        showModal(modalDialog(
          title = tagList(bs_icon("exclamation-triangle"), "Cannot Delete Database Release"),
          size = "m",
          
          div(
            class = "alert alert-warning",
            tagList(
              tags$strong("Database release has associated reporting efforts!"), 
              tags$br(),
              "This database release cannot be deleted because it has ", length(release_efforts), " associated reporting effort(s)."
            )
          ),
          
          tags$p(
            "The database release ", tags$strong(release_label), " from study ", tags$strong(study_label), " has the following reporting efforts:"
          ),
          
          tags$ul(
            lapply(effort_labels, function(label) {
              tags$li(tags$code(label))
            })
          ),
          
          tags$p(
            class = "text-muted",
            "Please delete all associated reporting efforts first, then try deleting the database release again."
          ),
          
          footer = div(
            class = "d-flex justify-content-end",
            actionButton(
              ns("close_cannot_delete"),
              tagList(bs_icon("x"), "Close"),
              class = "btn btn-secondary"
            )
          )
        ))
        return()
      }
      
      # No associated reporting efforts - proceed with deletion confirmation
      showModal(modalDialog(
        title = tagList(bs_icon("exclamation-triangle"), "Confirm Deletion"),
        size = "m",
        
        div(
          class = "alert alert-danger",
          tagList(
            tags$strong("Warning: "), 
            "This action cannot be undone."
          )
        ),
        
        tags$p(
          "Are you sure you want to delete the database release: ",
          tags$strong(release_label), " from study ",
          tags$strong(study_label), "?"
        ),
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          actionButton(
            ns("cancel_delete"),
            tagList(bs_icon("x"), "Cancel"),
            class = "btn btn-outline-secondary"
          ),
          actionButton(
            ns("confirm_delete"), 
            tagList(bs_icon("trash"), "Delete Release"),
            class = "btn btn-danger",
            onclick = sprintf("Shiny.setInputValue('%s', %s)", ns("confirm_delete_id"), release_id)
          )
        )
      ))
    })
    
    # Cancel delete
    observeEvent(input$cancel_delete, {
      removeModal()
    })
    
    # Close "cannot delete" modal
    observeEvent(input$close_cannot_delete, {
      removeModal()
    })
    
    # Confirm delete
    observeEvent(input$confirm_delete, {
      release_id <- input$confirm_delete_id
      if (is.null(release_id)) return()
      
      result <- delete_database_release(release_id)
      if (!is.null(result$error)) {
        showNotification(
          tagList(bs_icon("x-circle"), "Error deleting database release:", result$error), 
          type = "error"
        )
      } else {
        showNotification(
          tagList(bs_icon("check"), "Database release deleted successfully"), 
          type = "message"
        )
        # Data will be updated via WebSocket events or fallback to HTTP
        load_releases_data()
      }
      removeModal()
    })
    
    # Status message with filtering info
    output$status_message <- renderText({
      all_releases <- releases_data()
      filtered <- filtered_releases()
      
      if (nrow(all_releases) == 0) {
        "No database releases found"
      } else if (!is.null(input$new_study_id) && input$new_study_id != "") {
        # Show filtered count
        current_studies <- studies_data()
        study_row <- current_studies[current_studies$ID == as.numeric(input$new_study_id), ]
        study_name <- if (nrow(study_row) > 0) study_row$`Study Label`[1] else "Selected Study"
        
        if (nrow(filtered) == 0) {
          paste("No releases found for", study_name)
        } else if (nrow(filtered) == 1) {
          paste("1 release for", study_name)
        } else {
          paste(nrow(filtered), "releases for", study_name)
        }
      } else {
        # Show total count
        if (nrow(all_releases) == 1) {
          "1 database release"
        } else {
          paste(nrow(all_releases), "database releases")
        }
      }
    })
    
    # Last updated display
    output$last_updated_display <- renderText({
      paste("Updated:", format(last_update(), "%H:%M:%S"))
    })
    
    # Custom message handler for tab refresh
    observeEvent(input$refresh_database_releases, {
      cat("🔄 Refreshing database releases data due to tab change...\n")
      load_studies_http() # Refresh studies for dropdown
      load_releases_data() # Refresh releases data
    })
  })
}