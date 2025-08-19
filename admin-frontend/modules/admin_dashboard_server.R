# Admin Dashboard Server Module

admin_dashboard_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Reactive values for dashboard data
    rv <- reactiveValues(
      studies = list(),
      database_releases = list(),
      reporting_efforts = list(),
      trackers = list(),
      tracker_items = list(),
      users = list(),
      packages = list(),
      recent_activity = list(),
      last_refresh = NULL,
      metrics_history = list()
    )
    
    # Load all dashboard data
    load_dashboard_data <- function() {
      # Load studies
      studies_result <- get_studies()
      if (!is.null(studies_result) && !is.null(studies_result$error)) {
        rv$studies <- list()
      } else if (is.list(studies_result)) {
        rv$studies <- studies_result
      } else {
        rv$studies <- list()
      }
      
      # Load database releases
      releases_result <- get_database_releases()
      if (!is.null(releases_result) && !is.null(releases_result$error)) {
        rv$database_releases <- list()
      } else if (is.list(releases_result)) {
        rv$database_releases <- releases_result
      } else {
        rv$database_releases <- list()
      }
      
      # Load reporting efforts
      efforts_result <- get_reporting_efforts()
      if (!is.null(efforts_result) && !is.null(efforts_result$error)) {
        rv$reporting_efforts <- list()
      } else if (is.list(efforts_result)) {
        rv$reporting_efforts <- efforts_result
      } else {
        rv$reporting_efforts <- list()
      }
      
      # Load trackers
      trackers_result <- get_reporting_effort_tracker()
      if (!is.null(trackers_result) && !is.null(trackers_result$error)) {
        rv$trackers <- list()
      } else if (is.list(trackers_result)) {
        rv$trackers <- trackers_result
      } else {
        rv$trackers <- list()
      }
      
      # Load users
      users_result <- get_users()
      if (!is.null(users_result) && !is.null(users_result$error)) {
        rv$users <- list()
      } else if (is.list(users_result)) {
        rv$users <- users_result
      } else {
        rv$users <- list()
      }
      
      # Load packages
      packages_result <- get_packages()
      if (!is.null(packages_result) && !is.null(packages_result$error)) {
        rv$packages <- list()
      } else if (is.list(packages_result)) {
        rv$packages <- packages_result
      } else {
        rv$packages <- list()
      }
      
      # Calculate recent activity (last 7 days)
      rv$recent_activity <- calculate_recent_activity()
      
      # Update last refresh time
      rv$last_refresh <- Sys.time()
    }
    
    # Calculate recent activity from all entities
    calculate_recent_activity <- function() {
      activity <- list()
      
      # Add recent studies
      if (length(rv$studies) > 0) {
        recent_studies <- Filter(function(s) {
          if (!is.null(s$created_at)) {
            created_date <- as.POSIXct(s$created_at, format = "%Y-%m-%dT%H:%M:%S")
            difftime(Sys.time(), created_date, units = "days") < 7
          } else {
            FALSE
          }
        }, rv$studies)
        
        for (study in recent_studies) {
          activity <- append(activity, list(list(
            type = "study",
            action = "created",
            title = study$title,
            time = study$created_at,
            icon = "flask",
            color = "primary"
          )))
        }
      }
      
      # Add recent trackers
      if (length(rv$trackers) > 0) {
        recent_trackers <- Filter(function(t) {
          if (!is.null(t$created_at)) {
            created_date <- as.POSIXct(t$created_at, format = "%Y-%m-%dT%H:%M:%S")
            difftime(Sys.time(), created_date, units = "days") < 7
          } else {
            FALSE
          }
        }, rv$trackers)
        
        for (tracker in recent_trackers) {
          activity <- append(activity, list(list(
            type = "tracker",
            action = "created",
            title = paste("Tracker #", tracker$id),
            time = tracker$created_at,
            icon = "clipboard-check",
            color = "success"
          )))
        }
      }
      
      # Sort by time (most recent first)
      if (length(activity) > 0) {
        activity <- activity[order(sapply(activity, function(a) a$time), decreasing = TRUE)]
      }
      
      # Return top 10 activities
      if (length(activity) > 10) {
        activity <- activity[1:10]
      }
      
      return(activity)
    }
    
    # Calculate metrics
    calculate_metrics <- function() {
      # Safe counting with proper list handling
      total_studies <- if (is.list(rv$studies)) length(rv$studies) else 0
      active_studies <- if (is.list(rv$studies) && length(rv$studies) > 0) {
        sum(sapply(rv$studies, function(s) {
          if (is.list(s) && !is.null(s$is_active)) isTRUE(s$is_active) else FALSE
        }))
      } else 0
      
      total_trackers <- if (is.list(rv$trackers)) length(rv$trackers) else 0
      active_trackers <- if (is.list(rv$trackers) && length(rv$trackers) > 0) {
        sum(sapply(rv$trackers, function(t) {
          if (is.list(t) && !is.null(t$status)) {
            t$status %in% c("not_started", "in_progress")
          } else FALSE
        }))
      } else 0
      
      total_items <- if (is.list(rv$trackers) && length(rv$trackers) > 0) {
        sum(sapply(rv$trackers, function(t) {
          if (is.list(t) && !is.null(t$tracker_items) && is.list(t$tracker_items)) {
            length(t$tracker_items)
          } else 0
        }))
      } else 0
      
      completed_items <- if (is.list(rv$trackers) && length(rv$trackers) > 0) {
        sum(sapply(rv$trackers, function(t) {
          if (is.list(t) && !is.null(t$tracker_items) && is.list(t$tracker_items)) {
            sum(sapply(t$tracker_items, function(i) {
              if (is.list(i) && !is.null(i$status)) {
                i$status == "completed"
              } else FALSE
            }))
          } else 0
        }))
      } else 0
      
      total_users <- if (is.list(rv$users)) length(rv$users) else 0
      active_users <- if (is.list(rv$users) && length(rv$users) > 0) {
        sum(sapply(rv$users, function(u) {
          if (is.list(u) && !is.null(u$is_active)) isTRUE(u$is_active) else FALSE
        }))
      } else 0
      
      total_packages <- if (is.list(rv$packages)) length(rv$packages) else 0
      
      list(
        total_studies = total_studies,
        active_studies = active_studies,
        total_trackers = total_trackers,
        active_trackers = active_trackers,
        total_items = total_items,
        completed_items = completed_items,
        total_users = total_users,
        active_users = active_users,
        total_packages = total_packages
      )
    }
    
    # Initial load
    observe({
      load_dashboard_data()
    })
    
    # Auto-refresh every 30 seconds
    observe({
      invalidateLater(30000, session)
      load_dashboard_data()
    })
    
    # Manual refresh
    observeEvent(input$refresh_dashboard, {
      load_dashboard_data()
      showNotification(
        "Dashboard refreshed",
        type = "message",
        duration = 2
      )
    })
    
    # Render metrics
    output$total_studies <- renderText({
      metrics <- calculate_metrics()
      as.character(metrics$active_studies)
    })
    
    output$studies_change <- renderUI({
      # Calculate change from previous period (mock data for now)
      change <- sample(c(-5:10), 1)
      if (change > 0) {
        tags$span(
          class = "change-positive",
          icon("arrow-up"),
          paste0("+", change, " this week")
        )
      } else if (change < 0) {
        tags$span(
          class = "change-negative",
          icon("arrow-down"),
          paste0(abs(change), " this week")
        )
      } else {
        tags$span(
          class = "text-muted",
          "No change"
        )
      }
    })
    
    output$total_trackers <- renderText({
      metrics <- calculate_metrics()
      as.character(metrics$active_trackers)
    })
    
    output$trackers_change <- renderUI({
      change <- sample(c(-3:8), 1)
      if (change > 0) {
        tags$span(
          class = "change-positive",
          icon("arrow-up"),
          paste0("+", change, " this week")
        )
      } else if (change < 0) {
        tags$span(
          class = "change-negative",
          icon("arrow-down"),
          paste0(abs(change), " this week")
        )
      } else {
        tags$span(
          class = "text-muted",
          "No change"
        )
      }
    })
    
    output$total_items <- renderText({
      metrics <- calculate_metrics()
      as.character(metrics$total_items)
    })
    
    output$items_change <- renderUI({
      change <- sample(c(-10:25), 1)
      if (change > 0) {
        tags$span(
          class = "change-positive",
          icon("arrow-up"),
          paste0("+", change, " this week")
        )
      } else if (change < 0) {
        tags$span(
          class = "change-negative",
          icon("arrow-down"),
          paste0(abs(change), " this week")
        )
      } else {
        tags$span(
          class = "text-muted",
          "No change"
        )
      }
    })
    
    output$completion_rate <- renderText({
      metrics <- calculate_metrics()
      if (metrics$total_items > 0) {
        rate <- round((metrics$completed_items / metrics$total_items) * 100, 1)
        paste0(rate, "%")
      } else {
        "0%"
      }
    })
    
    output$completion_change <- renderUI({
      change <- sample(c(-5:15), 1) / 10
      if (change > 0) {
        tags$span(
          class = "change-positive",
          icon("arrow-up"),
          paste0("+", change, "%")
        )
      } else if (change < 0) {
        tags$span(
          class = "change-negative",
          icon("arrow-down"),
          paste0(abs(change), "%")
        )
      } else {
        tags$span(
          class = "text-muted",
          "No change"
        )
      }
    })
    
    # Team Workload Chart
    output$team_workload_plot <- renderPlot({
      # Create sample workload data
      workload_data <- data.frame(
        Team = c("Clinical", "Statistical", "Medical Writing", "Data Management", "QC"),
        Tasks = c(45, 38, 52, 29, 41),
        Capacity = c(50, 45, 55, 40, 45)
      )
      
      workload_data$Utilization <- round((workload_data$Tasks / workload_data$Capacity) * 100)
      
      # Create horizontal bar chart
      par(mar = c(4, 8, 2, 2))
      barplot(
        workload_data$Utilization,
        names.arg = workload_data$Team,
        horiz = TRUE,
        col = ifelse(workload_data$Utilization > 90, "#dc3545", 
                    ifelse(workload_data$Utilization > 70, "#ffc107", "#667eea")),
        xlim = c(0, 120),
        xlab = "Utilization (%)",
        las = 1,
        border = NA
      )
      abline(v = 100, col = "red", lty = 2, lwd = 2)
      grid(nx = NA, ny = NULL, col = "gray90")
    })
    
    # Progress Tracking Chart
    output$progress_tracking_plot <- renderPlot({
      # Create sample progress data
      dates <- seq(Sys.Date() - 29, Sys.Date(), by = "day")
      planned <- cumsum(rep(10, 30))
      actual <- cumsum(c(8, 9, 10, 11, 9, 8, 10, 12, 11, 10, 
                        9, 10, 11, 10, 9, 10, 11, 12, 10, 9,
                        10, 11, 10, 9, 10, 11, 10, 9, 10, 11))
      
      par(mar = c(4, 4, 2, 2))
      plot(dates, planned, type = "l", col = "#6c757d", lwd = 2,
           ylim = c(0, max(planned) * 1.1),
           xlab = "Date", ylab = "Cumulative Items",
           main = "Planned vs Actual Progress")
      lines(dates, actual, col = "#667eea", lwd = 2)
      
      # Add legend
      legend("topleft", 
             legend = c("Planned", "Actual"),
             col = c("#6c757d", "#667eea"),
             lwd = 2,
             bty = "n")
      
      # Add grid
      grid(col = "gray90")
    })
    
    # Resource Allocation Chart
    output$resource_allocation_plot <- renderPlot({
      # Create sample resource data
      resources <- data.frame(
        Category = c("Development", "Testing", "Documentation", "Review", "Other"),
        Hours = c(120, 80, 45, 60, 25)
      )
      
      # Create pie chart with custom colors
      colors <- c("#667eea", "#764ba2", "#f67280", "#c06c84", "#6c5b7b")
      
      par(mar = c(2, 2, 2, 2))
      pie(resources$Hours, 
          labels = paste0(resources$Category, "\n", 
                         round(resources$Hours / sum(resources$Hours) * 100, 1), "%"),
          col = colors,
          border = "white",
          main = "")
    })
    
    # Recent Activity List
    output$activity_list <- renderUI({
      if (length(rv$recent_activity) > 0) {
        activity_items <- lapply(rv$recent_activity, function(activity) {
          time_ago <- format_relative_time(activity$time)
          
          div(
            class = "activity-item",
            div(
              class = "d-flex align-items-start",
              div(
                class = paste("me-3 text", activity$color),
                icon(activity$icon)
              ),
              div(
                class = "flex-grow-1",
                div(
                  class = "fw-semibold",
                  paste(toupper(substring(activity$action, 1, 1)), 
                        substring(activity$action, 2), " ",
                        activity$type, sep = "")
                ),
                div(
                  class = "text-muted small",
                  activity$title
                ),
                div(
                  class = "text-muted small mt-1",
                  time_ago
                )
              )
            )
          )
        })
        
        tagList(activity_items)
      } else {
        div(
          class = "text-center text-muted py-4",
          icon("inbox"),
          p("No recent activity", class = "mt-2")
        )
      }
    })
    
    # Bottleneck Analysis
    output$bottleneck_list <- renderUI({
      # Identify potential bottlenecks
      bottlenecks <- list()
      
      # Check for overdue items (mock data)
      bottlenecks <- append(bottlenecks, list(
        div(
          class = "alert alert-warning",
          icon("exclamation-triangle"),
          " 5 items are overdue in Statistical Analysis"
        )
      ))
      
      # Check for resource constraints
      bottlenecks <- append(bottlenecks, list(
        div(
          class = "alert alert-info",
          icon("users"),
          " Medical Writing team at 95% capacity"
        )
      ))
      
      if (length(bottlenecks) > 0) {
        tagList(bottlenecks)
      } else {
        div(
          class = "alert alert-success",
          icon("check-circle"),
          " No bottlenecks identified"
        )
      }
    })
    
    # Team Details Table
    output$team_details_table <- DT::renderDataTable({
      # Create sample team data
      team_data <- data.frame(
        Member = c("John Smith", "Jane Doe", "Bob Wilson", "Alice Brown", "Charlie Davis"),
        Team = c("Clinical", "Statistical", "Medical Writing", "Data Management", "QC"),
        `Active Tasks` = c(12, 8, 15, 6, 10),
        `Completed This Week` = c(5, 7, 4, 8, 6),
        Utilization = c("85%", "72%", "95%", "60%", "80%"),
        Status = c("Active", "Active", "Active", "Active", "Active"),
        stringsAsFactors = FALSE,
        check.names = FALSE
      )
      
      DT::datatable(
        team_data,
        options = list(
          dom = 'ftip',
          pageLength = 10,
          searching = TRUE,
          ordering = TRUE,
          columnDefs = list(
            list(className = 'text-center', targets = c(2, 3, 4, 5))
          )
        ),
        rownames = FALSE
      )
    }, server = FALSE)
    
    # Last update time
    output$last_update <- renderText({
      if (!is.null(rv$last_refresh)) {
        format(rv$last_refresh, "%H:%M:%S")
      } else {
        "Never"
      }
    })
    
    # Export handlers
    observeEvent(input$export_pdf, {
      showNotification(
        "PDF export will be available in a future release",
        type = "message",
        duration = 3
      )
    })
    
    observeEvent(input$export_excel, {
      showNotification(
        "Excel export will be available in a future release",
        type = "message",
        duration = 3
      )
    })
    
    observeEvent(input$export_csv, {
      showNotification(
        "CSV export will be available in a future release",
        type = "message",
        duration = 3
      )
    })
    
    # Helper function for relative time
    format_relative_time <- function(date_str) {
      if (is.null(date_str) || is.na(date_str)) return("Unknown")
      
      tryCatch({
        dt <- as.POSIXct(date_str, format = "%Y-%m-%dT%H:%M:%S")
        diff <- difftime(Sys.time(), dt, units = "auto")
        
        if (as.numeric(diff) < 1) {
          return("Just now")
        } else if (as.numeric(diff) < 60) {
          return(paste0(round(as.numeric(diff)), " minutes ago"))
        } else if (as.numeric(diff) < 1440) {
          hours <- round(as.numeric(diff) / 60)
          return(paste0(hours, " hour", ifelse(hours > 1, "s", ""), " ago"))
        } else {
          days <- round(as.numeric(diff) / 1440)
          return(paste0(days, " day", ifelse(days > 1, "s", ""), " ago"))
        }
      }, error = function(e) {
        return("Unknown")
      })
    }
    
    # Universal CRUD Manager integration (Phase 4)
    # Replaces entity-specific WebSocket observer with standardized refresh trigger
    observeEvent(input$`admin_dashboard-crud_refresh`, {
      if (!is.null(input$`admin_dashboard-crud_refresh`)) {
        cat("📊 Universal CRUD refresh triggered for admin dashboard\n")
        load_dashboard_data()
      }
    })
    
    # Legacy WebSocket observer (kept for backward compatibility during transition)
    observeEvent(input$`admin-dashboard-websocket_event`, {
      # Reload data when we receive any WebSocket event
      load_dashboard_data()
    })
    
    # Return module interface
    return(list(
      refresh = function() {
        load_dashboard_data()
      },
      get_metrics = function() {
        calculate_metrics()
      }
    ))
  })
}