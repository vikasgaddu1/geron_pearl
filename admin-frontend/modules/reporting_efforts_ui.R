reporting_efforts_ui <- function(id) {
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
          height = NULL,
          
          # Header
          card_header(
            class = "d-flex justify-content-between align-items-center",
            div(
              tags$h4(bs_icon("journal-plus"), " Reporting Efforts", class = "mb-0 text-primary"),
              tags$small("Manage reporting efforts for database releases", class = "text-muted")
            ),
            div(
              class = "d-flex gap-2",
              input_task_button(
                ns("refresh_btn"),
                tagList(bs_icon("arrow-clockwise"), "Refresh"),
                class = "btn btn-outline-secondary btn-sm",
                title = "Refresh the reporting efforts list"
              ),
              input_task_button(
                ns("toggle_add_form"),
                tagList(bs_icon("plus-lg"), "Add Effort"),
                class = "btn btn-success btn-sm",
                title = "Add a new reporting effort"
              )
            )
          ),
          
          # Body with sidebar layout
          card_body(
            class = "p-0",
            
            layout_sidebar(
              sidebar = sidebar(
                id = ns("add_effort_sidebar"),
                title = div(
                  class = "d-flex align-items-center",
                  style = "margin-left: 8px; margin-top: 30px;",
                  bs_icon("journal-plus"),
                  span("Add New Reporting Effort", style = "margin-left: 15px;")
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
                    
                    # Database Release selection
                    div(
                      class = "mb-3",
                      tags$label("Database Release", `for` = ns("new_database_release_id"), class = "form-label fw-bold"),
                      selectInput(
                        ns("new_database_release_id"),
                        label = NULL,
                        choices = NULL,
                        selected = NULL,
                        width = "100%"
                      )
                    ),
                    
                    # Database Release Label
                    div(
                      class = "mb-3",
                      tags$label("Reporting Effort Label", `for` = ns("new_effort_label"), class = "form-label fw-bold"),
                      textInput(
                        ns("new_effort_label"),
                        label = NULL,
                        value = "",
                        placeholder = "Enter reporting effort label"
                      )
                    ),
                    
                    # Action buttons
                    layout_columns(
                      col_widths = c(6, 6),
                      gap = 2,
                      input_task_button(
                        ns("save_new_effort"),
                        tagList(bs_icon("check"), "Create"),
                        class = "btn btn-success w-100",
                        style = "height: auto; padding: 0.375rem 0.75rem;",
                        title = "Create the new reporting effort"
                      ),
                      input_task_button(
                        ns("cancel_new_effort"),
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
              div(class = "p-3", DT::dataTableOutput(ns("efforts_table")))
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