# app.R
library(shiny)
library(bslib)
library(DT)
library(httr)
library(jsonlite)
library(bsicons)

# API Configuration
API_BASE_URL <- "http://localhost:8000/api/v1"
STUDIES_ENDPOINT <- paste0(API_BASE_URL, "/studies")

# Source modules
source("modules/api_client.R")
source("modules/studies_ui.R")
source("modules/studies_server.R")

# Theme
pearl_theme <- bs_theme(
  version = 5,
  bootswatch = "flatly",

)

# UI
ui <- page_sidebar(
  title = span(
    bs_icon("database-fill", "bi", width = "1.2em"),
    " PEARL Admin"
  ),
  sidebar = sidebar(
    id = "main_sidebar",
    width = 250,
    style = "height: 100vh; padding: 0;",
    
    div(
      style = "position: sticky; top: 0; height: calc(100vh); padding: 1rem 0; overflow-y: auto;",
      
      nav_menu(
        "Data Management",
        icon = bs_icon("database", "bi"),
        
        nav_panel(
          "Studies",
          value = "data_tab",
          icon = bs_icon("table", "bi")
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
  fillable = TRUE
) |>
  page_sidebar_body(
    tabset_panel(
      id = "main_tabs",
      type = "tabs",
      
      tab_panel(
        "Studies",
        value = "data_tab",
        card(
          card_header(h5("Studies Management")),
          card_body(
            studies_ui("studies")
          )
        )
      )
    )
  )

# Server
server <- function(input, output, session) {
  studies_server("studies")
}

# Run
shinyApp(ui, server)