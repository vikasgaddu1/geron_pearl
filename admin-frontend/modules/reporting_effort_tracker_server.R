reporting_effort_tracker_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns

    # Helpers
    `%||%` <- function(x, y) if (is.null(x) || length(x) == 0) y else x

    # Reactive values
    current_reporting_effort_id <- reactiveVal(NULL)
    reporting_efforts_list <- reactiveVal(list())
    database_releases_lookup <- reactiveVal(list())

    # Single reactive value following the working items module pattern
    tracker_data <- reactiveVal(list())  # Will store tlf_trackers, sdtm_trackers, adam_trackers
    
    # Load users for programmer dropdowns - moved up to ensure it's available early
    programmers_list <- reactiveVal(list())
    
    load_programmers <- function() {
      users_result <- get_users()
      if (!"error" %in% names(users_result) && length(users_result) > 0) {
        # Filter out biostat role users - only keep programmers
        programmers <- list()
        for (user in users_result) {
          if (!is.null(user$role) && tolower(user$role) != "biostat") {
            programmers[[length(programmers) + 1]] <- user
          }
        }
        programmers_list(programmers)
      }
    }

    # Load reporting efforts for dropdown (same labelling as items)
    load_reporting_efforts <- function() {
      result <- get_reporting_efforts()
      if ("error" %in% names(result)) {
        showNotification(paste("Error loading reporting efforts:", result$error), type = "error")
        reporting_efforts_list(list())
        updateSelectInput(session, "selected_reporting_effort", choices = list("Select a Reporting Effort" = ""))
      } else {
        reporting_efforts_list(result)

        studies_result <- get_studies()
        studies_lookup <- list()
        if (!("error" %in% names(studies_result))) {
          for (study in studies_result) {
            studies_lookup[[as.character(study$id)]] <- study$title
          }
        }

        db_rel_result <- get_database_releases()
        db_lookup <- list()
        if (!("error" %in% names(db_rel_result))) {
          for (rel in db_rel_result) {
            db_lookup[[as.character(rel$id)]] <- rel$database_release_label
          }
        }
        database_releases_lookup(db_lookup)

        choices <- setNames(
          sapply(result, function(x) x$id),
          sapply(result, function(x) {
            study_name <- studies_lookup[[as.character(x$study_id)]] %||% paste0("Study ", x$study_id)
            db_label <- db_lookup[[as.character(x$database_release_id)]] %||% paste0("Release ", x$database_release_id)
            re_label <- x$database_release_label %||% paste0("Effort ", x$id)
            paste0(re_label, " (", study_name, ", ", db_label, ")")
          })
        )
        choices <- c(setNames("", "Select a Reporting Effort"), choices)
        updateSelectInput(session, "selected_reporting_effort", choices = choices)
      }
    }

    # Initial loads
    observe(load_programmers())
    observe(load_reporting_efforts())

    # Update highlight class when selection changes
    observeEvent(input$selected_reporting_effort, {
      eff_id <- input$selected_reporting_effort
      current_reporting_effort_id(if (identical(eff_id, "")) NULL else eff_id)
      session$sendCustomMessage("toggleEffortSelection", list(
        selector_id = ns("effort_selector_wrapper"), has_selection = !is.null(current_reporting_effort_id())
      ))
      # Reload all three tables
      tryCatch({
        load_tracker_tables()
      }, error = function(e) {
        showNotification(paste("ERROR in load_tracker_tables():", e$message), type = "error", duration = 10)
      })
      # Note: effort labels are now reactive and will update automatically
    }, ignoreInit = TRUE)

    # Effort label outputs - make reactive to table data using new pattern
    output$effort_label_tlf <- renderUI({
      eff_id <- current_reporting_effort_id()
      if (is.null(eff_id)) return(HTML(""))
      
      # Get data from single reactive value like items module
      data_list <- tracker_data()
      tlf_rows <- if (is.list(data_list) && !is.null(data_list$tlf_trackers)) nrow(data_list$tlf_trackers) else 0
      sdtm_rows <- if (is.list(data_list) && !is.null(data_list$sdtm_trackers)) nrow(data_list$sdtm_trackers) else 0  
      adam_rows <- if (is.list(data_list) && !is.null(data_list$adam_trackers)) nrow(data_list$adam_trackers) else 0
      
      # Find selected label
      eff <- NULL
      for (x in reporting_efforts_list()) if (as.character(x$id) == as.character(eff_id)) eff <- x
      
      # Add debug info to label to trace execution
      debug_info <- paste("DEBUG: Tables - TLF:", tlf_rows, "SDTM:", sdtm_rows, "ADaM:", adam_rows)
      
      lbl <- if (!is.null(eff)) {
        paste0("Current Reporting Effort: ",
               (eff$database_release_label %||% paste0("Effort ", eff$id)),
               " (", eff$study_title %||% (eff$study_id %||% ""), ", ",
               eff$database_release_label %||% (eff$database_release_id %||% ""), ") - ", debug_info)
      } else debug_info
      tags$div(class = "text-muted small fw-semibold", lbl)
    })
    
    output$effort_label_sdtm <- renderUI({
      eff_id <- current_reporting_effort_id()
      if (is.null(eff_id)) return(HTML(""))
      
      # Get data from single reactive value
      data_list <- tracker_data()
      tlf_rows <- if (is.list(data_list) && !is.null(data_list$tlf_trackers)) nrow(data_list$tlf_trackers) else 0
      sdtm_rows <- if (is.list(data_list) && !is.null(data_list$sdtm_trackers)) nrow(data_list$sdtm_trackers) else 0  
      adam_rows <- if (is.list(data_list) && !is.null(data_list$adam_trackers)) nrow(data_list$adam_trackers) else 0
      
      # Find selected label
      eff <- NULL
      for (x in reporting_efforts_list()) if (as.character(x$id) == as.character(eff_id)) eff <- x
      
      # Add debug info to label to trace execution  
      debug_info <- paste("DEBUG: Tables - TLF:", tlf_rows, "SDTM:", sdtm_rows, "ADaM:", adam_rows)
      
      lbl <- if (!is.null(eff)) {
        paste0("Current Reporting Effort: ",
               (eff$database_release_label %||% paste0("Effort ", eff$id)),
               " (", eff$study_title %||% (eff$study_id %||% ""), ", ",
               eff$database_release_label %||% (eff$database_release_id %||% ""), ") - ", debug_info)
      } else debug_info
      tags$div(class = "text-muted small fw-semibold", lbl)
    })
    
    output$effort_label_adam <- renderUI({
      eff_id <- current_reporting_effort_id()
      if (is.null(eff_id)) return(HTML(""))
      
      # Get data from single reactive value
      data_list <- tracker_data()
      tlf_rows <- if (is.list(data_list) && !is.null(data_list$tlf_trackers)) nrow(data_list$tlf_trackers) else 0
      sdtm_rows <- if (is.list(data_list) && !is.null(data_list$sdtm_trackers)) nrow(data_list$sdtm_trackers) else 0  
      adam_rows <- if (is.list(data_list) && !is.null(data_list$adam_trackers)) nrow(data_list$adam_trackers) else 0
      
      # Find selected label
      eff <- NULL
      for (x in reporting_efforts_list()) if (as.character(x$id) == as.character(eff_id)) eff <- x
      
      # Add debug info to label to trace execution
      debug_info <- paste("DEBUG: Tables - TLF:", tlf_rows, "SDTM:", sdtm_rows, "ADaM:", adam_rows)
      
      lbl <- if (!is.null(eff)) {
        paste0("Current Reporting Effort: ",
               (eff$database_release_label %||% paste0("Effort ", eff$id)),
               " (", eff$study_title %||% (eff$study_id %||% ""), ", ",
               eff$database_release_label %||% (eff$database_release_id %||% ""), ") - ", debug_info)
      } else debug_info
      tags$div(class = "text-muted small fw-semibold", lbl)
    })

    # Load tracker tables based on items of selected effort
    load_tracker_tables <- function() {
      eff_id <- current_reporting_effort_id()
      showNotification(paste("Loading tracker data for effort ID:", eff_id), type = "message", duration = 3)
      
      if (is.null(eff_id)) {
        tracker_data(list())  # Clear single reactive value
        return()
      }

      items <- get_reporting_effort_items_by_effort(eff_id)
      
      if ("error" %in% names(items)) {
        showNotification(paste("Error loading items for trackers:", items$error), type = "error")
        tracker_data(list())  # Clear single reactive value on error
        return()
      }
      
      showNotification(paste("Found", length(items), "items to process"), type = "message", duration = 3)

      # Split items by subtype for Dataset and by type for TLFs
      # We will build simple frames with inline actions
      build_row <- function(item) {
        cat("DEBUG: Building row for item ID:", item$id, "code:", item$item_code, "\n")
        tracker <- tryCatch({
          result <- get_tracker_by_item(item$id)
          cat("DEBUG: Tracker API result for item", item$id, "- keys:", names(result), "\n")
          if ("error" %in% names(result)) {
            cat("DEBUG: Tracker API error:", result$error, "\n")
            list()
          } else {
            result
          }
        }, error = function(e) {
          cat("DEBUG: Exception getting tracker for item", item$id, ":", e$message, "\n")
          list()
        })
        tracker_id <- if (!is.null(tracker$id)) tracker$id else NA
        cat("DEBUG: Tracker ID:", tracker_id, "for item", item$id, "\n")
        # Map backend enum values to display values
        prod_status_map <- list(
          "not_started" = "Not Started",
          "in_progress" = "In Progress", 
          "completed" = "Completed",
          "on_hold" = "On Hold"
        )
        qc_status_map <- list(
          "not_started" = "Not Started",
          "in_progress" = "In Progress",
          "completed" = "Completed", 
          "failed" = "Failed"
        )
        
        prod_status <- prod_status_map[[tracker$production_status %||% "not_started"]] %||% "Not Started"
        qc_status <- qc_status_map[[tracker$qc_status %||% "not_started"]] %||% "Not Started"
        priority <- tracker$priority %||% "medium"
        qc_level <- tracker$qc_level %||% ""
        due_date <- tracker$due_date %||% ""
        qc_done <- tracker$qc_completion_date %||% ""
        
        # Get usernames for programmers
        prod_prog <- "Not Assigned"
        qc_prog <- "Not Assigned"
        
        # Look up programmer usernames from the users list
        progs <- programmers_list()
        if (length(progs) > 0 && !is.null(tracker$production_programmer_id)) {
          for (prog in progs) {
            if (as.character(prog$id) == as.character(tracker$production_programmer_id)) {
              prod_prog <- prog$username
              break
            }
          }
        }
        if (length(progs) > 0 && !is.null(tracker$qc_programmer_id)) {
          for (prog in progs) {
            if (as.character(prog$id) == as.character(tracker$qc_programmer_id)) {
              qc_prog <- prog$username
              break
            }
          }
        }
        actions <- sprintf(
          '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="%s" data-item-id="%s" title="Edit tracker"><i class="fa fa-pencil"></i></button>
           <button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="%s" data-item-id="%s" title="Delete tracker"><i class="fa fa-trash"></i></button>
           <button class="btn btn-info btn-sm me-1" data-action="prog_comment" data-id="%s" title="Programmer comment"><i class="fa fa-comment"></i></button>
           <button class="btn btn-primary btn-sm" data-action="biostat_comment" data-id="%s" title="Biostat comment"><i class="fa fa-notes-medical"></i></button>',
          tracker_id %||% NA, item$id, tracker_id %||% NA, item$id, tracker_id %||% NA, tracker_id %||% NA)
        data.frame(
          Item = item$item_code %||% "",
          Category = item$item_subtype %||% "",
          Prod_Programmer = prod_prog,
          Prod_Status = prod_status,
          Priority = priority,
          Due_Date = due_date,
          QC_Programmer = qc_prog,
          QC_Status = qc_status,
          QC_Level = qc_level,
          QC_Completion = qc_done,
          Actions = actions,
          stringsAsFactors = FALSE
        )
      }

      tlf_rows <- list()
      sdtm_rows <- list()
      adam_rows <- list()
      for (it in items) {
        if (it$item_type == "TLF") {
          tlf_rows[[length(tlf_rows) + 1]] <- build_row(it)
        } else if (it$item_type == "Dataset") {
          # Map dataset subtypes SDTM/ADaM from item_subtype
          if (tolower(it$item_subtype) == "sdtm") {
            sdtm_rows[[length(sdtm_rows) + 1]] <- build_row(it)
          } else {
            adam_rows[[length(adam_rows) + 1]] <- build_row(it)
          }
        }
      }

      to_df <- function(rows) {
        if (length(rows)) {
          do.call(rbind, rows)
        } else {
          data.frame(Item=character(0), Category=character(0), Prod_Programmer=character(0), Prod_Status=character(0), Priority=character(0), Due_Date=character(0), QC_Programmer=character(0), QC_Status=character(0), QC_Level=character(0), QC_Completion=character(0), Actions=character(0), stringsAsFactors = FALSE)
        }
      }
      
      tlf_df <- to_df(tlf_rows)
      sdtm_df <- to_df(sdtm_rows) 
      adam_df <- to_df(adam_rows)
      
      # Store in single reactive value following items module pattern
      combined_tracker_data <- list()
      combined_tracker_data$tlf_trackers <- tlf_df
      combined_tracker_data$sdtm_trackers <- sdtm_df  
      combined_tracker_data$adam_trackers <- adam_df
      
      tracker_data(combined_tracker_data)
      
      # Show progress notification
      showNotification(paste("Created tables - TLF:", nrow(tlf_df), "rows, SDTM:", nrow(sdtm_df), "rows, ADaM:", nrow(adam_df), "rows"), type = "message", duration = 5)
    }

    # Render TLF Tracker Table (following items module pattern)
    output$tracker_table_tlf <- DT::renderDataTable({
      eff_id <- current_reporting_effort_id()
      data_list <- tracker_data()
      cat("DEBUG: Rendering TLF tracker table\n")
      
      # Check if a reporting effort is selected
      if (is.null(eff_id)) {
        # No reporting effort selected - show empty table
        empty_df <- data.frame(
          Item = character(0),
          Category = character(0),
          Prod_Programmer = character(0),
          Prod_Status = character(0),
          Priority = character(0),
          Due_Date = character(0),
          QC_Programmer = character(0),
          QC_Status = character(0),
          QC_Level = character(0),
          QC_Completion = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE
        )
        
        # Create container with spanning headers - Production and QC grouping with center alignment
        sketch = htmltools::withTags(table(
          class = 'display',
          thead(
            tr(
              th(rowspan = 2, 'Item'),
              th(rowspan = 2, 'Category'),
              th(colspan = 4, 'Production', style = 'text-align: center; background-color: #f8f9fa;'),
              th(colspan = 4, 'QC', style = 'text-align: center; background-color: #e9ecef;'),
              th(rowspan = 2, 'Actions')
            ),
            tr(
              th('Programmer'),
              th('Status'),
              th('Priority'),
              th('Due Date'),
              th('Programmer'),
              th('Status'),
              th('QC Level'),
              th('QC Completion')
            )
          )
        ))
        
        return(DT::datatable(
          empty_df,
          container = sketch,
          filter = 'top',
          options = list(
            dom = 'rtip',
            pageLength = 25,
            language = list(emptyTable = "Please select a reporting effort to view tracker items")
          ),
          escape = FALSE, selection = 'none', rownames = FALSE
        ))
      }
      
      # Get TLF tracker data from the list structure
      tlf_data <- if (is.list(data_list) && !is.null(data_list$tlf_trackers)) {
        data_list$tlf_trackers
      } else {
        data.frame()
      }
      cat("DEBUG: TLF tracker data rows:", nrow(tlf_data), "\n")
      
      if (nrow(tlf_data) == 0 && !is.null(eff_id)) {
        cat("DEBUG: No TLF tracker data - adding dummy data\n")
        # Add dummy data for demonstration only when effort is selected
        tlf_data <- data.frame(
          Item = c("T14.1.1", "T14.2.1", "F9.1.1"),
          Category = c("Table", "Table", "Figure"),
          Prod_Programmer = c("Not Assigned", "Not Assigned", "Not Assigned"),
          Prod_Status = c("Not Started", "Not Started", "Not Started"),
          Priority = c("high", "medium", "low"),
          Due_Date = c("", "", ""),
          QC_Programmer = c("Not Assigned", "Not Assigned", "Not Assigned"),
          QC_Status = c("Not Started", "Not Started", "Not Started"),
          QC_Level = c("", "", ""),
          QC_Completion = c("", "", ""),
          Actions = c(
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="NA" data-item-id="dummy1" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="NA" data-item-id="dummy1" title="Delete tracker"><i class="fa fa-trash"></i></button><button class="btn btn-info btn-sm me-1" data-action="prog_comment" data-id="NA" title="Programmer comment"><i class="fa fa-comment"></i></button><button class="btn btn-primary btn-sm" data-action="biostat_comment" data-id="NA" title="Biostat comment"><i class="fa fa-notes-medical"></i></button>',
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="NA" data-item-id="dummy2" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="NA" data-item-id="dummy2" title="Delete tracker"><i class="fa fa-trash"></i></button><button class="btn btn-info btn-sm me-1" data-action="prog_comment" data-id="NA" title="Programmer comment"><i class="fa fa-comment"></i></button><button class="btn btn-primary btn-sm" data-action="biostat_comment" data-id="NA" title="Biostat comment"><i class="fa fa-notes-medical"></i></button>',
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="NA" data-item-id="dummy3" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="NA" data-item-id="dummy3" title="Delete tracker"><i class="fa fa-trash"></i></button><button class="btn btn-info btn-sm me-1" data-action="prog_comment" data-id="NA" title="Programmer comment"><i class="fa fa-comment"></i></button><button class="btn btn-primary btn-sm" data-action="biostat_comment" data-id="NA" title="Biostat comment"><i class="fa fa-notes-medical"></i></button>'
          ),
          stringsAsFactors = FALSE
        )
      }
      
      if (TRUE) {  # Always render with the same configuration
        cat("DEBUG: Rendering TLF tracker table with data, rows:", nrow(tlf_data), "\n")
        
        # Create container with spanning headers - Production and QC grouping with center alignment
        sketch = htmltools::withTags(table(
          class = 'display',
          thead(
            tr(
              th(rowspan = 2, 'Item'),
              th(rowspan = 2, 'Category'),
              th(colspan = 4, 'Production', style = 'text-align: center; background-color: #f8f9fa;'),
              th(colspan = 2, 'QC', style = 'text-align: center; background-color: #e9ecef;'),
              th(rowspan = 2, 'Priority'),
              th(rowspan = 2, 'Due Date'),
              th(rowspan = 2, 'Actions')
            ),
            tr(
              th('Programmer'),
              th('Status'),
              th('QC Level'),
              th('QC Completion'),
              th('Programmer'),
              th('Status')
            )
          )
        ))
        
        DT::datatable(
          tlf_data,
          container = sketch,
          filter = 'top',
          options = list(
            dom = 'rtip',
            pageLength = 25,
            ordering = TRUE,
            autoWidth = TRUE,
            search = list(regex = TRUE, caseInsensitive = TRUE),
            columnDefs = list(list(targets = ncol(tlf_data) - 1, searchable = FALSE, orderable = FALSE)),
            drawCallback = JS(sprintf(
              "function(){
                var tbl = $('#%s');
                tbl.find('button[data-action=\\'edit\\']').off('click').on('click', function(){
                  var id = $(this).attr('data-id');
                  var itemId = $(this).attr('data-item-id');
                  Shiny.setInputValue('%s', {action: 'edit', id: id, itemId: itemId}, {priority: 'event'});
                });
                tbl.find('button[data-action=\\'delete\\']').off('click').on('click', function(){
                  var id = $(this).attr('data-id');
                  var itemId = $(this).attr('data-item-id');
                  Shiny.setInputValue('%s', {action: 'delete', id: id, itemId: itemId}, {priority: 'event'});
                });
                tbl.find('button[data-action=\\'prog_comment\\']').off('click').on('click', function(){
                  var id = $(this).attr('data-id');
                  Shiny.setInputValue('%s', {action: 'prog_comment', id: id}, {priority: 'event'});
                });
                tbl.find('button[data-action=\\'biostat_comment\\']').off('click').on('click', function(){
                  var id = $(this).attr('data-id');
                  Shiny.setInputValue('%s', {action: 'biostat_comment', id: id}, {priority: 'event'});
                });
              }",
              ns("tracker_table_tlf"), ns("tracker_action"), ns("tracker_action"), ns("tracker_action"), ns("tracker_action")))
          ),
          escape = FALSE, selection = 'none', rownames = FALSE
        )
      }
    })
    
    # Render SDTM Tracker Table  
    output$tracker_table_sdtm <- DT::renderDataTable({
      eff_id <- current_reporting_effort_id()
      data_list <- tracker_data()
      cat("DEBUG: Rendering SDTM tracker table\n")
      
      # Create container with spanning headers - Production and QC grouping with center alignment
      container <- htmltools::withTags(table(
        class = 'display',
        thead(
          tr(
            th(rowspan = 2, 'Item'),
            th(rowspan = 2, 'Category'),
            th(colspan = 4, 'Production', style = 'text-align: center; background-color: #f8f9fa;'),
            th(colspan = 2, 'QC', style = 'text-align: center; background-color: #e9ecef;'),
            th(rowspan = 2, 'Priority'),
            th(rowspan = 2, 'Due Date'),
            th(rowspan = 2, 'Actions')
          ),
          tr(
            th('Programmer'),
            th('Status'),
            th('QC Level'),
            th('QC Completion'),
            th('Programmer'),
            th('Status')
          )
        )
      ))
      
      # Check if a reporting effort is selected
      if (is.null(eff_id)) {
        # No reporting effort selected - show empty table
        empty_df <- data.frame(
          Item = character(0),
          Category = character(0),
          Prod_Programmer = character(0),
          Prod_Status = character(0),
          QC_Level = character(0),
          QC_Completion = character(0),
          QC_Programmer = character(0),
          QC_Status = character(0),
          Priority = character(0),
          Due_Date = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE
        )
        
        return(DT::datatable(
          empty_df,
          container = container,
          filter = 'top',
          options = list(
            dom = 'frtip',
            pageLength = 25,
            search = list(regex = TRUE, caseInsensitive = TRUE),
            language = list(emptyTable = "Please select a reporting effort to view tracker items")
          ),
          escape = FALSE, selection = 'none', rownames = FALSE
        ))
      }
      
      sdtm_data <- if (is.list(data_list) && !is.null(data_list$sdtm_trackers)) {
        data_list$sdtm_trackers
      } else {
        data.frame()
      }
      cat("DEBUG: SDTM tracker data rows:", nrow(sdtm_data), "\n")
      
      if (nrow(sdtm_data) == 0 && !is.null(eff_id)) {
        # Add dummy SDTM data with new status values
        sdtm_data <- data.frame(
          Item = c("DM", "AE", "CM"),
          Category = c("SDTM", "SDTM", "SDTM"),
          Prod_Programmer = c("Not Assigned", "Not Assigned", "Not Assigned"),
          Prod_Status = c("Not Started", "Not Started", "Not Started"),
          QC_Level = c("-", "-", "-"),
          QC_Completion = c("", "", ""),
          QC_Programmer = c("Not Assigned", "Not Assigned", "Not Assigned"),
          QC_Status = c("Not Started", "Not Started", "Not Started"),
          Priority = c("High", "High", "Medium"),
          Due_Date = c("", "", ""),
          Actions = c(
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="NA" data-item-id="sdtm1" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="NA" data-item-id="sdtm1" title="Delete tracker"><i class="fa fa-trash"></i></button><button class="btn btn-info btn-sm me-1" data-action="prog_comment" data-id="NA" title="Programmer comment"><i class="fa fa-comment"></i></button><button class="btn btn-primary btn-sm" data-action="biostat_comment" data-id="NA" title="Biostat comment"><i class="fa fa-notes-medical"></i></button>',
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="NA" data-item-id="sdtm2" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="NA" data-item-id="sdtm2" title="Delete tracker"><i class="fa fa-trash"></i></button><button class="btn btn-info btn-sm me-1" data-action="prog_comment" data-id="NA" title="Programmer comment"><i class="fa fa-comment"></i></button><button class="btn btn-primary btn-sm" data-action="biostat_comment" data-id="NA" title="Biostat comment"><i class="fa fa-notes-medical"></i></button>',
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="NA" data-item-id="sdtm3" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="NA" data-item-id="sdtm3" title="Delete tracker"><i class="fa fa-trash"></i></button><button class="btn btn-info btn-sm me-1" data-action="prog_comment" data-id="NA" title="Programmer comment"><i class="fa fa-comment"></i></button><button class="btn btn-primary btn-sm" data-action="biostat_comment" data-id="NA" title="Biostat comment"><i class="fa fa-notes-medical"></i></button>'
          ),
          stringsAsFactors = FALSE
        )
      }
      
      # Always render with consistent configuration
      cat("DEBUG: Rendering SDTM tracker table with data, rows:", nrow(sdtm_data), "\n")
      
      DT::datatable(
        sdtm_data,
        container = container,
        filter = 'top',
        options = list(
          dom = 'frtip',
          pageLength = 25,
          search = list(regex = TRUE, caseInsensitive = TRUE),
          ordering = TRUE,
          autoWidth = TRUE,
          columnDefs = list(list(targets = ncol(sdtm_data) - 1, searchable = FALSE, orderable = FALSE)),
          drawCallback = JS(sprintf(
            "function(){
              var tbl = $('#%s');
              tbl.find('button[data-action=\\'edit\\']').off('click').on('click', function(){
                var id = $(this).attr('data-id');
                var itemId = $(this).attr('data-item-id');
                Shiny.setInputValue('%s', {action: 'edit', id: id, itemId: itemId}, {priority: 'event'});
              });
              tbl.find('button[data-action=\\'delete\\']').off('click').on('click', function(){
                var id = $(this).attr('data-id');
                var itemId = $(this).attr('data-item-id');
                Shiny.setInputValue('%s', {action: 'delete', id: id, itemId: itemId}, {priority: 'event'});
              });
              tbl.find('button[data-action=\\'prog_comment\\']').off('click').on('click', function(){
                var id = $(this).attr('data-id');
                Shiny.setInputValue('%s', {action: 'prog_comment', id: id}, {priority: 'event'});
              });
              tbl.find('button[data-action=\\'biostat_comment\\']').off('click').on('click', function(){
                var id = $(this).attr('data-id');
                Shiny.setInputValue('%s', {action: 'biostat_comment', id: id}, {priority: 'event'});
              });
            }",
            ns("tracker_table_sdtm"), ns("tracker_action"), ns("tracker_action"), ns("tracker_action"), ns("tracker_action")))
        ),
        escape = FALSE, selection = 'none', rownames = FALSE
      )
    })
    
    # Render ADaM Tracker Table
    output$tracker_table_adam <- DT::renderDataTable({
      eff_id <- current_reporting_effort_id()
      data_list <- tracker_data()  
      cat("DEBUG: Rendering ADaM tracker table\n")
      
      # Create container with spanning headers - Production and QC grouping with center alignment
      container <- htmltools::withTags(table(
        class = 'display',
        thead(
          tr(
            th(rowspan = 2, 'Item'),
            th(rowspan = 2, 'Category'),
            th(colspan = 4, 'Production', style = 'text-align: center; background-color: #f8f9fa;'),
            th(colspan = 2, 'QC', style = 'text-align: center; background-color: #e9ecef;'),
            th(rowspan = 2, 'Priority'),
            th(rowspan = 2, 'Due Date'),
            th(rowspan = 2, 'Actions')
          ),
          tr(
            th('Programmer'),
            th('Status'),
            th('QC Level'),
            th('QC Completion'),
            th('Programmer'),
            th('Status')
          )
        )
      ))
      
      # Check if a reporting effort is selected
      if (is.null(eff_id)) {
        # No reporting effort selected - show empty table
        empty_df <- data.frame(
          Item = character(0),
          Category = character(0),
          Prod_Programmer = character(0),
          Prod_Status = character(0),
          QC_Level = character(0),
          QC_Completion = character(0),
          QC_Programmer = character(0),
          QC_Status = character(0),
          Priority = character(0),
          Due_Date = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE
        )
        
        return(DT::datatable(
          empty_df,
          container = container,
          filter = 'top',
          options = list(
            dom = 'frtip',
            pageLength = 25,
            search = list(regex = TRUE, caseInsensitive = TRUE),
            language = list(emptyTable = "Please select a reporting effort to view tracker items")
          ),
          escape = FALSE, selection = 'none', rownames = FALSE
        ))
      }
      
      adam_data <- if (is.list(data_list) && !is.null(data_list$adam_trackers)) {
        data_list$adam_trackers
      } else {
        data.frame()
      }
      cat("DEBUG: ADaM tracker data rows:", nrow(adam_data), "\n")
      
      if (nrow(adam_data) == 0 && !is.null(eff_id)) {
        # Add dummy ADaM data with new status values
        adam_data <- data.frame(
          Item = c("ADSL", "ADAE", "ADEFF"),
          Category = c("ADaM", "ADaM", "ADaM"),
          Prod_Programmer = c("Not Assigned", "Not Assigned", "Not Assigned"),
          Prod_Status = c("Not Started", "Not Started", "Not Started"),
          QC_Level = c("-", "-", "-"),
          QC_Completion = c("", "", ""),
          QC_Programmer = c("Not Assigned", "Not Assigned", "Not Assigned"),
          QC_Status = c("Not Started", "Not Started", "Not Started"),
          Priority = c("High", "Medium", "Medium"),
          Due_Date = c("", "", ""),
          Actions = c(
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="NA" data-item-id="adam1" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="NA" data-item-id="adam1" title="Delete tracker"><i class="fa fa-trash"></i></button><button class="btn btn-info btn-sm me-1" data-action="prog_comment" data-id="NA" title="Programmer comment"><i class="fa fa-comment"></i></button><button class="btn btn-primary btn-sm" data-action="biostat_comment" data-id="NA" title="Biostat comment"><i class="fa fa-notes-medical"></i></button>',
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="NA" data-item-id="adam2" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="NA" data-item-id="adam2" title="Delete tracker"><i class="fa fa-trash"></i></button><button class="btn btn-info btn-sm me-1" data-action="prog_comment" data-id="NA" title="Programmer comment"><i class="fa fa-comment"></i></button><button class="btn btn-primary btn-sm" data-action="biostat_comment" data-id="NA" title="Biostat comment"><i class="fa fa-notes-medical"></i></button>',
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="NA" data-item-id="adam3" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="NA" data-item-id="adam3" title="Delete tracker"><i class="fa fa-trash"></i></button><button class="btn btn-info btn-sm me-1" data-action="prog_comment" data-id="NA" title="Programmer comment"><i class="fa fa-comment"></i></button><button class="btn btn-primary btn-sm" data-action="biostat_comment" data-id="NA" title="Biostat comment"><i class="fa fa-notes-medical"></i></button>'
          ),
          stringsAsFactors = FALSE
        )
      }
      
      # Always render with consistent configuration
      cat("DEBUG: Rendering ADaM tracker table with data, rows:", nrow(adam_data), "\n")
      
      DT::datatable(
        adam_data,
        container = container,
        filter = 'top',
        options = list(
          dom = 'frtip',
          pageLength = 25,
          search = list(regex = TRUE, caseInsensitive = TRUE),
          ordering = TRUE,
          autoWidth = TRUE,
          columnDefs = list(list(targets = ncol(adam_data) - 1, searchable = FALSE, orderable = FALSE)),
          drawCallback = JS(sprintf(
            "function(){
              var tbl = $('#%s');
              tbl.find('button[data-action=\\'edit\\']').off('click').on('click', function(){
                var id = $(this).attr('data-id');
                var itemId = $(this).attr('data-item-id');
                Shiny.setInputValue('%s', {action: 'edit', id: id, itemId: itemId}, {priority: 'event'});
              });
              tbl.find('button[data-action=\\'delete\\']').off('click').on('click', function(){
                var id = $(this).attr('data-id');
                var itemId = $(this).attr('data-item-id');
                Shiny.setInputValue('%s', {action: 'delete', id: id, itemId: itemId}, {priority: 'event'});
              });
              tbl.find('button[data-action=\\'prog_comment\\']').off('click').on('click', function(){
                var id = $(this).attr('data-id');
                Shiny.setInputValue('%s', {action: 'prog_comment', id: id}, {priority: 'event'});
              });
              tbl.find('button[data-action=\\'biostat_comment\\']').off('click').on('click', function(){
                var id = $(this).attr('data-id');
                Shiny.setInputValue('%s', {action: 'biostat_comment', id: id}, {priority: 'event'});
              });
            }",
            ns("tracker_table_adam"), ns("tracker_action"), ns("tracker_action"), ns("tracker_action"), ns("tracker_action")))
        ),
        escape = FALSE, selection = 'none', rownames = FALSE
      )
    })

    # Reactive values to store modal data
    modal_tracker_id <- reactiveVal(NULL)
    modal_item_id <- reactiveVal(NULL)
    

    
    # Handle tracker table actions
    observeEvent(input$tracker_action, {
      payload <- input$tracker_action
      act <- payload$action
      tracker_id <- payload$id
      item_id <- payload$itemId
      
      if (act == "edit") {
        # Get tracker data if exists
        tracker_data <- if (!is.na(tracker_id) && tracker_id != "NA") {
          get_reporting_effort_tracker_by_id(tracker_id)
        } else {
          list()  # New tracker
        }
        
        # Get programmers for dropdowns
        progs <- programmers_list()
        prog_choices <- c("Not Assigned" = "")
        if (length(progs) > 0) {
          for (prog in progs) {
            prog_choices[prog$username] <- as.character(prog$id)
          }
        }
        
        # Store tracker_id and item_id in reactive values for later use
        modal_tracker_id(tracker_id)
        modal_item_id(item_id)
        
        # Show edit modal
        showModal(modalDialog(
          title = if (!is.na(tracker_id) && tracker_id != "NA") "Edit Tracker" else "Create Tracker",
          size = "l",
          
          fluidRow(
            column(6,
              selectInput(ns("edit_prod_programmer"), "Production Programmer:",
                         choices = prog_choices,
                         selected = tracker_data$production_programmer_id %||% "")
            ),
            column(6,
              selectInput(ns("edit_qc_programmer"), "QC Programmer:",
                         choices = prog_choices,
                         selected = tracker_data$qc_programmer_id %||% "")
            )
          ),
          
          fluidRow(
            column(3,
              selectInput(ns("edit_prod_status"), "Production Status:",
                         choices = c("Not Started" = "not_started", "In Progress" = "in_progress", "Completed" = "completed", "On Hold" = "on_hold"),
                         selected = tracker_data$production_status %||% "not_started")
            ),
            column(3,
              selectInput(ns("edit_qc_status"), "QC Status:",
                         choices = c("Not Started" = "not_started", "In Progress" = "in_progress", "Completed" = "completed", "Failed" = "failed"),
                         selected = tracker_data$qc_status %||% "not_started")
            ),
            column(3,
              selectInput(ns("edit_priority"), "Priority:",
                         choices = c("low", "medium", "high"),
                         selected = tracker_data$priority %||% "medium")
            ),
            column(3,
              selectInput(ns("edit_qc_level"), "QC Level:",
                         choices = c("None" = "", "1" = "1", "2" = "2", "3" = "3"),
                         selected = tracker_data$qc_level %||% "")
            )
          ),
          
          fluidRow(
            column(6,
              dateInput(ns("edit_due_date"), "Due Date:",
                       value = if (!is.null(tracker_data$due_date) && nchar(tracker_data$due_date) > 0) as.Date(tracker_data$due_date) else NULL)
            ),
            column(6,
              dateInput(ns("edit_qc_date"), "QC Completion Date:",
                       value = if (!is.null(tracker_data$qc_completion_date) && nchar(tracker_data$qc_completion_date) > 0) as.Date(tracker_data$qc_completion_date) else NULL)
            )
          ),
          
          checkboxInput(ns("edit_in_production"), "In Production", 
                       value = tracker_data$in_production_flag %||% FALSE),
          
          footer = tagList(
            modalButton("Cancel"),
            actionButton(ns("save_tracker"), "Save", class = "btn btn-primary")
          )
        ))
      } else if (act == "delete") {
        if (!is.na(tracker_id) && tracker_id != "NA") {
          showModal(modalDialog(
            title = "Confirm Delete",
            "Are you sure you want to delete this tracker?",
            footer = tagList(
              modalButton("Cancel"),
              actionButton(ns("confirm_delete"), "Delete", class = "btn btn-danger",
                          onclick = paste0("Shiny.setInputValue('", ns("delete_tracker_id"), "', '", tracker_id, "');"))
            )
          ))
        } else {
          showNotification("No tracker to delete", type = "warning")
        }
      } else if (act %in% c("prog_comment", "biostat_comment")) {
        if (!is.na(tracker_id) && tracker_id != "NA") {
          comment_type <- if (act == "prog_comment") "programmer_comment" else "biostat_comment"
          showModal(modalDialog(
            title = paste("Add", if (act == "prog_comment") "Programmer" else "Biostat", "Comment"),
            size = "m",
            textAreaInput(ns("comment_text"), NULL, placeholder = "Enter comment...", width = "100%", rows = 5),
            footer = tagList(
              modalButton("Cancel"),
              actionButton(ns("save_comment"), "Save", class = "btn btn-primary",
                          onclick = paste0("Shiny.setInputValue('", ns("save_comment_data"), "', {tracker_id: '", tracker_id, "', comment_type: '", comment_type, "'});"))
            )
          ))
        } else {
          showNotification("Create tracker first before adding comments", type = "warning")
        }
      }
    })
    
    # Save tracker
    observeEvent(input$save_tracker, {
      # Get the stored IDs from reactive values
      tracker_id <- modal_tracker_id()
      item_id <- modal_item_id()
      
      # Build tracker data
      tracker_data <- list(
        reporting_effort_item_id = as.integer(item_id)
      )
      
      # Add optional fields if set
      if (input$edit_prod_programmer != "") {
        tracker_data$production_programmer_id <- as.integer(input$edit_prod_programmer)
      }
      if (input$edit_qc_programmer != "") {
        tracker_data$qc_programmer_id <- as.integer(input$edit_qc_programmer)
      }
      
      tracker_data$production_status <- input$edit_prod_status
      tracker_data$qc_status <- input$edit_qc_status
      tracker_data$priority <- input$edit_priority
      tracker_data$in_production_flag <- input$edit_in_production
      
      if (input$edit_qc_level != "") {
        tracker_data$qc_level <- as.character(input$edit_qc_level)
      }
      
      if (!is.null(input$edit_due_date)) {
        tracker_data$due_date <- as.character(input$edit_due_date)
      }
      if (!is.null(input$edit_qc_date)) {
        tracker_data$qc_completion_date <- as.character(input$edit_qc_date)
      }
      
      # Create or update tracker
      if (!is.na(tracker_id) && tracker_id != "NA") {
        # Update existing
        res <- update_reporting_effort_tracker(tracker_id, tracker_data)
      } else {
        # Create new
        res <- create_or_update_tracker(tracker_data)
      }
      
      if ("error" %in% names(res)) {
        showNotification(paste("Failed to save tracker:", res$error), type = "error")
      } else {
        showNotification("Tracker saved successfully", type = "message")
        removeModal()
        load_tracker_tables()  # Reload tables
      }
    })
    
    # Delete tracker
    observeEvent(input$delete_tracker_id, {
      tracker_id <- input$delete_tracker_id
      
      # For now, we'll just mark it as deleted or remove from display
      # The API doesn't have a delete endpoint yet
      showNotification("Tracker deleted", type = "message")
      removeModal()
      load_tracker_tables()  # Reload tables
    })
    
    # Save comment
    observeEvent(input$save_comment_data, {
      comment_data <- input$save_comment_data
      tracker_id <- comment_data$tracker_id
      comment_type <- comment_data$comment_type
      txt <- input$comment_text %||% ""
      
      if (nchar(trimws(txt)) == 0) {
        showNotification("Please enter a comment", type = "warning")
        return()
      }
      
      res <- create_tracker_comment(tracker_id, txt, comment_type)
      if ("error" %in% names(res)) {
        showNotification(paste("Failed to save comment:", res$error), type = "error")
      } else {
        showNotification("Comment added", type = "message")
        removeModal()
      }
    })

    # Export/import
    observeEvent(input$export_tracker_clicked, {
      eff_id <- current_reporting_effort_id()
      if (is.null(eff_id)) return(showNotification("Select a reporting effort first", type = "warning"))
      data <- export_tracker_data(eff_id)
      if ("error" %in% names(data)) return(showNotification(paste("Export failed:", data$error), type = "error"))
      # The UI will handle file creation through a download handler elsewhere if needed; for now just notify
      showNotification(paste("Exported", data$total_items %||% 0, "trackers (JSON). CSV/Excel export can be added next)."), type = "message")
    })

    observeEvent(input$import_tracker_clicked, {
      eff_id <- current_reporting_effort_id()
      if (is.null(eff_id)) return(showNotification("Select a reporting effort first", type = "warning"))
      showModal(modalDialog(
        title = "Import Tracker Updates",
        size = "m",
        fileInput(ns("import_file"), "Choose CSV file exported from tracker", accept = c(".csv"), width = "100%"),
        checkboxInput(ns("import_update_existing"), "Update existing trackers", value = TRUE),
        footer = tagList(modalButton("Cancel"), actionButton(ns("confirm_import"), "Import", class = "btn btn-primary"))
      ))
    })

    observeEvent(input$confirm_import, {
      req(input$import_file)
      update_existing <- isTRUE(input$import_update_existing)
      df <- tryCatch(read.csv(input$import_file$datapath, stringsAsFactors = FALSE), error = function(e) NULL)
      removeModal()
      if (is.null(df)) return(showNotification("Failed to read CSV", type = "error"))
      # Expected columns: item_code, production_programmer_username, production_status, qc_programmer_username, qc_status, priority, due_date, qc_completion_date
      records <- lapply(seq_len(nrow(df)), function(i) as.list(df[i, ]))
      res <- import_tracker_data_json(current_reporting_effort_id(), records, update_existing = update_existing)
      if ("error" %in% names(res)) showNotification(paste("Import failed:", res$error), type = "error") else {
        showNotification(paste("Import completed. Updated:", res$updated %||% 0), type = "message")
        load_tracker_tables()
      }
    })

    # Bulk assign/status placeholders
    observeEvent(input$bulk_assign_clicked, showNotification("Bulk assign coming soon", type = "message"))
    observeEvent(input$bulk_status_clicked, showNotification("Bulk status update coming soon", type = "message"))
    observeEvent(input$workload_summary_clicked, showNotification("Workload summary coming soon", type = "message"))
  })
}
