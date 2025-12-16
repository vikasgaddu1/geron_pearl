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

# =============================================================================
# FORM VALIDATION PATTERNS (Phase 2C - Low Priority)
# =============================================================================

# Enhanced form validation setup with common patterns
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

# Standard validation functions for common input types
validate_required_text_input <- function(input_value, field_name, min_length = 1) {
  if (is.null(input_value) || nchar(trimws(input_value)) < min_length) {
    return(paste(field_name, "must be at least", min_length, "characters"))
  }
  return(NULL)
}

validate_numeric_input <- function(input_value, field_name, min_value = 0, max_value = NULL) {
  if (is.null(input_value) || !is.numeric(input_value)) {
    return(paste(field_name, "must be a valid number"))
  }
  
  if (input_value < min_value) {
    return(paste(field_name, "must be at least", min_value))
  }
  
  if (!is.null(max_value) && input_value > max_value) {
    return(paste(field_name, "must be no more than", max_value))
  }
  
  return(NULL)
}

validate_email_input <- function(input_value, field_name) {
  if (is.null(input_value) || trimws(input_value) == "") {
    return(NULL)  # Allow empty for optional email fields
  }
  
  email_pattern <- "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
  if (!grepl(email_pattern, input_value)) {
    return(paste(field_name, "must be a valid email address"))
  }
  
  return(NULL)
}

validate_dropdown_selection <- function(input_value, field_name, valid_choices = NULL) {
  if (is.null(input_value) || input_value == "") {
    return(paste(field_name, "must be selected"))
  }
  
  if (!is.null(valid_choices) && !input_value %in% valid_choices) {
    return(paste(field_name, "must be one of:", paste(valid_choices, collapse = ", ")))
  }
  
  return(NULL)
}

