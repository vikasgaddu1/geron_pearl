# Studies UI Module - Modern bslib version

studies_ui <- function(id) {
  ns <- NS(id)
  
  layout_columns(
    col_widths = 12,
    
    # Statistics Cards Row
    layout_columns(
      col_widths = c(3, 3, 3, 3),
      value_box(
        title = "Total Studies",
        value = textOutput(ns("total_studies"), inline = TRUE),
        showcase = bs_icon("database"),
        theme = "primary",
        full_screen = FALSE
      ),
      value_box(
        title = "Active Sessions", 
        value = "1",
        showcase = bs_icon("people"),
        theme = "info",
        full_screen = FALSE
      ),
      value_box(
        title = "Last Updated",
        value = textOutput(ns("last_updated"), inline = TRUE),
        showcase = bs_icon("clock"),
        theme = "secondary",
        full_screen = FALSE
      ),
      value_box(
        title = "System Status",
        value = "Online",
        showcase = bs_icon("check-circle-fill"),
        theme = "success",
        full_screen = FALSE
      )
    ),
    
    # Main Studies Management Card
    card(
      full_screen = TRUE,
      card_header(
        class = "d-flex justify-content-between align-items-center",
        tags$h4(
          bs_icon("table"), 
          "Studies Management",
          class = "mb-0"
        ),
        div(
          class = "btn-group",
          actionButton(
            ns("refresh"), 
            tagList(bs_icon("arrow-clockwise"), "Refresh"),
            class = "btn btn-outline-primary btn-sm"
          ),
          actionButton(
            ns("add_study"), 
            tagList(bs_icon("plus-lg"), "Add Study"),
            class = "btn btn-success btn-sm"
          )
        )
      ),
      card_body(
        # Action buttons for selected items
        div(
          class = "mb-3 d-flex gap-2",
          actionButton(
            ns("edit_study"), 
            tagList(bs_icon("pencil"), "Edit Selected"),
            class = "btn btn-warning btn-sm",
            disabled = TRUE
          ),
          actionButton(
            ns("delete_study"), 
            tagList(bs_icon("trash"), "Delete Selected"),
            class = "btn btn-danger btn-sm", 
            disabled = TRUE
          )
        ),
        
        # Studies table with modern styling
        div(
          class = "table-responsive",
          DT::dataTableOutput(ns("studies_table"))
        )
      ),
      card_footer(
        class = "text-muted small",
        textOutput(ns("status_message"))
      )
    )
  )
}