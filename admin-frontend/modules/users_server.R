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
          Department = sapply(users_list, function(x) {
            dept <- x$department
            if (is.null(dept) || dept == "") {
              "Unassigned"
            } else {
              switch(dept,
                "programming" = "Programming",
                "biostatistics" = "Biostatistics", 
                "management" = "Management",
                dept
              )
            }
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
          Department = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        ))
      }
    }
    
    # Load Users data
    load_users_data <- function() {
      result <- get_users()
      if (!is.null(result$error)) {
        cat("Error loading users:", result$error, "\n")
        showNotification("Error loading users", type = "error")
        users_data(data.frame())
      } else {
        users_data(convert_users_to_df(result))
        last_users_update(Sys.time())
      }
    }
    
    # Initialize data loading
    observe({
      load_users_data()
    })
    
    # Universal CRUD Manager integration (Phase 4)
    # Replaces entity-specific WebSocket observer with standardized refresh trigger
    observeEvent(input$`users-crud_refresh`, {
      if (!is.null(input$`users-crud_refresh`)) {
        cat("👤 Universal CRUD refresh triggered for users\n")
        load_users_data()
      }
    })
    
    # Legacy WebSocket observer (kept for backward compatibility during transition)
    observeEvent(input$websocket_event, {
      if (!is.null(input$websocket_event)) {
        event_data <- input$websocket_event
        cat("👤 Legacy WebSocket event received:", event_data$type, "\n")
        if (startsWith(event_data$type, "user_")) {
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
          Department = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE, check.names = FALSE
        )
        
        create_standard_datatable(
          empty_df,
          actions_column = TRUE,
          empty_message = "No users found. Click 'Create User' to add your first user."
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
        display_df <- current_users[, c("Username", "Role", "Department", "Actions")]
        
        create_standard_datatable(
          display_df,
          actions_column = TRUE,
          draw_callback = JS(sprintf(
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
            ns("users_table"), ns("user_action_click"), ns("user_action_click"))
          )
        ) %>%
          DT::formatStyle(
            columns = 1:4,
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
                
                div(
                  class = "mb-3",
                  tags$label("Department", class = "form-label fw-bold"),
                  selectInput(ns("edit_modal_department"), NULL,
                             choices = list(
                               "Unassigned" = "",
                               "Programming" = "programming",
                               "Biostatistics" = "biostatistics",
                               "Management" = "management"
                             ),
                             selected = if(is.null(result$department) || result$department == "") "" else result$department,
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
                  tags$dd(user_row$Role[1]),
                  tags$dt("Department:"),
                  tags$dd(user_row$Department[1])
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
      # Reset form for new user
      editing_user_id(NULL)
      updateTextInput(session, "new_username", value = "")
      updateSelectInput(session, "new_role", selected = "VIEWER")
      updateSelectInput(session, "new_department", selected = "")
      updateNumericInput(session, "edit_user_id", value = NULL)
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
        department <- input$edit_modal_department
        
        cat("Updating user ID:", user_id, "\n")
        result <- update_user(user_id, username, role, department)
        
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
        department <- input$new_department
        
        # Create new user
        cat("Creating new user:", username, "with role:", role, "department:", department, "\n")
        result <- create_user(username, role, department)
          
        if (is.null(result$error)) {
          showNotification("User created successfully", type = "message")
          load_users_data()
          sidebar_toggle(id = "users_sidebar")
          iv_user$disable()
          
          # Reset form
          updateTextInput(session, "new_username", value = "")
          updateSelectInput(session, "new_role", selected = "VIEWER")
          updateSelectInput(session, "new_department", selected = "")
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
      updateSelectInput(session, "new_department", selected = "")
      updateNumericInput(session, "edit_user_id", value = NULL)
    })
    
    # Refresh button
    observeEvent(input$refresh_btn, {
      cat("Refresh button clicked\n")
      showNotification("Refreshing users data...", type = "message", duration = 2)
      load_users_data()
    })
    
    # Bulk Upload Handler
    observeEvent(input$process_bulk_upload, {
      # Check if a file has been selected
      if (is.null(input$bulk_upload_file)) {
        showNotification(
          "Please select an Excel file to upload",
          type = "warning",
          duration = 3  # Duration in seconds
        )
        return()
      }
      
      # Clear previous results
      output$upload_results <- renderUI({
        div(class = "text-muted small", "Processing...")
      })
      
      # Check if readxl is available
      if (!requireNamespace("readxl", quietly = TRUE)) {
        showNotification(
          "Excel support not installed. Please install the 'readxl' package.",
          type = "error",
          duration = 5  # Duration in seconds
        )
        output$upload_results <- renderUI({
          div(class = "alert alert-danger small", "Excel support not available")
        })
        return()
      }
      
      # Validate file extension
      file_ext <- tolower(tools::file_ext(input$bulk_upload_file$name))
      if (!file_ext %in% c("xlsx", "xls")) {
        showNotification(
          "Please upload an Excel file (.xlsx or .xls)",
          type = "error",
          duration = 4  # Duration in seconds
        )
        output$upload_results <- renderUI({
          div(class = "alert alert-danger small", "Invalid file type. Please use .xlsx or .xls files.")
        })
        return()
      }
      
      # Read the uploaded file
      file_path <- input$bulk_upload_file$datapath
      
      # Check if file exists and is readable
      if (!file.exists(file_path)) {
        showNotification(
          "Unable to read the uploaded file. Please try again.",
          type = "error",
          duration = 4  # Duration in seconds
        )
        output$upload_results <- renderUI({
          div(class = "alert alert-danger small", "File upload failed. Please try again.")
        })
        return()
      }
      
      tryCatch({
        # Read Excel file
        df <- readxl::read_excel(file_path)
        
        # Check for required columns (case-insensitive)
        col_names_lower <- tolower(names(df))
        username_col <- which(col_names_lower == "username")[1]
        role_col <- which(col_names_lower == "role")[1]
        department_col <- which(col_names_lower == "department")[1]
        
        if (is.na(username_col) || is.na(role_col)) {
          showNotification(
            "Excel file must contain 'Username' and 'Role' columns",
            type = "error",
            duration = 5  # Duration in seconds
          )
          output$upload_results <- renderUI({
            div(class = "alert alert-danger small", 
                "Missing required columns. File must have 'Username' and 'Role' columns.")
          })
          return()
        }
        
        # Extract username and role columns
        usernames <- as.character(df[[username_col]])
        roles <- as.character(df[[role_col]])
        
        # Extract department column if it exists
        departments <- NULL
        if (!is.na(department_col)) {
          departments <- as.character(df[[department_col]])
        }
        
        # Validate and process each row
        role_mapping <- list(
          "Admin" = "ADMIN",
          "ADMIN" = "ADMIN",
          "Editor" = "EDITOR",
          "EDITOR" = "EDITOR",
          "Viewer" = "VIEWER",
          "VIEWER" = "VIEWER"
        )
        
        department_mapping <- list(
          "Programming" = "programming",
          "programming" = "programming",
          "Biostatistics" = "biostatistics", 
          "biostatistics" = "biostatistics",
          "Management" = "management",
          "management" = "management"
        )
        
        results <- list(
          success = 0,
          duplicates = 0,
          invalid_role = 0,
          invalid_department = 0,
          empty_content = 0,
          errors = 0,
          details = list()
        )
        
        # Get existing usernames to check for duplicates
        existing_users <- users_data()
        existing_usernames <- character()
        if (nrow(existing_users) > 0) {
          existing_usernames <- tolower(existing_users$Username)
        }
        
        for (i in seq_along(usernames)) {
          # Skip empty rows
          if (is.na(usernames[i]) || is.na(roles[i]) || 
              trimws(usernames[i]) == "" || trimws(roles[i]) == "") {
            results$empty_content <- results$empty_content + 1
            next
          }
          
          username_val <- trimws(usernames[i])
          role_val <- trimws(roles[i])
          
          # Get department value if available
          department_val <- ""
          if (!is.null(departments)) {
            department_val <- trimws(departments[i])
            if (is.na(department_val)) department_val <- ""
          }
          
          # Check for duplicate username
          if (tolower(username_val) %in% existing_usernames) {
            results$duplicates <- results$duplicates + 1
            results$details <- append(results$details,
              list(paste("Row", i, ": Username already exists - '", username_val, "'")))
            next
          }
          
          # Map role to internal value
          internal_role <- role_mapping[[role_val]]
          if (is.null(internal_role)) {
            results$invalid_role <- results$invalid_role + 1
            results$details <- append(results$details, 
              list(paste("Row", i, ": Invalid role '", role_val, "' (use Admin, Editor, or Viewer)")))
            next
          }
          
          # Map department to internal value (if provided)
          internal_department <- ""
          if (department_val != "") {
            internal_department <- department_mapping[[department_val]]
            if (is.null(internal_department)) {
              results$invalid_department <- results$invalid_department + 1
              results$details <- append(results$details, 
                list(paste("Row", i, ": Invalid department '", department_val, "' (use programming, biostatistics, management, or blank)")))
              next
            }
          }
          
          # Create the user
          result <- create_user(username_val, internal_role, internal_department)
          
          if (!is.null(result$error)) {
            results$errors <- results$errors + 1
            # Check if it's a duplicate error from the backend
            if (grepl("already exists", result$error, ignore.case = TRUE)) {
              results$duplicates <- results$duplicates + 1
              results$errors <- results$errors - 1  # Adjust count
            }
          } else {
            results$success <- results$success + 1
            # Add to existing usernames to prevent duplicates within the same upload
            existing_usernames <- c(existing_usernames, tolower(username_val))
          }
        }
        
        # Display results with appropriate styling based on outcome
        if (results$success == 0 && results$duplicates > 0) {
          # All users were duplicates
          output$upload_results <- renderUI({
            div(
              class = "alert alert-info small",
              tags$strong("No New Users Added"),
              tags$p(
                class = "mb-2 mt-2",
                paste("All", results$duplicates, "user(s) in the file already exist in the database.")
              ),
              tags$small(
                class = "text-muted",
                "The system skipped duplicates to maintain unique usernames."
              ),
              if (length(results$details) > 0 && length(results$details) <= 5) {
                tags$details(
                  tags$summary("Skipped users"),
                  tags$ul(
                    class = "small",
                    lapply(results$details[1:min(5, length(results$details))], tags$li)
                  )
                )
              }
            )
          })
          
          showNotification(
            "No new users imported - all users already exist in the database",
            type = "warning",
            duration = 4  # Duration in seconds
          )
        } else if (results$success == 0) {
          # No users were imported for other reasons
          output$upload_results <- renderUI({
            div(
              class = "alert alert-warning small",
              tags$strong("No Users Imported"),
              tags$ul(
                class = "mb-0 mt-2",
                if (results$duplicates > 0) tags$li(paste("Already in database:", results$duplicates)),
                if (results$invalid_role > 0) tags$li(paste("Invalid roles:", results$invalid_role)),
                if (results$invalid_department > 0) tags$li(paste("Invalid departments:", results$invalid_department)),
                if (results$empty_content > 0) tags$li(paste("Empty rows:", results$empty_content)),
                if (results$errors > 0) tags$li(paste("Errors:", results$errors))
              ),
              if (length(results$details) > 0 && length(results$details) <= 5) {
                tags$details(
                  tags$summary("Details"),
                  tags$ul(
                    class = "small",
                    lapply(results$details[1:min(5, length(results$details))], tags$li)
                  )
                )
              }
            )
          })
          
          showNotification(
            "No users were imported. Check the details for more information.",
            type = "warning",
            duration = 4  # Duration in seconds
          )
        } else {
          # Some users were successfully imported
          output$upload_results <- renderUI({
            div(
              class = "alert alert-success small",
              tags$strong("Upload Complete"),
              tags$ul(
                class = "mb-0 mt-2",
                tags$li(paste("Successfully created:", results$success, "users")),
                if (results$duplicates > 0) tags$li(paste("Already in database (skipped):", results$duplicates)),
                if (results$invalid_role > 0) tags$li(paste("Invalid roles:", results$invalid_role)),
                if (results$invalid_department > 0) tags$li(paste("Invalid departments:", results$invalid_department)),
                if (results$empty_content > 0) tags$li(paste("Empty rows:", results$empty_content)),
                if (results$errors > 0) tags$li(paste("Errors:", results$errors))
              ),
              if (length(results$details) > 0 && length(results$details) <= 5) {
                tags$details(
                  tags$summary("Details"),
                  tags$ul(
                    class = "small",
                    lapply(results$details[1:min(5, length(results$details))], tags$li)
                  )
                )
              }
            )
          })
          
          # Refresh the table and show success notification
          load_users_data()
          showNotification(
            paste("Successfully imported", results$success, "users"),
            type = "message",
            duration = 4  # Duration in seconds
          )
        }
        
        # Clean up the temp file
        if (file.exists(file_path)) {
          unlink(file_path)
        }
        
        # Reset file input
        shinyjs::reset("bulk_upload_file")
        
      }, error = function(e) {
        showNotification(
          paste("Error reading Excel file:", e$message),
          type = "error",
          duration = 5  # Duration in seconds
        )
        output$upload_results <- renderUI({
          div(class = "alert alert-danger small", 
              paste("Error:", e$message))
        })
        
        # Clean up the temp file
        if (file.exists(file_path)) {
          unlink(file_path)
        }
      })
    })
  })
}