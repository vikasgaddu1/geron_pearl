# Reporting Effort Items UI Module - CRUD for reporting effort items

reporting_effort_items_ui <- function(id) {
  ns <- NS(id)
  
  # Helper function for hidden elements (if not already loaded)
  if (!exists("hidden")) {
    hidden <- function(...) {
      shinyjs::hidden(...)
    }
  }
  
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
              tags$h4(bs_icon("list-task"), " Reporting Effort Items", class = "mb-0 text-primary"),
              tags$small("Manage TLFs and datasets for reporting efforts", class = "text-muted")
            ),
            div(
              class = "d-flex gap-2",
              # Reporting Effort selector
              div(
                style = "min-width: 200px;",
                selectInput(
                  ns("selected_reporting_effort"),
                  NULL,
                  choices = NULL,
                  width = "100%",
                  selectize = TRUE
                )
              ),
              actionButton(
                ns("refresh_btn"),
                "Refresh",
                icon = icon("sync"),
                class = "btn btn-primary btn-sm",
                title = "Refresh the items data"
              ),
              actionButton(
                ns("toggle_add_item"),
                "Add Item",
                icon = icon("plus"),
                class = "btn btn-success btn-sm",
                title = "Add a new item"
              ),
              # Dropdown for bulk operations
              div(
                class = "dropdown",
                tags$button(
                  class = "btn btn-info btn-sm dropdown-toggle",
                  type = "button",
                  `data-bs-toggle` = "dropdown",
                  `aria-expanded` = "false",
                  title = "Bulk operations and copy features",
                  tagList(icon("tools"), " Actions")
                ),
                tags$ul(
                  class = "dropdown-menu",
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("bulk_tlf_btn"),
                    tagList(icon("upload"), " Bulk Upload TLFs")
                  )),
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("bulk_dataset_btn"),
                    tagList(icon("upload"), " Bulk Upload Datasets")
                  )),
                  tags$li(tags$hr(class = "dropdown-divider")),
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("copy_from_package_btn"),
                    tagList(icon("copy"), " Copy from Package")
                  )),
                  tags$li(tags$a(
                    class = "dropdown-item", 
                    href = "#",
                    id = ns("copy_from_effort_btn"),
                    tagList(icon("copy"), " Copy from Reporting Effort")
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
          
          # Body with sidebar
          card_body(
            class = "p-0",
            style = "height: 100%;",
            
            layout_sidebar(
              fillable = TRUE,
              sidebar = sidebar(
                id = ns("items_sidebar"),
                width = 500,
                position = "right",
                padding = c(3, 3, 3, 4),
                open = "closed",
                
                # Item Form
                div(
                  id = ns("item_form"),
                  tags$h6("Add/Edit Item", class = "text-center fw-bold mb-3"),
                  
                  # Item Type
                  radioButtons(
                    ns("item_type"),
                    "Item Type",
                    choices = list("TLF" = "TLF", "Dataset" = "Dataset"),
                    selected = "TLF",
                    inline = TRUE
                  ),
                  
                  # Item Code
                  textInput(
                    ns("item_code"),
                    "Item Code",
                    placeholder = "Enter item code..."
                  ),
                  
                  # Item Subtype (conditional on type)
                  conditionalPanel(
                    condition = "input.item_type == 'TLF'",
                    ns = ns,
                    selectInput(
                      ns("tlf_subtype"),
                      "TLF Subtype",
                      choices = list(
                        "Table" = "Table",
                        "Listing" = "Listing", 
                        "Figure" = "Figure"
                      ),
                      selected = "Table"
                    )
                  ),
                  
                  conditionalPanel(
                    condition = "input.item_type == 'Dataset'",
                    ns = ns,
                    selectInput(
                      ns("dataset_subtype"),
                      "Dataset Subtype",
                      choices = list(
                        "ADAM" = "ADAM",
                        "SDTM" = "SDTM",
                        "Raw" = "Raw"
                      ),
                      selected = "ADAM"
                    )
                  ),
                  
                  # TLF-specific fields
                  conditionalPanel(
                    condition = "input.item_type == 'TLF'",
                    ns = ns,
                    textInput(
                      ns("tlf_title"),
                      "Title",
                      placeholder = "Enter TLF title..."
                    ),
                    textAreaInput(
                      ns("tlf_description"),
                      "Description",
                      placeholder = "Enter TLF description...",
                      rows = 3
                    ),
                    textInput(
                      ns("tlf_population"),
                      "Population",
                      placeholder = "e.g., Safety, ITT, PP..."
                    ),
                    checkboxInput(
                      ns("tlf_mock_available"),
                      "Mock Available",
                      value = FALSE
                    ),
                    checkboxInput(
                      ns("tlf_asr_ready"),
                      "ASR Ready",
                      value = FALSE
                    )
                  ),
                  
                  # Dataset-specific fields
                  conditionalPanel(
                    condition = "input.item_type == 'Dataset'",
                    ns = ns,
                    textInput(
                      ns("dataset_name"),
                      "Dataset Name",
                      placeholder = "Enter dataset name..."
                    ),
                    textAreaInput(
                      ns("dataset_description"),
                      "Description",
                      placeholder = "Enter dataset description...",
                      rows = 3
                    ),
                    textInput(
                      ns("dataset_location"),
                      "Location",
                      placeholder = "Enter dataset path/location..."
                    ),
                    checkboxInput(
                      ns("dataset_locked"),
                      "Locked",
                      value = FALSE
                    )
                  ),
                  
                  # Hidden ID field for editing
                  hidden(
                    numericInput(ns("edit_item_id"), "ID", value = NA)
                  ),
                  
                  # Action buttons
                  layout_columns(
                    col_widths = c(6, 6),
                    gap = 2,
                    actionButton(
                      ns("save_item"),
                      "Create",
                      icon = icon("check"),
                      class = "btn btn-success w-100",
                      style = "height: auto; padding: 0.375rem 0.75rem;",
                      title = "Create the item"
                    ),
                    actionButton(
                      ns("cancel_item"),
                      "Cancel",
                      icon = icon("times"),
                      class = "btn btn-secondary w-100",
                      style = "height: auto; padding: 0.375rem 0.75rem;",
                      title = "Cancel and close"
                    )
                  )
                )
              ),
              
              # Main content area
              div(
                style = "padding: 10px 0;",
                uiOutput(ns("items_error_msg")),
                
                # Status message for no reporting effort selected
                conditionalPanel(
                  condition = "input.selected_reporting_effort == null || input.selected_reporting_effort == ''",
                  ns = ns,
                  div(
                    class = "alert alert-info text-center",
                    style = "margin: 50px 20px;",
                    tags$h5(icon("info-circle"), " Select a Reporting Effort"),
                    tags$p("Please select a reporting effort from the dropdown above to view and manage its items.")
                  )
                ),
                
                # DataTable container with fixed height
                conditionalPanel(
                  condition = "input.selected_reporting_effort != null && input.selected_reporting_effort != ''",
                  ns = ns,
                  div(
                    style = "height: 550px; overflow-y: auto;",
                    DTOutput(ns("items_table"))
                  )
                )
              )
            )
          )
        )
      )
    ),
    
    # JavaScript for dropdown clicks
    tags$script(HTML(sprintf("
      document.addEventListener('DOMContentLoaded', function() {
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
        document.getElementById('%s').addEventListener('click', function(e) {
          e.preventDefault();
          Shiny.setInputValue('%s', Math.random(), {priority: 'event'});
        });
      });
    ", 
    ns("bulk_tlf_btn"), ns("bulk_tlf_clicked"),
    ns("bulk_dataset_btn"), ns("bulk_dataset_clicked"),
    ns("copy_from_package_btn"), ns("copy_from_package_clicked"),
    ns("copy_from_effort_btn"), ns("copy_from_effort_clicked"),
    ns("export_tracker_btn"), ns("export_tracker_clicked"),
    ns("import_tracker_btn"), ns("import_tracker_clicked")
    )))
  )
}