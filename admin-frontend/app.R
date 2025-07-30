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
library(shinyjs)

# API Configuration
API_BASE_URL <- "http://localhost:8000/api/v1"
STUDIES_ENDPOINT <- paste0(API_BASE_URL, "/studies")

# Source modules
source("modules/api_client.R")
source("modules/studies_ui.R")
source("modules/studies_server.R")

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
# UI
ui <- page_sidebar(
  window_title = "PEARL Admin",
  title = div(
    class = "pearl-topbar d-flex justify-content-between align-items-center w-100 px-3 py-2",
    span(
      class = "fw-bold",
      style = "font-size: 1.2rem;",
      bs_icon("database-fill", size = "1.2em"),
      " PEARL Admin"
    ),
    div(class = "pearl-darkmode-switch", 
        input_dark_mode(id = "dark_mode", mode = "light"))
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
  
  # Initialize shinyjs and SweetAlert
  useShinyjs(),
  useSweetAlert(),
  
  # Include custom JavaScript for WebSocket and custom CSS
  tags$head(
    # Browser tab title and favicon
    tags$title("PEARL Admin"),
    tags$link(rel = "icon", type = "image/svg+xml", href = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cdefs%3E%3CradialGradient id='pearl' cx='0.3' cy='0.3'%3E%3Cstop offset='0%25' stop-color='%23ffffff' stop-opacity='0.8'/%3E%3Cstop offset='30%25' stop-color='%23f8f9fa' stop-opacity='0.6'/%3E%3Cstop offset='70%25' stop-color='%23e9ecef' stop-opacity='0.4'/%3E%3Cstop offset='100%25' stop-color='%23adb5bd' stop-opacity='0.8'/%3E%3C/radialGradient%3E%3C/defs%3E%3Ccircle cx='50' cy='50' r='45' fill='url(%23pearl)' stroke='%236c757d' stroke-width='2'/%3E%3Cellipse cx='35' cy='35' rx='8' ry='12' fill='%23ffffff' opacity='0.7' transform='rotate(-20 35 35)'/%3E%3C/svg%3E"),
    tags$style(HTML('
      /* Light mode styles (default) */
      .pearl-topbar {
        background: #f8f9fa !important;  /* Light gray background */
        color: #212529 !important;       /* Dark text */
        margin: -0.5rem -0.5rem 0.5rem -0.5rem !important;
        padding: 1rem !important;
        transition: background-color 0.3s ease, color 0.3s ease;
        border-bottom: 1px solid #dee2e6 !important;  /* Subtle border */
      }
      .bslib-page-title {
        background: #f8f9fa !important;
        padding: 0 !important;
        margin: 0 !important;
        transition: background-color 0.3s ease;
      }
      
      /* Dark mode styles */
      [data-bs-theme="dark"] .pearl-topbar {
        background: #212529 !important;  /* Bootstrap dark */
        color: #f8f9fa !important;       /* Light gray text */
      }
      [data-bs-theme="dark"] .bslib-page-title {
        background: #212529 !important;
      }
      
      /* Light mode toggle styling */
      .pearl-darkmode-switch .form-switch .form-check-input {
        border-color: #6c757d;
        background-color: rgba(108, 117, 125, 0.2);
      }
      .pearl-darkmode-switch .form-switch .form-check-input:checked {
        background-color: #0d6efd;
        border-color: #0d6efd;
      }
      
      /* Dark mode toggle styling */
      [data-bs-theme="dark"] .pearl-darkmode-switch .form-switch .form-check-input {
        border-color: #6c757d;
        background-color: rgba(108, 117, 125, 0.3);
      }
      [data-bs-theme="dark"] .pearl-darkmode-switch .form-switch .form-check-input:checked {
        background-color: #6c757d;
        border-color: #6c757d;
      }
    ')),
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