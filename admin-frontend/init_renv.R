#!/usr/bin/env Rscript

# Initialize renv for PEARL Admin Frontend
# This creates a reproducible R environment

cat("Initializing renv for PEARL Admin Frontend...\n")

# Install renv if not available
if (!requireNamespace("renv", quietly = TRUE)) {
  cat("Installing renv...\n")
  install.packages("renv")
}

# Initialize renv project
renv::init()

# Install required packages
packages <- c(
  "shiny",
  "shinydashboard", 
  "shinyWidgets",
  "shinyBS",
  "DT",
  "httr",
  "jsonlite",
  "dplyr",
  "lubridate"
)

cat("Installing required packages...\n")
renv::install(packages)

# Take a snapshot to lock versions
cat("Creating renv snapshot...\n")
renv::snapshot()

cat("\n✅ renv environment initialized successfully!\n")
cat("📦 Package versions locked in renv.lock\n")
cat("🚀 You can now run the app with: Rscript run_app.R\n")
cat("\nFor other developers:\n")
cat("  1. Run: renv::restore()\n")
cat("  2. Then: Rscript run_app.R\n")