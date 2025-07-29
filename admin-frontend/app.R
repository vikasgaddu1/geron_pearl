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

# Modern theme using bslib
pearl_theme <- bs_theme(
  version = 5,
  bootswatch = "flatly",
  primary = "#3498db",
  secondary = "#95a5a6",
  success = "#2ecc71",
  info = "#3498db",
  warning = "#f39c12",
  danger = "#e74c3c",
  base_font = font_google("Inter"),
  heading_font = font_google("Inter", wght = "600"),
  code_font = font_google("Fira Code")
)

# UI with modern bslib layout
ui <- page_navbar(
  title = tags$span(
    bs_icon("database-fill"), 
    "PEARL Studies Manager"
  ),
  theme = pearl_theme,
  id = "navbar",
  
  # Studies tab
  nav_panel(
    title = tagList(bs_icon("table"), "Studies"),
    value = "studies",
    studies_ui("studies")
  ),
  
  # Health check tab
  nav_panel(
    title = tagList(bs_icon("heart-pulse"), "Health Check"),
    value = "health",
    layout_columns(
      col_widths = 12,
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
  ),
  
  # Navigation customization
  nav_spacer(),
  nav_item(
    tags$a(
      bs_icon("github"), 
      "GitHub",
      href = "#",
      target = "_blank",
      class = "nav-link"
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