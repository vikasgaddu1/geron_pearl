# Restore renv environment for PEARL Admin Frontend
# This restores packages from the renv.lock file for reproducible environments

cat("Restoring renv environment for PEARL Admin Frontend...\n")

# Check if renv is available
if (!requireNamespace("renv", quietly = TRUE)) {
  cat("renv not found. Installing renv...\n")
  install.packages("renv")
}

# Check if this is an renv project
if (!file.exists("renv.lock")) {
  cat("❌ renv.lock not found!\n")
  cat("Please run: Rscript init_renv.R to initialize the renv environment first.\n")
  quit(status = 1)
}

# Restore packages from renv.lock
cat("Restoring packages from renv.lock...\n")
renv::restore()

cat("\n✅ renv environment restored successfully!\n")
cat("🚀 You can now run the Shiny app with: Rscript run_app.R\n")