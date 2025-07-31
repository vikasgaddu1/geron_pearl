database_releases_ui <- function(id) {
  ns <- NS(id)

  # Fluid page as container
  page_fluid(
    # Center content using d-flex
    div(
      style = "display: flex; justify-content: center; padding: 20px;",
      div(
        style = "width: 100%; max-width: 1200px;",
        
        # Main card
        card(
          class = "border border-2",
          full_screen = FALSE,
          height = "700px",
          
          # Header
          card_header(
            class = "d-flex justify-content-between align-items-center",
            div(
              tags$h4(bs_icon("database-gear"), " Database Releases", class = "mb-0 text-primary"),
              tags$small("Manage database releases for studies", class = "text-muted")
            ),
            div(
              class = "d-flex gap-2",
              actionButton(
                ns("refresh_btn"),
                tagList(bs_icon("arrow-clockwise"), "Refresh"),
                class = "btn btn-outline-secondary btn-sm",
                title = "Refresh the database releases list"
              ),
              actionButton(
                ns("toggle_add_form"),
                tagList(bs_icon("plus-lg"), "Add Release"),
                class = "btn btn-success btn-sm",
                title = "Add a new database release"
              )
            )
          ),
          
          # Body with sidebar layout
          card_body(
            class = "p-0",
            
            layout_sidebar(
              sidebar = sidebar(
                id = ns("add_release_sidebar"),
                title = div(
                  class = "d-flex align-items-center",
                  style = "margin-left: 8px; margin-top: 30px;",
                  bs_icon("database-add"),
                  span("Add New Database Release", style = "margin-left: 15px;")
                ),
                width = 450,
                open = FALSE,
                position = "right",
                padding = c(3, 3, 3, 4),
                gap = 2,
                
                # Add form card
                card(
                  class = "border border-2",
                  card_body(
                    # Study selection
                    div(
                      class = "mb-3",
                      tags$label("Study", `for` = ns("new_study_id"), class = "form-label fw-bold"),
                      selectInput(
                        ns("new_study_id"),
                        label = NULL,
                        choices = NULL,
                        selected = NULL,
                        width = "100%"
                      )
                    ),
                    
                    # Database Release Label
                    div(
                      class = "mb-3",
                      tags$label("Database Release Label", `for` = ns("new_release_label"), class = "form-label fw-bold"),
                      textInput(
                        ns("new_release_label"),
                        label = NULL,
                        value = "",
                        placeholder = "Enter database release label"
                      )
                    ),
                    
                    # Action buttons
                    layout_columns(
                      col_widths = c(6, 6),
                      gap = 2,
                      actionButton(
                        ns("save_new_release"),
                        tagList(bs_icon("check"), "Create"),
                        class = "btn btn-success w-100",
                        style = "height: auto; padding: 0.375rem 0.75rem;",
                        title = "Create the new database release"
                      ),
                      actionButton(
                        ns("cancel_new_release"),
                        tagList(bs_icon("x"), "Cancel"),
                        class = "btn btn-secondary w-100",
                        style = "height: auto; padding: 0.375rem 0.75rem;",
                        title = "Cancel and close the form"
                      )
                    )
                  )
                )
              ),
              
              # Main content
              div(
                class = "p-3",
                style = "height: 500px; overflow-y: auto;",
                DT::dataTableOutput(ns("releases_table"))
              )
            )
          ),
          
          # Footer
          card_footer(
            class = "d-flex flex-wrap justify-content-between align-items-center small text-muted gap-2",
            div(
              class = "d-flex align-items-center gap-3",
              textOutput(ns("status_message"))
            ),
            textOutput(ns("last_updated_display"))
          )
        )
      )
    )
  )
}