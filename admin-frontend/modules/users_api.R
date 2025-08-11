# Users API Module

# Get API base URL
get_api_base_url <- function() {
  base_url <- Sys.getenv("API_BASE_URL", "http://localhost:8000")
  return(paste0(base_url, "/api/v1"))
}

# Get all users
get_users <- function() {
  api_url <- paste0(get_api_base_url(), "/users/")
  
  tryCatch({
    response <- httr::GET(api_url)
    
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
  api_url <- paste0(get_api_base_url(), "/users/", user_id)
  
  tryCatch({
    response <- httr::GET(api_url)
    
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
create_user <- function(username, role) {
  api_url <- paste0(get_api_base_url(), "/users/")
  
  # Prepare the payload
  payload <- list(
    username = username,
    role = role
  )
  
  tryCatch({
    response <- httr::POST(
      api_url,
      body = jsonlite::toJSON(payload, auto_unbox = TRUE),
      httr::content_type_json()
    )
    
    if (httr::status_code(response) == 200 || httr::status_code(response) == 201) {
      content <- httr::content(response, "text", encoding = "UTF-8")
      user <- jsonlite::fromJSON(content)
      return(user)
    } else {
      # Try to get detailed error message
      error_content <- httr::content(response, "text", encoding = "UTF-8")
      return(list(error = paste("HTTP", httr::status_code(response), "-", error_content)))
    }
  }, error = function(e) {
    return(list(error = paste("Failed to create user:", e$message)))
  })
}

# Update an existing user
update_user <- function(user_id, username, role) {
  api_url <- paste0(get_api_base_url(), "/users/", user_id)
  
  # Prepare the payload
  payload <- list(
    username = username,
    role = role
  )
  
  tryCatch({
    response <- httr::PUT(
      api_url,
      body = jsonlite::toJSON(payload, auto_unbox = TRUE),
      httr::content_type_json()
    )
    
    if (httr::status_code(response) == 200) {
      content <- httr::content(response, "text", encoding = "UTF-8")
      user <- jsonlite::fromJSON(content)
      return(user)
    } else {
      # Try to get detailed error message
      error_content <- httr::content(response, "text", encoding = "UTF-8")
      return(list(error = paste("HTTP", httr::status_code(response), "-", error_content)))
    }
  }, error = function(e) {
    return(list(error = paste("Failed to update user:", e$message)))
  })
}

# Delete a user
delete_user <- function(user_id) {
  api_url <- paste0(get_api_base_url(), "/users/", user_id)
  
  tryCatch({
    response <- httr::DELETE(api_url)
    
    if (httr::status_code(response) == 200) {
      return(list(success = TRUE))
    } else {
      # Try to get detailed error message
      error_content <- httr::content(response, "text", encoding = "UTF-8")
      return(list(error = paste("HTTP", httr::status_code(response), "-", error_content)))
    }
  }, error = function(e) {
    return(list(error = paste("Failed to delete user:", e$message)))
  })
}