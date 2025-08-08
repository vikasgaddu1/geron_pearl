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
        update_package_selector(df)
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
    # Accepts optional df to avoid reactive read outside reactive context
    update_package_selector <- function(pkgs_df = NULL) {
      pkgs <- pkgs_df
      if (is.null(pkgs)) {
        pkgs <- isolate(packages_data())
      }
      if (!is.null(pkgs) && nrow(pkgs) > 0) {
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
    
    # Contextual hint under the items toolbar
    output$package_items_hint <- renderUI({
      if (is.null(input$selected_package) || input$selected_package == "") {
        div(
          class = "alert alert-info py-2 px-3 mb-3",
          tagList(
            bs_icon("info-circle"),
            span(" First select a package from the dropdown above, then click ", tags$strong("Add Item"), ".")
          )
        )
      } else {
        NULL
      }
    })
    observeEvent(input$selected_package, {
      output$package_items_hint <- renderUI({
        if (is.null(input$selected_package) || input$selected_package == "") {
          div(
            class = "alert alert-info py-2 px-3 mb-3",
            tagList(bs_icon("info-circle"), span(" First select a package from the dropdown above, then click ", tags$strong("Add Item"), "."))
          )
        } else { NULL }
      })
    })

    # Dynamic Add Item button that disables when no package is selected
    output$add_item_container <- renderUI({
      selected <- input$selected_package
      disabled <- is.null(selected) || selected == ""
      btn_class <- if (disabled) "btn btn-success btn-sm w-100 disabled" else "btn btn-success btn-sm w-100"
      tags$button(
        class = btn_class,
        title = if (disabled) "Select a package first" else "Add item to selected package",
        `data-bs-toggle` = if (disabled) NA else "tooltip",
        `data-bs-title` = if (disabled) "Select a package from the dropdown to enable this" else NA,
        onclick = if (disabled) NULL else sprintf("Shiny.setInputValue('%s', true, {priority:'event'})", ns("add_item")),
        tagList(bs_icon("plus"), " Add Item")
      )
    })
    observeEvent(input$selected_package, {
      output$add_item_container <- renderUI({
        selected <- input$selected_package
        disabled <- is.null(selected) || selected == ""
        btn_class <- if (disabled) "btn btn-success btn-sm w-100 disabled" else "btn btn-success btn-sm w-100"
        tags$button(
          class = btn_class,
          title = if (disabled) "Select a package first" else "Add item to selected package",
          `data-bs-toggle` = if (disabled) NA else "tooltip",
          `data-bs-title` = if (disabled) "Select a package from the dropdown to enable this" else NA,
          onclick = if (disabled) NULL else sprintf("Shiny.setInputValue('%s', true, {priority:'event'})", ns("add_item")),
          tagList(bs_icon("plus"), " Add Item")
        )
      })
    })

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
      sidebar_toggle(id = "add_package_sidebar")
      updateTextInput(session, "new_package_name", value = "")
      iv_new$disable()  # Validate only on Create button click
    })
    
    # Save new package
    observeEvent(input$save_new_package, {
      # Enable validation only on submit
      iv_new$enable()
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
          
          sidebar_toggle(id = "add_package_sidebar")
          updateTextInput(session, "new_package_name", value = "")
          iv_new$disable()
          
          load_packages_data()
        }
      } else {
        return()
      }
    })
    
    # Cancel new package
    observeEvent(input$cancel_new_package, {
      sidebar_toggle(id = "add_package_sidebar")
      updateTextInput(session, "new_package_name", value = "")
      iv_new$disable()
    })
    
    # Refresh button
    observeEvent(input$refresh, {
      load_packages_data()
      if (!is.null(input$selected_package)) {
        load_package_items(input$selected_package)
      }
      showNotification("Data refreshed", type = "message", duration = 2)
    })
    
    # Handle package table clicks (edit/delete)
    observeEvent(input$package_action_click, {
      info <- input$package_action_click
      if (is.null(info)) return()
      action <- info$action
      package_id <- as.integer(info$id)

      if (action == "edit") {
        # Use existing table data (avoid extra API call and potential 500s)
        current <- isolate(packages_data())
        pkg_row <- current[current$ID == package_id, , drop = FALSE]
        pkg_name <- if (nrow(pkg_row) > 0) pkg_row$`Package Name`[1] else ""

        is_editing(TRUE)
        editing_package_id(package_id)

        showModal(modalDialog(
          title = tagList(bs_icon("pencil"), "Edit Package"),
          size = "m",
          easyClose = FALSE,
          div(
            class = "mb-3",
            tags$label("Package Name", class = "form-label fw-bold"),
            textInput(ns("edit_package_name"), NULL, value = pkg_name, placeholder = "Enter unique package name", width = "100%"),
            tags$small(class = "form-text text-muted", "Package names must be unique across the system")
          ),
          footer = div(
            class = "d-flex justify-content-end gap-2",
            input_task_button(ns("cancel_edit_package"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-secondary"),
            input_task_button(ns("save_edit_package"), tagList(bs_icon("check"), "Update Package"), class = "btn btn-warning")
          )
        ))
      } else if (action == "delete") {
        # Prevent deletion if items exist; show first 5 codes
        items_result <- get_package_items(package_id)
        if (!("error" %in% names(items_result)) && length(items_result) > 0) {
          codes <- unique(sapply(items_result, function(x) x$item_code))
          preview <- head(codes, 5)
          showModal(modalDialog(
            title = tagList(bs_icon("exclamation-triangle"), "Cannot Delete Package"),
            size = "m",
            div(class = "alert alert-warning",
                tagList(tags$strong("Package has associated items!"), tags$br(),
                        "This package cannot be deleted because it has ", length(codes), " item(s).")),
            tags$p("Please delete all items in this package first, then try deleting the package again."),
            tags$p("First few item codes:"),
            tags$ul(lapply(preview, function(code) tags$li(tags$code(code)))),
            footer = div(class = "d-flex justify-content-end",
                        input_task_button(ns("close_cannot_delete_package"), tagList(bs_icon("x"), "Close"), class = "btn btn-secondary"))
          ))
          return()
        }

        showModal(modalDialog(
          title = tagList(bs_icon("exclamation-triangle"), "Confirm Deletion"),
          size = "m",
          div(class = "alert alert-danger", tagList(tags$strong("Warning: "), "This action cannot be undone.")),
          tags$p("Are you sure you want to delete this package?"),
          footer = div(
            class = "d-flex justify-content-end gap-2",
            input_task_button(ns("cancel_delete_package"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-outline-secondary"),
            input_task_button(ns("confirm_delete_package"), tagList(bs_icon("trash"), "Delete Package"), class = "btn btn-danger",
                              onclick = sprintf("Shiny.setInputValue('%s', %s)", ns("confirm_delete_package_id"), package_id))
          )
        ))
      }
    })

    observeEvent(input$close_cannot_delete_package, { removeModal() })
    
    # Confirm package deletion
    observeEvent(input$confirm_delete_package, {
      package_id <- input$confirm_delete_package_id
      if (is.null(package_id) || package_id == "") return()
      result <- delete_package(package_id)

      if ("error" %in% names(result)) {
        showNotification(paste("Error deleting package:", result$error), type = "error", duration = 5)
      } else {
        showNotification("Package deleted successfully", type = "message", duration = 3)
        load_packages_data()
      }
      removeModal()
    })

    # Cancel delete
    observeEvent(input$cancel_delete_package, { removeModal() })
    
    # Add item button
    observeEvent(input$add_item, {
      if (is.null(input$selected_package) || input$selected_package == "") {
        showNotification("Please select a package first", type = "warning")
        return()
      }
      
      # Show modal for adding item
      showModal(modalDialog(
        title = tagList(bs_icon("plus"), "Add Package Item"),
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
            ),
            tags$small(class="text-muted", "Pick the study this item belongs to")
          ),
          column(6,
            selectInput(ns("item_type"), "Type:",
              choices = c("Select..." = "", "TLF" = "TLF", "Dataset" = "Dataset")
            ),
            tags$small(class="text-muted", "TLF = Table/Listing/Figure; Dataset = SDTM/ADaM")
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
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          input_task_button(ns("save_item"), tagList(bs_icon("check"), "Save"), class = "btn btn-success"),
          input_task_button(ns("cancel_add_item"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-secondary")
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

    # Cancel add item
    observeEvent(input$cancel_add_item, { removeModal() })

    # Cancel edit package
    observeEvent(input$cancel_edit_package, {
      is_editing(FALSE)
      editing_package_id(NULL)
      iv_edit$disable()
      removeModal()
    })

    # Save edit package
    observeEvent(input$save_edit_package, {
      iv_edit$enable()
      if (!iv_edit$is_valid()) return()
      pkg_id <- editing_package_id()
      pkg_name <- trimws(input$edit_package_name)
      result <- update_package(pkg_id, list(package_name = pkg_name))

      if ("error" %in% names(result)) {
        error_msg <- result$error
        if (grepl("duplicate|unique|already exists", error_msg, ignore.case = TRUE)) {
          showNotification(tagList(bs_icon("exclamation-triangle"), "Package name already exists. Please choose a different name."), type = "error")
        } else {
          showNotification(tagList(bs_icon("x-circle"), "Error updating package:", error_msg), type = "error")
        }
      } else {
        showNotification(tagList(bs_icon("check"), "Package updated successfully"), type = "message")
        is_editing(FALSE)
        editing_package_id(NULL)
        iv_edit$disable()
        removeModal()
        load_packages_data()
      }
    })
    
    # Render packages table
    output$packages_table <- DT::renderDataTable({
      packages <- packages_data()

      if (nrow(packages) == 0) {
        # Empty state with standardized config and messaging
        empty_df <- data.frame(
          `Package Name` = character(0),
          `Actions` = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(DT::datatable(
          empty_df,
          filter = 'top',
          options = list(
            dom = 'frtip',
            pageLength = 10,
            language = list(
              emptyTable = "No packages found. Click 'Add Package' to create your first package.",
              search = "",
              searchPlaceholder = "Search (regex supported):"
            ),
            columnDefs = list(
              list(targets = 1, orderable = FALSE, searchable = FALSE, className = 'text-center dt-nowrap', width = '1%')
            ),
            initComplete = JS(sprintf("function(){ $('#%s thead tr:nth-child(2) th:last').html(''); }", ns("packages_table")))
          ),
          rownames = FALSE,
          escape = FALSE
        ))
      }

      # Build display data frame (hide ID) and add Actions column
      display_df <- packages[, c("Package Name"), drop = FALSE]
      display_df$Actions <- sapply(packages$ID, function(package_id) {
        as.character(div(
          class = "d-flex gap-2 justify-content-center",
          tags$button(class = "btn btn-warning btn-sm", `data-action` = "edit", `data-id` = package_id, title = "Edit package", bs_icon("pencil")),
          tags$button(class = "btn btn-danger btn-sm", `data-action` = "delete", `data-id` = package_id, title = "Delete package", bs_icon("trash"))
        ))
      })

      DT::datatable(
        display_df,
        filter = 'top',
        options = list(
          dom = 'frtip',
          search = list(regex = TRUE, caseInsensitive = TRUE),
          pageLength = 10,
          searching = TRUE,
          columnDefs = list(
            list(targets = ncol(display_df) - 1, orderable = FALSE, searchable = FALSE, className = 'text-center dt-nowrap', width = '1%')
          ),
          language = list(search = "", searchPlaceholder = "Search (regex supported):"),
          initComplete = JS(sprintf("function(){ $('#%s thead tr:nth-child(2) th:last').html(''); }", ns("packages_table"))),
          drawCallback = JS(sprintf(
            "function(){\n              var tbl = $('#%s');\n              tbl.find('button[data-action=\\'edit\\']').off('click').on('click', function(){\n                var id = $(this).attr('data-id');\n                Shiny.setInputValue('%s', {action: 'edit', id: id}, {priority: 'event'});\n              });\n              tbl.find('button[data-action=\\'delete\\']').off('click').on('click', function(){\n                var id = $(this).attr('data-id');\n                Shiny.setInputValue('%s', {action: 'delete', id: id}, {priority: 'event'});\n              });\n            }",
            ns("packages_table"), ns("package_action_click"), ns("package_action_click")))
        ),
        rownames = FALSE,
        escape = FALSE,
        selection = 'none'
      )
    }, server = FALSE)
    
    # Render items table
    output$items_table <- DT::renderDataTable({
      items <- items_data()

      if (nrow(items) == 0) {
        # Empty state with standardized config and messaging
        empty_df <- data.frame(
          `Study` = character(0),
          `Type` = character(0),
          `Subtype` = character(0),
          `Code` = character(0),
          `Actions` = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(DT::datatable(
          empty_df,
          filter = 'top',
          options = list(
            dom = 'frtip',
            pageLength = 10,
            language = list(
              emptyTable = "No items in this package. Click 'Add Item' to add items.",
              search = "",
              searchPlaceholder = "Search (regex supported):"
            ),
            columnDefs = list(
              list(targets = 4, orderable = FALSE, searchable = FALSE, className = 'text-center dt-nowrap', width = '1%')
            ),
            initComplete = JS(sprintf("function(){ $('#%s thead tr:nth-child(2) th:last').html(''); }", ns("items_table")))
          ),
          rownames = FALSE,
          escape = FALSE
        ))
      }

      # Build display data frame (hide ID) and add Actions column
      display_df <- items[, c("Study", "Type", "Subtype", "Code"), drop = FALSE]
      display_df$Actions <- sapply(items$ID, function(item_id) {
        as.character(div(
          class = "d-flex gap-2 justify-content-center",
          tags$button(class = "btn btn-warning btn-sm", `data-action` = "edit", `data-id` = item_id, title = "Edit item", bs_icon("pencil")),
          tags$button(class = "btn btn-danger btn-sm", `data-action` = "delete", `data-id` = item_id, title = "Delete item", bs_icon("trash"))
        ))
      })

      DT::datatable(
        display_df,
        filter = 'top',
        options = list(
          dom = 'frtip',
          search = list(regex = TRUE, caseInsensitive = TRUE),
          pageLength = 10,
          searching = TRUE,
          columnDefs = list(
            list(targets = ncol(display_df) - 1, orderable = FALSE, searchable = FALSE, className = 'text-center dt-nowrap', width = '1%')
          ),
          language = list(search = "", searchPlaceholder = "Search (regex supported):"),
          initComplete = JS(sprintf("function(){ $('#%s thead tr:nth-child(2) th:last').html(''); }", ns("items_table"))),
          drawCallback = JS(sprintf(
            "function(){\n              var tbl = $('#%s');\n              tbl.find('button[data-action=\\'edit\\']').off('click').on('click', function(){\n                var id = $(this).attr('data-id');\n                Shiny.setInputValue('%s', {action: 'edit', id: id}, {priority: 'event'});\n              });\n              tbl.find('button[data-action=\\'delete\\']').off('click').on('click', function(){\n                var id = $(this).attr('data-id');\n                Shiny.setInputValue('%s', {action: 'delete', id: id}, {priority: 'event'});\n              });\n            }",
            ns("items_table"), ns("item_action_click"), ns("item_action_click")))
        ),
        rownames = FALSE,
        escape = FALSE,
        selection = 'none'
      )
    }, server = FALSE)
    
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