# Enhanced validation setup with pre-built validators
setup_enhanced_form_validation <- function(input_validator, validation_config) {
  # validation_config format:
  # list(
  #   field_id = list(type = "text", required = TRUE, min_length = 3),
  #   email_field = list(type = "email", required = FALSE),
  #   role_field = list(type = "dropdown", required = TRUE, choices = c("ADMIN", "EDITOR"))
  # )
  
  for (field_id in names(validation_config)) {
    config <- validation_config[[field_id]]
    field_type <- config$type
    
    if (field_type == "text") {
      if (config$required %||% FALSE) {
        input_validator$add_rule(field_id, sv_required())
      }
      
      min_len <- config$min_length %||% 1
      input_validator$add_rule(field_id, function(value) {
        validate_required_text_input(value, field_id, min_len)
      })
      
    } else if (field_type == "email") {
      if (config$required %||% FALSE) {
        input_validator$add_rule(field_id, sv_required())
      }
      
      input_validator$add_rule(field_id, function(value) {
        validate_email_input(value, field_id)
      })
      
    } else if (field_type == "dropdown") {
      if (config$required %||% FALSE) {
        input_validator$add_rule(field_id, sv_required())
      }
      
      choices <- config$choices
      input_validator$add_rule(field_id, function(value) {
        validate_dropdown_selection(value, field_id, choices)
      })
      
    } else if (field_type == "numeric") {
      if (config$required %||% FALSE) {
        input_validator$add_rule(field_id, sv_required())
      }
      
      min_val <- config$min_value %||% 0
      max_val <- config$max_value
      input_validator$add_rule(field_id, function(value) {
        validate_numeric_input(value, field_id, min_val, max_val)
      })
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

# =============================================================================
# MODAL DIALOG STANDARDIZATION (Phase 2A - High Priority)
# =============================================================================

# Standard edit modal for entity CRUD operations
# If footer is provided, it overrides the default footer generation
create_edit_modal <- function(title, content = NULL, size = "m", save_button_id = NULL, cancel_button_id = NULL, 
                             save_button_label = "Update", save_button_icon = "check", 
                             save_button_class = "btn-warning", footer = NULL, easyClose = FALSE, ...) {
  # Generate default footer if not provided
  modal_footer <- if (!is.null(footer)) {
    footer
  } else if (!is.null(save_button_id)) {
    div(
      class = "d-flex justify-content-end gap-2",
      if (!is.null(cancel_button_id)) {
        actionButton(cancel_button_id, "Cancel", class = "btn btn-secondary")
      } else {
        modalButton("Cancel")
      },
      actionButton(save_button_id, save_button_label,
                  icon = icon(save_button_icon),
                  class = paste("btn", save_button_class))
    )
  } else {
    modalButton("Close")
  }
  
  modalDialog(
    title = tagList(bs_icon("pencil"), " ", title),
    size = size,
    easyClose = easyClose,
    content,
    ...,
    footer = modal_footer
  )
}

# Standard create modal for new entities
# If footer is provided, it overrides the default footer generation
create_create_modal <- function(title, content = NULL, size = "m", save_button_id = NULL, cancel_button_id = NULL,
                               save_button_label = "Create", save_button_icon = "plus",
                               save_button_class = "btn-success", footer = NULL, easyClose = FALSE, ...) {
  # Generate default footer if not provided
  modal_footer <- if (!is.null(footer)) {
    footer
  } else if (!is.null(save_button_id)) {
    div(
      class = "d-flex justify-content-end gap-2",
      if (!is.null(cancel_button_id)) {
        actionButton(cancel_button_id, "Cancel", class = "btn btn-secondary")
      } else {
        modalButton("Cancel")
      },
      actionButton(save_button_id, save_button_label,
                  icon = icon(save_button_icon),
                  class = paste("btn", save_button_class))
    )
  } else {
    modalButton("Close")
  }
  
  modalDialog(
    title = tagList(bs_icon("plus-circle"), " ", title),
    size = size,
    easyClose = easyClose,
    content,
    ...,
    footer = modal_footer
  )
}

# Standard view modal for displaying read-only information
# Used for info dialogs, warnings, export confirmations, comments, etc.
create_view_modal <- function(title, content = NULL, size = "m", footer = NULL, easyClose = TRUE, ...) {
  modal_footer <- if (!is.null(footer)) {
    footer
  } else {
    modalButton("Close")
  }
  
  modalDialog(
    title = title,
    size = size,
    easyClose = easyClose,
    content,
    ...,
    footer = modal_footer
  )
}

# Standard delete confirmation modal with enhanced warning
# Supports two calling conventions:
# 1. Standard: create_delete_confirmation_modal(entity_type, entity_name, confirm_button_id, ...)
# 2. Custom: create_delete_confirmation_modal(title = ..., content = ..., footer = ..., size = ...)
create_delete_confirmation_modal <- function(entity_type = NULL, entity_name = NULL, confirm_button_id = NULL, 
                                           additional_info = NULL, warning_message = NULL,
                                           title = NULL, content = NULL, footer = NULL, size = "m", ...) {
  # Custom API: use provided title, content, and footer directly
  if (!is.null(title) && !is.null(content)) {
    return(modalDialog(
      title = title,
      content,
      ...,
      footer = if (!is.null(footer)) footer else modalButton("Close"),
      easyClose = FALSE,
      size = size
    ))
  }
  
  # Standard API: generate content from entity_type and entity_name
  default_warning <- "This action cannot be undone!"
  warning_text <- if (!is.null(warning_message)) warning_message else default_warning
  
  generated_content <- tagList(
    tags$div(class = "alert alert-danger",
      tags$strong("Warning: "), warning_text
    ),
    tags$p(paste("Are you sure you want to delete this", tolower(entity_type %||% "item"), "?")),
    tags$hr(),
    tags$dl(
      tags$dt(paste(entity_type %||% "Item", "Name:")),
      tags$dd(tags$strong(entity_name %||% ""))
    )
  )
  
  # Add additional info if provided
  if (!is.null(additional_info)) {
    generated_content <- tagList(generated_content, additional_info)
  }
  
  modalDialog(
    title = tagList(bs_icon("exclamation-triangle", class = "text-danger"), " Confirm Deletion"),
    generated_content,
    footer = if (!is.null(footer)) {
      footer
    } else if (!is.null(confirm_button_id)) {
      tagList(
        actionButton(confirm_button_id, paste("Delete", entity_type %||% "Item"),
                    icon = bs_icon("trash"),
                    class = "btn-danger"),
        modalButton("Cancel")
      )
    } else {
      modalButton("Close")
    },
    easyClose = FALSE,
    size = size
  )
}

# Standard bulk upload modal for Excel/CSV files
create_bulk_upload_modal <- function(upload_type, file_input_id, template_download_id, 
                                   process_button_id, allowed_extensions = c("xlsx", "xls"),
                                   template_filename = NULL) {
  extension_text <- paste(allowed_extensions, collapse = ", ")
  
  modalDialog(
    title = tagList(bs_icon("upload"), " Bulk Upload ", upload_type),
    size = "l",
    easyClose = FALSE,
    
    tagList(
      # Instructions
      div(class = "alert alert-info",
        tags$h6("Upload Instructions:", class = "mb-2"),
        tags$ul(
          tags$li(paste("File format:", extension_text)),
          tags$li("Required columns: Username, Role"),
          tags$li("Optional columns: Department"),
          tags$li("Download template below for correct format")
        )
      ),
      
      # Template download
      if (!is.null(template_download_id)) {
        div(class = "mb-3",
          tags$label("1. Download Template", class = "form-label fw-bold"),
          br(),
          downloadButton(template_download_id, 
                        label = if (!is.null(template_filename)) template_filename else paste("Download", upload_type, "Template"),
                        icon = bs_icon("download"),
                        class = "btn btn-outline-primary btn-sm")
        )
      },
      
      # File upload
      div(class = "mb-3",
        tags$label("2. Select File to Upload", class = "form-label fw-bold"),
        fileInput(file_input_id, NULL,
                 accept = paste0(".", allowed_extensions),
                 width = "100%")
      ),
      
      # Results area
      div(id = "upload_results_area",
        uiOutput("upload_results")
      )
    ),
    
    footer = div(
      class = "d-flex justify-content-end gap-2",
      modalButton("Close"),
      actionButton(process_button_id, "Process Upload",
                  icon = bs_icon("upload"),
                  class = "btn btn-success")
    )
  )
}

# Standard export completion modal
create_export_modal <- function(filename, download_button_id, entity_type = "data", 
                               success_message = NULL) {
  default_message <- paste("Your", entity_type, "export is ready for download.")
  message_text <- if (!is.null(success_message)) success_message else default_message
  
  modalDialog(
    title = tagList(bs_icon("download"), " Export Complete"),
    size = "m",
    easyClose = TRUE,
    
    tagList(
      div(class = "alert alert-success",
        tags$h6("Export Successful!", class = "mb-2"),
        tags$p(message_text, class = "mb-0")
      ),
      
      div(class = "text-center mt-3",
        downloadButton(download_button_id,
                      label = paste("Download", filename),
                      icon = bs_icon("download"),
                      class = "btn btn-primary btn-lg")
      ),
      
      div(class = "text-muted text-center mt-3",
        tags$small("File will be downloaded to your default Downloads folder")
      )
    ),
    
    footer = div(
      class = "d-flex justify-content-center",
      modalButton("Close", class = "btn btn-secondary")
    )
  )
}

# Standard loading state management
show_loading_state <- function(button_id, loading = TRUE, loading_text = "Loading...", 
                              default_text = "Save", default_icon = "check") {
  if (loading) {
    shinyjs::addClass(id = button_id, class = "disabled")
    shinyjs::html(id = button_id, html = paste0('<i class="fa fa-spinner fa-spin"></i> ', loading_text))
  } else {
    shinyjs::removeClass(id = button_id, class = "disabled")
    icon_html <- if (!is.null(default_icon)) paste0('<i class="bi bi-', default_icon, '"></i> ') else ""
    shinyjs::html(id = button_id, html = paste0(icon_html, default_text))
  }
}

# Standard modal form field generators
create_text_input_field <- function(input_id, label, value = "", placeholder = "", required = FALSE) {
  required_indicator <- if (required) tags$span("*", class = "text-danger") else ""
  
  div(class = "mb-3",
    tags$label(tagList(label, required_indicator), class = "form-label fw-bold"),
    textInput(input_id, NULL,
             value = value,
             placeholder = placeholder,
             width = "100%")
  )
}

create_select_input_field <- function(input_id, label, choices, selected = NULL, required = FALSE) {
  required_indicator <- if (required) tags$span("*", class = "text-danger") else ""
  
  div(class = "mb-3",
    tags$label(tagList(label, required_indicator), class = "form-label fw-bold"),
    selectInput(input_id, NULL,
               choices = choices,
               selected = selected,
               width = "100%")
  )
}

create_textarea_input_field <- function(input_id, label, value = "", placeholder = "", 
                                       rows = 3, required = FALSE) {
  required_indicator <- if (required) tags$span("*", class = "text-danger") else ""
  
  div(class = "mb-3",
    tags$label(tagList(label, required_indicator), class = "form-label fw-bold"),
    textAreaInput(input_id, NULL,
                 value = value,
                 placeholder = placeholder,
                 rows = rows,
                 width = "100%")
  )
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

# =============================================================================
# WEBSOCKET OBSERVER CONSOLIDATION (Phase 2B - Medium Priority)
# =============================================================================

# Enhanced WebSocket observer setup that replaces all legacy patterns
setup_websocket_observers <- function(input, load_data_func, module_name, event_types = NULL) {
  # Universal CRUD Manager refresh observer (Primary)
  observeEvent(input$crud_refresh, {
    if (!is.null(input$crud_refresh)) {
      cat("🔄 Universal CRUD refresh triggered for", module_name, "\n")
      load_data_func()
    }
  })
  
  # Legacy WebSocket observer (Fallback - will be deprecated)
  if (!is.null(event_types)) {
    observeEvent(input$websocket_event, {
      if (!is.null(input$websocket_event)) {
        event_data <- input$websocket_event
        cat("📡 Legacy WebSocket event received for", module_name, ":", event_data$type, "\n")
        
        # Check if event type matches this module
        if (any(sapply(event_types, function(pattern) startsWith(event_data$type, pattern)))) {
          load_data_func()
        }
      }
    })
  }
}

# Standard WebSocket event observer setup (Deprecated - use setup_websocket_observers instead)
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

# Simplified WebSocket observer for modules using Universal CRUD Manager only
setup_universal_crud_observer <- function(input, load_data_func, module_name, debug = TRUE) {
  observeEvent(input$crud_refresh, {
    if (!is.null(input$crud_refresh)) {
      if (debug) {
        cat("🔄", module_name, "refresh triggered via Universal CRUD Manager\n")
      }
      load_data_func()
    }
  })
}

# Environment variable helpers
get_api_endpoint <- function(endpoint_name, default_path) {
  base_url <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  path <- Sys.getenv(endpoint_name, default_path)
  paste0(base_url, path)
}