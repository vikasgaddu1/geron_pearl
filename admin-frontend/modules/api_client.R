# API Client Module for PEARL Backend Communication

library(httr)

# API Configuration
BASE_URL <- "http://localhost:8000"
STUDIES_ENDPOINT <- paste0(BASE_URL, "/api/v1/studies")

# Get all studies
get_studies <- function() {
  tryCatch({
    response <- GET(STUDIES_ENDPOINT)
    if (status_code(response) == 200) {
      content(response, "parsed")
    } else {
      list(error = paste("HTTP", status_code(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Get single study by ID
get_study <- function(id) {
  tryCatch({
    response <- GET(paste0(STUDIES_ENDPOINT, "/", id))
    if (status_code(response) == 200) {
      content(response, "parsed")
    } else {
      list(error = paste("HTTP", status_code(response)))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Create new study
create_study <- function(study_data) {
  tryCatch({
    response <- POST(
      STUDIES_ENDPOINT,
      body = study_data,
      encode = "json",
      content_type_json()
    )
    if (status_code(response) == 201) {
      content(response, "parsed")
    } else {
      list(error = paste("HTTP", status_code(response), "-", content(response, "text")))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Update existing study
update_study <- function(id, study_data) {
  tryCatch({
    response <- PUT(
      paste0(STUDIES_ENDPOINT, "/", id),
      body = study_data,
      encode = "json",
      content_type_json()
    )
    if (status_code(response) == 200) {
      content(response, "parsed")
    } else {
      list(error = paste("HTTP", status_code(response), "-", content(response, "text")))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}

# Delete study
delete_study <- function(id) {
  tryCatch({
    response <- DELETE(paste0(STUDIES_ENDPOINT, "/", id))
    if (status_code(response) == 200) {
      content(response, "parsed")
    } else {
      list(error = paste("HTTP", status_code(response), "-", content(response, "text")))
    }
  }, error = function(e) {
    list(error = e$message)
  })
}