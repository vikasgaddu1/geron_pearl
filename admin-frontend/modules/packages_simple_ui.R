# Simple Packages UI Module - CRUD for package names only

packages_simple_ui <- function(id) {
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
              tags$h4(bs_icon("box-seam"), " Packages", class = "mb-0 text-primary"),
              tags$small("Manage package registry", class = "text-muted")
            ),
            div(
              class = "d-flex gap-2",
              actionButton(
                ns("refresh_btn"),
                "Refresh",
                icon = icon("sync"),
                class = "btn btn-primary btn-sm",
                title = "Refresh the packages data"
              ),
              actionButton(
                ns("export_excel"),
                "Export to Excel",
                icon = icon("file-excel"),
                class = "btn btn-info btn-sm",
                title = "Export all packages to Excel"
              ),
              actionButton(
                ns("toggle_add_package"),
                "Add Package",
                icon = icon("plus"),
                class = "btn btn-success btn-sm",
                title = "Add a new package"
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
                id = ns("packages_sidebar"),
                width = 450,
                position = "right",
                padding = c(3, 3, 3, 4),
                open = "closed",
                
                # Package Form
                div(
                  id = ns("package_form"),
                  tags$h6("Add Individual Package", class = "text-center fw-bold mb-3"),
                  
                  # Package Name
                  textInput(
                    ns("new_package_name"),
                    "Package Name",
                    placeholder = "Enter unique package name..."
                  ),
                  
                  # Hidden ID field for editing
                  hidden(
                    numericInput(ns("edit_package_id"), "ID", value = NULL)
                  ),
                  
                  # Action buttons
                  layout_columns(
                    col_widths = c(6, 6),
                    gap = 2,
                    actionButton(
                      ns("save_package"),
                      "Create",
                      icon = icon("check"),
                      class = "btn btn-success w-100",
                      style = "height: auto; padding: 0.375rem 0.75rem;",
                      title = "Create the package"
                    ),
                    actionButton(
                      ns("cancel_package"),
                      "Cancel",
                      icon = icon("times"),
                      class = "btn btn-secondary w-100",
                      style = "height: auto; padding: 0.375rem 0.75rem;",
                      title = "Cancel and close"
                    )
                  ),
                  
                  # Bulk Upload Section
                  tags$hr(class = "my-4"),
                  tags$h6("Bulk Upload", class = "text-center fw-bold mb-3"),
                  
                  # Download template link
                  div(
                    class = "mb-3",
                    tags$a(
                      href = "packages_template.xlsx",
                      download = "packages_template.xlsx",
                      class = "btn btn-outline-info btn-sm w-100",
                      tagList(
                        icon("download"),
                        " Download Excel Template"
                      )
                    ),
                    tags$small(
                      class = "text-muted d-block mt-2 text-center",
                      "Template includes sample package names"
                    )
                  ),
                  
                  # File upload instructions
                  div(
                    class = "alert alert-info small",
                    tags$strong("File Requirements:"),
                    tags$ul(
                      class = "mb-0 mt-2",
                      tags$li("Use the template above for best results"),
                      tags$li("Must contain 'Package Name' column"),
                      tags$li("Duplicate package names automatically skipped"),
                      tags$li("Package names must be at least 3 characters")
                    )
                  ),
                  
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
                  div(
                    id = ns("upload_results"),
                    class = "mt-3"
                  )
                )
              ),
              
              # Main content area
              div(
                style = "padding: 10px 0;",
                uiOutput(ns("packages_error_msg")),
                
                # DataTable container with fixed height
                div(
                  style = "height: 550px; overflow-y: auto;",
                  DTOutput(ns("packages_table"))
                )
              )
            )
          ),
          
        )
      )
    )
  )
}