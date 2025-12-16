# API utilities for standardized HTTP client operations
# Provides common patterns for API calls with error handling

library(httr2)
library(jsonlite)

# Standard API client with error handling
make_api_request <- function(url, method = "GET", body = NULL, timeout = 30) {
  tryCatch({
    # Build request
    req <- request(url)
    
    # Set timeout
    req <- req_timeout(req, timeout)
    
    # Add body for POST/PUT requests
    if (!is.null(body)) {
      req <- req_body_json(req, body)
    }
    
    # Set method
    if (method == "POST") {
      req <- req_method(req, "POST")
    } else if (method == "PUT") {
      req <- req_method(req, "PUT")
    } else if (method == "DELETE") {
      req <- req_method(req, "DELETE")
    }
    
    # Perform request
    response <- req_perform(req)
    
    # Check status
    if (resp_status(response) >= 200 && resp_status(response) < 300) {
      # Success - try to parse JSON response
      if (resp_has_body(response)) {
        content_type <- resp_content_type(response)
        if (grepl("application/json", content_type)) {
          return(resp_body_json(response))
        } else {
          return(resp_body_string(response))
        }
      } else {
        return(list(success = TRUE))
      }
    } else {
      # HTTP error
      error_body <- if (resp_has_body(response)) {
        tryCatch({
          error_data <- resp_body_json(response)
          if ("detail" %in% names(error_data)) {
            error_data$detail
          } else {
            error_data
          }
        }, error = function(e) {
          resp_body_string(response)
        })
      } else {
        paste("HTTP", resp_status(response))
      }
      
      return(list(error = paste("HTTP", resp_status(response), "-", error_body)))
    }
    
  }, error = function(e) {
    return(list(error = paste("Network error:", e$message)))
  })
}

# GET request helper
api_get <- function(url, timeout = 30) {
  make_api_request(url, "GET", timeout = timeout)
}

# POST request helper
api_post <- function(url, data, timeout = 30) {
  make_api_request(url, "POST", data, timeout = timeout)
}

# PUT request helper
api_put <- function(url, data, timeout = 30) {
  make_api_request(url, "PUT", data, timeout = timeout)
}

# DELETE request helper
api_delete <- function(url, timeout = 30) {
  make_api_request(url, "DELETE", timeout = timeout)
}

# Health check helper
check_api_health <- function(base_url = NULL) {
  if (is.null(base_url)) {
    base_url <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  }
  
  health_url <- paste0(base_url, "/health")
  result <- api_get(health_url, timeout = 5)
  
  if ("error" %in% names(result)) {
    return(list(
      status = "error",
      message = result$error,
      healthy = FALSE
    ))
  } else {
    return(list(
      status = "healthy",
      message = "API is responding",
      healthy = TRUE,
      data = result
    ))
  }
}

# Standard CRUD operations for any entity
crud_operations <- list(
  # Get all entities
  get_all = function(endpoint, skip = 0, limit = 100) {
    url <- paste0(endpoint, "?skip=", skip, "&limit=", limit)
    api_get(url)
  },
  
  # Get single entity
  get_by_id = function(endpoint, id) {
    url <- paste0(endpoint, "/", id)
    api_get(url)
  },
  
  # Create entity
  create = function(endpoint, data) {
    api_post(endpoint, data)
  },
  
  # Update entity
  update = function(endpoint, id, data) {
    url <- paste0(endpoint, "/", id)
    api_put(url, data)
  },
  
  # Delete entity
  delete = function(endpoint, id) {
    url <- paste0(endpoint, "/", id)
    api_delete(url)
  },
  
  # Search entities (if endpoint supports it)
  search = function(endpoint, query) {
    url <- paste0(endpoint, "/search?q=", URLencode(query))
    api_get(url)
  }
)

# Helper to extract error messages from API responses
extract_error_message <- function(api_result) {
  if ("error" %in% names(api_result)) {
    error_msg <- api_result$error
    
    # Try to extract detailed error from HTTP response
    if (grepl("HTTP \\d+ -", error_msg)) {
      # Extract everything after "HTTP xxx - "
      detail_part <- sub(".*HTTP \\d+ - ", "", error_msg)
      
      # Try to parse as JSON
      tryCatch({
        error_data <- jsonlite::fromJSON(detail_part)
        if (is.list(error_data) && "detail" %in% names(error_data)) {
          return(error_data$detail)
        } else if (is.character(error_data)) {
          return(error_data)
        }
      }, error = function(e) {
        # JSON parsing failed, return the detail part as-is
      })
      
      return(detail_part)
    }
    
    return(error_msg)
  }
  
  return("Unknown error")
}

# =============================================================================
# NOTIFICATION STANDARDIZATION (Phase 2A - High Priority)
# =============================================================================

# Helper to convert duration - Shiny expects seconds, but code may pass milliseconds
# If duration > 100, assume milliseconds and convert to seconds
convert_duration <- function(duration) {
  if (duration > 100) {
    return(duration / 1000)  # Convert milliseconds to seconds
  }
  return(duration)  # Already in seconds
}

