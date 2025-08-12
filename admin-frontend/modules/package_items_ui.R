# Package Items UI Module - Manage TLF and Dataset items

package_items_ui <- function(id) {
  ns <- NS(id)
  
  # Helper function for hidden elements (if not already loaded)
  if (!exists("hidden")) {
    hidden <- function(...) {
      shinyjs::hidden(...)
    }
  }
  
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
              actionButton(
                ns("refresh_btn"),
                "Refresh",
                icon = icon("sync"),
                class = "btn btn-primary btn-sm",
                title = "Refresh the items data"
              ),
              actionButton(
                ns("toggle_add_item"),
                "Add Item",
                icon = icon("plus"),
                class = "btn btn-success btn-sm",
                title = "Add a new item to the selected package"
              )
            )
          ),
          
          # Body with sidebar
          card_body(
            class = "p-0",
            style = "height: 100%;",
            
            layout_sidebar(
              fillable = TRUE,
              sidebar = sidebar(
                id = ns("items_sidebar"),
                width = 450,
                position = "right",
                padding = c(3, 3, 3, 4),
                open = "closed",
                
                # Item Form
                div(
                  id = ns("item_form"),
                  tags$h6("Add Individual Item", class = "text-center fw-bold mb-3"),
                  
                  # Dynamic form content based on item type
                  uiOutput(ns("add_item_form")),
                  
                  # Hidden ID field for editing
                  hidden(
                    numericInput(ns("edit_item_id"), "ID", value = NA)
                  ),
                  
                  # Bulk Upload Section
                  tags$hr(class = "my-4"),
                  tags$h6("Bulk Upload", class = "text-center fw-bold mb-3"),
                  
                  # Dynamic template download
                  uiOutput(ns("template_download")),
                  
                  # Dynamic file upload instructions
                  uiOutput(ns("upload_instructions")),
                  
                  # File input
                  fileInput(
                    ns("bulk_upload_file"),
                    label = NULL,
                    accept = c(".xlsx", ".xls"),
                    buttonLabel = "Choose Excel File",
                    placeholder = "No file selected"
                  ),
                  
                  # Upload button
                  actionButton(
                    ns("process_bulk_upload"),
                    tagList(icon("upload"), "Process Upload"),
                    class = "btn btn-primary w-100",
                    style = "height: auto; padding: 0.375rem 0.75rem;",
                    title = "Process the bulk upload file"
                  ),
                  
                  # Upload results placeholder
                  uiOutput(ns("upload_results"))
                )
              ),
              
              # Main content area
              div(
                style = "padding: 10px 0;",
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
          
        )
      )
    )
  )
}