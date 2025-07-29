#!/usr/bin/env Rscript

# PEARL Admin Frontend - R Shiny Application Runner
# Simple script to run the Shiny application

library(shiny)

# Run the application
cat("Starting PEARL Admin Frontend (R Shiny)...\n")
cat("Application will be available at: http://localhost:3838\n")
cat("Make sure the FastAPI backend is running on http://localhost:8000\n\n")

runApp(
  appDir = ".",
  port = 3838,
  host = "0.0.0.0",
  launch.browser = TRUE
)