# Standard success notification
show_success_notification <- function(message, duration = 3) {
  showNotification(
    message,
    type = "message",  # Shiny's valid success type
    duration = convert_duration(duration)
  )
}

# Standard error notification - uses SweetAlert modal for visibility
show_error_notification <- function(message, duration = 5) {
  session <- shiny::getDefaultReactiveDomain()
  if (!is.null(session)) {
    shinyWidgets::sendSweetAlert(
      session = session,
      title = "Error",
      text = message,
      type = "error",
      btn_labels = "OK",
      closeOnClickOutside = TRUE,
      showCloseButton = TRUE
    )
  } else {
    # Fallback to showNotification if no reactive domain
    showNotification(
      message,
      type = "error",
      duration = convert_duration(duration)
    )
  }
}

# Standard warning notification - uses SweetAlert modal for visibility
show_warning_notification <- function(message, duration = 4) {
  session <- shiny::getDefaultReactiveDomain()
  if (!is.null(session)) {
    shinyWidgets::sendSweetAlert(
      session = session,
      title = "Warning",
      text = message,
      type = "warning",
      btn_labels = "OK",
      closeOnClickOutside = TRUE,
      showCloseButton = TRUE
    )
  } else {
    # Fallback to showNotification if no reactive domain
    showNotification(
      message,
      type = "warning",
      duration = convert_duration(duration)
    )
  }
}

# Enhanced validation error notification for API responses - uses SweetAlert modal
show_validation_error_notification <- function(api_result, duration = 8) {
  error_msg <- extract_error_message(api_result)
  session <- shiny::getDefaultReactiveDomain()

  # Special handling for duplicate validation errors
  if (grepl("Duplicate.*are not allowed", error_msg)) {
    if (!is.null(session)) {
      shinyWidgets::sendSweetAlert(
        session = session,
        title = "Duplicate Content Detected",
        text = tags$div(
          tags$p(error_msg),
          tags$small(
            class = "text-muted",
            "Tip: The system compares content ignoring spaces and letter case."
          )
        ),
        type = "error",
        html = TRUE,
        btn_labels = "OK",
        closeOnClickOutside = TRUE,
        showCloseButton = TRUE
      )
    } else {
      showNotification(
        tagList(
          tags$strong("Duplicate Content Detected"),
          tags$br(),
          error_msg,
          tags$br(),
          tags$small("Tip: The system compares content ignoring spaces and letter case.")
        ),
        type = "error",
        duration = convert_duration(duration)
      )
    }
  } else if (grepl("already exists", error_msg)) {
    if (!is.null(session)) {
      shinyWidgets::sendSweetAlert(
        session = session,
        title = "Duplicate Entry",
        text = error_msg,
        type = "error",
        btn_labels = "OK",
        closeOnClickOutside = TRUE,
        showCloseButton = TRUE
      )
    } else {
      showNotification(
        tagList(
          tags$strong("Duplicate Entry"),
          tags$br(),
          error_msg
        ),
        type = "error",
        duration = convert_duration(duration)
      )
    }
  } else {
    show_error_notification(error_msg, duration)
  }
}

# Standard operation notification with entity context
show_operation_notification <- function(operation, entity, success = TRUE, entity_name = NULL) {
  if (success) {
    if (!is.null(entity_name)) {
      message <- paste(entity, "'", entity_name, "'", operation, "successfully")
    } else {
      message <- paste(entity, operation, "successfully")
    }
    show_success_notification(message)
  } else {
    message <- paste("Failed to", operation, tolower(entity))
    show_error_notification(message)
  }
}

# Standard loading notification
show_loading_notification <- function(message = "Loading...", duration = 2) {
  showNotification(
    message,
    type = "message",
    duration = convert_duration(duration)
  )
}

# Helper to show API response notifications (enhanced version)
show_api_notification <- function(api_result, success_message = "Operation completed successfully") {
  if ("error" %in% names(api_result)) {
    show_validation_error_notification(api_result)
    return(FALSE)
  } else {
    if (!is.null(success_message)) {
      show_success_notification(success_message)
    }
    return(TRUE)
  }
}

# Helper to build endpoint URLs from environment variables
build_endpoint_url <- function(endpoint_env_var, default_path) {
  base_url <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  path <- Sys.getenv(endpoint_env_var, default_path)
  paste0(base_url, path)
}

# Validation helpers
validate_required_fields <- function(data, required_fields) {
  errors <- c()
  
  for (field in required_fields) {
    if (!field %in% names(data) || is.null(data[[field]]) || 
        (is.character(data[[field]]) && trimws(data[[field]]) == "")) {
      errors <- c(errors, paste("Field", field, "is required"))
    }
  }
  
  return(errors)
}

# Helper for pagination
create_pagination_info <- function(total_items, current_page = 1, page_size = 25) {
  total_pages <- ceiling(total_items / page_size)
  start_item <- (current_page - 1) * page_size + 1
  end_item <- min(current_page * page_size, total_items)
  
  list(
    total_items = total_items,
    total_pages = total_pages,
    current_page = current_page,
    page_size = page_size,
    start_item = start_item,
    end_item = end_item,
    has_previous = current_page > 1,
    has_next = current_page < total_pages
  )
}