# Update Dependencies for Modern bslib PEARL Admin Frontend
# This script installs the required packages for the modernized bslib version

cat("🚀 Updating dependencies for modern bslib PEARL Admin Frontend...\n")

# Required packages for the modernized application
required_packages <- c(
  "shiny",      # Core Shiny framework
  "bslib",      # Modern Bootstrap themes and components
  "bsicons",    # Bootstrap icons
  "DT",         # Interactive data tables
  "httr",       # HTTP requests to backend API
  "jsonlite",   # JSON parsing
  "shinyWidgets" # Enhanced UI widgets
)

# Install packages if not already available
cat("📦 Installing required packages...\n")

for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    cat(paste("Installing", pkg, "...\n"))
    install.packages(pkg, dependencies = TRUE)
  } else {
    cat(paste("✅", pkg, "is already installed\n"))
  }
}

# Initialize or update renv if available
if (requireNamespace("renv", quietly = TRUE)) {
  cat("📝 Updating renv snapshot...\n")
  renv::snapshot(confirm = FALSE)
  cat("✅ renv snapshot updated successfully!\n")
} else {
  cat("⚠️  renv not available. Consider using renv for reproducible environments.\n")
  cat("   Run: install.packages('renv') and then renv::init() to get started.\n")
}

cat("\n🎉 Dependencies updated successfully!\n")
cat("📋 Installed packages:\n")
for (pkg in required_packages) {
  if (requireNamespace(pkg, quietly = TRUE)) {
    version <- as.character(packageVersion(pkg))
    cat(paste("  •", pkg, "version", version, "\n"))
  }
}

cat("\n🚀 You can now run the modernized Shiny app with: Rscript run_app.R\n")