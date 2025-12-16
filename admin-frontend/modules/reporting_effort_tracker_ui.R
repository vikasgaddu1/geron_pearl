# Reporting Effort Tracker UI Module - Tracker assignments and status management

reporting_effort_tracker_ui <- function(id) {
  ns <- NS(id)
  
  # Helper function for hidden elements (if not already loaded)
  if (!exists("hidden")) {
    hidden <- function(...) {
      shinyjs::hidden(...)
    }
  }
  
  # Fluid page as container
  page_fluid(
    # Include simplified comments JavaScript
    tags$script(src = paste0("simplified_comments.js?v=", format(Sys.time(), "%Y%m%d%H%M%S"))),
    # Center content using d-flex
    div(
      style = "display: flex; justify-content: center; padding: 20px;",
      div(
        style = "width: 100%; max-width: 100%;",
        
        # Main card
        card(
          class = "border border-2",
          full_screen = FALSE,
          height = "auto",
          
          # Header
          card_header(
            class = "d-flex justify-content-between align-items-center",
            div(
              tags$h4(bs_icon("clipboard-check"), " Tracker Management", class = "mb-0 text-primary"),
              tags$small("Manage programmer assignments and status tracking", class = "text-muted")
            ),
            div(
              class = "d-flex gap-2",
              actionButton(
                ns("refresh_btn"),
                "Refresh",
                icon = icon("sync"),
                class = "btn btn-primary btn-sm",
                title = "Refresh tracker data"
              ),
              # Dropdown for actions
              div(
                class = "dropdown",
                tags$button(
                  class = "btn btn-info btn-sm dropdown-toggle",
                  type = "button",
                  `data-bs-toggle` = "dropdown",
                  `aria-expanded` = "false",
                  title = "Bulk operations and utilities",
                  tagList(icon("tools"), " Actions")
                ),
                tags$ul(
                  class = "dropdown-menu",
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("bulk_assign_btn"),
                    tagList(icon("users"), " Bulk Assign")
                  )),
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("bulk_status_btn"),
                    tagList(icon("clipboard-check"), " Bulk Status Update")
                  )),
                  tags$li(tags$hr(class = "dropdown-divider")),
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("workload_summary_btn"),
                    tagList(icon("chart-bar"), " Workload Summary")
                  )),
                  tags$li(tags$hr(class = "dropdown-divider")),
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("export_tracker_btn"),
                    tagList(icon("download"), " Export Tracker Data")
                  )),
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("import_tracker_btn"),
                    tagList(icon("upload"), " Import Tracker Data")
                  ))
                )
              )
            )
          ),
          
          # Body without sidebar
          card_body(
            class = "p-2",
            style = "height: 100%;",
            
            # Main content area
            div(
              style = "padding: 10px 0;",
              uiOutput(ns("tracker_error_msg")),

              # Reporting Effort selector (same style as items module)
              div(
                id = ns("effort_selector_wrapper"),
                class = "effort-selector-wrapper mb-3",
                div(
                  class = "d-flex align-items-center flex-wrap gap-2",
                  tags$label("Select Reporting Effort", `for` = ns("selected_reporting_effort"), class = "me-2 mb-0 fw-semibold"),
                  selectInput(ns("selected_reporting_effort"), NULL, choices = list("Select a Reporting Effort" = ""), width = "520px")
                )
              ),

              # Three trackers: TLF, SDTM, ADaM
              navset_pill(
                id = ns("tracker_tabs"),
                nav_panel(
                  "TLF Tracker",
                  value = "tlf",
                  div(class = "mb-2", uiOutput(ns("effort_label_tlf"))),
                  div(style = "min-height: 560px; overflow-x: auto;", DTOutput(ns("tracker_table_tlf")))
                ),
                nav_panel(
                  "SDTM Tracker",
                  value = "sdtm",
                  div(class = "mb-2", uiOutput(ns("effort_label_sdtm"))),
                  div(style = "min-height: 560px; overflow-x: auto;", DTOutput(ns("tracker_table_sdtm")))
                ),
                nav_panel(
                  "ADaM Tracker",
                  value = "adam",
                  div(class = "mb-2", uiOutput(ns("effort_label_adam"))),
                  div(style = "min-height: 560px; overflow-x: auto;", DTOutput(ns("tracker_table_adam")))
                )
              )
            )
          )
        )
      )
    ),
    
    # JavaScript for dropdown clicks and row actions
    tags$script(HTML(sprintf("
      document.addEventListener('DOMContentLoaded', function() {
        
        // Custom message handler for loading comments in modal
        Shiny.addCustomMessageHandler('loadCommentsForModal', function(data) {
          if (typeof loadCommentsForModal === 'function') {
            loadCommentsForModal(data.tracker_id);
          }
        });
        document.getElementById('%s').addEventListener('click', function(e) {
          e.preventDefault();
          Shiny.setInputValue('%s', Math.random(), {priority: 'event'});
        });
        document.getElementById('%s').addEventListener('click', function(e) {
          e.preventDefault();
          Shiny.setInputValue('%s', Math.random(), {priority: 'event'});
        });
        document.getElementById('%s').addEventListener('click', function(e) {
          e.preventDefault();
          Shiny.setInputValue('%s', Math.random(), {priority: 'event'});
        });
        document.getElementById('%s').addEventListener('click', function(e) {
          e.preventDefault();
          Shiny.setInputValue('%s', Math.random(), {priority: 'event'});
        });
        document.getElementById('%s').addEventListener('click', function(e) {
          e.preventDefault();
          Shiny.setInputValue('%s', Math.random(), {priority: 'event'});
        });

        // Delegate clicks for inline row actions in all tracker tables
        document.addEventListener('click', function(e) {
          var target = e.target;
          if (target && target.classList.contains('pearl-tracker-action')) {
            e.preventDefault();
            var id = target.getAttribute('data-id');
            var action = target.getAttribute('data-action');
            Shiny.setInputValue('%s', { id: id, action: action, nonce: Math.random() }, {priority: 'event'});
          }
        });
      });
    ", 
    ns("bulk_assign_btn"), ns("bulk_assign_clicked"),
    ns("bulk_status_btn"), ns("bulk_status_clicked"),
    ns("workload_summary_btn"), ns("workload_summary_clicked"),
    ns("export_tracker_btn"), ns("export_tracker_clicked"),
    ns("import_tracker_btn"), ns("import_tracker_clicked"),
    ns("row_action")
    )))
  )
}