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
                  tags$h6("User Details", class = "text-muted mb-3"),
                  
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
                  
                  # Hidden ID field for editing
                  hidden(
                    numericInput(ns("edit_user_id"), "ID", value = NA)
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