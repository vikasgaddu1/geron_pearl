reporting_effort_tracker_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns

    # Helpers
    `%||%` <- function(x, y) if (is.null(x) || length(x) == 0) y else x
    
    # Helper function to filter data by comment status
    filter_by_comments <- function(df) {
      if (nrow(df) == 0) return(df)
      
      filter_value <- input$comment_filter %||% "all"
      
      if (filter_value == "all") {
        return(df)
      } else if (filter_value == "has_comments") {
        # Any comments (prog, biostat, both, or resolved)
        return(df[df$Comment_Status != "none", ])
      } else if (filter_value == "prog") {
        # Programming comments (prog or both)
        return(df[df$Comment_Status %in% c("prog", "both"), ])
      } else if (filter_value == "biostat") {
        # Biostat comments (biostat or both)
        return(df[df$Comment_Status %in% c("biostat", "both"), ])
      } else if (filter_value == "none") {
        # No comments
        return(df[df$Comment_Status == "none", ])
      }
      
      return(df)
    }

    # Reactive values
    current_reporting_effort_id <- reactiveVal(NULL)
    reporting_efforts_list <- reactiveVal(list())
    database_releases_lookup <- reactiveVal(list())

    # Single reactive value following the working items module pattern
    tracker_data <- reactiveVal(list())  # Will store tlf_trackers, sdtm_trackers, adam_trackers
    
    # Load users for programmer dropdowns - moved up to ensure it's available early
    programmers_list <- reactiveVal(list())
    
    load_programmers <- function() {
      users_result <- get_users()
      if (!"error" %in% names(users_result) && length(users_result) > 0) {
        # Filter out biostat role users - only keep programmers
        programmers <- list()
        for (user in users_result) {
          if (!is.null(user$role) && tolower(user$role) != "biostat") {
            programmers[[length(programmers) + 1]] <- user
          }
        }
        programmers_list(programmers)
      }
    }

    # Load reporting efforts for dropdown (same labelling as items)
    load_reporting_efforts <- function() {
      result <- get_reporting_efforts()
      if ("error" %in% names(result)) {
        show_error_notification(paste("Error loading reporting efforts:", result$error))
        reporting_efforts_list(list())
        updateSelectInput(session, "selected_reporting_effort", choices = list("Select a Reporting Effort" = ""))
      } else {
        reporting_efforts_list(result)

        studies_result <- get_studies()
        studies_lookup <- list()
        if (!("error" %in% names(studies_result))) {
          for (study in studies_result) {
            studies_lookup[[as.character(study$id)]] <- study$title
          }
        }

        db_rel_result <- get_database_releases()
        db_lookup <- list()
        if (!("error" %in% names(db_rel_result))) {
          for (rel in db_rel_result) {
            db_lookup[[as.character(rel$id)]] <- rel$database_release_label
          }
        }
        database_releases_lookup(db_lookup)

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
        updateSelectInput(session, "selected_reporting_effort", choices = choices)
      }
    }

    # Initial loads
    observe(load_programmers())
    observe(load_reporting_efforts())
    
    # WebSocket connection diagnostic (helps debug cross-browser issues)
    observe({
      invalidateLater(15000, session)  # Check every 15 seconds
      
      tryCatch({
        session$sendCustomMessage("websocket_debug_info", list(
          timestamp = as.character(Sys.time()),
          session_token = session$token,
          check_type = "periodic"
        ))
      }, error = function(e) {
        cat("DEBUG: WebSocket diagnostic error:", e$message, "\n")
      })
    })

    # Update highlight class when selection changes
    observeEvent(input$selected_reporting_effort, {
      eff_id <- input$selected_reporting_effort
      current_reporting_effort_id(if (identical(eff_id, "")) NULL else eff_id)
      session$sendCustomMessage("toggleEffortSelection", list(
        selector_id = ns("effort_selector_wrapper"), has_selection = !is.null(current_reporting_effort_id())
      ))
      # Reload all three tables
      tryCatch({
        load_tracker_tables()
      }, error = function(e) {
        show_error_notification(paste("ERROR in load_tracker_tables():", e$message), duration = 10000)
      })
      # Note: effort labels are now reactive and will update automatically
    }, ignoreInit = TRUE)

    # Effort label outputs - make reactive to table data using new pattern
    output$effort_label_tlf <- renderUI({
      eff_id <- current_reporting_effort_id()
      if (is.null(eff_id)) return(HTML(""))
      
      # Get data from single reactive value like items module
      data_list <- tracker_data()
      tlf_rows <- if (is.list(data_list) && !is.null(data_list$tlf_trackers)) nrow(data_list$tlf_trackers) else 0
      sdtm_rows <- if (is.list(data_list) && !is.null(data_list$sdtm_trackers)) nrow(data_list$sdtm_trackers) else 0  
      adam_rows <- if (is.list(data_list) && !is.null(data_list$adam_trackers)) nrow(data_list$adam_trackers) else 0
      
      # Find selected label
      eff <- NULL
      for (x in reporting_efforts_list()) if (as.character(x$id) == as.character(eff_id)) eff <- x
      
      # Add debug info to label to trace execution
      debug_info <- paste("DEBUG: Tables - TLF:", tlf_rows, "SDTM:", sdtm_rows, "ADaM:", adam_rows)
      
      lbl <- if (!is.null(eff)) {
        paste0("Current Reporting Effort: ",
               (eff$database_release_label %||% paste0("Effort ", eff$id)),
               " (", eff$study_title %||% (eff$study_id %||% ""), ", ",
               eff$database_release_label %||% (eff$database_release_id %||% ""), ") - ", debug_info)
      } else debug_info
      tags$div(class = "text-muted small fw-semibold", lbl)
    })
    
    output$effort_label_sdtm <- renderUI({
      eff_id <- current_reporting_effort_id()
      if (is.null(eff_id)) return(HTML(""))
      
      # Get data from single reactive value
      data_list <- tracker_data()
      tlf_rows <- if (is.list(data_list) && !is.null(data_list$tlf_trackers)) nrow(data_list$tlf_trackers) else 0
      sdtm_rows <- if (is.list(data_list) && !is.null(data_list$sdtm_trackers)) nrow(data_list$sdtm_trackers) else 0  
      adam_rows <- if (is.list(data_list) && !is.null(data_list$adam_trackers)) nrow(data_list$adam_trackers) else 0
      
      # Find selected label
      eff <- NULL
      for (x in reporting_efforts_list()) if (as.character(x$id) == as.character(eff_id)) eff <- x
      
      # Add debug info to label to trace execution  
      debug_info <- paste("DEBUG: Tables - TLF:", tlf_rows, "SDTM:", sdtm_rows, "ADaM:", adam_rows)
      
      lbl <- if (!is.null(eff)) {
        paste0("Current Reporting Effort: ",
               (eff$database_release_label %||% paste0("Effort ", eff$id)),
               " (", eff$study_title %||% (eff$study_id %||% ""), ", ",
               eff$database_release_label %||% (eff$database_release_id %||% ""), ") - ", debug_info)
      } else debug_info
      tags$div(class = "text-muted small fw-semibold", lbl)
    })
    
    output$effort_label_adam <- renderUI({
      eff_id <- current_reporting_effort_id()
      if (is.null(eff_id)) return(HTML(""))
      
      # Get data from single reactive value
      data_list <- tracker_data()
      tlf_rows <- if (is.list(data_list) && !is.null(data_list$tlf_trackers)) nrow(data_list$tlf_trackers) else 0
      sdtm_rows <- if (is.list(data_list) && !is.null(data_list$sdtm_trackers)) nrow(data_list$sdtm_trackers) else 0  
      adam_rows <- if (is.list(data_list) && !is.null(data_list$adam_trackers)) nrow(data_list$adam_trackers) else 0
      
      # Find selected label
      eff <- NULL
      for (x in reporting_efforts_list()) if (as.character(x$id) == as.character(eff_id)) eff <- x
      
      # Add debug info to label to trace execution
      debug_info <- paste("DEBUG: Tables - TLF:", tlf_rows, "SDTM:", sdtm_rows, "ADaM:", adam_rows)
      
      lbl <- if (!is.null(eff)) {
        paste0("Current Reporting Effort: ",
               (eff$database_release_label %||% paste0("Effort ", eff$id)),
               " (", eff$study_title %||% (eff$study_id %||% ""), ", ",
               eff$database_release_label %||% (eff$database_release_id %||% ""), ") - ", debug_info)
      } else debug_info
      tags$div(class = "text-muted small fw-semibold", lbl)
    })

    # Load tracker tables based on items of selected effort
    load_tracker_tables <- function() {
      eff_id <- current_reporting_effort_id()
      show_success_notification(paste("Loading tracker data for effort ID:", eff_id), duration = 3000)
      
      if (is.null(eff_id)) {
        tracker_data(list())  # Clear single reactive value
        return()
      }

      items <- get_reporting_effort_items_by_effort(eff_id)
      
      if ("error" %in% names(items)) {
        show_error_notification(paste("Error loading items for trackers:", items$error))
        tracker_data(list())  # Clear single reactive value on error
        return()
      }
      
      show_success_notification(paste("Found", length(items), "items to process"), duration = 3000)

      # Split items by subtype for Dataset and by type for TLFs
      # We will build simple frames with inline actions
      build_row <- function(item) {
        cat("DEBUG: Building row for item ID:", item$id, "code:", item$item_code, "\n")
        tracker <- tryCatch({
          result <- get_tracker_by_item(item$id)
          cat("DEBUG: Tracker API result for item", item$id, "- keys:", names(result), "\n")
          if ("error" %in% names(result)) {
            cat("DEBUG: Tracker API error:", result$error, "\n")
            list()
          } else {
            result
          }
        }, error = function(e) {
          cat("DEBUG: Exception getting tracker for item", item$id, ":", e$message, "\n")
          list()
        })
        tracker_id <- if (!is.null(tracker$id)) tracker$id else ""
        cat("DEBUG: Tracker ID:", tracker_id, "for item", item$id, "\n")
        # Map backend enum values to display values
        prod_status_map <- list(
          "not_started" = "Not Started",
          "in_progress" = "In Progress", 
          "completed" = "Completed",
          "on_hold" = "On Hold"
        )
        qc_status_map <- list(
          "not_started" = "Not Started",
          "in_progress" = "In Progress",
          "completed" = "Completed", 
          "failed" = "Failed"
        )
        
        prod_status <- prod_status_map[[tracker$production_status %||% "not_started"]] %||% "Not Started"
        qc_status <- qc_status_map[[tracker$qc_status %||% "not_started"]] %||% "Not Started"
        priority <- tracker$priority %||% "medium"
        qc_level <- tracker$qc_level %||% "3"
        due_date <- tracker$due_date %||% ""
        qc_done <- tracker$qc_completion_date %||% ""
        
        # Get usernames for programmers
        prod_prog <- "Not Assigned"
        qc_prog <- "Not Assigned"
        
        # Look up programmer usernames from the users list
        progs <- programmers_list()
        if (length(progs) > 0 && !is.null(tracker$production_programmer_id)) {
          for (prog in progs) {
            if (as.character(prog$id) == as.character(tracker$production_programmer_id)) {
              prod_prog <- prog$username
              break
            }
          }
        }
        if (length(progs) > 0 && !is.null(tracker$qc_programmer_id)) {
          for (prog in progs) {
            if (as.character(prog$id) == as.character(tracker$qc_programmer_id)) {
              qc_prog <- prog$username
              break
            }
          }
        }
        # Create simplified comments column with modal trigger button
        # Default: gray outline (no comments), then colored based on comment types
        # Shows separate badges for Programming (P:N yellow) and Biostat (B:N blue) comments
        
        # Get comment summary for dropdown filtering
        comment_status <- "none"  # Default: no comments
        if (!is.null(tracker_id) && !is.na(tracker_id) && tracker_id != "") {
          comment_summary <- tryCatch({
            get_tracker_comment_summary(tracker_id)
          }, error = function(e) list())
          
          prog_count <- comment_summary$programming_unresolved_count %||% 0
          biostat_count <- comment_summary$biostat_unresolved_count %||% 0
          total_count <- comment_summary$total_comments %||% 0
          
          if (prog_count > 0 && biostat_count > 0) {
            comment_status <- "both"
          } else if (prog_count > 0) {
            comment_status <- "prog"
          } else if (biostat_count > 0) {
            comment_status <- "biostat"
          } else if (total_count > 0) {
            comment_status <- "resolved"
          }
        }
        
        comments_column <- if (!is.null(tracker_id) && !is.na(tracker_id) && tracker_id != "") {
          sprintf('<div class="comment-column" data-tracker-id="%s">
                     <button class="btn btn-outline-secondary btn-sm comment-btn" data-tracker-id="%s" 
                             onclick="showSimplifiedCommentModal(%s)" 
                             title="No comments yet">
                       <i class="fa fa-comment-o"></i>
                       <span class="comment-badge-prog badge bg-warning text-dark ms-1" style="display: none;"></span>
                       <span class="comment-badge-biostat badge bg-info text-white ms-1" style="display: none;"></span>
                     </button>
                   </div>', tracker_id, tracker_id, tracker_id)
        } else {
          '<div class="comment-column">
             <button class="btn btn-outline-secondary btn-sm" disabled title="Create tracker first">
               <i class="fa fa-plus"></i>
             </button>
           </div>'
        }
        
        actions <- sprintf(
          '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="%s" data-item-id="%s" title="Edit tracker"><i class="fa fa-pencil"></i></button>
           <button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="%s" data-item-id="%s" title="Delete tracker"><i class="fa fa-trash"></i></button>',
          tracker_id %||% "", item$id, tracker_id %||% "", item$id)
        data.frame(
          Tracker_ID = tracker_id %||% "",  # Hidden column for bulk selection
          Item_ID = item$id %||% "",  # Hidden column for bulk selection
          Item = item$item_code %||% "",
          Category = item$item_subtype %||% "",
          Prod_Programmer = prod_prog,
          Prod_Status = prod_status,
          Priority = priority,
          Due_Date = due_date,
          QC_Programmer = qc_prog,
          QC_Status = qc_status,
          QC_Level = qc_level,
          QC_Completion = qc_done,
          Comments = comments_column,
          Actions = actions,
          Comment_Status = comment_status,  # Hidden column for filtering
          stringsAsFactors = FALSE
        )
      }

      tlf_rows <- list()
      sdtm_rows <- list()
      adam_rows <- list()
      for (it in items) {
        # Check if item has a tracker before building row
        tracker_check <- tryCatch({
          result <- get_tracker_by_item(it$id)
          if ("error" %in% names(result) || length(result) == 0) {
            NULL  # No tracker exists
          } else {
            result  # Tracker exists
          }
        }, error = function(e) {
          NULL  # Error means no tracker
        })
        
        # Only build row if tracker exists
        if (!is.null(tracker_check)) {
          if (it$item_type == "TLF") {
            tlf_rows[[length(tlf_rows) + 1]] <- build_row(it)
          } else if (it$item_type == "Dataset") {
            # Map dataset subtypes SDTM/ADaM from item_subtype
            if (tolower(it$item_subtype) == "sdtm") {
              sdtm_rows[[length(sdtm_rows) + 1]] <- build_row(it)
            } else {
              adam_rows[[length(adam_rows) + 1]] <- build_row(it)
            }
          }
        }
      }

      to_df <- function(rows) {
        if (length(rows)) {
          do.call(rbind, rows)
        } else {
          data.frame(Item=character(0), Category=character(0), Prod_Programmer=character(0), Prod_Status=character(0), Priority=character(0), Due_Date=character(0), QC_Programmer=character(0), QC_Status=character(0), QC_Level=character(0), QC_Completion=character(0), Comments=character(0), Actions=character(0), Comment_Status=character(0), stringsAsFactors = FALSE)
        }
      }
      
      tlf_df <- to_df(tlf_rows)
      sdtm_df <- to_df(sdtm_rows) 
      adam_df <- to_df(adam_rows)
      
      # Store in single reactive value following items module pattern
      combined_tracker_data <- list()
      combined_tracker_data$tlf_trackers <- tlf_df
      combined_tracker_data$sdtm_trackers <- sdtm_df  
      combined_tracker_data$adam_trackers <- adam_df
      
      tracker_data(combined_tracker_data)
      
      # Get comment summaries for all trackers and update badges
      tryCatch({
        # Collect all tracker IDs from the data
        all_tracker_ids <- c()
        for (it in items) {
          tracker <- tryCatch({
            get_tracker_by_item(it$id)
          }, error = function(e) list())
          if (!is.null(tracker$id) && !is.na(tracker$id)) {
            all_tracker_ids <- c(all_tracker_ids, tracker$id)
          }
        }
        
        if (length(all_tracker_ids) > 0) {
          cat("DEBUG: Calling get_tracker_comments_summary with tracker IDs:", paste(all_tracker_ids, collapse = ", "), "\n")
          # Get comment summaries
          summaries <- get_tracker_comments_summary(all_tracker_ids)
          
          cat("DEBUG: API response:", str(summaries), "\n")
          
          if (!("error" %in% names(summaries))) {
            cat("DEBUG: Sending updateCommentBadges message to JavaScript with delay\n")
            # Delay badge update to ensure DataTable DOM is fully rendered
            shinyjs::delay(500, {
              session$sendCustomMessage("updateCommentBadges", list(
                summaries = summaries
              ))
            })
          } else {
            cat("DEBUG: Error in summaries response:", summaries$error, "\n")
          }
        } else {
          cat("DEBUG: No tracker IDs found, skipping badge update\n")
        }
      }, error = function(e) {
        cat("ERROR: Failed to get comment summaries:", e$message, "\n")
      })
      
      # Show progress notification
      show_success_notification(paste("Created tables - TLF:", nrow(tlf_df), "rows, SDTM:", nrow(sdtm_df), "rows, ADaM:", nrow(adam_df), "rows"), duration = 5000)
    }

    # Function to update badges for a single tracker (efficient WebSocket updates)
    update_single_tracker_badges <- function(tracker_id) {
      tryCatch({
        cat("DEBUG: Updating badges for single tracker:", tracker_id, "\n")
        
        # Get comment summary for just this tracker
        summary <- get_tracker_comments_summary(c(tracker_id))
        
        if (!("error" %in% names(summary)) && length(summary) > 0) {
          cat("DEBUG: Got summary for tracker", tracker_id, "- sending to JS\n")
          session$sendCustomMessage("updateCommentBadges", list(
            summaries = summary
          ))
        } else {
          cat("DEBUG: No summary data available for tracker", tracker_id, "\n")
        }
      }, error = function(e) {
        cat("ERROR: Failed to update single tracker badges:", e$message, "\n")
      })
    }
    
    # Optimistic comment creation with immediate badge update
    create_comment_with_optimistic_update <- function(tracker_id, comment_text, comment_type = "qc_comment", user_id = 1, user_role = "USER") {
      tryCatch({
        cat("DEBUG: Creating comment with optimistic update for tracker", tracker_id, "\n")
        
        # 1. Immediately update badge optimistically
        session$sendCustomMessage("updateCommentBadgeRealtime", list(
          tracker_id = tracker_id,
          event_type = "comment_created",
          comment_data = list(
            is_resolved = FALSE,  # New comments are unresolved by default
            is_pinned = FALSE,
            comment_type = comment_type
          )
        ))
        
        # 2. Create the actual comment via API
        result <- create_tracker_comment(tracker_id, comment_text, comment_type, user_id, user_role)
        
        if ("error" %in% names(result)) {
          # If API call failed, revert the optimistic update
          cat("ERROR: Comment creation failed, reverting optimistic update:", result$error, "\n")
          session$sendCustomMessage("updateCommentBadgeRealtime", list(
            tracker_id = tracker_id,
            event_type = "comment_deleted",  # Revert the addition
            comment_data = list(
              is_resolved = FALSE,
              is_pinned = FALSE
            )
          ))
          
          show_error_notification(paste("Failed to create comment:", result$error))
          return(result)
        }
        
        # 3. Success! The WebSocket will handle the authoritative update from other clients
        cat("DEBUG: Comment created successfully, WebSocket will sync across clients\n")
        show_success_notification("Comment added successfully", duration = 3000)
        
        return(result)
        
      }, error = function(e) {
        cat("ERROR: Exception in optimistic comment creation:", e$message, "\n")
        # Revert optimistic update on error
        session$sendCustomMessage("updateCommentBadgeRealtime", list(
          tracker_id = tracker_id,
          event_type = "comment_deleted",  # Revert the addition
          comment_data = list(
            is_resolved = FALSE,
            is_pinned = FALSE
          )
        ))
        
        show_error_notification(paste("Error creating comment:", e$message))
        return(list(error = e$message))
      })
    }

    # Create single container function for consistency
    create_tracker_container <- function() {
      htmltools::withTags(table(
        class = 'display',
        thead(
          tr(
            th(rowspan = 2, 'Item'),
            th(rowspan = 2, 'Category'),
            th(colspan = 4, 'Production', style = 'text-align: center; background-color: #f8f9fa;'),
            th(colspan = 4, 'QC', style = 'text-align: center; background-color: #e9ecef;'),
            th(rowspan = 2, 'Comments'),
            th(rowspan = 2, 'Actions')
          ),
          tr(
            th('Programmer'),
            th('Status'),
            th('Priority'),
            th('Due Date'),
            th('Programmer'),
            th('Status'),
            th('QC Level'),
            th('QC Completion')
          )
        )
      ))
    }

    # Render TLF Tracker Table (following items module pattern)
    output$tracker_table_tlf <- DT::renderDT({
      eff_id <- current_reporting_effort_id()
      data_list <- tracker_data()
      cat("DEBUG: Rendering TLF tracker table\n")

      # Check if a reporting effort is selected
      if (is.null(eff_id)) {
        # No reporting effort selected - show empty table
        empty_df <- data.frame(
          Tracker_ID = character(0),
          Item_ID = character(0),
          Item = character(0),
          Category = character(0),
          Prod_Programmer = character(0),
          Prod_Status = character(0),
          Priority = character(0),
          Due_Date = character(0),
          QC_Programmer = character(0),
          QC_Status = character(0),
          QC_Level = character(0),
          QC_Completion = character(0),
          Comments = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE
        )

        return(DT::datatable(
          empty_df,
          container = create_tracker_container(),
          filter = 'top',
          options = list(
            dom = 'rtip',
            pageLength = 25,
            columnDefs = list(
              list(targets = c(0, 1), visible = FALSE)  # Hide Tracker_ID and Item_ID columns
            ),
            language = list(emptyTable = "Please select a reporting effort to view tracker items")
          ),
          escape = FALSE, rownames = FALSE
        ))
      }
      
      # Get TLF tracker data from the list structure
      tlf_data <- if (is.list(data_list) && !is.null(data_list$tlf_trackers)) {
        data_list$tlf_trackers
      } else {
        data.frame()
      }
      cat("DEBUG: TLF tracker data rows:", nrow(tlf_data), "\n")
      
      if (nrow(tlf_data) == 0 && !is.null(eff_id)) {
        cat("DEBUG: No TLF tracker data - adding dummy data\n")
        # Add dummy data for demonstration only when effort is selected
        tlf_data <- data.frame(
          Tracker_ID = c("", "", ""),  # Empty for dummy data
          Item_ID = c("dummy1", "dummy2", "dummy3"),
          Item = c("T14.1.1", "T14.2.1", "F9.1.1"),
          Category = c("Table", "Table", "Figure"),
          Prod_Programmer = c("Not Assigned", "Not Assigned", "Not Assigned"),
          Prod_Status = c("Not Started", "Not Started", "Not Started"),
          Priority = c("high", "medium", "low"),
          Due_Date = c("", "", ""),
          QC_Programmer = c("Not Assigned", "Not Assigned", "Not Assigned"),
          QC_Status = c("Not Started", "Not Started", "Not Started"),
          QC_Level = c("3", "3", "3"),
          QC_Completion = c("", "", ""),
          Comments = c(
            '<div class="comment-column"><button class="btn btn-outline-secondary btn-sm" disabled title="Create tracker first"><i class="fa fa-plus"></i></button></div>',
            '<div class="comment-column"><button class="btn btn-outline-secondary btn-sm" disabled title="Create tracker first"><i class="fa fa-plus"></i></button></div>',
            '<div class="comment-column"><button class="btn btn-outline-secondary btn-sm" disabled title="Create tracker first"><i class="fa fa-plus"></i></button></div>'
          ),
          Actions = c(
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="" data-item-id="dummy1" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="" data-item-id="dummy1" title="Delete tracker"><i class="fa fa-trash"></i></button>',
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="" data-item-id="dummy2" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="" data-item-id="dummy2" title="Delete tracker"><i class="fa fa-trash"></i></button>',
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="" data-item-id="dummy3" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="" data-item-id="dummy3" title="Delete tracker"><i class="fa fa-trash"></i></button>'
          ),
          Comment_Status = c("none", "none", "none"),
          stringsAsFactors = FALSE
        )
      }
      
      # Apply comment filter
      tlf_data <- filter_by_comments(tlf_data)

      # Remove Comment_Status column before display (keep Tracker_ID and Item_ID for selection)
      display_data <- if (nrow(tlf_data) > 0 && "Comment_Status" %in% names(tlf_data)) {
        tlf_data[, !names(tlf_data) %in% "Comment_Status", drop = FALSE]
      } else {
        tlf_data
      }

      if (TRUE) {  # Always render with the same configuration
        cat("DEBUG: Rendering TLF tracker table with data, rows:", nrow(display_data), "\n")

        DT::datatable(
          display_data,
          container = create_tracker_container(),
          filter = 'top',
          options = list(
            dom = 'rtip',
            pageLength = 25,
            ordering = TRUE,
            autoWidth = TRUE,
            search = list(regex = TRUE, caseInsensitive = TRUE),
            columnDefs = list(
              list(targets = c(0, 1), visible = FALSE),  # Hide Tracker_ID and Item_ID columns
              list(targets = ncol(display_data) - 2, searchable = FALSE, orderable = FALSE, width = "120px"),  # Comments column
              list(targets = ncol(display_data) - 1, searchable = FALSE, orderable = FALSE)  # Actions column
            ),
            drawCallback = JS(sprintf(
              "function(settings){
                var api = this.api();
                var tbl = $(api.table().node()).closest('.dataTables_wrapper').find('table');

                // Edit/Delete button handlers - use event.stopPropagation to prevent comment modal from opening
                tbl.find('button[data-action=\\'edit\\']').off('click').on('click', function(e){
                  e.stopPropagation();
                  e.preventDefault();
                  var id = $(this).attr('data-id');
                  var itemId = $(this).attr('data-item-id');
                  console.log('TLF Edit clicked: tracker_id=' + id + ', item_id=' + itemId);
                  Shiny.setInputValue('%s', {action: 'edit', id: id, itemId: itemId}, {priority: 'event'});
                });
                tbl.find('button[data-action=\\'delete\\']').off('click').on('click', function(e){
                  e.stopPropagation();
                  e.preventDefault();
                  var id = $(this).attr('data-id');
                  var itemId = $(this).attr('data-item-id');
                  Shiny.setInputValue('%s', {action: 'delete', id: id, itemId: itemId}, {priority: 'event'});
                });

                // Refresh comment badges after table draw
                if (typeof refreshAllCommentBadges === 'function') {
                  setTimeout(refreshAllCommentBadges, 100);
                }
              }",
              ns("tracker_action"), ns("tracker_action")))
          ),
          escape = FALSE, rownames = FALSE
        )
      }
    }, selection = list(mode = 'multiple', target = 'row'))

    # Render SDTM Tracker Table
    output$tracker_table_sdtm <- DT::renderDT({
      eff_id <- current_reporting_effort_id()
      data_list <- tracker_data()
      cat("DEBUG: Rendering SDTM tracker table\n")

      # Check if a reporting effort is selected
      if (is.null(eff_id)) {
        # No reporting effort selected - show empty table
        empty_df <- data.frame(
          Tracker_ID = character(0),
          Item_ID = character(0),
          Item = character(0),
          Category = character(0),
          Prod_Programmer = character(0),
          Prod_Status = character(0),
          Priority = character(0),
          Due_Date = character(0),
          QC_Programmer = character(0),
          QC_Status = character(0),
          QC_Level = character(0),
          QC_Completion = character(0),
          Comments = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE
        )

        return(DT::datatable(
          empty_df,
          container = create_tracker_container(),
          filter = 'top',
          options = list(
            dom = 'frtip',
            pageLength = 25,
            columnDefs = list(
              list(targets = c(0, 1), visible = FALSE)  # Hide Tracker_ID and Item_ID columns
            ),
            search = list(regex = TRUE, caseInsensitive = TRUE),
            language = list(emptyTable = "Please select a reporting effort to view tracker items")
          ),
          escape = FALSE, rownames = FALSE
        ))
      }

      sdtm_data <- if (is.list(data_list) && !is.null(data_list$sdtm_trackers)) {
        data_list$sdtm_trackers
      } else {
        data.frame()
      }
      cat("DEBUG: SDTM tracker data rows:", nrow(sdtm_data), "\n")

      if (nrow(sdtm_data) == 0 && !is.null(eff_id)) {
        # Add dummy SDTM data with new status values
        sdtm_data <- data.frame(
          Tracker_ID = c("", "", ""),  # Empty for dummy data
          Item_ID = c("sdtm1", "sdtm2", "sdtm3"),
          Item = c("DM", "AE", "CM"),
          Category = c("SDTM", "SDTM", "SDTM"),
          Prod_Programmer = c("Not Assigned", "Not Assigned", "Not Assigned"),
          Prod_Status = c("Not Started", "Not Started", "Not Started"),
          Priority = c("High", "High", "Medium"),
          Due_Date = c("", "", ""),
          QC_Programmer = c("Not Assigned", "Not Assigned", "Not Assigned"),
          QC_Status = c("Not Started", "Not Started", "Not Started"),
          QC_Level = c("3", "3", "3"),
          QC_Completion = c("", "", ""),
          Comments = c(
            '<div class="comment-column"><button class="btn btn-outline-secondary btn-sm" disabled title="Create tracker first"><i class="fa fa-plus"></i></button></div>',
            '<div class="comment-column"><button class="btn btn-outline-secondary btn-sm" disabled title="Create tracker first"><i class="fa fa-plus"></i></button></div>',
            '<div class="comment-column"><button class="btn btn-outline-secondary btn-sm" disabled title="Create tracker first"><i class="fa fa-plus"></i></button></div>'
          ),
          Actions = c(
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="" data-item-id="sdtm1" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="" data-item-id="sdtm1" title="Delete tracker"><i class="fa fa-trash"></i></button>',
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="" data-item-id="sdtm2" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="" data-item-id="sdtm2" title="Delete tracker"><i class="fa fa-trash"></i></button>',
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="" data-item-id="sdtm3" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="" data-item-id="sdtm3" title="Delete tracker"><i class="fa fa-trash"></i></button>'
          ),
          Comment_Status = c("none", "none", "none"),
          stringsAsFactors = FALSE
        )
      }

      # Apply comment filter
      sdtm_data <- filter_by_comments(sdtm_data)

      # Remove Comment_Status column before display
      display_data <- if (nrow(sdtm_data) > 0 && "Comment_Status" %in% names(sdtm_data)) {
        sdtm_data[, !names(sdtm_data) %in% "Comment_Status", drop = FALSE]
      } else {
        sdtm_data
      }

      # Always render with consistent configuration
      cat("DEBUG: Rendering SDTM tracker table with data, rows:", nrow(display_data), "\n")

      DT::datatable(
        display_data,
        container = create_tracker_container(),
        filter = 'top',
        options = list(
          dom = 'frtip',
          pageLength = 25,
          search = list(regex = TRUE, caseInsensitive = TRUE),
          ordering = TRUE,
          autoWidth = TRUE,
          columnDefs = list(
            list(targets = c(0, 1), visible = FALSE),  # Hide Tracker_ID and Item_ID columns
            list(targets = ncol(display_data) - 2, searchable = FALSE, orderable = FALSE, width = "120px"),  # Comments column
            list(targets = ncol(display_data) - 1, searchable = FALSE, orderable = FALSE)  # Actions column
          ),
          drawCallback = JS(sprintf(
            "function(settings){
              var api = this.api();
              var tbl = $(api.table().node()).closest('.dataTables_wrapper').find('table');

              // Edit/Delete button handlers - use event.stopPropagation to prevent comment modal from opening
              tbl.find('button[data-action=\\'edit\\']').off('click').on('click', function(e){
                e.stopPropagation();
                e.preventDefault();
                var id = $(this).attr('data-id');
                var itemId = $(this).attr('data-item-id');
                console.log('SDTM Edit clicked: tracker_id=' + id + ', item_id=' + itemId);
                Shiny.setInputValue('%s', {action: 'edit', id: id, itemId: itemId}, {priority: 'event'});
              });
              tbl.find('button[data-action=\\'delete\\']').off('click').on('click', function(e){
                e.stopPropagation();
                e.preventDefault();
                var id = $(this).attr('data-id');
                var itemId = $(this).attr('data-item-id');
                Shiny.setInputValue('%s', {action: 'delete', id: id, itemId: itemId}, {priority: 'event'});
              });

              // Comment modal button handlers
              tbl.find('.comment-btn').off('click').on('click', function(){
                var trackerId = $(this).attr('data-tracker-id');
                showSimplifiedCommentModal(trackerId);
              });

              // Refresh comment badges after table draw
              if (typeof refreshAllCommentBadges === 'function') {
                setTimeout(refreshAllCommentBadges, 100);
              }
            }",
            ns("tracker_action"), ns("tracker_action")))
        ),
        escape = FALSE, rownames = FALSE
      )
    }, selection = list(mode = 'multiple', target = 'row'))

    # Render ADaM Tracker Table
    output$tracker_table_adam <- DT::renderDT({
      eff_id <- current_reporting_effort_id()
      data_list <- tracker_data()
      cat("DEBUG: Rendering ADaM tracker table\n")

      # Check if a reporting effort is selected
      if (is.null(eff_id)) {
        # No reporting effort selected - show empty table
        empty_df <- data.frame(
          Tracker_ID = character(0),
          Item_ID = character(0),
          Item = character(0),
          Category = character(0),
          Prod_Programmer = character(0),
          Prod_Status = character(0),
          Priority = character(0),
          Due_Date = character(0),
          QC_Programmer = character(0),
          QC_Status = character(0),
          QC_Level = character(0),
          QC_Completion = character(0),
          Comments = character(0),
          Actions = character(0),
          stringsAsFactors = FALSE
        )

        return(DT::datatable(
          empty_df,
          container = create_tracker_container(),
          filter = 'top',
          options = list(
            dom = 'frtip',
            pageLength = 25,
            columnDefs = list(
              list(targets = c(0, 1), visible = FALSE)  # Hide Tracker_ID and Item_ID columns
            ),
            search = list(regex = TRUE, caseInsensitive = TRUE),
            language = list(emptyTable = "Please select a reporting effort to view tracker items")
          ),
          escape = FALSE, rownames = FALSE
        ))
      }

      adam_data <- if (is.list(data_list) && !is.null(data_list$adam_trackers)) {
        data_list$adam_trackers
      } else {
        data.frame()
      }
      cat("DEBUG: ADaM tracker data rows:", nrow(adam_data), "\n")

      if (nrow(adam_data) == 0 && !is.null(eff_id)) {
        # Add dummy ADaM data with new status values
        adam_data <- data.frame(
          Tracker_ID = c("", "", ""),  # Empty for dummy data
          Item_ID = c("adam1", "adam2", "adam3"),
          Item = c("ADSL", "ADAE", "ADEFF"),
          Category = c("ADaM", "ADaM", "ADaM"),
          Prod_Programmer = c("Not Assigned", "Not Assigned", "Not Assigned"),
          Prod_Status = c("Not Started", "Not Started", "Not Started"),
          Priority = c("High", "Medium", "Medium"),
          Due_Date = c("", "", ""),
          QC_Programmer = c("Not Assigned", "Not Assigned", "Not Assigned"),
          QC_Status = c("Not Started", "Not Started", "Not Started"),
          QC_Level = c("3", "3", "3"),
          QC_Completion = c("", "", ""),
          Comments = c(
            '<div class="comment-column"><button class="btn btn-outline-secondary btn-sm" disabled title="Create tracker first"><i class="fa fa-plus"></i></button></div>',
            '<div class="comment-column"><button class="btn btn-outline-secondary btn-sm" disabled title="Create tracker first"><i class="fa fa-plus"></i></button></div>',
            '<div class="comment-column"><button class="btn btn-outline-secondary btn-sm" disabled title="Create tracker first"><i class="fa fa-plus"></i></button></div>'
          ),
          Actions = c(
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="" data-item-id="adam1" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="" data-item-id="adam1" title="Delete tracker"><i class="fa fa-trash"></i></button>',
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="" data-item-id="adam2" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="" data-item-id="adam2" title="Delete tracker"><i class="fa fa-trash"></i></button>',
            '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="" data-item-id="adam3" title="Edit tracker"><i class="fa fa-pencil"></i></button><button class="btn btn-danger btn-sm me-1" data-action="delete" data-id="" data-item-id="adam3" title="Delete tracker"><i class="fa fa-trash"></i></button>'
          ),
          Comment_Status = c("none", "none", "none"),
          stringsAsFactors = FALSE
        )
      }

      # Apply comment filter
      adam_data <- filter_by_comments(adam_data)

      # Remove Comment_Status column before display
      display_data <- if (nrow(adam_data) > 0 && "Comment_Status" %in% names(adam_data)) {
        adam_data[, !names(adam_data) %in% "Comment_Status", drop = FALSE]
      } else {
        adam_data
      }

      # Always render with consistent configuration
      cat("DEBUG: Rendering ADaM tracker table with data, rows:", nrow(display_data), "\n")

      DT::datatable(
        display_data,
        container = create_tracker_container(),
        filter = 'top',
        options = list(
          dom = 'frtip',
          pageLength = 25,
          search = list(regex = TRUE, caseInsensitive = TRUE),
          ordering = TRUE,
          autoWidth = TRUE,
          columnDefs = list(
            list(targets = c(0, 1), visible = FALSE),  # Hide Tracker_ID and Item_ID columns
            list(targets = ncol(display_data) - 2, searchable = FALSE, orderable = FALSE, width = "120px"),  # Comments column
            list(targets = ncol(display_data) - 1, searchable = FALSE, orderable = FALSE)  # Actions column
          ),
          drawCallback = JS(sprintf(
            "function(settings){
              var api = this.api();
              var tbl = $(api.table().node()).closest('.dataTables_wrapper').find('table');

              // Edit/Delete button handlers - use event.stopPropagation to prevent comment modal from opening
              tbl.find('button[data-action=\\'edit\\']').off('click').on('click', function(e){
                e.stopPropagation();
                e.preventDefault();
                var id = $(this).attr('data-id');
                var itemId = $(this).attr('data-item-id');
                console.log('ADaM Edit clicked: tracker_id=' + id + ', item_id=' + itemId);
                Shiny.setInputValue('%s', {action: 'edit', id: id, itemId: itemId}, {priority: 'event'});
              });
              tbl.find('button[data-action=\\'delete\\']').off('click').on('click', function(e){
                e.stopPropagation();
                e.preventDefault();
                var id = $(this).attr('data-id');
                var itemId = $(this).attr('data-item-id');
                Shiny.setInputValue('%s', {action: 'delete', id: id, itemId: itemId}, {priority: 'event'});
              });

              // Comment modal button handlers
              tbl.find('.comment-btn').off('click').on('click', function(){
                var trackerId = $(this).attr('data-tracker-id');
                showSimplifiedCommentModal(trackerId);
              });

              // Refresh comment badges after table draw
              if (typeof refreshAllCommentBadges === 'function') {
                setTimeout(refreshAllCommentBadges, 100);
              }
            }",
            ns("tracker_action"), ns("tracker_action")))
        ),
        escape = FALSE, rownames = FALSE
      )
    }, selection = list(mode = 'multiple', target = 'row'))

    # Reactive values to store modal data
    modal_tracker_id <- reactiveVal(NULL)
    modal_item_id <- reactiveVal(NULL)
    
    # Comment modal observer - triggered by JavaScript
    observeEvent(input$comment_modal_trigger, {
      if (!is.null(input$comment_modal_trigger)) {
        tracker_id <- input$comment_modal_trigger$tracker_id
        cat("DEBUG: Comment modal triggered for tracker ID:", tracker_id, "\n")
        
        # Show the simplified comment modal
        showModal(create_view_modal(
          title = tagList(
            tags$i(class = "fa fa-comments me-2"),
            "Comments"
          ),
          size = "xl",
          easyClose = TRUE,
          
          # Modal content
          tags$div(
            class = "container-fluid",
            
            # Comment type filter at the TOP (controls viewing AND creating)
            tags$div(
              class = "comment-type-filter mb-3 p-3 bg-light rounded",
              tags$div(
                class = "d-flex align-items-center justify-content-between flex-wrap gap-2",
                tags$div(
                  class = "d-flex align-items-center gap-2",
                  tags$label("View & Add:", class = "form-label fw-bold mb-0 me-2"),
                  tags$div(
                    class = "btn-group",
                    role = "group",
                    `aria-label` = "Comment type filter",
                    tags$input(
                      type = "radio", 
                      class = "btn-check comment-type-filter-radio", 
                      name = "comment-type-filter", 
                      id = "comment-filter-prog", 
                      value = "programming", 
                      checked = "checked",
                      autocomplete = "off",
                      onclick = "filterCommentsByType('programming')"
                    ),
                    tags$label(
                      class = "btn btn-outline-warning", 
                      `for` = "comment-filter-prog", 
                      tags$i(class = "fa fa-code me-1"),
                      "Programming",
                      tags$span(id = "prog-count-badge", class = "badge bg-dark ms-1", "0")
                    ),
                    tags$input(
                      type = "radio", 
                      class = "btn-check comment-type-filter-radio", 
                      name = "comment-type-filter", 
                      id = "comment-filter-biostat", 
                      value = "biostat",
                      autocomplete = "off",
                      onclick = "filterCommentsByType('biostat')"
                    ),
                    tags$label(
                      class = "btn btn-outline-info", 
                      `for` = "comment-filter-biostat", 
                      tags$i(class = "fa fa-chart-bar me-1"),
                      "Biostat",
                      tags$span(id = "biostat-count-badge", class = "badge bg-dark ms-1", "0")
                    )
                  )
                ),
                tags$small(class = "text-muted", "Select type to filter comments and set type for new comments")
              )
            ),
            
            # Comments display area
            tags$div(
              id = "modal-comments-list",
              class = "mb-4",
              style = "max-height: 350px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 0.375rem; padding: 1rem;",
              tags$div(
                class = "text-center p-3",
                tags$div(class = "spinner-border text-primary", role = "status"),
                tags$div(class = "mt-2 text-muted", "Loading comments...")
              )
            ),
            
            # Add new comment form (simplified - type is controlled by filter above)
            tags$div(
              class = "comment-form-section border-top pt-3",
              tags$h6(
                id = "comment-form-title",
                class = "mb-3 d-flex align-items-center",
                tags$i(class = "fa fa-plus me-2"),
                "Add New ",
                tags$span(id = "comment-type-label", class = "badge bg-warning text-dark ms-1", "Programming"),
                " Comment"
              ),
              
              # Comment text input
              tags$div(
                class = "mb-3",
                tags$textarea(
                  id = "comment-text-input",
                  class = "form-control",
                  placeholder = "Write your comment here...",
                  rows = "3",
                  style = "resize: vertical;"
                )
              ),
              
              # Action buttons
              tags$div(
                class = "d-flex gap-2",
                tags$button(
                  id = "comment-submit-btn",
                  class = "btn btn-primary",
                  onclick = "submitComment()",
                  tags$i(class = "fa fa-paper-plane me-1"),
                  "Submit Comment"
                ),
                tags$button(
                  id = "comment-cancel-reply-btn",
                  class = "btn btn-outline-secondary",
                  onclick = "cancelReply()",
                  style = "display: none;",
                  tags$i(class = "fa fa-times me-1"),
                  "Cancel Reply"
                )
              )
            )
          ),
          
          footer = tagList(
            modalButton("Close")
          )
        ))
        
        # Load comments after modal is shown using JavaScript
        shinyjs::delay(200, {
          session$sendCustomMessage("loadCommentsForModal", list(
            tracker_id = tracker_id
          ))
        })
      }
    })
    
    # Comment added event observer - for updating badges
    observeEvent(input$comment_added_event, {
      if (!is.null(input$comment_added_event)) {
        tracker_id <- input$comment_added_event$tracker_id
        cat("DEBUG: Comment added event for tracker ID:", tracker_id, "\n")
        
        # Update badge for this tracker
        update_single_tracker_badges(tracker_id)
      }
    })
    
    # Comment resolved event observer - for updating badges  
    observeEvent(input$comment_resolved_event, {
      if (!is.null(input$comment_resolved_event)) {
        tracker_id <- input$comment_resolved_event$tracker_id
        comment_id <- input$comment_resolved_event$comment_id
        cat("DEBUG: Comment resolved event for tracker ID:", tracker_id, "comment ID:", comment_id, "\n")
        
        # Update badge for this tracker
        update_single_tracker_badges(tracker_id)
      }
    })
    

    
    # Handle tracker table actions
    observeEvent(input$tracker_action, {
      payload <- input$tracker_action
      act <- payload$action
      tracker_id <- payload$id
      item_id <- payload$itemId
      
      if (act == "edit") {
        # Get tracker data if exists
        tracker_data <- if (!is.na(tracker_id) && tracker_id != "") {
          get_reporting_effort_tracker_by_id(tracker_id)
        } else {
          list()  # New tracker
        }
        
        # Get programmers for dropdowns
        progs <- programmers_list()
        prog_choices <- c("Not Assigned" = "")
        if (length(progs) > 0) {
          for (prog in progs) {
            prog_choices[prog$username] <- as.character(prog$id)
          }
        }
        
        # Store tracker_id and item_id in reactive values for later use
        modal_tracker_id(tracker_id)
        modal_item_id(item_id)
        
        # Get item label for display
        item_label <- tryCatch({
          items <- reporting_effort_items()
          item <- items[sapply(items, function(x) x$id == as.integer(item_id))]
          if (length(item) > 0) item[[1]]$item_code else paste("Item", item_id)
        }, error = function(e) paste("Item", item_id))

        # Show edit modal with Production/QC sections
        showModal(create_edit_modal(
          title = if (!is.na(tracker_id) && tracker_id != "") "Edit Tracker" else "Create Tracker",
          size = "l",
          content = tagList(
            # Item info header
            div(
              class = "alert alert-info mb-3 py-2",
              tags$strong("Item: "), item_label
            ),

            # ===== PRODUCTION SECTION =====
            div(
              class = "card mb-3",
              div(
                class = "card-header bg-warning text-dark py-2",
                tags$h6(bs_icon("gear"), " Production", class = "mb-0")
              ),
              div(
                class = "card-body",
                fluidRow(
                  column(6,
                    selectInput(ns("edit_prod_programmer"), "Programmer:",
                               choices = prog_choices,
                               selected = tracker_data$production_programmer_id %||% "")
                  ),
                  column(6,
                    selectInput(ns("edit_prod_status"), "Status:",
                               choices = c("Not Started" = "not_started", "In Progress" = "in_progress", "Completed" = "completed", "On Hold" = "on_hold"),
                               selected = tracker_data$production_status %||% "not_started")
                  )
                ),
                fluidRow(
                  column(6,
                    selectInput(ns("edit_priority"), "Priority:",
                               choices = c("Low" = "low", "Medium" = "medium", "High" = "high"),
                               selected = tracker_data$priority %||% "medium")
                  ),
                  column(6,
                    dateInput(ns("edit_due_date"), "Due Date:",
                             value = if (!is.null(tracker_data$due_date) && nchar(tracker_data$due_date) > 0) as.Date(tracker_data$due_date) else NULL)
                  )
                )
              )
            ),

            # ===== QC SECTION =====
            div(
              class = "card mb-3",
              div(
                class = "card-header bg-info text-white py-2",
                tags$h6(bs_icon("check2-circle"), " QC", class = "mb-0")
              ),
              div(
                class = "card-body",
                fluidRow(
                  column(6,
                    selectInput(ns("edit_qc_programmer"), "QC Programmer:",
                               choices = prog_choices,
                               selected = tracker_data$qc_programmer_id %||% "")
                  ),
                  column(6,
                    selectInput(ns("edit_qc_status"), "QC Status:",
                               choices = c("Not Started" = "not_started", "In Progress" = "in_progress", "Completed" = "completed", "Failed" = "failed"),
                               selected = tracker_data$qc_status %||% "not_started")
                  )
                ),
                fluidRow(
                  column(6,
                    selectInput(ns("edit_qc_level"), "QC Level:",
                               choices = c("None" = "", "Level 1" = "1", "Level 2" = "2", "Level 3" = "3"),
                               selected = tracker_data$qc_level %||% "3")
                  ),
                  column(6,
                    dateInput(ns("edit_qc_date"), "QC Completion Date:",
                             value = if (!is.null(tracker_data$qc_completion_date) && nchar(tracker_data$qc_completion_date) > 0) as.Date(tracker_data$qc_completion_date) else NULL)
                  )
                )
              )
            ),

            # In Production Flag
            checkboxInput(ns("edit_in_production"), "In Production",
                         value = tracker_data$in_production_flag %||% FALSE)
          ),
          footer = tagList(
            modalButton("Cancel"),
            actionButton(ns("save_tracker"), "Save", class = "btn btn-primary")
          )
        ))
      } else if (act == "delete") {
        if (!is.na(tracker_id) && tracker_id != "") {
          showModal(create_delete_confirmation_modal(
            title = "Confirm Delete",
            "Are you sure you want to delete this tracker?",
            footer = tagList(
              modalButton("Cancel"),
              actionButton(ns("confirm_delete"), "Delete", class = "btn btn-danger",
                          onclick = paste0("Shiny.setInputValue('", ns("delete_tracker_id"), "', '", tracker_id, "');"))
            )
          ))
        } else {
          show_warning_notification("No tracker to delete")
        }
      }
    })
    
    # Save tracker
    observeEvent(input$save_tracker, {
      # Get the stored IDs from reactive values
      tracker_id <- modal_tracker_id()
      item_id <- modal_item_id()

      # ===== VALIDATION RULES =====
      validation_errors <- c()

      # Get current values
      prod_programmer <- input$edit_prod_programmer
      qc_programmer <- input$edit_qc_programmer
      prod_status <- input$edit_prod_status
      qc_status <- input$edit_qc_status
      in_production <- input$edit_in_production

      # Rule 1: If Production Programmer is assigned, Due Date and Priority are required
      if (prod_programmer != "") {
        # Note: dateInput returns NA when empty, not NULL
        if (is.null(input$edit_due_date) || is.na(input$edit_due_date)) {
          validation_errors <- c(validation_errors, "Due Date is required when Production Programmer is assigned")
        }
        if (is.null(input$edit_priority) || input$edit_priority == "") {
          validation_errors <- c(validation_errors, "Priority is required when Production Programmer is assigned")
        }
      }

      # Rule 2: In Production can only be checked if QC Status is "completed" (QC pass)
      if (isTRUE(in_production) && qc_status != "completed") {
        validation_errors <- c(validation_errors, "In Production can only be enabled when QC Status is 'Completed'")
      }

      # Rule 3: Production and QC Programmer cannot be the same (unless both are Not Assigned)
      if (prod_programmer != "" && qc_programmer != "" && prod_programmer == qc_programmer) {
        validation_errors <- c(validation_errors, "Production Programmer and QC Programmer cannot be the same person")
      }

      # Rule 4: If Production Programmer is Not Assigned, Production Status must be Not Started
      if (prod_programmer == "" && prod_status != "not_started") {
        validation_errors <- c(validation_errors, "Production Status must be 'Not Started' when no Production Programmer is assigned")
      }

      # Rule 5: If QC Programmer is Not Assigned, QC Status must be Not Started
      if (qc_programmer == "" && qc_status != "not_started") {
        validation_errors <- c(validation_errors, "QC Status must be 'Not Started' when no QC Programmer is assigned")
      }

      # Show validation errors if any
      if (length(validation_errors) > 0) {
        show_warning_notification(paste("Validation Error:", paste(validation_errors, collapse = "; ")))
        return()
      }

      # Build tracker data
      tracker_data <- list(
        reporting_effort_item_id = as.integer(item_id)
      )

      # Add optional fields if set
      if (input$edit_prod_programmer != "") {
        tracker_data$production_programmer_id <- as.integer(input$edit_prod_programmer)
      }
      if (input$edit_qc_programmer != "") {
        tracker_data$qc_programmer_id <- as.integer(input$edit_qc_programmer)
      }

      tracker_data$production_status <- input$edit_prod_status
      tracker_data$qc_status <- input$edit_qc_status
      tracker_data$priority <- input$edit_priority
      tracker_data$in_production_flag <- input$edit_in_production

      if (input$edit_qc_level != "") {
        tracker_data$qc_level <- as.character(input$edit_qc_level)
      }

      if (!is.null(input$edit_due_date)) {
        tracker_data$due_date <- as.character(input$edit_due_date)
      }
      if (!is.null(input$edit_qc_date)) {
        tracker_data$qc_completion_date <- as.character(input$edit_qc_date)
      }

      # Create or update tracker
      if (!is.na(tracker_id) && tracker_id != "") {
        # Update existing
        res <- update_reporting_effort_tracker(tracker_id, tracker_data)
      } else {
        # Create new
        res <- create_or_update_tracker(tracker_data)
      }

      if ("error" %in% names(res)) {
        show_error_notification(paste("Failed to save tracker:", res$error))
      } else {
        show_success_notification("Tracker saved successfully")
        removeModal()
        load_tracker_tables()  # Reload tables
      }
    })
    
    # Delete tracker
    observeEvent(input$delete_tracker_id, {
      tracker_id <- input$delete_tracker_id
      
      if (!is.null(tracker_id) && nchar(tracker_id) > 0 && tracker_id != "") {
        # Call the API to delete the tracker
        result <- delete_reporting_effort_tracker(tracker_id)
        
        if ("error" %in% names(result)) {
          show_error_notification(paste("Failed to delete tracker:", result$error))
        } else {
          show_success_notification("Tracker deleted successfully")
          removeModal()
          load_tracker_tables()  # Reload tables
        }
      } else {
        show_error_notification("Invalid tracker ID")
      }
    })
    


    # Export/import
    observeEvent(input$export_tracker_clicked, {
      eff_id <- current_reporting_effort_id()
      if (is.null(eff_id)) return(show_warning_notification("Select a reporting effort first"))
      data <- export_tracker_data(eff_id)
      if ("error" %in% names(data)) return(show_error_notification(paste("Export failed:", data$error)))
      # The UI will handle file creation through a download handler elsewhere if needed; for now just notify
      show_success_notification(paste("Exported", data$total_items %||% 0, "trackers (JSON). CSV/Excel export can be added next)."))
    })

    observeEvent(input$import_tracker_clicked, {
      eff_id <- current_reporting_effort_id()
      if (is.null(eff_id)) return(show_warning_notification("Select a reporting effort first"))
      showModal(create_edit_modal(
        title = "Import Tracker Updates",
        size = "m",
        fileInput(ns("import_file"), "Choose CSV file exported from tracker", accept = c(".csv"), width = "100%"),
        checkboxInput(ns("import_update_existing"), "Update existing trackers", value = TRUE),
        footer = tagList(modalButton("Cancel"), actionButton(ns("confirm_import"), "Import", class = "btn btn-primary"))
      ))
    })

    observeEvent(input$confirm_import, {
      req(input$import_file)
      update_existing <- isTRUE(input$import_update_existing)
      df <- tryCatch(read.csv(input$import_file$datapath, stringsAsFactors = FALSE), error = function(e) NULL)
      removeModal()
      if (is.null(df)) return(show_error_notification("Failed to read CSV"))
      # Expected columns: item_code, production_programmer_username, production_status, qc_programmer_username, qc_status, priority, due_date, qc_completion_date
      records <- lapply(seq_len(nrow(df)), function(i) as.list(df[i, ]))
      res <- import_tracker_data_json(current_reporting_effort_id(), records, update_existing = update_existing)
      if ("error" %in% names(res)) show_error_notification(paste("Import failed:", res$error)) else {
        show_success_notification(paste("Import completed. Updated:", res$updated %||% 0))
        load_tracker_tables()
      }
    })

    # Universal CRUD Manager integration (Phase 4)
    # Replaces entity-specific WebSocket observer with standardized refresh trigger
    observeEvent(input$`reporting_effort_tracker-crud_refresh`, {
      if (!is.null(input$`reporting_effort_tracker-crud_refresh`)) {
        cat("📊 Universal CRUD refresh triggered for reporting effort tracker\n")
        load_tracker_tables()
      }
    })
    
    # Legacy WebSocket observer (kept for backward compatibility during transition)
    observeEvent(input$websocket_event, {
      if (!is.null(input$websocket_event)) {
        event_data <- input$websocket_event
        
        cat("DEBUG: R WebSocket event received - type:", event_data$type, "\n")
        cat("DEBUG: Event data structure:", str(event_data), "\n")
        
        # Handle tracker events (created, updated, deleted)
        if (startsWith(event_data$type, "reporting_effort_tracker_")) {
          cat("DEBUG: Tracker WebSocket event received:", event_data$type, "\n")
          
          if (event_data$type == "reporting_effort_tracker_deleted") {
            cat("DEBUG: Tracker deleted event - checking if surgical removal already handled\n")
            
            # Check if this deletion was already handled by JavaScript surgical removal
            # If JavaScript handled it successfully, we won't reach here due to early return
            # This means either surgical removal failed or wasn't attempted
            
            cat("DEBUG: Using fallback table refresh for tracker deletion\n")
            load_tracker_tables()
            show_success_notification("Tracker deleted (fallback update)", duration = 3000)
            
          } else if (event_data$type %in% c("reporting_effort_tracker_updated", "reporting_effort_tracker_created")) {
            cat("DEBUG: Tracker updated/created event - refreshing tables\n")
            # Refresh tables for updates and creates
            load_tracker_tables()
          }
        }
        
        # Handle comment events that should trigger badge updates
        if (startsWith(event_data$type, "comment_")) {
          tracker_id <- event_data$data$tracker_id
          unresolved_count <- event_data$data$unresolved_count
          
          cat("DEBUG: Extracted - tracker_id:", tracker_id, "unresolved_count:", unresolved_count, "\n")
          
          # Update badge with new comment count
          if (!is.null(tracker_id) && !is.null(unresolved_count)) {
            cat("DEBUG: Updating comment badge via WebSocket - tracker_id:", tracker_id, "unresolved_count:", unresolved_count, "\n")
            session$sendCustomMessage("updateSmartCommentButtons", list(
              summaries = list(list(
                tracker_id = tracker_id,
                unresolved_count = unresolved_count  # Use consistent field name
              )),
              source = "websocket_realtime"
            ))
          }
        }
      }
    })

    # Comment action handlers (pin, unpin, etc.)
    observeEvent(input$comment_action, {
      if (!is.null(input$comment_action)) {
        action_data <- input$comment_action
        cat("DEBUG: Comment action received:", action_data$action, "for comment", action_data$comment_id, "\n")
        
        tryCatch({
          result <- NULL
          
          if (action_data$action == "pin") {
            result <- pin_tracker_comment(action_data$comment_id, user_id = 1, user_role = "USER")
            action_name <- "pinned"
          } else if (action_data$action == "unpin") {
            result <- unpin_tracker_comment(action_data$comment_id, user_id = 1, user_role = "USER")
            action_name <- "unpinned"
          } else if (action_data$action == "mark_addressed") {
            result <- resolve_tracker_comment(action_data$comment_id, is_resolved = TRUE, user_id = 1, user_role = "USER")
            action_name <- "marked as addressed"
          } else {
            show_error_notification(paste("Unknown action:", action_data$action))
            return()
          }
          
          if (!is.null(result$error)) {
            show_error_notification(paste("Error:", result$error))
          } else {
            show_success_notification(paste("Comment", action_name, "successfully"))
            # The WebSocket event will handle the refresh automatically
          }
          
        }, error = function(e) {
          cat("ERROR: Failed to execute comment action:", e$message, "\n")
          show_error_notification(paste("Error executing action:", e$message))
        })
      }
    })

    # ===== BULK OPERATIONS SECTION =====

    # Helper function to get the current tab's data
    get_current_tab_data <- function() {
      active_tab <- input$tracker_tabs
      data_list <- tracker_data()
      if (is.null(data_list)) return(data.frame())

      switch(active_tab,
        "tlf" = if (!is.null(data_list$tlf_trackers)) data_list$tlf_trackers else data.frame(),
        "sdtm" = if (!is.null(data_list$sdtm_trackers)) data_list$sdtm_trackers else data.frame(),
        "adam" = if (!is.null(data_list$adam_trackers)) data_list$adam_trackers else data.frame(),
        data.frame()
      )
    }

    # Get selected row indices for current tab
    get_current_selection <- reactive({
      active_tab <- input$tracker_tabs
      switch(active_tab,
        "tlf" = input$tracker_table_tlf_rows_selected,
        "sdtm" = input$tracker_table_sdtm_rows_selected,
        "adam" = input$tracker_table_adam_rows_selected,
        NULL
      )
    })

    # Get selected tracker data for current tab
    get_selected_trackers <- reactive({
      selected_rows <- get_current_selection()
      if (is.null(selected_rows) || length(selected_rows) == 0) {
        return(data.frame())
      }

      tab_data <- get_current_tab_data()
      if (nrow(tab_data) == 0) return(data.frame())

      # Apply comment filter to get the same data as displayed
      filtered_data <- filter_by_comments(tab_data)
      if (nrow(filtered_data) == 0) return(data.frame())

      # Return selected rows
      filtered_data[selected_rows, , drop = FALSE]
    })

    # Render selection action bar (dynamic - appears when items selected)
    output$selection_action_bar <- renderUI({
      selected_rows <- get_current_selection()
      active_tab <- input$tracker_tabs

      # Only show if items are selected
      if (is.null(selected_rows) || length(selected_rows) == 0) {
        return(NULL)
      }

      tab_name <- switch(active_tab,
        "tlf" = "TLF",
        "sdtm" = "SDTM",
        "adam" = "ADaM",
        "Unknown"
      )

      # Get selection summary
      selected_data <- get_selected_trackers()
      prod_assigned <- sum(selected_data$Prod_Programmer != "Not Assigned", na.rm = TRUE)
      prod_unassigned <- length(selected_rows) - prod_assigned
      qc_assigned <- sum(selected_data$QC_Programmer != "Not Assigned", na.rm = TRUE)
      qc_unassigned <- length(selected_rows) - qc_assigned

      div(
        class = "alert alert-info mb-3 d-flex justify-content-between align-items-center flex-wrap gap-2",
        style = "padding: 10px 15px;",
        # Left side: Selection info
        div(
          class = "d-flex align-items-center gap-3",
          tags$strong(paste0(length(selected_rows), " item(s) selected")),
          tags$span(class = "text-muted", paste0("from ", tab_name, " Tracker")),
          tags$span(
            class = "badge bg-warning text-dark",
            title = "Production assignment status",
            paste0("Prod: ", prod_assigned, " assigned, ", prod_unassigned, " unassigned")
          ),
          tags$span(
            class = "badge bg-info text-white",
            title = "QC assignment status",
            paste0("QC: ", qc_assigned, " assigned, ", qc_unassigned, " unassigned")
          )
        ),
        # Right side: Action buttons
        div(
          class = "d-flex gap-2",
          actionButton(
            ns("select_all_visible"),
            "Select All Visible",
            icon = icon("check-square"),
            class = "btn btn-outline-secondary btn-sm"
          ),
          actionButton(
            ns("deselect_all"),
            "Deselect All",
            icon = icon("square"),
            class = "btn btn-outline-secondary btn-sm"
          ),
          tags$span(class = "vr mx-1"),  # Vertical divider
          actionButton(
            ns("bulk_assign_action"),
            "Bulk Assign",
            icon = icon("users"),
            class = "btn btn-primary btn-sm"
          ),
          actionButton(
            ns("bulk_update_action"),
            "Bulk Update",
            icon = icon("edit"),
            class = "btn btn-info btn-sm"
          )
        )
      )
    })

    # Select All Visible button handler
    observeEvent(input$select_all_visible, {
      active_tab <- input$tracker_tabs
      tab_data <- get_current_tab_data()
      filtered_data <- filter_by_comments(tab_data)

      if (nrow(filtered_data) == 0) {
        show_warning_notification("No items to select")
        return()
      }

      # Get the proxy for the current table and select all rows
      proxy <- switch(active_tab,
        "tlf" = DT::dataTableProxy("tracker_table_tlf"),
        "sdtm" = DT::dataTableProxy("tracker_table_sdtm"),
        "adam" = DT::dataTableProxy("tracker_table_adam")
      )

      # Select all rows (1:nrow gives all visible after filtering)
      DT::selectRows(proxy, 1:nrow(filtered_data))
    })

    # Deselect All button handler
    observeEvent(input$deselect_all, {
      active_tab <- input$tracker_tabs

      proxy <- switch(active_tab,
        "tlf" = DT::dataTableProxy("tracker_table_tlf"),
        "sdtm" = DT::dataTableProxy("tracker_table_sdtm"),
        "adam" = DT::dataTableProxy("tracker_table_adam")
      )

      # Clear selection
      DT::selectRows(proxy, NULL)
    })

    # Bulk Assign button handler (from action bar)
    observeEvent(input$bulk_assign_action, {
      selected_data <- get_selected_trackers()
      if (nrow(selected_data) == 0) {
        show_warning_notification("Please select items first")
        return()
      }

      # Filter out items without tracker IDs (dummy data)
      valid_trackers <- selected_data[selected_data$Tracker_ID != "", , drop = FALSE]
      if (nrow(valid_trackers) == 0) {
        show_warning_notification("No valid tracker items selected. Please create trackers first.")
        return()
      }

      # Get programmers list for dropdown
      progs <- programmers_list()
      prog_choices <- c("-- No Change --" = "", "Not Assigned" = "UNASSIGN")
      if (length(progs) > 0) {
        prog_choices <- c(prog_choices, setNames(
          sapply(progs, function(x) x$id),
          sapply(progs, function(x) x$username)
        ))
      }

      # Calculate assignment summary
      prod_assigned <- sum(valid_trackers$Prod_Programmer != "Not Assigned", na.rm = TRUE)
      prod_unassigned <- nrow(valid_trackers) - prod_assigned
      qc_assigned <- sum(valid_trackers$QC_Programmer != "Not Assigned", na.rm = TRUE)
      qc_unassigned <- nrow(valid_trackers) - qc_assigned

      showModal(modalDialog(
        title = tagList(icon("users"), " Bulk Assign Programmers"),
        size = "l",

        # Selection summary
        div(
          class = "alert alert-info mb-3",
          tags$h6(class = "mb-2", paste0(nrow(valid_trackers), " items selected")),
          div(
            class = "d-flex gap-3",
            tags$span(class = "badge bg-warning text-dark",
              paste0("Prod: ", prod_assigned, " assigned, ", prod_unassigned, " unassigned")),
            tags$span(class = "badge bg-info text-white",
              paste0("QC: ", qc_assigned, " assigned, ", qc_unassigned, " unassigned"))
          )
        ),

        # Production Section
        div(
          class = "card mb-3",
          div(class = "card-header bg-warning text-dark",
              tags$h6(bs_icon("gear"), " Production Assignment", class = "mb-0")),
          div(
            class = "card-body",
            selectInput(ns("bulk_prod_programmer"), "Assign Production Programmer:",
                       choices = prog_choices, selected = ""),
            checkboxInput(ns("bulk_prod_only_unassigned"), "Only assign to unassigned items", value = FALSE)
          )
        ),

        # QC Section
        div(
          class = "card mb-3",
          div(class = "card-header bg-info text-white",
              tags$h6(bs_icon("check2-circle"), " QC Assignment", class = "mb-0")),
          div(
            class = "card-body",
            selectInput(ns("bulk_qc_programmer"), "Assign QC Programmer:",
                       choices = prog_choices, selected = ""),
            checkboxInput(ns("bulk_qc_only_unassigned"), "Only assign to unassigned items", value = FALSE)
          )
        ),

        # Validation note
        div(
          class = "alert alert-secondary small",
          tags$strong("Note: "),
          "Production and QC programmers cannot be the same person for any item."
        ),

        footer = tagList(
          modalButton("Cancel"),
          actionButton(ns("confirm_bulk_assign"), "Apply Changes",
                      class = "btn btn-primary", icon = icon("check"))
        )
      ))
    })

    # Confirm bulk assign
    observeEvent(input$confirm_bulk_assign, {
      selected_data <- get_selected_trackers()
      valid_trackers <- selected_data[selected_data$Tracker_ID != "", , drop = FALSE]

      prod_prog <- input$bulk_prod_programmer
      qc_prog <- input$bulk_qc_programmer
      prod_only_unassigned <- input$bulk_prod_only_unassigned
      qc_only_unassigned <- input$bulk_qc_only_unassigned

      # Build assignments list
      assignments <- list()

      for (i in 1:nrow(valid_trackers)) {
        tracker_id <- valid_trackers$Tracker_ID[i]
        current_prod <- valid_trackers$Prod_Programmer[i]
        current_qc <- valid_trackers$QC_Programmer[i]

        # Production assignment
        if (prod_prog != "") {
          skip_prod <- prod_only_unassigned && current_prod != "Not Assigned"
          if (!skip_prod) {
            if (prod_prog == "UNASSIGN") {
              assignments <- append(assignments, list(list(
                tracker_id = tracker_id,
                user_id = NULL,
                role = "production"
              )))
            } else {
              # Validation: check if same as QC
              if (qc_prog != "" && qc_prog != "UNASSIGN" && prod_prog == qc_prog) {
                show_warning_notification(paste0("Skipping item ", valid_trackers$Item[i],
                  ": Production and QC programmer cannot be the same"))
                next
              }
              assignments <- append(assignments, list(list(
                tracker_id = tracker_id,
                user_id = prod_prog,
                role = "production"
              )))
            }
          }
        }

        # QC assignment
        if (qc_prog != "") {
          skip_qc <- qc_only_unassigned && current_qc != "Not Assigned"
          if (!skip_qc) {
            if (qc_prog == "UNASSIGN") {
              assignments <- append(assignments, list(list(
                tracker_id = tracker_id,
                user_id = NULL,
                role = "qc"
              )))
            } else {
              # Validation: check if same as production
              if (prod_prog != "" && prod_prog != "UNASSIGN" && prod_prog == qc_prog) {
                # Already warned above
                next
              }
              assignments <- append(assignments, list(list(
                tracker_id = tracker_id,
                user_id = qc_prog,
                role = "qc"
              )))
            }
          }
        }
      }

      if (length(assignments) == 0) {
        show_warning_notification("No assignments to apply. Check your selections.")
        return()
      }

      # Call bulk assign API
      result <- bulk_assign_programmers(list(assignments = assignments))

      if ("error" %in% names(result)) {
        show_error_notification(paste("Bulk assign failed:", result$error))
      } else {
        removeModal()
        show_success_notification(paste0("Successfully updated ", length(assignments), " assignment(s)"))

        # Clear selection and refresh
        active_tab <- input$tracker_tabs
        proxy <- switch(active_tab,
          "tlf" = DT::dataTableProxy("tracker_table_tlf"),
          "sdtm" = DT::dataTableProxy("tracker_table_sdtm"),
          "adam" = DT::dataTableProxy("tracker_table_adam")
        )
        DT::selectRows(proxy, NULL)
        load_tracker_tables()
      }
    })

    # Bulk Update button handler (from action bar)
    observeEvent(input$bulk_update_action, {
      selected_data <- get_selected_trackers()
      if (nrow(selected_data) == 0) {
        show_warning_notification("Please select items first")
        return()
      }

      # Filter out items without tracker IDs
      valid_trackers <- selected_data[selected_data$Tracker_ID != "", , drop = FALSE]
      if (nrow(valid_trackers) == 0) {
        show_warning_notification("No valid tracker items selected. Please create trackers first.")
        return()
      }

      # Status choices with "No Change" option
      prod_status_choices <- c(
        "-- No Change --" = "",
        "Not Started" = "not_started",
        "In Progress" = "in_progress",
        "Completed" = "completed",
        "On Hold" = "on_hold"
      )

      qc_status_choices <- c(
        "-- No Change --" = "",
        "Not Started" = "not_started",
        "In Progress" = "in_progress",
        "Completed" = "completed",
        "Failed" = "failed"
      )

      priority_choices <- c(
        "-- No Change --" = "",
        "Low" = "low",
        "Medium" = "medium",
        "High" = "high",
        "Critical" = "critical"
      )

      qc_level_choices <- c(
        "-- No Change --" = "",
        "None" = "0",
        "Level 1" = "1",
        "Level 2" = "2",
        "Level 3" = "3"
      )

      showModal(modalDialog(
        title = tagList(icon("edit"), " Bulk Update Fields"),
        size = "l",

        # Selection summary
        div(
          class = "alert alert-info mb-3",
          tags$h6(paste0(nrow(valid_trackers), " items selected")),
          tags$small(class = "text-muted", "Leave fields as 'No Change' to keep existing values")
        ),

        # Production Section
        div(
          class = "card mb-3",
          div(class = "card-header bg-warning text-dark",
              tags$h6(bs_icon("gear"), " Production Fields", class = "mb-0")),
          div(
            class = "card-body",
            fluidRow(
              column(6, selectInput(ns("bulk_prod_status"), "Production Status:",
                                   choices = prod_status_choices, selected = "")),
              column(6, selectInput(ns("bulk_priority"), "Priority:",
                                   choices = priority_choices, selected = ""))
            ),
            fluidRow(
              column(6,
                div(
                  class = "d-flex align-items-end gap-2",
                  div(style = "flex: 1;",
                    dateInput(ns("bulk_due_date"), "Due Date:", value = NA)
                  ),
                  checkboxInput(ns("bulk_due_date_no_change"), "No Change", value = TRUE)
                )
              ),
              column(6, "")
            )
          )
        ),

        # QC Section
        div(
          class = "card mb-3",
          div(class = "card-header bg-info text-white",
              tags$h6(bs_icon("check2-circle"), " QC Fields", class = "mb-0")),
          div(
            class = "card-body",
            fluidRow(
              column(6, selectInput(ns("bulk_qc_status"), "QC Status:",
                                   choices = qc_status_choices, selected = "")),
              column(6, selectInput(ns("bulk_qc_level"), "QC Level:",
                                   choices = qc_level_choices, selected = ""))
            )
          )
        ),

        # In Production flag
        div(
          class = "card mb-3",
          div(class = "card-body",
            div(
              class = "form-check",
              tags$input(type = "checkbox", class = "form-check-input",
                        id = ns("bulk_in_production_check")),
              tags$label(class = "form-check-label", `for` = ns("bulk_in_production_check"),
                        "Set In Production flag (only applies to items with QC Status = Completed)")
            ),
            checkboxInput(ns("bulk_in_production_no_change"), "No Change to In Production", value = TRUE)
          )
        ),

        footer = tagList(
          modalButton("Cancel"),
          actionButton(ns("confirm_bulk_update"), "Apply Changes",
                      class = "btn btn-primary", icon = icon("check"))
        )
      ))
    })

    # Confirm bulk update
    observeEvent(input$confirm_bulk_update, {
      selected_data <- get_selected_trackers()
      valid_trackers <- selected_data[selected_data$Tracker_ID != "", , drop = FALSE]

      prod_status <- input$bulk_prod_status
      priority <- input$bulk_priority
      due_date <- input$bulk_due_date
      due_date_no_change <- input$bulk_due_date_no_change
      qc_status <- input$bulk_qc_status
      qc_level <- input$bulk_qc_level
      in_production_no_change <- input$bulk_in_production_no_change

      # Build updates list
      updates <- list()

      for (i in 1:nrow(valid_trackers)) {
        tracker_id <- valid_trackers$Tracker_ID[i]
        update_obj <- list(tracker_id = tracker_id)
        has_updates <- FALSE

        # Production status
        if (prod_status != "") {
          update_obj$production_status <- prod_status
          has_updates <- TRUE
        }

        # Priority
        if (priority != "") {
          update_obj$priority <- priority
          has_updates <- TRUE
        }

        # Due date
        if (!due_date_no_change && !is.na(due_date)) {
          update_obj$due_date <- as.character(due_date)
          has_updates <- TRUE
        }

        # QC status
        if (qc_status != "") {
          update_obj$qc_status <- qc_status
          has_updates <- TRUE
        }

        # QC level
        if (qc_level != "") {
          update_obj$qc_level <- qc_level
          has_updates <- TRUE
        }

        # In production flag
        if (!in_production_no_change) {
          in_prod_checked <- isTRUE(input$bulk_in_production_check)
          # Only set in_production if QC status is completed
          if (in_prod_checked) {
            current_qc_status <- valid_trackers$QC_Status[i]
            if (qc_status == "completed" || current_qc_status == "Completed") {
              update_obj$in_production <- TRUE
              has_updates <- TRUE
            }
          } else {
            update_obj$in_production <- FALSE
            has_updates <- TRUE
          }
        }

        if (has_updates) {
          updates <- append(updates, list(update_obj))
        }
      }

      if (length(updates) == 0) {
        show_warning_notification("No updates to apply. Please select at least one field to change.")
        return()
      }

      # Call bulk status update API
      result <- bulk_status_update(list(updates = updates))

      if ("error" %in% names(result)) {
        show_error_notification(paste("Bulk update failed:", result$error))
      } else {
        removeModal()
        show_success_notification(paste0("Successfully updated ", length(updates), " item(s)"))

        # Clear selection and refresh
        active_tab <- input$tracker_tabs
        proxy <- switch(active_tab,
          "tlf" = DT::dataTableProxy("tracker_table_tlf"),
          "sdtm" = DT::dataTableProxy("tracker_table_sdtm"),
          "adam" = DT::dataTableProxy("tracker_table_adam")
        )
        DT::selectRows(proxy, NULL)
        load_tracker_tables()
      }
    })

    # Legacy dropdown menu handlers (kept for backward compatibility)
    observeEvent(input$bulk_assign_clicked, {
      # Trigger the same action as the action bar button
      shinyjs::click("bulk_assign_action")
    })
    observeEvent(input$bulk_status_clicked, {
      # Trigger the same action as the action bar button
      shinyjs::click("bulk_update_action")
    })
    observeEvent(input$workload_summary_clicked, show_success_notification("Workload summary coming soon"))
    
    # Enhanced surgical update event handlers
    
    # Handle surgical removal fallback when JavaScript fails
    observeEvent(input$surgical_removal_fallback, {
      if (!is.null(input$surgical_removal_fallback)) {
        tracker_id <- input$surgical_removal_fallback$tracker_id
        cat("DEBUG: Surgical removal fallback triggered for tracker:", tracker_id, "\n")
        
        # Fall back to full table refresh
        load_tracker_tables()
        show_success_notification("Tracker removed (fallback refresh)", duration = 3000)
      }
    })
    
    # Handle optimized bulk refresh requests from JavaScript
    observeEvent(input$bulk_refresh_request, {
      if (!is.null(input$bulk_refresh_request)) {
        effort_id <- input$bulk_refresh_request$effort_id
        cat("DEBUG: Bulk refresh request for effort:", effort_id, "\n")
        
        # Use optimized bulk loading
        if (!is.null(effort_id) && effort_id == current_reporting_effort_id()) {
          load_tracker_tables_optimized(effort_id)
        }
      }
    })
    
    # Cross-browser force refresh handler (triggered by global observer)
    observeEvent(input$force_refresh, {
      cat("DEBUG: Cross-browser force refresh triggered\n")
      load_tracker_tables()
      show_success_notification("Data refreshed due to changes in another session", duration = 3000)
    })
    
    # Handle enhanced delete notifications from JavaScript
    observeEvent(input$delete_notification, {
      if (!is.null(input$delete_notification)) {
        notification_data <- input$delete_notification
        
        if (notification_data$type == "surgical_delete") {
          # Show enhanced notification with context
          context <- notification_data$context
          message <- notification_data$message
          
          # Create rich notification with user context
          if (!is.null(context$deleted_by) && !is.null(context$deleted_by$username)) {
            user_info <- paste0(" by ", context$deleted_by$username)
          } else {
            user_info <- ""
          }
          
          show_success_notification(
            tagList(
              tags$div(
                class = "d-flex align-items-center",
                tags$i(class = "fa fa-trash me-2 text-warning"),
                tags$span(message, user_info)
              )
            ),
            duration = 4000
          )
        }
      }
    })
    
    # Optimized table loading using bulk endpoint
    load_tracker_tables_optimized <- function(effort_id = NULL) {
      eff_id <- effort_id %||% current_reporting_effort_id()
      
      if (is.null(eff_id)) {
        cat("DEBUG: No effort ID for optimized loading\n")
        return()
      }
      
      cat("DEBUG: Loading tracker tables optimized for effort:", eff_id, "\n")
      
      tryCatch({
        # Use bulk endpoint for efficient loading
        bulk_result <- get_trackers_by_effort_bulk(eff_id)
        
        if ("error" %in% names(bulk_result)) {
          cat("ERROR: Bulk loading failed:", bulk_result$error, "\n")
          # Fall back to regular loading
          load_tracker_tables()
          return()
        }
        
        # Process bulk data into table structure
        processed_data <- process_bulk_tracker_data(bulk_result)
        tracker_data(processed_data)
        
        cat("DEBUG: Optimized loading completed with", length(bulk_result), "items\n")
        
      }, error = function(e) {
        cat("ERROR: Exception in optimized loading:", e$message, "\n")
        # Fall back to regular loading
        load_tracker_tables()
      })
    }
    
    # Process bulk tracker data into table format
    process_bulk_tracker_data <- function(bulk_data) {
      # Transform bulk API response into the expected table structure
      # This would need to be implemented based on the bulk endpoint response format
      
      # For now, return empty structure - this would be enhanced based on actual bulk response
      list(
        tlf_trackers = data.frame(),
        sdtm_trackers = data.frame(), 
        adam_trackers = data.frame()
      )
    }
  })
}
