# PEARL Admin Frontend - R Shiny Application
# Modern bslib-based CRUD interface for Studies management

library(shiny)
library(bslib)
library(DT)
library(httr2)
library(jsonlite)
library(shinyWidgets)
library(bsicons)
library(shinyvalidate)
library(shinyjs)
library(dotenv)
library(rlang)

load_dot_env()

# API Configuration
API_BASE_URL <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")
API_HEALTH_PATH <- Sys.getenv("PEARL_API_HEALTH_PATH", "/health")
API_STUDIES_PATH <- Sys.getenv("PEARL_API_STUDIES_PATH", "/api/v1/studies")
API_WEBSOCKET_PATH <- Sys.getenv("PEARL_API_WEBSOCKET_PATH", "/api/v1/ws/studies")

STUDIES_ENDPOINT <- paste0(API_BASE_URL, API_STUDIES_PATH)
WEBSOCKET_URL <- paste0(gsub("^http", "ws", API_BASE_URL), API_WEBSOCKET_PATH)

# Source modules (order matters - api_client needs STUDIES_ENDPOINT)
source("modules/websocket_client.R")
source("modules/api_client.R")
source("modules/studies_ui.R")
source("modules/studies_server.R")
source("modules/database_releases_ui.R")
source("modules/database_releases_server.R")
source("modules/reporting_efforts_ui.R")
source("modules/reporting_efforts_server.R")
source("modules/tnfp_ui.R")
source("modules/tnfp_server.R")
source("modules/packages_ui.R")
source("modules/packages_server.R")

