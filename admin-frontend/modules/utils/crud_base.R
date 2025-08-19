# Base CRUD utilities for R Shiny modules
# Provides common patterns for form validation, API calls, and DataTable configuration

library(shinyvalidate)
library(DT)

# Standard DataTable configuration for all modules
create_standard_datatable <- function(data, 
                                      actions_column = TRUE, 
                                      search_placeholder = "Search (regex supported):",
                                      page_length = 25,
                                      empty_message = "No data available",
                                      show_entries = TRUE,
                                      show_pagination = TRUE,
                                      draw_callback = NULL,
                                      extra_options = list()) {
  
  # Handle empty data case
  if (is.null(data) || nrow(data) == 0) {
    # Create empty dataframe with proper structure
    if (actions_column && (is.null(data) || !"Actions" %in% names(data))) {
      if (is.null(data)) {
        data <- data.frame(Actions = character(0))
      } else {
        data$Actions <- character(0)
      }
    }
    
    # Return empty table with consistent styling
    return(DT::datatable(
      data,
      filter = 'top',
      options = list(
        dom = if (show_entries && show_pagination) 'frtip' else if (!show_entries && show_pagination) 'frtip' else 'frt',
        pageLength = page_length,
        searching = TRUE,
        language = list(
          search = "",
          searchPlaceholder = search_placeholder,
          emptyTable = empty_message
        ),
        columnDefs = if (actions_column && "Actions" %in% names(data)) {
          list(list(
            targets = which(names(data) == "Actions") - 1,
            searchable = FALSE,
            orderable = FALSE,
            width = "120px"
          ))
        } else {
          list()
        }
      ),
      escape = FALSE,
      rownames = FALSE,
      selection = 'none'
    ))
  }
  
  # Add Actions column if requested and not present
  if (actions_column && !"Actions" %in% names(data)) {
    data$Actions <- ""  # Will be populated by JavaScript drawCallback
  }
  
  # Standard options for non-empty tables
  dom_config <- if (show_entries && show_pagination) 'frtip' else if (!show_entries && show_pagination) 'frtip' else 'frt'
  
  options <- list(
    dom = dom_config,  # Show filter, processing, table, info, pagination
    pageLength = page_length,
    searching = TRUE,
    autoWidth = FALSE,
    language = list(
      search = "",
      searchPlaceholder = search_placeholder,
      emptyTable = empty_message,
      info = paste("Showing _START_ to _END_ of _TOTAL_ entries"),
      infoEmpty = "Showing 0 to 0 of 0 entries",
      infoFiltered = "(filtered from _MAX_ total entries)"
    ),
    search = list(
      regex = TRUE,
      caseInsensitive = TRUE,
      search = ""
    ),
    columnDefs = list()
  )
  
  # Add drawCallback if provided
  if (!is.null(draw_callback)) {
    options$drawCallback <- draw_callback
  }
  
  # Merge any extra options
  if (length(extra_options) > 0) {
    options <- modifyList(options, extra_options)
  }
  
  # Configure Actions column if present
  if (actions_column && "Actions" %in% names(data)) {
    actions_col_index <- which(names(data) == "Actions") - 1  # 0-indexed
    options$columnDefs <- append(options$columnDefs, list(list(
      targets = actions_col_index,
      searchable = FALSE,
      orderable = FALSE,
      width = "120px",
      className = "text-center"
    )))
  }
  
  DT::datatable(
    data,
    filter = 'top',
    options = options,
    escape = FALSE,  # Allow HTML in Actions column
    rownames = FALSE,
    selection = 'none'
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