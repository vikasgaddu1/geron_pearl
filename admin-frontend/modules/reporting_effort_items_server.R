# Reporting Effort Items Server Module - CRUD for reporting effort items

reporting_effort_items_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Helper function for null coalescing
    `%||%` <- function(x, y) {
      if (is.null(x) || length(x) == 0) y else x
    }
    
    # Reactive values
    items_data <- reactiveVal(data.frame())
    reporting_efforts_list <- reactiveVal(list())
    packages_list <- reactiveVal(list())
    last_update <- reactiveVal(Sys.time())
    is_editing <- reactiveVal(FALSE)
    editing_item_id <- reactiveVal(NULL)
    current_reporting_effort_id <- reactiveVal(NULL)
    
    # Set up validation for item form
    iv_item <- InputValidator$new()
    iv_item$add_rule("item_code", sv_required())
    iv_item$add_rule("item_code", function(value) {
      if (nchar(trimws(value)) < 2) {
        "Item code must be at least 2 characters long"
      }
    })
    
    # Conditional validation for TLF fields
    iv_item$add_rule("tlf_title", function(value) {
      if (input$item_type == "TLF" && (is.null(value) || nchar(trimws(value)) == 0)) {
        "Title is required for TLF items"
      }
    })
    
    # Conditional validation for Dataset fields
    iv_item$add_rule("dataset_name", function(value) {
      if (input$item_type == "Dataset" && (is.null(value) || nchar(trimws(value)) == 0)) {
        "Dataset name is required for Dataset items"
      }
    })
    
    # Load reporting efforts for dropdown
    load_reporting_efforts <- function() {
      result <- get_reporting_efforts()
      if ("error" %in% names(result)) {
        showNotification(paste("Error loading reporting efforts:", result$error), type = "error")
        reporting_efforts_list(list())
      } else {
        reporting_efforts_list(result)
        
        # Create choices for select input
        choices <- setNames(
          sapply(result, function(x) x$id),
          sapply(result, function(x) paste0(x$effort_name, " (", x$study_name, ")"))
        )
        choices <- c("" = "", choices)
        
        updateSelectInput(session, "selected_reporting_effort", choices = choices)
      }
    }
    
    # Load packages for copy operations
    load_packages <- function() {
      result <- get_packages()
      if ("error" %in% names(result)) {
        showNotification(paste("Error loading packages:", result$error), type = "error")
        packages_list(list())
      } else {
        packages_list(result)
      }
    }
    
    # Load items data for selected reporting effort
    load_items_data <- function() {
      effort_id <- current_reporting_effort_id()
      if (is.null(effort_id) || effort_id == "") {
        items_data(data.frame())
        return()
      }
      
      result <- get_reporting_effort_items_by_effort(effort_id)
      if ("error" %in% names(result)) {
        showNotification(paste("Error loading items:", result$error), type = "error")
        items_data(data.frame())
      } else {
        df <- convert_items_to_df(result)
        items_data(df)
        last_update(Sys.time())
      }
    }
    
    # Convert API data to data frame
    convert_items_to_df <- function(items_list) {
      if (length(items_list) > 0) {
        df <- data.frame(
          ID = sapply(items_list, function(x) x$id),
          Type = sapply(items_list, function(x) x$item_type),
          Subtype = sapply(items_list, function(x) x$item_subtype),
          Code = sapply(items_list, function(x) x$item_code),
          Title = sapply(items_list, function(x) {
            if (x$item_type == "TLF" && !is.null(x$tlf_details)) {
              x$tlf_details$title %||% ""
            } else if (x$item_type == "Dataset" && !is.null(x$dataset_details)) {
              x$dataset_details$dataset_name %||% ""
            } else {
              ""
            }
          }),
          Status = sapply(items_list, function(x) {
            if (x$item_type == "TLF" && !is.null(x$tlf_details)) {
              status_parts <- c()
              if (isTRUE(x$tlf_details$mock_available)) status_parts <- c(status_parts, "Mock")
              if (isTRUE(x$tlf_details$asr_ready)) status_parts <- c(status_parts, "ASR")
              if (length(status_parts) > 0) paste(status_parts, collapse = ", ") else "Draft"
            } else if (x$item_type == "Dataset" && !is.null(x$dataset_details)) {
              if (isTRUE(x$dataset_details$locked)) "Locked" else "Unlocked"
            } else {
              "Unknown"
            }
          }),
          Actions = sapply(items_list, function(x) x$id),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(df)
      } else {
        return(data.frame(
          ID = character(0),
          Type = character(0),
          Subtype = character(0),
          Code = character(0),
          Title = character(0),
          Status = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        ))
      }
    }
    
    # Load data on initialization
    observe({
      load_reporting_efforts()
      load_packages()
    })
    
    # Watch for reporting effort selection changes
    observeEvent(input$selected_reporting_effort, {
      effort_id <- input$selected_reporting_effort
      if (!is.null(effort_id) && effort_id != "") {
        current_reporting_effort_id(effort_id)
        load_items_data()
      } else {
        current_reporting_effort_id(NULL)
        items_data(data.frame())
      }
    })
    
    # Render items table
    output$items_table <- DT::renderDataTable({
      data <- items_data()
      
      if (nrow(data) == 0) {
        empty_df <- data.frame(
          Type = character(0),
          Subtype = character(0),
          Code = character(0),
          Title = character(0),
          Status = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE, check.names = FALSE
        )
        
        datatable(
          empty_df,
          options = list(
            dom = 'rtip',
            pageLength = 25,
            language = list(emptyTable = "No items found for this reporting effort"),
            columnDefs = list(
              list(targets = 5, searchable = FALSE, orderable = FALSE, width = '100px')
            )
          ),
          escape = FALSE,
          selection = 'none',
          rownames = FALSE
        )
      } else {
        # Add action buttons
        data$Actions <- sapply(data$ID, function(item_id) {
          sprintf(
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="%s" title="Edit item"><i class="fa fa-pencil"></i></button>
             <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" title="Delete item"><i class="fa fa-trash"></i></button>',
            item_id, item_id
          )
        })
        
        # Remove ID column for display
        display_df <- data[, c("Type", "Subtype", "Code", "Title", "Status", "Actions")]
        
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
              list(targets = 5, searchable = FALSE, orderable = FALSE, width = '100px')
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
              ns("items_table"), ns("item_action_click"), ns("item_action_click")))
          ),
          escape = FALSE,
          selection = 'none',
          rownames = FALSE
        ) %>%
          DT::formatStyle(
            columns = 1:6,
            fontSize = '14px'
          )
      }
    })
    
    # Handle DataTable button clicks
    observeEvent(input$item_action_click, {
      info <- input$item_action_click
      if (!is.null(info)) {
        action <- info$action
        item_id <- as.integer(info$id)
        
        if (action == "edit") {
          cat("Edit item clicked, ID:", item_id, "\n")
          
          # Get item details
          result <- get_reporting_effort_item(item_id)
          if ("error" %in% names(result)) {
            showNotification(paste("Error loading item:", result$error), type = "error")
            return()
          }
          
          # Set editing mode
          editing_item_id(item_id)
          is_editing(TRUE)
          
          # Populate form with item data
          updateTextInput(session, "item_code", value = result$item_code)
          updateRadioButtons(session, "item_type", selected = result$item_type)
          
          if (result$item_type == "TLF") {
            updateSelectInput(session, "tlf_subtype", selected = result$item_subtype)
            if (!is.null(result$tlf_details)) {
              updateTextInput(session, "tlf_title", value = result$tlf_details$title %||% "")
              updateTextAreaInput(session, "tlf_description", value = result$tlf_details$description %||% "")
              updateTextInput(session, "tlf_population", value = result$tlf_details$population %||% "")
              updateCheckboxInput(session, "tlf_mock_available", value = isTRUE(result$tlf_details$mock_available))
              updateCheckboxInput(session, "tlf_asr_ready", value = isTRUE(result$tlf_details$asr_ready))
            }
          } else if (result$item_type == "Dataset") {
            updateSelectInput(session, "dataset_subtype", selected = result$item_subtype)
            if (!is.null(result$dataset_details)) {
              updateTextInput(session, "dataset_name", value = result$dataset_details$dataset_name %||% "")
              updateTextAreaInput(session, "dataset_description", value = result$dataset_details$description %||% "")
              updateTextInput(session, "dataset_location", value = result$dataset_details$location %||% "")
              updateCheckboxInput(session, "dataset_locked", value = isTRUE(result$dataset_details$locked))
            }
          }
          
          # Update button text
          updateActionButton(session, "save_item", 
                           label = "Update",
                           icon = icon("check"))
          
          # Open sidebar
          sidebar_toggle(id = "items_sidebar")
          iv_item$disable()
          
        } else if (action == "delete") {
          cat("Delete item clicked, ID:", item_id, "\n")
          
          # Find the item data
          current_items <- items_data()
          item_row <- current_items[current_items$ID == item_id, ]
          
          if (nrow(item_row) > 0) {
            showModal(modalDialog(
              title = tagList(icon("exclamation-triangle", class = "text-danger"), " Confirm Deletion"),
              tagList(
                tags$div(class = "alert alert-danger",
                  tags$strong("Warning: "), "This action cannot be undone!"
                ),
                tags$p("Are you sure you want to delete this item?"),
                tags$hr(),
                tags$dl(
                  tags$dt("Type:"),
                  tags$dd(tags$strong(item_row$Type[1])),
                  tags$dt("Code:"),
                  tags$dd(tags$strong(item_row$Code[1])),
                  tags$dt("Title:"),
                  tags$dd(tags$strong(item_row$Title[1]))
                )
              ),
              footer = tagList(
                actionButton(ns("confirm_delete_item"), "Delete Item", 
                            icon = icon("trash"),
                            class = "btn-danger"),
                modalButton("Cancel")
              ),
              easyClose = FALSE,
              size = "m"
            ))
            
            # Store the ID for deletion
            editing_item_id(item_id)
          }
        }
      }
    })
    
    # Toggle add item sidebar
    observeEvent(input$toggle_add_item, {
      if (is.null(current_reporting_effort_id()) || current_reporting_effort_id() == "") {
        showNotification("Please select a reporting effort first", type = "warning")
        return()
      }
      
      # Reset form for new item
      editing_item_id(NULL)
      is_editing(FALSE)
      updateTextInput(session, "item_code", value = "")
      updateRadioButtons(session, "item_type", selected = "TLF")
      updateSelectInput(session, "tlf_subtype", selected = "Table")
      updateSelectInput(session, "dataset_subtype", selected = "ADAM")
      updateTextInput(session, "tlf_title", value = "")
      updateTextAreaInput(session, "tlf_description", value = "")
      updateTextInput(session, "tlf_population", value = "")
      updateCheckboxInput(session, "tlf_mock_available", value = FALSE)
      updateCheckboxInput(session, "tlf_asr_ready", value = FALSE)
      updateTextInput(session, "dataset_name", value = "")
      updateTextAreaInput(session, "dataset_description", value = "")
      updateTextInput(session, "dataset_location", value = "")
      updateCheckboxInput(session, "dataset_locked", value = FALSE)
      updateActionButton(session, "save_item", 
                       label = "Create",
                       icon = icon("check"))
      
      # Toggle sidebar
      sidebar_toggle(id = "items_sidebar")
      
      # Disable validation until save is clicked
      iv_item$disable()
    })
    
    # Save item (create or update)
    observeEvent(input$save_item, {
      # Enable validation and check
      iv_item$enable()
      if (iv_item$is_valid()) {
        cat("Save item clicked\n")
        
        effort_id <- current_reporting_effort_id()
        if (is.null(effort_id) || effort_id == "") {
          showNotification("Please select a reporting effort first", type = "error")
          return()
        }
        
        item_code <- trimws(input$item_code)
        item_type <- input$item_type
        
        # Build item data
        item_data <- list(
          reporting_effort_id = as.integer(effort_id),
          item_type = item_type,
          item_code = item_code
        )
        
        if (item_type == "TLF") {
          item_data$item_subtype <- input$tlf_subtype
          item_data$tlf_details <- list(
            title = trimws(input$tlf_title),
            description = if (nchar(trimws(input$tlf_description)) > 0) trimws(input$tlf_description) else NULL,
            population = if (nchar(trimws(input$tlf_population)) > 0) trimws(input$tlf_population) else NULL,
            mock_available = input$tlf_mock_available,
            asr_ready = input$tlf_asr_ready
          )
        } else if (item_type == "Dataset") {
          item_data$item_subtype <- input$dataset_subtype
          item_data$dataset_details <- list(
            dataset_name = trimws(input$dataset_name),
            description = if (nchar(trimws(input$dataset_description)) > 0) trimws(input$dataset_description) else NULL,
            location = if (nchar(trimws(input$dataset_location)) > 0) trimws(input$dataset_location) else NULL,
            locked = input$dataset_locked
          )
        }
        
        if (is_editing()) {
          # Update existing item
          item_id <- editing_item_id()
          cat("Updating item ID:", item_id, "\n")
          result <- update_reporting_effort_item(item_id, item_data)
        } else {
          # Create new item
          cat("Creating new item:", item_code, "\n")
          result <- create_reporting_effort_item(item_data)
        }
          
        if (!is.null(result$error)) {
          showNotification(paste("Error saving item:", result$error), type = "error")
        } else {
          action_text <- if (is_editing()) "updated" else "created"
          showNotification(paste("Item", action_text, "successfully"), type = "message")
          load_items_data()
          sidebar_toggle(id = "items_sidebar")
          iv_item$disable()
          editing_item_id(NULL)
          is_editing(FALSE)
        }
      }
    })
    
    # Cancel button
    observeEvent(input$cancel_item, {
      sidebar_toggle(id = "items_sidebar")
      editing_item_id(NULL)
      is_editing(FALSE)
      iv_item$disable()
    })
    
    # Confirm delete item
    observeEvent(input$confirm_delete_item, {
      item_id <- editing_item_id()
      if (!is.null(item_id)) {
        cat("Deleting item ID:", item_id, "\n")
        result <- delete_reporting_effort_item(item_id)
        
        if (is.null(result$error)) {
          showNotification("Item deleted successfully", type = "message")
          load_items_data()
        } else {
          showNotification(paste("Error deleting item:", result$error), type = "error")
        }
        
        removeModal()
        editing_item_id(NULL)
      }
    })
    
    # Refresh button
    observeEvent(input$refresh_btn, {
      cat("Refresh button clicked\n")
      showNotification("Refreshing items data...", type = "message", duration = 2)
      load_items_data()
    })
    
    # Bulk TLF upload
    observeEvent(input$bulk_tlf_clicked, {
      effort_id <- current_reporting_effort_id()
      if (is.null(effort_id) || effort_id == "") {
        showNotification("Please select a reporting effort first", type = "warning")
        return()
      }
      
      showModal(modalDialog(
        title = tagList(icon("upload"), " Bulk Upload TLF Items"),
        size = "m",
        easyClose = FALSE,
        
        div(
          class = "mb-3",
          tags$p("Upload an Excel file containing TLF items to add multiple items at once."),
          
          tags$div(
            class = "alert alert-info small",
            tags$strong("File Requirements:"),
            tags$ul(
              class = "mb-0 mt-2",
              tags$li("Excel file (.xlsx or .xls)"),
              tags$li("Required columns: item_code, item_subtype, title"),
              tags$li("Optional columns: description, population, mock_available, asr_ready")
            )
          ),
          
          fileInput(
            ns("bulk_tlf_file"),
            label = "Select Excel File",
            accept = c(".xlsx", ".xls"),
            buttonLabel = "Choose File",
            placeholder = "No file selected"
          )
        ),
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          actionButton(ns("cancel_bulk_tlf"), "Cancel", 
                      class = "btn btn-secondary"),
          actionButton(ns("process_bulk_tlf"), "Upload TLFs", 
                      icon = icon("upload"),
                      class = "btn btn-primary")
        )
      ))
    })
    
    # Process bulk TLF upload
    observeEvent(input$process_bulk_tlf, {
      if (is.null(input$bulk_tlf_file)) {
        showNotification("Please select a file", type = "warning")
        return()
      }
      
      effort_id <- current_reporting_effort_id()
      result <- bulk_upload_tlf_items(effort_id, input$bulk_tlf_file$datapath)
      
      if (!is.null(result$error)) {
        showNotification(paste("Bulk upload failed:", result$error), type = "error")
      } else {
        showNotification(paste("Successfully uploaded", result$created_count, "TLF items"), type = "message")
        load_items_data()
        removeModal()
      }
    })
    
    # Cancel bulk TLF upload
    observeEvent(input$cancel_bulk_tlf, {
      removeModal()
    })
    
    # Bulk Dataset upload
    observeEvent(input$bulk_dataset_clicked, {
      effort_id <- current_reporting_effort_id()
      if (is.null(effort_id) || effort_id == "") {
        showNotification("Please select a reporting effort first", type = "warning")
        return()
      }
      
      showModal(modalDialog(
        title = tagList(icon("upload"), " Bulk Upload Dataset Items"),
        size = "m",
        easyClose = FALSE,
        
        div(
          class = "mb-3",
          tags$p("Upload an Excel file containing Dataset items to add multiple items at once."),
          
          tags$div(
            class = "alert alert-info small",
            tags$strong("File Requirements:"),
            tags$ul(
              class = "mb-0 mt-2",
              tags$li("Excel file (.xlsx or .xls)"),
              tags$li("Required columns: item_code, item_subtype, dataset_name"),
              tags$li("Optional columns: description, location, locked")
            )
          ),
          
          fileInput(
            ns("bulk_dataset_file"),
            label = "Select Excel File",
            accept = c(".xlsx", ".xls"),
            buttonLabel = "Choose File",
            placeholder = "No file selected"
          )
        ),
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          actionButton(ns("cancel_bulk_dataset"), "Cancel", 
                      class = "btn btn-secondary"),
          actionButton(ns("process_bulk_dataset"), "Upload Datasets", 
                      icon = icon("upload"),
                      class = "btn btn-primary")
        )
      ))
    })
    
    # Process bulk Dataset upload
    observeEvent(input$process_bulk_dataset, {
      if (is.null(input$bulk_dataset_file)) {
        showNotification("Please select a file", type = "warning")
        return()
      }
      
      effort_id <- current_reporting_effort_id()
      result <- bulk_upload_dataset_items(effort_id, input$bulk_dataset_file$datapath)
      
      if (!is.null(result$error)) {
        showNotification(paste("Bulk upload failed:", result$error), type = "error")
      } else {
        showNotification(paste("Successfully uploaded", result$created_count, "Dataset items"), type = "message")
        load_items_data()
        removeModal()
      }
    })
    
    # Cancel bulk Dataset upload
    observeEvent(input$cancel_bulk_dataset, {
      removeModal()
    })
    
    # Copy from package
    observeEvent(input$copy_from_package_clicked, {
      effort_id <- current_reporting_effort_id()
      if (is.null(effort_id) || effort_id == "") {
        showNotification("Please select a reporting effort first", type = "warning")
        return()
      }
      
      packages <- packages_list()
      if (length(packages) == 0) {
        showNotification("No packages available", type = "warning")
        return()
      }
      
      # Create choices for packages
      package_choices <- setNames(
        sapply(packages, function(x) x$id),
        sapply(packages, function(x) x$package_name)
      )
      
      showModal(modalDialog(
        title = tagList(icon("copy"), " Copy Items from Package"),
        size = "m",
        easyClose = FALSE,
        
        div(
          class = "mb-3",
          tags$p("Select a package to copy all its items to this reporting effort."),
          
          selectInput(
            ns("copy_package_id"),
            "Select Package",
            choices = package_choices,
            width = "100%"
          ),
          
          tags$div(
            class = "alert alert-warning small",
            tags$strong("Note: "), "This will copy all items from the selected package. Duplicate item codes will be skipped."
          )
        ),
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          actionButton(ns("cancel_copy_package"), "Cancel", 
                      class = "btn btn-secondary"),
          actionButton(ns("process_copy_package"), "Copy Items", 
                      icon = icon("copy"),
                      class = "btn btn-primary")
        )
      ))
    })
    
    # Process copy from package
    observeEvent(input$process_copy_package, {
      if (is.null(input$copy_package_id) || input$copy_package_id == "") {
        showNotification("Please select a package", type = "warning")
        return()
      }
      
      effort_id <- current_reporting_effort_id()
      result <- copy_items_from_package(effort_id, input$copy_package_id)
      
      if (!is.null(result$error)) {
        showNotification(paste("Copy failed:", result$error), type = "error")
      } else {
        showNotification(paste("Successfully copied", result$copied_count, "items"), type = "message")
        load_items_data()
        removeModal()
      }
    })
    
    # Cancel copy from package
    observeEvent(input$cancel_copy_package, {
      removeModal()
    })
    
    # Copy from reporting effort
    observeEvent(input$copy_from_effort_clicked, {
      effort_id <- current_reporting_effort_id()
      if (is.null(effort_id) || effort_id == "") {
        showNotification("Please select a reporting effort first", type = "warning")
        return()
      }
      
      efforts <- reporting_efforts_list()
      if (length(efforts) == 0) {
        showNotification("No reporting efforts available", type = "warning")
        return()
      }
      
      # Filter out current effort and create choices
      other_efforts <- efforts[sapply(efforts, function(x) x$id != effort_id)]
      if (length(other_efforts) == 0) {
        showNotification("No other reporting efforts available to copy from", type = "warning")
        return()
      }
      
      effort_choices <- setNames(
        sapply(other_efforts, function(x) x$id),
        sapply(other_efforts, function(x) paste0(x$effort_name, " (", x$study_name, ")"))
      )
      
      showModal(modalDialog(
        title = tagList(icon("copy"), " Copy Items from Reporting Effort"),
        size = "m",
        easyClose = FALSE,
        
        div(
          class = "mb-3",
          tags$p("Select a reporting effort to copy all its items to the current reporting effort."),
          
          selectInput(
            ns("copy_effort_id"),
            "Select Source Reporting Effort",
            choices = effort_choices,
            width = "100%"
          ),
          
          tags$div(
            class = "alert alert-warning small",
            tags$strong("Note: "), "This will copy all items from the selected reporting effort. Duplicate item codes will be skipped."
          )
        ),
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          actionButton(ns("cancel_copy_effort"), "Cancel", 
                      class = "btn btn-secondary"),
          actionButton(ns("process_copy_effort"), "Copy Items", 
                      icon = icon("copy"),
                      class = "btn btn-primary")
        )
      ))
    })
    
    # Process copy from reporting effort
    observeEvent(input$process_copy_effort, {
      if (is.null(input$copy_effort_id) || input$copy_effort_id == "") {
        showNotification("Please select a reporting effort", type = "warning")
        return()
      }
      
      effort_id <- current_reporting_effort_id()
      result <- copy_items_from_reporting_effort(effort_id, input$copy_effort_id)
      
      if (!is.null(result$error)) {
        showNotification(paste("Copy failed:", result$error), type = "error")
      } else {
        showNotification(paste("Successfully copied", result$copied_count, "items"), type = "message")
        load_items_data()
        removeModal()
      }
    })
    
    # Cancel copy from reporting effort
    observeEvent(input$cancel_copy_effort, {
      removeModal()
    })
    
    # Export tracker data
    observeEvent(input$export_tracker_clicked, {
      effort_id <- current_reporting_effort_id()
      if (is.null(effort_id) || effort_id == "") {
        showNotification("Please select a reporting effort first", type = "warning")
        return()
      }
      
      showNotification("Export functionality will be implemented in a future release", type = "info")
    })
    
    # Import tracker data
    observeEvent(input$import_tracker_clicked, {
      effort_id <- current_reporting_effort_id()
      if (is.null(effort_id) || effort_id == "") {
        showNotification("Please select a reporting effort first", type = "warning")
        return()
      }
      
      showNotification("Import functionality will be implemented in a future release", type = "info")
    })
    
    # WebSocket event handling
    observeEvent(input$`reporting_effort_items-websocket_event`, {
      if (!is.null(input$`reporting_effort_items-websocket_event`)) {
        event_data <- input$`reporting_effort_items-websocket_event`
        if (startsWith(event_data$type, "reporting_effort_item_")) {
          load_items_data()
        }
      }
    })
    
  })
}