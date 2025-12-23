# Dashboard Server Module - Role-Based Dashboards
# Provides Lead Dashboard and Programmer Dashboard functionality

admin_dashboard_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns

    # Reactive values for dashboard data
    rv <- reactiveValues(
      users = list(),
      current_user_id = NULL,
      workload_data = NULL,
      all_trackers = list(),
      studies = list(),
      last_refresh = NULL,
      assignment_filter = "all",  # all, production, qc
      users_loaded = FALSE  # Flag to track if users have been loaded
    )

    # Load all users for the selector (only fetches data, doesn't update UI)
    load_users <- function() {
      users_result <- get_users()
      if (!is.null(users_result) && is.null(users_result$error)) {
        rv$users <- users_result
        rv$users_loaded <- TRUE
      }
    }
    
    # Load workload data for selected user
    load_workload_data <- function(user_id) {
      if (is.null(user_id) || user_id == "") return()
      
      workload_result <- get_programmer_workload(as.integer(user_id))
      if (!is.null(workload_result) && is.null(workload_result$error)) {
        rv$workload_data <- workload_result
      } else {
        rv$workload_data <- list(
          production = list(stats = list(total = 0, not_started = 0, in_progress = 0, completed = 0, on_hold = 0), trackers = list()),
          qc = list(stats = list(total = 0, not_started = 0, in_progress = 0, completed = 0, failed = 0), trackers = list()),
          total_workload = 0
        )
      }
    }
    
    # Load all trackers for lead dashboard
    load_all_trackers <- function() {
      trackers_result <- get_reporting_effort_tracker()
      if (!is.null(trackers_result) && is.null(trackers_result$error)) {
        rv$all_trackers <- trackers_result
      } else {
        rv$all_trackers <- list()
      }
    }
    
    # Load studies
    load_studies <- function() {
      studies_result <- get_studies()
      if (!is.null(studies_result) && is.null(studies_result$error)) {
        rv$studies <- studies_result
      } else {
        rv$studies <- list()
      }
    }
    
    # Load all dashboard data (studies and trackers only - users handled separately)
    load_dashboard_data <- function() {
      load_studies()
      load_all_trackers()

      # Load workload for current user - use isolate to prevent reactive dependency
      current_user <- isolate(rv$current_user_id)
      if (!is.null(current_user) && current_user != "") {
        load_workload_data(current_user)
      }

      rv$last_refresh <- Sys.time()
    }

    # Initial load - load users once at startup
    observe({
      if (!rv$users_loaded) {
        load_users()
        load_studies()
        load_all_trackers()
        rv$last_refresh <- Sys.time()
      }
    })

    # Watch for user selector changes and initial render
    # ignoreInit = FALSE so we catch the first render when selectInput gets a value
    observeEvent(input$current_user, {
      req(input$current_user)
      if (input$current_user != "") {
        new_user <- as.character(input$current_user)
        # Only load workload if the user actually changed
        if (is.null(rv$current_user_id) || rv$current_user_id != new_user) {
          rv$current_user_id <- new_user
          load_workload_data(new_user)
        }
      }
    }, ignoreInit = FALSE)

    # Build choices for user selector (reactive)
    user_choices <- reactive({
      req(rv$users_loaded)
      choices <- c()
      for (user in rv$users) {
        dept_label <- if (!is.null(user$department) && user$department != "") {
          paste0(" (", user$department, ")")
        } else {
          ""
        }
        choices[paste0(user$username, dept_label)] <- user$id
      }
      choices
    })

    # Render user selector UI - only re-renders when users list changes
    output$user_selector_ui <- renderUI({
      choices <- user_choices()

      if (length(choices) == 0) {
        return(tags$span("Loading...", class = "text-muted"))
      }

      # Get current selection to preserve it (if any)
      current_selection <- isolate(rv$current_user_id)

      # Determine which user to select:
      # - If we have a valid current selection, keep it
      # - Otherwise, select the first user
      selected_user <- if (!is.null(current_selection) &&
                           current_selection != "" &&
                           current_selection %in% choices) {
        current_selection
      } else if (length(choices) > 0) {
        as.character(choices[1])
      } else {
        NULL
      }

      selectInput(
        ns("current_user"),
        label = NULL,
        choices = choices,
        selected = selected_user,
        width = "200px"
      )
    })

    # Manual refresh
    observeEvent(input$refresh_dashboard, {
      load_dashboard_data()
      show_success_notification("Dashboard refreshed", duration = 2000)
    })
    
    # Filter buttons
    observeEvent(input$filter_all, {
      rv$assignment_filter <- "all"
      shinyjs::runjs(sprintf("
        $('#%s').addClass('active');
        $('#%s').removeClass('active');
        $('#%s').removeClass('active');
      ", ns("filter_all"), ns("filter_production"), ns("filter_qc")))
    })
    
    observeEvent(input$filter_production, {
      rv$assignment_filter <- "production"
      shinyjs::runjs(sprintf("
        $('#%s').removeClass('active');
        $('#%s').addClass('active');
        $('#%s').removeClass('active');
      ", ns("filter_all"), ns("filter_production"), ns("filter_qc")))
    })
    
    observeEvent(input$filter_qc, {
      rv$assignment_filter <- "qc"
      shinyjs::runjs(sprintf("
        $('#%s').removeClass('active');
        $('#%s').removeClass('active');
        $('#%s').addClass('active');
      ", ns("filter_all"), ns("filter_production"), ns("filter_qc")))
    })
    
    # Helper: Calculate overdue and due soon counts
    get_deadline_stats <- function(trackers) {
      today <- Sys.Date()
      week_ahead <- today + 7
      
      overdue <- 0
      due_soon <- 0
      
      for (tracker in trackers) {
        if (!is.null(tracker$due_date) && tracker$due_date != "") {
          due_date <- tryCatch({
            as.Date(tracker$due_date)
          }, error = function(e) NULL)
          
          if (!is.null(due_date)) {
            # Check if not completed
            status <- tracker$production_status %||% tracker$status %||% "not_started"
            if (status != "completed") {
              if (due_date < today) {
                overdue <- overdue + 1
              } else if (due_date <= week_ahead) {
                due_soon <- due_soon + 1
              }
            }
          }
        }
      }
      
      list(overdue = overdue, due_soon = due_soon)
    }
    
    # Helper: Get in production count
    get_in_production_count <- function(trackers) {
      count <- 0
      for (tracker in trackers) {
        if (isTRUE(tracker$in_production_flag) || isTRUE(tracker$in_production)) {
          count <- count + 1
        }
      }
      count
    }
    
    # ============================================
    # PROGRAMMER DASHBOARD OUTPUTS
    # ============================================
    
    # Total Assignments
    output$prog_total_assignments <- renderText({
      if (is.null(rv$workload_data)) return("0")
      as.character(rv$workload_data$total_workload %||% 0)
    })
    
    # In Production count
    output$prog_in_production <- renderText({
      if (is.null(rv$workload_data)) return("0")

      all_trackers <- c(
        rv$workload_data$production$trackers %||% list(),
        rv$workload_data$qc$trackers %||% list()
      )

      as.character(get_in_production_count(all_trackers))
    })

    # Not Started count
    output$prog_not_started_value <- renderUI({
      if (is.null(rv$workload_data)) {
        return(div(class = "metric-value", "0"))
      }

      prod_not_started <- rv$workload_data$production$stats$not_started %||% 0
      qc_not_started <- rv$workload_data$qc$stats$not_started %||% 0
      total_not_started <- prod_not_started + qc_not_started

      div(class = "metric-value", total_not_started)
    })

    # Overdue count
    output$prog_overdue_value <- renderUI({
      if (is.null(rv$workload_data)) {
        return(div(class = "metric-value", "0"))
      }
      
      all_trackers <- c(
        rv$workload_data$production$trackers %||% list(),
        rv$workload_data$qc$trackers %||% list()
      )
      
      stats <- get_deadline_stats(all_trackers)
      
      if (stats$overdue > 0) {
        div(class = "metric-value danger", stats$overdue)
      } else {
        div(class = "metric-value success", "0")
      }
    })
    
    # Due soon count
    output$prog_due_soon_value <- renderUI({
      if (is.null(rv$workload_data)) {
        return(div(class = "metric-value", "0"))
      }
      
      all_trackers <- c(
        rv$workload_data$production$trackers %||% list(),
        rv$workload_data$qc$trackers %||% list()
      )
      
      stats <- get_deadline_stats(all_trackers)
      
      if (stats$due_soon > 0) {
        div(class = "metric-value warning", stats$due_soon)
      } else {
        div(class = "metric-value", "0")
      }
    })
    
    # My Assignments Table
    output$my_assignments_table <- DT::renderDataTable({
      if (is.null(rv$workload_data)) {
        return(DT::datatable(
          data.frame(Message = "Select a user to view assignments"),
          options = list(dom = 't'),
          rownames = FALSE
        ))
      }

      # Build combined assignments dataframe with enhanced columns
      assignments <- data.frame(
        ID = integer(0),
        Item = character(0),
        Study = character(0),
        DB_RE = character(0),
        Type = character(0),
        Status = character(0),
        Status_Raw = character(0),
        Priority = character(0),
        Due_Date = character(0),
        In_Production = character(0),
        RE_ID = integer(0),
        Actions = character(0),
        stringsAsFactors = FALSE
      )

      today <- Sys.Date()

      # Helper to format item display as "category, item_code"
      format_item <- function(tracker) {
        # Try multiple possible field names for item_code
        item_code <- tracker$item_code
        if (is.null(item_code) || item_code == "") {
          # Fallback to nested item object if present
          if (!is.null(tracker$item) && !is.null(tracker$item$item_code)) {
            item_code <- tracker$item$item_code
          } else {
            item_code <- paste0("Item #", tracker$reporting_effort_item_id %||% tracker$id)
          }
        }
        
        item_subtype <- tracker$item_subtype %||% tracker$item$item_subtype %||% ""
        if (item_subtype != "" && !is.null(item_subtype)) {
          paste0(item_subtype, ", ", item_code)
        } else {
          item_code
        }
      }

      # Helper to format DB/RE column  
      format_db_re <- function(tracker) {
        # Try multiple possible field names
        db_label <- tracker$database_release_label
        if (is.null(db_label) || db_label == "") {
          # Try nested paths
          db_label <- tracker$item$reporting_effort$database_release$database_release_label %||% ""
        }
        
        re_label <- tracker$reporting_effort_label
        if (is.null(re_label) || re_label == "") {
          re_label <- tracker$item$reporting_effort$database_release_label %||% ""
        }
        
        if (!is.null(db_label) && db_label != "" && !is.null(re_label) && re_label != "") {
          paste0(db_label, " / ", re_label)
        } else if (!is.null(db_label) && db_label != "") {
          db_label
        } else if (!is.null(re_label) && re_label != "") {
          re_label
        } else {
          "-"
        }
      }
      
      # Helper to safely get study label
      get_study_label <- function(tracker) {
        study_label <- tracker$study_label
        if (is.null(study_label) || study_label == "") {
          study_label <- tracker$item$reporting_effort$study$study_label %||% "-"
        }
        study_label %||% "-"
      }

      # Helper to create action buttons HTML
      create_action_buttons <- function(tracker_id, status, type, re_id, item_code) {
        status_type <- if (type == "Production") "production" else "qc"

        # Start button (only if not_started)
        start_btn <- if (status == "not_started") {
          sprintf(
            '<button class="btn btn-success btn-sm me-1 quick-status-btn" data-tracker-id="%s" data-status="in_progress" data-type="%s" title="Start">
               <i class="bi bi-play-fill"></i>
             </button>',
            tracker_id, status_type
          )
        } else {
          ""
        }

        # Complete button (only if in_progress)
        complete_btn <- if (status == "in_progress") {
          sprintf(
            '<button class="btn btn-primary btn-sm me-1 quick-status-btn" data-tracker-id="%s" data-status="completed" data-type="%s" title="Complete">
               <i class="bi bi-check-lg"></i>
             </button>',
            tracker_id, status_type
          )
        } else {
          ""
        }

        # Go to Tracker button (always visible)
        go_btn <- sprintf(
          '<button class="btn btn-outline-secondary btn-sm go-to-tracker-btn" data-reporting-effort-id="%s" data-item-code="%s" title="Go to Tracker">
             <i class="bi bi-box-arrow-up-right"></i>
           </button>',
          re_id, item_code
        )

        paste0('<div class="d-flex justify-content-center">', start_btn, complete_btn, go_btn, '</div>')
      }

      # Add production assignments - PENDING TASKS ONLY
      # Show production items where QC is not completed (pending work)
      if (rv$assignment_filter %in% c("all", "production")) {
        prod_trackers <- rv$workload_data$production$trackers %||% list()
        
        # Filter to show only pending tasks: QC not completed
        prod_trackers <- Filter(function(t) {
          qc_status <- t$qc_status %||% "not_started"
          # Show if QC is not completed (pending work for this production programmer)
          qc_status != "completed"
        }, prod_trackers)
        
        cat("DEBUG: Production trackers after pending filter:", length(prod_trackers), "\n")
        
        for (tracker in prod_trackers) {
          due_date_str <- ""
          if (!is.null(tracker$due_date) && tracker$due_date != "") {
            due_date <- tryCatch(as.Date(tracker$due_date), error = function(e) NULL)
            if (!is.null(due_date)) {
              due_date_str <- format(due_date, "%Y-%m-%d")
            }
          }

          status_raw <- tracker$production_status %||% "not_started"
          item_code <- tracker$item_code %||% paste0("Item #", tracker$reporting_effort_item_id)
          re_id <- tracker$reporting_effort_id %||% 0
          
          # Debug logging for data mapping
          cat("DEBUG: Tracker", tracker$id, "-> item_code:", tracker$item_code %||% "NULL",
              ", study:", tracker$study_label %||% "NULL",
              ", db:", tracker$database_release_label %||% "NULL", "\n")

          assignments <- rbind(assignments, data.frame(
            ID = tracker$id %||% 0,
            Item = format_item(tracker),
            Study = get_study_label(tracker),
            DB_RE = format_db_re(tracker),
            Type = "Production",
            Status = status_raw,
            Status_Raw = status_raw,
            Priority = tracker$priority %||% "medium",
            Due_Date = due_date_str,
            In_Production = if (isTRUE(tracker$in_production_flag) || isTRUE(tracker$in_production)) "Yes" else "No",
            RE_ID = re_id,
            Actions = create_action_buttons(tracker$id %||% 0, status_raw, "Production", re_id, item_code),
            stringsAsFactors = FALSE
          ))
        }
      }

      # Add QC assignments - PENDING TASKS ONLY
      # Show QC items where QC is not completed
      if (rv$assignment_filter %in% c("all", "qc")) {
        qc_trackers <- rv$workload_data$qc$trackers %||% list()
        
        # Filter to show only pending QC tasks: QC not completed
        qc_trackers <- Filter(function(t) {
          qc_status <- t$qc_status %||% "not_started"
          qc_status != "completed"
        }, qc_trackers)
        
        cat("DEBUG: QC trackers after pending filter:", length(qc_trackers), "\n")
        
        for (tracker in qc_trackers) {
          due_date_str <- ""
          if (!is.null(tracker$due_date) && tracker$due_date != "") {
            due_date <- tryCatch(as.Date(tracker$due_date), error = function(e) NULL)
            if (!is.null(due_date)) {
              due_date_str <- format(due_date, "%Y-%m-%d")
            }
          }

          status_raw <- tracker$qc_status %||% "not_started"
          item_code <- tracker$item_code %||% paste0("Item #", tracker$reporting_effort_item_id)
          re_id <- tracker$reporting_effort_id %||% 0
          
          # Debug logging for data mapping
          cat("DEBUG: QC Tracker", tracker$id, "-> item_code:", tracker$item_code %||% "NULL",
              ", study:", tracker$study_label %||% "NULL",
              ", db:", tracker$database_release_label %||% "NULL", "\n")

          assignments <- rbind(assignments, data.frame(
            ID = tracker$id %||% 0,
            Item = format_item(tracker),
            Study = get_study_label(tracker),
            DB_RE = format_db_re(tracker),
            Type = "QC",
            Status = status_raw,
            Status_Raw = status_raw,
            Priority = tracker$priority %||% "medium",
            Due_Date = due_date_str,
            In_Production = if (isTRUE(tracker$in_production_flag) || isTRUE(tracker$in_production)) "Yes" else "No",
            RE_ID = re_id,
            Actions = create_action_buttons(tracker$id %||% 0, status_raw, "QC", re_id, item_code),
            stringsAsFactors = FALSE
          ))
        }
      }

      if (nrow(assignments) == 0) {
        return(DT::datatable(
          data.frame(Message = "No pending tasks found - all work is complete or QC passed!"),
          options = list(dom = 't'),
          rownames = FALSE
        ))
      }

      # Format for display
      assignments$Priority <- sapply(assignments$Priority, function(p) {
        sprintf('<span class="priority-badge priority-%s">%s</span>', p, toupper(p))
      })

      assignments$Status <- sapply(assignments$Status, function(s) {
        label <- gsub("_", " ", s)
        label <- paste0(toupper(substr(label, 1, 1)), substr(label, 2, nchar(label)))
        sprintf('<span class="status-badge status-%s">%s</span>', s, label)
      })

      assignments$Type <- sapply(assignments$Type, function(t) {
        if (t == "Production") {
          '<span class="badge bg-primary">Production</span>'
        } else {
          '<span class="badge bg-info">QC</span>'
        }
      })

      # Rename columns for display
      colnames(assignments) <- c("ID", "Item", "Study", "DB / RE", "Type", "Status", "Status_Raw", "Priority", "Due Date", "In Production", "RE_ID", "Actions")

      DT::datatable(
        assignments,
        options = list(
          dom = 'frtip',
          pageLength = 10,
          order = list(list(8, 'asc')),  # Sort by due date
          columnDefs = list(
            list(visible = FALSE, targets = c(0, 6, 10)),  # Hide ID, Status_Raw, RE_ID columns
            list(className = 'text-center', targets = c(4, 5, 7, 9, 11))
          )
        ),
        escape = FALSE,
        rownames = FALSE,
        selection = 'none'
      )
    }, server = FALSE)
    
    # Upcoming Deadlines List
    output$upcoming_deadlines_list <- renderUI({
      if (is.null(rv$workload_data)) {
        return(div(class = "empty-state", icon("calendar"), p("No deadline data available")))
      }
      
      all_trackers <- c(
        rv$workload_data$production$trackers %||% list(),
        rv$workload_data$qc$trackers %||% list()
      )
      
      today <- Sys.Date()
      upcoming <- list()
      
      for (tracker in all_trackers) {
        if (!is.null(tracker$due_date) && tracker$due_date != "") {
          due_date <- tryCatch(as.Date(tracker$due_date), error = function(e) NULL)
          if (!is.null(due_date)) {
            # Check status
            status <- tracker$production_status %||% tracker$qc_status %||% "not_started"
            if (status != "completed") {
              item_code <- tracker$item_code %||% tracker$item$item_code %||% paste0("Item #", tracker$reporting_effort_item_id)
              upcoming[[length(upcoming) + 1]] <- list(
                item = item_code,
                due_date = due_date,
                priority = tracker$priority %||% "medium",
                status = status,
                is_overdue = due_date < today,
                days_until = as.integer(due_date - today)
              )
            }
          }
        }
      }
      
      if (length(upcoming) == 0) {
        return(div(
          class = "empty-state",
          icon("check-circle"),
          p("No upcoming deadlines"),
          tags$small("All items are either completed or have no due date", class = "text-muted")
        ))
      }
      
      # Sort by due date
      upcoming <- upcoming[order(sapply(upcoming, function(x) x$due_date))]
      
      # Take first 15 items
      if (length(upcoming) > 15) {
        upcoming <- upcoming[1:15]
      }
      
      items <- lapply(upcoming, function(item) {
        item_class <- if (item$is_overdue) {
          "deadline-item overdue"
        } else if (item$days_until <= 7) {
          "deadline-item due-soon"
        } else {
          "deadline-item"
        }
        
        due_label <- if (item$is_overdue) {
          sprintf('<span class="badge bg-danger">%d days overdue</span>', abs(item$days_until))
        } else if (item$days_until == 0) {
          '<span class="badge bg-warning">Due Today</span>'
        } else if (item$days_until == 1) {
          '<span class="badge bg-warning">Due Tomorrow</span>'
        } else if (item$days_until <= 7) {
          sprintf('<span class="badge bg-warning">%d days left</span>', item$days_until)
        } else {
          sprintf('<span class="badge bg-secondary">%d days left</span>', item$days_until)
        }
        
        div(
          class = item_class,
          div(
            class = "flex-grow-1",
            div(class = "fw-semibold", item$item),
            div(
              class = "d-flex align-items-center gap-2 mt-1",
              tags$small(class = "text-muted", format(item$due_date, "%b %d, %Y")),
              HTML(sprintf('<span class="priority-badge priority-%s">%s</span>', 
                          item$priority, toupper(item$priority)))
            )
          ),
          HTML(due_label)
        )
      })
      
      tagList(items)
    })
    
    # Production Status Breakdown
    output$production_status_breakdown <- renderUI({
      if (is.null(rv$workload_data)) {
        return(div(class = "text-muted", "No data available"))
      }
      
      stats <- rv$workload_data$production$stats
      if (is.null(stats) || stats$total == 0) {
        return(div(class = "text-muted", "No production assignments"))
      }
      
      statuses <- list(
        list(label = "Not Started", value = stats$not_started %||% 0, color = "#e9ecef"),
        list(label = "In Progress", value = stats$in_progress %||% 0, color = "#0dcaf0"),
        list(label = "Completed", value = stats$completed %||% 0, color = "#198754"),
        list(label = "On Hold", value = stats$on_hold %||% 0, color = "#6c757d")
      )
      
      items <- lapply(statuses, function(s) {
        pct <- round((s$value / stats$total) * 100)
        div(
          class = "mb-3",
          div(
            class = "d-flex justify-content-between mb-1",
            tags$span(s$label),
            tags$span(paste0(s$value, " (", pct, "%)"))
          ),
          div(
            class = "workload-progress",
            div(
              class = "workload-bar",
              style = sprintf("width: %d%%; background: %s;", pct, s$color)
            )
          )
        )
      })
      
      tagList(
        div(class = "mb-3", tags$strong(paste("Total:", stats$total))),
        items
      )
    })
    
    # QC Status Breakdown
    output$qc_status_breakdown <- renderUI({
      if (is.null(rv$workload_data)) {
        return(div(class = "text-muted", "No data available"))
      }
      
      stats <- rv$workload_data$qc$stats
      if (is.null(stats) || stats$total == 0) {
        return(div(class = "text-muted", "No QC assignments"))
      }
      
      statuses <- list(
        list(label = "Not Started", value = stats$not_started %||% 0, color = "#e9ecef"),
        list(label = "In Progress", value = stats$in_progress %||% 0, color = "#0dcaf0"),
        list(label = "Completed", value = stats$completed %||% 0, color = "#198754"),
        list(label = "Failed", value = stats$failed %||% 0, color = "#dc3545")
      )
      
      items <- lapply(statuses, function(s) {
        pct <- round((s$value / stats$total) * 100)
        div(
          class = "mb-3",
          div(
            class = "d-flex justify-content-between mb-1",
            tags$span(s$label),
            tags$span(paste0(s$value, " (", pct, "%)"))
          ),
          div(
            class = "workload-progress",
            div(
              class = "workload-bar",
              style = sprintf("width: %d%%; background: %s;", pct, s$color)
            )
          )
        )
      })
      
      tagList(
        div(class = "mb-3", tags$strong(paste("Total:", stats$total))),
        items
      )
    })
    
    # ============================================
    # LEAD DASHBOARD OUTPUTS
    # ============================================
    
    # Define consistent status colors
    status_colors <- list(
      not_started = "#e9ecef",
      in_progress = "#0dcaf0",
      completed = "#198754",
      on_hold = "#6c757d",
      failed = "#dc3545"
    )
    
    # =====================================================
    # Tracker Dashboard - RE Selection and Drill-Down
    # =====================================================
    
    # Populate Reporting Effort dropdown with Study/DB/RE format
    observe({
      if (length(rv$all_trackers) == 0) return()
      
      # Get unique reporting efforts with full context
      re_data <- list()
      seen_ids <- c()
      
      for (t in rv$all_trackers) {
        re_id <- t$reporting_effort_id
        if (!is.null(re_id) && !(re_id %in% seen_ids)) {
          seen_ids <- c(seen_ids, re_id)
          re_data[[length(re_data) + 1]] <- list(
            id = re_id,
            re_label = t$reporting_effort_label %||% paste0("RE ", re_id),
            study_label = t$study_label %||% paste0("Study ", t$study_id),
            db_label = t$database_release_label %||% ""
          )
        }
      }
      
      # Create choices with combined label: "RE_label (Study, DB)"
      choices <- c("Select a Reporting Effort" = "")
      for (r in re_data) {
        label <- paste0(r$re_label, " (", r$study_label)
        if (r$db_label != "") {
          label <- paste0(label, ", ", r$db_label)
        }
        label <- paste0(label, ")")
        choices[label] <- as.character(r$id)
      }
      
      updateSelectInput(session, "tracker_dashboard_re_selector", choices = choices, selected = "")
    })
    
    # Refresh button - reload tracker data
    observeEvent(input$tracker_dashboard_refresh, {
      cat("Tracker Dashboard: Refresh triggered\n")
      # Trigger a full data reload
      load_all_trackers()
    })
    
    # Summary info for selected RE
    output$tracker_dashboard_summary_info <- renderUI({
      re_id <- input$tracker_dashboard_re_selector
      if (is.null(re_id) || re_id == "") {
        return(div(
          class = "text-muted",
          icon("info-circle"), " Select a reporting effort to view details"
        ))
      }
      
      trackers <- filtered_trackers()
      total <- length(trackers)
      completed <- sum(sapply(trackers, function(t) (t$production_status %||% "") == "completed"))
      pct <- if (total > 0) round((completed / total) * 100) else 0
      
      div(
        class = "d-flex gap-3 align-items-center",
        div(
          class = "badge bg-primary fs-6",
          paste0(total, " items")
        ),
        div(
          class = "badge bg-success fs-6",
          paste0(pct, "% complete")
        )
      )
    })
    
    # Filtered trackers reactive - filter by selected RE
    filtered_trackers <- reactive({
      trackers <- rv$all_trackers
      if (length(trackers) == 0) return(list())
      
      re_id <- input$tracker_dashboard_re_selector
      
      # If no RE selected, return empty (show prompt to select)
      if (is.null(re_id) || re_id == "") {
        return(list())
      }
      
      # Filter by RE
      trackers <- trackers[sapply(trackers, function(t) {
        !is.null(t$reporting_effort_id) && as.character(t$reporting_effort_id) == re_id
      })]
      
      trackers
    })
    
    # Filtered summary metrics
    output$filtered_total <- renderText({
      as.character(length(filtered_trackers()))
    })
    
    output$filtered_completed <- renderText({
      trackers <- filtered_trackers()
      if (length(trackers) == 0) return("0")
      completed <- sum(sapply(trackers, function(t) {
        (t$production_status %||% "") == "completed"
      }))
      as.character(completed)
    })

    output$filtered_in_progress <- renderText({
      trackers <- filtered_trackers()
      if (length(trackers) == 0) return("0")
      in_prog <- sum(sapply(trackers, function(t) {
        (t$production_status %||% "") == "in_progress"
      }))
      as.character(in_prog)
    })

    output$filtered_overdue <- renderText({
      trackers <- filtered_trackers()
      if (length(trackers) == 0) return("0")
      today <- Sys.Date()
      overdue <- sum(sapply(trackers, function(t) {
        if (is.null(t$due_date) || t$due_date == "") return(FALSE)
        due_date <- tryCatch(as.Date(t$due_date), error = function(e) NULL)
        if (is.null(due_date)) return(FALSE)
        due_date < today && (t$production_status %||% "") != "completed"
      }))
      as.character(overdue)
    })
    
    # Helper to categorize task type
    get_task_category <- function(item_type, item_subtype) {
      item_type <- item_type %||% ""
      item_subtype <- item_subtype %||% ""
      
      if (toupper(item_subtype) == "SDTM") {
        return("SDTM")
      } else if (toupper(item_subtype) == "ADAM") {
        return("ADaM")
      } else if (toupper(item_type) == "TLF") {
        # Further categorize TLF by subtype
        subtype <- toupper(item_subtype)
        if (subtype == "TABLE") return("Table")
        if (subtype == "LISTING") return("Listing")
        if (subtype == "FIGURE") return("Figure")
        return("TLF")
      } else if (toupper(item_type) == "DATASET") {
        return("Dataset")
      }
      return("Other")
    }
    
    # Task Type Breakdown Chart
    output$task_type_breakdown_chart <- plotly::renderPlotly({
      trackers <- filtered_trackers()
      
      if (length(trackers) == 0) {
        return(plotly::plot_ly() %>%
                 plotly::add_annotations(
                   text = "No data available",
                   x = 0.5, y = 0.5,
                   xref = "paper", yref = "paper",
                   showarrow = FALSE,
                   font = list(size = 14, color = "#6c757d")
                 ) %>%
                 plotly::layout(
                   xaxis = list(visible = FALSE),
                   yaxis = list(visible = FALSE)
                 ) %>%
                 plotly::config(displayModeBar = FALSE))
      }
      
      # Aggregate by task category and status
      task_data <- list()
      
      for (t in trackers) {
        category <- get_task_category(t$item_type, t$item_subtype)
        status <- t$production_status %||% "not_started"
        
        key <- category
        if (is.null(task_data[[key]])) {
          task_data[[key]] <- list(
            category = category,
            not_started = 0,
            in_progress = 0,
            completed = 0,
            on_hold = 0
          )
        }
        
        if (status == "not_started") {
          task_data[[key]]$not_started <- task_data[[key]]$not_started + 1
        } else if (status == "in_progress") {
          task_data[[key]]$in_progress <- task_data[[key]]$in_progress + 1
        } else if (status == "completed") {
          task_data[[key]]$completed <- task_data[[key]]$completed + 1
        } else if (status == "on_hold") {
          task_data[[key]]$on_hold <- task_data[[key]]$on_hold + 1
        }
      }
      
      # Convert to data frame
      df <- data.frame(
        category = character(0),
        not_started = numeric(0),
        in_progress = numeric(0),
        completed = numeric(0),
        on_hold = numeric(0),
        stringsAsFactors = FALSE
      )
      
      # Define order for categories
      category_order <- c("SDTM", "ADaM", "Table", "Listing", "Figure", "TLF", "Dataset", "Other")
      
      for (cat in category_order) {
        if (!is.null(task_data[[cat]])) {
          df <- rbind(df, data.frame(
            category = task_data[[cat]]$category,
            not_started = task_data[[cat]]$not_started,
            in_progress = task_data[[cat]]$in_progress,
            completed = task_data[[cat]]$completed,
            on_hold = task_data[[cat]]$on_hold,
            stringsAsFactors = FALSE
          ))
        }
      }
      
      if (nrow(df) == 0) {
        return(plotly::plot_ly() %>%
                 plotly::add_annotations(
                   text = "No task categories found",
                   x = 0.5, y = 0.5,
                   xref = "paper", yref = "paper",
                   showarrow = FALSE,
                   font = list(size = 14, color = "#6c757d")
                 ) %>%
                 plotly::config(displayModeBar = FALSE))
      }
      
      # Create stacked bar chart
      plotly::plot_ly(df, x = ~category) %>%
        plotly::add_bars(y = ~completed, name = "Completed", marker = list(color = status_colors$completed)) %>%
        plotly::add_bars(y = ~in_progress, name = "In Progress", marker = list(color = status_colors$in_progress)) %>%
        plotly::add_bars(y = ~not_started, name = "Not Started", marker = list(color = status_colors$not_started)) %>%
        plotly::add_bars(y = ~on_hold, name = "On Hold", marker = list(color = status_colors$on_hold)) %>%
        plotly::layout(
          barmode = "stack",
          xaxis = list(title = "", categoryorder = "array", categoryarray = df$category),
          yaxis = list(title = "Count"),
          legend = list(orientation = "h", y = 1.15),
          margin = list(t = 40, b = 40, l = 40, r = 20),
          hovermode = "closest"
        ) %>%
        plotly::config(displayModeBar = FALSE)
    })
    
    # Task Type Summary Table
    output$task_type_summary_table <- DT::renderDataTable({
      trackers <- filtered_trackers()
      
      if (length(trackers) == 0) {
        return(DT::datatable(
          data.frame(Message = "No data available"),
          options = list(dom = 't'),
          rownames = FALSE
        ))
      }
      
      # Aggregate by task category
      task_data <- list()
      today <- Sys.Date()
      
      for (t in trackers) {
        category <- get_task_category(t$item_type, t$item_subtype)
        status <- t$production_status %||% "not_started"
        
        if (is.null(task_data[[category]])) {
          task_data[[category]] <- list(
            total = 0,
            not_started = 0,
            in_progress = 0,
            completed = 0,
            overdue = 0
          )
        }
        
        task_data[[category]]$total <- task_data[[category]]$total + 1
        
        if (status == "not_started") {
          task_data[[category]]$not_started <- task_data[[category]]$not_started + 1
        } else if (status == "in_progress") {
          task_data[[category]]$in_progress <- task_data[[category]]$in_progress + 1
        } else if (status == "completed") {
          task_data[[category]]$completed <- task_data[[category]]$completed + 1
        }
        
        # Check overdue
        if (!is.null(t$due_date) && t$due_date != "") {
          due_date <- tryCatch(as.Date(t$due_date), error = function(e) NULL)
          if (!is.null(due_date) && due_date < today && status != "completed") {
            task_data[[category]]$overdue <- task_data[[category]]$overdue + 1
          }
        }
      }
      
      # Convert to data frame
      df <- data.frame(
        Task_Type = character(0),
        Total = integer(0),
        Not_Started = integer(0),
        In_Progress = integer(0),
        Completed = integer(0),
        Overdue = integer(0),
        Completion_Pct = character(0),
        stringsAsFactors = FALSE
      )
      
      category_order <- c("SDTM", "ADaM", "Table", "Listing", "Figure", "TLF", "Dataset", "Other")
      
      for (cat in category_order) {
        if (!is.null(task_data[[cat]])) {
          d <- task_data[[cat]]
          completion_pct <- if (d$total > 0) sprintf("%.0f%%", (d$completed / d$total) * 100) else "0%"
          
          df <- rbind(df, data.frame(
            Task_Type = cat,
            Total = d$total,
            Not_Started = d$not_started,
            In_Progress = d$in_progress,
            Completed = d$completed,
            Overdue = d$overdue,
            Completion_Pct = completion_pct,
            stringsAsFactors = FALSE
          ))
        }
      }
      
      # Format overdue with badge
      df$Overdue <- sapply(df$Overdue, function(o) {
        if (o > 0) {
          sprintf('<span class="badge bg-danger">%d</span>', o)
        } else {
          '<span class="badge bg-success">0</span>'
        }
      })
      
      # Rename columns
      colnames(df) <- c("Task Type", "Total", "Not Started", "In Progress", "Completed", "Overdue", "Completion %")
      
      DT::datatable(
        df,
        options = list(
          dom = 't',
          pageLength = 10,
          ordering = FALSE,
          columnDefs = list(
            list(className = 'text-center', targets = c(1, 2, 3, 4, 5, 6))
          )
        ),
        escape = FALSE,
        rownames = FALSE
      )
    }, server = FALSE)
    
    # =====================================================
    # Tracker Dashboard - Programmer Workload Table
    # =====================================================
    
    output$programmer_workload_table <- DT::renderDataTable({
      trackers <- filtered_trackers()
      
      if (length(trackers) == 0) {
        return(DT::datatable(
          data.frame(Message = "Select a reporting effort to view programmer workload"),
          options = list(dom = 't'),
          rownames = FALSE
        ))
      }
      
      # Build user lookup
      user_lookup <- list()
      for (u in rv$users) {
        user_lookup[[as.character(u$id)]] <- u$username
      }
      
      # Aggregate by programmer
      workload <- list()
      today <- Sys.Date()
      
      for (t in trackers) {
        # Production programmer
        prod_id <- t$production_programmer_id
        if (!is.null(prod_id)) {
          key <- paste0("prod_", prod_id)
          if (is.null(workload[[key]])) {
            workload[[key]] <- list(
              user_id = prod_id,
              username = user_lookup[[as.character(prod_id)]] %||% paste0("User ", prod_id),
              role = "Production",
              total = 0,
              not_started = 0,
              in_progress = 0,
              completed = 0,
              overdue = 0
            )
          }
          workload[[key]]$total <- workload[[key]]$total + 1
          status <- t$production_status %||% "not_started"
          if (status == "not_started") workload[[key]]$not_started <- workload[[key]]$not_started + 1
          if (status == "in_progress") workload[[key]]$in_progress <- workload[[key]]$in_progress + 1
          if (status == "completed") workload[[key]]$completed <- workload[[key]]$completed + 1
          
          # Overdue check
          if (!is.null(t$due_date) && t$due_date != "" && status != "completed") {
            due_date <- tryCatch(as.Date(t$due_date), error = function(e) NULL)
            if (!is.null(due_date) && due_date < today) {
              workload[[key]]$overdue <- workload[[key]]$overdue + 1
            }
          }
        }
        
        # QC programmer
        qc_id <- t$qc_programmer_id
        if (!is.null(qc_id)) {
          key <- paste0("qc_", qc_id)
          if (is.null(workload[[key]])) {
            workload[[key]] <- list(
              user_id = qc_id,
              username = user_lookup[[as.character(qc_id)]] %||% paste0("User ", qc_id),
              role = "QC",
              total = 0,
              not_started = 0,
              in_progress = 0,
              completed = 0,
              overdue = 0
            )
          }
          workload[[key]]$total <- workload[[key]]$total + 1
          status <- t$qc_status %||% "not_started"
          if (status == "not_started") workload[[key]]$not_started <- workload[[key]]$not_started + 1
          if (status == "in_progress") workload[[key]]$in_progress <- workload[[key]]$in_progress + 1
          if (status == "completed") workload[[key]]$completed <- workload[[key]]$completed + 1
        }
      }
      
      # Convert to data frame
      df <- data.frame(
        Programmer = character(0),
        Role = character(0),
        Total = integer(0),
        Not_Started = integer(0),
        In_Progress = integer(0),
        Completed = integer(0),
        Overdue = integer(0),
        Completion_Pct = character(0),
        stringsAsFactors = FALSE
      )
      
      for (key in names(workload)) {
        w <- workload[[key]]
        completion_pct <- if (w$total > 0) sprintf("%.0f%%", (w$completed / w$total) * 100) else "0%"
        df <- rbind(df, data.frame(
          Programmer = w$username,
          Role = w$role,
          Total = w$total,
          Not_Started = w$not_started,
          In_Progress = w$in_progress,
          Completed = w$completed,
          Overdue = w$overdue,
          Completion_Pct = completion_pct,
          stringsAsFactors = FALSE
        ))
      }
      
      # Sort by role then total
      df <- df[order(df$Role, -df$Total), ]
      
      # Format overdue with badge
      df$Overdue <- sapply(df$Overdue, function(o) {
        if (o > 0) {
          sprintf('<span class="badge bg-danger">%d</span>', o)
        } else {
          '<span class="badge bg-success">0</span>'
        }
      })
      
      # Rename columns
      colnames(df) <- c("Programmer", "Role", "Total", "Not Started", "In Progress", "Completed", "Overdue", "Completion %")
      
      DT::datatable(
        df,
        options = list(
          dom = 'frtip',
          pageLength = 10,
          order = list(list(1, 'asc'), list(2, 'desc')),
          columnDefs = list(
            list(className = 'text-center', targets = c(2, 3, 4, 5, 6, 7))
          )
        ),
        escape = FALSE,
        rownames = FALSE
      )
    }, server = FALSE)
    
    # =====================================================
    # Tracker Dashboard - Aggregate Metrics
    # =====================================================
    
    # Total Studies - count unique studies from trackers data
    output$total_studies <- renderText({
      if (length(rv$all_trackers) == 0) return("0")
      
      # Get unique study IDs from trackers
      study_ids <- unique(sapply(rv$all_trackers, function(t) t$study_id))
      study_ids <- study_ids[!is.na(study_ids) & !is.null(study_ids)]
      as.character(length(study_ids))
    })
    
    # Active Trackers - count REs where NOT all items are completed (in production)
    output$total_trackers <- renderText({
      if (length(rv$all_trackers) == 0) return("0")
      
      # Group by RE and check if any item is not completed
      re_status <- list()
      for (t in rv$all_trackers) {
        re_id <- t$reporting_effort_id
        if (!is.null(re_id)) {
          key <- as.character(re_id)
          if (is.null(re_status[[key]])) {
            re_status[[key]] <- list(has_incomplete = FALSE)
          }
          # Mark as active if any production item is not completed
          prod_status <- t$production_status %||% "not_started"
          if (prod_status != "completed") {
            re_status[[key]]$has_incomplete <- TRUE
          }
        }
      }
      
      # Count REs with incomplete items
      active_count <- sum(sapply(re_status, function(r) r$has_incomplete))
      as.character(active_count)
    })
    
    # Total Items
    output$total_items <- renderText({
      as.character(length(rv$all_trackers))
    })
    
    # Completion Rate
    output$completion_rate <- renderText({
      if (length(rv$all_trackers) == 0) return("0%")
      
      completed <- sum(sapply(rv$all_trackers, function(t) {
        t$production_status == "completed" && (t$qc_status == "completed" || is.null(t$qc_programmer_id))
      }))
      
      rate <- round((completed / length(rv$all_trackers)) * 100)
      paste0(rate, "%")
    })
    
    # Production Status Distribution Pie Chart (for selected RE)
    output$lead_production_status_chart <- plotly::renderPlotly({
      trackers <- filtered_trackers()
      
      if (length(trackers) == 0) {
        return(plotly::plot_ly() %>%
                 plotly::add_annotations(
                   text = "Select a reporting effort",
                   x = 0.5, y = 0.5,
                   xref = "paper", yref = "paper",
                   showarrow = FALSE,
                   font = list(size = 14, color = "#6c757d")
                 ) %>%
                 plotly::layout(
                   xaxis = list(visible = FALSE),
                   yaxis = list(visible = FALSE)
                 ) %>%
                 plotly::config(displayModeBar = FALSE))
      }
      
      # Count production statuses
      status_counts <- list(
        not_started = 0,
        in_progress = 0,
        completed = 0,
        on_hold = 0
      )
      
      for (tracker in trackers) {
        status <- tracker$production_status %||% "not_started"
        if (status %in% names(status_counts)) {
          status_counts[[status]] <- status_counts[[status]] + 1
        }
      }
      
      # Create data frame for plotting
      status_df <- data.frame(
        status = c("Not Started", "In Progress", "Completed", "On Hold"),
        count = c(status_counts$not_started, status_counts$in_progress, 
                  status_counts$completed, status_counts$on_hold),
        color = c(status_colors$not_started, status_colors$in_progress,
                  status_colors$completed, status_colors$on_hold),
        stringsAsFactors = FALSE
      )
      
      # Filter out zero values for cleaner chart
      status_df <- status_df[status_df$count > 0, ]
      
      if (nrow(status_df) == 0) {
        return(plotly::plot_ly() %>%
                 plotly::add_annotations(
                   text = "No items found",
                   x = 0.5, y = 0.5,
                   xref = "paper", yref = "paper",
                   showarrow = FALSE,
                   font = list(size = 16, color = "#6c757d")
                 ) %>%
                 plotly::layout(
                   xaxis = list(visible = FALSE),
                   yaxis = list(visible = FALSE)
                 ))
      }
      
      plotly::plot_ly(
        data = status_df,
        labels = ~status,
        values = ~count,
        type = "pie",
        marker = list(colors = status_df$color),
        textinfo = "label+percent",
        textposition = "inside",
        hovertemplate = "<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"
      ) %>%
        plotly::layout(
          showlegend = TRUE,
          legend = list(orientation = "h", y = -0.1),
          margin = list(t = 20, b = 40, l = 20, r = 20)
        ) %>%
        plotly::config(displayModeBar = FALSE)
    })
    
    # QC Status Distribution Pie Chart (for selected RE)
    output$lead_qc_status_chart <- plotly::renderPlotly({
      trackers <- filtered_trackers()
      
      if (length(trackers) == 0) {
        return(plotly::plot_ly() %>%
                 plotly::add_annotations(
                   text = "Select a reporting effort",
                   x = 0.5, y = 0.5,
                   xref = "paper", yref = "paper",
                   showarrow = FALSE,
                   font = list(size = 14, color = "#6c757d")
                 ) %>%
                 plotly::layout(
                   xaxis = list(visible = FALSE),
                   yaxis = list(visible = FALSE)
                 ) %>%
                 plotly::config(displayModeBar = FALSE))
      }
      
      # Count QC statuses
      status_counts <- list(
        not_started = 0,
        in_progress = 0,
        completed = 0,
        failed = 0
      )
      
      for (tracker in trackers) {
        status <- tracker$qc_status %||% "not_started"
        if (status %in% names(status_counts)) {
          status_counts[[status]] <- status_counts[[status]] + 1
        }
      }
      
      # Create data frame for plotting
      status_df <- data.frame(
        status = c("Not Started", "In Progress", "Completed", "Failed"),
        count = c(status_counts$not_started, status_counts$in_progress, 
                  status_counts$completed, status_counts$failed),
        color = c(status_colors$not_started, status_colors$in_progress,
                  status_colors$completed, status_colors$failed),
        stringsAsFactors = FALSE
      )
      
      # Filter out zero values for cleaner chart
      status_df <- status_df[status_df$count > 0, ]
      
      if (nrow(status_df) == 0) {
        return(plotly::plot_ly() %>%
                 plotly::add_annotations(
                   text = "No items found",
                   x = 0.5, y = 0.5,
                   xref = "paper", yref = "paper",
                   showarrow = FALSE,
                   font = list(size = 16, color = "#6c757d")
                 ) %>%
                 plotly::layout(
                   xaxis = list(visible = FALSE),
                   yaxis = list(visible = FALSE)
                 ))
      }
      
      plotly::plot_ly(
        data = status_df,
        labels = ~status,
        values = ~count,
        type = "pie",
        marker = list(colors = status_df$color),
        textinfo = "label+percent",
        textposition = "inside",
        hovertemplate = "<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"
      ) %>%
        plotly::layout(
          showlegend = TRUE,
          legend = list(orientation = "h", y = -0.1),
          margin = list(t = 20, b = 40, l = 20, r = 20)
        ) %>%
        plotly::config(displayModeBar = FALSE)
    })
    
    # Study Breakdown Stacked Bar Chart
    output$study_breakdown_chart <- plotly::renderPlotly({
      if (length(rv$all_trackers) == 0 || length(rv$studies) == 0) {
        return(plotly::plot_ly() %>%
                 plotly::add_annotations(
                   text = "No data available",
                   x = 0.5, y = 0.5,
                   xref = "paper", yref = "paper",
                   showarrow = FALSE,
                   font = list(size = 16, color = "#6c757d")
                 ) %>%
                 plotly::layout(
                   xaxis = list(visible = FALSE),
                   yaxis = list(visible = FALSE)
                 ))
      }
      
      # Build a lookup of study_id to study_label
      study_lookup <- list()
      for (study in rv$studies) {
        study_lookup[[as.character(study$id)]] <- study$study_label %||% paste0("Study ", study$id)
      }
      
      # Aggregate tracker counts by study and production status
      study_status_data <- list()
      
      for (tracker in rv$all_trackers) {
        # Get study info - try multiple paths
        study_id <- tracker$study_id
        study_label <- NULL
        
        if (!is.null(study_id)) {
          study_label <- study_lookup[[as.character(study_id)]]
        }
        
        if (is.null(study_label)) {
          study_label <- tracker$study_label %||% "Unknown Study"
        }
        
        status <- tracker$production_status %||% "not_started"
        
        # Initialize study if not exists
        if (is.null(study_status_data[[study_label]])) {
          study_status_data[[study_label]] <- list(
            not_started = 0,
            in_progress = 0,
            completed = 0,
            on_hold = 0
          )
        }
        
        # Increment counter
        if (status %in% names(study_status_data[[study_label]])) {
          study_status_data[[study_label]][[status]] <- 
            study_status_data[[study_label]][[status]] + 1
        }
      }
      
      # Convert to data frames for plotting
      studies_list <- names(study_status_data)
      if (length(studies_list) == 0) {
        return(plotly::plot_ly() %>%
                 plotly::add_annotations(
                   text = "No study data available",
                   x = 0.5, y = 0.5,
                   xref = "paper", yref = "paper",
                   showarrow = FALSE,
                   font = list(size = 16, color = "#6c757d")
                 ))
      }
      
      # Sort studies by total items (descending)
      study_totals <- sapply(studies_list, function(s) {
        sum(unlist(study_status_data[[s]]))
      })
      studies_list <- studies_list[order(-study_totals)]
      
      # Take top 15 studies if there are many
      if (length(studies_list) > 15) {
        studies_list <- studies_list[1:15]
      }
      
      not_started <- sapply(studies_list, function(s) study_status_data[[s]]$not_started)
      in_progress <- sapply(studies_list, function(s) study_status_data[[s]]$in_progress)
      completed <- sapply(studies_list, function(s) study_status_data[[s]]$completed)
      on_hold <- sapply(studies_list, function(s) study_status_data[[s]]$on_hold)
      
      plotly::plot_ly(x = studies_list, y = completed, type = "bar", name = "Completed",
                      marker = list(color = status_colors$completed),
                      hovertemplate = "<b>%{x}</b><br>Completed: %{y}<extra></extra>") %>%
        plotly::add_trace(y = in_progress, name = "In Progress",
                          marker = list(color = status_colors$in_progress),
                          hovertemplate = "<b>%{x}</b><br>In Progress: %{y}<extra></extra>") %>%
        plotly::add_trace(y = not_started, name = "Not Started",
                          marker = list(color = status_colors$not_started),
                          hovertemplate = "<b>%{x}</b><br>Not Started: %{y}<extra></extra>") %>%
        plotly::add_trace(y = on_hold, name = "On Hold",
                          marker = list(color = status_colors$on_hold),
                          hovertemplate = "<b>%{x}</b><br>On Hold: %{y}<extra></extra>") %>%
        plotly::layout(
          barmode = "stack",
          xaxis = list(title = "", tickangle = -45, tickfont = list(size = 10)),
          yaxis = list(title = "Number of Items"),
          legend = list(orientation = "h", y = 1.1),
          margin = list(t = 50, b = 100, l = 50, r = 20),
          hovermode = "closest"
        ) %>%
        plotly::config(displayModeBar = FALSE)
    })
    
    # Reporting Effort Breakdown Chart
    output$reporting_effort_breakdown_chart <- plotly::renderPlotly({
      if (length(rv$all_trackers) == 0) {
        return(plotly::plot_ly() %>%
                 plotly::add_annotations(
                   text = "No data available",
                   x = 0.5, y = 0.5,
                   xref = "paper", yref = "paper",
                   showarrow = FALSE,
                   font = list(size = 16, color = "#6c757d")
                 ) %>%
                 plotly::layout(
                   xaxis = list(visible = FALSE),
                   yaxis = list(visible = FALSE)
                 ))
      }
      
      # Build a lookup of study_id to study_label
      study_lookup <- list()
      for (study in rv$studies) {
        study_lookup[[as.character(study$id)]] <- study$study_label %||% paste0("Study ", study$id)
      }
      
      # Aggregate tracker counts by reporting effort and status
      re_data <- list()
      
      for (tracker in rv$all_trackers) {
        # Get study and RE info
        study_id <- tracker$study_id
        study_label <- NULL
        
        if (!is.null(study_id)) {
          study_label <- study_lookup[[as.character(study_id)]]
        }
        if (is.null(study_label)) {
          study_label <- tracker$study_label %||% "Unknown"
        }
        
        re_label <- tracker$reporting_effort_label %||% 
                    tracker$database_release_label %||% 
                    paste0("RE ", tracker$reporting_effort_id %||% "?")
        
        # Create combined label for x-axis
        combined_label <- paste0(study_label, "\n", re_label)
        
        status <- tracker$production_status %||% "not_started"
        
        # Initialize RE if not exists
        if (is.null(re_data[[combined_label]])) {
          re_data[[combined_label]] <- list(
            study = study_label,
            re = re_label,
            not_started = 0,
            in_progress = 0,
            completed = 0,
            on_hold = 0
          )
        }
        
        # Increment counter
        if (status %in% c("not_started", "in_progress", "completed", "on_hold")) {
          re_data[[combined_label]][[status]] <- 
            re_data[[combined_label]][[status]] + 1
        }
      }
      
      # Convert to data frames for plotting
      re_list <- names(re_data)
      if (length(re_list) == 0) {
        return(plotly::plot_ly() %>%
                 plotly::add_annotations(
                   text = "No reporting effort data available",
                   x = 0.5, y = 0.5,
                   xref = "paper", yref = "paper",
                   showarrow = FALSE,
                   font = list(size = 16, color = "#6c757d")
                 ))
      }
      
      # Sort by study then by total items
      re_totals <- sapply(re_list, function(r) {
        sum(re_data[[r]]$not_started, re_data[[r]]$in_progress, 
            re_data[[r]]$completed, re_data[[r]]$on_hold)
      })
      re_studies <- sapply(re_list, function(r) re_data[[r]]$study)
      
      # Sort by study name first, then by total within study
      sort_order <- order(re_studies, -re_totals)
      re_list <- re_list[sort_order]
      
      # Take top 20 if there are many
      if (length(re_list) > 20) {
        re_list <- re_list[1:20]
      }
      
      not_started <- sapply(re_list, function(r) re_data[[r]]$not_started)
      in_progress <- sapply(re_list, function(r) re_data[[r]]$in_progress)
      completed <- sapply(re_list, function(r) re_data[[r]]$completed)
      on_hold <- sapply(re_list, function(r) re_data[[r]]$on_hold)
      
      # Create short labels for x-axis (just RE name)
      short_labels <- sapply(re_list, function(r) re_data[[r]]$re)
      
      # Create custom hover text with full info
      hover_text <- sapply(re_list, function(r) {
        paste0("Study: ", re_data[[r]]$study, "<br>RE: ", re_data[[r]]$re)
      })
      
      plotly::plot_ly(x = short_labels, y = completed, type = "bar", name = "Completed",
                      marker = list(color = status_colors$completed),
                      text = hover_text,
                      hovertemplate = "%{text}<br>Completed: %{y}<extra></extra>") %>%
        plotly::add_trace(y = in_progress, name = "In Progress",
                          marker = list(color = status_colors$in_progress),
                          text = hover_text,
                          hovertemplate = "%{text}<br>In Progress: %{y}<extra></extra>") %>%
        plotly::add_trace(y = not_started, name = "Not Started",
                          marker = list(color = status_colors$not_started),
                          text = hover_text,
                          hovertemplate = "%{text}<br>Not Started: %{y}<extra></extra>") %>%
        plotly::add_trace(y = on_hold, name = "On Hold",
                          marker = list(color = status_colors$on_hold),
                          text = hover_text,
                          hovertemplate = "%{text}<br>On Hold: %{y}<extra></extra>") %>%
        plotly::layout(
          barmode = "stack",
          xaxis = list(title = "", tickangle = -45, tickfont = list(size = 9)),
          yaxis = list(title = "Number of Items"),
          legend = list(orientation = "h", y = 1.08),
          margin = list(t = 50, b = 120, l = 50, r = 20),
          hovermode = "closest"
        ) %>%
        plotly::config(displayModeBar = FALSE)
    })
    
    # Workload by Study/Reporting Effort Table
    output$team_workload_table <- DT::renderDataTable({
      if (length(rv$all_trackers) == 0) {
        return(DT::datatable(
          data.frame(Message = "No tracker data available"),
          options = list(dom = 't'),
          rownames = FALSE
        ))
      }
      
      # Aggregate data by Study and Reporting Effort
      study_re_data <- list()
      today <- Sys.Date()
      
      for (tracker in rv$all_trackers) {
        study_label <- tracker$study_label %||% "Unknown Study"
        re_label <- tracker$reporting_effort_label %||% "Unknown RE"
        key <- paste0(study_label, "|||", re_label)
        
        # Initialize if not exists
        if (is.null(study_re_data[[key]])) {
          study_re_data[[key]] <- list(
            study = study_label,
            reporting_effort = re_label,
            total_items = 0,
            not_started = 0,
            in_progress = 0,
            completed = 0,
            overdue = 0
          )
        }
        
        # Count items
        study_re_data[[key]]$total_items <- study_re_data[[key]]$total_items + 1
        
        # Production status counts
        prod_status <- tracker$production_status %||% "not_started"
        if (prod_status == "not_started") {
          study_re_data[[key]]$not_started <- study_re_data[[key]]$not_started + 1
        } else if (prod_status == "in_progress") {
          study_re_data[[key]]$in_progress <- study_re_data[[key]]$in_progress + 1
        } else if (prod_status == "completed") {
          study_re_data[[key]]$completed <- study_re_data[[key]]$completed + 1
        }
        
        # Overdue check
        if (!is.null(tracker$due_date) && tracker$due_date != "") {
          due_date <- tryCatch(as.Date(tracker$due_date), error = function(e) NULL)
          if (!is.null(due_date) && due_date < today && prod_status != "completed") {
            study_re_data[[key]]$overdue <- study_re_data[[key]]$overdue + 1
          }
        }
      }
      
      # Convert to data frame
      workload_df <- data.frame(
        Study = character(0),
        Reporting_Effort = character(0),
        Total = integer(0),
        Not_Started = integer(0),
        In_Progress = integer(0),
        Completed = integer(0),
        Overdue = integer(0),
        stringsAsFactors = FALSE
      )
      
      for (key in names(study_re_data)) {
        item <- study_re_data[[key]]
        workload_df <- rbind(workload_df, data.frame(
          Study = item$study,
          Reporting_Effort = item$reporting_effort,
          Total = item$total_items,
          Not_Started = item$not_started,
          In_Progress = item$in_progress,
          Completed = item$completed,
          Overdue = item$overdue,
          stringsAsFactors = FALSE
        ))
      }
      
      # Sort by Study, then by Total (descending)
      workload_df <- workload_df[order(workload_df$Study, -workload_df$Total), ]
      
      # Calculate completion percentage
      workload_df$Completion <- sprintf("%.0f%%", (workload_df$Completed / workload_df$Total) * 100)
      
      # Format overdue column with badge
      workload_df$Overdue <- sapply(workload_df$Overdue, function(o) {
        if (o > 0) {
          sprintf('<span class="badge bg-danger">%d</span>', o)
        } else {
          '<span class="badge bg-success">0</span>'
        }
      })
      
      # Rename columns for display
      colnames(workload_df) <- c("Study", "Reporting Effort", "Total", "Not Started", "In Progress", "Completed", "Overdue", "Completion %")
      
      DT::datatable(
        workload_df,
        options = list(
          dom = 'frtip',
          pageLength = 15,
          order = list(list(0, 'asc'), list(2, 'desc')),
          columnDefs = list(
            list(className = 'text-center', targets = c(2, 3, 4, 5, 6, 7))
          )
        ),
        escape = FALSE,
        rownames = FALSE
      )
    }, server = FALSE)
    
    # Overdue Items (for selected RE)
    output$system_overdue_list <- renderUI({
      trackers <- filtered_trackers()
      
      if (length(trackers) == 0) {
        return(div(class = "text-muted text-center py-3", icon("filter"), " Select a reporting effort"))
      }
      
      today <- Sys.Date()
      overdue_items <- list()
      
      for (tracker in trackers) {
        if (!is.null(tracker$due_date) && tracker$due_date != "") {
          due_date <- tryCatch(as.Date(tracker$due_date), error = function(e) NULL)
          if (!is.null(due_date) && due_date < today) {
            if (tracker$production_status != "completed") {
              item_code <- tracker$item_code %||% tracker$item$item_code %||% paste0("Item #", tracker$reporting_effort_item_id)
              
              # Get assigned programmer
              programmer <- "Unassigned"
              for (user in rv$users) {
                if (!is.null(tracker$production_programmer_id) && user$id == tracker$production_programmer_id) {
                  programmer <- user$username
                  break
                }
              }
              
              overdue_items[[length(overdue_items) + 1]] <- list(
                item = item_code,
                programmer = programmer,
                days_overdue = as.integer(today - due_date),
                due_date = due_date
              )
            }
          }
        }
      }
      
      if (length(overdue_items) == 0) {
        return(div(
          class = "text-center text-success py-3",
          icon("check-circle", class = "fa-2x mb-2"),
          p("No overdue items!")
        ))
      }
      
      # Sort by days overdue (most overdue first)
      overdue_items <- overdue_items[order(-sapply(overdue_items, function(x) x$days_overdue))]
      
      # Limit to 10
      if (length(overdue_items) > 10) {
        overdue_items <- overdue_items[1:10]
      }
      
      items <- lapply(overdue_items, function(item) {
        div(
          class = "deadline-item overdue",
          div(
            class = "flex-grow-1",
            div(class = "fw-semibold", item$item),
            div(class = "small text-muted", paste("Assigned to:", item$programmer))
          ),
          span(class = "badge bg-danger", paste(item$days_overdue, "days overdue"))
        )
      })
      
      tagList(items)
    })
    
    # Due Soon Items (for selected RE)
    output$system_due_soon_list <- renderUI({
      trackers <- filtered_trackers()
      
      if (length(trackers) == 0) {
        return(div(class = "text-muted text-center py-3", icon("filter"), " Select a reporting effort"))
      }
      
      today <- Sys.Date()
      week_ahead <- today + 7
      due_soon_items <- list()
      
      for (tracker in trackers) {
        if (!is.null(tracker$due_date) && tracker$due_date != "") {
          due_date <- tryCatch(as.Date(tracker$due_date), error = function(e) NULL)
          if (!is.null(due_date) && due_date >= today && due_date <= week_ahead) {
            if (tracker$production_status != "completed") {
              item_code <- tracker$item_code %||% tracker$item$item_code %||% paste0("Item #", tracker$reporting_effort_item_id)
              
              # Get assigned programmer
              programmer <- "Unassigned"
              for (user in rv$users) {
                if (!is.null(tracker$production_programmer_id) && user$id == tracker$production_programmer_id) {
                  programmer <- user$username
                  break
                }
              }
              
              due_soon_items[[length(due_soon_items) + 1]] <- list(
                item = item_code,
                programmer = programmer,
                days_until = as.integer(due_date - today),
                due_date = due_date
              )
            }
          }
        }
      }
      
      if (length(due_soon_items) == 0) {
        return(div(
          class = "text-center text-muted py-3",
          icon("calendar-check", class = "fa-2x mb-2"),
          p("No items due this week")
        ))
      }
      
      # Sort by due date (soonest first)
      due_soon_items <- due_soon_items[order(sapply(due_soon_items, function(x) x$days_until))]
      
      # Limit to 10
      if (length(due_soon_items) > 10) {
        due_soon_items <- due_soon_items[1:10]
      }
      
      items <- lapply(due_soon_items, function(item) {
        badge_text <- if (item$days_until == 0) {
          "Due Today"
        } else if (item$days_until == 1) {
          "Due Tomorrow"
        } else {
          paste(item$days_until, "days left")
        }
        
        div(
          class = "deadline-item due-soon",
          div(
            class = "flex-grow-1",
            div(class = "fw-semibold", item$item),
            div(class = "small text-muted", paste("Assigned to:", item$programmer))
          ),
          span(class = "badge bg-warning text-dark", badge_text)
        )
      })
      
      tagList(items)
    })
    
    # Last update time
    output$last_update <- renderText({
      if (!is.null(rv$last_refresh)) {
        format(rv$last_refresh, "%H:%M:%S")
      } else {
        "Never"
      }
    })

    # Quick Status Button Handler
    observeEvent(input$quick_status_click, {
      req(input$quick_status_click)

      data <- input$quick_status_click
      tracker_id <- as.integer(data$tracker_id)
      new_status <- data$new_status
      status_type <- data$status_type  # "production" or "qc"

      cat("Quick status update: tracker_id=", tracker_id,
          ", new_status=", new_status,
          ", type=", status_type, "\n")

      # Call API to update tracker status
      result <- update_tracker_status(tracker_id, new_status, status_type)

      if (!is.null(result) && is.null(result$error)) {
        show_success_notification(
          paste0("Status updated to '", gsub("_", " ", new_status), "'"),
          duration = 2000
        )
        # Refresh workload data
        if (!is.null(rv$current_user_id) && rv$current_user_id != "") {
          load_workload_data(rv$current_user_id)
        }
      } else {
        error_msg <- if (!is.null(result$error)) result$error else "Unknown error"
        show_error_notification(paste("Failed to update status:", error_msg))
      }
    })

    # WebSocket/CRUD refresh integration - completely skip to preserve user selection
    # The user dropdown doesn't need to be refreshed on every WebSocket event
    observeEvent(input$crud_refresh, {
      if (!is.null(input$crud_refresh)) {
        # Only refresh trackers and studies, not users
        load_studies()
        load_all_trackers()
        current_user <- isolate(rv$current_user_id)
        if (!is.null(current_user) && current_user != "") {
          load_workload_data(current_user)
        }
        rv$last_refresh <- Sys.time()
      }
    })

    observeEvent(input$websocket_event, {
      if (!is.null(input$websocket_event)) {
        # Only refresh trackers and studies, not users
        load_studies()
        load_all_trackers()
        current_user <- isolate(rv$current_user_id)
        if (!is.null(current_user) && current_user != "") {
          load_workload_data(current_user)
        }
        rv$last_refresh <- Sys.time()
      }
    })
    
    # Return module interface
    return(list(
      refresh = function() {
        load_dashboard_data()
      }
    ))
  })
}
