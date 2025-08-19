# Quick verification that Export button is in the RIGHT files

cat("=== Verifying Export Button Implementation ===\n\n")

# Check which files the app.R actually loads
app_content <- readLines("app.R")
packages_module_line <- grep("source.*packages", app_content, value = TRUE)

cat("1. Your app.R loads these package modules:\n")
cat(paste("  ", packages_module_line[grepl("packages", packages_module_line)], collapse = "\n"), "\n\n")

# Check if Export button is in the CORRECT UI file
ui_file <- "modules/packages_ui.R"
ui_content <- readLines(ui_file)
export_button_found <- any(grepl("export_excel", ui_content))

cat("2. Export button in packages_ui.R: ")
if (export_button_found) {
  cat("✅ FOUND\n")
  line_num <- which(grepl("export_excel", ui_content))[1]
  cat(paste("   Line", line_num, ":", trimws(ui_content[line_num])), "\n")
} else {
  cat("❌ NOT FOUND\n")
}

# Check if Export handler is in the CORRECT server file
server_file <- "modules/packages_server.R"
server_content <- readLines(server_file)
export_handler_found <- any(grepl("observeEvent.*export_excel", server_content))

cat("\n3. Export handler in packages_server.R: ")
if (export_handler_found) {
  cat("✅ FOUND\n")
  line_num <- which(grepl("observeEvent.*export_excel", server_content))[1]
  cat(paste("   Line", line_num, ":", trimws(server_content[line_num])), "\n")
} else {
  cat("❌ NOT FOUND\n")
}

cat("\n=== Next Steps ===\n")
cat("1. Restart your Shiny app\n")
cat("2. The Export button should now appear!\n")
cat("3. If not visible, try: Ctrl+F5 (hard refresh) in browser\n")
