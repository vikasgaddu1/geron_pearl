packages_ui <- function(id) {
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
              tags$h4(bs_icon("package"), " Packages", class = "mb-0 text-primary"),
              tags$small("Manage TLF and Dataset packages", class = "text-muted")
            ),
            div(
              class = "d-flex gap-2",
              input_task_button(
                ns("refresh"),
                tagList(bs_icon("arrow-clockwise"), "Refresh"),
                class = "btn btn-primary btn-sm",
                title = "Refresh the packages list"
              ),
              input_task_button(
                ns("toggle_add_form"),
                tagList(bs_icon("plus-lg"), "Add Package"),
                class = "btn btn-success btn-sm",
                title = "Create a new package"
              )
            )
          ),
          
          # Body with sidebar
          card_body(
            class = "p-0",
            style = "height: 100%;",
            
            layout_sidebar(
              sidebar = sidebar(
                id = ns("add_package_sidebar"),
                title = div(
                  class = "d-flex align-items-center",
                  style = "margin-left: 8px; margin-top: 30px;",
                  bs_icon("plus-lg"),
                  span("Add New Package", style = "margin-left: 15px;")
                ),
                width = 450,
                open = FALSE,
                position = "right",
                padding = c(3, 3, 3, 4),
                gap = 2,
                
                # Add Package Form
                card(
                  class = "border border-2",
                  card_body(
                    div(
                      class = "mb-3",
                      tags$label("Package Name", `for` = ns("new_package_name"), class = "form-label fw-bold"),
                      textInput(
                        ns("new_package_name"),
                        label = NULL,
                        value = "",
                        placeholder = "Enter unique package name"
                      ),
                      tags$small(
                        class = "form-text text-muted",
                        "Package names must be unique."
                      )
                    ),
                    
                    # Action buttons
                    layout_columns(
                      col_widths = c(6, 6),
                      gap = 2,
                      input_task_button(
                        ns("save_new_package"),
                        tagList(bs_icon("check"), "Create"),
                        class = "btn btn-success w-100",
                        style = "height: auto; padding: 0.375rem 0.75rem;",
                        title = "Create the new package"
                      ),
                      input_task_button(
                        ns("cancel_new_package"),
                        tagList(bs_icon("x"), "Cancel"),
                        class = "btn btn-secondary w-100",
                        style = "height: auto; padding: 0.375rem 0.75rem;",
                        title = "Cancel and close the form"
                      )
                    )
                  )
                )
              ),
              
              # Main content with tabs for packages and items
              div(
                class = "p-3",
                style = "height: 500px; overflow-y: auto;",
                navset_pill(
                  id = ns("tabs"),
                  nav_panel(
                    "Packages",
                    icon = bs_icon("box"),
                    div(
                      class = "mt-3",
                      DT::dataTableOutput(ns("packages_table"))
                    )
                  ),
                  nav_panel(
                    "Package Items",
                    icon = bs_icon("list-ul"),
                    div(
                      class = "mt-3",
                      # Package selector
                      div(
                        class = "row mb-3",
                        div(
                          class = "col-md-8",
                          selectInput(
                            ns("selected_package"),
                            "Select Package:",
                            choices = NULL,
                            width = "100%"
                          )
                        ),
                        div(
                          class = "col-md-4",
                          input_task_button(
                            ns("add_item"),
                            tagList(bs_icon("plus"), "Add Item"),
                            class = "btn btn-success btn-sm w-100",
                            title = "Add item to selected package"
                          )
                        )
                      ),
                      # Items table
                      DT::dataTableOutput(ns("items_table"))
                    )
                  )
                )
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