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
    database_releases_lookup <- reactiveVal(list())
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
        
        # Also load studies to get study names
        studies_result <- get_studies()
        studies_lookup <- list()
        if (!("error" %in% names(studies_result))) {
          for (study in studies_result) {
            studies_lookup[[as.character(study$id)]] <- study$title
          }
        }
        
        # Load database releases for label lookup
        db_rel_result <- get_database_releases()
        db_lookup <- list()
        if (!("error" %in% names(db_rel_result))) {
          for (rel in db_rel_result) {
            db_lookup[[as.character(rel$id)]] <- rel$database_release_label
          }
        }
        database_releases_lookup(db_lookup)
        
        # Create choices for select input with user-friendly names
        choices <- setNames(
          sapply(result, function(x) x$id),
          sapply(result, function(x) {
            study_name <- studies_lookup[[as.character(x$study_id)]] %||% paste0("Study ", x$study_id)
            db_label <- db_lookup[[as.character(x$database_release_id)]] %||% paste0("Release ", x$database_release_id)
            # x$database_release_label is the reporting effort label
            re_label <- x$database_release_label %||% paste0("Effort ", x$id)
            paste0(re_label, " (", study_name, ", ", db_label, ")")
          })
        )
        # Add empty option at the beginning
        choices <- c(setNames("", "Select a Reporting Effort"), choices)
        
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
      cat("DEBUG: load_items_data called with effort_id:", effort_id, "\n")
      
      if (is.null(effort_id) || effort_id == "") {
        cat("DEBUG: No effort_id, setting empty data frame\n")
        items_data(data.frame())
        return()
      }
      
      cat("DEBUG: Calling API for effort_id:", effort_id, "\n")
      result <- get_reporting_effort_items_by_effort(effort_id)
      
      if ("error" %in% names(result)) {
        cat("DEBUG: API returned error:", result$error, "\n")
        showNotification(paste("Error loading items:", result$error), type = "error")
        items_data(data.frame())
      } else {
        cat("DEBUG: API call successful, result length:", length(result), "\n")
        if (length(result) > 0) {
          cat("DEBUG: First item keys:", names(result[[1]]), "\n")
          cat("DEBUG: First item type:", result[[1]]$item_type, "code:", result[[1]]$item_code, "\n")
        }
        
        # Split items by type
        tlf_items <- list()
        dataset_items <- list()
        
        for (item in result) {
          if (item$item_type == "TLF") {
            tlf_items <- append(tlf_items, list(item))
          } else if (item$item_type == "Dataset") {
            dataset_items <- append(dataset_items, list(item))
          }
        }
        
        cat("DEBUG: Split items - TLF:", length(tlf_items), "Dataset:", length(dataset_items), "\n")
        
        # Convert to data frames separately
        tlf_df <- convert_tlf_to_df(tlf_items)
        dataset_df <- convert_dataset_to_df(dataset_items)
        
        cat("DEBUG: TLF data frame - rows:", nrow(tlf_df), "cols:", ncol(tlf_df), "\n")
        cat("DEBUG: Dataset data frame - rows:", nrow(dataset_df), "cols:", ncol(dataset_df), "\n")
        
        # Store both data frames (for backward compatibility, combine them)
        combined_df <- list()
        combined_df$tlf_items <- tlf_df
        combined_df$dataset_items <- dataset_df
        
        items_data(combined_df)
        last_update(Sys.time())
        cat("DEBUG: Data updated successfully\n")
      }
    }
    
    # Convert TLF items to data frame (matching Package Items format)
    convert_tlf_to_df <- function(items) {
      if (length(items) > 0) {
        df <- data.frame(
          ID = sapply(items, function(x) x$id),
          Type = sapply(items, function(x) x$item_subtype %||% ""),
          `Title Key` = sapply(items, function(x) x$item_code %||% ""),
          Title = sapply(items, function(x) {
            if (!is.null(x$tlf_details) && !is.null(x$tlf_details$title_id)) {
              # For now show Title ID (TODO: resolve to actual title text from text elements)
              paste0("Title ID: ", x$tlf_details$title_id)
            } else {
              ""
            }
          }),
          Population = sapply(items, function(x) {
            if (!is.null(x$tlf_details) && !is.null(x$tlf_details$population_flag_id)) {
              paste0("Pop ID: ", x$tlf_details$population_flag_id)
            } else {
              ""
            }
          }),
          `ICH Category` = sapply(items, function(x) {
            if (!is.null(x$tlf_details) && !is.null(x$tlf_details$ich_category_id)) {
              paste0("ICH ID: ", x$tlf_details$ich_category_id)
            } else {
              ""
            }
          }),

          Actions = sapply(items, function(x) x$id),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        return(df)
      } else {
        return(data.frame(
          ID = character(0),
          Type = character(0),
          `Title Key` = character(0),
          Title = character(0),
          Population = character(0),
          `ICH Category` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        ))
      }
    }
    
    # Convert Dataset items to data frame (matching Package Items format)
    convert_dataset_to_df <- function(items) {
      if (length(items) > 0) {
        df <- data.frame(
          ID = sapply(items, function(x) x$id),
          Type = sapply(items, function(x) x$item_subtype %||% ""),
          `Dataset Name` = sapply(items, function(x) x$item_code %||% ""),
          Label = sapply(items, function(x) {
            if (!is.null(x$dataset_details) && !is.null(x$dataset_details$label)) {
              x$dataset_details$label
            } else {
              ""
            }
          }),
          `Run Order` = sapply(items, function(x) {
            if (!is.null(x$dataset_details) && !is.null(x$dataset_details$sorting_order)) {
              x$dataset_details$sorting_order
            } else {
              ""
            }
          }),

          Actions = sapply(items, function(x) x$id),
          stringsAsFactors = FALSE,
          check.names = FALSE
        )
        
        # Sort by Run Order
        df <- df[order(as.numeric(df$`Run Order`)), ]
        
        return(df)
      } else {
        return(data.frame(
          ID = character(0),
          Type = character(0),
          `Dataset Name` = character(0),
          Label = character(0),
          `Run Order` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        ))
      }
    }
    
    # Ensure text elements list available (reuse from package module pattern)
    text_elements_list <- reactiveVal(list())
    load_text_elements <- function() {
      result <- get_text_elements()
      if (!"error" %in% names(result)) {
        text_elements_list(result)
      }
    }
    
    # Load data on initialization
    observe({
      load_reporting_efforts()
      load_packages()
      load_text_elements()
    })
    
    # Watch for reporting effort selection changes
    observeEvent(input$selected_reporting_effort, {
      effort_id <- input$selected_reporting_effort
      if (!is.null(effort_id) && effort_id != "") {
        current_reporting_effort_id(effort_id)
        load_items_data()
        # Highlight selector wrapper like package management
        shinyjs::runjs(sprintf(
          "$('#%s').addClass('has-selection');",
          ns("effort_selector_wrapper")
        ))
      } else {
        current_reporting_effort_id(NULL)
        items_data(data.frame())
        shinyjs::runjs(sprintf(
          "$('#%s').removeClass('has-selection');",
          ns("effort_selector_wrapper")
        ))
      }
    })

    # Render TLF header with selected reporting effort name
    output$tlf_header <- renderUI({
      effort_id <- current_reporting_effort_id()
      if (!is.null(effort_id) && effort_id != "") {
        efforts <- reporting_efforts_list()
        # Find selected effort
        selected_effort <- NULL
        for (e in efforts) {
          if (as.character(e$id) == as.character(effort_id)) {
            selected_effort <- e
            break
          }
        }
        if (!is.null(selected_effort)) {
          # Lookup study and DB names
          studies <- get_studies()
          study_name <- NULL
          if (!("error" %in% names(studies))) {
            for (s in studies) {
              if (as.character(s$id) == as.character(selected_effort$study_id)) {
                study_name <- s$title
                break
              }
            }
          }
          db_lookup <- database_releases_lookup()
          db_label <- db_lookup[[as.character(selected_effort$database_release_id)]] %||% paste0("Release ", selected_effort$database_release_id)
          re_label <- selected_effort$database_release_label %||% paste0("Effort ", selected_effort$id)
          label_text <- paste0(re_label, " (", if (!is.null(study_name)) study_name else paste0("Study ", selected_effort$study_id), ", ", db_label, ")")
          div(
            class = "alert alert-info py-2 mb-3 d-flex align-items-center",
            style = "background: linear-gradient(90deg, #cfe2ff 0%, #e7f1ff 100%); border-left: 4px solid #0d6efd;",
            icon("clipboard-list", class = "me-2"),
            tags$span(
              "Current Reporting Effort: ",
              tags$strong(label_text, class = "text-primary")
            )
          )
        } else {
          NULL
        }
      } else {
        NULL
      }
    })

    # Render Dataset header with selected reporting effort name
    output$dataset_header <- renderUI({
      effort_id <- current_reporting_effort_id()
      if (!is.null(effort_id) && effort_id != "") {
        efforts <- reporting_efforts_list()
        selected_effort <- NULL
        for (e in efforts) {
          if (as.character(e$id) == as.character(effort_id)) {
            selected_effort <- e
            break
          }
        }
        if (!is.null(selected_effort)) {
          studies <- get_studies()
          study_name <- NULL
          if (!("error" %in% names(studies))) {
            for (s in studies) {
              if (as.character(s$id) == as.character(selected_effort$study_id)) {
                study_name <- s$title
                break
              }
            }
          }
          db_lookup <- database_releases_lookup()
          db_label <- db_lookup[[as.character(selected_effort$database_release_id)]] %||% paste0("Release ", selected_effort$database_release_id)
          re_label <- selected_effort$database_release_label %||% paste0("Effort ", selected_effort$id)
          label_text <- paste0(re_label, " (", if (!is.null(study_name)) study_name else paste0("Study ", selected_effort$study_id), ", ", db_label, ")")
          div(
            class = "alert alert-info py-2 mb-3 d-flex align-items-center",
            style = "background: linear-gradient(90deg, #cfe2ff 0%, #e7f1ff 100%); border-left: 4px solid #0d6efd;",
            icon("clipboard-list", class = "me-2"),
            tags$span(
              "Current Reporting Effort: ",
              tags$strong(label_text, class = "text-primary")
            )
          )
        } else {
          NULL
        }
      } else {
        NULL
      }
    })
    
    # Render TLF items table
    output$tlf_table <- DT::renderDataTable({
      data_list <- items_data()
      cat("DEBUG: Rendering TLF table\n")
      
      # Get TLF data from the list structure
      tlf_data <- if (is.list(data_list) && !is.null(data_list$tlf_items)) {
        data_list$tlf_items
      } else {
        data.frame()
      }
      cat("DEBUG: TLF data rows:", nrow(tlf_data), "\n")
      
      if (nrow(tlf_data) == 0) {
        cat("DEBUG: No TLF data - rendering empty TLF table\n")
        empty_df <- data.frame(
          Type = character(0),
          `Title Key` = character(0),
          Title = character(0),
          Population = character(0),
          `ICH Category` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE, check.names = FALSE
        )
        
        datatable(
          empty_df,
          options = list(
            dom = 'rtip',
            pageLength = 25,
            language = list(emptyTable = "No TLF items found for this reporting effort"),
            columnDefs = list(
              list(targets = 5, searchable = FALSE, orderable = FALSE, width = '100px')
            )
          ),
          escape = FALSE,
          selection = 'none',
          rownames = FALSE
        )
      } else {
        cat("DEBUG: Rendering TLF table with data, rows:", nrow(tlf_data), "columns:", names(tlf_data), "\n")
        
        # Add action buttons  
        tlf_data$Actions <- sapply(tlf_data$ID, function(item_id) {
          sprintf(
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="%s" title="Edit item"><i class="fa fa-pencil"></i></button>
             <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" title="Delete item"><i class="fa fa-trash"></i></button>',
            item_id, item_id
          )
        })
        
        # Remove ID column for display (matching Package Items format)
        display_df <- tlf_data[, c("Type", "Title Key", "Title", "Population", "ICH Category", "Actions")]
        cat("DEBUG: TLF display data frame created, rows:", nrow(display_df), "columns:", names(display_df), "\n")
        if (nrow(display_df) > 0) {
          cat("DEBUG: First TLF display row:", paste(display_df[1,], collapse = " | "), "\n")
        }
        
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
              ns("tlf_table"), ns("item_action_click"), ns("item_action_click")))
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
    
    # Render Dataset items table
    output$dataset_table <- DT::renderDataTable({
      data_list <- items_data()
      cat("DEBUG: Rendering Dataset table\n")
      
      # Get Dataset data from the list structure
      dataset_data <- if (is.list(data_list) && !is.null(data_list$dataset_items)) {
        data_list$dataset_items
      } else {
        data.frame()
      }
      cat("DEBUG: Dataset data rows:", nrow(dataset_data), "\n")
      
      if (nrow(dataset_data) == 0) {
        cat("DEBUG: No Dataset data - rendering empty Dataset table\n")
        empty_df <- data.frame(
          Type = character(0),
          `Dataset Name` = character(0),
          Label = character(0),
          `Run Order` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE, check.names = FALSE
        )
        
        datatable(
          empty_df,
          options = list(
            dom = 'rtip',
            pageLength = 25,
            language = list(emptyTable = "No Dataset items found for this reporting effort"),
            columnDefs = list(
              list(targets = 4, searchable = FALSE, orderable = FALSE, width = '100px')
            )
          ),
          escape = FALSE,
          selection = 'none',
          rownames = FALSE
        )
      } else {
        cat("DEBUG: Rendering Dataset table with data, rows:", nrow(dataset_data), "columns:", names(dataset_data), "\n")
        
        # Add action buttons  
        dataset_data$Actions <- sapply(dataset_data$ID, function(item_id) {
          sprintf(
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="%s" title="Edit item"><i class="fa fa-pencil"></i></button>
             <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" title="Delete item"><i class="fa fa-trash"></i></button>',
            item_id, item_id
          )
        })
        
        # Remove ID column for display (matching Package Items format)
        display_df <- dataset_data[, c("Type", "Dataset Name", "Label", "Run Order", "Actions")]
        cat("DEBUG: Dataset display data frame created, rows:", nrow(display_df), "columns:", names(display_df), "\n")
        if (nrow(display_df) > 0) {
          cat("DEBUG: First Dataset display row:", paste(display_df[1,], collapse = " | "), "\n")
        }
        
        datatable(
          display_df,
          filter = 'top',
          options = list(
            dom = 'frtip',
            search = list(
              regex = TRUE,
              caseInsensitive = TRUE,
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
              ns("dataset_table"), ns("item_action_click"), ns("item_action_click")))
          ),
          escape = FALSE,
          selection = 'none',
          rownames = FALSE
        ) %>%
          DT::formatStyle(
            columns = 1:5,
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
          
          # Find the item data in the new list structure
          data_list <- items_data()
          item_row <- NULL
          
          # Check TLF items first
          if (is.list(data_list) && !is.null(data_list$tlf_items) && nrow(data_list$tlf_items) > 0) {
            tlf_match <- data_list$tlf_items[data_list$tlf_items$ID == item_id, ]
            if (nrow(tlf_match) > 0) {
              item_row <- tlf_match
            }
          }
          
          # If not found in TLF, check Dataset items
          if (is.null(item_row) && is.list(data_list) && !is.null(data_list$dataset_items) && nrow(data_list$dataset_items) > 0) {
            dataset_match <- data_list$dataset_items[data_list$dataset_items$ID == item_id, ]
            if (nrow(dataset_match) > 0) {
              item_row <- dataset_match
            }
          }
          
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
    
    # Render add item form based on current tab
    output$add_item_form <- renderUI({
      library(shinyWidgets)
      # Determine active tab from UI navset via input$item_tabs in session (default tlf)
      tab <- input$item_tabs %||% "tlf"
      # Prepare text element choices by type
      elements <- text_elements_list()
      title_choices <- c()
      population_choices <- c()
      ich_choices <- c()
      for (elem in elements) {
        if (elem$type == "title") {
          title_choices[elem$label] <- elem$id
        } else if (elem$type == "population_set") {
          population_choices[elem$label] <- elem$id
        } else if (elem$type == "ich_category") {
          ich_choices[elem$label] <- elem[id]
        }
      }
      if (tab == "tlf") {
        card(
          class = "border border-2",
          card_body(
            div(
              class = "mb-2",
              tags$label("TLF Type", class = "form-label fw-bold"),
              pickerInput(
                ns("tlf_subtype"), label = NULL,
                choices = c("Table", "Listing", "Figure"),
                options = list(style = "btn-outline-primary")
              )
            ),
            div(
              class = "mb-2",
              tags$label("Title Key", class = "form-label fw-bold"),
              textInput(ns("item_code"), label = NULL, placeholder = "e.g., t14.1.1")
            ),
            div(
              class = "mb-2",
              tags$label("Title", class = "form-label fw-bold"),
              selectizeInput(
                ns("tlf_title"), label = NULL,
                choices = title_choices,
                options = list(create = TRUE, placeholder = "Select or create new title...", maxItems = 1)
              )
            ),
            div(
              class = "mb-2",
              tags$label("Population Flag", class = "form-label"),
              selectizeInput(
                ns("tlf_population"), label = NULL,
                choices = population_choices,
                options = list(create = TRUE, placeholder = "Select or create new population...", maxItems = 1)
              )
            ),
            div(
              class = "mb-2",
              tags$label("ICH Category", class = "form-label"),
              selectizeInput(
                ns("tlf_ich"), label = NULL,
                choices = ich_choices,
                options = list(create = TRUE, placeholder = "Select or create new ICH category...", maxItems = 1)
              )
            ),
            layout_columns(
              col_widths = c(6, 6),
              gap = 2,
              actionButton(ns("save_item"), "Create", icon = icon("check"), class = "btn btn-success w-100"),
              actionButton(ns("cancel_item"), "Cancel", icon = icon("times"), class = "btn btn-secondary w-100")
            )
          )
        )
      } else {
        card(
          class = "border border-2",
          card_body(
            div(
              class = "mb-2",
              tags$label("Dataset Type", class = "form-label fw-bold"),
              pickerInput(
                ns("dataset_subtype"), label = NULL,
                choices = c("SDTM", "ADaM"),
                options = list(style = "btn-outline-primary")
              )
            ),
            div(
              class = "mb-2",
              tags$label("Dataset Name", class = "form-label fw-bold"),
              textInput(ns("item_code"), label = NULL, placeholder = "e.g., DM, AE, ADSL")
            ),
            div(
              class = "mb-2",
              tags$label("Label (optional)", class = "form-label"),
              textInput(ns("dataset_label"), label = NULL, placeholder = "e.g., Demographics")
            ),
            div(
              class = "mb-2",
              tags$label("Run Order", class = "form-label"),
              numericInput(ns("dataset_order"), label = NULL, value = 1, min = 1)
            ),
            layout_columns(
              col_widths = c(6, 6),
              gap = 2,
              actionButton(ns("save_item"), "Create", icon = icon("check"), class = "btn btn-success w-100"),
              actionButton(ns("cancel_item"), "Cancel", icon = icon("times"), class = "btn btn-secondary w-100")
            )
          )
        )
      }
    })
    
    # Save item (create or update)
    observeEvent(input$save_item, {
      iv_item$enable()
      if (iv_item$is_valid()) {
        cat("Save item clicked\n")
        effort_id <- current_reporting_effort_id()
        if (is.null(effort_id) || effort_id == "") {
          showNotification("Please select a reporting effort first", type = "error")
          return()
        }
        item_code <- trimws(input$item_code)
        # Determine current tab by which inputs exist
        is_tlf <- !is.null(input$tlf_subtype)
        if (is_tlf) {
          # Process text elements (create when user typed new)
          process_text_element <- function(value, type) {
            if (is.null(value) || is.na(value) || value == "") return(NULL)
            # If numeric ID chosen
            if (grepl("^[0-9]+$", value)) return(as.integer(value))
            # Otherwise create via API
            res <- create_text_element(list(type = type, label = value))
            if (!"error" %in% names(res)) {
              load_text_elements()
              return(res$id)
            }
            return(NULL)
          }
          title_id <- process_text_element(input$tlf_title, "title")
          pop_id <- process_text_element(input$tlf_population, "population_set")
          ich_id <- process_text_element(input$tlf_ich, "ich_category")
        item_data <- list(
            item_type = "TLF",
            item_subtype = input$tlf_subtype,
            item_code = item_code,
            is_active = TRUE,
            tlf_details = list(
              title_id = title_id,
              population_flag_id = pop_id,
              ich_category_id = ich_id
            ),
            footnotes = list(),
            acronyms = list()
          )
        } else {
          item_data <- list(
            item_type = "Dataset",
            item_subtype = input$dataset_subtype,
            item_code = item_code,
            is_active = TRUE,
            dataset_details = list(
              label = if (!is.null(input$dataset_label) && input$dataset_label != "") input$dataset_label else NULL,
              sorting_order = if (!is.null(input$dataset_order)) as.integer(input$dataset_order) else NULL
            ),
            footnotes = list(),
            acronyms = list()
          )
        }
        # Create via API
        result <- create_reporting_effort_item_with_details(as.integer(effort_id), item_data)
        if (!is.null(result$error)) {
          showNotification(paste("Error saving item:", result$error), type = "error")
        } else {
          showNotification("Item created successfully", type = "message")
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
    
    # Copy TLF items from package
    observeEvent(input$copy_tlf_from_package_clicked, {
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
        title = tagList(icon("copy"), " Copy TLF Items from Package"),
        size = "m",
        easyClose = FALSE,
        
        div(
          class = "mb-3",
          tags$p("Select a package to copy only TLF items to this reporting effort."),
          
          selectInput(
            ns("copy_tlf_package_id"),
            "Select Package",
            choices = package_choices,
            width = "100%"
          ),
          
          tags$div(
            class = "alert alert-info small",
            tags$strong("Note: "), "This will copy only TLF items from the selected package. Duplicate item codes will be skipped."
          )
        ),
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          actionButton(ns("cancel_copy_tlf_package"), "Cancel", 
                      class = "btn btn-secondary"),
          actionButton(ns("process_copy_tlf_package"), "Copy TLF Items", 
                      icon = icon("copy"),
                      class = "btn btn-primary")
        )
      ))
    })
    
    # Process copy TLF items from package
    observeEvent(input$process_copy_tlf_package, {
      if (is.null(input$copy_tlf_package_id) || input$copy_tlf_package_id == "") {
        showNotification("Please select a package", type = "warning")
        return()
      }
      
      effort_id <- current_reporting_effort_id()
      result <- copy_tlf_items_from_package(effort_id, input$copy_tlf_package_id)
      
      if (!is.null(result$error)) {
        showNotification(paste("Copy failed:", result$error), type = "error")
      } else {
        showNotification(paste("Successfully copied", result$copied_count, "TLF items"), type = "message")
        load_items_data()
        removeModal()
      }
    })
    
    # Cancel copy TLF items from package
    observeEvent(input$cancel_copy_tlf_package, {
      removeModal()
    })
    
    # Copy TLF items from reporting effort
    observeEvent(input$copy_tlf_from_effort_clicked, {
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
      
      # Load studies for name lookup
      studies_result <- get_studies()
      studies_lookup <- list()
      if (!("error" %in% names(studies_result))) {
        for (study in studies_result) {
          studies_lookup[[as.character(study$id)]] <- study$title
        }
      }
      
      effort_choices <- setNames(
        sapply(other_efforts, function(x) x$id),
        sapply(other_efforts, function(x) {
          study_name <- studies_lookup[[as.character(x$study_id)]] %||% paste0("Study ", x$study_id)
          paste0(x$database_release_label, " (", study_name, ")")
        })
      )
      
      showModal(modalDialog(
        title = tagList(icon("copy"), " Copy TLF Items from Reporting Effort"),
        size = "m",
        easyClose = FALSE,
        
        div(
          class = "mb-3",
          tags$p("Select a reporting effort to copy only TLF items to the current reporting effort."),
          
          selectInput(
            ns("copy_tlf_effort_id"),
            "Select Source Reporting Effort",
            choices = effort_choices,
            width = "100%"
          ),
          
          tags$div(
            class = "alert alert-info small",
            tags$strong("Note: "), "This will copy only TLF items from the selected reporting effort. Duplicate item codes will be skipped."
          )
        ),
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          actionButton(ns("cancel_copy_tlf_effort"), "Cancel", 
                      class = "btn btn-secondary"),
          actionButton(ns("process_copy_tlf_effort"), "Copy TLF Items", 
                      icon = icon("copy"),
                      class = "btn btn-primary")
        )
      ))
    })
    
    # Process copy TLF items from reporting effort
    observeEvent(input$process_copy_tlf_effort, {
      if (is.null(input$copy_tlf_effort_id) || input$copy_tlf_effort_id == "") {
        showNotification("Please select a reporting effort", type = "warning")
        return()
      }
      
      effort_id <- current_reporting_effort_id()
      result <- copy_tlf_items_from_reporting_effort(effort_id, input$copy_tlf_effort_id)
      
      if (!is.null(result$error)) {
        showNotification(paste("Copy failed:", result$error), type = "error")
      } else {
        showNotification(paste("Successfully copied", result$copied_count, "TLF items"), type = "message")
        load_items_data()
        removeModal()
      }
    })
    
    # Cancel copy TLF items from reporting effort
    observeEvent(input$cancel_copy_tlf_effort, {
      removeModal()
    })
    
    # Copy Dataset items from package
    observeEvent(input$copy_dataset_from_package_clicked, {
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
        title = tagList(icon("copy"), " Copy Dataset Items from Package"),
        size = "m",
        easyClose = FALSE,
        
        div(
          class = "mb-3",
          tags$p("Select a package to copy only Dataset items to this reporting effort."),
          
          selectInput(
            ns("copy_dataset_package_id"),
            "Select Package",
            choices = package_choices,
            width = "100%"
          ),
          
          tags$div(
            class = "alert alert-info small",
            tags$strong("Note: "), "This will copy only Dataset items from the selected package. Duplicate item codes will be skipped."
          )
        ),
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          actionButton(ns("cancel_copy_dataset_package"), "Cancel", 
                      class = "btn btn-secondary"),
          actionButton(ns("process_copy_dataset_package"), "Copy Dataset Items", 
                      icon = icon("copy"),
                      class = "btn btn-primary")
        )
      ))
    })
    
    # Process copy Dataset items from package
    observeEvent(input$process_copy_dataset_package, {
      if (is.null(input$copy_dataset_package_id) || input$copy_dataset_package_id == "") {
        showNotification("Please select a package", type = "warning")
        return()
      }
      
      effort_id <- current_reporting_effort_id()
      result <- copy_dataset_items_from_package(effort_id, input$copy_dataset_package_id)
      
      if (!is.null(result$error)) {
        showNotification(paste("Copy failed:", result$error), type = "error")
      } else {
        showNotification(paste("Successfully copied", result$copied_count, "Dataset items"), type = "message")
        load_items_data()
        removeModal()
      }
    })
    
    # Cancel copy Dataset items from package
    observeEvent(input$cancel_copy_dataset_package, {
      removeModal()
    })
    
    # Copy Dataset items from reporting effort
    observeEvent(input$copy_dataset_from_effort_clicked, {
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
      
      # Load studies for name lookup
      studies_result <- get_studies()
      studies_lookup <- list()
      if (!("error" %in% names(studies_result))) {
        for (study in studies_result) {
          studies_lookup[[as.character(study$id)]] <- study$title
        }
      }
      
      effort_choices <- setNames(
        sapply(other_efforts, function(x) x$id),
        sapply(other_efforts, function(x) {
          study_name <- studies_lookup[[as.character(x$study_id)]] %||% paste0("Study ", x$study_id)
          paste0(x$database_release_label, " (", study_name, ")")
        })
      )
      
      showModal(modalDialog(
        title = tagList(icon("copy"), " Copy Dataset Items from Reporting Effort"),
        size = "m",
        easyClose = FALSE,
        
        div(
          class = "mb-3",
          tags$p("Select a reporting effort to copy only Dataset items to the current reporting effort."),
          
          selectInput(
            ns("copy_dataset_effort_id"),
            "Select Source Reporting Effort",
            choices = effort_choices,
            width = "100%"
          ),
          
          tags$div(
            class = "alert alert-info small",
            tags$strong("Note: "), "This will copy only Dataset items from the selected reporting effort. Duplicate item codes will be skipped."
          )
        ),
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          actionButton(ns("cancel_copy_dataset_effort"), "Cancel", 
                      class = "btn btn-secondary"),
          actionButton(ns("process_copy_dataset_effort"), "Copy Dataset Items", 
                      icon = icon("copy"),
                      class = "btn btn-primary")
        )
      ))
    })
    
    # Process copy Dataset items from reporting effort
    observeEvent(input$process_copy_dataset_effort, {
      if (is.null(input$copy_dataset_effort_id) || input$copy_dataset_effort_id == "") {
        showNotification("Please select a reporting effort", type = "warning")
        return()
      }
      
      effort_id <- current_reporting_effort_id()
      result <- copy_dataset_items_from_reporting_effort(effort_id, input$copy_dataset_effort_id)
      
      if (!is.null(result$error)) {
        showNotification(paste("Copy failed:", result$error), type = "error")
      } else {
        showNotification(paste("Successfully copied", result$copied_count, "Dataset items"), type = "message")
        load_items_data()
        removeModal()
      }
    })
    
    # Cancel copy Dataset items from reporting effort
    observeEvent(input$cancel_copy_dataset_effort, {
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
    
    # Track current tab for bulk template/instructions
    current_tab <- reactiveVal("tlf")
    observeEvent(input$item_tabs, {
      current_tab(input$item_tabs)
      # Clear previous upload results when switching tabs
      output$upload_results <- renderUI({ NULL })
      shinyjs::reset("bulk_upload_file")
    })
    
    # Render dynamic template download based on current tab
    output$template_download <- renderUI({
      tab <- current_tab()
      if (tab == "tlf") {
        div(
          class = "mb-3",
          div(
            class = "d-grid gap-2",
            tags$a(
              href = "package_tlf_template.xlsx",
              download = "package_tlf_template.xlsx",
              class = "btn btn-outline-info btn-sm",
              tagList(icon("download"), " Download TLF Template")
            )
          ),
          tags$small(class = "text-muted d-block mt-2 text-center", "Template for TLF items upload")
        )
      } else {
        div(
          class = "mb-3",
          div(
            class = "d-grid gap-2",
            tags$a(
              href = "package_dataset_template.xlsx",
              download = "package_dataset_template.xlsx",
              class = "btn btn-outline-info btn-sm",
              tagList(icon("download"), " Download Dataset Template")
            )
          ),
          tags$small(class = "text-muted d-block mt-2 text-center", "Template for Dataset items upload")
        )
      }
    })

    # Render dynamic upload instructions based on current tab
    output$upload_instructions <- renderUI({
      tab <- current_tab()
      if (tab == "tlf") {
        div(
          class = "alert alert-info small",
          tags$strong("TLF File Requirements:"),
          tags$ul(
            class = "mb-0 mt-2",
            tags$li("Required columns: 'Title Key'"),
            tags$li("Optional columns: 'TLF Type', 'Title', 'Population', 'ICH Category', 'Run Order'"),
            tags$li("TLF Type: Table, Listing, or Figure (defaults to Table)"),
            tags$li("Text elements (Title, Population, ICH Category) will be created if new"),
            tags$li("Primary key: Type + Title Key + Title must be unique (ignoring case/spaces)")
          )
        )
      } else {
        div(
          class = "alert alert-info small",
          tags$strong("Dataset File Requirements:"),
          tags$ul(
            class = "mb-0 mt-2",
            tags$li("Required columns: 'Dataset Name', 'Run Order'"),
            tags$li("Optional columns: 'Dataset Type', 'Dataset Label'"),
            tags$li("Dataset Type: SDTM or ADaM (defaults to SDTM)"),
            tags$li("Run Order must be a positive number"),
            tags$li("Label provides description for the dataset")
          )
        )
      }
    })
    
  })
}