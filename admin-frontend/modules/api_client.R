# API Client Module for PEARL Backend Communication

library(httr2)

# API Configuration
BASE_URL <- "http://localhost:8000"
STUDIES_ENDPOINT <- paste0(BASE_URL, "/api/v1/studies")

# Get all studies
get_studies <- function() {
  tryCatch({
    response <- httr2::request(STUDIES_ENDPOINT) |> 
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
    response <- httr2::request(paste0(STUDIES_ENDPOINT, "/", id)) |> 
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
    response <- httr2::request(STUDIES_ENDPOINT) |>
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
    response <- httr2::request(paste0(STUDIES_ENDPOINT, "/", id)) |>
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
    response <- httr2::request(paste0(STUDIES_ENDPOINT, "/", id)) |>
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