# Test the problematic setNames section
`%||%` <- function(x, y) if (is.null(x) || length(x) == 0) y else x

# Create test data that might cause the issue
result <- list(
  list(id = 1, study_id = 1, database_release_id = 1, database_release_label = NULL),
  list(id = 2, study_id = 2, database_release_id = 2, database_release_label = ""),
  list(id = 3, study_id = 3, database_release_id = 3, database_release_label = "Test")
)

studies_lookup <- list("1" = "Study 1", "2" = "Study 2", "3" = "Study 3")
db_lookup <- list("1" = "Release 1", "2" = "Release 2", "3" = "Release 3")

# Test the setNames construction
choices <- setNames(
  sapply(result, function(x) x$id),
  sapply(result, function(x) {
    study_name <- studies_lookup[[as.character(x$study_id)]] %||% paste0("Study ", x$study_id)
    db_label <- db_lookup[[as.character(x$database_release_id)]] %||% paste0("Release ", x$database_release_id)
    re_label <- x$database_release_label %||% paste0("Effort ", x$id)
    paste0(re_label, " (", study_name, ", ", db_label, ")")
  })
)

choices <- c(setNames("", "Select a Reporting Effort"), choices)
cat("setNames test successful!")
