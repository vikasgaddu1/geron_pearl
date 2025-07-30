# Database Releases Server Module - CRUD operations with WebSocket support

database_releases_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Reactive values
    releases_data <- reactiveVal(data.frame())
    studies_data <- reactiveVal(data.frame())
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
        output$status_message <- renderText("❌ Error loading database releases")
        releases_data(data.frame())
      } else {
        # Get current studies data safely
        current_studies <- isolate(studies_data())
        releases_df <- convert_releases_to_df(releases_result, current_studies)
        releases_data(releases_df)
        last_update(Sys.time())
        cat("✅ Database releases loaded successfully:", nrow(releases_df), "releases\n")
        output$status_message <- renderText(paste("✅", nrow(releases_df), "database releases loaded"))
      }
    }
    
    # Load data on module initialization
    load_studies_http()
    load_releases_data()
    
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
      df <- releases_data()
      if (nrow(df) == 0) {
        return(data.frame(Message = "No database releases found"))
      }
      
      # Remove Actions column for now (following studies pattern)
      df$Actions <- NULL
      
      df
    }, options = list(
      pageLength = 10,
      searching = TRUE,
      lengthChange = TRUE,
      info = TRUE,
      columnDefs = list(
        list(targets = 0, visible = FALSE),  # Hide ID column
        list(targets = 1, visible = FALSE)   # Hide Study ID column  
      ),
      dom = 'frtip',
      language = list(
        emptyTable = "No database releases available",
        zeroRecords = "No database releases match your search"
      )
    ), escape = FALSE, server = TRUE)
    
    # Toggle add release sidebar
    observeEvent(input$toggle_add_form, {
      sidebar_toggle(id = "add_release_sidebar")
      
      # Update study choices when opening
      current_studies <- isolate(studies_data())
      if (nrow(current_studies) > 0) {
        choices <- setNames(current_studies$ID, current_studies$`Study Label`)
        updateSelectInput(session, "new_study_id", choices = choices, selected = NULL)
      } else {
        updateSelectInput(session, "new_study_id", choices = list("No studies available" = ""), selected = "")
      }
      
      # Clear form when opening
      updateTextInput(session, "new_release_label", value = "")
      iv_new$disable()
    })
    
    # Cancel new release
    observeEvent(input$cancel_new_release, {
      updateTextInput(session, "new_release_label", value = "")
      updateSelectInput(session, "new_study_id", selected = NULL)
      iv_new$disable()
      sidebar_toggle(id = "add_release_sidebar")
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
        output$status_message <- renderText(paste("❌ Error creating database release:", result$error))
      } else {
        output$status_message <- renderText("✅ Database release created successfully")
        updateTextInput(session, "new_release_label", value = "")
        updateSelectInput(session, "new_study_id", selected = NULL)
        iv_new$disable()
        sidebar_toggle(id = "add_release_sidebar")
        # Data will be updated via WebSocket events or fallback to HTTP
        load_releases_data()
      }
    })
    
    # Note: Edit and delete functionality to be implemented later following studies pattern
    
    # Last updated display
    output$last_updated_display <- renderText({
      paste("Updated:", format(last_update(), "%H:%M:%S"))
    })
  })
}