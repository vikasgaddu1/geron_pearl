# Package Items UI Module - Manage TLF and Dataset items

package_items_ui <- function(id) {
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
              tags$h4(bs_icon("list-ul"), " Package Items", class = "mb-0 text-primary"),
              tags$small("Manage TLF and Dataset items in packages", class = "text-muted")
            ),
            div(
              class = "d-flex gap-2",
              # Package selector
              div(
                style = "width: 300px; margin-right: 10px;",
                selectizeInput(
                  ns("selected_package"),
                  label = NULL,
                  choices = NULL,
                  options = list(
                    placeholder = "Select a package...",
                    maxItems = 1
                  )
                )
              ),
              input_task_button(
                ns("refresh"),
                tagList(bs_icon("arrow-clockwise"), "Refresh"),
                class = "btn btn-primary btn-sm",
                title = "Refresh the items list"
              ),
              input_task_button(
                ns("toggle_add_form"),
                tagList(bs_icon("plus-lg"), "Add Item"),
                class = "btn btn-success btn-sm",
                title = "Add a new item to the selected package"
              ),
              input_task_button(
                ns("bulk_upload"),
                tagList(bs_icon("cloud-upload"), "Bulk Upload"),
                class = "btn btn-info btn-sm",
                title = "Bulk upload items from Excel"
              )
            )
          ),
          
          # Body with sidebar
          card_body(
            class = "p-0",
            style = "height: 100%;",
            
            layout_sidebar(
              sidebar = sidebar(
                id = ns("add_item_sidebar"),
                title = div(
                  class = "d-flex align-items-center",
                  style = "margin-left: 8px; margin-top: 30px;",
                  bs_icon("plus-lg"),
                  span("Add New Item", style = "margin-left: 15px;")
                ),
                width = 450,
                open = FALSE,
                position = "right",
                padding = c(3, 3, 3, 4),
                gap = 2,
                
                # Dynamic form content based on item type
                uiOutput(ns("add_item_form"))
              ),
              
              # Main content with tabs for TLF and Dataset
              div(
                class = "p-3",
                style = "height: 500px; overflow-y: auto;",
                navset_pill(
                  id = ns("item_tabs"),
                  nav_panel(
                    "TLF Items",
                    value = "tlf",
                    icon = bs_icon("table"),
                    div(
                      class = "mt-3",
                      DT::dataTableOutput(ns("tlf_table"))
                    )
                  ),
                  nav_panel(
                    "Dataset Items",
                    value = "dataset",
                    icon = bs_icon("database"),
                    div(
                      class = "mt-3",
                      DT::dataTableOutput(ns("dataset_table"))
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