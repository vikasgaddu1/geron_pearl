# Package Items Server Module - Manage TLF and Dataset items

package_items_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Helper function for null coalescing
    `%||%` <- function(x, y) {
      if (is.null(x) || length(x) == 0) y else x
    }
    
    # Helper function to normalize text for duplicate checking
    normalize_text <- function(text) {
      if (is.null(text) || is.na(text) || text == "") {
        return("")
      }
      # Remove all spaces and convert to uppercase
      toupper(gsub("\\s+", "", trimws(text)))
    }
    
    # Helper function to check for TLF duplicates
    # Primary key: TLF Type + Title Key + Title (all three must be unique together)
    check_tlf_duplicate <- function(package_id, item_type, title_key, title_text, exclude_id = NULL) {
      current_items <- get_package_items(package_id)
      if ("error" %in% names(current_items)) {
        return(NULL)  # Can't check, assume no duplicate
      }
      
      # Normalize input values
      norm_type <- normalize_text(item_type)
      norm_title_key <- normalize_text(title_key)
      norm_title <- normalize_text(title_text)
      
      for (item in current_items) {
        # Skip if this is the item being edited
        if (!is.null(exclude_id) && item$id == exclude_id) {
          next
        }
        
        if (item$item_type == "TLF") {
          # Get existing values
          existing_type <- normalize_text(item$item_subtype)
          existing_key <- normalize_text(item$item_code)
          existing_title <- ""
          
          # Get existing title text from text elements
          if (!is.null(item$tlf_details) && !is.null(item$tlf_details$title_id)) {
            elements <- text_elements_list()
            for (elem in elements) {
              if (elem$id == item$tlf_details$title_id) {
                existing_title <- normalize_text(elem$label)
                break
              }
            }
          }
          
          # Check if all three components match (Type + Title Key + Title)
          if (norm_type == existing_type && norm_title_key == existing_key && norm_title == existing_title) {
            # Get original title text for display
            display_title <- ""
            if (!is.null(item$tlf_details) && !is.null(item$tlf_details$title_id)) {
              elements <- text_elements_list()
              for (elem in elements) {
                if (elem$id == item$tlf_details$title_id) {
                  display_title <- elem$label
                  break
                }
              }
            }
            
            if (display_title != "") {
              return(paste0("A ", item$item_subtype, " with Title Key '", item$item_code, "' and Title '", display_title, "' already exists in this package"))
            } else {
              return(paste0("A ", item$item_subtype, " with Title Key '", item$item_code, "' (no title) already exists in this package"))
            }
          }
        }
      }
      
      return(NULL)  # No duplicate found
    }
    
    # Helper function to check for Dataset duplicates
    check_dataset_duplicate <- function(package_id, dataset_type, dataset_name, exclude_id = NULL) {
      current_items <- get_package_items(package_id)
      if ("error" %in% names(current_items)) {
        return(NULL)  # Can't check, assume no duplicate
      }
      
      # Normalize input values
      norm_type <- normalize_text(dataset_type)
      norm_name <- normalize_text(dataset_name)
      
      for (item in current_items) {
        # Skip if this is the item being edited
        if (!is.null(exclude_id) && item$id == exclude_id) {
          next
        }
        
        if (item$item_type == "Dataset") {
          # Check Dataset Type and Dataset Name combination
          existing_type <- normalize_text(item$item_subtype)
          existing_name <- normalize_text(item$item_code)
          
          if (norm_type == existing_type && norm_name == existing_name) {
            return(paste("A", item$item_subtype, "dataset with name '", item$item_code, "' already exists in this package", sep = " "))
          }
        }
      }
      
      return(NULL)  # No duplicate found
    }
    
    # Reactive values
    packages_list <- reactiveVal(list())
    tlf_data <- reactiveVal(data.frame())
    dataset_data <- reactiveVal(data.frame())
    text_elements_list <- reactiveVal(list())
    last_update <- reactiveVal(Sys.time())
    current_tab <- reactiveVal("tlf")
    is_editing <- reactiveVal(FALSE)
    editing_item_id <- reactiveVal(NULL)
    deleting_item_id <- reactiveVal(NULL)
    deleting_item_type <- reactiveVal(NULL)
    
    # Load packages for dropdown
    load_packages <- function() {
      result <- get_packages()
      
      # Debug logging
      cat("API Response type:", class(result), "\n")
      cat("API Response length:", length(result), "\n")
      
      if (!"error" %in% names(result)) {
        packages_list(result)
        
        # Create choices for selectizeInput
        if (length(result) > 0) {
          # Debug first package
          cat("First package:\n")
          print(str(result[[1]]))
          
          # Create a named vector for choices
          choices <- character(0)
          choice_names <- character(0)
          
          for (i in seq_along(result)) {
            pkg <- result[[i]]
            # Get ID
            pkg_id <- if (!is.null(pkg$id)) as.character(pkg$id) else as.character(i)
            # Get name with fallback
            pkg_name <- if (!is.null(pkg$package_name)) {
              as.character(pkg$package_name)
            } else {
              paste0("Package #", pkg_id)
            }
            
            choices <- c(choices, pkg_id)
            choice_names <- c(choice_names, pkg_name)
          }
          
          names(choices) <- choice_names
          
          cat("Final choices:\n")
          print(choices)
          
          updateSelectizeInput(session, "selected_package", 
                              choices = choices,
                              server = FALSE)
        } else {
          # No packages available
          updateSelectizeInput(session, "selected_package", 
                              choices = character(0),
                              server = FALSE)
        }
      } else {
        cat("Error loading packages:", result$error, "\n")
      }
    }
    
    # Load text elements for dropdowns
    load_text_elements <- function() {
      result <- get_text_elements()
      if (!"error" %in% names(result)) {
        text_elements_list(result)
      }
    }
    
    # Load package items
    load_package_items <- function() {
      pkg_id <- input$selected_package
      if (!is.null(pkg_id) && pkg_id != "") {
        result <- get_package_items(pkg_id)
        if (!"error" %in% names(result)) {
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
          
          # Convert to data frames
          tlf_df <- convert_tlf_to_df(tlf_items)
          dataset_df <- convert_dataset_to_df(dataset_items)
          
          tlf_data(tlf_df)
          dataset_data(dataset_df)
          last_update(Sys.time())
        }
      } else {
        tlf_data(data.frame())
        dataset_data(data.frame())
      }
    }
    
    # Convert TLF items to data frame
    convert_tlf_to_df <- function(items) {
      if (length(items) > 0) {
        df <- data.frame(
          ID = sapply(items, function(x) x$id),
          Type = sapply(items, function(x) x$item_subtype %||% ""),
          `Title Key` = sapply(items, function(x) x$item_code %||% ""),
          Title = sapply(items, function(x) {
            if (!is.null(x$tlf_details) && !is.null(x$tlf_details$title_id)) {
              # Look up title text from text elements
              elements <- text_elements_list()
              for (elem in elements) {
                if (elem$id == x$tlf_details$title_id) {
                  return(elem$label)
                }
              }
            }
            return("")
          }),
          Population = sapply(items, function(x) {
            if (!is.null(x$tlf_details) && !is.null(x$tlf_details$population_flag_id)) {
              elements <- text_elements_list()
              for (elem in elements) {
                if (elem$id == x$tlf_details$population_flag_id) {
                  return(elem$label)
                }
              }
            }
            return("")
          }),
          `ICH Category` = sapply(items, function(x) {
            if (!is.null(x$tlf_details) && !is.null(x$tlf_details$ich_category_id)) {
              elements <- text_elements_list()
              for (elem in elements) {
                if (elem$id == x$tlf_details$ich_category_id) {
                  return(elem$label)
                }
              }
            }
            return("")
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
          Code = character(0),
          Title = character(0),
          Population = character(0),
          `ICH Category` = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE,
          check.names = FALSE
        ))
      }
    }
    
    # Convert Dataset items to data frame
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
    
    # Initialize on startup
    observe({
      load_packages()
      load_text_elements()
    })
    
    # Package reminder when no package is selected
    output$package_reminder <- renderUI({
      if (is.null(input$selected_package) || input$selected_package == "") {
        div(
          class = "alert alert-warning d-flex align-items-center mx-3 mt-3",
          style = "border-left: 5px solid #ffc107;",
          icon("exclamation-triangle", class = "me-2"),
          tags$strong("Please select a package from the dropdown above to view and manage its items.")
        )
      } else {
        NULL
      }
    })
    
    # Disable/enable Add Item button based on package selection
    observe({
      if (is.null(input$selected_package) || input$selected_package == "") {
        shinyjs::disable("toggle_add_item")
      } else {
        shinyjs::enable("toggle_add_item")
      }
    })
    
    # Reload items when package changes
    observeEvent(input$selected_package, {
      load_package_items()
      
      # Clear upload results when changing package
      output$upload_results <- renderUI({
        NULL
      })
      
      # Reset file input
      shinyjs::reset("bulk_upload_file")
      
      # Update package selector visual state
      if (!is.null(input$selected_package) && input$selected_package != "") {
        shinyjs::runjs(sprintf("
          $('#%s').removeClass('package-selector-wrapper').addClass('package-selector-wrapper has-selection');
        ", ns("package_selector_wrapper")))
      } else {
        shinyjs::runjs(sprintf("
          $('#%s').removeClass('has-selection');
        ", ns("package_selector_wrapper")))
      }
    })
    
    # Track current tab and clear upload results when switching
    observeEvent(input$item_tabs, {
      current_tab(input$item_tabs)
      
      # Clear upload results when switching tabs
      output$upload_results <- renderUI({
        NULL
      })
      
      # Reset the file input when switching tabs
      shinyjs::reset("bulk_upload_file")
      
      cat("Tab switched to:", input$item_tabs, "- Clearing upload results\n")
    })
    
    # Render TLF header with package name
    output$tlf_header <- renderUI({
      pkg_id <- input$selected_package
      if (!is.null(pkg_id) && pkg_id != "") {
        pkgs <- packages_list()
        pkg_name <- NULL
        for (pkg in pkgs) {
          if (pkg$id == as.integer(pkg_id)) {
            pkg_name <- pkg$package_name
            break
          }
        }
        if (!is.null(pkg_name)) {
          div(
            class = "alert alert-info py-2 mb-3 d-flex align-items-center",
            style = "background: linear-gradient(90deg, #cfe2ff 0%, #e7f1ff 100%); border-left: 4px solid #0d6efd;",
            icon("box", class = "me-2"),
            tags$span(
              "Viewing TLF items for package: ",
              tags$strong(pkg_name, class = "text-primary")
            )
          )
        } else {
          NULL
        }
      } else {
        NULL
      }
    })
    
    # Render Dataset header with package name
    output$dataset_header <- renderUI({
      pkg_id <- input$selected_package
      if (!is.null(pkg_id) && pkg_id != "") {
        pkgs <- packages_list()
        pkg_name <- NULL
        for (pkg in pkgs) {
          if (pkg$id == as.integer(pkg_id)) {
            pkg_name <- pkg$package_name
            break
          }
        }
        if (!is.null(pkg_name)) {
          div(
            class = "alert alert-info py-2 mb-3 d-flex align-items-center",
            style = "background: linear-gradient(90deg, #cfe2ff 0%, #e7f1ff 100%); border-left: 4px solid #0d6efd;",
            icon("database", class = "me-2"),
            tags$span(
              "Viewing Dataset items for package: ",
              tags$strong(pkg_name, class = "text-primary")
            )
          )
        } else {
          NULL
        }
      } else {
        NULL
      }
    })
    
    # Render TLF table
    output$tlf_table <- DT::renderDataTable({
      data <- tlf_data()
      
      if (nrow(data) > 0) {
        data$Actions <- sapply(data$ID, function(item_id) {
          sprintf(
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="%s" data-type="tlf" title="Edit TLF item"><i class="fa fa-pencil"></i></button>
             <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" data-type="tlf" title="Delete TLF item"><i class="fa fa-trash"></i></button>',
            item_id, item_id
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
            emptyTable = "No TLF items found",
            searchPlaceholder = "Type to search..."
          ),
          columnDefs = list(
            list(targets = 0, visible = FALSE),  # Hide ID column
            list(targets = 6, searchable = FALSE, sortable = FALSE, width = '100px')  # Actions column
          ),
          search = list(regex = TRUE, caseInsensitive = TRUE),
          drawCallback = JS(sprintf(
            "function(){
              var tbl = $('#%s');
              tbl.find('button[data-action=\\'edit\\']').off('click').on('click', function(){
                var id = $(this).attr('data-id');
                var type = $(this).attr('data-type');
                Shiny.setInputValue('%s', {action: 'edit', id: id, type: type}, {priority: 'event'});
              });
              tbl.find('button[data-action=\\'delete\\']').off('click').on('click', function(){
                var id = $(this).attr('data-id');
                var type = $(this).attr('data-type');
                Shiny.setInputValue('%s', {action: 'delete', id: id, type: type}, {priority: 'event'});
              });
            }",
            ns("tlf_table"), ns("item_action_click"), ns("item_action_click")))
        ),
        rownames = FALSE
      )
    })
    
    # Render Dataset table
    output$dataset_table <- DT::renderDataTable({
      data <- dataset_data()
      
      if (nrow(data) > 0) {
        data$Actions <- sapply(data$ID, function(item_id) {
          sprintf(
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="%s" data-type="dataset" title="Edit dataset item"><i class="fa fa-pencil"></i></button>
             <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" data-type="dataset" title="Delete dataset item"><i class="fa fa-trash"></i></button>',
            item_id, item_id
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
            emptyTable = "No dataset items found",
            searchPlaceholder = "Type to search..."
          ),
          columnDefs = list(
            list(targets = 0, visible = FALSE),  # Hide ID column
            list(targets = 5, searchable = FALSE, sortable = FALSE, width = '100px')  # Actions column
          ),
          search = list(regex = TRUE, caseInsensitive = TRUE),
          drawCallback = JS(sprintf(
            "function(){
              var tbl = $('#%s');
              tbl.find('button[data-action=\\'edit\\']').off('click').on('click', function(){
                var id = $(this).attr('data-id');
                var type = $(this).attr('data-type');
                Shiny.setInputValue('%s', {action: 'edit', id: id, type: type}, {priority: 'event'});
              });
              tbl.find('button[data-action=\\'delete\\']').off('click').on('click', function(){
                var id = $(this).attr('data-id');
                var type = $(this).attr('data-type');
                Shiny.setInputValue('%s', {action: 'delete', id: id, type: type}, {priority: 'event'});
              });
            }",
            ns("dataset_table"), ns("item_action_click"), ns("item_action_click")))
        ),
        rownames = FALSE
      )
    })
    
    # Handle DataTable button clicks for both TLF and Dataset items
    observeEvent(input$item_action_click, {
      info <- input$item_action_click
      if (!is.null(info)) {
        action <- info$action
        item_id <- as.integer(info$id)
        item_type <- info$type
        
        cat("Item action clicked - Action:", action, "ID:", item_id, "Type:", item_type, "\n")
        
        if (action == "edit") {
          if (item_type == "tlf") {
            # Store editing item info
            editing_item_id(item_id)
            is_editing(TRUE)
            
            # Get current TLF data
            current_items <- tlf_data()
            item_row <- current_items[current_items$ID == item_id, ]
            
            if (nrow(item_row) > 0) {
              # Find the original item data from the API
              pkg_id <- input$selected_package
              if (!is.null(pkg_id) && pkg_id != "") {
                result <- get_package_items(pkg_id)
                if (!"error" %in% names(result)) {
                  # Find the specific TLF item
                  tlf_item <- NULL
                  for (item in result) {
                    if (item$id == item_id && item$item_type == "TLF") {
                      tlf_item <- item
                      break
                    }
                  }
                  
                  if (!is.null(tlf_item)) {
                    # Show edit modal for TLF item
                    showModal(modalDialog(
                      title = tagList(icon("pencil"), " Edit TLF Item"),
                      size = "l",
                      easyClose = FALSE,
                      
                      # TLF edit form
                      div(
                        class = "container-fluid",
                        
                        # Item type and code
                        div(
                          class = "row mb-3",
                          div(
                            class = "col-md-6",
                            tags$label("TLF Type", class = "form-label fw-bold"),
                            selectInput(
                              ns("edit_tlf_type"),
                              label = NULL,
                              choices = c("Table", "Listing", "Figure"),
                              selected = tlf_item$item_subtype %||% "Table"
                            )
                          ),
                          div(
                            class = "col-md-6",
                            tags$label("Title Key", class = "form-label fw-bold"),
                            textInput(
                              ns("edit_tlf_code"),
                              label = NULL,
                              value = tlf_item$item_code %||% "",
                              placeholder = "e.g., t14.1.1"
                            )
                          )
                        ),
                        
                        # Title, Population, ICH Category
                        div(
                          class = "row mb-3",
                          div(
                            class = "col-md-4",
                            tags$label("Title", class = "form-label"),
                            selectizeInput(
                              ns("edit_tlf_title"),
                              label = NULL,
                              choices = NULL,  # Will be populated
                              selected = if (!is.null(tlf_item$tlf_details) && !is.null(tlf_item$tlf_details$title_id)) tlf_item$tlf_details$title_id else NULL,
                              options = list(
                                create = TRUE,
                                placeholder = "Select or create new title...",
                                maxItems = 1
                              )
                            )
                          ),
                          div(
                            class = "col-md-4",
                            tags$label("Population Flag", class = "form-label"),
                            selectizeInput(
                              ns("edit_tlf_population"),
                              label = NULL,
                              choices = NULL,  # Will be populated
                              selected = if (!is.null(tlf_item$tlf_details) && !is.null(tlf_item$tlf_details$population_flag_id)) tlf_item$tlf_details$population_flag_id else NULL,
                              options = list(
                                create = TRUE,
                                placeholder = "Select or create new population...",
                                maxItems = 1
                              )
                            )
                          ),
                          div(
                            class = "col-md-4",
                            tags$label("ICH Category", class = "form-label"),
                            selectizeInput(
                              ns("edit_tlf_ich"),
                              label = NULL,
                              choices = NULL,  # Will be populated
                              selected = if (!is.null(tlf_item$tlf_details) && !is.null(tlf_item$tlf_details$ich_category_id)) tlf_item$tlf_details$ich_category_id else NULL,
                              options = list(
                                create = TRUE,
                                placeholder = "Select or create new ICH category...",
                                maxItems = 1
                              )
                            )
                          )
                        ),
                        
                        # Footnotes and Acronyms
                        div(
                          class = "row mb-3",
                          div(
                            class = "col-md-6",
                            tags$label("Footnotes", class = "form-label"),
                            selectizeInput(
                              ns("edit_tlf_footnotes"),
                              label = NULL,
                              choices = NULL,  # Will be populated
                              multiple = TRUE,
                              options = list(
                                create = TRUE,
                                placeholder = "Select or create footnotes..."
                              )
                            )
                          ),
                          div(
                            class = "col-md-6",
                            tags$label("Acronyms", class = "form-label"),
                            selectizeInput(
                              ns("edit_tlf_acronyms"),
                              label = NULL,
                              choices = NULL,  # Will be populated
                              multiple = TRUE,
                              options = list(
                                create = TRUE,
                                placeholder = "Select or create acronyms..."
                              )
                            )
                          )
                        )
                      ),
                      
                      footer = tagList(
                        actionButton(
                          ns("save_edit_tlf"),
                          "Update Item",
                          icon = icon("check"),
                          class = "btn btn-success"
                        ),
                        modalButton("Cancel")
                      )
                    ))
                    
                    # Populate the selectize inputs with current values
                    populate_edit_selectize_inputs(tlf_item)
                  }
                }
              }
            }
          } else if (item_type == "dataset") {
            # Store editing item info
            editing_item_id(item_id)
            is_editing(TRUE)
            
            # Get current Dataset data
            current_items <- dataset_data()
            item_row <- current_items[current_items$ID == item_id, ]
            
            if (nrow(item_row) > 0) {
              # Find the original item data from the API
              pkg_id <- input$selected_package
              if (!is.null(pkg_id) && pkg_id != "") {
                result <- get_package_items(pkg_id)
                if (!"error" %in% names(result)) {
                  # Find the specific Dataset item
                  dataset_item <- NULL
                  for (item in result) {
                    if (item$id == item_id && item$item_type == "Dataset") {
                      dataset_item <- item
                      break
                    }
                  }
                  
                  if (!is.null(dataset_item)) {
                    # Show edit modal for Dataset item
                    showModal(modalDialog(
                      title = tagList(icon("pencil"), " Edit Dataset Item"),
                      size = "m",
                      easyClose = FALSE,
                      
                      # Dataset edit form
                      div(
                        class = "container-fluid",
                        
                        # Item type and code
                        div(
                          class = "row mb-3",
                          div(
                            class = "col-md-6",
                            tags$label("Dataset Type", class = "form-label fw-bold"),
                            selectInput(
                              ns("edit_dataset_type"),
                              label = NULL,
                              choices = c("SDTM", "ADaM"),
                              selected = dataset_item$item_subtype %||% "SDTM"
                            )
                          ),
                          div(
                            class = "col-md-6",
                            tags$label("Dataset Name", class = "form-label fw-bold"),
                            textInput(
                              ns("edit_dataset_code"),
                              label = NULL,
                              value = dataset_item$item_code %||% "",
                              placeholder = "e.g., DM, AE, ADSL"
                            )
                          )
                        ),
                        
                        # Label and Run Order
                        div(
                          class = "row mb-3",
                          div(
                            class = "col-md-8",
                            tags$label("Dataset Label", class = "form-label"),
                            textInput(
                              ns("edit_dataset_label"),
                              label = NULL,
                              value = if (!is.null(dataset_item$dataset_details) && !is.null(dataset_item$dataset_details$label)) dataset_item$dataset_details$label else "",
                              placeholder = "e.g., Demographics"
                            )
                          ),
                          div(
                            class = "col-md-4",
                            tags$label("Run Order", class = "form-label"),
                            numericInput(
                              ns("edit_dataset_order"),
                              label = NULL,
                              value = if (!is.null(dataset_item$dataset_details) && !is.null(dataset_item$dataset_details$sorting_order)) dataset_item$dataset_details$sorting_order else 1,
                              min = 1
                            )
                          )
                        )
                      ),
                      
                      footer = tagList(
                        actionButton(
                          ns("save_edit_dataset"),
                          "Update Item",
                          icon = icon("check"),
                          class = "btn btn-success"
                        ),
                        modalButton("Cancel")
                      )
                    ))
                  }
                }
              }
            }
          }
        } else if (action == "delete") {
          # Store the item ID and type for deletion
          deleting_item_id(item_id)
          deleting_item_type(item_type)
          
          if (item_type == "tlf") {
            # Show delete confirmation for TLF item
            current_items <- tlf_data()
            item_row <- current_items[current_items$ID == item_id, ]
            
            if (nrow(item_row) > 0) {
              showModal(modalDialog(
                title = tagList(icon("exclamation-triangle", class = "text-danger"), " Confirm Deletion"),
                tagList(
                  tags$div(class = "alert alert-danger",
                    tags$strong("Warning: "), "This action cannot be undone!"
                  ),
                  tags$p("Are you sure you want to delete this TLF item?"),
                  tags$hr(),
                  tags$dl(
                    tags$dt("Type:"),
                    tags$dd(tags$strong(item_row$Type[1])),
                    tags$dt("Title Key:"),
                    tags$dd(tags$strong(item_row$`Title Key`[1])),
                    if (!is.na(item_row$Title[1]) && item_row$Title[1] != "") {
                      tagList(
                        tags$dt("Title:"),
                        tags$dd(item_row$Title[1])
                      )
                    }
                  )
                ),
                footer = tagList(
                  actionButton(ns("confirm_delete_tlf"), "Delete Item", 
                              icon = icon("trash"),
                              class = "btn-danger"),
                  modalButton("Cancel")
                ),
                easyClose = FALSE,
                size = "m"
              ))
            }
          } else if (item_type == "dataset") {
            # Show delete confirmation for Dataset item
            current_items <- dataset_data()
            item_row <- current_items[current_items$ID == item_id, ]
            
            if (nrow(item_row) > 0) {
              showModal(modalDialog(
                title = tagList(icon("exclamation-triangle", class = "text-danger"), " Confirm Deletion"),
                tagList(
                  tags$div(class = "alert alert-danger",
                    tags$strong("Warning: "), "This action cannot be undone!"
                  ),
                  tags$p("Are you sure you want to delete this dataset item?"),
                  tags$hr(),
                  tags$dl(
                    tags$dt("Type:"),
                    tags$dd(tags$strong(item_row$Type[1])),
                    tags$dt("Dataset Name:"),
                    tags$dd(tags$strong(item_row$`Dataset Name`[1])),
                    if (!is.na(item_row$Label[1]) && item_row$Label[1] != "") {
                      tagList(
                        tags$dt("Label:"),
                        tags$dd(item_row$Label[1])
                      )
                    }
                  )
                ),
                footer = tagList(
                  actionButton(ns("confirm_delete_dataset"), "Delete Item", 
                              icon = icon("trash"),
                              class = "btn-danger"),
                  modalButton("Cancel")
                ),
                easyClose = FALSE,
                size = "m"
              ))
            }
          }
        }
      }
    })
    
    # Confirm delete TLF item
    observeEvent(input$confirm_delete_tlf, {
      item_id <- deleting_item_id()
      
      if (!is.null(item_id)) {
        cat("Deleting TLF item ID:", item_id, "\n")
        result <- delete_package_item(item_id)
        
        if (is.null(result$error)) {
          showNotification("TLF item deleted successfully", type = "message", duration = 3)
          load_package_items()
        } else {
          showNotification(paste("Error deleting item:", result$error), type = "error", duration = 5)
        }
        
        # Clear the reactive values
        deleting_item_id(NULL)
        deleting_item_type(NULL)
        
        removeModal()
      }
    })
    
    # Confirm delete Dataset item
    observeEvent(input$confirm_delete_dataset, {
      item_id <- deleting_item_id()
      
      if (!is.null(item_id)) {
        cat("Deleting Dataset item ID:", item_id, "\n")
        result <- delete_package_item(item_id)
        
        if (is.null(result$error)) {
          showNotification("Dataset item deleted successfully", type = "message", duration = 3)
          load_package_items()
        } else {
          showNotification(paste("Error deleting item:", result$error), type = "error", duration = 5)
        }
        
        # Clear the reactive values
        deleting_item_id(NULL)
        deleting_item_type(NULL)
        
        removeModal()
      }
    })
    
    # Toggle add item sidebar
    observeEvent(input$toggle_add_item, {
      if (is.null(input$selected_package) || input$selected_package == "") {
        showNotification(
          "Please select a package first",
          type = "warning",
          duration = 3
        )
      } else {
        # Reset form for new item
        editing_item_id(NULL)
        updateNumericInput(session, "edit_item_id", value = NA)
        
        # Clear any previous upload results
        output$upload_results <- renderUI({
          NULL
        })
        
        # Reset file input
        shinyjs::reset("bulk_upload_file")
        
        # Toggle sidebar (without namespace)
        sidebar_toggle(id = "items_sidebar")
      }
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
              tagList(
                icon("download"),
                " Download TLF Template"
              )
            )
          ),
          tags$small(
            class = "text-muted d-block mt-2 text-center",
            "Template for TLF items upload"
          )
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
              tagList(
                icon("download"),
                " Download Dataset Template"
              )
            )
          ),
          tags$small(
            class = "text-muted d-block mt-2 text-center",
            "Template for Dataset items upload"
          )
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
            tags$li("Label provides description for the dataset"),
            tags$li("Duplicates checked: Type + Dataset Name (ignoring case/spaces)")
          )
        )
      }
    })
    
    # Render add item form based on current tab
    output$add_item_form <- renderUI({
      tab <- current_tab()
      elements <- text_elements_list()
      
      # Prepare text element choices by type
      title_choices <- c()
      population_choices <- c()
      ich_choices <- c()
      footnote_choices <- c()
      acronym_choices <- c()
      
      for (elem in elements) {
        if (elem$type == "title") {
          title_choices[elem$label] <- elem$id
        } else if (elem$type == "population_set") {
          population_choices[elem$label] <- elem$id
        } else if (elem$type == "ich_category") {
          ich_choices[elem$label] <- elem$id
        } else if (elem$type == "footnote") {
          footnote_choices[elem$label] <- elem$id
        } else if (elem$type == "acronyms_set") {
          acronym_choices[elem$label] <- elem$id
        }
      }
      
      if (tab == "tlf") {
        # TLF form
        card(
          class = "border border-2",
          card_body(
            # Item type and code
            div(
              class = "mb-2",
              tags$label("TLF Type", class = "form-label fw-bold"),
              selectInput(
                ns("new_tlf_type"),
                label = NULL,
                choices = c("Table", "Listing", "Figure"),
                selected = "Table"
              )
            ),
            div(
              class = "mb-2",
              tags$label("Title Key", class = "form-label fw-bold"),
              textInput(
                ns("new_tlf_code"),
                label = NULL,
                placeholder = "e.g., t14.1.1"
              )
            ),
            
            # Title with selectize
            div(
              class = "mb-2",
              tags$label("Title", class = "form-label fw-bold"),
              selectizeInput(
                ns("new_tlf_title"),
                label = NULL,
                choices = title_choices,
                options = list(
                  create = TRUE,
                  placeholder = "Select or create new title...",
                  maxItems = 1
                )
              )
            ),
            
            # Population with selectize
            div(
              class = "mb-2",
              tags$label("Population Flag", class = "form-label"),
              selectizeInput(
                ns("new_tlf_population"),
                label = NULL,
                choices = population_choices,
                options = list(
                  create = TRUE,
                  placeholder = "Select or create new population...",
                  maxItems = 1
                )
              )
            ),
            
            # ICH Category with selectize
            div(
              class = "mb-2",
              tags$label("ICH Category", class = "form-label"),
              selectizeInput(
                ns("new_tlf_ich"),
                label = NULL,
                choices = ich_choices,
                options = list(
                  create = TRUE,
                  placeholder = "Select or create new ICH category...",
                  maxItems = 1
                )
              )
            ),
            
            # Footnotes with selectize
            div(
              class = "mb-2",
              tags$label("Footnotes", class = "form-label"),
              selectizeInput(
                ns("new_tlf_footnotes"),
                label = NULL,
                choices = footnote_choices,
                multiple = TRUE,
                options = list(
                  create = TRUE,
                  placeholder = "Select or create footnotes..."
                )
              )
            ),
            
            # Acronyms with selectize
            div(
              class = "mb-2",
              tags$label("Acronyms", class = "form-label"),
              selectizeInput(
                ns("new_tlf_acronyms"),
                label = NULL,
                choices = acronym_choices,
                multiple = TRUE,
                options = list(
                  create = TRUE,
                  placeholder = "Select or create acronyms..."
                )
              )
            ),
            
            # Action buttons
            layout_columns(
              col_widths = c(6, 6),
              gap = 2,
              actionButton(
                ns("save_new_tlf"),
                "Create",
                icon = icon("check"),
                class = "btn btn-success w-100",
                style = "height: auto; padding: 0.375rem 0.75rem;",
                title = "Create the item"
              ),
              actionButton(
                ns("cancel_new_tlf"),
                "Cancel",
                icon = icon("times"),
                class = "btn btn-secondary w-100",
                style = "height: auto; padding: 0.375rem 0.75rem;",
                title = "Cancel and close"
              )
            )
          )
        )
      } else {
        # Dataset form
        card(
          class = "border border-2",
          card_body(
            # Item type and code
            div(
              class = "mb-2",
              tags$label("Dataset Type", class = "form-label fw-bold"),
              selectInput(
                ns("new_dataset_type"),
                label = NULL,
                choices = c("SDTM", "ADaM"),
                selected = "SDTM"
              )
            ),
            div(
              class = "mb-2",
              tags$label("Dataset Name", class = "form-label fw-bold"),
              textInput(
                ns("new_dataset_code"),
                label = NULL,
                placeholder = "e.g., DM, AE, ADSL"
              )
            ),
            div(
              class = "mb-2",
              tags$label("Dataset Label", class = "form-label"),
              textInput(
                ns("new_dataset_label"),
                label = NULL,
                placeholder = "e.g., Demographics"
              )
            ),
            div(
              class = "mb-2",
              tags$label("Run Order", class = "form-label"),
              numericInput(
                ns("new_dataset_order"),
                label = NULL,
                value = 1,
                min = 1
              )
            ),
            
            # Action buttons
            layout_columns(
              col_widths = c(6, 6),
              gap = 2,
              actionButton(
                ns("save_new_dataset"),
                "Create",
                icon = icon("check"),
                class = "btn btn-success w-100",
                style = "height: auto; padding: 0.375rem 0.75rem;",
                title = "Create the item"
              ),
              actionButton(
                ns("cancel_new_dataset"),
                "Cancel",
                icon = icon("times"),
                class = "btn btn-secondary w-100",
                style = "height: auto; padding: 0.375rem 0.75rem;",
                title = "Cancel and close"
              )
            )
          )
        )
      }
    })
    
    # Save edit TLF item
    observeEvent(input$save_edit_tlf, {
      item_id <- editing_item_id()
      pkg_id <- input$selected_package
      if (!is.null(item_id) && !is.null(pkg_id)) {
        # Check for duplicates (excluding current item)
        duplicate_error <- check_tlf_duplicate(as.integer(pkg_id), input$edit_tlf_type, input$edit_tlf_code, input$edit_tlf_title, exclude_id = item_id)
        
        if (!is.null(duplicate_error)) {
          showNotification(
            paste("Duplicate TLF item:", duplicate_error),
            type = "error",
            duration = 6
          )
          return()
        }
        
        # Process text elements (create new ones if needed)
        title_id <- process_text_element(input$edit_tlf_title, "title")
        population_id <- process_text_element(input$edit_tlf_population, "population_set")
        ich_id <- process_text_element(input$edit_tlf_ich, "ich_category")
        
        footnote_ids <- list()
        if (!is.null(input$edit_tlf_footnotes)) {
          for (fn in input$edit_tlf_footnotes) {
            fn_id <- process_text_element(fn, "footnote")
            if (!is.null(fn_id)) {
              footnote_ids <- append(footnote_ids, fn_id)
            }
          }
        }
        
        acronym_ids <- list()
        if (!is.null(input$edit_tlf_acronyms)) {
          for (ac in input$edit_tlf_acronyms) {
            ac_id <- process_text_element(ac, "acronyms_set")
            if (!is.null(ac_id)) {
              acronym_ids <- append(acronym_ids, ac_id)
            }
          }
        }
        
        # Update the TLF item
        result <- update_package_item(
          item_id = item_id,
          item_type = "TLF",
          item_subtype = input$edit_tlf_type,
          item_code = input$edit_tlf_code,
          tlf_details = list(
            title_id = title_id,
            population_flag_id = population_id,
            ich_category_id = ich_id
          ),
          footnotes = lapply(seq_along(footnote_ids), function(i) {
            list(footnote_id = footnote_ids[[i]], sequence_number = i)
          }),
          acronyms = lapply(acronym_ids, function(id) {
            list(acronym_id = id)
          })
        )
        
        if ("error" %in% names(result)) {
          showNotification(
            paste("Failed to update TLF item:", result$error),
            type = "error",
            duration = 5
          )
        } else {
          showNotification(
            "TLF item updated successfully",
            type = "message",
            duration = 3
          )
          
          # Clear editing state
          is_editing(FALSE)
          editing_item_id(NULL)
          
          removeModal()
          load_package_items()
        }
      }
    })
    
    # Save edit Dataset item
    observeEvent(input$save_edit_dataset, {
      item_id <- editing_item_id()
      pkg_id <- input$selected_package
      if (!is.null(item_id) && !is.null(pkg_id)) {
        # Check for duplicates (excluding current item)
        duplicate_error <- check_dataset_duplicate(as.integer(pkg_id), input$edit_dataset_type, input$edit_dataset_code, exclude_id = item_id)
        
        if (!is.null(duplicate_error)) {
          showNotification(
            paste("Duplicate Dataset item:", duplicate_error),
            type = "error",
            duration = 6
          )
          return()
        }
        
        # Update the Dataset item
        result <- update_package_item(
          item_id = item_id,
          item_type = "Dataset",
          item_subtype = input$edit_dataset_type,
          item_code = input$edit_dataset_code,
          dataset_details = list(
            label = input$edit_dataset_label,
            sorting_order = input$edit_dataset_order
          )
        )
        
        if ("error" %in% names(result)) {
          showNotification(
            paste("Failed to update dataset item:", result$error),
            type = "error",
            duration = 5
          )
        } else {
          showNotification(
            "Dataset item updated successfully",
            type = "message",
            duration = 3
          )
          
          # Clear editing state
          is_editing(FALSE)
          editing_item_id(NULL)
          
          removeModal()
          load_package_items()
        }
      }
    })
    
    # Save new TLF item
    observeEvent(input$save_new_tlf, {
      pkg_id <- input$selected_package
      if (!is.null(pkg_id) && pkg_id != "") {
        # Check for duplicates
        duplicate_error <- check_tlf_duplicate(as.integer(pkg_id), input$new_tlf_type, input$new_tlf_code, input$new_tlf_title)
        
        if (!is.null(duplicate_error)) {
          showNotification(
            paste("Duplicate TLF item:", duplicate_error),
            type = "error",
            duration = 6
          )
          return()
        }
        
        # Process text elements (create new ones if needed)
        title_id <- process_text_element(input$new_tlf_title, "title")
        population_id <- process_text_element(input$new_tlf_population, "population_set")
        ich_id <- process_text_element(input$new_tlf_ich, "ich_category")
        
        footnote_ids <- list()
        if (!is.null(input$new_tlf_footnotes)) {
          for (fn in input$new_tlf_footnotes) {
            fn_id <- process_text_element(fn, "footnote")
            if (!is.null(fn_id)) {
              footnote_ids <- append(footnote_ids, fn_id)
            }
          }
        }
        
        acronym_ids <- list()
        if (!is.null(input$new_tlf_acronyms)) {
          for (ac in input$new_tlf_acronyms) {
            ac_id <- process_text_element(ac, "acronyms_set")
            if (!is.null(ac_id)) {
              acronym_ids <- append(acronym_ids, ac_id)
            }
          }
        }
        
        # Create the TLF item
        result <- create_package_item(
          package_id = pkg_id,
          item_type = "TLF",
          item_subtype = input$new_tlf_type,
          item_code = input$new_tlf_code,
          tlf_details = list(
            title_id = title_id,
            population_flag_id = population_id,
            ich_category_id = ich_id
          ),
          footnotes = lapply(seq_along(footnote_ids), function(i) {
            list(footnote_id = footnote_ids[[i]], sequence_number = i)
          }),
          acronyms = lapply(acronym_ids, function(id) {
            list(acronym_id = id)
          })
        )
        
        if ("error" %in% names(result)) {
          showNotification(
            paste("Failed to create TLF item:", result$error),
            type = "error",
            duration = 5000
          )
        } else {
          showNotification(
            "TLF item created successfully",
            type = "message",
            duration = 3000
          )
          sidebar_toggle(id = "items_sidebar", open = FALSE)
          load_package_items()
          
          # Clear upload results after successful creation
          output$upload_results <- renderUI({
            NULL
          })
          
          # Clear form
          updateSelectizeInput(session, "new_tlf_title", selected = "")
          updateSelectizeInput(session, "new_tlf_population", selected = "")
          updateSelectizeInput(session, "new_tlf_ich", selected = "")
          updateSelectizeInput(session, "new_tlf_footnotes", selected = "")
          updateSelectizeInput(session, "new_tlf_acronyms", selected = "")
          updateTextInput(session, "new_tlf_code", value = "")
        }
      }
    })
    
    # Save new Dataset item
    observeEvent(input$save_new_dataset, {
      pkg_id <- input$selected_package
      if (!is.null(pkg_id) && pkg_id != "") {
        # Check for duplicates
        duplicate_error <- check_dataset_duplicate(as.integer(pkg_id), input$new_dataset_type, input$new_dataset_code)
        
        if (!is.null(duplicate_error)) {
          showNotification(
            paste("Duplicate Dataset item:", duplicate_error),
            type = "error",
            duration = 6
          )
          return()
        }
        
        result <- create_package_item(
          package_id = pkg_id,
          item_type = "Dataset",
          item_subtype = input$new_dataset_type,
          item_code = input$new_dataset_code,
          dataset_details = list(
            label = input$new_dataset_label,
            sorting_order = input$new_dataset_order
          )
        )
        
        if ("error" %in% names(result)) {
          showNotification(
            paste("Failed to create dataset item:", result$error),
            type = "error",
            duration = 5000
          )
        } else {
          showNotification(
            "Dataset item created successfully",
            type = "message",
            duration = 3000
          )
          sidebar_toggle(id = "items_sidebar", open = FALSE)
          load_package_items()
          
          # Clear upload results after successful creation
          output$upload_results <- renderUI({
            NULL
          })
          
          # Clear form
          updateTextInput(session, "new_dataset_code", value = "")
          updateTextInput(session, "new_dataset_label", value = "")
          updateNumericInput(session, "new_dataset_order", value = 1)
        }
      }
    })
    
    # Helper function to populate selectize inputs for editing
    populate_edit_selectize_inputs <- function(tlf_item) {
      elements <- text_elements_list()
      
      # Prepare text element choices by type
      title_choices <- c()
      population_choices <- c()
      ich_choices <- c()
      footnote_choices <- c()
      acronym_choices <- c()
      
      for (elem in elements) {
        if (elem$type == "title") {
          title_choices[elem$label] <- elem$id
        } else if (elem$type == "population_set") {
          population_choices[elem$label] <- elem$id
        } else if (elem$type == "ich_category") {
          ich_choices[elem$label] <- elem$id
        } else if (elem$type == "footnote") {
          footnote_choices[elem$label] <- elem$id
        } else if (elem$type == "acronyms_set") {
          acronym_choices[elem$label] <- elem$id
        }
      }
      
      # Update choices
      updateSelectizeInput(session, "edit_tlf_title", choices = title_choices, server = FALSE)
      updateSelectizeInput(session, "edit_tlf_population", choices = population_choices, server = FALSE)
      updateSelectizeInput(session, "edit_tlf_ich", choices = ich_choices, server = FALSE)
      updateSelectizeInput(session, "edit_tlf_footnotes", choices = footnote_choices, server = FALSE)
      updateSelectizeInput(session, "edit_tlf_acronyms", choices = acronym_choices, server = FALSE)
      
      # Set selected values
      if (!is.null(tlf_item$tlf_details)) {
        if (!is.null(tlf_item$tlf_details$title_id)) {
          updateSelectizeInput(session, "edit_tlf_title", selected = as.character(tlf_item$tlf_details$title_id))
        }
        if (!is.null(tlf_item$tlf_details$population_flag_id)) {
          updateSelectizeInput(session, "edit_tlf_population", selected = as.character(tlf_item$tlf_details$population_flag_id))
        }
        if (!is.null(tlf_item$tlf_details$ich_category_id)) {
          updateSelectizeInput(session, "edit_tlf_ich", selected = as.character(tlf_item$tlf_details$ich_category_id))
        }
      }
      
      # Set footnotes and acronyms if available
      if (!is.null(tlf_item$footnotes) && length(tlf_item$footnotes) > 0) {
        footnote_ids <- sapply(tlf_item$footnotes, function(f) as.character(f$footnote_id))
        updateSelectizeInput(session, "edit_tlf_footnotes", selected = footnote_ids)
      }
      
      if (!is.null(tlf_item$acronyms) && length(tlf_item$acronyms) > 0) {
        acronym_ids <- sapply(tlf_item$acronyms, function(f) as.character(f$acronym_id))
        updateSelectizeInput(session, "edit_tlf_acronyms", selected = acronym_ids)
      }
    }
    
    # Helper function to process text elements with logging
    process_text_element_with_log <- function(value, type, results_ref) {
      if (is.null(value) || is.na(value) || value == "") {
        return(NULL)
      }
      
      # Ensure value is character and trimmed
      value <- trimws(as.character(value))
      if (value == "") {
        return(NULL)
      }
      
      # Check if it's an existing ID (numeric)
      if (grepl("^[0-9]+$", value)) {
        return(as.integer(value))
      }
      
      # Check if this text element already exists
      elements <- text_elements_list()
      for (elem in elements) {
        if (elem$type == type && elem$label == value) {
          # Log reuse
          reuse_key <- paste(type, value, sep = "::")
          if (!reuse_key %in% results_ref$text_elements_reused) {
            results_ref$text_elements_reused <- append(results_ref$text_elements_reused, reuse_key)
          }
          return(elem$id)
        }
      }
      
      # It's a new text element, create it
      result <- create_text_element(list(type = type, label = value))
      if (!"error" %in% names(result)) {
        # Reload text elements to get the new one
        load_text_elements()
        # Log creation
        create_key <- paste(type, value, sep = "::")
        if (!create_key %in% results_ref$text_elements_created) {
          results_ref$text_elements_created <- append(results_ref$text_elements_created, create_key)
        }
        return(result$id)
      }
      return(NULL)
    }
    
    # Original function for non-bulk operations
    process_text_element <- function(value, type) {
      if (is.null(value) || is.na(value) || value == "") {
        return(NULL)
      }
      
      # Ensure value is character and trimmed
      value <- trimws(as.character(value))
      if (value == "") {
        return(NULL)
      }
      
      # Check if it's an existing ID (numeric)
      if (grepl("^[0-9]+$", value)) {
        return(as.integer(value))
      }
      
      # Check if this text element already exists
      elements <- text_elements_list()
      for (elem in elements) {
        if (elem$type == type && elem$label == value) {
          return(elem$id)
        }
      }
      
      # It's a new text element, create it
      result <- create_text_element(list(type = type, label = value))
      if (!"error" %in% names(result)) {
        # Reload text elements to get the new one
        load_text_elements()
        return(result$id)
      }
      return(NULL)
    }
    
    # Cancel buttons
    observeEvent(input$cancel_new_tlf, {
      sidebar_toggle(id = "items_sidebar", open = FALSE)
      
      # Clear upload results when closing sidebar
      output$upload_results <- renderUI({
        NULL
      })
    })
    
    observeEvent(input$cancel_new_dataset, {
      sidebar_toggle(id = "items_sidebar", open = FALSE)
      
      # Clear upload results when closing sidebar
      output$upload_results <- renderUI({
        NULL
      })
    })
    
    # Refresh button
    observeEvent(input$refresh_btn, {
      cat("Refresh button clicked\n")
      load_packages()
      load_text_elements()
      load_package_items()
      showNotification("Refreshing items data...", type = "message", duration = 2)
    })
    
    # Bulk Upload Handler
    observeEvent(input$process_bulk_upload, {
      # Check if a package is selected
      if (is.null(input$selected_package) || input$selected_package == "") {
        showNotification(
          "Please select a package first",
          type = "warning",
          duration = 3
        )
        return()
      }
      
      # Check if a file has been selected
      if (is.null(input$bulk_upload_file)) {
        showNotification(
          "Please select an Excel file to upload",
          type = "warning",
          duration = 3
        )
        return()
      }
      
      # Clear previous results and show processing message
      output$upload_results <- renderUI({
        div(
          class = "mt-3",
          div(
            class = "alert alert-info small",
            icon("spinner", class = "fa-spin"),
            " Processing your upload..."
          )
        )
      })
      
      cat("Starting bulk upload processing...\n")
      
      # Check if readxl is available
      if (!requireNamespace("readxl", quietly = TRUE)) {
        showNotification(
          "Excel support not installed. Please install the 'readxl' package.",
          type = "error",
          duration = 5
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
          duration = 4
        )
        output$upload_results <- renderUI({
          div(class = "alert alert-danger small", "Invalid file type. Please use .xlsx or .xls files.")
        })
        return()
      }
      
      # Read the uploaded file
      file_path <- input$bulk_upload_file$datapath
      pkg_id <- input$selected_package
      
      tryCatch({
        # Get current active tab to determine expected format
        current_active_tab <- current_tab()
        
        # Read Excel file
        df <- readxl::read_excel(file_path)
        
        # Check if file has data
        if (nrow(df) == 0) {
          showNotification(
            "Excel file is empty - no data rows found",
            type = "error",
            duration = 5
          )
          output$upload_results <- renderUI({
            div(class = "alert alert-danger small", 
                "Excel file contains no data rows. Please check your file.")
          })
          return()
        }
        
        # Process results with detailed logging
        results <- list(
          success = 0,
          errors = 0,
          skipped = 0,
          details = list(),
          log_entries = list(),
          text_elements_created = list(),
          text_elements_reused = list()
        )
        
        # Add header to log
        results$log_entries <- append(results$log_entries, 
          list(paste("=== BULK UPLOAD LOG ===", Sys.time(), "===")))
        results$log_entries <- append(results$log_entries, 
          list(paste("File:", input$bulk_upload_file$name)))
        results$log_entries <- append(results$log_entries, 
          list(paste("Package:", pkg_id)))
        results$log_entries <- append(results$log_entries, 
          list(paste("Item Type:", toupper(current_active_tab))))
        results$log_entries <- append(results$log_entries, 
          list(paste("Total Rows:", nrow(df))))
        results$log_entries <- append(results$log_entries, list(""))
        results$log_entries <- append(results$log_entries, list("=== PROCESSING DETAILS ==="))
        
        # Check for required columns based on active tab (case-insensitive)
        col_names_lower <- tolower(names(df))
        
        if (current_active_tab == "tlf") {
          # TLF tab - expect TLF-specific columns
          title_key_col <- which(col_names_lower == "title key")[1]
          
          if (is.na(title_key_col)) {
            showNotification(
              "Excel file must contain 'Title Key' column for TLF items",
              type = "error",
              duration = 5
            )
            output$upload_results <- renderUI({
              div(class = "alert alert-danger small", 
                  "Missing required column. TLF file must have 'Title Key' column.")
            })
            return()
          }
        } else {
          # Dataset tab - expect Dataset-specific columns
          dataset_name_col <- which(col_names_lower == "dataset name")[1]
          run_order_col <- which(col_names_lower == "run order")[1]
          
          if (is.na(dataset_name_col) || is.na(run_order_col)) {
            showNotification(
              "Excel file must contain 'Dataset Name' and 'Run Order' columns for Dataset items",
              type = "error",
              duration = 5
            )
            output$upload_results <- renderUI({
              div(class = "alert alert-danger small", 
                  "Missing required columns. Dataset file must have 'Dataset Name' and 'Run Order' columns.")
            })
            return()
          }
        }
        
        # Process each row based on active tab
        for (i in 1:nrow(df)) {
          if (current_active_tab == "tlf") {
            # Process TLF items
            title_key <- trimws(as.character(df[[title_key_col]][i]))
            
            # Skip empty rows
            if (is.na(title_key) || title_key == "") {
              results$skipped <- results$skipped + 1
              results$log_entries <- append(results$log_entries, 
                list(paste("Row", i, ": SKIPPED - Empty Title Key")))
              next
            }
            
            # Get optional TLF columns
            tlf_type_col <- which(col_names_lower == "tlf type")[1]
            title_col <- which(col_names_lower == "title")[1]
            population_col <- which(col_names_lower == "population")[1]
            ich_category_col <- which(col_names_lower == "ich category")[1]
            run_order_col <- which(col_names_lower == "run order")[1]
            
            tlf_type <- if (!is.na(tlf_type_col)) {
              val <- df[[tlf_type_col]][i]
              if (is.na(val)) "Table" else trimws(as.character(val))
            } else "Table"
            
            # Log row processing start
            results$log_entries <- append(results$log_entries, 
              list(paste("Row", i, ": Processing TLF -", tlf_type, title_key)))
            
            title_text <- if (!is.na(title_col)) {
              val <- df[[title_col]][i]
              if (is.na(val)) "" else trimws(as.character(val))
            } else ""
            
            population_text <- if (!is.na(population_col)) {
              val <- df[[population_col]][i]
              if (is.na(val)) "" else trimws(as.character(val))
            } else ""
            
            ich_category_text <- if (!is.na(ich_category_col)) {
              val <- df[[ich_category_col]][i]
              if (is.na(val)) "" else trimws(as.character(val))
            } else ""
            
            # Check for duplicates
            duplicate_error <- check_tlf_duplicate(as.integer(pkg_id), tlf_type, title_key, title_text)
            
            if (!is.null(duplicate_error)) {
              results$errors <- results$errors + 1
              results$details <- append(results$details,
                list(paste("Row", i, ": Duplicate TLF -", duplicate_error)))
              results$log_entries <- append(results$log_entries,
                list(paste("  REJECTED - Duplicate:", duplicate_error)))
            } else {
              # Process text elements with logging
              title_id <- process_text_element_with_log(title_text, "title", results)
              population_id <- process_text_element_with_log(population_text, "population_set", results) 
              ich_id <- process_text_element_with_log(ich_category_text, "ich_category", results)
              
              # Log text element processing
              if (!is.na(title_text) && title_text != "") {
                results$log_entries <- append(results$log_entries,
                  list(paste("  Title:", title_text, "-> ID:", title_id)))
              }
              if (!is.na(population_text) && population_text != "") {
                results$log_entries <- append(results$log_entries,
                  list(paste("  Population:", population_text, "-> ID:", population_id)))
              }
              if (!is.na(ich_category_text) && ich_category_text != "") {
                results$log_entries <- append(results$log_entries,
                  list(paste("  ICH Category:", ich_category_text, "-> ID:", ich_id)))
              }
              
              # Build TLF details only with non-NULL values
              tlf_details_data <- list()
              if (!is.null(title_id)) tlf_details_data$title_id <- title_id
              if (!is.null(population_id)) tlf_details_data$population_flag_id <- population_id
              if (!is.null(ich_id)) tlf_details_data$ich_category_id <- ich_id
              
              
              # Create TLF item
              result <- create_package_item(
                package_id = as.integer(pkg_id),
                item_type = "TLF",
                item_subtype = tlf_type,
                item_code = title_key,
                tlf_details = if(length(tlf_details_data) > 0) tlf_details_data else NULL,
                footnotes = list(),
                acronyms = list()
              )
              
              if ("error" %in% names(result)) {
                results$errors <- results$errors + 1
                results$details <- append(results$details,
                  list(paste("Row", i, ": Failed to create TLF -", title_key)))
                results$log_entries <- append(results$log_entries,
                  list(paste("  FAILED - API Error:", result$error)))
              } else {
                results$success <- results$success + 1
                results$log_entries <- append(results$log_entries,
                  list(paste("  SUCCESS - Created TLF with ID:", result$id)))
              }
            }
            
          } else {
            # Process Dataset items
            dataset_name <- trimws(as.character(df[[dataset_name_col]][i]))
            run_order <- as.numeric(df[[run_order_col]][i])
            
            # Skip empty rows
            if (is.na(dataset_name) || dataset_name == "" || is.na(run_order)) {
              results$skipped <- results$skipped + 1
              results$log_entries <- append(results$log_entries, 
                list(paste("Row", i, ": SKIPPED - Empty Dataset Name or Run Order")))
              next
            }
            
            # Get optional Dataset columns
            dataset_type_col <- which(col_names_lower == "dataset type")[1]
            label_col <- which(col_names_lower %in% c("label", "dataset label"))[1]
            
            dataset_type <- if (!is.na(dataset_type_col)) {
              val <- df[[dataset_type_col]][i]
              if (is.na(val)) "SDTM" else trimws(as.character(val))
            } else "SDTM"
            
            # Log row processing start
            results$log_entries <- append(results$log_entries, 
              list(paste("Row", i, ": Processing Dataset -", dataset_type, dataset_name, "Order:", run_order)))
            
            label_text <- if (!is.na(label_col)) {
              val <- df[[label_col]][i]
              if (is.na(val)) "" else trimws(as.character(val))
            } else ""
            
            # Log dataset details
            if (!is.na(label_text) && label_text != "") {
              results$log_entries <- append(results$log_entries,
                list(paste("  Label:", label_text)))
            }
            
            # Check for duplicates
            duplicate_error <- check_dataset_duplicate(as.integer(pkg_id), dataset_type, dataset_name)
            
            if (!is.null(duplicate_error)) {
              results$errors <- results$errors + 1
              results$details <- append(results$details,
                list(paste("Row", i, ": Duplicate Dataset -", duplicate_error)))
              results$log_entries <- append(results$log_entries,
                list(paste("  REJECTED - Duplicate:", duplicate_error)))
            } else {
              # Create Dataset item
              result <- create_package_item(
                package_id = as.integer(pkg_id),
                item_type = "Dataset",
                item_subtype = dataset_type,
                item_code = dataset_name,
                dataset_details = list(
                  label = label_text,
                  sorting_order = run_order
                )
              )
              
              if ("error" %in% names(result)) {
                results$errors <- results$errors + 1
                results$details <- append(results$details,
                  list(paste("Row", i, ": Failed to create Dataset -", dataset_name)))
                results$log_entries <- append(results$log_entries,
                  list(paste("  FAILED - API Error:", result$error)))
              } else {
                results$success <- results$success + 1
                results$log_entries <- append(results$log_entries,
                  list(paste("  SUCCESS - Created Dataset with ID:", result$id)))
              }
            }
          }
        }
        
        # Add summary to log
        results$log_entries <- append(results$log_entries, list(""))
        results$log_entries <- append(results$log_entries, list("=== SUMMARY ==="))
        results$log_entries <- append(results$log_entries, 
          list(paste("Total Processed:", results$success + results$errors + results$skipped)))
        results$log_entries <- append(results$log_entries, 
          list(paste("Successfully Created:", results$success)))
        results$log_entries <- append(results$log_entries, 
          list(paste("Errors/Rejected:", results$errors)))
        results$log_entries <- append(results$log_entries, 
          list(paste("Skipped (Empty):", results$skipped)))
        
        if (length(results$text_elements_created) > 0) {
          results$log_entries <- append(results$log_entries, list(""))
          results$log_entries <- append(results$log_entries, list("=== NEW TEXT ELEMENTS CREATED ==="))
          for (elem in results$text_elements_created) {
            parts <- strsplit(elem, "::")[[1]]
            results$log_entries <- append(results$log_entries, 
              list(paste("-", parts[1], ":", parts[2])))
          }
        }
        
        if (length(results$text_elements_reused) > 0) {
          results$log_entries <- append(results$log_entries, list(""))
          results$log_entries <- append(results$log_entries, list("=== EXISTING TEXT ELEMENTS REUSED ==="))
          for (elem in results$text_elements_reused) {
            parts <- strsplit(elem, "::")[[1]]
            results$log_entries <- append(results$log_entries, 
              list(paste("-", parts[1], ":", parts[2])))
          }
        }
        
        # Create log file
        log_content <- paste(results$log_entries, collapse = "\n")
        log_filename <- paste0("upload_log_", format(Sys.time(), "%Y%m%d_%H%M%S"), ".txt")
        log_filepath <- file.path("www", log_filename)
        
        # Ensure www directory exists
        if (!dir.exists("www")) {
          dir.create("www", recursive = TRUE)
        }
        
        writeLines(log_content, log_filepath)
        cat("Log file created at:", log_filepath, "\n")
        cat("Log file exists:", file.exists(log_filepath), "\n")
        
        # Display results
        cat("Displaying upload results - Success:", results$success, "Errors:", results$errors, "\n")
        if (results$success > 0) {
          output$upload_results <- renderUI({
            div(
              class = "mt-3",  # Add margin wrapper
              div(
                id = ns("upload_results_container"),
                class = "alert alert-success small",
                style = "border: 2px solid #28a745;",
                tags$strong(icon("check-circle"), " Upload Complete"),
              tags$ul(
                class = "mb-0 mt-2",
                tags$li(paste("Successfully created:", results$success, "items")),
                if (results$errors > 0) tags$li(paste("Errors/Rejected:", results$errors)),
                if (results$skipped > 0) tags$li(paste("Skipped (empty rows):", results$skipped)),
                if (length(results$text_elements_created) > 0) tags$li(paste("New text elements created:", length(results$text_elements_created))),
                if (length(results$text_elements_reused) > 0) tags$li(paste("Existing text elements reused:", length(results$text_elements_reused)))
              ),
              div(
                class = "mt-3 d-flex gap-2",
                tags$a(
                  href = log_filename,
                  download = log_filename,
                  target = "_blank",
                  class = "btn btn-primary btn-sm",
                  style = "animation: pulse 2s infinite;",
                  title = paste("Download log file:", log_filename),
                  tagList(icon("file-text"), " Download Detailed Log")
                ),
                if (length(results$details) > 0) {
                  tags$button(
                    class = "btn btn-outline-warning btn-sm",
                    onclick = paste0("document.getElementById('", ns("error_details"), "').style.display = document.getElementById('", ns("error_details"), "').style.display === 'none' ? 'block' : 'none'"),
                    tagList(icon("exclamation-triangle"), " Show/Hide Issues")
                  )
                }
              ),
              if (length(results$details) > 0) {
                div(
                  id = ns("error_details"),
                  style = "display: none;",
                  class = "mt-2",
                  tags$strong("Issues Details:"),
                  tags$ul(
                    class = "small mt-1",
                    lapply(results$details[1:min(15, length(results$details))], tags$li)
                  ),
                  if (length(results$details) > 15) {
                    tags$p(class = "small text-muted", paste("... and", length(results$details) - 15, "more issues. See detailed log for complete list."))
                  }
                )
              }
              )
            )
          })
          
          # Refresh data
          load_text_elements()  # Refresh text elements first
          load_package_items()  # Then refresh package items
          
          showNotification(
            HTML(paste0("Successfully imported ", results$success, " items<br>",
                       "<small>Download log file from the sidebar for details</small>")),
            type = "message",
            duration = 6
          )
          
          # Ensure sidebar stays open to show results
          sidebar_toggle(id = "items_sidebar", open = TRUE)
          
          # Scroll to the upload results after a brief delay
          shinyjs::delay(200, {
            shinyjs::runjs(sprintf("
              var elem = document.getElementById('%s');
              if (elem) {
                elem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
              }
            ", ns("upload_results_container")))
          })
        } else {
          output$upload_results <- renderUI({
            div(
              class = "mt-3",  # Add margin wrapper
              div(
                id = ns("upload_results_container"),
                class = "alert alert-warning small",
                style = "border: 2px solid #ffc107;",
                tags$strong(icon("exclamation-circle"), " No Items Imported"),
              tags$ul(
                class = "mb-0 mt-2",
                if (results$errors > 0) tags$li(paste("Errors/Rejected:", results$errors)),
                if (results$skipped > 0) tags$li(paste("Skipped (empty rows):", results$skipped))
              ),
              div(
                class = "mt-3 d-flex gap-2",
                tags$a(
                  href = log_filename,
                  download = log_filename,
                  target = "_blank",
                  class = "btn btn-primary btn-sm",
                  style = "animation: pulse 2s infinite;",
                  title = paste("Download log file:", log_filename),
                  tagList(icon("file-text"), " Download Detailed Log")
                ),
                if (length(results$details) > 0) {
                  tags$button(
                    class = "btn btn-outline-warning btn-sm",
                    onclick = paste0("document.getElementById('", ns("error_details_fail"), "').style.display = document.getElementById('", ns("error_details_fail"), "').style.display === 'none' ? 'block' : 'none'"),
                    tagList(icon("exclamation-triangle"), " Show/Hide Issues")
                  )
                }
              ),
              if (length(results$details) > 0) {
                div(
                  id = ns("error_details_fail"),
                  style = "display: none;",
                  class = "mt-2",
                  tags$strong("Issues Details:"),
                  tags$ul(
                    class = "small mt-1",
                    lapply(results$details[1:min(15, length(results$details))], tags$li)
                  ),
                  if (length(results$details) > 15) {
                    tags$p(class = "small text-muted", paste("... and", length(results$details) - 15, "more issues. See detailed log for complete list."))
                  }
                )
              } else {
                tags$p(class = "mt-2 mb-0", "No specific errors detected. Check file format and content. See detailed log for more information.")
              }
              )
            )
          })
          
          showNotification(
            HTML("No items were imported. Check the details for more information.<br><small>Download log file from the sidebar for details</small>"),
            type = "warning",
            duration = 6
          )
          
          # Ensure sidebar stays open to show results  
          sidebar_toggle(id = "items_sidebar", open = TRUE)
        }
        
        # Clean up the temp file
        if (file.exists(file_path)) {
          unlink(file_path)
        }
        
        # Don't reset the file input immediately as it might interfere with the UI
        # The user can upload a new file which will naturally replace the old one
        # shinyjs::delay(500, shinyjs::reset("bulk_upload_file"))
        
      }, error = function(e) {
        showNotification(
          paste("Error reading Excel file:", e$message),
          type = "error",
          duration = 5
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
    
    # WebSocket event handling
    observeEvent(input$`package-items-websocket_event`, {
      if (!is.null(input$`package-items-websocket_event`)) {
        event_data <- input$`package-items-websocket_event`
        if (startsWith(event_data$type, "package_item_")) {
          load_package_items()
        }
      }
    })
    
    # Update status message
    output$status_message <- renderText({
      tlf <- tlf_data()
      dataset <- dataset_data()
      pkg_id <- input$selected_package
      
      if (!is.null(pkg_id) && pkg_id != "") {
        paste("TLF items:", nrow(tlf), "| Dataset items:", nrow(dataset))
      } else {
        "Select a package to view items"
      }
    })
    
    # Update last updated display
    output$last_updated_display <- renderText({
      paste("Last updated:", format(last_update(), "%Y-%m-%d %H:%M:%S"))
    })
  })
}