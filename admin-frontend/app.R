# PEARL Admin Frontend - R Shiny Application
# Modern bslib-based CRUD interface for Studies management

library(shiny)
library(bslib)
library(DT)
library(httr)
library(jsonlite)
library(shinyWidgets)
library(bsicons)

# API Configuration
API_BASE_URL <- "http://localhost:8000/api/v1"
STUDIES_ENDPOINT <- paste0(API_BASE_URL, "/studies")

# Source modules
source("modules/api_client.R")
source("modules/studies_ui.R")
source("modules/studies_server.R")

# Minimal modern theme
pearl_theme <- bs_theme(
  version = 5,
  bootswatch = "flatly",
  base_font = font_google("Inter"),
  heading_font = font_google("Inter", wght = "600")
)

# UI
ui <- page_sidebar(
  title = span(
    bs_icon("database-fill", size = "1.2em"),
    " PEARL Admin"
  ),
  sidebar = sidebar(
    id = "main_sidebar",
    width = 250,
    style = "height: 100vh; padding: 0;",

    div(
      style = "position: sticky; top: 0; height: 100%; overflow-y: auto; padding: 1rem 0;",

      nav_menu(
        "Data Management",
        icon = bs_icon("database"),

        nav_panel(
          "Studies",
          value = "data_tab",
          icon = bs_icon("table")
        )
      )
    ),

    div(
      style = "padding: 1rem;",
      tags$small(
        "v1.0 • ",
        tags$a("GitHub", href = "#", style = "color: #0d6efd;")
      )
    )
  ),
  theme = pearl_theme,
  fillable = TRUE,
  
  # Include custom JavaScript for WebSocket
  tags$head(
    tags$script(src = "websocket_client.js"),
    tags$script(HTML("
      // Custom message handlers for WebSocket integration
      $(document).on('shiny:connected', function(event) {
        console.log('Shiny connected - WebSocket should be initializing...');
      });
      
      // Handle WebSocket refresh requests from Shiny
      Shiny.addCustomMessageHandler('websocket_refresh', function(message) {
        if (window.pearlWebSocket && window.pearlWebSocket.isConnected()) {
          window.pearlWebSocket.refresh();
          console.log('WebSocket refresh requested');
        } else {
          console.log('WebSocket not connected, skipping refresh');
        }
      });
    "))
  ),
  
  # Main content area
  navset_tab(
    id = "main_tabs",

    nav_panel(
      "Studies",
      value = "data_tab",
      studies_ui("studies")
    ),

    nav_panel(
      "Health Check",
      value = "health_tab",
      card(
        card_header(
          tags$h4(
            bs_icon("activity"), 
            "API Health Status",
            class = "mb-0"
          )
        ),
        card_body(
          verbatimTextOutput("health_status")
        )
      )
    )
  )
)

# Server
server <- function(input, output, session) {
  # Studies module
  studies_server("studies")
  
  # Health check
  output$health_status <- renderText({
    tryCatch({
      response <- GET(paste0(API_BASE_URL, "/../health"))
      if (status_code(response) == 200) {
        content <- content(response, "parsed")
        paste("✅ Backend API is healthy\n",
              "Status:", content$status, "\n",
              "Message:", content$message)
      } else {
        paste("❌ Backend API unhealthy\n",
              "Status Code:", status_code(response))
      }
    }, error = function(e) {
      paste("❌ Cannot connect to backend API\n",
            "Error:", e$message, "\n",
            "Please ensure the FastAPI server is running on http://localhost:8000")
    })
  })
}

# Run the application
shinyApp(ui = ui, server = server)