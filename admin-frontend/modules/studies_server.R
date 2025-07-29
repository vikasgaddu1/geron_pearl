# Studies Server Module - Modern bslib version

studies_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Reactive values
    studies_data <- reactiveVal(data.frame())
    selected_study_id <- reactiveVal(NULL)
    is_editing <- reactiveVal(FALSE)
    last_update <- reactiveVal(Sys.time())
    
    # Load studies data
    load_studies <- function() {
      result <- get_studies()
      if ("error" %in% names(result)) {
        showNotification(paste("Error loading studies:", result$error), type = "error")
        studies_data(data.frame())
      } else {
        # Convert list to data frame
        if (length(result) > 0) {
          df <- data.frame(
            ID = sapply(result, function(x) x$id),
            Label = sapply(result, function(x) x$study_label),
            stringsAsFactors = FALSE
          )
          studies_data(df)
        } else {
          studies_data(data.frame(
            ID = character(0),
            Label = character(0)
          ))
        }
        last_update(Sys.time())
      }
    }
    
    # Initial load
    load_studies()
    
    # Value box outputs
    output$total_studies <- renderText({
      nrow(studies_data())
    })
    
    output$last_updated <- renderText({
      format(last_update(), "%H:%M:%S")
    })
    
    # Enable/disable action buttons based on selection
    observe({
      selected_rows <- input$studies_table_rows_selected
      has_selection <- !is.null(selected_rows) && length(selected_rows) > 0
      
      updateActionButton(session, "edit_study", disabled = !has_selection)
      updateActionButton(session, "delete_study", disabled = !has_selection)
    })
    
    # Render studies table with modern styling
    output$studies_table <- DT::renderDataTable({
      DT::datatable(
        studies_data(),
        selection = "single",
        class = "table table-hover table-striped",
        options = list(
          pageLength = 10,
          autoWidth = TRUE,
          scrollX = TRUE,
          columnDefs = list(
            list(targets = 0, width = "80px"),  # ID column
            list(targets = 1, width = "300px") # Label column
          ),
          dom = 'Bfrtip',
          buttons = list('copy', 'csv', 'excel', 'pdf', 'print'),
          responsive = TRUE
        ),
        extensions = 'Buttons'
      )
    })
    
    # Refresh button
    observeEvent(input$refresh, {
      load_studies()
      showNotification(
        tagList(bs_icon("check"), "Studies refreshed successfully"),
        type = "message",
        duration = 3
      )
    })
    
    # Add study button - using bslib modal
    observeEvent(input$add_study, {
      is_editing(FALSE)
      selected_study_id(NULL)
      
      showModal(modalDialog(
        title = tagList(bs_icon("plus-lg"), "Add New Study"),
        size = "m",
        easyClose = FALSE,
        
        div(
          class = "mb-3",
          tags$label("Study Label", class = "form-label"),
          textInput(
            ns("study_label"), 
            NULL,
            value = "", 
            placeholder = "Enter a unique study identifier",
            width = "100%"
          )
        ),
        
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          actionButton(
            ns("cancel_study"), 
            tagList(bs_icon("x"), "Cancel"),
            class = "btn btn-outline-secondary"
          ),
          actionButton(
            ns("save_study"), 
            tagList(bs_icon("check"), "Save Study"),
            class = "btn btn-success"
          )
        )
      ))
    })
    
    # Edit study button
    observeEvent(input$edit_study, {
      selected_row <- input$studies_table_rows_selected
      if (length(selected_row) == 0) {
        showNotification("Please select a study to edit", type = "warning")
        return()
      }
      
      study_id <- studies_data()[selected_row, "ID"]
      selected_study_id(study_id)
      is_editing(TRUE)
      
      # Load study data
      result <- get_study(study_id)
      if ("error" %in% names(result)) {
        showNotification(paste("Error loading study:", result$error), type = "error")
      } else {
        showModal(modalDialog(
          title = tagList(bs_icon("pencil"), "Edit Study"),
          size = "m",
          easyClose = FALSE,
          
          div(
            class = "mb-3",
            tags$label("Study Label", class = "form-label"),
            textInput(
              ns("study_label"), 
              NULL,
              value = result$study_label, 
              placeholder = "Enter a unique study identifier",
              width = "100%"
            )
          ),
          
          
          footer = div(
            class = "d-flex justify-content-end gap-2",
            actionButton(
              ns("cancel_study"), 
              tagList(bs_icon("x"), "Cancel"),
              class = "btn btn-outline-secondary"
            ),
            actionButton(
              ns("save_study"), 
              tagList(bs_icon("check"), "Update Study"),
              class = "btn btn-warning"
            )
          )
        ))
      }
    })
    
    # Delete study button
    observeEvent(input$delete_study, {
      selected_row <- input$studies_table_rows_selected
      if (length(selected_row) == 0) {
        showNotification("Please select a study to delete", type = "warning")
        return()
      }
      
      study_id <- studies_data()[selected_row, "ID"]
      study_label <- studies_data()[selected_row, "Label"]
      
      showModal(modalDialog(
        title = tagList(bs_icon("exclamation-triangle"), "Confirm Deletion"),
        
        div(
          class = "alert alert-danger",
          tagList(
            tags$strong("Warning: "), 
            "This action cannot be undone."
          )
        ),
        
        tags$p(
          "Are you sure you want to delete the study: ",
          tags$strong(study_label), "?"
        ),
        
        footer = div(
          class = "d-flex justify-content-end gap-2",
          modalButton("Cancel"),
          actionButton(
            ns("confirm_delete"), 
            tagList(bs_icon("trash"), "Delete Study"),
            class = "btn btn-danger"
          )
        )
      ))
    })
    
    # Confirm delete
    observeEvent(input$confirm_delete, {
      selected_row <- input$studies_table_rows_selected
      study_id <- studies_data()[selected_row, "ID"]
      
      result <- delete_study(study_id)
      if ("error" %in% names(result)) {
        showNotification(
          tagList(bs_icon("x-circle"), "Error deleting study:", result$error), 
          type = "error"
        )
      } else {
        showNotification(
          tagList(bs_icon("check"), "Study deleted successfully"), 
          type = "message"
        )
        load_studies()
      }
      removeModal()
    })
    
    # Save study
    observeEvent(input$save_study, {
      if (nchar(trimws(input$study_label)) == 0) {
        showNotification(
          tagList(bs_icon("exclamation-circle"), "Study label is required"), 
          type = "error"
        )
        return()
      }
      
      study_data <- list(
        study_label = trimws(input$study_label)
      )
      
      if (is_editing()) {
        # Update existing study
        result <- update_study(selected_study_id(), study_data)
        if ("error" %in% names(result)) {
          showNotification(
            tagList(bs_icon("x-circle"), "Error updating study:", result$error), 
            type = "error"
          )
        } else {
          showNotification(
            tagList(bs_icon("check"), "Study updated successfully"), 
            type = "message"
          )
          load_studies()
          removeModal()
        }
      } else {
        # Create new study
        result <- create_study(study_data)
        if ("error" %in% names(result)) {
          showNotification(
            tagList(bs_icon("x-circle"), "Error creating study:", result$error), 
            type = "error"
          )
        } else {
          showNotification(
            tagList(bs_icon("check"), "Study created successfully"), 
            type = "message"
          )
          load_studies()
          removeModal()
        }
      }
    })
    
    # Cancel study form
    observeEvent(input$cancel_study, {
      removeModal()
    })
    
    # Status message
    output$status_message <- renderText({
      count <- nrow(studies_data())
      if (count == 0) {
        "No studies found. Click 'Add Study' to create your first study."
      } else if (count == 1) {
        "1 study in database"
      } else {
        paste(count, "studies in database")
      }
    })
  })
}