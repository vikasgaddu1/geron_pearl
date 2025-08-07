# Packages Server Module - Modern bslib version with WebSocket support

packages_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Helper function for null coalescing
    `%||%` <- function(x, y) {
      if (is.null(x) || length(x) == 0) y else x
    }
    
    # Reactive values
    packages_data <- reactiveVal(data.frame())
    items_data <- reactiveVal(data.frame())
    studies_list <- reactiveVal(list())
    text_elements_list <- reactiveVal(list())
    last_update <- reactiveVal(Sys.time())
    
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
    
    # Load initial data on startup
    load_packages_data <- function() {
      result <- get_packages()
      if ("error" %in% names(result)) {
        showNotification(paste("Error loading packages:", result$error), type = "error")
        packages_data(data.frame())
      } else {
        df <- convert_packages_to_df(result)
        packages_data(df)
        last_update(Sys.time())
        update_package_selector()
      }
    }
    
    # Load studies for dropdown
    load_studies_list <- function() {
      result <- get_studies()
      if (!"error" %in% names(result)) {
        studies_list(result)
      }
    }
    
    # Load text elements for dropdowns
    load_text_elements <- function() {
      result <- get_text_elements()
      if (!"error" %in% names(result)) {
        text_elements_list(result)
      }
    }
    
    # Convert API data to data frame
    convert_packages_to_df <- function(packages_list) {
      if (length(packages_list) > 0) {
        df <- data.frame(
          ID = sapply(packages_list, function(x) x$id),
          `Package Name` = sapply(packages_list, function(x) x$package_name),
          `Created` = sapply(packages_list, function(x) {
            format(as.POSIXct(x$created_at, format = "%Y-%m-%dT%H:%M:%S"), "%Y-%m-%d %H:%M")
          }),
          Actions = sapply(packages_list, function(x) x$id),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(df)
      } else {
        return(data.frame(
          ID = character(0),
          `Package Name` = character(0),
          `Created` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        ))
      }
    }
    
    # Convert package items to data frame
    convert_items_to_df <- function(items_list) {
      if (length(items_list) > 0) {
        df <- data.frame(
          ID = sapply(items_list, function(x) x$id),
          `Study` = sapply(items_list, function(x) x$study_label %||% "N/A"),
          `Type` = sapply(items_list, function(x) x$item_type),
          `Subtype` = sapply(items_list, function(x) x$item_subtype),
          `Code` = sapply(items_list, function(x) x$item_code),
          Actions = sapply(items_list, function(x) x$id),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(df)
      } else {
        return(data.frame(
          ID = character(0),
          `Study` = character(0),
          `Type` = character(0),
          `Subtype` = character(0),
          `Code` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        ))
      }
    }
    
    # Update package selector dropdown
    update_package_selector <- function() {
      pkgs <- packages_data()
      if (nrow(pkgs) > 0) {
        choices <- setNames(pkgs$ID, pkgs$`Package Name`)
        updateSelectInput(session, "selected_package", choices = choices)
      } else {
        updateSelectInput(session, "selected_package", choices = NULL)
      }
    }
    
    # Handle WebSocket events
    observeEvent(input$websocket_event, {
      event <- input$websocket_event
      if (is.null(event)) return()
      
      switch(event$type,
        "package_created" = load_packages_data(),
        "package_updated" = load_packages_data(),
        "package_deleted" = load_packages_data(),
        "package_item_created" = {
          if (!is.null(input$selected_package)) {
            load_package_items(input$selected_package)
          }
        },
        "package_item_updated" = {
          if (!is.null(input$selected_package)) {
            load_package_items(input$selected_package)
          }
        },
        "package_item_deleted" = {
          if (!is.null(input$selected_package)) {
            load_package_items(input$selected_package)
          }
        }
      )
    })
    
    # Initialize data
    load_packages_data()
    load_studies_list()
    load_text_elements()
    
    # Load package items when package is selected
    load_package_items <- function(package_id) {
      if (!is.null(package_id) && package_id != "") {
        result <- get_package_items(package_id)
        if ("error" %in% names(result)) {
          showNotification(paste("Error loading items:", result$error), type = "error")
          items_data(data.frame())
        } else {
          df <- convert_items_to_df(result)
          items_data(df)
        }
      } else {
        items_data(data.frame())
      }
    }
    
    # When package selection changes
    observeEvent(input$selected_package, {
      load_package_items(input$selected_package)
    })
    
    # Toggle add package form
    observeEvent(input$toggle_add_form, {
      toggle_sidebar(ns("add_package_sidebar"))
      updateTextInput(session, "new_package_name", value = "")
      iv_new$enable()
    })
    
    # Save new package
    observeEvent(input$save_new_package, {
      if (iv_new$is_valid()) {
        package_data <- list(
          package_name = trimws(input$new_package_name)
        )
        
        result <- create_package(package_data)
        
        if ("error" %in% names(result)) {
          showNotification(
            paste("Error creating package:", result$error),
            type = "error",
            duration = 5
          )
        } else {
          showNotification(
            paste("Package", result$package_name, "created successfully"),
            type = "message",
            duration = 3
          )
          
          toggle_sidebar(ns("add_package_sidebar"))
          updateTextInput(session, "new_package_name", value = "")
          iv_new$disable()
          
          load_packages_data()
        }
      }
    })
    
    # Cancel new package
    observeEvent(input$cancel_new_package, {
      toggle_sidebar(ns("add_package_sidebar"))
      updateTextInput(session, "new_package_name", value = "")
    })
    
    # Refresh button
    observeEvent(input$refresh, {
      load_packages_data()
      if (!is.null(input$selected_package)) {
        load_package_items(input$selected_package)
      }
      showNotification("Data refreshed", type = "message", duration = 2)
    })
    
    # Handle package table clicks
    observeEvent(input$package_action_click, {
      info <- input$package_action_click
      if (!is.null(info)) {
        action <- info$action
        package_id <- info$id
        
        if (action == "edit") {
          # Edit functionality can be added here
          showNotification("Edit functionality coming soon", type = "message")
        } else if (action == "delete") {
          showModal(modalDialog(
            title = "Confirm Deletion",
            "Are you sure you want to delete this package? This action cannot be undone.",
            footer = tagList(
              actionButton(ns("confirm_delete_package"), "Delete", class = "btn-danger"),
              modalButton("Cancel")
            ),
            tags$script(paste0("
              $('#", ns("confirm_delete_package"), "').data('package-id', '", package_id, "');
            "))
          ))
        }
      }
    })
    
    # Confirm package deletion
    observeEvent(input$confirm_delete_package, {
      package_id <- input$package_action_click$id
      result <- delete_package(package_id)
      
      if ("error" %in% names(result)) {
        showNotification(
          paste("Error deleting package:", result$error),
          type = "error",
          duration = 5
        )
      } else {
        showNotification("Package deleted successfully", type = "message", duration = 3)
        load_packages_data()
      }
      
      removeModal()
    })
    
    # Add item button
    observeEvent(input$add_item, {
      if (is.null(input$selected_package) || input$selected_package == "") {
        showNotification("Please select a package first", type = "warning")
        return()
      }
      
      # Show modal for adding item
      showModal(modalDialog(
        title = "Add Package Item",
        size = "l",
        
        fluidRow(
          column(6,
            selectInput(ns("item_study"), "Study:", 
              choices = c("Select..." = "", 
                setNames(
                  sapply(studies_list(), function(x) x$id),
                  sapply(studies_list(), function(x) x$study_label)
                )
              )
            )
          ),
          column(6,
            selectInput(ns("item_type"), "Type:",
              choices = c("Select..." = "", "TLF" = "TLF", "Dataset" = "Dataset")
            )
          )
        ),
        
        conditionalPanel(
          condition = "input.item_type == 'TLF'",
          ns = ns,
          fluidRow(
            column(6,
              selectInput(ns("tlf_subtype"), "Subtype:",
                choices = c("Select..." = "", "Table" = "Table", "Listing" = "Listing", "Figure" = "Figure")
              )
            ),
            column(6,
              textInput(ns("tlf_code"), "TLF ID:", placeholder = "e.g., T14.1.1")
            )
          )
        ),
        
        conditionalPanel(
          condition = "input.item_type == 'Dataset'",
          ns = ns,
          fluidRow(
            column(6,
              selectInput(ns("dataset_subtype"), "Subtype:",
                choices = c("Select..." = "", "SDTM" = "SDTM", "ADaM" = "ADaM")
              )
            ),
            column(6,
              textInput(ns("dataset_code"), "Dataset Name:", placeholder = "e.g., ADSL")
            )
          ),
          fluidRow(
            column(12,
              textInput(ns("dataset_label"), "Dataset Label:", placeholder = "Subject-Level Analysis Dataset")
            )
          )
        ),
        
        footer = tagList(
          actionButton(ns("save_item"), "Save", class = "btn-success"),
          modalButton("Cancel")
        )
      ))
    })
    
    # Save new item
    observeEvent(input$save_item, {
      # Validate inputs
      if (is.null(input$item_study) || input$item_study == "") {
        showNotification("Please select a study", type = "error")
        return()
      }
      if (is.null(input$item_type) || input$item_type == "") {
        showNotification("Please select item type", type = "error")
        return()
      }
      
      # Build item data based on type
      if (input$item_type == "TLF") {
        if (is.null(input$tlf_subtype) || input$tlf_subtype == "" || 
            is.null(input$tlf_code) || trimws(input$tlf_code) == "") {
          showNotification("Please fill in all TLF fields", type = "error")
          return()
        }
        
        item_data <- list(
          package_id = as.integer(input$selected_package),
          study_id = as.integer(input$item_study),
          item_type = "TLF",
          item_subtype = input$tlf_subtype,
          item_code = trimws(input$tlf_code)
        )
      } else {
        if (is.null(input$dataset_subtype) || input$dataset_subtype == "" || 
            is.null(input$dataset_code) || trimws(input$dataset_code) == "") {
          showNotification("Please fill in all Dataset fields", type = "error")
          return()
        }
        
        item_data <- list(
          package_id = as.integer(input$selected_package),
          study_id = as.integer(input$item_study),
          item_type = "Dataset",
          item_subtype = input$dataset_subtype,
          item_code = trimws(input$dataset_code),
          dataset_details = list(
            label = trimws(input$dataset_label)
          )
        )
      }
      
      result <- create_package_item(input$selected_package, item_data)
      
      if ("error" %in% names(result)) {
        showNotification(paste("Error creating item:", result$error), type = "error", duration = 5)
      } else {
        showNotification("Item added successfully", type = "message", duration = 3)
        removeModal()
        load_package_items(input$selected_package)
      }
    })
    
    # Render packages table
    output$packages_table <- DT::renderDataTable({
      packages <- packages_data()
      
      if (nrow(packages) == 0) {
        empty_df <- data.frame(
          ID = character(0),
          `Package Name` = character(0),
          `Created` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(DT::datatable(
          empty_df,
          options = list(
            dom = 'ft',
            pageLength = 10,
            language = list(emptyTable = "No packages found. Click 'Add Package' to create your first package.")
          ),
          rownames = FALSE,
          escape = FALSE
        ))
      }
      
      # Add action buttons
      packages$Actions <- sapply(packages$ID, function(package_id) {
        sprintf(
          '<button class="btn btn-primary btn-sm me-1" data-action="edit" data-id="%s" onclick="Shiny.setInputValue(\'%s\', {action: \'edit\', id: \'%s\'}, {priority: \'event\'})">
             <i class="bi bi-pencil"></i>
           </button>
           <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" onclick="Shiny.setInputValue(\'%s\', {action: \'delete\', id: \'%s\'}, {priority: \'event\'})">
             <i class="bi bi-trash"></i>
           </button>',
          package_id, ns("package_action_click"), package_id,
          package_id, ns("package_action_click"), package_id
        )
      })
      
      DT::datatable(
        packages,
        filter = 'top',
        options = list(
          dom = 'frtip',
          search = list(regex = TRUE, caseInsensitive = TRUE),
          pageLength = 10,
          searching = TRUE,
          columnDefs = list(
            list(targets = 0, visible = FALSE)
          )
        ),
        rownames = FALSE,
        escape = FALSE
      )
    })
    
    # Render items table
    output$items_table <- DT::renderDataTable({
      items <- items_data()
      
      if (nrow(items) == 0) {
        empty_df <- data.frame(
          ID = character(0),
          `Study` = character(0),
          `Type` = character(0),
          `Subtype` = character(0),
          `Code` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(DT::datatable(
          empty_df,
          options = list(
            dom = 'ft',
            pageLength = 10,
            language = list(emptyTable = "No items in this package. Click 'Add Item' to add items.")
          ),
          rownames = FALSE,
          escape = FALSE
        ))
      }
      
      # Add action buttons
      items$Actions <- sapply(items$ID, function(item_id) {
        sprintf(
          '<button class="btn btn-primary btn-sm me-1" data-action="edit" data-id="%s" onclick="Shiny.setInputValue(\'%s\', {action: \'edit\', id: \'%s\'}, {priority: \'event\'})">
             <i class="bi bi-pencil"></i>
           </button>
           <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" onclick="Shiny.setInputValue(\'%s\', {action: \'delete\', id: \'%s\'}, {priority: \'event\'})">
             <i class="bi bi-trash"></i>
           </button>',
          item_id, ns("item_action_click"), item_id,
          item_id, ns("item_action_click"), item_id
        )
      })
      
      DT::datatable(
        items,
        filter = 'top',
        options = list(
          dom = 'frtip',
          search = list(regex = TRUE, caseInsensitive = TRUE),
          pageLength = 10,
          searching = TRUE,
          columnDefs = list(
            list(targets = 0, visible = FALSE)
          )
        ),
        rownames = FALSE,
        escape = FALSE
      )
    })
    
    # Handle item table clicks
    observeEvent(input$item_action_click, {
      info <- input$item_action_click
      if (!is.null(info)) {
        if (info$action == "delete") {
          showModal(modalDialog(
            title = "Confirm Deletion",
            "Are you sure you want to delete this item?",
            footer = tagList(
              actionButton(ns("confirm_delete_item"), "Delete", class = "btn-danger"),
              modalButton("Cancel")
            ),
            tags$script(paste0("
              $('#", ns("confirm_delete_item"), "').data('item-id', '", info$id, "');
            "))
          ))
        }
      }
    })
    
    # Confirm item deletion
    observeEvent(input$confirm_delete_item, {
      item_id <- input$item_action_click$id
      result <- delete_package_item(item_id)
      
      if ("error" %in% names(result)) {
        showNotification(paste("Error deleting item:", result$error), type = "error", duration = 5)
      } else {
        showNotification("Item deleted successfully", type = "message", duration = 3)
        load_package_items(input$selected_package)
      }
      
      removeModal()
    })
    
    # Display last update time
    output$last_updated_display <- renderText({
      paste("Last updated:", format(last_update(), "%Y-%m-%d %H:%M:%S"))
    })
    
    # Display status message
    output$status_message <- renderText({
      pkgs <- packages_data()
      paste("Total packages:", nrow(pkgs))
    })
  })
}