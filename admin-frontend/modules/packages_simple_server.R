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
    
    # Set up validation for package form
    iv_package <- InputValidator$new()
    iv_package$add_rule("new_package_name", sv_required())
    iv_package$add_rule("new_package_name", function(value) {
      if (nchar(trimws(value)) < 3) {
        "Package name must be at least 3 characters long"
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
      
      if (nrow(data) == 0) {
        empty_df <- data.frame(
          `Package Name` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE, check.names = FALSE
        )
        
        datatable(
          empty_df,
          options = list(
            dom = 'rtip',
            pageLength = 25,
            language = list(emptyTable = "No packages found"),
            columnDefs = list(
              list(targets = 1, searchable = FALSE, orderable = FALSE, width = '100px')
            )
          ),
          escape = FALSE,
          selection = 'none',
          rownames = FALSE
        )
      } else {
        # Add action buttons
        data$Actions <- sapply(data$ID, function(pkg_id) {
          sprintf(
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="%s" title="Edit package"><i class="fa fa-pencil"></i></button>
             <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" title="Delete package"><i class="fa fa-trash"></i></button>',
            pkg_id, pkg_id
          )
        })
        
        # Remove ID column for display
        display_df <- data[, c("Package Name", "Actions")]
        
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
              list(targets = 1, searchable = FALSE, orderable = FALSE, width = '100px')
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
              ns("packages_table"), ns("package_action_click"), ns("package_action_click")))
          ),
          escape = FALSE,
          selection = 'none',
          rownames = FALSE
        ) %>%
          DT::formatStyle(
            columns = 1:2,
            fontSize = '14px'
          )
      }
    })
    
    # Handle DataTable button clicks
    observeEvent(input$package_action_click, {
      info <- input$package_action_click
      if (!is.null(info)) {
        action <- info$action
        package_id <- as.integer(info$id)
        
        if (action == "edit") {
          cat("Edit package clicked, ID:", package_id, "\n")
          
          # Find the package data
          current_packages <- packages_data()
          package_row <- current_packages[current_packages$ID == package_id, ]
          
          if (nrow(package_row) > 0) {
            # Set editing mode
            editing_package_id(package_id)
            
            # Show edit modal
            showModal(modalDialog(
              title = tagList(icon("pencil"), " Edit Package"),
              size = "m",
              easyClose = FALSE,
              
              div(
                class = "mb-3",
                tags$label("Package Name", class = "form-label fw-bold"),
                textInput(ns("edit_modal_package_name"), NULL, 
                         value = package_row$`Package Name`[1], 
                         placeholder = "Enter package name", 
                         width = "100%")
              ),
              
              footer = div(
                class = "d-flex justify-content-end gap-2",
                actionButton(ns("cancel_edit_modal"), "Cancel", 
                            class = "btn btn-secondary"),
                actionButton(ns("save_edit_modal"), "Update Package", 
                            icon = icon("check"),
                            class = "btn btn-warning")
              )
            ))
          }
        } else if (action == "delete") {
          cat("Delete package clicked, ID:", package_id, "\n")
          
          # Find the package data
          current_packages <- packages_data()
          package_row <- current_packages[current_packages$ID == package_id, ]
          
          if (nrow(package_row) > 0) {
            showModal(modalDialog(
              title = tagList(icon("exclamation-triangle", class = "text-danger"), " Confirm Deletion"),
              tagList(
                tags$div(class = "alert alert-danger",
                  tags$strong("Warning: "), "This action cannot be undone!"
                ),
                tags$p("Are you sure you want to delete this package?"),
                tags$hr(),
                tags$dl(
                  tags$dt("Package Name:"),
                  tags$dd(tags$strong(package_row$`Package Name`[1]))
                )
              ),
              footer = tagList(
                actionButton(ns("confirm_delete_package"), "Delete Package", 
                            icon = icon("trash"),
                            class = "btn-danger"),
                modalButton("Cancel")
              ),
              easyClose = FALSE,
              size = "m"
            ))
            
            # Store the ID for deletion
            editing_package_id(package_id)
          }
        }
      }
    })
    
    # Toggle add package sidebar
    observeEvent(input$toggle_add_package, {
      # Reset form for new package
      editing_package_id(NULL)
      updateTextInput(session, "new_package_name", value = "")
      updateNumericInput(session, "edit_package_id", value = NULL)
      updateActionButton(session, "save_package", 
                       label = "Create",
                       icon = icon("check"))
      
      # Toggle sidebar (without namespace)
      sidebar_toggle(id = "packages_sidebar")
      
      # Disable validation until save is clicked
      iv_package$disable()
    })
    
    # Save package (create new package from sidebar)
    observeEvent(input$save_package, {
      # Enable validation and check
      iv_package$enable()
      if (iv_package$is_valid()) {
        cat("Save package clicked\n")
        
        package_name <- trimws(input$new_package_name)
        
        # Create new package
        cat("Creating new package:", package_name, "\n")
        result <- create_package(package_name)
          
        if (!is.null(result$error)) {
          showNotification(paste("Error creating package:", result$error), type = "error")
        } else {
          showNotification("Package created successfully", type = "message")
          load_packages_data()
          sidebar_toggle(id = "packages_sidebar")
          iv_package$disable()
          
          # Reset form
          updateTextInput(session, "new_package_name", value = "")
        }
      }
    })
    
    # Cancel button
    observeEvent(input$cancel_package, {
      sidebar_toggle(id = "packages_sidebar")
      editing_package_id(NULL)
      iv_package$disable()
      
      # Reset form
      updateTextInput(session, "new_package_name", value = "")
      updateNumericInput(session, "edit_package_id", value = NULL)
    })
    
    # Refresh button
    observeEvent(input$refresh_btn, {
      cat("Refresh button clicked\n")
      showNotification("Refreshing packages data...", type = "message", duration = 2)
      load_packages_data()
    })
    
    # Export to Excel button
    observeEvent(input$export_excel, {
      # Check if openxlsx is available
      if (!requireNamespace("openxlsx", quietly = TRUE)) {
        showNotification("Please install the 'openxlsx' package to export to Excel", type = "error")
        return()
      }
      
      # Get all packages data
      packages <- packages_data()
      
      if (nrow(packages) == 0) {
        showNotification("No packages to export", type = "warning")
        return()
      }
      
      # Create workbook
      wb <- openxlsx::createWorkbook()
      
      # Add Packages sheet
      openxlsx::addWorksheet(wb, "Packages")
      
      # Prepare packages data for export
      export_packages <- data.frame(
        ID = packages$ID,
        `Package Name` = packages$`Package Name`,
        check.names = FALSE
      )
      
      openxlsx::writeData(wb, "Packages", export_packages)
      
      # Add metadata sheet
      openxlsx::addWorksheet(wb, "Export Info")
      metadata <- data.frame(
        Property = c("Export Date", "Total Packages", "Exported By"),
        Value = c(
          format(Sys.time(), "%Y-%m-%d %H:%M:%S"),
          nrow(packages),
          "PEARL System"
        )
      )
      openxlsx::writeData(wb, "Export Info", metadata)
      
      # Style the workbook
      headerStyle <- openxlsx::createStyle(
        fontSize = 12,
        fontColour = "#FFFFFF",
        fgFill = "#4472C4",
        halign = "center",
        valign = "center",
        textDecoration = "bold"
      )
      
      # Apply styles to all sheets
      for (sheet in c("Packages", "Export Info")) {
        openxlsx::addStyle(wb, sheet, headerStyle, rows = 1, cols = 1:10, gridExpand = TRUE)
      }
      
      # Save the file
      filename <- paste0("PEARL_Packages_Export_", format(Sys.time(), "%Y%m%d_%H%M%S"), ".xlsx")
      filepath <- file.path(tempdir(), filename)
      openxlsx::saveWorkbook(wb, filepath, overwrite = TRUE)
      
      # Download the file
      showModal(modalDialog(
        title = "Export Complete",
        paste("Excel file has been generated:", filename),
        br(),
        downloadButton(ns("download_excel"), "Download Excel File"),
        footer = modalButton("Close")
      ))
      
      # Store filepath for download handler
      session$userData$export_filepath <- filepath
    })
    
    # Download handler for Excel export
    output$download_excel <- downloadHandler(
      filename = function() {
        paste0("PEARL_Packages_Export_", format(Sys.time(), "%Y%m%d_%H%M%S"), ".xlsx")
      },
      content = function(file) {
        if (!is.null(session$userData$export_filepath)) {
          file.copy(session$userData$export_filepath, file)
        }
      }
    )
    
    # Save edit modal
    observeEvent(input$save_edit_modal, {
      package_id <- editing_package_id()
      if (!is.null(package_id)) {
        package_name <- trimws(input$edit_modal_package_name)
        
        cat("Updating package ID:", package_id, "\n")
        result <- update_package(package_id, package_name)
        
        if (is.null(result$error)) {
          showNotification("Package updated successfully", type = "message")
          load_packages_data()
          removeModal()
          editing_package_id(NULL)
        } else {
          showNotification(paste("Error updating package:", result$error), type = "error")
        }
      }
    })
    
    # Cancel edit modal
    observeEvent(input$cancel_edit_modal, {
      removeModal()
      editing_package_id(NULL)
    })
    
    # Confirm delete package
    observeEvent(input$confirm_delete_package, {
      package_id <- editing_package_id()
      if (!is.null(package_id)) {
        cat("Deleting package ID:", package_id, "\n")
        result <- delete_package(package_id)
        
        if (is.null(result$error)) {
          showNotification("Package deleted successfully", type = "message")
          load_packages_data()
        } else {
          # Check if error is about associated items
          if (grepl("associated item", result$error, ignore.case = TRUE)) {
            showNotification(
              tagList(
                tags$strong("Cannot delete package"),
                tags$br(),
                "This package has associated items. Please delete all items first."
              ),
              type = "error",
              duration = 6
            )
          } else {
            showNotification(paste("Error deleting package:", result$error), type = "error")
          }
        }
        
        removeModal()
        editing_package_id(NULL)
      }
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
        
        # Check for required column (case-insensitive)
        col_names_lower <- tolower(names(df))
        package_col <- which(col_names_lower == "package name")[1]
        
        if (is.na(package_col)) {
          showNotification(
            "Excel file must contain 'Package Name' column",
            type = "error",
            duration = 5  # Duration in seconds
          )
          output$upload_results <- renderUI({
            div(class = "alert alert-danger small", 
                "Missing required column. File must have 'Package Name' column.")
          })
          return()
        }
        
        # Extract package names
        package_names <- as.character(df[[package_col]])
        
        # Validate and process each row
        results <- list(
          success = 0,
          duplicates = 0,
          empty_content = 0,
          too_short = 0,
          errors = 0,
          details = list()
        )
        
        # Get existing packages to check for duplicates
        existing_packages <- packages_data()
        existing_names <- character()
        if (nrow(existing_packages) > 0) {
          existing_names <- tolower(trimws(existing_packages$`Package Name`))
        }
        
        for (i in seq_along(package_names)) {
          # Skip empty rows
          if (is.na(package_names[i]) || trimws(package_names[i]) == "") {
            results$empty_content <- results$empty_content + 1
            next
          }
          
          package_name <- trimws(package_names[i])
          
          # Check minimum length
          if (nchar(package_name) < 3) {
            results$too_short <- results$too_short + 1
            results$details <- append(results$details,
              list(paste("Row", i, ": Package name too short - '", package_name, "' (min 3 characters)")))
            next
          }
          
          # Check for duplicate
          if (tolower(package_name) %in% existing_names) {
            results$duplicates <- results$duplicates + 1
            results$details <- append(results$details,
              list(paste("Row", i, ": Package already exists - '", package_name, "'")))
            next
          }
          
          # Create the package
          result <- create_package(package_name)
          
          if (!is.null(result$error)) {
            results$errors <- results$errors + 1
            # Check if it's a duplicate error from the backend
            if (grepl("already exists", result$error, ignore.case = TRUE)) {
              results$duplicates <- results$duplicates + 1
              results$errors <- results$errors - 1  # Adjust count
            }
          } else {
            results$success <- results$success + 1
            # Add to existing names to prevent duplicates within the same upload
            existing_names <- c(existing_names, tolower(package_name))
          }
        }
        
        # Display results with appropriate styling based on outcome
        if (results$success == 0 && results$duplicates > 0) {
          # All packages were duplicates
          output$upload_results <- renderUI({
            div(
              class = "alert alert-info small",
              tags$strong("No New Packages Added"),
              tags$p(
                class = "mb-2 mt-2",
                paste("All", results$duplicates, "package(s) in the file already exist in the database.")
              ),
              tags$small(
                class = "text-muted",
                "The system skipped duplicates to maintain unique package names."
              ),
              if (length(results$details) > 0 && length(results$details) <= 5) {
                tags$details(
                  tags$summary("Skipped packages"),
                  tags$ul(
                    class = "small",
                    lapply(results$details[1:min(5, length(results$details))], tags$li)
                  )
                )
              }
            )
          })
          
          showNotification(
            "No new packages imported - all packages already exist in the database",
            type = "warning",
            duration = 4  # Duration in seconds
          )
        } else if (results$success == 0) {
          # No packages were imported for other reasons
          output$upload_results <- renderUI({
            div(
              class = "alert alert-warning small",
              tags$strong("No Packages Imported"),
              tags$ul(
                class = "mb-0 mt-2",
                if (results$duplicates > 0) tags$li(paste("Already in database:", results$duplicates)),
                if (results$too_short > 0) tags$li(paste("Name too short:", results$too_short)),
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
            "No packages were imported. Check the details for more information.",
            type = "warning",
            duration = 4  # Duration in seconds
          )
        } else {
          # Some packages were successfully imported
          output$upload_results <- renderUI({
            div(
              class = "alert alert-success small",
              tags$strong("Upload Complete"),
              tags$ul(
                class = "mb-0 mt-2",
                tags$li(paste("Successfully created:", results$success, "packages")),
                if (results$duplicates > 0) tags$li(paste("Already in database (skipped):", results$duplicates)),
                if (results$too_short > 0) tags$li(paste("Name too short:", results$too_short)),
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
          load_packages_data()
          showNotification(
            paste("Successfully imported", results$success, "packages"),
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
    
    # Universal CRUD Manager integration (Phase 3)
    # Replaces entity-specific WebSocket observer with standardized refresh trigger
    observeEvent(input$`packages-crud_refresh`, {
      if (!is.null(input$`packages-crud_refresh`)) {
        cat("📦 Universal CRUD refresh triggered for packages\n")
        load_packages_data()
      }
    })
    
    # Legacy WebSocket observer (kept for backward compatibility during transition)
    observeEvent(input$`packages-websocket_event`, {
      if (!is.null(input$`packages-websocket_event`)) {
        event_data <- input$`packages-websocket_event`
        cat("📦 Legacy WebSocket event received:", event_data$type, "\n")
        if (startsWith(event_data$type, "package_")) {
          load_packages_data()
        }
      }
    })
    
  })
}