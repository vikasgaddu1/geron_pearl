# Users Server Module - User Management

users_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Reactive values for Users
    users_data <- reactiveVal(data.frame())
    last_users_update <- reactiveVal(Sys.time())
    editing_user_id <- reactiveVal(NULL)
    
    # Set up validation for user form
    iv_user <- InputValidator$new()
    iv_user$add_rule("new_username", sv_required())
    iv_user$add_rule("new_username", function(value) {
      if (nchar(trimws(value)) < 1) {
        "Username must be at least 1 character long"
      }
    })
    iv_user$add_rule("new_role", sv_required())
    
    # Convert API data to data frame for Users
    convert_users_to_df <- function(users_list) {
      if (length(users_list) > 0) {
        df <- data.frame(
          ID = sapply(users_list, function(x) x$id),
          Username = sapply(users_list, function(x) x$username),
          Role = sapply(users_list, function(x) {
            role <- x$role
            switch(role,
              "ADMIN" = "Admin",
              "EDITOR" = "Editor",
              "VIEWER" = "Viewer",
              role
            )
          }),
          Actions = sapply(users_list, function(x) x$id),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(df)
      } else {
        return(data.frame(
          ID = numeric(0),
          Username = character(0),
          Role = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        ))
      }
    }
    
    # Load Users data
    load_users_data <- function() {
      cat("Loading users data...\n")
      result <- get_users()
      if (!is.null(result$error)) {
        cat("Error loading users:", result$error, "\n")
        showNotification("Error loading users", type = "error")
        users_data(data.frame())
      } else {
        cat("Loaded", length(result), "users\n")
        users_data(convert_users_to_df(result))
        last_users_update(Sys.time())
      }
    }
    
    # Initialize data loading
    observe({
      load_users_data()
    })
    
    # WebSocket event handling for Users
    observeEvent(input$websocket_event, {
      if (!is.null(input$websocket_event)) {
        event_data <- input$websocket_event
        cat("Users WebSocket event received:", event_data$type, "\n")
        
        if (startsWith(event_data$type, "user_")) {
          cat("User event detected, refreshing data\n")
          load_users_data()
        }
      }
    })
    
    # Render Users table
    output$users_table <- DT::renderDataTable({
      current_users <- users_data()
      
      if (nrow(current_users) == 0) {
        empty_df <- data.frame(
          Username = character(0),
          Role = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE, check.names = FALSE
        )
        
        datatable(
          empty_df,
          options = list(
            dom = 'rtip',
            pageLength = 25,
            language = list(emptyTable = "No users found"),
            columnDefs = list(
              list(targets = 2, searchable = FALSE, orderable = FALSE, width = '100px')
            )
          ),
          escape = FALSE,
          selection = 'none',
          rownames = FALSE
        )
      } else {
        # Add action buttons
        current_users$Actions <- sapply(current_users$ID, function(user_id) {
          sprintf(
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="%s" title="Edit user"><i class="fa fa-pencil"></i></button>
             <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" title="Delete user"><i class="fa fa-trash"></i></button>',
            user_id, user_id
          )
        })
        
        # Remove ID column for display
        display_df <- current_users[, c("Username", "Role", "Actions")]
        
        datatable(
          display_df,
          filter = 'top',
          options = list(
            dom = 'frtip',
            search = list(
              regex = TRUE,
              caseInsensitive = TRUE,
              search = "",
              placeholder = "Search (regex supported):"
            ),
            pageLength = 25,
            columnDefs = list(
              list(targets = 2, searchable = FALSE, orderable = FALSE, width = '100px')
            ),
            language = list(
              search = "",
              searchPlaceholder = "Search (regex supported):"
            ),
            drawCallback = JS(sprintf(
              "function(){
                var tbl = $('#%s');
                tbl.find('button[data-action=\\'edit\\']').off('click').on('click', function(){
                  var id = $(this).attr('data-id');
                  Shiny.setInputValue('%s', {action: 'edit', id: id}, {priority: 'event'});
                });
                tbl.find('button[data-action=\\'delete\\']').off('click').on('click', function(){
                  var id = $(this).attr('data-id');
                  Shiny.setInputValue('%s', {action: 'delete', id: id}, {priority: 'event'});
                });
              }",
              ns("users_table"), ns("user_action_click"), ns("user_action_click")))
          ),
          escape = FALSE,
          selection = 'none',
          rownames = FALSE
        ) %>%
          DT::formatStyle(
            columns = 1:3,
            fontSize = '14px'
          )
      }
    })
    
    # Handle DataTable button clicks
    observeEvent(input$user_action_click, {
      info <- input$user_action_click
      if (!is.null(info)) {
        action <- info$action
        user_id <- as.integer(info$id)
        
        if (action == "edit") {
          cat("Edit user clicked, ID:", user_id, "\n")
          
          # Find the user data
          current_users <- users_data()
          user_row <- current_users[current_users$ID == user_id, ]
          
          if (nrow(user_row) > 0) {
            # Get full user data from API to get actual role value
            result <- get_user_by_id(user_id)
            if (!is.null(result) && is.null(result$error)) {
              # Set editing mode
              editing_user_id(user_id)
              
              # Show edit modal
              showModal(modalDialog(
                title = tagList(icon("pencil"), " Edit User"),
                size = "m",
                easyClose = FALSE,
                
                div(
                  class = "mb-3",
                  tags$label("Username", class = "form-label fw-bold"),
                  textInput(ns("edit_modal_username"), NULL, 
                           value = result$username, 
                           placeholder = "Enter username", 
                           width = "100%")
                ),
                
                div(
                  class = "mb-3",
                  tags$label("Role", class = "form-label fw-bold"),
                  selectInput(ns("edit_modal_role"), NULL,
                             choices = list(
                               "Admin" = "ADMIN",
                               "Editor" = "EDITOR", 
                               "Viewer" = "VIEWER"
                             ),
                             selected = result$role,
                             width = "100%")
                ),
                
                footer = div(
                  class = "d-flex justify-content-end gap-2",
                  actionButton(ns("cancel_edit_modal"), "Cancel", 
                              class = "btn btn-secondary"),
                  actionButton(ns("save_edit_modal"), "Update User", 
                              icon = icon("check"),
                              class = "btn btn-warning")
                )
              ))
            }
          }
        } else if (action == "delete") {
          cat("Delete user clicked, ID:", user_id, "\n")
          
          # Find the user data
          current_users <- users_data()
          user_row <- current_users[current_users$ID == user_id, ]
          
          if (nrow(user_row) > 0) {
            showModal(modalDialog(
              title = tagList(icon("exclamation-triangle", class = "text-danger"), " Confirm Deletion"),
              tagList(
                tags$div(class = "alert alert-danger",
                  tags$strong("Warning: "), "This action cannot be undone!"
                ),
                tags$p("Are you sure you want to delete this user?"),
                tags$hr(),
                tags$dl(
                  tags$dt("Username:"),
                  tags$dd(tags$strong(user_row$Username[1])),
                  tags$dt("Role:"),
                  tags$dd(user_row$Role[1])
                )
              ),
              footer = tagList(
                actionButton(ns("confirm_delete_user"), "Delete User", 
                            icon = icon("trash"),
                            class = "btn-danger"),
                modalButton("Cancel")
              ),
              easyClose = FALSE,
              size = "m"
            ))
            
            # Store the ID for deletion
            editing_user_id(user_id)
          }
        }
      }
    })
    
    # Confirm delete user
    observeEvent(input$confirm_delete_user, {
      user_id <- editing_user_id()
      if (!is.null(user_id)) {
        cat("Deleting user ID:", user_id, "\n")
        result <- delete_user(user_id)
        
        if (is.null(result$error)) {
          showNotification("User deleted successfully", type = "message")
          load_users_data()
        } else {
          showNotification(paste("Error deleting user:", result$error), type = "error")
        }
        
        removeModal()
        editing_user_id(NULL)
      }
    })
    
    # Toggle add user sidebar
    observeEvent(input$toggle_add_user, {
      cat("Add user button clicked\n")
      
      # Reset form for new user
      editing_user_id(NULL)
      updateTextInput(session, "new_username", value = "")
      updateSelectInput(session, "new_role", selected = "VIEWER")
      updateNumericInput(session, "edit_user_id", value = NA)
      updateActionButton(session, "save_user", 
                       label = "Create",
                       icon = icon("check"))
      
      # Toggle sidebar (without namespace)
      sidebar_toggle(id = "users_sidebar")
      
      # Disable validation until save is clicked
      iv_user$disable()
    })
    
    # Helper function to format error messages
    format_error_message <- function(error_string) {
      if (grepl("HTTP 400", error_string)) {
        # Remove the HTTP error prefix to get the JSON part
        json_part <- gsub("^.*HTTP 400[^-]*- ", "", error_string)
        tryCatch({
          error_data <- jsonlite::fromJSON(json_part)
          return(error_data$detail)
        }, error = function(e) {
          return(error_string)
        })
      }
      return(error_string)
    }
    
    # Save edit modal
    observeEvent(input$save_edit_modal, {
      user_id <- editing_user_id()
      if (!is.null(user_id)) {
        username <- trimws(input$edit_modal_username)
        role <- input$edit_modal_role
        
        cat("Updating user ID:", user_id, "\n")
        result <- update_user(user_id, username, role)
        
        if (is.null(result$error)) {
          showNotification("User updated successfully", type = "message")
          load_users_data()
          removeModal()
          editing_user_id(NULL)
        } else {
          formatted_error <- format_error_message(result$error)
          if (grepl("already exists", formatted_error)) {
            showNotification(
              tagList(
                tags$strong("Duplicate Username"),
                tags$br(),
                formatted_error
              ),
              type = "error",
              duration = 6000
            )
          } else {
            showNotification(paste("Error updating user:", formatted_error), type = "error")
          }
        }
      }
    })
    
    # Cancel edit modal
    observeEvent(input$cancel_edit_modal, {
      removeModal()
      editing_user_id(NULL)
    })
    
    # Save user (create new user from sidebar)
    observeEvent(input$save_user, {
      # Enable validation and check
      iv_user$enable()
      if (iv_user$is_valid()) {
        cat("Save user clicked\n")
        
        username <- trimws(input$new_username)
        role <- input$new_role
        
        # Create new user
        cat("Creating new user:", username, "with role:", role, "\n")
        result <- create_user(username, role)
          
        if (is.null(result$error)) {
          showNotification("User created successfully", type = "message")
          load_users_data()
          sidebar_toggle(id = "users_sidebar")
          iv_user$disable()
          
          # Reset form
          updateTextInput(session, "new_username", value = "")
          updateSelectInput(session, "new_role", selected = "VIEWER")
        } else {
          formatted_error <- format_error_message(result$error)
          if (grepl("already exists", formatted_error)) {
            showNotification(
              tagList(
                tags$strong("Duplicate Username"),
                tags$br(),
                formatted_error
              ),
              type = "error",
              duration = 6000
            )
          } else {
            showNotification(paste("Error creating user:", formatted_error), type = "error")
          }
        }
      }
    })
    
    # Cancel button
    observeEvent(input$cancel_user, {
      sidebar_toggle(id = "users_sidebar")
      editing_user_id(NULL)
      iv_user$disable()
      
      # Reset form
      updateTextInput(session, "new_username", value = "")
      updateSelectInput(session, "new_role", selected = "VIEWER")
      updateNumericInput(session, "edit_user_id", value = NA)
    })
    
    # Refresh button
    observeEvent(input$refresh_btn, {
      cat("Refresh button clicked\n")
      showNotification("Refreshing users data...", type = "message", duration = 2)
      load_users_data()
    })
  })
}