# Theme with automatic dark mode support
pearl_theme <-  bs_theme(
  version = 5,
  # Use a preset as base (try "vapor", "pulse", "morph", "quartz")
  preset = "bootstrap",
  
  # Colors that make a big difference
  primary = "#0d6efd",     # Bright blue
  secondary = "#6c757d",   
  success = "#198754",
  info = "#0dcaf0",
  warning = "#ffc107",
  danger = "#dc3545",
  
  # Background and foreground
  bg = "#ffffff",
  fg = "#212529",
  
  # These Bootstrap variables make a big visual impact
  "body-bg" = "#f8f9fa",   # Light gray background
  "card-border-width" = "0px",
  "card-shadow" = "0 0.5rem 1rem rgba(0, 0, 0, 0.15)",
  "card-cap-bg" = "rgba(0, 0, 0, 0.03)",
  
  # Better spacing
  "spacer" = "1.5rem",
  
  # Fonts
  base_font = font_google("Inter"),
  heading_font = font_google("Inter", wght = "600"),
  font_scale = 1.1,
  
  # Make everything bit rounder
  "border-radius" = "0.5rem",
  "border-radius-lg" = "0.8rem",
  "border-radius-sm" = "0.3rem",
  
  # Enable shadows - this alone makes a big difference
  "enable-shadows" = TRUE,
  
  # Better buttons
  "btn-padding-y" = ".5rem",
  "btn-padding-x" = "1.5rem",
  "btn-font-weight" = "500",
  
  # Navbar styling
  "navbar-padding-y" = "1rem",
  "navbar-brand-font-size" = "1.5rem"
)
## UI - Design A: Top navbar with contextual sidebars per module
ui <- page_navbar(
  title = tagList(
    bs_icon("database-fill", size = "1.2em"),
    " PEARL Admin"
  ),
  theme = pearl_theme,

  # Global dependencies
  useShinyjs(),
  useSweetAlert(),

  # Head: favicon, styles, websocket bootstrapping
  tags$head(
    tags$title("PEARL Admin"),
    tags$link(
      rel = "icon",
      type = "image/svg+xml",
      href = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cdefs%3E%3CradialGradient id='pearl' cx='0.3' cy='0.3'%3E%3Cstop offset='0%25' stop-color='%23ffffff' stop-opacity='0.8'/%3E%3Cstop offset='30%25' stop-color='%23f8f9fa' stop-opacity='0.6'/%3E%3Cstop offset='70%25' stop-color='%23e9ecef' stop-opacity='0.4'/%3E%3Cstop offset='100%25' stop-color='%23adb5bd' stop-opacity='0.8'/%3E%3C/radialGradient%3E%3C/defs%3E%3Ccircle cx='50' cy='50' r='45' fill='url(%23pearl)' stroke='%236c757d' stroke-width='2'/%3E%3Cellipse cx='35' cy='35' rx='8' ry='12' fill='%23ffffff' opacity='0.7' transform='rotate(-20 35 35)'/%3E%3C/svg%3E"
    ),
    tags$link(rel = "stylesheet", type = "text/css", href = "custom.css"),
    tags$script(HTML(sprintf("const pearlApiUrl = '%s'; const pearlWsPath = '%s';", API_BASE_URL, API_WEBSOCKET_PATH))),
    tags$script(src = "websocket_client.js"),
    tags$script(src = "shiny_handlers.js"),
    tags$script(HTML("
      $(document).on('shiny:connected', function() {
        console.log('Shiny connected - WebSocket should be initializing...');
      });
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

  # Primary navigation (grouped)
  nav_menu(
    "Data Management",
    nav_panel("Studies", value = "data_tab", studies_ui("studies")),
    nav_panel("Database Releases", value = "releases_tab", database_releases_ui("database_releases")),
    nav_panel("Reporting Efforts", value = "efforts_tab", reporting_efforts_ui("reporting_efforts")),
    nav_panel("TFL Properties", value = "tnfp_tab", tnfp_ui("tnfp"))
  ),

  nav_menu(
    "Packages",
    nav_panel("Package Registry", value = "packages_tab", packages_ui("packages")),
    nav_panel("Package Installer", disabled = TRUE),
    nav_panel("Package Config", disabled = TRUE)
  ),

  nav_panel(
    "Health Check",
    value = "health_tab",
    card(
      card_header(tags$h4(bs_icon("activity"), "API Health Status", class = "mb-0")),
      card_body(verbatimTextOutput("health_status"))
    )
  ),

  # Right-aligned utilities
  nav_spacer(),
  input_dark_mode(id = "dark_mode", mode = "light"),
  uiOutput("ws_badge")
)

# Server
server <- function(input, output, session) {
  # Handle theme transitions with SweetAlert feedback
  observeEvent(input$dark_mode, {
    # Skip if this is the initial load
    if (is.null(input$dark_mode)) return()
    
    # Temporarily disable interactions during theme transition
    shinyjs::runjs("$('body').css('pointer-events', 'none');")
    
    # Show loading SweetAlert
    sendSweetAlert(
      session = session,
      title = NULL,
      text = tags$div(
        style = "text-align: center;",
        tags$div(
          class = "spinner-border text-primary",
          style = "width: 3rem; height: 3rem;",
          role = "status"
        ),
        tags$p("Switching theme...", style = "margin-top: 15px; font-size: 16px;")
      ),
      html = TRUE,
      type = NULL,
      btn_labels = NA,
      closeOnClickOutside = FALSE,
      showCloseButton = FALSE,
      timer = 1200
    )
    
    # Re-enable interactions and show success after theme transition
    shinyjs::delay(1200, {
      shinyjs::runjs("$('body').css('pointer-events', 'auto');")
      
      theme_mode <- if(input$dark_mode == "dark") "Dark Mode" else "Light Mode"
      icon_name <- if(input$dark_mode == "dark") "🌙" else "☀️"
      
      sendSweetAlert(
        session = session,
        title = paste(icon_name, theme_mode, "Activated!"),
        text = "Theme has been successfully applied.",
        type = "success",
        timer = 1500,
        showConfirmButton = FALSE
      )
    })
  }, ignoreInit = TRUE)
  
  # Studies module
  studies_server("studies")
  
  # Packages module
  packages_server("packages")
  
  # Database Releases module
  database_releases_server("database_releases")
  
  # Reporting Efforts module
  reporting_efforts_server("reporting_efforts")
  
  # TNFP module
  tnfp_server("tnfp")
  
  # Package Management placeholder handlers
  observeEvent(input$refresh_packages_btn, {
    showNotification(
      "Package refresh functionality will be available in a future release.",
      type = "message",
      duration = 3000
    )
  })
  
  observeEvent(input$add_package_btn, {
    showNotification(
      "Package addition functionality will be available in a future release.",
      type = "message", 
      duration = 3000
    )
  })
  
  # Health check
  output$health_status <- renderText({
    tryCatch({
      response <- request(paste0(API_BASE_URL, API_HEALTH_PATH)) |>
        req_perform()
      
      if (resp_status(response) == 200) {
        content <- resp_body_json(response)
        paste("✅ Backend API is healthy\n",
              "Status:", content$status, "\n",
              "Message:", content$message)
      } else {
        paste("❌ Backend API unhealthy\n",
              "Status Code:", resp_status(response))
      }
    }, error = function(e) {
      paste("❌ Cannot connect to backend API\n",
            "Error:", e$message, "\n",
            paste("Please ensure the FastAPI server is running on", API_BASE_URL))
    })
  })
  
  # WebSocket status badge for navbar
  websocket_status <- reactiveVal("Initializing")
  observeEvent(input$websocket_status, {
    websocket_status(input$websocket_status)
  })

  output$ws_badge <- renderUI({
    status <- websocket_status()
    badge_class <- switch(status,
      "Connected" = "bg-success",
      "Connecting" = "bg-warning text-dark",
      "Reconnecting" = "bg-warning text-dark",
      "Failed" = "bg-danger",
      "Disconnected" = "bg-danger",
      "bg-secondary"
    )
    tags$span(class = paste("badge", badge_class), paste("WS:", status))
  })
}

# Run the application
shinyApp(ui = ui, server = server)