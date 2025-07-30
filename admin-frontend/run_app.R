#!/usr/bin/env Rscript

# PEARL Admin Frontend - R Shiny Application Runner
# Simple script to run the Shiny application

library(shiny)

# Load environment variables
if (requireNamespace("dotenv", quietly = TRUE)) {
  dotenv::load_dot_env()
}

# Get API URL from environment
API_BASE_URL <- Sys.getenv("PEARL_API_URL", "http://localhost:8000")

# Run the application
cat("Starting PEARL Admin Frontend (R Shiny)...\n")
cat("Application will be available at: http://localhost:3838\n")
cat("Make sure the FastAPI backend is running on", API_BASE_URL, "\n\n")

runApp(
  appDir = ".",
  port = 3838,
  host = "0.0.0.0",
  launch.browser = TRUE
)