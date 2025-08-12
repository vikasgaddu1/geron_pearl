# Simple Packages Server Module - CRUD for package names only

packages_simple_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Helper function for null coalescing
    `%||%` <- function(x, y) {
      if (is.null(x) || length(x) == 0) y else x
    }
    
    # Reactive values
    packages_data <- reactiveVal(data.frame())
    last_update <- reactiveVal(Sys.time())
    is_editing <- reactiveVal(FALSE)
    editing_package_id <- reactiveVal(NULL)
    
    # Set up validation for new package form
    iv_new <- InputValidator$new()
    iv_new$add_rule("new_package_name", sv_required())
    iv_new$add_rule("new_package_name", function(value) {
      if (nchar(trimws(value)) < 3) {
        "Package name must be at least 3 characters"
      }
    })
    iv_new$add_rule("new_package_name", function(value) {
      existing_packages <- packages_data()
      if (nrow(existing_packages) > 0 && trimws(value) %in% existing_packages$`Package Name`) {
        "A package with this name already exists"
      }
    })

    # Validation for edit package form
    iv_edit <- InputValidator$new()
    iv_edit$add_rule("edit_package_name", sv_required())
    iv_edit$add_rule("edit_package_name", function(value) {
      if (nchar(trimws(value)) < 3) {
        return("Package name must be at least 3 characters")
      }
    })
    iv_edit$add_rule("edit_package_name", function(value) {
      current_id <- editing_package_id()
      existing <- packages_data()
      if (nrow(existing) > 0 && !is.null(current_id)) {
        others <- existing[existing$ID != current_id, ]
        if (nrow(others) > 0 && trimws(value) %in% others$`Package Name`) {
          return("A package with this name already exists")
        }
      }
    })
    
    # Load packages data
    load_packages_data <- function() {
      result <- get_packages()
      if ("error" %in% names(result)) {
        showNotification(paste("Error loading packages:", result$error), type = "error")
        packages_data(data.frame())
      } else {
        df <- convert_packages_to_df(result)
        packages_data(df)
        last_update(Sys.time())
      }
    }
    
    # Convert API data to data frame
    convert_packages_to_df <- function(packages_list) {
      if (length(packages_list) > 0) {
        df <- data.frame(
          ID = sapply(packages_list, function(x) x$id),
          `Package Name` = sapply(packages_list, function(x) x$package_name),
          Actions = sapply(packages_list, function(x) x$id),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(df)
      } else {
        return(data.frame(
          ID = character(0),
          `Package Name` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        ))
      }
    }
    
    # Load data on initialization
    observe({
      load_packages_data()
    })
    
    # Render packages table
    output$packages_table <- DT::renderDataTable({
      data <- packages_data()
      
      if (nrow(data) > 0) {
        # Add action buttons
        data$Actions <- sapply(data$ID, function(pkg_id) {
          sprintf(
            '<button class="btn btn-primary btn-sm me-1" data-action="edit" data-id="%s" data-bs-toggle="tooltip" title="Edit Package">
               <i class="bi bi-pencil"></i>
             </button>
             <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" data-bs-toggle="tooltip" title="Delete Package">
               <i class="bi bi-trash"></i>
             </button>',
            pkg_id, pkg_id
          )
        })
      }
      
      DT::datatable(
        data,
        filter = 'top',
        escape = FALSE,
        selection = 'none',
        options = list(
          dom = 'frtip',
          pageLength = 10,
          searching = TRUE,
          language = list(
            search = "Search (regex supported):",
            emptyTable = "No packages found",
            searchPlaceholder = "Type to search..."
          ),
          columnDefs = list(
            list(targets = 0, visible = FALSE),  # Hide ID column
            list(targets = 2, searchable = FALSE, sortable = FALSE, width = '100px')  # Actions column
          ),
          search = list(regex = TRUE, caseInsensitive = TRUE)
        ),
        rownames = FALSE
      )
    })
    
    # Handle table clicks
    observeEvent(input$packages_table_click_action, {
      info <- input$packages_table_click_action
      if (!is.null(info)) {
        if (info$action == "edit") {
          show_edit_modal(info$id)
        } else if (info$action == "delete") {
          show_delete_modal(info$id)
        }
      }
    })
    
    # Toggle add form sidebar
    observeEvent(input$toggle_add_form, {
      sidebar_toggle(ns("add_package_sidebar"))
    })
    
    # Save new package
    observeEvent(input$save_new_package, {
      # Enable validation only when save is clicked
      iv_new$enable()
      
      if (iv_new$is_valid()) {
        package_name <- trimws(input$new_package_name)
        
        result <- create_package(package_name)
        
        if ("error" %in% names(result)) {
          showNotification(
            paste("Failed to create package:", result$error),
            type = "error",
            duration = 5000
          )
        } else {
          showNotification(
            paste("Package created successfully:", package_name),
            type = "message",
            duration = 3000
          )
          updateTextInput(session, "new_package_name", value = "")
          sidebar_toggle(ns("add_package_sidebar"), open = FALSE)
          load_packages_data()
          iv_new$disable()
        }
      }
    })
    
    # Cancel new package
    observeEvent(input$cancel_new_package, {
      updateTextInput(session, "new_package_name", value = "")
      sidebar_toggle(ns("add_package_sidebar"), open = FALSE)
      iv_new$disable()
    })
    
    # Refresh button
    observeEvent(input$refresh, {
      load_packages_data()
      showNotification("Packages refreshed", type = "message", duration = 2000)
    })
    
    # Show edit modal
    show_edit_modal <- function(package_id) {
      pkg <- packages_data()[packages_data()$ID == package_id, ]
      if (nrow(pkg) > 0) {
        is_editing(TRUE)
        editing_package_id(package_id)
        
        showModal(
          modalDialog(
            title = tagList(bs_icon("pencil"), "Edit Package"),
            size = "m",
            
            div(
              class = "mb-3",
              tags$label("Package Name", `for` = ns("edit_package_name"), class = "form-label fw-bold"),
              textInput(
                ns("edit_package_name"),
                label = NULL,
                value = pkg$`Package Name`[1],
                placeholder = "Enter package name"
              )
            ),
            
            footer = tagList(
              modalButton("Cancel"),
              actionButton(ns("confirm_edit"), "Save Changes", class = "btn-primary")
            )
          )
        )
      }
    }
    
    # Confirm edit
    observeEvent(input$confirm_edit, {
      # Enable validation only when save is clicked
      iv_edit$enable()
      
      if (iv_edit$is_valid()) {
        package_id <- editing_package_id()
        new_name <- trimws(input$edit_package_name)
        
        result <- update_package(package_id, new_name)
        
        if ("error" %in% names(result)) {
          showNotification(
            paste("Failed to update package:", result$error),
            type = "error",
            duration = 5000
          )
        } else {
          showNotification(
            "Package updated successfully",
            type = "message",
            duration = 3000
          )
          removeModal()
          load_packages_data()
          is_editing(FALSE)
          editing_package_id(NULL)
          iv_edit$disable()
        }
      }
    })
    
    # Show delete modal
    show_delete_modal <- function(package_id) {
      pkg <- packages_data()[packages_data()$ID == package_id, ]
      if (nrow(pkg) > 0) {
        showModal(
          modalDialog(
            title = tagList(bs_icon("exclamation-triangle"), "Confirm Deletion"),
            size = "m",
            
            div(
              class = "alert alert-warning",
              tags$strong("Warning:"),
              tags$p(paste("Are you sure you want to delete the package '", pkg$`Package Name`[1], "'?")),
              tags$p("This action cannot be undone. The package must not have any associated items.")
            ),
            
            footer = tagList(
              modalButton("Cancel"),
              actionButton(ns("confirm_delete"), "Delete", class = "btn-danger", `data-id` = package_id)
            )
          )
        )
      }
    }
    
    # Confirm delete
    observeEvent(input$confirm_delete, {
      package_id <- input$confirm_delete$`data-id` %||% input$confirm_delete
      
      if (!is.null(package_id)) {
        result <- delete_package(package_id)
        
        if ("error" %in% names(result)) {
          # Parse error message for better display
          error_msg <- result$error
          if (grepl("associated item", error_msg, ignore.case = TRUE)) {
            showNotification(
              tagList(
                tags$strong("Cannot delete package"),
                tags$br(),
                "This package has associated items. Please delete all items first."
              ),
              type = "error",
              duration = 6000
            )
          } else {
            showNotification(
              paste("Failed to delete package:", error_msg),
              type = "error",
              duration = 5000
            )
          }
        } else {
          showNotification(
            "Package deleted successfully",
            type = "message",
            duration = 3000
          )
          removeModal()
          load_packages_data()
        }
      }
    })
    
    # WebSocket event handling
    observeEvent(input$`packages-websocket_event`, {
      if (!is.null(input$`packages-websocket_event`)) {
        event_data <- input$`packages-websocket_event`
        if (startsWith(event_data$type, "package_")) {
          load_packages_data()
        }
      }
    })
    
    # Update status message
    output$status_message <- renderText({
      data <- packages_data()
      if (nrow(data) > 0) {
        paste("Total packages:", nrow(data))
      } else {
        "No packages found"
      }
    })
    
    # Update last updated display
    output$last_updated_display <- renderText({
      paste("Last updated:", format(last_update(), "%Y-%m-%d %H:%M:%S"))
    })
  })
}