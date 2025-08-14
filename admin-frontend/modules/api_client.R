# API Client Module for PEARL Backend Communication

library(httr2)
library(jsonlite)

# Get the studies endpoint dynamically
get_studies_endpoint <- function() {
  api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  api_path <- Sys.getenv("PEARL_API_STUDIES_PATH", "/api/v1/studies")
  return(paste0(api_base, api_path))
}

# Get all studies
get_studies <- function() {
  tryCatch({
    response <- httr2::request(get_studies_endpoint()) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Get single study by ID
get_study <- function(id) {
  tryCatch({
    response <- httr2::request(paste0(get_studies_endpoint(), "/", id)) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Create new study
create_study <- function(study_data) {
  tryCatch({
    response <- httr2::request(get_studies_endpoint()) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(study_data) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 201) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Update existing study
update_study <- function(id, study_data) {
  tryCatch({
    response <- httr2::request(paste0(get_studies_endpoint(), "/", id)) |>
      httr2::req_method("PUT") |>
      httr2::req_body_json(study_data) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Delete study
delete_study <- function(id) {
  tryCatch({
    response <- httr2::request(paste0(get_studies_endpoint(), "/", id)) |>
      httr2::req_method("DELETE") |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# ===== DATABASE RELEASES FUNCTIONS =====

# Get the database releases endpoint dynamically
get_database_releases_endpoint <- function() {
  api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  return(paste0(api_base, "/api/v1/database-releases"))
}

# Get all database releases
get_database_releases <- function() {
  tryCatch({
    response <- httr2::request(get_database_releases_endpoint()) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Get single database release by ID
get_database_release <- function(id) {
  tryCatch({
    response <- httr2::request(paste0(get_database_releases_endpoint(), "/", id)) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Create new database release
create_database_release <- function(release_data) {
  tryCatch({
    response <- httr2::request(get_database_releases_endpoint()) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(release_data) |>
      httr2::req_error(is_error = ~ FALSE) |>  # Don't throw on HTTP errors
      httr2::req_perform()
    if (httr2::resp_status(response) == 201) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Update existing database release
update_database_release <- function(id, release_data) {
  tryCatch({
    response <- httr2::request(paste0(get_database_releases_endpoint(), "/", id)) |>
      httr2::req_method("PUT") |>
      httr2::req_body_json(release_data) |>
      httr2::req_error(is_error = ~ FALSE) |>  # Don't throw on HTTP errors
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Delete database release
delete_database_release <- function(id) {
  tryCatch({
    response <- httr2::request(paste0(get_database_releases_endpoint(), "/", id)) |>
      httr2::req_method("DELETE") |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# ===== REPORTING EFFORTS FUNCTIONS =====

# Get the reporting efforts endpoint dynamically
get_reporting_efforts_endpoint <- function() {
  api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  return(paste0(api_base, "/api/v1/reporting-efforts"))
}

# Get all reporting efforts
get_reporting_efforts <- function() {
  tryCatch({
    response <- httr2::request(get_reporting_efforts_endpoint()) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Get single reporting effort by ID
get_reporting_effort <- function(id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_efforts_endpoint(), "/", id)) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Create new reporting effort
create_reporting_effort <- function(effort_data) {
  tryCatch({
    response <- httr2::request(get_reporting_efforts_endpoint()) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(effort_data) |>
      httr2::req_error(is_error = ~ FALSE) |>  # Don't throw on HTTP errors
      httr2::req_perform()
    if (httr2::resp_status(response) == 201) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Update existing reporting effort
update_reporting_effort <- function(id, effort_data) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_efforts_endpoint(), "/", id)) |>
      httr2::req_method("PUT") |>
      httr2::req_body_json(effort_data) |>
      httr2::req_error(is_error = ~ FALSE) |>  # Don't throw on HTTP errors
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Delete reporting effort
delete_reporting_effort <- function(id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_efforts_endpoint(), "/", id)) |>
      httr2::req_method("DELETE") |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# ===== TEXT ELEMENTS FUNCTIONS =====

# Get the text elements endpoint dynamically
get_text_elements_endpoint <- function() {
  api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  return(paste0(api_base, "/api/v1/text-elements"))
}

# Get the text elements endpoint with trailing slash for POST operations
get_text_elements_endpoint_post <- function() {
  api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  return(paste0(api_base, "/api/v1/text-elements/"))
}

# Get all text elements
get_text_elements <- function() {
  tryCatch({
    response <- httr2::request(get_text_elements_endpoint_post()) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Get single text element by ID
get_text_element <- function(id) {
  tryCatch({
    response <- httr2::request(paste0(get_text_elements_endpoint_post(), id)) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Create new text element
create_text_element <- function(element_data) {
  tryCatch({
    response <- httr2::request(get_text_elements_endpoint_post()) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(element_data) |>
      httr2::req_error(is_error = function(resp) FALSE) |>  # Don't throw errors, let us handle
      httr2::req_perform()
    
    if (httr2::resp_status(response) == 201) {
      httr2::resp_body_json(response)
    } else {
      # Include response body for error details
      response_body <- tryCatch(httr2::resp_body_string(response), error = function(e) "")
      list(error = paste("HTTP", httr2::resp_status(response), "-", response_body))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Update existing text element
update_text_element <- function(id, element_data) {
  tryCatch({
    response <- httr2::request(paste0(get_text_elements_endpoint(), "/", id)) |>
      httr2::req_method("PUT") |>
      httr2::req_body_json(element_data) |>
      httr2::req_error(is_error = function(resp) FALSE) |>  # Don't throw errors, let us handle
      httr2::req_perform()
      
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      # Include response body for error details
      response_body <- tryCatch(httr2::resp_body_string(response), error = function(e) "")
      list(error = paste("HTTP", httr2::resp_status(response), "-", response_body))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Delete text element
delete_text_element <- function(id) {
  tryCatch({
    response <- httr2::request(paste0(get_text_elements_endpoint_post(), id)) |>
      httr2::req_method("DELETE") |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# ===== PACKAGES FUNCTIONS =====

# Get the packages endpoint dynamically
get_packages_endpoint <- function() {
  api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  return(paste0(api_base, "/api/v1/packages"))
}

# Get all packages
get_packages <- function() {
  tryCatch({
    response <- httr2::request(get_packages_endpoint()) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Get single package by ID
get_package <- function(id) {
  tryCatch({
    response <- httr2::request(paste0(get_packages_endpoint(), "/", id)) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Create new package
create_package <- function(package_name) {
  tryCatch({
    response <- httr2::request(get_packages_endpoint()) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(list(package_name = package_name)) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 201) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Update existing package
update_package <- function(id, package_name) {
  tryCatch({
    response <- httr2::request(paste0(get_packages_endpoint(), "/", id)) |>
      httr2::req_method("PUT") |>
      httr2::req_body_json(list(package_name = package_name)) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Delete package
delete_package <- function(id) {
  tryCatch({
    response <- httr2::request(paste0(get_packages_endpoint(), "/", id)) |>
      httr2::req_method("DELETE") |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Get package items
get_package_items <- function(package_id) {
  tryCatch({
    response <- httr2::request(paste0(get_packages_endpoint(), "/", package_id, "/items")) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Create package item - supports both TLF and Dataset types
create_package_item <- function(package_id, item_type, item_subtype, item_code, 
                               tlf_details = NULL, dataset_details = NULL, 
                               footnotes = list(), acronyms = list()) {
  tryCatch({
    # Build request body
    body <- list(
      package_id = as.integer(package_id),
      item_type = item_type,
      item_subtype = item_subtype,
      item_code = item_code
    )
    
    # Add type-specific details
    if (!is.null(tlf_details)) {
      body$tlf_details <- tlf_details
    }
    if (!is.null(dataset_details)) {
      body$dataset_details <- dataset_details
    }
    
    # Add footnotes and acronyms if provided
    if (length(footnotes) > 0) {
      body$footnotes <- footnotes
    }
    if (length(acronyms) > 0) {
      body$acronyms <- acronyms
    }
    
    response <- httr2::request(paste0(get_packages_endpoint(), "/", package_id, "/items")) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(body) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 201) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Update package item - supports both TLF and Dataset types
update_package_item <- function(item_id, item_type, item_subtype, item_code, 
                                tlf_details = NULL, dataset_details = NULL,
                                footnotes = NULL, acronyms = NULL) {
  tryCatch({
    # Build the request body
    body_data <- list(
      item_type = item_type,
      item_subtype = item_subtype,
      item_code = item_code
    )
    
    # Add type-specific details
    if (item_type == "TLF" && !is.null(tlf_details)) {
      body_data$tlf_details <- tlf_details
      
      if (!is.null(footnotes)) {
        body_data$footnotes <- footnotes
      }
      if (!is.null(acronyms)) {
        body_data$acronyms <- acronyms
      }
    } else if (item_type == "Dataset" && !is.null(dataset_details)) {
      body_data$dataset_details <- dataset_details
    }
    
    response <- httr2::request(paste0(get_packages_endpoint(), "/items/", item_id)) |>
      httr2::req_method("PUT") |>
      httr2::req_body_json(body_data) |>
      httr2::req_perform()
      
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      # Include response body for error details
      response_body <- tryCatch(httr2::resp_body_string(response), error = function(e) "")
      list(error = paste("HTTP", httr2::resp_status(response), "-", response_body))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Delete package item
delete_package_item <- function(item_id) {
  tryCatch({
    response <- httr2::request(paste0(get_packages_endpoint(), "/items/", item_id)) |>
      httr2::req_method("DELETE") |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# ===== USERS FUNCTIONS =====

# Get the users endpoint dynamically
get_users_endpoint <- function() {
  api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  return(paste0(api_base, "/api/v1/users"))
}

# Get all users
get_users <- function() {
  tryCatch({
    response <- httr::GET(paste0(get_users_endpoint(), "/"))
    
    if (httr::status_code(response) == 200) {
      content <- httr::content(response, "text", encoding = "UTF-8")
      if (content == "" || content == "[]") {
        return(list())
      }
      users <- jsonlite::fromJSON(content, simplifyVector = FALSE)
      return(users)
    } else {
      return(list(error = paste("HTTP", httr::status_code(response))))
    }
  }, error = function(e) {
    return(list(error = paste("Failed to fetch users:", e$message)))
  })
}

# Get user by ID
get_user_by_id <- function(user_id) {
  tryCatch({
    response <- httr::GET(paste0(get_users_endpoint(), "/", user_id))
    
    if (httr::status_code(response) == 200) {
      content <- httr::content(response, "text", encoding = "UTF-8")
      user <- jsonlite::fromJSON(content)
      return(user)
    } else {
      return(list(error = paste("HTTP", httr::status_code(response))))
    }
  }, error = function(e) {
    return(list(error = paste("Failed to fetch user:", e$message)))
  })
}

# Create a new user
create_user <- function(username, role, department = NULL) {
  payload <- list(
    username = username,
    role = role
  )
  
  # Add department if provided
  if (!is.null(department) && department != "") {
    payload$department <- department
  }
  
  tryCatch({
    response <- httr::POST(
      paste0(get_users_endpoint(), "/"),
      body = jsonlite::toJSON(payload, auto_unbox = TRUE),
      httr::content_type_json()
    )
    
    if (httr::status_code(response) == 200 || httr::status_code(response) == 201) {
      content <- httr::content(response, "text", encoding = "UTF-8")
      user <- jsonlite::fromJSON(content)
      return(user)
    } else {
      error_content <- httr::content(response, "text", encoding = "UTF-8")
      return(list(error = paste("HTTP", httr::status_code(response), "-", error_content)))
    }
  }, error = function(e) {
    return(list(error = paste("Failed to create user:", e$message)))
  })
}

# Update an existing user
update_user <- function(user_id, username, role, department = NULL) {
  payload <- list(
    username = username,
    role = role
  )
  
  # Add department if provided
  if (!is.null(department)) {
    payload$department <- if (department == "") "" else department
  }
  
  tryCatch({
    response <- httr::PUT(
      paste0(get_users_endpoint(), "/", user_id),
      body = jsonlite::toJSON(payload, auto_unbox = TRUE),
      httr::content_type_json()
    )
    
    if (httr::status_code(response) == 200) {
      content <- httr::content(response, "text", encoding = "UTF-8")
      user <- jsonlite::fromJSON(content)
      return(user)
    } else {
      error_content <- httr::content(response, "text", encoding = "UTF-8")
      return(list(error = paste("HTTP", httr::status_code(response), "-", error_content)))
    }
  }, error = function(e) {
    return(list(error = paste("Failed to update user:", e$message)))
  })
}

# Delete a user
delete_user <- function(user_id) {
  tryCatch({
    response <- httr::DELETE(paste0(get_users_endpoint(), "/", user_id))
    
    if (httr::status_code(response) == 200) {
      return(list(success = TRUE))
    } else {
      error_content <- httr::content(response, "text", encoding = "UTF-8")
      return(list(error = paste("HTTP", httr::status_code(response), "-", error_content)))
    }
  }, error = function(e) {
    return(list(error = paste("Failed to delete user:", e$message)))
  })
}

# ===== REPORTING EFFORT ITEMS FUNCTIONS =====

# Get the reporting effort items endpoint dynamically
get_reporting_effort_items_endpoint <- function() {
  api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  return(paste0(api_base, "/api/v1/reporting-effort-items"))
}

# Get all reporting effort items
get_reporting_effort_items <- function() {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/")) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Get reporting effort items by reporting effort ID
get_reporting_effort_items_by_effort <- function(reporting_effort_id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/by-effort/", reporting_effort_id)) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Get single reporting effort item by ID
get_reporting_effort_item <- function(id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/", id)) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Create new reporting effort item
create_reporting_effort_item <- function(item_data) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/")) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(item_data) |>
      httr2::req_error(is_error = ~ FALSE) |>  # Don't throw on HTTP errors
      httr2::req_perform()
    if (httr2::resp_status(response) == 201) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Update existing reporting effort item
update_reporting_effort_item <- function(id, item_data) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/", id)) |>
      httr2::req_method("PUT") |>
      httr2::req_body_json(item_data) |>
      httr2::req_error(is_error = ~ FALSE) |>  # Don't throw on HTTP errors
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Delete reporting effort item
delete_reporting_effort_item <- function(id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/", id)) |>
      httr2::req_method("DELETE") |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Bulk upload TLF items
bulk_upload_tlf_items <- function(reporting_effort_id, file_path) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/", reporting_effort_id, "/bulk-tlf")) |>
      httr2::req_method("POST") |>
      httr2::req_body_multipart(file = curl::form_file(file_path)) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Bulk upload Dataset items
bulk_upload_dataset_items <- function(reporting_effort_id, file_path) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/", reporting_effort_id, "/bulk-dataset")) |>
      httr2::req_method("POST") |>
      httr2::req_body_multipart(file = curl::form_file(file_path)) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Copy items from package
copy_items_from_package <- function(reporting_effort_id, package_id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/", reporting_effort_id, "/copy-from-package")) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(list(package_id = as.integer(package_id))) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Copy TLF items from package
copy_tlf_items_from_package <- function(reporting_effort_id, package_id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/", reporting_effort_id, "/copy-tlf-from-package")) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(list(package_id = as.integer(package_id))) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Copy Dataset items from package
copy_dataset_items_from_package <- function(reporting_effort_id, package_id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/", reporting_effort_id, "/copy-dataset-from-package")) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(list(package_id = as.integer(package_id))) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Copy items from reporting effort
copy_items_from_reporting_effort <- function(reporting_effort_id, source_reporting_effort_id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/", reporting_effort_id, "/copy-from-reporting-effort")) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(list(source_reporting_effort_id = as.integer(source_reporting_effort_id))) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Copy TLF items from reporting effort
copy_tlf_items_from_reporting_effort <- function(reporting_effort_id, source_reporting_effort_id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/", reporting_effort_id, "/copy-tlf-from-reporting-effort")) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(list(source_reporting_effort_id = as.integer(source_reporting_effort_id))) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Copy Dataset items from reporting effort
copy_dataset_items_from_reporting_effort <- function(reporting_effort_id, source_reporting_effort_id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_items_endpoint(), "/", reporting_effort_id, "/copy-dataset-from-reporting-effort")) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(list(source_reporting_effort_id = as.integer(source_reporting_effort_id))) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# ===== REPORTING EFFORT TRACKER FUNCTIONS =====

# Get the reporting effort tracker endpoint dynamically
get_reporting_effort_tracker_endpoint <- function() {
  api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  return(paste0(api_base, "/api/v1/reporting-effort-tracker"))
}

# Get all tracker entries
get_reporting_effort_tracker <- function() {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_tracker_endpoint(), "/")) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Get single tracker entry by ID
get_reporting_effort_tracker_by_id <- function(tracker_id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_tracker_endpoint(), "/", tracker_id)) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Update tracker entry
update_reporting_effort_tracker <- function(tracker_id, tracker_data) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_tracker_endpoint(), "/", tracker_id)) |>
      httr2::req_method("PUT") |>
      httr2::req_body_json(tracker_data) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Assign programmer to tracker entry
assign_programmer_to_tracker <- function(tracker_id, assignment_data) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_tracker_endpoint(), "/", tracker_id, "/assign-programmer")) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(assignment_data) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Unassign programmer from tracker entry
unassign_programmer_from_tracker <- function(tracker_id, assignment_data) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_tracker_endpoint(), "/", tracker_id, "/unassign-programmer")) |>
      httr2::req_method("DELETE") |>
      httr2::req_body_json(assignment_data) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Bulk assign programmers
bulk_assign_programmers <- function(assignment_data) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_tracker_endpoint(), "/bulk-assign")) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(assignment_data) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Bulk status update
bulk_status_update <- function(status_data) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_tracker_endpoint(), "/bulk-status-update")) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(status_data) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Get workload summary
get_workload_summary <- function() {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_tracker_endpoint(), "/workload-summary")) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Get workload for specific programmer
get_programmer_workload <- function(programmer_id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_tracker_endpoint(), "/workload/", programmer_id)) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Export tracker data
export_tracker_data <- function(reporting_effort_id) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_tracker_endpoint(), "/export/", reporting_effort_id)) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Import tracker data
import_tracker_data <- function(reporting_effort_id, file_path) {
  tryCatch({
    response <- httr2::request(paste0(get_reporting_effort_tracker_endpoint(), "/import/", reporting_effort_id)) |>
      httr2::req_method("POST") |>
      httr2::req_body_multipart(file = curl::form_file(file_path)) |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Database Backup Functions
get_database_backup_endpoint <- function() {
  api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  paste0(api_base, "/api/v1/database-backup")
}

# Create database backup
create_database_backup <- function(description = NULL) {
  tryCatch({
    request <- httr2::request(paste0(get_database_backup_endpoint(), "/create")) |>
      httr2::req_method("POST") |>
      httr2::req_headers("X-User-Role" = "admin")
    
    if (!is.null(description)) {
      request <- request |> httr2::req_body_json(list(description = description))
    }
    
    response <- request |> 
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    
    if (httr2::resp_status(response) == 200) {
      list(success = TRUE, data = httr2::resp_body_json(response))
    } else {
      list(success = FALSE, error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(success = FALSE, error = e$message)
  })
}

# List database backups
list_database_backups <- function() {
  tryCatch({
    response <- httr2::request(paste0(get_database_backup_endpoint(), "/list")) |>
      httr2::req_headers("X-User-Role" = "admin") |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    
    if (httr2::resp_status(response) == 200) {
      list(success = TRUE, data = httr2::resp_body_json(response))
    } else {
      list(success = FALSE, error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(success = FALSE, error = e$message)
  })
}

# Delete database backup
delete_database_backup <- function(filename) {
  tryCatch({
    response <- httr2::request(paste0(get_database_backup_endpoint(), "/delete/", filename)) |>
      httr2::req_method("DELETE") |>
      httr2::req_headers("X-User-Role" = "admin") |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    
    if (httr2::resp_status(response) == 200) {
      list(success = TRUE, data = httr2::resp_body_json(response))
    } else {
      list(success = FALSE, error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(success = FALSE, error = e$message)
  })
}

# Restore database backup
restore_database_backup <- function(filename) {
  tryCatch({
    response <- httr2::request(paste0(get_database_backup_endpoint(), "/restore/", filename)) |>
      httr2::req_method("POST") |>
      httr2::req_headers("X-User-Role" = "admin") |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    
    if (httr2::resp_status(response) == 200) {
      list(success = TRUE, data = httr2::resp_body_json(response))
    } else {
      list(success = FALSE, error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(success = FALSE, error = e$message)
  })
}

# Get backup status
get_database_backup_status <- function() {
  tryCatch({
    response <- httr2::request(paste0(get_database_backup_endpoint(), "/status")) |>
      httr2::req_headers("X-User-Role" = "admin") |>
      httr2::req_error(is_error = ~ FALSE) |>
      httr2::req_perform()
    
    if (httr2::resp_status(response) == 200) {
      list(success = TRUE, data = httr2::resp_body_json(response))
    } else {
      list(success = FALSE, error = paste("HTTP", httr2::resp_status(response), "-", httr2::resp_body_string(response)))
    }
  }, error = function(e) {
    list(success = FALSE, error = e$message)
  })
}

# Health check function
health_check <- function() {
  api_base <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
  health_path <- Sys.getenv("PEARL_API_HEALTH_PATH", "/health")
  
  tryCatch({
    response <- httr2::request(paste0(api_base, health_path)) |> 
      httr2::req_perform()
    if (httr2::resp_status(response) == 200) {
      httr2::resp_body_json(response)
    } else {
      list(error = paste("Health check failed with status:", httr2::resp_status(response)))
    }
  }, error = function(e) {
    list(error = paste("Health check error:", e$message))
  })
}

