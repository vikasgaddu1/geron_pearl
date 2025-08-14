reporting_effort_tracker_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns

    # Helpers
    `%||%` <- function(x, y) if (is.null(x) || length(x) == 0) y else x

    # Reactive values
    current_reporting_effort_id <- reactiveVal(NULL)
    reporting_efforts_list <- reactiveVal(list())
    database_releases_lookup <- reactiveVal(list())

    trackers_tlf <- reactiveVal(data.frame())
    trackers_sdtm <- reactiveVal(data.frame())
    trackers_adam <- reactiveVal(data.frame())

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
      load_tracker_tables()
      # Update effort label under each tab
      render_effort_labels()
    }, ignoreInit = TRUE)

    # Effort label outputs
    render_effort_labels <- function() {
      eff_id <- current_reporting_effort_id()
      if (is.null(eff_id)) {
        output$effort_label_tlf <- renderUI(HTML(""))
        output$effort_label_sdtm <- renderUI(HTML(""))
        output$effort_label_adam <- renderUI(HTML(""))
        return()
      }
      # Find selected label
      eff <- NULL
      for (x in reporting_efforts_list()) if (as.character(x$id) == as.character(eff_id)) eff <- x
      lbl <- if (!is.null(eff)) {
        paste0("Current Reporting Effort: ",
               (eff$database_release_label %||% paste0("Effort ", eff$id)),
               " (", eff$study_title %||% (eff$study_id %||% ""), ", ",
               eff$database_release_label %||% (eff$database_release_id %||% ""), ")")
      } else ""
      output$effort_label_tlf <- renderUI(tags$div(class = "text-muted small", lbl))
      output$effort_label_sdtm <- renderUI(tags$div(class = "text-muted small", lbl))
      output$effort_label_adam <- renderUI(tags$div(class = "text-muted small", lbl))
    }

    # Load tracker tables based on items of selected effort
    load_tracker_tables <- function() {
      eff_id <- current_reporting_effort_id()
      if (is.null(eff_id)) {
        trackers_tlf(data.frame())
        trackers_sdtm(data.frame())
        trackers_adam(data.frame())
        return()
      }

      items <- get_reporting_effort_items_by_effort(eff_id)
      if ("error" %in% names(items)) {
        showNotification(paste("Error loading items for trackers:", items$error), type = "error")
        trackers_tlf(data.frame()); trackers_sdtm(data.frame()); trackers_adam(data.frame())
        return()
      }

      # Split items by subtype for Dataset and by type for TLFs
      # We will build simple frames with inline actions
      build_row <- function(item) {
        tracker <- tryCatch(get_tracker_by_item(item$id), error = function(e) list())
        tracker_id <- if (!is.null(tracker$id)) tracker$id else NA
        prod_status <- tracker$production_status %||% "not_started"
        qc_status <- tracker$qc_status %||% "not_started"
        priority <- tracker$priority %||% "medium"
        actions <- sprintf(
          "<div class='btn-group btn-group-sm' role='group'>\n           <a href='#' class='btn btn-outline-primary pearl-tracker-action' data-action='prog_comment' data-id='%s' title='Programmer comment'><i class='fa fa-user-edit'></i></a>\n           <a href='#' class='btn btn-outline-info pearl-tracker-action' data-action='biostat_comment' data-id='%s' title='Biostat comment'><i class='fa fa-notes-medical'></i></a>\n           <a href='#' class='btn btn-outline-secondary pearl-tracker-action' data-action='edit' data-id='%s' title='Edit tracker'><i class='fa fa-edit'></i></a>\n         </div>",
          tracker_id %||% item$id, tracker_id %||% item$id, tracker_id %||% item$id)
        data.frame(
          Item = item$item_code %||% "",
          Category = item$item_subtype %||% "",
          Priority = priority,
          Production_Status = prod_status,
          QC_Status = qc_status,
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
          if (tolower(it$item_subtype) == "sdtm") sdtm_rows[[length(sdtm_rows) + 1]] <- build_row(it)
          else adam_rows[[length(adam_rows) + 1]] <- build_row(it)
        }
      }

      to_df <- function(rows) if (length(rows)) do.call(rbind, rows) else data.frame(Item=character(0), Category=character(0), Priority=character(0), Production_Status=character(0), QC_Status=character(0), Actions=character(0), stringsAsFactors = FALSE)
      trackers_tlf(to_df(tlf_rows))
      trackers_sdtm(to_df(sdtm_rows))
      trackers_adam(to_df(adam_rows))
    }

    # Render DataTables
    render_tracker_table <- function(data_rv) {
      DT::renderDataTable({
        df <- data_rv()
        if (nrow(df) == 0) {
          df <- data.frame(Item=character(0), Category=character(0), Priority=character(0), Production_Status=character(0), QC_Status=character(0), Actions=character(0), stringsAsFactors = FALSE)
        }
        DT::datatable(
          df,
          options = list(dom = 'rtip', pageLength = 25, ordering = TRUE, autoWidth = TRUE, columnDefs = list(list(targets = ncol(df), orderable = FALSE))),
          escape = FALSE,
          selection = 'none',
          rownames = FALSE
        )
      })
    }
    output$tracker_table_tlf <- render_tracker_table(trackers_tlf)
    output$tracker_table_sdtm <- render_tracker_table(trackers_sdtm)
    output$tracker_table_adam <- render_tracker_table(trackers_adam)

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