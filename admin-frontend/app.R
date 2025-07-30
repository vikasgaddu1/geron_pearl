# PEARL Admin Frontend - R Shiny Application
# Modern bslib-based CRUD interface for Studies management

library(shiny)
library(bslib)
library(DT)
library(httr)
library(jsonlite)
library(shinyWidgets)
library(bsicons)
library(shinyvalidate)

# API Configuration
API_BASE_URL <- "http://localhost:8000/api/v1"
STUDIES_ENDPOINT <- paste0(API_BASE_URL, "/studies")

# Source modules
source("modules/api_client.R")
source("modules/studies_ui.R")
source("modules/studies_server.R")

# Theme with automatic dark mode support
pearl_theme <- bs_theme(
  version = 5,
  base_font = font_google("Inter"),
  heading_font = font_google("Inter", wght = "600")
)

# UI
ui <- page_sidebar(
  title = div(
    class = "d-flex justify-content-between align-items-center w-100 bg-body-secondary px-3 py-2 rounded",
    span(
      bs_icon("database-fill", size = "1.2em"),
      " PEARL Admin"
    ),
    input_dark_mode(id = "dark_mode", mode = "light")
  ),
  sidebar = sidebar(
    id = "main_sidebar",
    width = 250,
    padding = 3,
    gap = 3,

    # Navigation section
    card(
      class = "border border-2",
      card_header(
        class = "bg-primary text-white",
        tags$h6(
          bs_icon("database"),
          "Data Management",
          class = "mb-0 d-flex align-items-center gap-2"
        )
      ),
      card_body(
        class = "p-2",
        div(
          class = "list-group list-group-flush",
          tags$a(
            href = "#",
            class = "list-group-item list-group-item-action d-flex align-items-center gap-2 border-0",
            onclick = "document.getElementById('main_tabs').querySelector('[data-value=\"data_tab\"]').click();",
            bs_icon("table"),
            "Studies"
          )
        )
      )
    ),

    # Footer
    div(
      class = "mt-auto pt-3 border-top text-center",
      tags$small(
        class = "text-muted",
        "v1.0 • ",
        tags$a("GitHub", href = "#", class = "text-decoration-none")
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
      response <- GET("http://localhost:8000/health")
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