# TNFP UI Module - Text Elements Management

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
          height = NULL,
          
          # Header
          card_header(
            class = "d-flex justify-content-between align-items-center",
            div(
              tags$h4(bs_icon("file-text"), "TFL Properties", class = "mb-0 text-primary"),
              tags$small("Manage titles, footnotes, population sets, and acronym sets", class = "text-muted")
            ),
            div(
              class = "d-flex gap-2",
              actionButton(
                ns("refresh_btn"),
                tagList(bs_icon("arrow-clockwise"), "Refresh"),
                class = "btn btn-primary btn-sm",
                title = "Refresh the TFL Properties data"
              ),
              actionButton(
                ns("toggle_add_text_element"),
                tagList(bs_icon("plus-lg"), "Add Text Element"),
                class = "btn btn-success btn-sm",
                title = "Add a new text element"
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
                
                # Text Element Form
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
                      "Population Set" = "population_set",
                      "Acronym Set" = "acronyms_set"
                    ),
                    selected = "title"
                  ),
                  
                  # Text Element Label
                  div(
                    textAreaInput(
                      ns("new_text_element_label"),
                      "Content",
                      placeholder = "Enter text content...",
                      rows = 4
                    ),
                    tags$small(
                      class = "text-muted form-text",
                      tagList(
                        bs_icon("info-circle", size = "0.8em"),
                        " Duplicate content is not allowed (comparison ignores spaces and letter case)"
                      )
                    )
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
                      title = "Create the text element"
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
              
              # Main content area
              div(class = "p-3",
                  div(class = "mb-3", tags$h5("Text Elements", class = "mb-0")),
                  DT::dataTableOutput(ns("text_elements_table")))
            )
          )
        )
      )
    )
  )
}