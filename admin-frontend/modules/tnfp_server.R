# TNFP Server Module - Text Elements and Acronyms Management

tnfp_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Reactive values for Text Elements
    text_elements_data <- reactiveVal(data.frame())
    last_text_elements_update <- reactiveVal(Sys.time())
    is_editing_text_element <- reactiveVal(FALSE)
    editing_text_element_id <- reactiveVal(NULL)
    
    # Reactive values for Acronyms
    acronyms_data <- reactiveVal(data.frame())
    last_acronyms_update <- reactiveVal(Sys.time())
    is_editing_acronym <- reactiveVal(FALSE)
    editing_acronym_id <- reactiveVal(NULL)
    
    # Set up validation for new text element form
    iv_text_element_new <- InputValidator$new()
    iv_text_element_new$add_rule("new_text_element_type", sv_required())
    iv_text_element_new$add_rule("new_text_element_label", sv_required())
    iv_text_element_new$add_rule("new_text_element_label", function(value) {
      if (nchar(trimws(value)) < 3) {
        "Label must be at least 3 characters long"
      }
    })
    
    # Set up validation for new acronym form
    iv_acronym_new <- InputValidator$new()
    iv_acronym_new$add_rule("new_acronym_key", sv_required())
    iv_acronym_new$add_rule("new_acronym_value", sv_required())
    iv_acronym_new$add_rule("new_acronym_key", function(value) {
      if (nchar(trimws(value)) < 1 || nchar(trimws(value)) > 50) {
        "Key must be between 1 and 50 characters"
      }
    })
    iv_acronym_new$add_rule("new_acronym_key", function(value) {
      existing_acronyms <- acronyms_data()
      current_id <- editing_acronym_id()
      if (nrow(existing_acronyms) > 0) {
        other_acronyms <- if (!is.null(current_id)) {
          existing_acronyms[existing_acronyms$ID != current_id, ]
        } else {
          existing_acronyms
        }
        if (nrow(other_acronyms) > 0 && trimws(toupper(value)) %in% toupper(other_acronyms$Key)) {
          "An acronym with this key already exists"
        }
      }
    })
    
    # Convert API data to data frame for Text Elements
    convert_text_elements_to_df <- function(elements_list) {
      if (length(elements_list) > 0) {
        df <- data.frame(
          ID = sapply(elements_list, function(x) x$id),
          Type = sapply(elements_list, function(x) tools::toTitleCase(gsub("_", " ", x$type))),
          Label = sapply(elements_list, function(x) {
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
          Label = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        ))
      }
    }
    
    # Convert API data to data frame for Acronyms
    convert_acronyms_to_df <- function(acronyms_list) {
      if (length(acronyms_list) > 0) {
        df <- data.frame(
          ID = sapply(acronyms_list, function(x) x$id),
          Key = sapply(acronyms_list, function(x) x$key),
          Value = sapply(acronyms_list, function(x) x$value),
          Description = sapply(acronyms_list, function(x) {
            desc <- ifelse(is.null(x$description) || x$description == "", "-", x$description)
            if (!is.null(desc) && nchar(desc) > 100) paste0(substr(desc, 1, 97), "...") else desc
          }),
          Actions = sapply(acronyms_list, function(x) x$id),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(df)
      } else {
        return(data.frame(
          ID = character(0),
          Key = character(0),
          Value = character(0),
          Description = character(0),
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
    
    # Load Acronyms data
    load_acronyms_data <- function() {
      cat("Loading acronyms data...\n")
      result <- get_acronyms()
      if (!is.null(result$error)) {
        cat("Error loading acronyms:", result$error, "\n")
        showNotification("Error loading acronyms", type = "error")
        acronyms_data(data.frame())
      } else {
        cat("Loaded", length(result), "acronyms\n")
        acronyms_data(convert_acronyms_to_df(result))
        last_acronyms_update(Sys.time())
      }
    }
    
    # Initialize data loading
    observe({
      load_text_elements_data()
      load_acronyms_data()
    })
    
    # WebSocket event handling for Text Elements
    observeEvent(input$websocket_event, {
      if (!is.null(input$websocket_event)) {
        event_data <- input$websocket_event
        cat("TNFP WebSocket event received:", event_data$type, "\n")
        
        if (startsWith(event_data$type, "text_element_")) {
          cat("Text element event detected, refreshing data\n")
          load_text_elements_data()
        } else if (startsWith(event_data$type, "acronym_")) {
          cat("Acronym event detected, refreshing data\n") 
          load_acronyms_data()
        }
      }
    })
    
    # Render Text Elements table
    output$text_elements_table <- DT::renderDataTable({
      current_elements <- text_elements_data()
      
      if (nrow(current_elements) == 0) {
        empty_df <- data.frame(
          Type = character(0),
          Label = character(0),
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
        display_df <- current_elements[, c("Type", "Label")]
        display_df$Actions <- sapply(current_elements$ID, function(element_id) {
          element_label <- current_elements$Label[current_elements$ID == element_id]
          as.character(div(
            class = "d-flex gap-2 justify-content-center",
            tags$button(
              class = "btn btn-warning btn-sm",
              `data-action` = "edit",
              `data-id` = element_id,
              title = paste("Edit text element:", element_label),
              tagList(bs_icon("pencil"), "Edit")
            ),
            tags$button(
              class = "btn btn-danger btn-sm",
              `data-action` = "delete",
              `data-id` = element_id,
              title = paste("Delete text element:", element_label),
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
              list(targets = 0, width = "30%"), # Type column
              list(targets = 1, width = "50%"), # Label column
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
    
    # Render Acronyms table
    output$acronyms_table <- DT::renderDataTable({
      current_acronyms <- acronyms_data()
      
      if (nrow(current_acronyms) == 0) {
        empty_df <- data.frame(
          Key = character(0),
          Value = character(0), 
          Description = character(0),
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
            language = list(emptyTable = "No acronyms found. Click 'Add Acronym' to create your first acronym.")
          ),
          escape = FALSE, rownames = FALSE, selection = 'none'
        )
      } else {
        # Add action buttons
        display_df <- current_acronyms[, c("Key", "Value", "Description")]
        display_df$Actions <- sapply(current_acronyms$ID, function(acronym_id) {
          acronym_key <- current_acronyms$Key[current_acronyms$ID == acronym_id]
          as.character(div(
            class = "d-flex gap-2 justify-content-center",
            tags$button(
              class = "btn btn-warning btn-sm",
              `data-action` = "edit",
              `data-id` = acronym_id,
              title = paste("Edit acronym:", acronym_key),
              tagList(bs_icon("pencil"), "Edit")
            ),
            tags$button(
              class = "btn btn-danger btn-sm",
              `data-action` = "delete",
              `data-id` = acronym_id,
              title = paste("Delete acronym:", acronym_key),
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
              list(targets = 0, width = "15%"), # Key column
              list(targets = 1, width = "35%"), # Value column  
              list(targets = 2, width = "30%"), # Description column
              list(targets = 3, width = "20%", orderable = FALSE, className = "text-center") # Actions column
            ),
            drawCallback = JS(sprintf("
              function() {
                var table = this;
                console.log('Acronyms table drawCallback triggered');
                var editButtons = $('#%s button[data-action=\"edit\"]');
                var deleteButtons = $('#%s button[data-action=\"delete\"]');
                console.log('Found edit buttons:', editButtons.length);
                console.log('Found delete buttons:', deleteButtons.length);
                editButtons.off('click').on('click', function() {
                  var id = $(this).attr('data-id');
                  console.log('Edit acronym button clicked for ID:', id);
                  Shiny.setInputValue('%s', id, {priority: 'event'});
                });
                deleteButtons.off('click').on('click', function() {
                  var id = $(this).attr('data-id');
                  console.log('Delete acronym button clicked for ID:', id);
                  Shiny.setInputValue('%s', id, {priority: 'event'});
                });
              }
            ", ns("acronyms_table"), ns("acronyms_table"), ns("edit_acronym_id"), ns("delete_acronym_id")))
          ),
          escape = FALSE, rownames = FALSE, selection = 'none'
        )
      }
    })
    
    # Output for conditional panels
    output$is_editing_text_element <- reactive({ is_editing_text_element() })
    output$is_editing_acronym <- reactive({ is_editing_acronym() })
    outputOptions(output, "is_editing_text_element", suspendWhenHidden = FALSE)
    outputOptions(output, "is_editing_acronym", suspendWhenHidden = FALSE)
    
    # Toggle sidebar for Text Element form
    observeEvent(input$toggle_add_text_element, {
      # Switch to text elements and open sidebar
      updateRadioButtons(session, "entity_type", selected = "text_elements")
      sidebar_toggle(id = "tnfp_sidebar")
      
      # Clear form and set to add mode
      is_editing_text_element(FALSE)
      editing_text_element_id(NULL)
      updateSelectInput(session, "new_text_element_type", selected = "title")
      updateTextAreaInput(session, "new_text_element_label", value = "")
    })
    
    # Toggle sidebar for Acronym form
    observeEvent(input$toggle_add_acronym, {
      # Switch to acronyms and open sidebar
      updateRadioButtons(session, "entity_type", selected = "acronyms")
      sidebar_toggle(id = "tnfp_sidebar")
      
      # Clear form and set to add mode  
      is_editing_acronym(FALSE)
      editing_acronym_id(NULL)
      updateTextInput(session, "new_acronym_key", value = "")
      updateTextInput(session, "new_acronym_value", value = "")
      updateTextAreaInput(session, "new_acronym_description", value = "")
    })
    
    # Save Text Element (using extended reactive for task button)
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
      
      # Perform operation
      if (is_editing_text_element()) {
        # Update existing element
        current_id <- editing_text_element_id()
        cat("Updating text element with ID:", current_id, "\n")
        result <- update_text_element(current_id, element_data)
      } else {
        # Create new element
        cat("Creating new text element\n")
        result <- create_text_element(element_data)
      }
      
      # Handle result
      if (!is.null(result$error)) {
        showNotification(paste("Error:", result$error), type = "error")
      } else {
        action_word <- if (is_editing_text_element()) "updated" else "created"
        showNotification(paste("Text element", action_word, "successfully!"), type = "message")
        
        # Clear form and reset state
        is_editing_text_element(FALSE)
        editing_text_element_id(NULL)
        updateSelectInput(session, "new_text_element_type", selected = "title")
        updateTextAreaInput(session, "new_text_element_label", value = "")
        
        # Refresh data
        load_text_elements_data()
      }
    })
    
    # Save Acronym (using extended reactive for task button)
    observeEvent(input$save_acronym, {
      # Validate first
      iv_acronym_new$enable()
      if (!iv_acronym_new$is_valid()) {
        return()
      }
      
      # Prepare data
      acronym_data <- list(
        key = trimws(input$new_acronym_key),
        value = trimws(input$new_acronym_value),
        description = if (trimws(input$new_acronym_description) == "") NULL else trimws(input$new_acronym_description)
      )
      
      # Perform operation
      if (is_editing_acronym()) {
        # Update existing acronym
        current_id <- editing_acronym_id()
        cat("Updating acronym with ID:", current_id, "\n")
        result <- update_acronym(current_id, acronym_data)
      } else {
        # Create new acronym
        cat("Creating new acronym\n")
        result <- create_acronym(acronym_data)
      }
      
      # Handle result
      if (!is.null(result$error)) {
        showNotification(paste("Error:", result$error), type = "error")
      } else {
        action_word <- if (is_editing_acronym()) "updated" else "created"
        showNotification(paste("Acronym", action_word, "successfully!"), type = "message")
        
        # Clear form and reset state
        is_editing_acronym(FALSE)
        editing_acronym_id(NULL)
        updateTextInput(session, "new_acronym_key", value = "")
        updateTextInput(session, "new_acronym_value", value = "")
        updateTextAreaInput(session, "new_acronym_description", value = "")
        
        # Refresh data
        load_acronyms_data()
      }
    })
    
    # Cancel buttons
    observeEvent(input$cancel_text_element, {
      is_editing_text_element(FALSE)
      editing_text_element_id(NULL)
      updateSelectInput(session, "new_text_element_type", selected = "title")
      updateTextAreaInput(session, "new_text_element_label", value = "")
    })
    
    observeEvent(input$cancel_acronym, {
      is_editing_acronym(FALSE)
      editing_acronym_id(NULL)
      updateTextInput(session, "new_acronym_key", value = "")
      updateTextInput(session, "new_acronym_value", value = "")
      updateTextAreaInput(session, "new_acronym_description", value = "")
    })
    
    # Refresh button
    observeEvent(input$refresh_btn, {
      load_text_elements_data()
      load_acronyms_data()
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
        
        # Switch to text elements tab and open sidebar
        updateRadioButtons(session, "entity_type", selected = "text_elements")
        sidebar_toggle(id = "tnfp_sidebar", open = TRUE)
        
        # Set editing state
        is_editing_text_element(TRUE)
        editing_text_element_id(element_id)
        
        # Populate form with current data
        updateSelectInput(session, "new_text_element_type", selected = element_result$type)
        updateTextAreaInput(session, "new_text_element_label", value = element_result$label)
        
        # Enable validation
        iv_text_element_new$enable()
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
          paste("Are you sure you want to delete the text element:", element_to_delete$Label[1], "?"),
          footer = tagList(
            modalButton("Cancel"),
            input_task_button(ns("confirm_delete_text_element"), "Delete", class = "btn-danger")
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
    
    # Handle acronym edit button clicks
    observeEvent(input$edit_acronym_id, {
      acronym_id <- input$edit_acronym_id
      cat("Edit acronym button clicked for ID:", acronym_id, "\n")
      
      # Get current acronym data
      current_acronyms <- acronyms_data()
      acronym_to_edit <- current_acronyms[current_acronyms$ID == acronym_id, ]
      
      if (nrow(acronym_to_edit) > 0) {
        # Get full acronym data from API
        acronym_result <- get_acronym(acronym_id)
        if (!is.null(acronym_result$error)) {
          showNotification("Error loading acronym for editing", type = "error")
          return()
        }
        
        # Switch to acronyms tab and open sidebar
        updateRadioButtons(session, "entity_type", selected = "acronyms")
        sidebar_toggle(id = "tnfp_sidebar", open = TRUE)
        
        # Set editing state
        is_editing_acronym(TRUE)
        editing_acronym_id(acronym_id)
        
        # Populate form with current data
        updateTextInput(session, "new_acronym_key", value = acronym_result$key)
        updateTextInput(session, "new_acronym_value", value = acronym_result$value)
        updateTextAreaInput(session, "new_acronym_description", 
                           value = if (is.null(acronym_result$description)) "" else acronym_result$description)
        
        # Enable validation
        iv_acronym_new$enable()
      }
    })
    
    # Handle acronym delete button clicks
    observeEvent(input$delete_acronym_id, {
      acronym_id <- input$delete_acronym_id
      cat("Delete acronym button clicked for ID:", acronym_id, "\n")
      
      # Get acronym info for confirmation
      current_acronyms <- acronyms_data()
      acronym_to_delete <- current_acronyms[current_acronyms$ID == acronym_id, ]
      
      if (nrow(acronym_to_delete) > 0) {
        showModal(modalDialog(
          title = "Confirm Deletion",
          paste("Are you sure you want to delete the acronym:", acronym_to_delete$Key[1], "->", acronym_to_delete$Value[1], "?"),
          footer = tagList(
            modalButton("Cancel"),
            input_task_button(ns("confirm_delete_acronym"), "Delete", class = "btn-danger")
          ),
          easyClose = TRUE
        ))
        
        # Store ID for confirmation handler
        observe({
          observeEvent(input$confirm_delete_acronym, {
            result <- delete_acronym(acronym_id)
            if (!is.null(result$error)) {
              showNotification(paste("Error deleting acronym:", result$error), type = "error")
            } else {
              showNotification("Acronym deleted successfully!", type = "message")
              load_acronyms_data()
            }
            removeModal()
          }, once = TRUE)
        })
      }
    })
  })
}