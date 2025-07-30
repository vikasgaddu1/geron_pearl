# API Client Module for PEARL Backend Communication

library(httr2)

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