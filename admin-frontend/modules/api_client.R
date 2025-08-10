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
create_package <- function(package_data) {
  tryCatch({
    response <- httr2::request(paste0(get_packages_endpoint(), "/")) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(package_data) |>
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
update_package <- function(id, package_data) {
  tryCatch({
    response <- httr2::request(paste0(get_packages_endpoint(), "/", id)) |>
      httr2::req_method("PUT") |>
      httr2::req_body_json(package_data) |>
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

# Create package item
create_package_item <- function(package_id, item_data) {
  tryCatch({
    response <- httr2::request(paste0(get_packages_endpoint(), "/", package_id, "/items")) |>
      httr2::req_method("POST") |>
      httr2::req_body_json(item_data) |>
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

