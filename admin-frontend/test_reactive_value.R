# Simple test to verify reactive values work correctly
library(shiny)

ui <- fluidPage(
  h3("Reactive Value Test"),
  actionButton("set_value", "Set Value"),
  actionButton("clear_value", "Clear Value"),
  verbatimTextOutput("display_value")
)

server <- function(input, output, session) {
  # Create reactive value similar to study_tree_server
  selected_node <- reactiveVal(list(type = NULL, label = NULL))
  
  observeEvent(input$set_value, {
    cat("Setting selected_node to study/Test Study\n")
    selected_node(list(type = "study", label = "Test Study"))
    cat("After setting, selected_node value is:\n")
    print(selected_node())
  })
  
  observeEvent(input$clear_value, {
    cat("Clearing selected_node\n")
    selected_node(list(type = NULL, label = NULL))
    cat("After clearing, selected_node value is:\n")
    print(selected_node())
  })
  
  output$display_value <- renderText({
    s <- selected_node()
    cat("renderText triggered, selected_node is:\n")
    print(s)
    
    if (is.null(s$type) || is.null(s$label)) {
      return("Selection: none")
    }
    
    type_label <- switch(s$type,
      study = "Study",
      release = "Database Release",
      effort = "Reporting Effort",
      "Item"
    )
    
    paste0("Selection: ", type_label, " — ", s$label)
  })
}

shinyApp(ui, server)