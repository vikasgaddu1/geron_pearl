# TNFP Server Module - Text Elements Management

tnfp_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Reactive values for Text Elements
    text_elements_data <- reactiveVal(data.frame())
    last_text_elements_update <- reactiveVal(Sys.time())
    editing_text_element_id <- reactiveVal(NULL)
    editing_text_element_type <- reactiveVal(NULL)
    
    # Helper function to normalize text for duplicate checking (ignore spaces and case)
    normalize_text <- function(text) {
      if (is.null(text) || text == "") return("")
      return(toupper(gsub("\\s+", "", trimws(text))))
    }
    
    # Helper function to check for duplicates client-side
    check_duplicate_content <- function(new_content, new_type, exclude_id = NULL) {
      current_data <- text_elements_data()
      if (nrow(current_data) == 0) return(FALSE)
      
      # Get raw data to access original labels
      raw_result <- get_text_elements()
      if (is.null(raw_result) || !is.null(raw_result$error) || length(raw_result) == 0) {
        return(FALSE)
      }
      
      normalized_new <- normalize_text(new_content)
      if (normalized_new == "") return(FALSE)
      
      for (element in raw_result) {
        # Skip if this is the element being edited
        if (!is.null(exclude_id) && element$id == exclude_id) next
        
        # Check if same type and normalized content matches
        if (element$type == new_type && normalize_text(element$label) == normalized_new) {
          return(list(exists = TRUE, existing_label = element$label))
        }
      }
      return(FALSE)
    }
    
    # Set up validation for new text element form
    iv_text_element_new <- InputValidator$new()
    iv_text_element_new$add_rule("new_text_element_type", sv_required())
    iv_text_element_new$add_rule("new_text_element_label", sv_required())
    iv_text_element_new$add_rule("new_text_element_label", function(value) {
      if (nchar(trimws(value)) < 3) {
        "Content must be at least 3 characters long"
      }
    })
    iv_text_element_new$add_rule("new_text_element_label", function(value) {
      if (!is.null(input$new_text_element_type)) {
        duplicate_check <- check_duplicate_content(value, input$new_text_element_type)
        if (is.list(duplicate_check) && duplicate_check$exists) {
          paste0("Similar content already exists: '", duplicate_check$existing_label, "' (ignoring spaces and case)")
        }
      }
    })
    
    # Set up validation for edit text element form
    iv_text_element_edit <- InputValidator$new()
    # Don't validate the type field since it's disabled/hidden and can't be changed
    iv_text_element_edit$add_rule("edit_text_element_label", sv_required())
    iv_text_element_edit$add_rule("edit_text_element_label", function(value) {
      if (nchar(trimws(value)) < 3) {
        "Content must be at least 3 characters long"
      }
    })
    iv_text_element_edit$add_rule("edit_text_element_label", function(value) {
      current_id <- editing_text_element_id()
      current_type <- editing_text_element_type()
      if (!is.null(current_type) && !is.null(current_id)) {
        duplicate_check <- check_duplicate_content(value, current_type, current_id)
        if (is.list(duplicate_check) && duplicate_check$exists) {
          paste0("Similar content already exists: '", duplicate_check$existing_label, "' (ignoring spaces and case)")
        }
      }
    })
    
    # Convert API data to data frame for Text Elements
    convert_text_elements_to_df <- function(elements_list) {
      if (length(elements_list) > 0) {
        df <- data.frame(
          ID = sapply(elements_list, function(x) x$id),
          Type = sapply(elements_list, function(x) tools::toTitleCase(gsub("_", " ", x$type))),
          TypeSort = sapply(elements_list, function(x) x$type),  # Original type for sorting
          Content = sapply(elements_list, function(x) {
            label <- x$label
            if (nchar(label) > 100) paste0(substr(label, 1, 97), "...") else label
          }),
          Actions = sapply(elements_list, function(x) x$id),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        
        # Sort by Type first, then by Content alphabetically
        type_order <- c("title", "footnote", "population_set", "acronyms_set", "ich_category")
        df$TypeSort <- factor(df$TypeSort, levels = type_order)
        df <- df[order(df$TypeSort, df$Content), ]
        
        # Remove the TypeSort column after sorting
        df$TypeSort <- NULL
        
        return(df)
      } else {
        return(data.frame(
          ID = character(0),
          Type = character(0),
          Content = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        ))
      }
    }
    
    # Load Text Elements data
    load_text_elements_data <- function() {
      result <- get_text_elements()
      if (!is.null(result$error)) {
        cat("Error loading text elements:", result$error, "\n")
        show_error_notification("Error loading text elements")
        text_elements_data(data.frame())
      } else {
        text_elements_data(convert_text_elements_to_df(result))
        last_text_elements_update(Sys.time())
      }
    }
    
    # Initialize data loading
    observe({
      load_text_elements_data()
    })
    
    # Universal CRUD Manager integration (Phase 4)
    # Replaces entity-specific WebSocket observer with standardized refresh trigger
    observeEvent(input$`tnfp-crud_refresh`, {
      if (!is.null(input$`tnfp-crud_refresh`)) {
        cat("📝 Universal CRUD refresh triggered for TNFP\n")
        load_text_elements_data()
      }
    })
    
    # Legacy WebSocket observer (kept for backward compatibility during transition)
    observeEvent(input$websocket_event, {
      if (!is.null(input$websocket_event)) {
        event_data <- input$websocket_event
        cat("📝 Legacy WebSocket event received:", event_data$type, "\n")
        if (startsWith(event_data$type, "text_element_")) {
          load_text_elements_data()
        }
      }
    })
    
    # Render Text Elements table
    output$text_elements_table <- DT::renderDataTable({
      current_elements <- text_elements_data()
      
      if (nrow(current_elements) == 0) {
        empty_df <- data.frame(
          Type = character(0),
          Content = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE, check.names = FALSE
        )
        
        create_standard_datatable(
          empty_df,
          actions_column = TRUE,
          page_length = 10,
          empty_message = "No text elements found. Click 'Add Text Element' to create your first text element."
        )
      } else {
        # Add action buttons
        display_df <- current_elements[, c("Type", "Content")]
        display_df$Actions <- sapply(current_elements$ID, function(element_id) {
          element_content <- current_elements$Content[current_elements$ID == element_id]
          as.character(div(
            class = "d-flex gap-2 justify-content-center",
            tags$button(class = "btn btn-warning btn-sm", `data-action` = "edit", `data-id` = element_id, title = paste("Edit text element:", element_content), bs_icon("pencil")),
            tags$button(class = "btn btn-danger btn-sm", `data-action` = "delete", `data-id` = element_id, title = paste("Delete text element:", element_content), bs_icon("trash"))
          ))
        })
        
        create_standard_datatable(
          display_df,
          actions_column = TRUE,
          page_length = 10,
          draw_callback = JS(sprintf("
            function() {
              var table = this;
              console.log('Text elements table drawCallback triggered');
              var editButtons = $('#%s button[data-action=\"edit\"]');
              var deleteButtons = $('#%s button[data-action=\"delete\"]');
              console.log('Found edit buttons:', editButtons.length);
              console.log('Found delete buttons:', deleteButtons.length);
              editButtons.off('click').on('click', function() {
                var id = $(this).attr('data-id');
                console.log('Edit text element button clicked for ID:', id);
                Shiny.setInputValue('%s', id, {priority: 'event'});
              });
              deleteButtons.off('click').on('click', function() {
                var id = $(this).attr('data-id');
                console.log('Delete text element button clicked for ID:', id);
                Shiny.setInputValue('%s', id, {priority: 'event'});
              });
            }
          ", ns("text_elements_table"), ns("text_elements_table"), ns("edit_text_element_id"), ns("delete_text_element_id"))),
          extra_options = list(
            columnDefs = list(
              list(targets = 0, width = "25%"), # Type column
              list(targets = 1, width = "55%"), # Content column
              list(targets = 2, orderable = FALSE, searchable = FALSE, className = "text-center dt-nowrap", width = "1%") # Actions column minimal width
            ),
            initComplete = JS(sprintf("function(){ $('#%s thead tr:nth-child(2) th:last input, #%s thead tr:nth-child(2) th:last select').prop('disabled', true).attr('placeholder',''); }", ns("text_elements_table"), ns("text_elements_table")))
          )
        )
      }
    })
    
    # Output for conditional panels (simplified)
    # No longer needed since we use modals instead of conditional panels
    
    # Toggle sidebar for Text Element form
    observeEvent(input$toggle_add_text_element, {
      sidebar_toggle(id = "tnfp_sidebar")
      
      # Clear form
      editing_text_element_id(NULL)
      updateSelectInput(session, "new_text_element_type", selected = "title")
      updateTextAreaInput(session, "new_text_element_label", value = "")
    })
    
    # Helper function to extract and format error messages
    format_error_message <- function(error_string) {
      if (is.null(error_string) || error_string == "") {
        return("An unknown error occurred")
      }
      
      # Check if this is an HTTP error with response body
      if (grepl("HTTP 400 -", error_string)) {
        # Extract the JSON error message from HTTP 400 response
        json_part <- sub(".*HTTP 400 - ", "", error_string)
        tryCatch({
          # Parse the JSON response to get the detail message
          error_data <- jsonlite::fromJSON(json_part)
          if (!is.null(error_data$detail)) {
            return(error_data$detail)
          }
        }, error = function(e) {
          # If JSON parsing fails, return the original error
          return(error_string)
        })
      }
      
      # For other errors, return as-is
      return(error_string)
    }
    
    # Save Text Element (Add new element)
    observeEvent(input$save_text_element, {
      # Validate first
      iv_text_element_new$enable()
      if (!iv_text_element_new$is_valid()) {
        return()
      }
      
      # Prepare data
      element_data <- list(
        type = input$new_text_element_type,
        label = trimws(input$new_text_element_label)
      )
      
      # Create new element
      cat("Creating new text element\n")
      result <- create_text_element(element_data)
      
      # Handle result
      if (!is.null(result$error)) {
        formatted_error <- format_error_message(result$error)
        
        # Show detailed error message with better formatting
        if (grepl("Duplicate text elements are not allowed", formatted_error)) {
          # Special handling for duplicate errors
          showNotification(
            tagList(
              tags$strong("Duplicate Content Detected"),
              tags$br(),
              formatted_error,
              tags$br(),
              tags$small(
                class = "text-muted",
                "Tip: The system compares content ignoring spaces and letter case."
              )
            ),
            type = "error",
            duration = 8  # Duration in seconds
          )
        } else {
          showNotification(formatted_error, type = "error")
        }
      } else {
        showNotification("Text element created successfully!", type = "message")
        
        # Clear form and reset state
        updateSelectInput(session, "new_text_element_type", selected = "title")
        updateTextAreaInput(session, "new_text_element_label", value = "")
        
        # Disable validation to prevent triggering on cleared form
        iv_text_element_new$disable()
        
        # Close sidebar
        sidebar_toggle(id = "tnfp_sidebar")
        
        # Refresh data
        load_text_elements_data()
      }
    })
    
    # Save Text Element Edit (Update existing element)
    observeEvent(input$save_edit_text_element, {
      current_id <- editing_text_element_id()
      if (is.null(current_id)) return()
      
      # Validate using InputValidator
      iv_text_element_edit$enable()
      if (!iv_text_element_edit$is_valid()) {
        return()
      }
      
      # Prepare data
      element_data <- list(
        type = editing_text_element_type(),
        label = trimws(input$edit_text_element_label)
      )
      
      # Update existing element
      cat("Updating text element with ID:", current_id, "\n")
      result <- update_text_element(current_id, element_data)
      
      # Handle result
      if (!is.null(result$error)) {
        formatted_error <- format_error_message(result$error)
        
        # Show detailed error message with better formatting
        if (grepl("Duplicate text elements are not allowed", formatted_error)) {
          # Special handling for duplicate errors
          showNotification(
            tagList(
              tags$strong("Duplicate Content Detected"),
              tags$br(),
              formatted_error,
              tags$br(),
              tags$small(
                class = "text-muted",
                "Tip: The system compares content ignoring spaces and letter case."
              )
            ),
            type = "error",
            duration = 8  # Duration in seconds
          )
        } else {
          showNotification(formatted_error, type = "error")
        }
      } else {
        showNotification("Text element updated successfully!", type = "message")
        
        # Reset state
        editing_text_element_id(NULL)
        
        # Disable validation
        iv_text_element_edit$disable()
        
        # Close modal
        removeModal()
        
        # Refresh data
        load_text_elements_data()
      }
    })
    
    # Cancel button
    observeEvent(input$cancel_text_element, {
      editing_text_element_id(NULL)
      editing_text_element_type(NULL)
      updateSelectInput(session, "new_text_element_type", selected = "title")
      updateTextAreaInput(session, "new_text_element_label", value = "")
      iv_text_element_new$disable()
      sidebar_toggle(id = "tnfp_sidebar")
    })
    
    # Refresh button
    observeEvent(input$refresh_btn, {
      load_text_elements_data()
      showNotification("TNFP data refreshed", type = "message")
    })
    
    # Handle text element edit button clicks
    observeEvent(input$edit_text_element_id, {
      element_id <- input$edit_text_element_id
      cat("Edit text element button clicked for ID:", element_id, "\n")
      
      # Get current element data
      current_elements <- text_elements_data()
      element_to_edit <- current_elements[current_elements$ID == element_id, ]
      
      if (nrow(element_to_edit) > 0) {
        # Get full element data from API
        element_result <- get_text_element(element_id)
        if (!is.null(element_result$error)) {
          showNotification("Error loading text element for editing", type = "error")
          return()
        }
        
        # Set editing state
        editing_text_element_id(element_id)
        editing_text_element_type(element_result$type)
        
        # Show edit modal using Phase 2 utility
        modal_content <- tagList(
          create_text_input_field(
            input_id = ns("edit_text_element_type_display"),
            label = "Type",
            value = tools::toTitleCase(gsub("_", " ", element_result$type)),
            required = FALSE
          ) %>% 
            tagAppendAttributes(disabled = TRUE),
          
          create_textarea_input_field(
            input_id = ns("edit_text_element_label"),
            label = "Content",
            value = element_result$label,
            placeholder = "Enter text content...",
            rows = 4,
            required = TRUE
          ),
          
          tags$small(
            class = "text-muted form-text",
            tagList(
              bs_icon("info-circle", size = "0.8em"),
              " Duplicate content is not allowed (comparison ignores spaces and letter case)"
            )
          )
        )
        
        showModal(create_edit_modal(
          title = "Edit Text Element",
          content = modal_content,
          save_button_id = ns("save_edit_text_element"),
          save_button_label = "Save Changes",
          save_button_class = "btn-success"
        ))
      }
    })
    
    # Handle text element delete button clicks
    observeEvent(input$delete_text_element_id, {
      element_id <- input$delete_text_element_id
      cat("Delete text element button clicked for ID:", element_id, "\n")
      
      # Get element info for confirmation
      current_elements <- text_elements_data()
      element_to_delete <- current_elements[current_elements$ID == element_id, ]
      
      if (nrow(element_to_delete) > 0) {
        showModal(create_delete_confirmation_modal(
          entity_type = "Text Element",
          entity_name = element_to_delete$Content[1],
          confirm_button_id = ns("confirm_delete_text_element")
        ))
        
        # Store ID for confirmation handler
        observe({
          observeEvent(input$confirm_delete_text_element, {
            result <- delete_text_element(element_id)
            if (!is.null(result$error)) {
              showNotification(paste("Error deleting text element:", result$error), type = "error")
            } else {
              showNotification("Text element deleted successfully!", type = "message")
              load_text_elements_data()
            }
            removeModal()
          }, once = TRUE)
        })
      }
    })
    
    # Bulk Upload Handler
    observeEvent(input$process_bulk_upload, {
      # Check if a file has been selected
      if (is.null(input$bulk_upload_file)) {
        showNotification(
          "Please select an Excel file to upload",
          type = "warning",
          duration = 3  # Duration in seconds, not milliseconds
        )
        return()
      }
      
      # Clear previous results
      output$upload_results <- renderUI({
        div(class = "text-muted small", "Processing...")
      })
      
      # Check if readxl is available
      if (!requireNamespace("readxl", quietly = TRUE)) {
        showNotification(
          "Excel support not installed. Please install the 'readxl' package.",
          type = "error",
          duration = 5  # Duration in seconds
        )
        output$upload_results <- renderUI({
          div(class = "alert alert-danger small", "Excel support not available")
        })
        return()
      }
      
      # Validate file extension
      file_ext <- tolower(tools::file_ext(input$bulk_upload_file$name))
      if (!file_ext %in% c("xlsx", "xls")) {
        showNotification(
          "Please upload an Excel file (.xlsx or .xls)",
          type = "error",
          duration = 4  # Duration in seconds
        )
        output$upload_results <- renderUI({
          div(class = "alert alert-danger small", "Invalid file type. Please use .xlsx or .xls files.")
        })
        return()
      }
      
      # Read the uploaded file
      file_path <- input$bulk_upload_file$datapath
      
      # Check if file exists and is readable
      if (!file.exists(file_path)) {
        showNotification(
          "Unable to read the uploaded file. Please try again.",
          type = "error",
          duration = 4  # Duration in seconds
        )
        output$upload_results <- renderUI({
          div(class = "alert alert-danger small", "File upload failed. Please try again.")
        })
        return()
      }
      
      tryCatch({
        # Read Excel file
        df <- readxl::read_excel(file_path)
        
        # Check for required columns (case-insensitive)
        col_names_lower <- tolower(names(df))
        type_col <- which(col_names_lower == "type")[1]
        content_col <- which(col_names_lower == "content")[1]
        
        if (is.na(type_col) || is.na(content_col)) {
          showNotification(
            "Excel file must contain 'Type' and 'Content' columns",
            type = "error",
            duration = 5  # Duration in seconds
          )
          output$upload_results <- renderUI({
            div(class = "alert alert-danger small", 
                "Missing required columns. File must have 'Type' and 'Content' columns.")
          })
          return()
        }
        
        # Extract type and content columns
        types <- as.character(df[[type_col]])
        contents <- as.character(df[[content_col]])
        
        # Validate and process each row
        valid_types <- c("title", "footnote", "population_set", "acronyms_set", "ich_category")
        results <- list(
          success = 0,
          duplicates = 0,
          invalid_type = 0,
          empty_content = 0,
          errors = 0,
          details = list()
        )
        
        for (i in seq_along(types)) {
          # Skip empty rows
          if (is.na(types[i]) || is.na(contents[i]) || 
              trimws(types[i]) == "" || trimws(contents[i]) == "") {
            results$empty_content <- results$empty_content + 1
            next
          }
          
          # Normalize type value
          type_val <- tolower(trimws(types[i]))
          content_val <- trimws(contents[i])
          
          # Check if type is valid
          if (!type_val %in% valid_types) {
            results$invalid_type <- results$invalid_type + 1
            results$details <- append(results$details, 
              list(paste("Row", i, ": Invalid type '", types[i], "'")))
            next
          }
          
          # Check for duplicates (using our normalize function)
          duplicate_check <- check_duplicate_content(content_val, type_val)
          if (is.list(duplicate_check) && duplicate_check$exists) {
            results$duplicates <- results$duplicates + 1
            results$details <- append(results$details,
              list(paste("Row", i, ": Already exists - '", 
                        substr(content_val, 1, 50), 
                        if(nchar(content_val) > 50) "..." else "",
                        "'")))
            next
          }
          
          # Create the text element
          element_data <- list(
            type = type_val,
            label = content_val
          )
          
          result <- create_text_element(element_data)
          
          if (!is.null(result$error)) {
            results$errors <- results$errors + 1
            # Check if it's a duplicate error from the backend
            if (grepl("Duplicate", result$error)) {
              results$duplicates <- results$duplicates + 1
              results$success <- results$success - 1 # Adjust if we miscounted
            }
          } else {
            results$success <- results$success + 1
          }
        }
        
        # Display results with appropriate styling based on outcome
        if (results$success == 0 && results$duplicates > 0) {
          # All items were duplicates
          output$upload_results <- renderUI({
            div(
              class = "alert alert-info small",
              tags$strong("No New Items Added"),
              tags$p(
                class = "mb-2 mt-2",
                paste("All", results$duplicates, "item(s) in the file already exist in the database.")
              ),
              tags$small(
                class = "text-muted",
                "The system skipped duplicates to maintain data integrity."
              ),
              if (length(results$details) > 0 && length(results$details) <= 5) {
                tags$details(
                  tags$summary("Skipped items"),
                  tags$ul(
                    class = "small",
                    lapply(results$details[1:min(5, length(results$details))], tags$li)
                  )
                )
              }
            )
          })
          
          showNotification(
            "No new items imported - all items already exist in the database",
            type = "warning",
            duration = 4  # Duration in seconds
          )
        } else if (results$success == 0) {
          # No items were imported for other reasons
          output$upload_results <- renderUI({
            div(
              class = "alert alert-warning small",
              tags$strong("No Items Imported"),
              tags$ul(
                class = "mb-0 mt-2",
                if (results$duplicates > 0) tags$li(paste("Already in database:", results$duplicates)),
                if (results$invalid_type > 0) tags$li(paste("Invalid types:", results$invalid_type)),
                if (results$empty_content > 0) tags$li(paste("Empty rows:", results$empty_content)),
                if (results$errors > 0) tags$li(paste("Errors:", results$errors))
              ),
              if (length(results$details) > 0 && length(results$details) <= 5) {
                tags$details(
                  tags$summary("Details"),
                  tags$ul(
                    class = "small",
                    lapply(results$details[1:min(5, length(results$details))], tags$li)
                  )
                )
              }
            )
          })
          
          showNotification(
            "No items were imported. Check the details for more information.",
            type = "warning",
            duration = 4  # Duration in seconds
          )
        } else {
          # Some items were successfully imported
          output$upload_results <- renderUI({
            div(
              class = "alert alert-success small",
              tags$strong("Upload Complete"),
              tags$ul(
                class = "mb-0 mt-2",
                tags$li(paste("Successfully created:", results$success, "items")),
                if (results$duplicates > 0) tags$li(paste("Already in database (skipped):", results$duplicates)),
                if (results$invalid_type > 0) tags$li(paste("Invalid types:", results$invalid_type)),
                if (results$empty_content > 0) tags$li(paste("Empty rows:", results$empty_content)),
                if (results$errors > 0) tags$li(paste("Errors:", results$errors))
              ),
              if (length(results$details) > 0 && length(results$details) <= 5) {
                tags$details(
                  tags$summary("Details"),
                  tags$ul(
                    class = "small",
                    lapply(results$details[1:min(5, length(results$details))], tags$li)
                  )
                )
              }
            )
          })
          
          # Refresh the table and show success notification
          load_text_elements_data()
          showNotification(
            paste("Successfully imported", results$success, "text elements"),
            type = "message",
            duration = 4  # Duration in seconds
          )
        }
        
        # Clean up the temp file
        if (file.exists(file_path)) {
          unlink(file_path)
        }
        
        # Reset file input
        shinyjs::reset("bulk_upload_file")
        
      }, error = function(e) {
        showNotification(
          paste("Error reading Excel file:", e$message),
          type = "error",
          duration = 5  # Duration in seconds
        )
        output$upload_results <- renderUI({
          div(class = "alert alert-danger small", 
              paste("Error:", e$message))
        })
        
        # Clean up the temp file
        if (file.exists(file_path)) {
          unlink(file_path)
        }
      })
    })
  })
}