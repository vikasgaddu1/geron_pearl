# Base CRUD utilities for R Shiny modules
# Provides common patterns for form validation, API calls, and DataTable configuration

library(shinyvalidate)
library(DT)

# Standard DataTable configuration for all modules
create_standard_datatable <- function(data, 
                                      actions_column = TRUE, 
                                      search_placeholder = "Search (regex supported):",
                                      page_length = 25) {
  
  # Add Actions column if requested
  if (actions_column && !"Actions" %in% names(data)) {
    data$Actions <- ""  # Will be populated by JavaScript drawCallback
  }
  
  # Standard options
  options <- list(
    dom = 'frtip',  # Show filter, processing, table, info, pagination
    search = list(regex = TRUE, caseInsensitive = TRUE),
    pageLength = page_length,
    searching = TRUE,
    language = list(search = search_placeholder),
    columnDefs = list()
  )
  
  # Configure Actions column if present
  if (actions_column && "Actions" %in% names(data)) {
    actions_col_index <- which(names(data) == "Actions") - 1  # 0-indexed
    options$columnDefs <- append(options$columnDefs, list(list(
      targets = actions_col_index,
      searchable = FALSE,
      orderable = FALSE,
      width = "120px"
    )))
  }
  
  DT::datatable(
    data,
    filter = 'top',
    options = options,
    escape = FALSE,  # Allow HTML in Actions column
    rownames = FALSE
  )
}

# Standard form validation setup
setup_form_validation <- function(input_validator, fields) {
  # fields should be a list of lists: list(list(id = "field_id", rules = list(...)))
  
  for (field in fields) {
    field_id <- field$id
    
    # Add required rule if specified
    if ("required" %in% names(field) && field$required) {
      input_validator$add_rule(field_id, sv_required())
    }
    
    # Add minimum length rule if specified
    if ("min_length" %in% names(field)) {
      min_len <- field$min_length
      input_validator$add_rule(field_id, function(value) {
        if (is.null(value) || nchar(trimws(value)) < min_len) {
          paste("Must be at least", min_len, "characters")
        }
      })
    }
    
    # Add custom rules if specified
    if ("custom_rules" %in% names(field)) {
      for (rule in field$custom_rules) {
        input_validator$add_rule(field_id, rule)
      }
    }
  }
  
  return(input_validator)
}

# Standard API error handling
handle_api_response <- function(result, success_message = "Operation completed successfully") {
  if ("error" %in% names(result)) {
    # Format error message for display
    error_msg <- result$error
    if (grepl("HTTP 400 -", error_msg)) {
      # Extract JSON part from HTTP error
      json_part <- sub(".*HTTP 400 - ", "", error_msg)
      tryCatch({
        error_data <- jsonlite::fromJSON(json_part)
        error_msg <- error_data$detail
      }, error = function(e) {
        # Keep original error if JSON parsing fails
      })
    }
    
    showNotification(
      error_msg,
      type = "error",
      duration = 5000
    )
    return(FALSE)
  } else {
    if (!is.null(success_message)) {
      showNotification(
        success_message,
        type = "message",
        duration = 3000
      )
    }
    return(TRUE)
  }
}

# Standard CRUD refresh pattern
setup_crud_refresh_observer <- function(input, load_data_func, module_prefix = NULL) {
  # Generate the input name for CRUD refresh
  refresh_input_name <- if (!is.null(module_prefix)) {
    paste0(module_prefix, "-crud_refresh")
  } else {
    "crud_refresh"
  }
  
  # Note: The actual observer needs to be created in the calling module
  # This function returns the input name to observe
  return(refresh_input_name)
}

# Standard modal creation for CRUD operations
create_crud_modal <- function(modal_id, title, form_content, size = "m") {
  modalDialog(
    title = title,
    size = size,
    footer = tagList(
      modalButton("Cancel"),
      actionButton(paste0(modal_id, "_save"), "Save", class = "btn-primary")
    ),
    form_content,
    easyClose = FALSE
  )
}

# Standard loading state management
show_loading_state <- function(button_id, loading = TRUE) {
  if (loading) {
    shinyjs::addClass(id = button_id, class = "disabled")
    shinyjs::html(id = button_id, html = '<i class="fa fa-spinner fa-spin"></i> Loading...')
  } else {
    shinyjs::removeClass(id = button_id, class = "disabled")
    shinyjs::html(id = button_id, html = 'Save')
  }
}

# Utility function for generating action buttons HTML
generate_action_buttons <- function(item_id, edit_label = "Edit", delete_label = "Delete") {
  sprintf(
    '<button class="btn btn-primary btn-sm me-1" data-action="edit" data-id="%s" title="%s">
       <i class="bi bi-pencil"></i>
     </button>
     <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" title="%s">
       <i class="bi bi-trash"></i>
     </button>',
    item_id, edit_label, item_id, delete_label
  )
}

# Standard delete confirmation modal
create_delete_confirmation_modal <- function(entity_type, entity_name) {
  modalDialog(
    title = paste("Delete", entity_type),
    paste("Are you sure you want to delete", tolower(entity_type), "'", entity_name, "'?"),
    tags$div(class = "mt-2 text-muted", 
             "This action cannot be undone."),
    footer = tagList(
      modalButton("Cancel"),
      actionButton("confirm_delete", "Delete", class = "btn-danger")
    ),
    easyClose = FALSE
  )
}

# Standard WebSocket event observer setup
# Note: This returns the observer code that should be used in modules
get_websocket_observer_code <- function(module_name, event_types, refresh_function_name = "load_data") {
  sprintf('
    # WebSocket event observer for %s
    observeEvent(input$`%s-websocket_event`, {
      if (!is.null(input$`%s-websocket_event`)) {
        event_data <- input$`%s-websocket_event`
        event_types <- c(%s)
        if (event_data$type %%in%% event_types) {
          %s()  # Refresh data
        }
      }
    })
    
    # Universal CRUD Manager refresh observer
    observeEvent(input$crud_refresh, {
      if (!is.null(input$crud_refresh)) {
        %s()  # Refresh data
      }
    })
  ', module_name, module_name, module_name, module_name,
     paste0('"', event_types, '"', collapse = ", "),
     refresh_function_name, refresh_function_name)
}

# Environment variable helpers
get_api_endpoint <- function(endpoint_name, default_path) {
  base_url <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  path <- Sys.getenv(endpoint_name, default_path)
  paste0(base_url, path)
}