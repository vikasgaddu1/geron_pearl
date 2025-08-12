# Package Items Server Module - Manage TLF and Dataset items

package_items_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Helper function for null coalescing
    `%||%` <- function(x, y) {
      if (is.null(x) || length(x) == 0) y else x
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
    
    # Load packages for dropdown
    load_packages <- function() {
      result <- get_packages()
      if (!"error" %in% names(result)) {
        packages_list(result)
        
        # Update package selector
        choices <- setNames(
          sapply(result, function(x) x$id),
          sapply(result, function(x) x$package_name)
        )
        updateSelectizeInput(session, "selected_package", 
                            choices = choices,
                            server = FALSE)
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
          Code = sapply(items, function(x) x$item_code %||% ""),
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
          Code = sapply(items, function(x) x$item_code %||% ""),
          Label = sapply(items, function(x) {
            if (!is.null(x$dataset_details) && !is.null(x$dataset_details$label)) {
              x$dataset_details$label
            } else {
              ""
            }
          }),
          `Sort Order` = sapply(items, function(x) {
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
        return(df)
      } else {
        return(data.frame(
          ID = character(0),
          Type = character(0),
          Code = character(0),
          Label = character(0),
          `Sort Order` = character(0),
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
    
    # Reload items when package changes
    observeEvent(input$selected_package, {
      load_package_items()
    })
    
    # Track current tab
    observeEvent(input$item_tabs, {
      current_tab(input$item_tabs)
    })
    
    # Render TLF table
    output$tlf_table <- DT::renderDataTable({
      data <- tlf_data()
      
      if (nrow(data) > 0) {
        data$Actions <- sapply(data$ID, function(item_id) {
          sprintf(
            '<button class="btn btn-primary btn-sm me-1" data-action="edit" data-id="%s" data-type="tlf">
               <i class="bi bi-pencil"></i>
             </button>
             <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" data-type="tlf">
               <i class="bi bi-trash"></i>
             </button>',
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
          search = list(regex = TRUE, caseInsensitive = TRUE)
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
            '<button class="btn btn-primary btn-sm me-1" data-action="edit" data-id="%s" data-type="dataset">
               <i class="bi bi-pencil"></i>
             </button>
             <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" data-type="dataset">
               <i class="bi bi-trash"></i>
             </button>',
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
          search = list(regex = TRUE, caseInsensitive = TRUE)
        ),
        rownames = FALSE
      )
    })
    
    # Handle table clicks for TLF
    observeEvent(input$tlf_table_click_action, {
      info <- input$tlf_table_click_action
      if (!is.null(info)) {
        if (info$action == "edit") {
          show_edit_modal(info$id, "tlf")
        } else if (info$action == "delete") {
          show_delete_modal(info$id, "tlf")
        }
      }
    })
    
    # Handle table clicks for Dataset
    observeEvent(input$dataset_table_click_action, {
      info <- input$dataset_table_click_action
      if (!is.null(info)) {
        if (info$action == "edit") {
          show_edit_modal(info$id, "dataset")
        } else if (info$action == "delete") {
          show_delete_modal(info$id, "dataset")
        }
      }
    })
    
    # Toggle add form sidebar
    observeEvent(input$toggle_add_form, {
      if (is.null(input$selected_package) || input$selected_package == "") {
        showNotification(
          "Please select a package first",
          type = "warning",
          duration = 3000
        )
      } else {
        sidebar_toggle(ns("add_item_sidebar"))
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
              class = "mb-3",
              tags$label("TLF Type", class = "form-label fw-bold"),
              selectInput(
                ns("new_tlf_type"),
                label = NULL,
                choices = c("Table", "Listing", "Figure"),
                selected = "Table"
              )
            ),
            div(
              class = "mb-3",
              tags$label("TLF Code", class = "form-label fw-bold"),
              textInput(
                ns("new_tlf_code"),
                label = NULL,
                placeholder = "e.g., t14.1.1"
              )
            ),
            
            # Title with selectize
            div(
              class = "mb-3",
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
              class = "mb-3",
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
              class = "mb-3",
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
              class = "mb-3",
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
              class = "mb-3",
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
              input_task_button(
                ns("save_new_tlf"),
                tagList(bs_icon("check"), "Create"),
                class = "btn btn-success w-100",
                style = "height: auto; padding: 0.375rem 0.75rem;"
              ),
              input_task_button(
                ns("cancel_new_tlf"),
                tagList(bs_icon("x"), "Cancel"),
                class = "btn btn-secondary w-100",
                style = "height: auto; padding: 0.375rem 0.75rem;"
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
              class = "mb-3",
              tags$label("Dataset Type", class = "form-label fw-bold"),
              selectInput(
                ns("new_dataset_type"),
                label = NULL,
                choices = c("SDTM", "ADaM"),
                selected = "SDTM"
              )
            ),
            div(
              class = "mb-3",
              tags$label("Dataset Code", class = "form-label fw-bold"),
              textInput(
                ns("new_dataset_code"),
                label = NULL,
                placeholder = "e.g., DM, AE, ADSL"
              )
            ),
            div(
              class = "mb-3",
              tags$label("Dataset Label", class = "form-label"),
              textInput(
                ns("new_dataset_label"),
                label = NULL,
                placeholder = "e.g., Demographics"
              )
            ),
            div(
              class = "mb-3",
              tags$label("Sort Order", class = "form-label"),
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
              input_task_button(
                ns("save_new_dataset"),
                tagList(bs_icon("check"), "Create"),
                class = "btn btn-success w-100",
                style = "height: auto; padding: 0.375rem 0.75rem;"
              ),
              input_task_button(
                ns("cancel_new_dataset"),
                tagList(bs_icon("x"), "Cancel"),
                class = "btn btn-secondary w-100",
                style = "height: auto; padding: 0.375rem 0.75rem;"
              )
            )
          )
        )
      }
    })
    
    # Save new TLF item
    observeEvent(input$save_new_tlf, {
      pkg_id <- input$selected_package
      if (!is.null(pkg_id) && pkg_id != "") {
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
          sidebar_toggle(ns("add_item_sidebar"), open = FALSE)
          load_package_items()
          
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
          sidebar_toggle(ns("add_item_sidebar"), open = FALSE)
          load_package_items()
          
          # Clear form
          updateTextInput(session, "new_dataset_code", value = "")
          updateTextInput(session, "new_dataset_label", value = "")
          updateNumericInput(session, "new_dataset_order", value = 1)
        }
      }
    })
    
    # Helper function to process text elements
    process_text_element <- function(value, type) {
      if (is.null(value) || value == "") {
        return(NULL)
      }
      
      # Check if it's an existing ID (numeric)
      if (grepl("^[0-9]+$", value)) {
        return(as.integer(value))
      }
      
      # It's a new text element, create it
      result <- create_text_element(type = type, label = value)
      if (!"error" %in% names(result)) {
        # Reload text elements to get the new one
        load_text_elements()
        return(result$id)
      }
      return(NULL)
    }
    
    # Show edit modal (placeholder)
    show_edit_modal <- function(item_id, item_type) {
      showNotification(
        "Edit functionality will be implemented next",
        type = "message",
        duration = 3000
      )
    }
    
    # Show delete modal
    show_delete_modal <- function(item_id, item_type) {
      showModal(
        modalDialog(
          title = tagList(bs_icon("exclamation-triangle"), "Confirm Deletion"),
          size = "m",
          
          div(
            class = "alert alert-warning",
            tags$strong("Warning:"),
            tags$p(paste("Are you sure you want to delete this", item_type, "item?")),
            tags$p("This action cannot be undone.")
          ),
          
          footer = tagList(
            modalButton("Cancel"),
            actionButton(ns("confirm_delete_item"), "Delete", class = "btn-danger", 
                        `data-id` = item_id, `data-type` = item_type)
          )
        )
      )
    }
    
    # Confirm delete item
    observeEvent(input$confirm_delete_item, {
      item_id <- input$confirm_delete_item$`data-id` %||% input$confirm_delete_item
      
      if (!is.null(item_id)) {
        result <- delete_package_item(item_id)
        
        if ("error" %in% names(result)) {
          showNotification(
            paste("Failed to delete item:", result$error),
            type = "error",
            duration = 5000
          )
        } else {
          showNotification(
            "Item deleted successfully",
            type = "message",
            duration = 3000
          )
          removeModal()
          load_package_items()
        }
      }
    })
    
    # Cancel buttons
    observeEvent(input$cancel_new_tlf, {
      sidebar_toggle(ns("add_item_sidebar"), open = FALSE)
    })
    
    observeEvent(input$cancel_new_dataset, {
      sidebar_toggle(ns("add_item_sidebar"), open = FALSE)
    })
    
    # Refresh button
    observeEvent(input$refresh, {
      load_packages()
      load_text_elements()
      load_package_items()
      showNotification("Data refreshed", type = "message", duration = 2000)
    })
    
    # Bulk upload (placeholder)
    observeEvent(input$bulk_upload, {
      showNotification(
        "Bulk upload functionality will be implemented next",
        type = "message",
        duration = 3000
      )
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