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
      
      # Build combined assignments dataframe
      assignments <- data.frame(
        ID = integer(0),
        Item = character(0),
        Type = character(0),
        Status = character(0),
        Priority = character(0),
        Due_Date = character(0),
        In_Production = character(0),
        stringsAsFactors = FALSE
      )
      
      today <- Sys.Date()
      
      # Add production assignments
      if (rv$assignment_filter %in% c("all", "production")) {
        prod_trackers <- rv$workload_data$production$trackers %||% list()
        for (tracker in prod_trackers) {
          # Get item info if available
          item_code <- tracker$item_code %||% tracker$item$item_code %||% paste0("Item #", tracker$reporting_effort_item_id)
          
          due_date_str <- ""
          deadline_class <- ""
          if (!is.null(tracker$due_date) && tracker$due_date != "") {
            due_date <- tryCatch(as.Date(tracker$due_date), error = function(e) NULL)
            if (!is.null(due_date)) {
              due_date_str <- format(due_date, "%Y-%m-%d")
              if (due_date < today && tracker$production_status != "completed") {
                deadline_class <- "overdue"
              } else if (due_date <= today + 7 && tracker$production_status != "completed") {
                deadline_class <- "due-soon"
              }
            }
          }
          
          assignments <- rbind(assignments, data.frame(
            ID = tracker$id %||% 0,
            Item = item_code,
            Type = "Production",
            Status = tracker$production_status %||% "not_started",
            Priority = tracker$priority %||% "medium",
            Due_Date = due_date_str,
            In_Production = if (isTRUE(tracker$in_production_flag) || isTRUE(tracker$in_production)) "Yes" else "No",
            stringsAsFactors = FALSE
          ))
        }
      }
      
      # Add QC assignments
      if (rv$assignment_filter %in% c("all", "qc")) {
        qc_trackers <- rv$workload_data$qc$trackers %||% list()
        for (tracker in qc_trackers) {
          item_code <- tracker$item_code %||% tracker$item$item_code %||% paste0("Item #", tracker$reporting_effort_item_id)
          
          due_date_str <- ""
          if (!is.null(tracker$due_date) && tracker$due_date != "") {
            due_date <- tryCatch(as.Date(tracker$due_date), error = function(e) NULL)
            if (!is.null(due_date)) {
              due_date_str <- format(due_date, "%Y-%m-%d")
            }
          }
          
          assignments <- rbind(assignments, data.frame(
            ID = tracker$id %||% 0,
            Item = item_code,
            Type = "QC",
            Status = tracker$qc_status %||% "not_started",
            Priority = tracker$priority %||% "medium",
            Due_Date = due_date_str,
            In_Production = if (isTRUE(tracker$in_production_flag) || isTRUE(tracker$in_production)) "Yes" else "No",
            stringsAsFactors = FALSE
          ))
        }
      }
      
      if (nrow(assignments) == 0) {
        return(DT::datatable(
          data.frame(Message = "No assignments found for this user"),
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
      colnames(assignments) <- c("ID", "Item", "Type", "Status", "Priority", "Due Date", "In Production")
      
      DT::datatable(
        assignments,
        options = list(
          dom = 'frtip',
          pageLength = 10,
          order = list(list(5, 'asc')),  # Sort by due date
          columnDefs = list(
            list(visible = FALSE, targets = 0),  # Hide ID column
            list(className = 'text-center', targets = c(2, 3, 4, 6))
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
    
    # Total Studies
    output$total_studies <- renderText({
      active_count <- sum(sapply(rv$studies, function(s) isTRUE(s$is_active)))
      as.character(active_count)
    })
    
    # Total Trackers
    output$total_trackers <- renderText({
      as.character(length(rv$all_trackers))
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
    
    # Team Workload Table
    output$team_workload_table <- DT::renderDataTable({
      if (length(rv$users) == 0) {
        return(DT::datatable(
          data.frame(Message = "No users found"),
          options = list(dom = 't'),
          rownames = FALSE
        ))
      }
      
      # Calculate workload for each user
      team_data <- data.frame(
        Username = character(0),
        Department = character(0),
        Production = integer(0),
        QC = integer(0),
        Total = integer(0),
        Overdue = integer(0),
        In_Progress = integer(0),
        stringsAsFactors = FALSE
      )
      
      for (user in rv$users) {
        prod_count <- 0
        qc_count <- 0
        overdue_count <- 0
        in_progress_count <- 0
        today <- Sys.Date()
        
        for (tracker in rv$all_trackers) {
          # Production assignments
          if (!is.null(tracker$production_programmer_id) && 
              tracker$production_programmer_id == user$id) {
            prod_count <- prod_count + 1
            
            if (tracker$production_status == "in_progress") {
              in_progress_count <- in_progress_count + 1
            }
            
            if (!is.null(tracker$due_date) && tracker$due_date != "") {
              due_date <- tryCatch(as.Date(tracker$due_date), error = function(e) NULL)
              if (!is.null(due_date) && due_date < today && tracker$production_status != "completed") {
                overdue_count <- overdue_count + 1
              }
            }
          }
          
          # QC assignments
          if (!is.null(tracker$qc_programmer_id) && 
              tracker$qc_programmer_id == user$id) {
            qc_count <- qc_count + 1
            
            if (tracker$qc_status == "in_progress") {
              in_progress_count <- in_progress_count + 1
            }
          }
        }
        
        total_count <- prod_count + qc_count
        
        # Only show users with assignments or all users
        team_data <- rbind(team_data, data.frame(
          Username = user$username,
          Department = user$department %||% "-",
          Production = prod_count,
          QC = qc_count,
          Total = total_count,
          Overdue = overdue_count,
          In_Progress = in_progress_count,
          stringsAsFactors = FALSE
        ))
      }
      
      # Sort by total (descending)
      team_data <- team_data[order(-team_data$Total), ]
      
      # Format overdue column
      team_data$Overdue <- sapply(team_data$Overdue, function(o) {
        if (o > 0) {
          sprintf('<span class="badge bg-danger">%d</span>', o)
        } else {
          '<span class="badge bg-success">0</span>'
        }
      })
      
      # Rename columns
      colnames(team_data) <- c("Username", "Department", "Production", "QC", "Total", "Overdue", "In Progress")
      
      DT::datatable(
        team_data,
        options = list(
          dom = 'frtip',
          pageLength = 15,
          order = list(list(4, 'desc')),
          columnDefs = list(
            list(className = 'text-center', targets = c(2, 3, 4, 5, 6))
          )
        ),
        escape = FALSE,
        rownames = FALSE
      )
    }, server = FALSE)
    
    # System-wide Overdue Items
    output$system_overdue_list <- renderUI({
      if (length(rv$all_trackers) == 0) {
        return(div(class = "text-muted", "No trackers available"))
      }
      
      today <- Sys.Date()
      overdue_items <- list()
      
      for (tracker in rv$all_trackers) {
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
    
    # System-wide Due Soon Items
    output$system_due_soon_list <- renderUI({
      if (length(rv$all_trackers) == 0) {
        return(div(class = "text-muted", "No trackers available"))
      }
      
      today <- Sys.Date()
      week_ahead <- today + 7
      due_soon_items <- list()
      
      for (tracker in rv$all_trackers) {
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
