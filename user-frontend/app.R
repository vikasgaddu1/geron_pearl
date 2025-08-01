library(shiny)
library(bslib)
library(DT)
library(plotly)

ui <- page_sidebar(
  title = "PEARL - R Shiny & bslib Demo",
  sidebar = sidebar(
    width = 300,
    h4("Controls"),
    sliderInput("n", "Sample Size:", min = 10, max = 1000, value = 100),
    selectInput("plot_type", "Plot Type:", 
                choices = c("Histogram" = "hist", "Scatter" = "scatter", "Box Plot" = "box")),
    radioButtons("theme", "Theme:", 
                 choices = c("Bootstrap" = "bootstrap", "Minty" = "minty", "Darkly" = "darkly")),
    actionButton("refresh", "Refresh Data", class = "btn-primary")
  ),
  
  layout_columns(
    col_widths = c(8, 4),
    
    card(
      card_header("Interactive Plot"),
      plotlyOutput("plot")
    ),
    
    card(
      card_header("Summary Statistics"),
      verbatimTextOutput("summary")
    )
  ),
  
  layout_columns(
    col_widths = c(6, 6),
    
    card(
      card_header("Data Table"),
      DTOutput("table")
    ),
    
    card(
      card_header("Value Boxes"),
      layout_columns(
        col_widths = c(6, 6),
        value_box(
          title = "Mean",
          value = textOutput("mean_val", inline = TRUE),
          showcase = icon("calculator"),
          theme = "primary"
        ),
        value_box(
          title = "Standard Deviation",
          value = textOutput("sd_val", inline = TRUE),
          showcase = icon("chart-line"),
          theme = "success"
        )
      )
    )
  ),
  
  theme = bs_theme(version = 5, preset = "bootstrap")
)

server <- function(input, output, session) {
  
  # Reactive theme switching
  observe({
    session$setCurrentTheme(
      switch(input$theme,
        "bootstrap" = bs_theme(version = 5, preset = "bootstrap"),
        "minty" = bs_theme(version = 5, preset = "minty"),
        "darkly" = bs_theme(version = 5, preset = "darkly")
      )
    )
  })
  
  # Reactive data generation
  data <- reactive({
    input$refresh  # Dependency on refresh button
    
    n <- input$n
    data.frame(
      x = rnorm(n),
      y = rnorm(n),
      category = sample(c("A", "B", "C"), n, replace = TRUE),
      value = runif(n, 1, 100)
    )
  })
  
  # Plot output
  output$plot <- renderPlotly({
    df <- data()
    
    p <- switch(input$plot_type,
      "hist" = ggplot(df, aes(x = x)) + 
               geom_histogram(bins = 30, fill = "steelblue", alpha = 0.7) +
               theme_minimal(),
      
      "scatter" = ggplot(df, aes(x = x, y = y, color = category)) + 
                  geom_point(alpha = 0.7) +
                  theme_minimal(),
      
      "box" = ggplot(df, aes(x = category, y = value, fill = category)) + 
              geom_boxplot(alpha = 0.7) +
              theme_minimal()
    )
    
    ggplotly(p)
  })
  
  # Summary statistics
  output$summary <- renderPrint({
    df <- data()
    summary(df[, c("x", "y", "value")])
  })
  
  # Data table
  output$table <- renderDT({
    datatable(data(), options = list(pageLength = 10, scrollX = TRUE))
  })
  
  # Value boxes
  output$mean_val <- renderText({
    round(mean(data()$x), 3)
  })
  
  output$sd_val <- renderText({
    round(sd(data()$x), 3)
  })
}

shinyApp(ui = ui, server = server)
