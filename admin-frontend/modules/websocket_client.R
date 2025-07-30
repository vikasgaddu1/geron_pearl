# WebSocket Client Module for PEARL
# Handles real-time updates from the FastAPI backend

library(websocket)
library(jsonlite)

# WebSocket configuration
WS_URL <- "ws://localhost:8000/api/v1/ws/studies"
WS_RECONNECT_INTERVAL <- 5  # seconds

# Global WebSocket connection
ws_connection <- NULL
ws_reconnect_timer <- NULL

#' Initialize WebSocket connection
#' @param on_message_callback Function to call when message received
#' @param session Shiny session object for reactive updates
init_websocket <- function(on_message_callback = NULL, session = NULL) {
  
  # Skip if already connected
  if (!is.null(ws_connection) && ws_connection$readyState() == 1L) {
    return(TRUE)
  }
  
  tryCatch({
    # Create WebSocket connection with proper headers
    ws_connection <<- websocket::WebSocket$new(
      WS_URL,
      protocols = character(0),
      headers = list()
    )
    
    # Set up event handlers
    ws_connection$onOpen(function(event) {
      cat("WebSocket connected to:", WS_URL, "\n")
      
      # Cancel any existing reconnect timer
      if (!is.null(ws_reconnect_timer)) {
        ws_reconnect_timer <<- NULL
      }
      
      # Send initial ping to keep connection alive
      send_ping()
    })
    
    ws_connection$onMessage(function(event) {
      tryCatch({
        message_data <- jsonlite::fromJSON(event$data)
        
        # Handle different message types
        if (!is.null(message_data$type)) {
          switch(message_data$type,
            "studies_update" = {
              cat("Received studies update with", length(message_data$data), "studies\n")
              if (!is.null(on_message_callback)) {
                on_message_callback("studies_update", message_data$data)
              }
            },
            "study_created" = {
              cat("Study created:", message_data$data$study_label, "\n")
              if (!is.null(on_message_callback)) {
                on_message_callback("study_created", message_data$data)
              }
            },
            "study_updated" = {
              cat("Study updated:", message_data$data$study_label, "\n")
              if (!is.null(on_message_callback)) {
                on_message_callback("study_updated", message_data$data)
              }
            },
            "study_deleted" = {
              cat("Study deleted, ID:", message_data$data$id, "\n")
              if (!is.null(on_message_callback)) {
                on_message_callback("study_deleted", message_data$data)
              }
            },
            "refresh_needed" = {
              cat("Refresh needed signal received\n")
              if (!is.null(on_message_callback)) {
                on_message_callback("refresh_needed", NULL)
              }
            },
            "pong" = {
              # Keep-alive response, no action needed
            },
            "error" = {
              cat("WebSocket error:", message_data$message, "\n")
            },
            {
              cat("Unknown message type:", message_data$type, "\n")
            }
          )
        }
      }, error = function(e) {
        cat("Error processing WebSocket message:", e$message, "\n")
      })
    })
    
    ws_connection$onClose(function(event) {
      cat("WebSocket connection closed. Code:", event$code, "Reason:", event$reason, "\n")
      ws_connection <<- NULL
      
      # Schedule reconnection if session is available
      if (!is.null(session)) {
        schedule_reconnect(on_message_callback, session)
      }
    })
    
    ws_connection$onError(function(event) {
      cat("WebSocket error occurred\n")
      ws_connection <<- NULL
      
      # Schedule reconnection if session is available
      if (!is.null(session)) {
        schedule_reconnect(on_message_callback, session)
      }
    })
    
    return(TRUE)
    
  }, error = function(e) {
    cat("Failed to initialize WebSocket:", e$message, "\n")
    
    # Schedule reconnection if session is available
    if (!is.null(session)) {
      schedule_reconnect(on_message_callback, session)
    }
    
    return(FALSE)
  })
}

#' Schedule WebSocket reconnection
schedule_reconnect <- function(on_message_callback, session) {
  if (is.null(ws_reconnect_timer)) {
    cat("Scheduling WebSocket reconnection in", WS_RECONNECT_INTERVAL, "seconds\n")
    
    # Use invalidateLater to schedule a reconnection attempt
    ws_reconnect_timer <<- TRUE
    
    later::later(function() {
      cat("Attempting WebSocket reconnection...\n")
      ws_reconnect_timer <<- NULL
      init_websocket(on_message_callback, session)
    }, delay = WS_RECONNECT_INTERVAL)
  }
}

#' Send a message to the WebSocket server
#' @param message List containing the message data
send_websocket_message <- function(message) {
  if (is.null(ws_connection) || ws_connection$readyState() != 1L) {
    cat("WebSocket not connected, cannot send message\n")
    return(FALSE)
  }
  
  tryCatch({
    json_message <- jsonlite::toJSON(message, auto_unbox = TRUE)
    ws_connection$send(json_message)
    return(TRUE)
  }, error = function(e) {
    cat("Error sending WebSocket message:", e$message, "\n")
    return(FALSE)
  })
}

#' Send a ping message to keep connection alive
send_ping <- function() {
  send_websocket_message(list(action = "ping"))
}

#' Request a data refresh from the server
request_refresh <- function() {
  send_websocket_message(list(action = "refresh"))
}

#' Check if WebSocket is connected
is_websocket_connected <- function() {
  !is.null(ws_connection) && ws_connection$readyState() == 1L
}

#' Close WebSocket connection
close_websocket <- function() {
  if (!is.null(ws_connection)) {
    ws_connection$close()
    ws_connection <<- NULL
  }
  
  if (!is.null(ws_reconnect_timer)) {
    ws_reconnect_timer <<- NULL
  }
}

#' Get WebSocket connection status
get_websocket_status <- function() {
  if (is.null(ws_connection)) {
    return("Disconnected")
  }
  
  state <- ws_connection$readyState()
  switch(as.character(state),
    "0" = "Connecting",
    "1" = "Connected",
    "2" = "Closing", 
    "3" = "Closed",
    "Unknown"
  )
}