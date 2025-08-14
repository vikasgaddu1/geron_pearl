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
        tracker <- tryCatch(get_tracker_by_item(item$id), error = function(e) list())
        tracker_id <- if (!is.null(tracker$id)) tracker$id else NA
        prod_status <- tracker$production_status %||% "not_started"
        qc_status <- tracker$qc_status %||% "not_started"
        priority <- tracker$priority %||% "medium"
        due_date <- tracker$due_date %||% ""
        qc_done <- tracker$qc_completion_date %||% ""
        prod_prog <- tracker$production_programmer_username %||% tracker$production_programmer_id %||% "Not Assigned"
        qc_prog <- tracker$qc_programmer_username %||% tracker$qc_programmer_id %||% "Not Assigned"
        actions <- sprintf(
          "<div class='btn-group btn-group-sm' role='group'>\n           <a href='#' class='btn btn-outline-primary pearl-tracker-action' data-action='prog_comment' data-id='%s' title='Programmer comment'><i class='fa fa-user-edit'></i></a>\n           <a href='#' class='btn btn-outline-info pearl-tracker-action' data-action='biostat_comment' data-id='%s' title='Biostat comment'><i class='fa fa-notes-medical'></i></a>\n           <a href='#' class='btn btn-outline-secondary pearl-tracker-action' data-action='edit' data-id='%s' title='Edit tracker'><i class='fa fa-edit'></i></a>\n         </div>",
          tracker_id %||% item$id, tracker_id %||% item$id, tracker_id %||% item$id)
        data.frame(
          Item = item$item_code %||% "",
          Category = item$item_subtype %||% "",
          Production_Programmer = prod_prog,
          QC_Programmer = qc_prog,
          Priority = priority,
          Production_Status = prod_status,
          QC_Status = qc_status,
          Assign_Date = due_date,
          QC_Completion_Date = qc_done,
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
          data.frame(Item=character(0), Category=character(0), Production_Programmer=character(0), QC_Programmer=character(0), Priority=character(0), Production_Status=character(0), QC_Status=character(0), Assign_Date=character(0), QC_Completion_Date=character(0), Actions=character(0), stringsAsFactors = FALSE)
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
      data_list <- tracker_data()
      cat("DEBUG: Rendering TLF tracker table\n")
      
      # Get TLF tracker data from the list structure
      tlf_data <- if (is.list(data_list) && !is.null(data_list$tlf_trackers)) {
        data_list$tlf_trackers
      } else {
        data.frame()
      }
      cat("DEBUG: TLF tracker data rows:", nrow(tlf_data), "\n")
      
      if (nrow(tlf_data) == 0) {
        cat("DEBUG: No TLF tracker data - rendering empty table\n")
        empty_df <- data.frame(
          Item=character(0), Category=character(0), Priority=character(0), 
          Production_Status=character(0), QC_Status=character(0), Actions=character(0),
          stringsAsFactors = FALSE
        )
        
        DT::datatable(
          empty_df,
          options = list(
            dom = 'rtip', pageLength = 25,
            language = list(emptyTable = "No TLF tracker items found for this reporting effort")
          ),
          escape = FALSE, selection = 'none', rownames = FALSE
        )
      } else {
        cat("DEBUG: Rendering TLF tracker table with data, rows:", nrow(tlf_data), "\n")
        
        DT::datatable(
          tlf_data,
          options = list(dom = 'tpi', pageLength = 25, ordering = TRUE, autoWidth = TRUE,
                         columnDefs = list(list(targets = ncol(tlf_data), orderable = FALSE))),
          escape = FALSE, selection = 'none', rownames = FALSE
        )
      }
    })
    
    # Render SDTM Tracker Table  
    output$tracker_table_sdtm <- DT::renderDataTable({
      data_list <- tracker_data()
      cat("DEBUG: Rendering SDTM tracker table\n")
      
      sdtm_data <- if (is.list(data_list) && !is.null(data_list$sdtm_trackers)) {
        data_list$sdtm_trackers
      } else {
        data.frame()
      }
      cat("DEBUG: SDTM tracker data rows:", nrow(sdtm_data), "\n")
      
      if (nrow(sdtm_data) == 0) {
        empty_df <- data.frame(
          Item=character(0), Category=character(0), Priority=character(0), 
          Production_Status=character(0), QC_Status=character(0), Actions=character(0),
          stringsAsFactors = FALSE
        )
        
        DT::datatable(
          empty_df,
          options = list(
            dom = 'rtip', pageLength = 25,
            language = list(emptyTable = "No SDTM tracker items found for this reporting effort")
          ),
          escape = FALSE, selection = 'none', rownames = FALSE
        )
      } else {
        cat("DEBUG: Rendering SDTM tracker table with data, rows:", nrow(sdtm_data), "\n")
        
        DT::datatable(
          sdtm_data,
          options = list(dom = 'tpi', pageLength = 25, ordering = TRUE, autoWidth = TRUE,
                         columnDefs = list(list(targets = ncol(sdtm_data), orderable = FALSE))),
          escape = FALSE, selection = 'none', rownames = FALSE
        )
      }
    })
    
    # Render ADaM Tracker Table
    output$tracker_table_adam <- DT::renderDataTable({
      data_list <- tracker_data()  
      cat("DEBUG: Rendering ADaM tracker table\n")
      
      adam_data <- if (is.list(data_list) && !is.null(data_list$adam_trackers)) {
        data_list$adam_trackers
      } else {
        data.frame()
      }
      cat("DEBUG: ADaM tracker data rows:", nrow(adam_data), "\n")
      
      if (nrow(adam_data) == 0) {
        empty_df <- data.frame(
          Item=character(0), Category=character(0), Priority=character(0), 
          Production_Status=character(0), QC_Status=character(0), Actions=character(0),
          stringsAsFactors = FALSE
        )
        
        DT::datatable(
          empty_df,
          options = list(
            dom = 'rtip', pageLength = 25,
            language = list(emptyTable = "No ADaM tracker items found for this reporting effort")
          ),
          escape = FALSE, selection = 'none', rownames = FALSE
        )
      } else {
        cat("DEBUG: Rendering ADaM tracker table with data, rows:", nrow(adam_data), "\n")
        
        DT::datatable(
          adam_data,
          options = list(dom = 'tpi', pageLength = 25, ordering = TRUE, autoWidth = TRUE,
                         columnDefs = list(list(targets = ncol(adam_data), orderable = FALSE))),
          escape = FALSE, selection = 'none', rownames = FALSE
        )
      }
    })

    # Inline row actions
    observeEvent(input$row_action, {
      payload <- input$row_action
      act <- payload$action
      target_id <- payload$id
      if (act %in% c("prog_comment", "biostat_comment")) {
        comment_type <- if (act == "prog_comment") "programmer_comment" else "biostat_comment"
        showModal(modalDialog(
          title = paste("Add", if (act == "prog_comment") "Programmer" else "Biostat", "Comment"),
          size = "m",
          textAreaInput(ns("comment_text"), NULL, placeholder = "Enter comment...", width = "100%", rows = 5),
          footer = tagList(
            modalButton("Cancel"),
            actionButton(ns("save_comment"), "Save", class = "btn btn-primary")
          )
        ))
        once <- new.env(parent = emptyenv()); once$done <- FALSE
        observeEvent(input$save_comment, {
          if (once$done) return(NULL)
          once$done <- TRUE
          removeModal()
          txt <- input$comment_text %||% ""
          if (nchar(trimws(txt)) == 0) return(NULL)
          res <- create_tracker_comment(target_id, txt, comment_type)
          if ("error" %in% names(res)) showNotification(paste("Failed to save comment:", res$error), type = "error") else showNotification("Comment added", type = "message")
        }, ignoreInit = TRUE, once = TRUE)
      } else if (act == "edit") {
        showNotification("Edit UI coming soon", type = "message")
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