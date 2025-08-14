# Test script for Packages Export functionality
# Run this after starting the Shiny app to test the export feature

library(shiny)
library(bslib)
library(openxlsx)

# Test that openxlsx is installed
if (!requireNamespace("openxlsx", quietly = TRUE)) {
  stop("Please install openxlsx package: install.packages('openxlsx')")
} else {
  cat("✓ openxlsx package is installed\n")
}

# Check if the UI changes are present
ui_file <- readLines("modules/packages_ui.R")
if (any(grepl("export_excel", ui_file))) {
  cat("✓ Export button added to UI\n")
} else {
  cat("✗ Export button not found in UI\n")
}

# Check if the server logic is present
server_file <- readLines("modules/packages_server.R")
if (any(grepl("observeEvent\\(input\\$export_excel", server_file))) {
  cat("✓ Export handler added to server\n")
} else {
  cat("✗ Export handler not found in server\n")
}

cat("\n")
cat("To test the export functionality:\n")
cat("1. Start the Shiny app: shiny::runApp('app.R')\n")
cat("2. Navigate to the Packages module\n")
cat("3. Click the 'Export to Excel' button (blue button with Excel icon)\n")
cat("4. A modal will appear with a download link\n")
cat("5. Click 'Download Excel File' to save the Excel file\n")
cat("\n")
cat("The Excel file will contain:\n")
cat("- Sheet 1: 'Packages' - List of all packages\n")
cat("- Sheet 2: 'Package Items' - All items in all packages\n")
cat("- Sheet 3: 'Export Info' - Metadata about the export\n")
