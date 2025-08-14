# Debug script to check why Export button might not be showing

library(bslib)
library(shiny)

# Test 1: Check if bsicons has the Excel icon
cat("Testing icon availability...\n")
tryCatch({
  icon_test <- bs_icon("file-earmark-excel")
  cat("✓ Excel icon is available\n")
}, error = function(e) {
  cat("✗ Excel icon not found. Try using a different icon.\n")
  cat("  Alternative: bs_icon('download') or bs_icon('file-earmark-arrow-down')\n")
})

# Test 2: Check if input_task_button is available
cat("\nTesting input_task_button...\n")
if (exists("input_task_button", mode = "function")) {
  cat("✓ input_task_button function exists\n")
} else {
  cat("✗ input_task_button not found. You may need to update bslib.\n")
}

# Test 3: Check bslib version
cat("\nChecking bslib version...\n")
bslib_version <- packageVersion("bslib")
cat(paste("Current bslib version:", bslib_version, "\n"))
if (bslib_version < "0.5.0") {
  cat("⚠ Consider updating bslib: install.packages('bslib')\n")
}

cat("\n--- Quick Fix Options ---\n")
cat("1. Restart R session: Ctrl+Shift+F10 (Windows) or Cmd+Shift+F10 (Mac)\n")
cat("2. Clear browser cache: Ctrl+F5 or Cmd+Shift+R\n")
cat("3. Check browser console for errors: F12 → Console tab\n")
