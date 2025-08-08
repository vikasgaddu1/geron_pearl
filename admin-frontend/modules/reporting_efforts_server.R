# Reporting Efforts Server Module - CRUD operations with WebSocket support

reporting_efforts_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Reactive values
    efforts_data <- reactiveVal(data.frame())
    studies_data <- reactiveVal(data.frame())
    database_releases_data <- reactiveVal(data.frame())
    filtered_efforts <- reactiveVal(data.frame())
    last_update <- reactiveVal(Sys.time())
    is_editing <- reactiveVal(FALSE)
    editing_effort_id <- reactiveVal(NULL)
    should_show_all_efforts <- reactiveVal(TRUE)
    
    # Set up validation for new effort form
    iv_new <- InputValidator$new()
    iv_new$add_rule("new_study_id", sv_required())
    iv_new$add_rule("new_database_release_id", sv_required())
    iv_new$add_rule("new_effort_label", sv_required())
    iv_new$add_rule("new_effort_label", function(value) {
      current_efforts <- efforts_data()
      current_db_release_id <- input$new_database_release_id
      if (nrow(current_efforts) > 0 && !is.null(current_db_release_id) && current_db_release_id != "") {
        release_efforts <- current_efforts[current_efforts$`Database Release ID` == as.numeric(current_db_release_id), ]
        if (nrow(release_efforts) > 0 && trimws(value) %in% release_efforts$`Effort Label`) {
          "A reporting effort with this label already exists for this database release"
        }
      }
    })
    
    # Set up validation for edit effort form
    iv_edit <- InputValidator$new()
    iv_edit$add_rule("edit_study_id", sv_required())
    iv_edit$add_rule("edit_database_release_id", sv_required())
    iv_edit$add_rule("edit_effort_label", sv_required())
    iv_edit$add_rule("edit_effort_label", function(value) {
      current_efforts <- efforts_data()
      current_effort_id <- editing_effort_id()
      current_db_release_id <- input$edit_database_release_id
      if (nrow(current_efforts) > 0 && !is.null(current_effort_id) && !is.null(current_db_release_id)) {
        # Check for duplicates within the same database release, excluding current effort
        release_efforts <- current_efforts[current_efforts$`Database Release ID` == as.numeric(current_db_release_id) & current_efforts$ID != current_effort_id, ]
        if (nrow(release_efforts) > 0 && trimws(value) %in% release_efforts$`Effort Label`) {
          "A reporting effort with this label already exists for this database release"
        }
      }
    })
    
    # Convert API data to data frame
    convert_efforts_to_df <- function(efforts_list, current_studies = NULL, current_releases = NULL) {
      if (length(efforts_list) > 0) {
        df <- data.frame(
          ID = sapply(efforts_list, function(x) x$id),
          `Study ID` = sapply(efforts_list, function(x) x$study_id),
          `Study` = sapply(efforts_list, function(x) {
            study_id <- x$study_id
            if (!is.null(current_studies) && nrow(current_studies) > 0) {
              study_row <- current_studies[current_studies$ID == study_id, ]
              if (nrow(study_row) > 0) {
                return(study_row$`Study`[1])
              }
            }
            return(paste("Study", study_id))
          }),
          `Database Release ID` = sapply(efforts_list, function(x) x$database_release_id),
          `Database Release` = sapply(efforts_list, function(x) {
            db_release_id <- x$database_release_id
            if (!is.null(current_releases) && nrow(current_releases) > 0) {
              release_row <- current_releases[current_releases$ID == db_release_id, ]
              if (nrow(release_row) > 0) {
                return(release_row$`Database Release`[1])
              }
            }
            return(paste("Release", db_release_id))
          }),
          `Reporting Effort` = sapply(efforts_list, function(x) x$database_release_label),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(df)
      } else {
        return(data.frame(
          ID = integer(0),
          `Study ID` = integer(0),
           `Study` = character(0),
          `Database Release ID` = integer(0),
           `Database Release` = character(0),
           `Reporting Effort` = character(0),
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
          `Study` = sapply(studies_result, function(x) x$study_label),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        studies_data(studies_df)
        cat("✅ Studies loaded for reference:", nrow(studies_df), "studies\n")
      }
    }
    
    # Load database releases data
    load_database_releases_http <- function() {
      releases_result <- get_database_releases()
      if (!is.null(releases_result$error)) {
        cat("❌ Error loading database releases:", releases_result$error, "\n")
        database_releases_data(data.frame())
      } else {
        releases_df <- data.frame(
          ID = sapply(releases_result, function(x) x$id),
          `Study ID` = sapply(releases_result, function(x) x$study_id),
          `Database Release` = sapply(releases_result, function(x) x$database_release_label),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        database_releases_data(releases_df)
        cat("✅ Database releases loaded for reference:", nrow(releases_df), "releases\n")
      }
    }
    
    # Load reporting efforts data
    load_efforts_http <- function() {
      efforts_result <- get_reporting_efforts()
      if (!is.null(efforts_result$error)) {
        cat("❌ Error loading reporting efforts:", efforts_result$error, "\n")
        output$status_message <- renderText("❌ Error loading reporting efforts")
      } else {
         efforts_df <- convert_efforts_to_df(efforts_result, studies_data(), database_releases_data())
        efforts_data(efforts_df)
        last_update(Sys.time())
        cat("✅ Reporting efforts loaded:", nrow(efforts_df), "efforts\n")
        output$status_message <- renderText(paste("✅ Loaded", nrow(efforts_df), "reporting efforts"))
      }
    }
    
    # Update dropdown choices for studies
    update_study_choices <- function() {
      current_studies <- studies_data()
      if (nrow(current_studies) > 0) {
        choices <- setNames(current_studies$ID, current_studies$`Study`)
        
        # Update form dropdown
        updateSelectInput(session, "new_study_id", 
                         choices = c("Select a study..." = "", choices))
      }
    }
    
    # Update dropdown choices for database releases based on selected study
    update_database_release_choices <- function(selected_study_id = NULL) {
      current_releases <- database_releases_data()
      
      if (nrow(current_releases) > 0) {
        # Filter releases by study if specified
        if (!is.null(selected_study_id) && selected_study_id != "") {
          filtered_releases <- current_releases[current_releases$`Study ID` == as.numeric(selected_study_id), ]
        } else {
          filtered_releases <- current_releases
        }
        
        if (nrow(filtered_releases) > 0) {
          choices <- setNames(filtered_releases$ID, 
                             filtered_releases$`Database Release`)
          
          # Update form dropdown
          updateSelectInput(session, "new_database_release_id", 
                           choices = c("Select a database release..." = "", choices))
        } else {
          # No releases for selected study
          updateSelectInput(session, "new_database_release_id", 
                           choices = c("No releases available for this study" = ""))
        }
      }
    }
    
    
    # Initialize on module load
    observe({
      cat("🚀 Initializing Reporting Efforts module...\n")
      load_studies_http()
      load_database_releases_http()
      load_efforts_http()
    })
    
    # Handle WebSocket events from JavaScript
    observeEvent(input$websocket_event, {
      event <- input$websocket_event
      cat("📥 WebSocket event observer triggered. Event:", if(is.null(event)) "NULL" else event$type, "\n")
      if (is.null(event)) return()
      
      cat("📊 Processing WebSocket event:", event$type, "with data length:", length(event$data), "\n")
      
      if (event$type == "reporting_effort_created") {
        cat("➕ Reporting effort created via WebSocket, refreshing data\n")
        load_efforts_http()
      } else if (event$type == "reporting_effort_updated") {
        cat("✏️ Reporting effort updated via WebSocket, refreshing data\n")
        load_efforts_http()
      } else if (event$type == "reporting_effort_deleted") {
        cat("🗑️ Reporting effort deleted via WebSocket, refreshing data\n")
        load_efforts_http()
      } else if (event$type == "studies_update") {
        # Update studies data for dropdown
        cat("📚 Studies updated via WebSocket, updating reference data\n")
        studies_df <- convert_studies_to_df_simple(event$data)
        studies_data(studies_df)
        # Refresh efforts to update study labels
        load_efforts_http()
      } else if (event$type == "database_release_created" || event$type == "database_release_updated" || event$type == "database_release_deleted") {
        # Update database releases data for dropdown
        cat("🗃️ Database releases updated via WebSocket, updating reference data\n")
        load_database_releases_http()
        # Refresh efforts to update release labels  
        load_efforts_http()
      }
    })
    
    # Helper function for studies data
    convert_studies_to_df_simple <- function(studies_list) {
      if (length(studies_list) > 0) {
         data.frame(
          ID = sapply(studies_list, function(x) x$id),
          `Study` = sapply(studies_list, function(x) x$study_label),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
      } else {
         data.frame(
          ID = numeric(0),
          `Study` = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
      }
    }
    
    # Update choices when data changes
    observe({
      update_study_choices()
    }) |> bindEvent(studies_data())
    
    observe({
      update_database_release_choices()
    }) |> bindEvent(database_releases_data())
    
    # Update database release choices when study selection changes
    observe({
      req(input$new_study_id)
      update_database_release_choices(input$new_study_id)
    }) |> bindEvent(input$new_study_id)
    
    # Filter efforts based on selected study in add form dropdown
    observe({
      current_efforts <- efforts_data()
      if (!is.null(input$new_study_id) && input$new_study_id != "") {
        # Filter to show only efforts for selected study
        should_show_all_efforts(FALSE)
        filtered <- current_efforts[current_efforts$`Study ID` == as.numeric(input$new_study_id), ]
        filtered_efforts(filtered)
        cat("🔍 Filtering table to show", nrow(filtered), "efforts for study ID", input$new_study_id, "\n")
      } else {
        # Show all efforts when no study is selected
        should_show_all_efforts(TRUE)
        filtered_efforts(current_efforts)
        cat("📋 Showing all", nrow(current_efforts), "efforts\n")
      }
    }) |> bindEvent(input$new_study_id, ignoreInit = TRUE)
    
    # Further filter efforts based on selected database release in add form dropdown
    observe({
      current_efforts <- efforts_data()
      if (!is.null(input$new_database_release_id) && input$new_database_release_id != "") {
        # Filter to show only efforts for selected database release
        should_show_all_efforts(FALSE)
        filtered <- current_efforts[current_efforts$`Database Release ID` == as.numeric(input$new_database_release_id), ]
        filtered_efforts(filtered)
        cat("🔍 Filtering table to show", nrow(filtered), "efforts for database release ID", input$new_database_release_id, "\n")
      } else if (!is.null(input$new_study_id) && input$new_study_id != "") {
        # If database release is cleared but study is still selected, filter by study only
        filtered <- current_efforts[current_efforts$`Study ID` == as.numeric(input$new_study_id), ]
        filtered_efforts(filtered)
        cat("🔍 Filtering table to show", nrow(filtered), "efforts for study ID", input$new_study_id, "\n")
      } else {
        # Show all efforts when both dropdowns are cleared
        should_show_all_efforts(TRUE)
        filtered_efforts(current_efforts)
        cat("📋 Showing all", nrow(current_efforts), "efforts\n")
      }
    }) |> bindEvent(input$new_database_release_id, ignoreInit = TRUE)
    
    # Update filtered data when efforts data changes
    observe({
      current_efforts <- efforts_data()
      
      # Check if we should maintain "show all" state (after creation/reset)
      if (should_show_all_efforts()) {
        filtered_efforts(current_efforts)
        cat("🔄 Data updated: Maintaining show all state (", nrow(current_efforts), "efforts)\n")
      } else if (!is.null(input$new_database_release_id) && input$new_database_release_id != "") {
        # Filter to show only efforts for selected database release
        filtered <- current_efforts[current_efforts$`Database Release ID` == as.numeric(input$new_database_release_id), ]
        filtered_efforts(filtered)
        cat("🔍 Data updated: Maintaining filter for database release ID", input$new_database_release_id, "(", nrow(filtered), "efforts)\n")
      } else if (!is.null(input$new_study_id) && input$new_study_id != "") {
        # Filter to show only efforts for selected study
        filtered <- current_efforts[current_efforts$`Study ID` == as.numeric(input$new_study_id), ]
        filtered_efforts(filtered)
        cat("🔍 Data updated: Maintaining filter for study ID", input$new_study_id, "(", nrow(filtered), "efforts)\n")
      } else {
        filtered_efforts(current_efforts)
        cat("🔄 Data updated: Showing all efforts (", nrow(current_efforts), ")\n")
      }
    }) |> bindEvent(efforts_data())
    
    
    # Render data table
    output$efforts_table <- DT::renderDataTable({
      current_efforts <- filtered_efforts()
      
      if (nrow(current_efforts) == 0) {
        # Create empty dataframe with proper structure
        empty_df <- data.frame(
          `Study Label` = character(0),
          `Database Release Label` = character(0),
          `Effort Label` = character(0),
          `Actions` = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        
        DT::datatable(
          empty_df,
          filter = 'top',
          options = list(
            dom = 'frtip',
            search = list(regex = TRUE, caseInsensitive = TRUE),
            searching = TRUE,
            pageLength = 25,
            language = list(
              emptyTable = "No reporting efforts found. Click 'Add Effort' to create your first reporting effort."
            )
          ),
          rownames = FALSE,
          selection = 'none',
          escape = FALSE
        )
      } else {
        # Sort by Study ID and Effort ID
        current_efforts <- current_efforts[order(current_efforts$`Study ID`, current_efforts$ID), ]
        
        # Prepare display dataframe (exclude ID columns for display)
        display_df <- current_efforts[, c("Study", "Database Release", "Reporting Effort"), drop = FALSE]
        
        # Add Actions column with edit and delete buttons
        display_df$Actions <- sapply(current_efforts$ID, function(id) {
          as.character(div(
            class = "d-flex gap-2 justify-content-center",
            tags$button(class = "btn btn-warning btn-sm", `data-action` = "edit", `data-id` = id, title = "Edit reporting effort", bs_icon("pencil")),
            tags$button(class = "btn btn-danger btn-sm", `data-action` = "delete", `data-id` = id, title = "Delete reporting effort", bs_icon("trash"))
          ))
        })
        
        DT::datatable(
          display_df,
          filter = 'top',
          options = list(
            dom = 'frtip',
            search = list(regex = TRUE, caseInsensitive = TRUE),
            searching = TRUE,
            pageLength = 25,
            scrollX = TRUE,
            language = list(search = "", searchPlaceholder = "Search (regex supported):"),
            columnDefs = list(
              list(orderable = FALSE, searchable = FALSE, className = 'text-center dt-nowrap', width = '1%', targets = ncol(display_df) - 1),
              list(className = 'text-start', targets = 0:(ncol(display_df)-2))
            ),
            initComplete = JS(sprintf("function() { $('#%s thead tr:nth-child(2) th:last input, #%s thead tr:nth-child(2) th:last select').prop('disabled', true).attr('placeholder',''); }", ns("efforts_table"), ns("efforts_table"))),
            drawCallback = JS(sprintf("
              function(settings) {
                $('#%s button[data-action=\"edit\"]').off('click').on('click', function() {
                  var id = $(this).attr('data-id');
                  Shiny.setInputValue('%s', id, {priority: 'event'});
                });
                $('#%s button[data-action=\"delete\"]').off('click').on('click', function() {
                  var id = $(this).attr('data-id');
                  Shiny.setInputValue('%s', id, {priority: 'event'});
                });
              }
            ", ns("efforts_table"), ns("edit_effort_id"), 
               ns("efforts_table"), ns("delete_effort_id")))
          ),
          rownames = FALSE,
          escape = FALSE, # Allow HTML in Actions column
          selection = 'none'
        )
      }
    }, server = FALSE)
    
    # Refresh button
    observe({
      load_studies_http()
      load_database_releases_http()
      load_efforts_http()
    }) |> bindEvent(input$refresh_btn)
    
    # Toggle add form sidebar
    observe({
      sidebar_toggle(id = "add_effort_sidebar")
    }) |> bindEvent(input$toggle_add_form)
    
    # Function to reset filter and form (called from multiple places)
    reset_filter_and_form <- function() {
      # Reset dropdowns to default options
      current_studies <- isolate(studies_data())
      if (nrow(current_studies) > 0) {
        choices <- c("Select a study..." = "", setNames(current_studies$ID, current_studies$`Study`))
        updateSelectInput(session, "new_study_id", choices = choices, selected = "")
      } else {
        updateSelectInput(session, "new_study_id", choices = list("No studies available" = ""), selected = "")
      }
      
      updateSelectInput(session, "new_database_release_id", choices = c("Select a database release..." = ""), selected = "")
      
      # Set flag to show all efforts and update filter
      should_show_all_efforts(TRUE)
      filtered_efforts(efforts_data())
      cat("🔄 Reset filter: Show all", nrow(efforts_data()), "efforts\n")
    }
    
    # Cancel new effort
    observe({
      updateTextInput(session, "new_effort_label", value = "")
      updateSelectInput(session, "new_study_id", selected = "")
      updateSelectInput(session, "new_database_release_id", selected = "")
      sidebar_toggle(id = "add_effort_sidebar", open = FALSE)
      
      # Reset filter and form
      reset_filter_and_form()
      cat("🗞️ Cancel button clicked\n")
    }) |> bindEvent(input$cancel_new_effort)
    
    # Save new effort
    observe({
      if (iv_new$is_valid()) {
        effort_data <- list(
          study_id = as.numeric(input$new_study_id),
          database_release_id = as.numeric(input$new_database_release_id),
          database_release_label = trimws(input$new_effort_label)
        )
        
        result <- create_reporting_effort(effort_data)
        
        if (!is.null(result$error)) {
          output$status_message <- renderText(paste("❌ Error creating reporting effort:", result$error))
        } else {
          output$status_message <- renderText("✅ Reporting effort created successfully")
          
          # Clear form and close sidebar
          updateTextInput(session, "new_effort_label", value = "")
          sidebar_toggle(id = "add_effort_sidebar", open = FALSE)
          
          # Reset filter and form
          reset_filter_and_form()
          
          # Reload data
          load_efforts_http()
        }
      } else {
        iv_new$enable()
      }
    }) |> bindEvent(input$save_new_effort)
    
    # Last updated display
    output$last_updated_display <- renderText({
      update_time <- last_update()
      if (!is.null(update_time)) {
        paste("Last updated:", format(update_time, "%H:%M:%S"))
      } else {
        ""
      }
    })
    
    # Edit effort handler
    observe({
      effort_id <- input$edit_effort_id
      if (is.null(effort_id)) return()
      
      # Get effort data
      result <- get_reporting_effort(effort_id)
      if (!is.null(result$error)) {
        showNotification(
          tagList(bs_icon("x-circle"), "Error loading reporting effort:", result$error), 
          type = "error"
        )
        return()
      }
      
      is_editing(TRUE)
      editing_effort_id(effort_id)
      
      # Get current labels (read-only in edit)
      current_studies <- isolate(studies_data())
      current_releases <- isolate(database_releases_data())
      study_label <- if (nrow(current_studies) > 0) current_studies$`Study Label`[match(result$study_id, current_studies$ID)] else result$study_id
      release_label <- if (nrow(current_releases) > 0) current_releases$`Release Label`[match(result$database_release_id, current_releases$ID)] else result$database_release_id

      showModal(modalDialog(
        title = tagList(bs_icon("pencil"), "Edit Reporting Effort"),
        size = "m",
        easyClose = FALSE,
        
        div(
          class = "mb-3",
          tags$label("Study", class = "form-label fw-bold"),
          tags$input(id = ns("edit_study_label_display"), class = "form-control", value = study_label, disabled = TRUE),
          tags$input(id = ns("edit_study_id"), type = "hidden", value = result$study_id)
        ),
        
        div(
          class = "mb-3",
          tags$label("Database Release", class = "form-label fw-bold"),
          tags$input(id = ns("edit_database_release_label_display"), class = "form-control", value = release_label, disabled = TRUE),
          tags$input(id = ns("edit_database_release_id"), type = "hidden", value = result$database_release_id)
        ),
        
        div(
          class = "mb-3",
          tags$label("Reporting Effort Label", class = "form-label fw-bold"),
          textInput(
            ns("edit_effort_label"), 
            NULL,
            value = result$database_release_label, 
            placeholder = "Enter reporting effort label",
            width = "100%"
          ),
          tags$small(
            class = "form-text text-muted",
            "Reporting effort labels must be unique within each database release"
          )
        ),
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          input_task_button(
            ns("cancel_edit"), 
            tagList(bs_icon("x"), "Cancel"),
            class = "btn btn-secondary"
          ),
          input_task_button(
            ns("save_edit"), 
            tagList(bs_icon("check"), "Update Effort"),
            class = "btn btn-warning"
          )
        )
      ))
      
      # Filter database releases after modal opens
      shinyjs::delay(100, {
        current_releases <- isolate(database_releases_data())
        study_id <- result$study_id
        
        if (nrow(current_releases) > 0) {
          # Filter releases by selected study
          filtered_releases <- current_releases[current_releases$`Study ID` == study_id, ]
          
          if (nrow(filtered_releases) > 0) {
            choices <- setNames(filtered_releases$ID, 
                               filtered_releases$`Release Label`)
            updateSelectInput(session, "edit_database_release_id", 
                             choices = choices,
                             selected = result$database_release_id)
          }
        }
      })
    }) |> bindEvent(input$edit_effort_id)
    
    # Delete effort handler
    observe({
      effort_id <- input$delete_effort_id
      current_efforts <- efforts_data()
      
      if (!is.null(effort_id) && nrow(current_efforts) > 0) {
        effort_row <- current_efforts[current_efforts$ID == effort_id, ]
        if (nrow(effort_row) > 0) {
          effort_label <- effort_row$`Effort Label`[1]
          study_label <- effort_row$`Study Label`[1]
          release_label <- effort_row$`Database Release Label`[1]
          
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
              "Are you sure you want to delete the reporting effort: ",
              tags$strong(effort_label), "?"
            ),
            
            div(
              class = "alert alert-info mt-3",
              tagList(
                tags$h6("Effort Details:"),
                tags$p(tags$strong("Study: "), study_label),
                tags$p(tags$strong("Database Release: "), release_label),
                tags$p(tags$strong("Effort Label: "), effort_label)
              )
            ),
            
            footer = div(
              class = "d-flex justify-content-end gap-2",
              input_task_button(
                ns("cancel_delete"),
                tagList(bs_icon("x"), "Cancel"),
                class = "btn btn-outline-secondary"
              ),
              input_task_button(
                ns("confirm_delete"), 
                tagList(bs_icon("trash"), "Delete Effort"),
                class = "btn btn-danger",
                onclick = sprintf("Shiny.setInputValue('%s', %s)", ns("confirm_delete_id"), effort_id)
              )
            )
          ))
        }
      }
    }) |> bindEvent(input$delete_effort_id)
    
    # Cancel delete
    observe({
      removeModal()
    }) |> bindEvent(input$cancel_delete)
    
    # Cancel edit
    observe({
      is_editing(FALSE)
      editing_effort_id(NULL)
      iv_edit$disable()
      removeModal()
    }) |> bindEvent(input$cancel_edit)
    
    # Save edit
    observe({
      # Enable validation and check form
      iv_edit$enable()
      if (!iv_edit$is_valid()) {
        return()
      }
      
      current_id <- editing_effort_id()
      study_id <- as.numeric(input$edit_study_id)
      database_release_id <- as.numeric(input$edit_database_release_id)
      effort_label <- trimws(input$edit_effort_label)
      
      effort_data <- list(
        study_id = study_id,
        database_release_id = database_release_id,
        database_release_label = effort_label
      )
      
      result <- update_reporting_effort(current_id, effort_data)
      if (!is.null(result$error)) {
        # Parse error message for duplicate constraint violations
        error_msg <- result$error
        if (grepl("duplicate|unique|already exists", error_msg, ignore.case = TRUE)) {
          showNotification(
            tagList(bs_icon("exclamation-triangle"), "Reporting effort label already exists for this database release. Please choose a different label."), 
            type = "error"
          )
        } else {
          showNotification(
            tagList(bs_icon("x-circle"), "Error updating reporting effort:", error_msg), 
            type = "error"
          )
        }
      } else {
        showNotification(
          tagList(bs_icon("check"), "Reporting effort updated successfully"), 
          type = "message"
        )
        is_editing(FALSE)
        editing_effort_id(NULL)
        iv_edit$disable()
        removeModal()
        # Reload data
        load_efforts_http()
      }
    }) |> bindEvent(input$save_edit)
    
    # Update database release choices when study selection changes in edit form
    observe({
      if (!is_editing()) return()
      req(input$edit_study_id)
      
      current_releases <- database_releases_data()
      study_id <- input$edit_study_id
      
      if (nrow(current_releases) > 0 && study_id != "") {
        # Filter releases by selected study
        filtered_releases <- current_releases[current_releases$`Study ID` == as.numeric(study_id), ]
        
        if (nrow(filtered_releases) > 0) {
          choices <- setNames(filtered_releases$ID, 
                             filtered_releases$`Release Label`)
          updateSelectInput(session, "edit_database_release_id", 
                           choices = c("Select a database release..." = "", choices))
        } else {
          updateSelectInput(session, "edit_database_release_id", 
                           choices = c("No releases available for this study" = ""))
        }
      }
    }) |> bindEvent(input$edit_study_id)
    
    # Confirm delete
    observe({
      effort_id <- input$confirm_delete_id
      if (is.null(effort_id)) return()
      
      result <- delete_reporting_effort(effort_id)
      if (!is.null(result$error)) {
        showNotification(
          tagList(bs_icon("x-circle"), "Error deleting reporting effort:", result$error), 
          type = "error"
        )
      } else {
        showNotification(
          tagList(bs_icon("check"), "Reporting effort deleted successfully"), 
          type = "message"
        )
        # Reload data
        load_efforts_http()
      }
      removeModal()
    }) |> bindEvent(input$confirm_delete)
    
    # Custom message handler for tab refresh
    observeEvent(input$refresh_reporting_efforts, {
      cat("🔄 Refreshing reporting efforts data due to tab change...\n")
      load_studies_http() # Refresh studies for dropdown
      load_database_releases_http() # Refresh database releases for dropdown
      load_efforts_http() # Refresh efforts data
    })
  })
}