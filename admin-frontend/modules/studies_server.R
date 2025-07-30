# Studies Server Module - Modern bslib version with JavaScript WebSocket support

studies_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Reactive values
    studies_data <- reactiveVal(data.frame())
    last_update <- reactiveVal(Sys.time())
    is_editing <- reactiveVal(FALSE)
    editing_study_id <- reactiveVal(NULL)
    websocket_status <- reactiveVal("Initializing")
    
    # Convert API data to data frame
    convert_studies_to_df <- function(studies_list) {
      if (length(studies_list) > 0) {
        df <- data.frame(
          ID = sapply(studies_list, function(x) x$id),
          `Study Label` = sapply(studies_list, function(x) x$study_label),
          Actions = sapply(studies_list, function(x) x$id), # Will be replaced with buttons
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(df)
      } else {
        return(data.frame(
          ID = character(0),
          `Study Label` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        ))
      }
    }
    
    # Handle WebSocket status updates from JavaScript
    observeEvent(input$websocket_status, {
      status <- input$websocket_status
      websocket_status(status)
      cat("🔄 WebSocket status update:", status, "\n")
    })
    
    # Handle WebSocket events from JavaScript
    observeEvent(input$websocket_event, {
      event <- input$websocket_event
      cat("📥 WebSocket event observer triggered. Event:", if(is.null(event)) "NULL" else event$type, "\n")
      if (is.null(event)) return()
      
      cat("📊 Processing WebSocket event:", event$type, "with data length:", length(event$data), "\n")
      
      switch(event$type,
        "studies_update" = {
          # Full studies data update
          cat("🔄 Converting WebSocket data to dataframe...\n")
          tryCatch({
            df <- convert_studies_to_df(event$data)
            cat("✅ Conversion successful, rows:", nrow(df), "\n")
            studies_data(df)
            last_update(Sys.time())
            cat("📊 Studies data updated in reactive value\n")
          }, error = function(e) {
            cat("❌ Error converting WebSocket data:", e$message, "\n")
            cat("📋 Raw event data structure:\n")
            str(event$data)
          })
        },
        "study_created" = {
          # Request fresh data after creation
          load_studies_http()
        },
        "study_updated" = {
          # Request fresh data after update
          load_studies_http()
        },
        "study_deleted" = {
          # Request fresh data after deletion
          load_studies_http()
        }
      )
    })
    
    # Handle WebSocket notifications from JavaScript
    observeEvent(input$websocket_notification, {
      notification <- input$websocket_notification
      if (is.null(notification)) return()
      
      # Convert JavaScript notification type to Shiny type
      shiny_type <- switch(notification$type,
        "success" = "message",
        "info" = "message",
        "warning" = "warning",
        "error" = "error",
        "message"
      )
      
      showNotification(
        notification$message,
        type = shiny_type,
        duration = 4
      )
    })
    
    # Initialize with HTTP data load
    load_studies_http <- function() {
      result <- get_studies()
      if ("error" %in% names(result)) {
        showNotification(paste("Error loading studies:", result$error), type = "error")
        studies_data(data.frame())
      } else {
        df <- convert_studies_to_df(result)
        studies_data(df)
        last_update(Sys.time())
      }
    }
    
    # Initial data load
    load_studies_http()
    
    # Render studies table with built-in search and action buttons
    output$studies_table <- DT::renderDataTable({
      studies <- studies_data()
      
      if (nrow(studies) == 0) {
        # Return empty table with proper structure
        empty_df <- data.frame(
          ID = character(0),
          `Study Label` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(DT::datatable(
          empty_df,
          options = list(
            dom = 'ft',
            pageLength = 10,
            language = list(emptyTable = "No studies found. Click 'Add Study' to create your first study.")
          ),
          rownames = FALSE,
          escape = FALSE
        ))
      }
      
      # Add action buttons to the Actions column
      studies$Actions <- sapply(studies$ID, function(id) {
        as.character(div(
          class = "btn-group btn-group-sm",
          actionButton(
            ns(paste0("edit_", id)),
            tagList(bs_icon("pencil"), "Edit"),
            class = "btn btn-warning btn-sm",
            onclick = sprintf("Shiny.setInputValue('%s', %s)", ns("edit_study_id"), id)
          ),
          actionButton(
            ns(paste0("delete_", id)),
            tagList(bs_icon("trash"), "Delete"),
            class = "btn btn-danger btn-sm",
            onclick = sprintf("Shiny.setInputValue('%s', %s)", ns("delete_study_id"), id)
          )
        ))
      })
      
      # Hide ID column but keep for reference
      display_df <- studies[, c("Study Label", "Actions"), drop = FALSE]
      
      DT::datatable(
        display_df,
        options = list(
          dom = 'ft', # Only show filter and table (f=filter, t=table)
          pageLength = 10,
          autoWidth = FALSE,
          columnDefs = list(
            list(targets = 0, width = "70%"), # Study Label column
            list(targets = 1, width = "30%", orderable = FALSE) # Actions column
          ),
          language = list(
            search = "Search studies:",
            searchPlaceholder = "Type to filter..."
          )
        ),
        rownames = FALSE,
        escape = FALSE, # Allow HTML in Actions column
        selection = 'none'
      )
    }, server = FALSE)
    
    # Toggle add study sidebar
    observeEvent(input$toggle_add_form, {
      sidebar_toggle(id = "add_study_sidebar")
      # Clear form when opening
      updateTextInput(session, "new_study_label", value = "")
    })
    
    # Cancel new study
    observeEvent(input$cancel_new_study, {
      updateTextInput(session, "new_study_label", value = "")
      sidebar_toggle(id = "add_study_sidebar")
    })
    
    # Save new study
    observeEvent(input$save_new_study, {
      study_label <- trimws(input$new_study_label)
      
      if (nchar(study_label) == 0) {
        showNotification(
          tagList(bs_icon("exclamation-circle"), "Study label is required"), 
          type = "error"
        )
        return()
      }
      
      # Check for duplicates locally first
      existing_studies <- studies_data()
      if (nrow(existing_studies) > 0 && study_label %in% existing_studies$`Study Label`) {
        showNotification(
          tagList(bs_icon("exclamation-triangle"), "A study with this label already exists"), 
          type = "error"
        )
        return()
      }
      
      study_data <- list(study_label = study_label)
      
      result <- create_study(study_data)
      if ("error" %in% names(result)) {
        # Parse error message for duplicate constraint violations
        error_msg <- result$error
        if (grepl("duplicate|unique|already exists", error_msg, ignore.case = TRUE)) {
          showNotification(
            tagList(bs_icon("exclamation-triangle"), "Study label already exists. Please choose a different label."), 
            type = "error"
          )
        } else {
          showNotification(
            tagList(bs_icon("x-circle"), "Error creating study:", error_msg), 
            type = "error"
          )
        }
      } else {
        showNotification(
          tagList(bs_icon("check"), "Study created successfully"), 
          type = "message"
        )
        updateTextInput(session, "new_study_label", value = "")
        sidebar_toggle(id = "add_study_sidebar")
        # Data will be updated via WebSocket events or fallback to HTTP
        load_studies_http()
      }
    })
    
    # Edit study handler
    observeEvent(input$edit_study_id, {
      study_id <- input$edit_study_id
      if (is.null(study_id)) return()
      
      # Get study data
      result <- get_study(study_id)
      if ("error" %in% names(result)) {
        showNotification(paste("Error loading study:", result$error), type = "error")
        return()
      }
      
      is_editing(TRUE)
      editing_study_id(study_id)
      
      showModal(modalDialog(
        title = tagList(bs_icon("pencil"), "Edit Study"),
        size = "m",
        easyClose = FALSE,
        
        div(
          class = "mb-3",
          tags$label("Study Label", class = "form-label fw-bold"),
          textInput(
            ns("edit_study_label"), 
            NULL,
            value = result$study_label, 
            placeholder = "Enter a unique study identifier",
            width = "100%"
          ),
          tags$small(
            class = "form-text text-muted",
            "Study labels must be unique across the system"
          )
        ),
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          actionButton(
            ns("cancel_edit"), 
            tagList(bs_icon("x"), "Cancel"),
            class = "btn btn-outline-secondary"
          ),
          actionButton(
            ns("save_edit"), 
            tagList(bs_icon("check"), "Update Study"),
            class = "btn btn-warning"
          )
        )
      ))
    })
    
    # Cancel edit
    observeEvent(input$cancel_edit, {
      is_editing(FALSE)
      editing_study_id(NULL)
      removeModal()
    })
    
    # Save edit
    observeEvent(input$save_edit, {
      study_label <- trimws(input$edit_study_label)
      
      if (nchar(study_label) == 0) {
        showNotification(
          tagList(bs_icon("exclamation-circle"), "Study label is required"), 
          type = "error"
        )
        return()
      }
      
      # Check for duplicates (excluding current study)
      existing_studies <- studies_data()
      current_id <- editing_study_id()
      if (nrow(existing_studies) > 0) {
        other_studies <- existing_studies[existing_studies$ID != current_id, ]
        if (nrow(other_studies) > 0 && study_label %in% other_studies$`Study Label`) {
          showNotification(
            tagList(bs_icon("exclamation-triangle"), "A study with this label already exists"), 
            type = "error"
          )
          return()
        }
      }
      
      study_data <- list(study_label = study_label)
      
      result <- update_study(current_id, study_data)
      if ("error" %in% names(result)) {
        # Parse error message for duplicate constraint violations
        error_msg <- result$error
        if (grepl("duplicate|unique|already exists", error_msg, ignore.case = TRUE)) {
          showNotification(
            tagList(bs_icon("exclamation-triangle"), "Study label already exists. Please choose a different label."), 
            type = "error"
          )
        } else {
          showNotification(
            tagList(bs_icon("x-circle"), "Error updating study:", error_msg), 
            type = "error"
          )
        }
      } else {
        showNotification(
          tagList(bs_icon("check"), "Study updated successfully"), 
          type = "message"
        )
        is_editing(FALSE)
        editing_study_id(NULL)
        removeModal()
        # Data will be updated via WebSocket events or fallback to HTTP
        load_studies_http()
      }
    })
    
    # Delete study handler
    observeEvent(input$delete_study_id, {
      study_id <- input$delete_study_id
      if (is.null(study_id)) return()
      
      # Find study label for confirmation
      all_studies <- studies_data()
      study_row <- all_studies[all_studies$ID == study_id, ]
      if (nrow(study_row) == 0) return()
      
      study_label <- study_row$`Study Label`
      
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
          "Are you sure you want to delete the study: ",
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
            tagList(bs_icon("trash"), "Delete Study"),
            class = "btn btn-danger",
            onclick = sprintf("Shiny.setInputValue('%s', %s)", ns("confirm_delete_id"), study_id)
          )
        )
      ))
    })
    
    # Cancel delete
    observeEvent(input$cancel_delete, {
      removeModal()
    })
    
    # Confirm delete
    observeEvent(input$confirm_delete, {
      study_id <- input$confirm_delete_id
      if (is.null(study_id)) return()
      
      result <- delete_study(study_id)
      if ("error" %in% names(result)) {
        showNotification(
          tagList(bs_icon("x-circle"), "Error deleting study:", result$error), 
          type = "error"
        )
      } else {
        showNotification(
          tagList(bs_icon("check"), "Study deleted successfully"), 
          type = "message"
        )
        # Data will be updated via WebSocket events or fallback to HTTP
        load_studies_http()
      }
      removeModal()
    })
    
    # Refresh button
    observeEvent(input$refresh, {
      # Try WebSocket refresh first, fallback to HTTP
      session$sendCustomMessage(
        type = "websocket_refresh",
        message = list(action = "refresh")
      )
      
      # Always do HTTP refresh as backup
      load_studies_http()
      
      showNotification(
        tagList(bs_icon("arrow-clockwise"), "Data refreshed"),
        type = "message",
        duration = 3
      )
    })
    
    # Status message
    output$status_message <- renderText({
      count <- nrow(studies_data())
      
      if (count == 0) {
        "No studies found"
      } else if (count == 1) {
        "1 study"
      } else {
        paste(count, "studies")
      }
    })
    
    # Last updated display
    output$last_updated_display <- renderText({
      paste("Updated:", format(last_update(), "%H:%M:%S"))
    })
    
    # WebSocket status display
    output$websocket_status_display <- renderText({
      status <- websocket_status()
      icon <- switch(status,
        "Connected" = "🟢",
        "Connecting" = "🟡", 
        "Disconnected" = "🔴",
        "🔴"
      )
      paste(icon, "WebSocket:", status)
    })
  })
}