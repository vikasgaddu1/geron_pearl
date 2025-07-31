# TNFP Server Module - Text Elements Management

tnfp_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Reactive values for Text Elements
    text_elements_data <- reactiveVal(data.frame())
    last_text_elements_update <- reactiveVal(Sys.time())
    editing_text_element_id <- reactiveVal(NULL)
    
    # Set up validation for new text element form
    iv_text_element_new <- InputValidator$new()
    iv_text_element_new$add_rule("new_text_element_type", sv_required())
    iv_text_element_new$add_rule("new_text_element_label", sv_required())
    iv_text_element_new$add_rule("new_text_element_label", function(value) {
      if (nchar(trimws(value)) < 3) {
        "Content must be at least 3 characters long"
      }
    })
    
    # Convert API data to data frame for Text Elements
    convert_text_elements_to_df <- function(elements_list) {
      if (length(elements_list) > 0) {
        df <- data.frame(
          ID = sapply(elements_list, function(x) x$id),
          Type = sapply(elements_list, function(x) tools::toTitleCase(gsub("_", " ", x$type))),
          Content = sapply(elements_list, function(x) {
            label <- x$label
            if (nchar(label) > 100) paste0(substr(label, 1, 97), "...") else label
          }),
          Actions = sapply(elements_list, function(x) x$id),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
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
      cat("Loading text elements data...\n")
      result <- get_text_elements()
      if (!is.null(result$error)) {
        cat("Error loading text elements:", result$error, "\n")
        showNotification("Error loading text elements", type = "error")
        text_elements_data(data.frame())
      } else {
        cat("Loaded", length(result), "text elements\n")
        text_elements_data(convert_text_elements_to_df(result))
        last_text_elements_update(Sys.time())
      }
    }
    
    # Initialize data loading
    observe({
      load_text_elements_data()
    })
    
    # WebSocket event handling for Text Elements
    observeEvent(input$websocket_event, {
      if (!is.null(input$websocket_event)) {
        event_data <- input$websocket_event
        cat("TNFP WebSocket event received:", event_data$type, "\n")
        
        if (startsWith(event_data$type, "text_element_")) {
          cat("Text element event detected, refreshing data\n")
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
        
        DT::datatable(empty_df, 
          filter = 'top',
          options = list(
            dom = 'frtip',
            search = list(regex = TRUE, caseInsensitive = TRUE),
            searching = TRUE,
            pageLength = 10,
            language = list(emptyTable = "No text elements found. Click 'Add Text Element' to create your first text element.")
          ),
          escape = FALSE, rownames = FALSE, selection = 'none'
        )
      } else {
        # Add action buttons
        display_df <- current_elements[, c("Type", "Content")]
        display_df$Actions <- sapply(current_elements$ID, function(element_id) {
          element_content <- current_elements$Content[current_elements$ID == element_id]
          as.character(div(
            class = "d-flex gap-2 justify-content-center",
            tags$button(
              class = "btn btn-warning btn-sm",
              `data-action` = "edit",
              `data-id` = element_id,
              title = paste("Edit text element:", element_content),
              tagList(bs_icon("pencil"), "Edit")
            ),
            tags$button(
              class = "btn btn-danger btn-sm",
              `data-action` = "delete",
              `data-id` = element_id,
              title = paste("Delete text element:", element_content),
              tagList(bs_icon("trash"), "Delete")
            )
          ))
        })
        
        DT::datatable(display_df,
          filter = 'top',
          options = list(
            dom = 'frtip',
            search = list(regex = TRUE, caseInsensitive = TRUE),
            searching = TRUE,
            pageLength = 10,
            autoWidth = FALSE,
            columnDefs = list(
              list(targets = 0, width = "25%"), # Type column
              list(targets = 1, width = "55%"), # Content column
              list(targets = 2, width = "20%", orderable = FALSE, className = "text-center") # Actions column
            ),
            drawCallback = JS(sprintf("
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
            ", ns("text_elements_table"), ns("text_elements_table"), ns("edit_text_element_id"), ns("delete_text_element_id")))
          ),
          escape = FALSE, rownames = FALSE, selection = 'none'
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
        showNotification(paste("Error:", result$error), type = "error")
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
      
      # Basic validation
      if (is.null(input$edit_text_element_type) || input$edit_text_element_type == "" ||
          is.null(input$edit_text_element_label) || trimws(input$edit_text_element_label) == "" ||
          nchar(trimws(input$edit_text_element_label)) < 3) {
        showNotification("Please fill in all fields. Content must be at least 3 characters long.", type = "error")
        return()
      }
      
      # Prepare data
      element_data <- list(
        type = input$edit_text_element_type,
        label = trimws(input$edit_text_element_label)
      )
      
      # Update existing element
      cat("Updating text element with ID:", current_id, "\n")
      result <- update_text_element(current_id, element_data)
      
      # Handle result
      if (!is.null(result$error)) {
        showNotification(paste("Error:", result$error), type = "error")
      } else {
        showNotification("Text element updated successfully!", type = "message")
        
        # Reset state
        editing_text_element_id(NULL)
        
        # Close modal
        removeModal()
        
        # Refresh data
        load_text_elements_data()
      }
    })
    
    # Cancel button
    observeEvent(input$cancel_text_element, {
      editing_text_element_id(NULL)
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
        
        # Show edit modal
        showModal(modalDialog(
          title = tagList(bs_icon("pencil"), "Edit Text Element"),
          size = "m",
          easyClose = FALSE,
          
          div(
            class = "mb-3",
            tags$label("Type", class = "form-label fw-bold"),
            selectInput(
              ns("edit_text_element_type"),
              NULL,
              choices = list(
                "Title" = "title",
                "Footnote" = "footnote",
                "Population Set" = "population_set",
                "Acronym Set" = "acronyms_set"
              ),
              selected = element_result$type,
              width = "100%"
            )
          ),
          
          div(
            class = "mb-3",
            tags$label("Content", class = "form-label fw-bold"),
            textAreaInput(
              ns("edit_text_element_label"),
              NULL,
              value = element_result$label,
              placeholder = "Enter text content...",
              rows = 4,
              width = "100%"
            )
          ),
          
          footer = tagList(
            modalButton("Cancel"),
            actionButton(
              ns("save_edit_text_element"),
              tagList(bs_icon("check"), "Save Changes"),
              class = "btn btn-success"
            )
          )
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
        showModal(modalDialog(
          title = "Confirm Deletion",
          paste("Are you sure you want to delete the text element:", element_to_delete$Content[1], "?"),
          footer = tagList(
            modalButton("Cancel"),
            actionButton(ns("confirm_delete_text_element"), "Delete", class = "btn btn-danger")
          ),
          easyClose = TRUE
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
  })
}