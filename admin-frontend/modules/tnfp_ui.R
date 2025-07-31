# TNFP UI Module - Text Elements and Acronyms Management

tnfp_ui <- function(id) {
  ns <- NS(id)

  # Fluid page as container
  page_fluid(
    # Center content using d-flex
    div(
      style = "display: flex; justify-content: center; padding: 20px;",
      div(
        style = "width: 100%; max-width: 1200px;",
        
        # Main card
        card(
          class = "border border-2",
          full_screen = FALSE,
          height = "700px",
          
          # Header
          card_header(
            class = "d-flex justify-content-between align-items-center",
            div(
              tags$h4(bs_icon("file-text"), " TNFP Management", class = "mb-0 text-primary"),
              tags$small("Manage text elements and acronyms", class = "text-muted")
            ),
            div(
              class = "d-flex gap-2",
              actionButton(
                ns("refresh_btn"),
                tagList(bs_icon("arrow-clockwise"), "Refresh"),
                class = "btn btn-primary btn-sm",
                title = "Refresh the TNFP data"
              )
            )
          ),
          
          # Body with sidebar layout
          card_body(
            class = "p-0",
      layout_sidebar(
        fillable = TRUE,
        sidebar = sidebar(
          id = ns("tnfp_sidebar"),
          width = 450,
          position = "right",
          padding = c(3, 3, 3, 4),
          open = "closed",
          
          # Tab selection for different TNFP entities
          div(
            class = "mb-3",
            tags$h6("Entity Type", class = "text-muted mb-2"),
            radioButtons(
              ns("entity_type"),
              label = NULL,
              choices = list(
                "Text Elements" = "text_elements",
                "Acronyms" = "acronyms"
              ),
              selected = "text_elements",
              inline = FALSE
            )
          ),
          
          # Text Elements Form (shown by default)
          conditionalPanel(
            condition = "input.entity_type == 'text_elements'",
            ns = ns,
            div(
              id = ns("text_element_form"),
              tags$h6("Text Element Details", class = "text-muted mb-3"),
              
              # Text Element Type
              selectInput(
                ns("new_text_element_type"),
                "Type",
                choices = list(
                  "Title" = "title",
                  "Footnote" = "footnote", 
                  "Population Set" = "population_set"
                ),
                selected = "title"
              ),
              
              # Text Element Label
              textAreaInput(
                ns("new_text_element_label"),
                "Label",
                placeholder = "Enter text content...",
                rows = 4
              ),
              
              # Action buttons
              layout_columns(
                col_widths = c(6, 6),
                gap = 2,
                actionButton(
                  ns("save_text_element"),
                  tagList(bs_icon("check"), "Create"),
                  class = "btn btn-success w-100",
                  style = "height: auto; padding: 0.375rem 0.75rem;",
                  title = "Create the new text element"
                ),
                actionButton(
                  ns("cancel_text_element"),
                  tagList(bs_icon("x"), "Cancel"),
                  class = "btn btn-secondary w-100",
                  style = "height: auto; padding: 0.375rem 0.75rem;",
                  title = "Cancel and close the form"
                )
              )
            )
          ),
          
          # Acronyms Form
          conditionalPanel(
            condition = "input.entity_type == 'acronyms'",
            ns = ns,
            div(
              id = ns("acronym_form"),
              tags$h6("Acronym Details", class = "text-muted mb-3"),
              
              # Acronym Key
              textInput(
                ns("new_acronym_key"),
                "Key",
                placeholder = "e.g., NA, EU, etc."
              ),
              
              # Acronym Value
              textInput(
                ns("new_acronym_value"),
                "Value", 
                placeholder = "e.g., North America, Europe, etc."
              ),
              
              # Acronym Description
              textAreaInput(
                ns("new_acronym_description"),
                "Description (Optional)",
                placeholder = "Additional details about this acronym...",
                rows = 3
              ),
              
              # Action buttons
              layout_columns(
                col_widths = c(6, 6),
                gap = 2,
                actionButton(
                  ns("save_acronym"),
                  tagList(bs_icon("check"), "Create"),
                  class = "btn btn-success w-100",
                  style = "height: auto; padding: 0.375rem 0.75rem;",
                  title = "Create the new acronym"
                ),
                actionButton(
                  ns("cancel_acronym"),
                  tagList(bs_icon("x"), "Cancel"),
                  class = "btn btn-secondary w-100",
                  style = "height: auto; padding: 0.375rem 0.75rem;",
                  title = "Cancel and close the form"
                )
              )
            )
          )
        ),
        
        # Main content area with tabbed interface
        div(
          class = "p-3",
          style = "height: 500px; overflow-y: auto;",
          
          # Text Elements Table
          conditionalPanel(
            condition = "input.entity_type == 'text_elements'",
            ns = ns,
            div(
              class = "mb-3 d-flex justify-content-between align-items-center",
              tags$h5("Text Elements", class = "mb-0"),
              div(
                class = "d-flex gap-2",
                actionButton(
                  ns("toggle_add_text_element"),
                  tagList(bs_icon("plus-lg"), "Add Text Element"),
                  class = "btn btn-success"
                )
              )
            ),
            DT::dataTableOutput(ns("text_elements_table"))
          ),
          
          # Acronyms Table
          conditionalPanel(
            condition = "input.entity_type == 'acronyms'",
            ns = ns,
            div(
              class = "mb-3 d-flex justify-content-between align-items-center",
              tags$h5("Acronyms", class = "mb-0"),
              div(
                class = "d-flex gap-2",
                actionButton(
                  ns("toggle_add_acronym"),
                  tagList(bs_icon("plus-lg"), "Add Acronym"),
                  class = "btn btn-success"
                )
              )
            ),
            DT::dataTableOutput(ns("acronyms_table"))
          )
        )
      )
    )
  )
)
)
)
}