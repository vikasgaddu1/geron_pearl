#!/usr/bin/env Rscript

# PEARL Admin Frontend - Consolidated Environment Setup
# This script consolidates init_renv.R, install_dependencies.R, and update_dependencies.R
# Ensures latest versions of all packages, especially Shiny and bslib

cat("🔧 PEARL Admin Frontend - Environment Setup\n")
cat("==========================================\n\n")

# Function to check and install a package with specific version requirements
install_or_update_package <- function(pkg_name, min_version = NULL, from_github = NULL) {
  cat(paste("📦 Processing", pkg_name, "...\n"))
  
  if (!is.null(from_github)) {
    # Install from GitHub for latest development versions
    if (!requireNamespace("remotes", quietly = TRUE)) {
      install.packages("remotes")
    }
    remotes::install_github(from_github, upgrade = "always")
    return()
  }
  
  # Check if package is installed and version requirements
  if (requireNamespace(pkg_name, quietly = TRUE)) {
    current_version <- as.character(packageVersion(pkg_name))
    if (!is.null(min_version)) {
      if (compareVersion(current_version, min_version) >= 0) {
        cat(paste("  ✅", pkg_name, "version", current_version, "meets requirements (>= ", min_version, ")\n"))
        return()
      } else {
        cat(paste("  ⬆️  Updating", pkg_name, "from", current_version, "to latest...\n"))
      }
    } else {
      cat(paste("  ⬆️  Updating", pkg_name, "from", current_version, "to latest...\n"))
    }
  } else {
    cat(paste("  📥 Installing", pkg_name, "...\n"))
  }
  
  # Install or update the package
  install.packages(pkg_name, dependencies = TRUE)
  
  # Verify installation
  if (requireNamespace(pkg_name, quietly = TRUE)) {
    new_version <- as.character(packageVersion(pkg_name))
    cat(paste("  ✅ Success:", pkg_name, "version", new_version, "\n"))
  } else {
    cat(paste("  ❌ Failed to install", pkg_name, "\n"))
  }
}

# Step 1: Install/Update renv first
cat("🎯 Step 1: Setting up renv environment management\n")
if (!requireNamespace("renv", quietly = TRUE)) {
  cat("Installing renv...\n")
  install.packages("renv")
}

# Step 2: Initialize renv project if not already done
if (!file.exists("renv.lock")) {
  cat("🎯 Step 2: Initializing new renv project\n")
  renv::init(bare = TRUE)  # Initialize without installing packages yet
} else {
  cat("🎯 Step 2: Existing renv project detected\n")
}

# Step 3: Install/Update core packages with latest versions
cat("\n🎯 Step 3: Installing/Updating core packages to latest versions\n")

# Core Shiny ecosystem with minimum version requirements
core_packages <- list(
  list(name = "shiny", min_version = "1.8.0"),
  list(name = "bslib", min_version = "0.6.0"),
  list(name = "bsicons", min_version = "0.1.2")
)

# Data and API packages
data_packages <- list(
  list(name = "DT", min_version = "0.30"),
  list(name = "httr2", min_version = "1.0.0"),  # Modern HTTP client
  list(name = "jsonlite", min_version = "1.8.7"),
  list(name = "dplyr", min_version = "1.1.3"),
  list(name = "lubridate", min_version = "1.9.3")
)

# Enhanced UI and validation packages (from rshiny-modern-builder recommendations)
enhancement_packages <- list(
  list(name = "shinyWidgets", min_version = "0.8.0"),
  list(name = "shinyvalidate", min_version = "0.1.3"),
  list(name = "shinyfeedback", min_version = "0.4.0"),
  list(name = "reactlog", min_version = "1.1.1"),
  list(name = "htmltools", min_version = "0.5.7"),
  list(name = "sass", min_version = "0.4.7")
)

# WebSocket and real-time features
realtime_packages <- list(
  list(name = "websocket", min_version = "1.4.1"),
  list(name = "later", min_version = "1.3.1"),
  list(name = "promises", min_version = "1.2.1")
)

