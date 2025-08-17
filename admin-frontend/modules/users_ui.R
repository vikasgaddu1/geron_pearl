# Users UI Module - User Management

users_ui <- function(id) {
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
              tags$h4(icon("users"), "User Management", class = "mb-0 text-primary"),
              tags$small("Manage users and their roles", class = "text-muted")
            ),
            div(
              class = "d-flex gap-2",
              actionButton(
                ns("refresh_btn"),
                "Refresh",
                icon = icon("sync"),
                class = "btn btn-primary btn-sm",
                title = "Refresh the users data"
              ),
              actionButton(
                ns("toggle_add_user"),
                "Add User",
                icon = icon("user-plus"),
                class = "btn btn-success btn-sm",
                title = "Add a new user"
              )
            )
          ),
          
          # Body with sidebar layout
          card_body(
            class = "p-0",
            layout_sidebar(
              fillable = TRUE,
              sidebar = sidebar(
                id = ns("users_sidebar"),
                width = 450,
                position = "right",
                padding = c(3, 3, 3, 4),
                open = "closed",
                
                # User Form
                div(
                  id = ns("user_form"),
                  tags$h6("Add Individual User", class = "text-center fw-bold mb-3"),
                  
                  # Username
                  textInput(
                    ns("new_username"),
                    "Username",
                    placeholder = "Enter username..."
                  ),
                  
                  # Role
                  selectInput(
                    ns("new_role"),
                    "Role",
                    choices = list(
                      "Admin" = "ADMIN",
                      "Editor" = "EDITOR",
                      "Viewer" = "VIEWER"
                    ),
                    selected = "VIEWER"
                  ),
                  
                  # Department
                  selectInput(
                    ns("new_department"),
                    "Department",
                    choices = list(
                      "Unassigned" = "",
                      "Programming" = "programming",
                      "Biostatistics" = "biostatistics",
                      "Management" = "management"
                    ),
                    selected = ""
                  ),
                  
                  # Hidden ID field for editing
                  hidden(
                    numericInput(ns("edit_user_id"), "ID", value = NULL)
                  ),
                  
                  # Action buttons
                  layout_columns(
                    col_widths = c(6, 6),
                    gap = 2,
                    actionButton(
                      ns("save_user"),
                      "Create",
                      icon = icon("check"),
                      class = "btn btn-success w-100",
                      style = "height: auto; padding: 0.375rem 0.75rem;",
                      title = "Create the user"
                    ),
                    actionButton(
                      ns("cancel_user"),
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
                      href = "users_template.xlsx",
                      download = "users_template.xlsx",
                      class = "btn btn-outline-info btn-sm w-100",
                      tagList(
                        icon("download"),
                        " Download Excel Template"
                      )
                    ),
                    tags$small(
                      class = "text-muted d-block mt-2 text-center",
                      "Template includes role validation and sample data"
                    )
                  ),
                  
                  # File upload instructions
                  div(
                    class = "alert alert-info small",
                    tags$strong("File Requirements:"),
                    tags$ul(
                      class = "mb-0 mt-2",
                      tags$li("Use the template above for best results"),
                      tags$li("Must contain 'Username' and 'Role' columns"),
                      tags$li("'Department' column is optional"),
                      tags$li("Role column has dropdown validation in template"),
                      tags$li("Valid roles: Admin, Editor, Viewer"),
                      tags$li("Valid departments: programming, biostatistics, management (or blank)"),
                      tags$li("Duplicate usernames automatically skipped")
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
                uiOutput(ns("users_error_msg")),
                
                # DataTable container with fixed height
                div(
                  style = "height: 550px; overflow-y: auto;",
                  DTOutput(ns("users_table"))
                )
              )
            )
          )
        )
      )
    )
  )
}