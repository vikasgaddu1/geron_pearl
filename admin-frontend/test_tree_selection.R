# Test script to diagnose tree selection issues
# Run this in R console while the app is running

library(shiny)
library(shinyTree)

# Test data structure similar to what build_tree_data() creates
test_tree <- list(
  "Study 1" = structure(
    list(
      "Release 1.1" = structure(
        list(
          "Effort 1.1.1" = structure(list(), stinfo = list(type = "effort", id = 3))
        ),
        stinfo = list(type = "release", id = 2)
      )
    ),
    stinfo = list(type = "study", id = 1)
  )
)

# Test UI
ui <- fluidPage(
  h3("ShinyTree Selection Test"),
  shinyTree("test_tree", search = TRUE),
  verbatimTextOutput("selection_output"),
  verbatimTextOutput("raw_input")
)

# Test Server
server <- function(input, output, session) {
  output$test_tree <- renderTree({
    test_tree
  })
  
  output$selection_output <- renderText({
    sel <- get_selected(input$test_tree, format = "names")
    if (length(sel) > 0) {
      paste("Selected:", sel[[1]])
    } else {
      "No selection"
    }
  })
  
  output$raw_input <- renderPrint({
    cat("Raw input$test_tree value:\n")
    str(input$test_tree)
  })
  
  observeEvent(input$test_tree, {
    cat("\n=== Tree selection event ===\n")
    cat("input$test_tree:\n")
    print(input$test_tree)
    
    sel <- get_selected(input$test_tree, format = "names")
    cat("\nget_selected result:\n")
    print(sel)
    cat("========================\n")
  })
}

# Run the test app
shinyApp(ui, server)