# Performance and caching
performance_packages <- list(
  list(name = "memoise", min_version = "2.0.1"),
  list(name = "cachem", min_version = "1.0.8")
)

# Process all package groups
all_package_groups <- list(
  "Core Shiny" = core_packages,
  "Data & API" = data_packages,
  "UI Enhancement" = enhancement_packages,
  "Real-time Features" = realtime_packages,
  "Performance" = performance_packages
)

for (group_name in names(all_package_groups)) {
  cat(paste("\n📋", group_name, "packages:\n"))
  for (pkg_info in all_package_groups[[group_name]]) {
    install_or_update_package(pkg_info$name, pkg_info$min_version, pkg_info$from_github)
  }
}

# Step 4: Update renv snapshot
cat("\n🎯 Step 4: Creating/Updating renv snapshot\n")
renv::snapshot(confirm = FALSE)

# Step 5: Display final package versions
cat("\n🎯 Step 5: Final Package Inventory\n")
cat("==================================\n")

all_packages <- unlist(lapply(all_package_groups, function(group) {
  sapply(group, function(pkg) pkg$name)
}))

for (pkg in all_packages) {
  if (requireNamespace(pkg, quietly = TRUE)) {
    version <- as.character(packageVersion(pkg))
    cat(paste("  ✅", sprintf("%-15s", pkg), "version", version, "\n"))
  } else {
    cat(paste("  ❌", sprintf("%-15s", pkg), "not installed\n"))
  }
}

# Step 6: Verify key package versions meet modern standards
cat("\n🎯 Step 6: Version Compatibility Check\n")
cat("=====================================\n")

version_checks <- list(
  list(name = "shiny", min = "1.8.0", reason = "Latest features and performance improvements"),
  list(name = "bslib", min = "0.6.0", reason = "Bootstrap 5 support and modern theming"),
  list(name = "DT", min = "0.30", reason = "Latest DataTables integration"),
  list(name = "httr2", min = "1.0.0", reason = "Modern HTTP client with better error handling"),
  list(name = "shinyvalidate", min = "0.1.3", reason = "Form validation support")
)

all_compatible <- TRUE
for (check in version_checks) {
  if (requireNamespace(check$name, quietly = TRUE)) {
    current <- as.character(packageVersion(check$name))
    is_compatible <- compareVersion(current, check$min) >= 0
    status <- if (is_compatible) "✅" else "⚠️ "
    cat(paste("  ", status, sprintf("%-15s", check$name), current, 
              if (!is_compatible) paste("(needs >=", check$min, ")") else "", 
              "\n"))
    if (!is_compatible) {
      cat(paste("      Reason:", check$reason, "\n"))
      all_compatible <- FALSE
    }
  } else {
    cat(paste("  ❌", sprintf("%-15s", check$name), "not installed\n"))
    all_compatible <- FALSE
  }
}

# Final status
cat("\n🎉 SETUP COMPLETE\n")
cat("=================\n")

if (all_compatible) {
  cat("✅ All packages are installed with compatible versions!\n")
} else {
  cat("⚠️  Some packages need attention (see above)\n")
}

cat("\n📋 Next Steps:\n")
cat("  1. Run the app: Rscript run_app.R\n")
cat("  2. For other developers: renv::restore()\n")
cat("  3. Check app.R for any additional configuration needed\n")

cat("\n🔧 Environment Features Enabled:\n")
cat("  • Modern bslib Bootstrap 5 theming\n")
cat("  • Form validation with shinyvalidate\n")
cat("  • Real-time WebSocket support\n")
cat("  • Performance caching with memoise\n")
cat("  • Modern HTTP client with httr2\n")
cat("  • Enhanced UI components\n")

cat("\n📊 Total packages installed:", length(all_packages), "\n")
cat("💾 Environment locked in renv.lock for reproducibility\n")