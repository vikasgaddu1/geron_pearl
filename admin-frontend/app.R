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
# Studies, Database Releases, and Reporting Efforts functionality 
# is now consolidated in study_tree modules
source("modules/study_tree_ui.R")
source("modules/study_tree_server.R")
source("modules/tnfp_ui.R")
source("modules/tnfp_server.R")
source("modules/packages_ui.R")
source("modules/packages_server.R")
source("modules/users_ui.R")
source("modules/users_server.R")

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
  window_title = "PEARL Admin",
  theme = pearl_theme,
  header = tagList(
    # Global dependencies and head content
    useShinyjs(),
    useSweetAlert(),
    tags$head(
      tags$title("PEARL Admin"),
      # Use a local SVG favicon for better tab rendering
      tags$link(rel = "icon", type = "image/svg+xml", href = "favicon-pearl.svg"),
      tags$link(rel = "stylesheet", type = "text/css", href = "custom.css"),
      tags$script(HTML(sprintf("const pearlApiUrl = '%s'; const pearlWsPath = '%s';", API_BASE_URL, API_WEBSOCKET_PATH))),
      tags$script(src = "websocket_client.js"),
      tags$script(src = "shiny_handlers.js"),
      tags$script(HTML("
        // Provide default red badges so users see status even before Shiny renders
        document.addEventListener('DOMContentLoaded', function() {
          var ws = document.getElementById('ws_badge');
          if (ws && ws.innerHTML.trim() === '') {
            ws.innerHTML = '<span class=\'badge bg-danger\'>WS: Disconnected</span>';
          }
          var api = document.getElementById('api_health_badge');
          if (api && api.innerHTML.trim() === '') {
            api.innerHTML = '<span class=\'badge bg-danger\'>API: Unknown</span>';
          }
        });
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
    )
  ),

  # Primary navigation (grouped)
  nav_menu(
    "Data Management",
    nav_panel("Study Management", value = "study_tree_tab", study_tree_ui("study_tree")),
    nav_panel("TFL Properties", value = "tnfp_tab", tnfp_ui("tnfp")),
    nav_panel("User Management", value = "users_tab", users_ui("users"))
  ),

  nav_menu(
    "Packages",
    nav_panel("Package Registry", value = "packages_tab", packages_ui("packages")),
    nav_panel("Package Installer", disabled = TRUE),
    nav_panel("Package Config", disabled = TRUE)
  ),

  # (Removed Health Check nav; show compact health badge instead)
  # Right-aligned controls inside navbar
  nav_spacer(),
  nav_item(input_dark_mode(id = "dark_mode", mode = "light")),
  # Bell dropdown (BS5)
  nav_item(uiOutput("status_dropdown"))
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
  
  # Packages module
  packages_server("packages")
  
  # Study Tree module (handles Studies, Database Releases, and Reporting Efforts)
  study_tree_server("study_tree")
  
  # TNFP module
  tnfp_server("tnfp")
  
  # Users module
  users_server("users")
  
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
  
  # Health check (internal helper for dropdown)
  api_health_reactive <- reactiveVal(list(status = NA_integer_, detail = "Unknown"))
  check_api_health <- function() {
    tryCatch({
      response <- request(paste0(API_BASE_URL, API_HEALTH_PATH)) |>
        req_perform()
      
      status_code <- resp_status(response)
      api_health_reactive(list(status = status_code, detail = if (status_code == 200) "Healthy" else paste("HTTP", status_code)))
    }, error = function(e) {
      api_health_reactive(list(status = NA_integer_, detail = "Unreachable"))
    })
  }
  check_api_health()
  
  # WebSocket status reactive
  websocket_status <- reactiveVal("Initializing")
  observeEvent(input$websocket_status, {
    websocket_status(input$websocket_status)
  })

  ws_ok <- reactive({ websocket_status() == "Connected" })
  api_ok <- reactive({ !is.na(api_health_reactive()$status) && api_health_reactive()$status == 200 })

  # Bell dropdown UI
  output$status_dropdown <- renderUI({
    ok <- ws_ok() && api_ok()
    dot_class <- if (ok) "bg-success" else "bg-danger"
    tags$div(class = "dropdown",
      tags$button(
        class = "btn nav-link position-relative",
        id = "statusBtn", `data-bs-toggle` = "dropdown", `aria-expanded` = "false",
        bs_icon("bell"),
        tags$span(class = paste("position-absolute top-0 start-100 translate-middle p-1 border border-light rounded-circle", dot_class), style = "width:10px;height:10px;")
      ),
      tags$ul(class = "dropdown-menu dropdown-menu-end shadow", `aria-labelledby` = "statusBtn",
        tags$li(class = "dropdown-item d-flex align-items-center gap-2",
          tags$span(class = paste("badge rounded-pill", if (ws_ok()) "bg-success" else "bg-danger"), " "),
          tags$div(tags$strong("WebSocket"), tags$br(), tags$small(class = "text-muted", websocket_status()))
        ),
        tags$li(class = "dropdown-item d-flex align-items-center gap-2",
          tags$span(class = paste("badge rounded-pill", if (api_ok()) "bg-success" else "bg-danger"), " "),
          tags$div(tags$strong("API"), tags$br(), tags$small(class = "text-muted", api_health_reactive()$detail))
        ),
        tags$li(class = "dropdown-divider"),
        tags$li(tags$button(class = "dropdown-item d-flex align-items-center gap-2",
          onclick = "Shiny.setInputValue('refresh_status', true, {priority:'event'})",
          bs_icon("arrow-clockwise"), "Refresh status")),
        tags$li(tags$small(class = "dropdown-item-text text-muted", paste("Checked", format(Sys.time(), "%H:%M:%S"))))
      )
    )
  })

  # Refresh handler
  observeEvent(input$refresh_status, {
    check_api_health()
    # Ask JS websocket client to refresh if connected
    session$sendCustomMessage(type = "websocket_refresh", message = list(action = "refresh"))
  })
}

# Run the application
shinyApp(ui = ui, server = server)