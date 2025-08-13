# Reporting Effort Tracker Server Module - Simplified version

reporting_effort_tracker_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    
    # Reactive values
    tracker_data <- reactiveVal(data.frame())
    users_list <- reactiveVal(list())
    
    # Load data functions
    load_tracker_data <- function() {
      result <- get_reporting_effort_tracker()
      if ("error" %in% names(result)) {
        showNotification(paste("Error loading tracker data:", result$error), type = "error")
        tracker_data(data.frame())
      } else {
        if (length(result) > 0) {
          df <- data.frame(
            ID = sapply(result, function(x) x$id),
            Item_Code = sapply(result, function(x) if (!is.null(x$reporting_effort_item$item_code)) x$reporting_effort_item$item_code else "N/A"),
            Item_Type = sapply(result, function(x) if (!is.null(x$reporting_effort_item$item_type)) x$reporting_effort_item$item_type else "N/A"),
            Production_Status = sapply(result, function(x) if (!is.null(x$production_status)) x$production_status else "not_started"),
            Actions = sapply(result, function(x) x$id),
            stringsAsFactors = FALSE
          )
        } else {
          df <- data.frame(
            ID = character(0),
            Item_Code = character(0),
            Item_Type = character(0),
            Production_Status = character(0),
            Actions = character(0),
            stringsAsFactors = FALSE
          )
        }
        tracker_data(df)
      }
    }
    
    # Load data on initialization
    observe({
      load_tracker_data()
    })
    
    # Refresh button
    observeEvent(input$refresh_btn, {
      load_tracker_data()
      showNotification("Tracker data refreshed", type = "message")
    })
    
    # Render table
    output$tracker_table <- DT::renderDataTable({
      data <- tracker_data()
      
      if (nrow(data) == 0) {
        empty_df <- data.frame(
          Item_Code = character(0),
          Item_Type = character(0),
          Production_Status = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE
        )
        
        DT::datatable(
          empty_df,
          options = list(
            dom = 'rtip',
            pageLength = 25,
            language = list(emptyTable = "No tracker entries found")
          ),
          escape = FALSE,
          selection = 'none',
          rownames = FALSE
        )
      } else {
        # Remove ID column for display
        display_df <- data[, c("Item_Code", "Item_Type", "Production_Status", "Actions")]
        
        DT::datatable(
          display_df,
          options = list(
            dom = 'rtip',
            pageLength = 25
          ),
          escape = FALSE,
          selection = 'none',
          rownames = FALSE
        )
      }
    })
    
    # Placeholder for other functionality
    observeEvent(input$bulk_assign_clicked, {
      showNotification("Bulk assign functionality will be available in a future update", type = "message")
    })
    
    observeEvent(input$bulk_status_clicked, {
      showNotification("Bulk status update functionality will be available in a future update", type = "message")
    })
    
    observeEvent(input$workload_summary_clicked, {
      showNotification("Workload summary functionality will be available in a future update", type = "message")
    })
    
    observeEvent(input$export_tracker_clicked, {
      showNotification("Export functionality will be available in a future update", type = "message")
    })
    
    observeEvent(input$import_tracker_clicked, {
      showNotification("Import functionality will be available in a future update", type = "message")
    })
  })
}