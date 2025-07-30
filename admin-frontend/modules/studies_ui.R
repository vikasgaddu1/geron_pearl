studies_ui <- function(id) {
  ns <- NS(id)
  
  # Main content area with centered card
  layout_columns(
    col_widths = 12,
    
    div(
      class = "d-flex justify-content-center",
      div(
        style = "width: 100%; max-width: 900px;",
        
        card(
          full_screen = FALSE,
          height = "600px",
          
          card_header(
            class = "d-flex justify-content-between align-items-center",
            tags$h4(
              bs_icon("database"), 
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
                ns("toggle_add_form"), 
                tagList(bs_icon("plus-lg"), "Add Study"),
                class = "btn btn-success btn-sm"
              )
            )
          ),
          
          card_body(
            class = "p-0",
            
            layout_sidebar(
              sidebar = sidebar(
                id = ns("add_study_sidebar"),
                title = tagList(bs_icon("plus-lg"), "Add New Study"),
                width = 300,
                open = FALSE,
                position = "right",
                
                # Add study form using bslib components
                card(
                  card_body(
                    # Study label input
                    layout_columns(
                      col_widths = 12,
                      
                      div(
                        tags$label("Study Label", class = "form-label fw-bold"),
                        textInput(
                          ns("new_study_label"), 
                          NULL,
                          value = "", 
                          placeholder = "Enter unique study identifier",
                          width = "100%"
                        ),
                        tags$small(
                          class = "form-text text-muted",
                          "Study labels must be unique"
                        )
                      )
                    ),
                    
                    # Action buttons
                    layout_columns(
                      col_widths = c(6, 6),
                      
                      actionButton(
                        ns("save_new_study"), 
                        tagList(bs_icon("check"), "Create"),
                        class = "btn btn-success w-100"
                      ),
                      actionButton(
                        ns("cancel_new_study"), 
                        tagList(bs_icon("x"), "Cancel"),
                        class = "btn btn-outline-secondary w-100"
                      )
                    )
                  )
                )
              ),
              
              # Main studies content
              div(
                class = "p-3",
                
                # Studies table with built-in search
                div(
                  style = "height: 400px;",
                  DT::dataTableOutput(ns("studies_table"))
                )
              )
            )
          ),
          
          card_footer(
            class = "d-flex justify-content-between align-items-center",
            div(
              class = "d-flex align-items-center gap-3",
              tags$small(
                class = "text-muted",
                textOutput(ns("status_message"))
              ),
              tags$small(
                class = "text-muted",
                textOutput(ns("websocket_status_display"))
              )
            ),
            tags$small(
              class = "text-muted",
              textOutput(ns("last_updated_display"))
            )
          )
        )
      )
    )
  )
}