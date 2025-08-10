study_tree_ui <- function(id) {
  ns <- NS(id)

  page_fluid(
    div(
      style = "display: flex; justify-content: center; padding: 20px;",
      div(
        style = "width: 100%; max-width: 1200px;",

        card(
          class = "border border-2",
          full_screen = FALSE,

          card_header(
            class = "d-flex justify-content-between align-items-center",
            div(
              tags$h4(bs_icon("diagram-3"), " Study Management", class = "mb-0 text-primary"),
              tags$small("Manage studies, database releases, and reporting efforts in a tree", class = "text-muted")
            ),
            div(
              class = "d-flex gap-2",
              input_task_button(
                ns("refresh_tree"),
                tagList(bs_icon("arrow-clockwise"), "Refresh"),
                class = "btn btn-primary btn-sm",
                title = "Refresh the tree"
              ),
              input_task_button(
                ns("add_study"),
                tagList(bs_icon("plus-lg"), "Add Study"),
                class = "btn btn-success btn-sm",
                title = "Add a new study"
              ),
              input_task_button(
                ns("add_child"),
                tagList(bs_icon("plus"), "Add Child"),
                class = "btn btn-outline-success btn-sm",
                title = "Add a child to the selected node (Release or Effort)"
              ),
              input_task_button(
                ns("edit_selected"),
                tagList(bs_icon("pencil"), "Edit"),
                class = "btn btn-warning btn-sm",
                title = "Edit the selected item"
              ),
              input_task_button(
                ns("delete_selected"),
                tagList(bs_icon("trash"), "Delete"),
                class = "btn btn-danger btn-sm",
                title = "Delete the selected item"
              )
            )
          ),

          card_body(
            class = "p-3",
            div(
              class = "row g-3",
              div(
                class = "col-12",
                shinyTree::shinyTree(ns("study_tree"), search = TRUE, theme = "default", themeIcons = TRUE, themeDots = TRUE)
              )
            )
          ),

          card_footer(
            class = "d-flex flex-wrap justify-content-between align-items-center small text-muted gap-3",
            div(
              class = "d-flex align-items-center gap-3",
              textOutput(ns("selection_display"), container = span),
              textOutput(ns("status_message"), container = span)
            ),
            textOutput(ns("last_updated_display"))
          )
        )
      )
    )
  )
}


