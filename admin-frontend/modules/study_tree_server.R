study_tree_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns

    last_update <- reactiveVal(Sys.time())
    selected_node <- reactiveVal(list(type = NULL, label = NULL))
    
    # Set up validation for Add Study form
    iv_study_new <- InputValidator$new()
    iv_study_new$add_rule("new_study_label", sv_required())
    iv_study_new$add_rule("new_study_label", function(value) {
      if (nchar(trimws(value)) < 1) {
        "Study label is required"
      }
    })
    
    # Set up validation for Add Database Release form
    iv_release_new <- InputValidator$new()
    iv_release_new$add_rule("new_release_label", sv_required())
    iv_release_new$add_rule("new_release_label", function(value) {
      if (nchar(trimws(value)) < 1) {
        "Database release label is required"
      }
    })
    
    # Set up validation for Add Reporting Effort form
    iv_effort_new <- InputValidator$new()
    iv_effort_new$add_rule("new_effort_label", sv_required())
    iv_effort_new$add_rule("new_effort_label", function(value) {
      if (nchar(trimws(value)) < 1) {
        "Reporting effort label is required"
      }
    })
    
    # Set up validation for Edit forms
    iv_edit <- InputValidator$new()
    iv_edit$add_rule("edit_label", sv_required())
    iv_edit$add_rule("edit_label", function(value) {
      if (nchar(trimws(value)) < 1) {
        "Label is required"
      }
    })

    # Load hierarchical data from APIs and build tree structure
    build_tree_data <- function() {
      studies <- get_studies()
      if (!is.null(studies$error)) return(list())

      releases <- get_database_releases(); if (!is.null(releases$error)) releases <- list()
      efforts  <- get_reporting_efforts();  if (!is.null(efforts$error))  efforts  <- list()

      # Sort studies alphabetically by label
      studies <- studies[order(vapply(studies, function(x) x$study_label, character(1)), na.last = TRUE)]

      # Index collections by parent IDs
      releases_by_study <- split(releases, vapply(releases, function(x) x$study_id, numeric(1)))
      efforts_by_release <- split(efforts, vapply(efforts, function(x) x$database_release_id, numeric(1)))

      tree <- list()
      for (study in studies) {
        study_id <- study$id
        study_label <- study$study_label

        # Build releases under this study
        releases_list <- releases_by_study[[as.character(study_id)]] %||% list()
        
        # Sort releases alphabetically by label
        if (length(releases_list) > 0) {
          releases_list <- releases_list[order(vapply(releases_list, function(x) x$database_release_label, character(1)), na.last = TRUE)]
        }
        
        release_nodes <- lapply(releases_list, function(rel) {
          rel_id <- rel$id
          rel_label <- rel$database_release_label

          # Build efforts under this release
          efforts_list <- efforts_by_release[[as.character(rel_id)]] %||% list()
          
          # Sort efforts alphabetically by label
          if (length(efforts_list) > 0) {
            efforts_list <- efforts_list[order(vapply(efforts_list, function(x) x$database_release_label, character(1)), na.last = TRUE)]
          }
          
          effort_nodes <- lapply(efforts_list, function(eff) {
            structure(list(), stinfo = list(type = "effort", id = eff$id, study_id = eff$study_id, release_id = eff$database_release_id))
          })
          if (length(effort_nodes) > 0) {
            names(effort_nodes) <- vapply(efforts_list, function(eff) eff$database_release_label, character(1))
            # Sort effort nodes alphabetically
            effort_nodes <- effort_nodes[order(names(effort_nodes), na.last = TRUE)]
          }

          # Build release node with metadata
          node <- structure(effort_nodes, 
                          stinfo = list(type = "release", id = rel_id, study_id = rel$study_id))
          setNames(list(node), rel_label)
        })
        # Flatten release_nodes (list of single-named lists) into a single named list
        if (length(release_nodes) > 0) {
          study_children <- do.call(c, release_nodes)
          # Sort study children (releases) alphabetically
          study_children <- study_children[order(names(study_children), na.last = TRUE)]
        } else {
          study_children <- list()
        }

        # Build study node with metadata
        study_node <- structure(study_children, 
                              stinfo = list(type = "study", id = study_id))
        tree[[study_label]] <- study_node
      }

      # Sort the top-level tree (studies) alphabetically
      tree <- tree[order(names(tree), na.last = TRUE)]
      
      tree
    }

    # Helper null-coalescing for lists
    `%||%` <- function(x, y) if (is.null(x)) y else x
    
    # Helper function to normalize labels for duplicate checking
    # Removes spaces and converts to uppercase for comparison
    normalize_label <- function(label) {
      gsub("\\s+", "", toupper(trimws(label)))
    }
    
    # Helper function to check if a study label already exists (case and space insensitive)
    check_duplicate_study <- function(new_label, exclude_id = NULL) {
      studies <- get_studies()
      if (!is.null(studies$error)) return(FALSE)
      
      normalized_new <- normalize_label(new_label)
      
      for (study in studies) {
        # Skip if this is the study being edited
        if (!is.null(exclude_id) && study$id == exclude_id) next
        
        if (normalize_label(study$study_label) == normalized_new) {
          return(study$study_label)  # Return the existing label
        }
      }
      return(FALSE)
    }
    
    # Helper function to check if a label already exists (case and space insensitive)
    check_duplicate_release <- function(study_id, new_label, exclude_id = NULL) {
      releases <- get_database_releases()
      if (!is.null(releases$error)) return(FALSE)
      
      normalized_new <- normalize_label(new_label)
      study_releases <- Filter(function(r) r$study_id == study_id, releases)
      
      for (release in study_releases) {
        # Skip if this is the release being edited
        if (!is.null(exclude_id) && release$id == exclude_id) next
        
        if (normalize_label(release$database_release_label) == normalized_new) {
          return(release$database_release_label)  # Return the existing label
        }
      }
      return(FALSE)
    }
    
    # Helper function to check if a reporting effort label already exists
    check_duplicate_effort <- function(release_id, new_label, exclude_id = NULL) {
      efforts <- get_reporting_efforts()
      if (!is.null(efforts$error)) return(FALSE)
      
      normalized_new <- normalize_label(new_label)
      release_efforts <- Filter(function(e) e$database_release_id == release_id, efforts)
      
      for (effort in release_efforts) {
        # Skip if this is the effort being edited
        if (!is.null(exclude_id) && effort$id == exclude_id) next
        
        if (normalize_label(effort$database_release_label) == normalized_new) {
          return(effort$database_release_label)  # Return the existing label
        }
      }
      return(FALSE)
    }
    
    # Helper function to parse error messages and check for duplicates
    parse_error_for_duplicate <- function(error_string) {
      # Debug: print the error string
      cat("DEBUG: Error string received:", error_string, "\n")
      
      # Check if it's a duplicate error (HTTP 400 with specific message)
      if (grepl("already exists", error_string, ignore.case = TRUE) || 
          grepl("duplicate", error_string, ignore.case = TRUE) ||
          grepl("HTTP 400", error_string, ignore.case = TRUE)) {
        return(TRUE)
      }
      return(FALSE)
    }
    
    # Helper to extract clean error message
    extract_error_message <- function(error_string) {
      # Debug: print for troubleshooting
      cat("DEBUG: Extracting message from:", error_string, "\n")
      
      # Try to extract the actual error message from HTTP errors
      if (grepl("HTTP \\d+", error_string)) {
        # Extract JSON part after the HTTP status
        json_part <- sub(".*HTTP \\d+ - ", "", error_string)
        cat("DEBUG: JSON part:", json_part, "\n")
        
        tryCatch({
          error_data <- jsonlite::fromJSON(json_part)
          if (!is.null(error_data$detail)) {
            cat("DEBUG: Extracted detail:", error_data$detail, "\n")
            return(error_data$detail)
          }
        }, error = function(e) {
          cat("DEBUG: JSON parsing error:", e$message, "\n")
        })
      }
      return(error_string)
    }

    # Render tree (collapsed by default)
    # NOTE: shinyTree automatically creates both input and output bindings with the same ID
    # The "Shared input/output ID" warnings are expected behavior for this widget
    # shinyTree needs both to function: input for selections, output for rendering
    output$tree_display <- shinyTree::renderTree({
      build_tree_data()
    })

    # Helper function to walk the shinyTree input and find selected paths
    # shinyTree marks selected nodes with the "stselected" attribute
    find_selected_paths <- function(tree, path = character()) {
      out <- list()
      if (length(tree) == 0) return(out)
      
      for (nm in names(tree)) {
        child <- tree[[nm]]
        this_path <- c(path, nm)
        
        # Check if this node is selected
        is_selected <- isTRUE(attr(child, "stselected"))
        
        if (is_selected) {
          out <- c(out, list(this_path))
        }
        
        # Recursively check children
        if (is.list(child)) {
          out <- c(out, find_selected_paths(child, this_path))
        }
      }
      out
    }
    
    # Track selection; enable/disable buttons accordingly
    observeEvent(input$tree_display, {
      # Default: nothing selected
      selected_node(list(type = NULL, label = NULL, path = NULL))
      
      # Enable Add Child by default; disable only when an effort is selected
      shinyjs::enable(ns("add_child"))
      
      # Find all selected paths in the tree
      selected_paths <- find_selected_paths(input$tree_display)
      
      # We only support single selection, so take the first path if any
      if (length(selected_paths) > 0) {
        path_components <- selected_paths[[1]]
        path_depth <- length(path_components)
        
        if (path_depth == 1) {
          # Top level = study
          selected_label <- path_components[1]
          selected_node(list(type = "study", label = selected_label, path = path_components))
        } else if (path_depth == 2) {
          # Second level = database release
          selected_label <- path_components[2]
          selected_node(list(type = "release", label = selected_label, path = path_components))
        } else if (path_depth == 3) {
          # Third level = reporting effort
          selected_label <- path_components[3]
          selected_node(list(type = "effort", label = selected_label, path = path_components))
          # Disable Add Child for efforts
          shinyjs::disable(ns("add_child"))
        }
      }
    }, ignoreNULL = FALSE, ignoreInit = FALSE)

    # Refresh tree
    observeEvent(input$refresh_tree, {
      output$tree_display <- shinyTree::renderTree({ build_tree_data() })
      last_update(Sys.time())
    })

    # Add Study (reuse studies module behavior)
    observeEvent(input$add_study, {
      showModal(modalDialog(
        title = tagList(bs_icon("plus-lg"), "Add Study"),
        size = "m",
        easyClose = FALSE,
        textInput(ns("new_study_label"), label = NULL, placeholder = "Enter unique study identifier"),
        footer = div(
          class = "d-flex justify-content-end gap-2",
          input_task_button(ns("cancel_add_study"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-secondary"),
          input_task_button(ns("save_add_study"), tagList(bs_icon("check"), "Create"), class = "btn btn-success")
        )
      ))
    })

    observeEvent(input$cancel_add_study, { 
      iv_study_new$disable()  # Disable validation on cancel
      removeModal() 
    })

    observeEvent(input$save_add_study, {
      # Enable validation and check
      iv_study_new$enable()
      if (!iv_study_new$is_valid()) {
        return()  # Don't proceed if validation fails
      }
      
      label <- trimws(input$new_study_label %||% "")
      if (nzchar(label)) {
        # Check for duplicate before sending to backend
        existing_label <- check_duplicate_study(label)
        if (existing_label != FALSE) {
          # Show duplicate error modal
          removeModal()
          Sys.sleep(0.1)  # Small delay to ensure modal is removed
          showModal(modalDialog(
            title = tagList(bs_icon("exclamation-triangle"), "Study Already Exists"),
            div(
              class = "alert alert-warning",
              tags$p(tags$strong("Cannot create study:")),
              tags$p("A study with similar label already exists: ", tags$strong(existing_label)),
              tags$hr(),
              tags$small("Each study must have a unique label (comparison ignores spaces and case).")
            ),
            footer = input_task_button(
              ns("close_duplicate_study_error"), 
              tagList(bs_icon("x"), "Close"), 
              class = "btn btn-secondary"
            ),
            easyClose = TRUE
          ))
          observeEvent(input$close_duplicate_study_error, { 
            removeModal() 
          }, once = TRUE, ignoreInit = TRUE)
          return()
        }
        
        res <- create_study(list(study_label = label))
        if (!is.null(res$error)) {
          # Check if it's a duplicate error from backend
          if (parse_error_for_duplicate(res$error)) {
            clean_msg <- extract_error_message(res$error)
            removeModal()
            Sys.sleep(0.1)
            showModal(modalDialog(
              title = tagList(bs_icon("exclamation-triangle"), "Study Already Exists"),
              div(
                class = "alert alert-warning",
                tags$p(tags$strong("Cannot create study:")),
                tags$p(clean_msg),
                tags$hr(),
                tags$small("Each study must have a unique label (comparison ignores spaces and case).")
              ),
              footer = input_task_button(
                ns("close_duplicate_study_error"), 
                tagList(bs_icon("x"), "Close"), 
                class = "btn btn-secondary"
              ),
              easyClose = TRUE
            ))
            observeEvent(input$close_duplicate_study_error, { 
              removeModal() 
            }, once = TRUE, ignoreInit = TRUE)
          } else {
            showNotification(paste("Error creating study:", res$error), type = "error")
            removeModal()
            iv_study_new$disable()
          }
        } else {
          showNotification("Study created", type = "message")
          removeModal()
          iv_study_new$disable()  # Disable validation after successful creation
          output$tree_display <- shinyTree::renderTree({ build_tree_data() })
          last_update(Sys.time())
        }
      }
    })

    # Utility to find selected node metadata by walking built tree and matching name
    find_selected_info <- function() {
      sel <- shinyTree::get_selected(input$tree_display, format = "names")
      if (length(sel) == 0) return(NULL)
      selected_label <- sel[[1]]
      # Rebuild tree to traverse attributes
      tree <- build_tree_data()

      # Depth-first search
      stack <- list(tree)
      while (length(stack) > 0) {
        node <- stack[[1]]; stack <- stack[-1]
        if (is.list(node)) {
          node_names <- names(node)
          # node itself can be a subtree; attributes live on the list
          node_info <- attr(node, "stinfo", exact = TRUE)
          node_name <- names(attributes(node))[names(attributes(node)) == "names"]
        }
      }
      NULL
    }

    # Add Child
    observeEvent(input$add_child, {
      # Use the selected_node reactive that was set by the selection observer
      node <- selected_node()
      
      if (is.null(node$type)) {
        showNotification("Select a study or database release to add a child", type = "warning")
        return()
      }
      
      # Get data for context
      releases <- get_database_releases()
      efforts <- get_reporting_efforts()
      studies <- get_studies()
      
      # Handle based on selected type
      if (node$type == "study") {
        # Find the study by label
        study_hit <- NULL
        for (s in studies) { 
          if (s$study_label == node$label) { 
            study_hit <- s
            break 
          } 
        }
        
        if (!is.null(study_hit)) {
        # Add Database Release to this study
        showModal(modalDialog(
          title = tagList(bs_icon("plus"), "Add Database Release"),
          textInput(ns("new_release_label"), NULL, placeholder = "Enter database release label"),
          footer = div(class = "d-flex justify-content-end gap-2",
            input_task_button(ns("cancel_add_release"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-secondary"),
            input_task_button(ns("save_add_release"), tagList(bs_icon("check"), "Create"), class = "btn btn-success")
          )
        ))
        observeEvent(input$cancel_add_release, { 
          iv_release_new$disable()  # Disable validation on cancel
          removeModal() 
        }, once = TRUE, ignoreInit = TRUE)
        observeEvent(input$save_add_release, {
          # Enable validation and check
          iv_release_new$enable()
          if (!iv_release_new$is_valid()) {
            return()  # Don't proceed if validation fails
          }
          
          label <- trimws(input$new_release_label %||% "")
          if (!nzchar(label)) return()
          
          # Check for duplicate before sending to backend
          existing_label <- check_duplicate_release(study_hit$id, label)
          if (existing_label != FALSE) {
            # Show duplicate error modal
            removeModal()
            Sys.sleep(0.1)  # Small delay to ensure modal is removed
            showModal(modalDialog(
              title = tagList(bs_icon("exclamation-triangle"), "Database Release Already Exists"),
              div(
                class = "alert alert-warning",
                tags$p(tags$strong("Cannot create database release:")),
                tags$p("A database release with similar label already exists: ", tags$strong(existing_label)),
                tags$hr(),
                tags$small("Each database release must have a unique label within its study (comparison ignores spaces and case).")
              ),
              footer = input_task_button(
                ns("close_duplicate_release_error"), 
                tagList(bs_icon("x"), "Close"), 
                class = "btn btn-secondary"
              ),
              easyClose = TRUE
            ))
            observeEvent(input$close_duplicate_release_error, { 
              removeModal() 
            }, once = TRUE, ignoreInit = TRUE)
            return()
          }
          
          res <- create_database_release(list(study_id = study_hit$id, database_release_label = label))
          if (!is.null(res$error)) {
            # Check if it's a duplicate error
            if (parse_error_for_duplicate(res$error)) {
              clean_msg <- extract_error_message(res$error)
              # First remove the current modal, then show error modal
              removeModal()
              Sys.sleep(0.1)  # Small delay to ensure modal is removed
              showModal(modalDialog(
                title = tagList(bs_icon("exclamation-triangle"), "Database Release Already Exists"),
                div(
                  class = "alert alert-warning",
                  tags$p(tags$strong("Cannot create database release:")),
                  tags$p(clean_msg),
                  tags$hr(),
                  tags$small("Each database release must have a unique label within its study.")
                ),
                footer = input_task_button(
                  ns("close_duplicate_release_error"), 
                  tagList(bs_icon("x"), "Close"), 
                  class = "btn btn-secondary"
                ),
                easyClose = TRUE
              ))
              observeEvent(input$close_duplicate_release_error, { 
                removeModal() 
              }, once = TRUE, ignoreInit = TRUE)
            } else {
              showNotification(paste("Error creating release:", res$error), type = "error")
              removeModal()  # Also remove modal on other errors
              iv_release_new$disable()
            }
          } else {
            showNotification("Database release created", type = "message")
            removeModal()
            iv_release_new$disable()  # Disable validation after successful creation
            output$tree_display <- shinyTree::renderTree({ build_tree_data() })
            last_update(Sys.time())
          }
        }, once = TRUE, ignoreInit = TRUE)
        return()
      }
      } else if (node$type == "release") {
        # Find the release - use both the release label AND the parent study from path
        release_hit <- NULL
        if (length(node$path) >= 2) {
          study_label <- node$path[1]
          release_label <- node$path[2]
          
          # Find the study first
          study_id <- NULL
          for (s in studies) {
            if (s$study_label == study_label) {
              study_id <- s$id
              break
            }
          }
          
          # Then find the release that belongs to this study
          if (!is.null(study_id)) {
            for (r in releases) {
              if (r$database_release_label == release_label && r$study_id == study_id) {
                release_hit <- r
                break
              }
            }
          }
        }
        
        if (!is.null(release_hit)) {
        # Add Reporting Effort under this release
        showModal(modalDialog(
          title = tagList(bs_icon("plus"), "Add Reporting Effort"),
          textInput(ns("new_effort_label"), NULL, placeholder = "Enter reporting effort label"),
          footer = div(class = "d-flex justify-content-end gap-2",
            input_task_button(ns("cancel_add_effort"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-secondary"),
            input_task_button(ns("save_add_effort"), tagList(bs_icon("check"), "Create"), class = "btn btn-success")
          )
        ))
        observeEvent(input$cancel_add_effort, { 
          iv_effort_new$disable()  # Disable validation on cancel
          removeModal() 
        }, once = TRUE, ignoreInit = TRUE)
        observeEvent(input$save_add_effort, {
          # Enable validation and check
          iv_effort_new$enable()
          if (!iv_effort_new$is_valid()) {
            return()  # Don't proceed if validation fails
          }
          
          label <- trimws(input$new_effort_label %||% "")
          if (!nzchar(label)) return()
          
          # Check for duplicate before sending to backend
          existing_label <- check_duplicate_effort(release_hit$id, label)
          if (existing_label != FALSE) {
            # Show duplicate error modal
            removeModal()
            Sys.sleep(0.1)  # Small delay to ensure modal is removed
            showModal(modalDialog(
              title = tagList(bs_icon("exclamation-triangle"), "Reporting Effort Already Exists"),
              div(
                class = "alert alert-warning",
                tags$p(tags$strong("Cannot create reporting effort:")),
                tags$p("A reporting effort with similar label already exists: ", tags$strong(existing_label)),
                tags$hr(),
                tags$small("Each reporting effort must have a unique label within its database release (comparison ignores spaces and case).")
              ),
              footer = input_task_button(
                ns("close_duplicate_effort_error"), 
                tagList(bs_icon("x"), "Close"), 
                class = "btn btn-secondary"
              ),
              easyClose = TRUE
            ))
            observeEvent(input$close_duplicate_effort_error, { 
              removeModal() 
            }, once = TRUE, ignoreInit = TRUE)
            return()
          }
          
          res <- create_reporting_effort(list(
            study_id = release_hit$study_id,
            database_release_id = release_hit$id,
            database_release_label = label
          ))
          if (!is.null(res$error)) {
            # Check if it's a duplicate error
            if (parse_error_for_duplicate(res$error)) {
              clean_msg <- extract_error_message(res$error)
              # First remove the current modal, then show error modal
              removeModal()
              Sys.sleep(0.1)  # Small delay to ensure modal is removed
              showModal(modalDialog(
                title = tagList(bs_icon("exclamation-triangle"), "Reporting Effort Already Exists"),
                div(
                  class = "alert alert-warning",
                  tags$p(tags$strong("Cannot create reporting effort:")),
                  tags$p(clean_msg),
                  tags$hr(),
                  tags$small("Each reporting effort must have a unique label within its database release.")
                ),
                footer = input_task_button(
                  ns("close_duplicate_effort_error"), 
                  tagList(bs_icon("x"), "Close"), 
                  class = "btn btn-secondary"
                ),
                easyClose = TRUE
              ))
              observeEvent(input$close_duplicate_effort_error, { 
                removeModal() 
              }, once = TRUE, ignoreInit = TRUE)
            } else {
              showNotification(paste("Error creating reporting effort:", res$error), type = "error")
              removeModal()  # Also remove modal on other errors
              iv_effort_new$disable()
            }
          } else {
            showNotification("Reporting effort created", type = "message")
            removeModal()
            iv_effort_new$disable()  # Disable validation after successful creation
            output$tree_display <- shinyTree::renderTree({ build_tree_data() })
            last_update(Sys.time())
          }
        }, once = TRUE, ignoreInit = TRUE)
        return()
      }
      
      # If the label matches a reporting effort, do nothing and warn
      effort_hit <- NULL
      for (e in efforts) { if (e$database_release_label == node$label) { effort_hit <- e; break } }
      if (!is.null(effort_hit)) {
        showNotification("Add Child is disabled for Reporting Efforts", type = "warning")
        return()
      }
      
    }

      showNotification("Please select a study or a database release", type = "warning")
    })

    # Edit selected item
    observeEvent(input$edit_selected, {
      # Use the selected_node reactive that was set by the selection observer
      node <- selected_node()
      
      if (is.null(node$type)) {
        showNotification("Select an item to edit", type = "warning")
        return()
      }
      
      # Get data
      studies <- get_studies()
      releases <- get_database_releases()
      efforts <- get_reporting_efforts()
      
      # Handle based on type
      if (node$type == "study") {
        # Find the study
        for (s in studies) {
          if (s$study_label == node$label) {
          # Change input ID to edit_label for validation
          iv_edit$enable()  # Enable validation
          showModal(modalDialog(
            title = tagList(bs_icon("pencil"), "Edit Study"),
            textInput(ns("edit_label"), NULL, value = s$study_label),
            footer = div(class = "d-flex justify-content-end gap-2",
              input_task_button(ns("cancel_edit_study"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-secondary"),
              input_task_button(ns("save_edit_study"), tagList(bs_icon("check"), "Save"), class = "btn btn-warning")
            )
          ))
          observeEvent(input$cancel_edit_study, { 
            iv_edit$disable()  # Disable validation on cancel
            removeModal() 
          }, once = TRUE)
          observeEvent(input$save_edit_study, {
            # Validate first
            if (!iv_edit$is_valid()) {
              return()  # Don't proceed if validation fails
            }
            
            lbl <- trimws(input$edit_label %||% "")
            if (!nzchar(lbl)) return()
            
            # Check for duplicate before sending to backend (exclude current study)
            existing_label <- check_duplicate_study(lbl, s$id)
            if (existing_label != FALSE) {
              # Show duplicate error modal
              removeModal()
              Sys.sleep(0.1)  # Small delay to ensure modal is removed
              showModal(modalDialog(
                title = tagList(bs_icon("exclamation-triangle"), "Study Already Exists"),
                div(
                  class = "alert alert-warning",
                  tags$p(tags$strong("Cannot update study:")),
                  tags$p("A study with similar label already exists: ", tags$strong(existing_label)),
                  tags$hr(),
                  tags$small("Each study must have a unique label (comparison ignores spaces and case).")
                ),
                footer = input_task_button(
                  ns("close_duplicate_study_edit_error"), 
                  tagList(bs_icon("x"), "Close"), 
                  class = "btn btn-secondary"
                ),
                easyClose = TRUE
              ))
              observeEvent(input$close_duplicate_study_edit_error, { 
                removeModal() 
              }, once = TRUE, ignoreInit = TRUE)
              return()
            }
            
            res <- update_study(s$id, list(study_label = lbl))
            if (!is.null(res$error)) {
              # Check if it's a duplicate error from backend
              if (parse_error_for_duplicate(res$error)) {
                clean_msg <- extract_error_message(res$error)
                removeModal()
                Sys.sleep(0.1)
                showModal(modalDialog(
                  title = tagList(bs_icon("exclamation-triangle"), "Study Already Exists"),
                  div(
                    class = "alert alert-warning",
                    tags$p(tags$strong("Cannot update study:")),
                    tags$p(clean_msg),
                    tags$hr(),
                    tags$small("Each study must have a unique label (comparison ignores spaces and case).")
                  ),
                  footer = input_task_button(
                    ns("close_duplicate_study_edit_error"), 
                    tagList(bs_icon("x"), "Close"), 
                    class = "btn btn-secondary"
                  ),
                  easyClose = TRUE
                ))
                observeEvent(input$close_duplicate_study_edit_error, { 
                  removeModal() 
                }, once = TRUE, ignoreInit = TRUE)
              } else {
                showNotification(paste("Error updating study:", res$error), type = "error")
                removeModal()
                iv_edit$disable()
              }
            } else {
              showNotification("Study updated", type = "message")
              removeModal()
              iv_edit$disable()  # Disable validation after successful update
              output$tree_display <- shinyTree::renderTree({ build_tree_data() })
              last_update(Sys.time())
            }
          }, once = TRUE, ignoreInit = TRUE)
            return()
          }
        }
      } else if (node$type == "release") {
        # Find the release using path information
        if (length(node$path) >= 2) {
          study_label <- node$path[1]
          release_label <- node$path[2]
          
          # Find the study first
          study_id <- NULL
          for (s in studies) {
            if (s$study_label == study_label) {
              study_id <- s$id
              break
            }
          }
          
          # Then find the release that belongs to this study
          if (!is.null(study_id)) {
            for (r in releases) {
              if (r$database_release_label == release_label && r$study_id == study_id) {
          # Change input ID to edit_label for validation
          iv_edit$enable()  # Enable validation
          showModal(modalDialog(
            title = tagList(bs_icon("pencil"), "Edit Database Release"),
            textInput(ns("edit_label"), NULL, value = r$database_release_label),
            footer = div(class = "d-flex justify-content-end gap-2",
              input_task_button(ns("cancel_edit_release"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-secondary"),
              input_task_button(ns("save_edit_release"), tagList(bs_icon("check"), "Save"), class = "btn btn-warning")
            )
          ))
          observeEvent(input$cancel_edit_release, { 
            iv_edit$disable()  # Disable validation on cancel
            removeModal() 
          }, once = TRUE)
          observeEvent(input$save_edit_release, {
            # Validate first
            if (!iv_edit$is_valid()) {
              return()  # Don't proceed if validation fails
            }
            
            lbl <- trimws(input$edit_label %||% "")
            if (!nzchar(lbl)) return()
            
            # Check for duplicate before sending to backend (exclude current release)
            existing_label <- check_duplicate_release(r$study_id, lbl, r$id)
            if (existing_label != FALSE) {
              # Show duplicate error modal
              removeModal()
              Sys.sleep(0.1)  # Small delay to ensure modal is removed
              showModal(modalDialog(
                title = tagList(bs_icon("exclamation-triangle"), "Database Release Already Exists"),
                div(
                  class = "alert alert-warning",
                  tags$p(tags$strong("Cannot update database release:")),
                  tags$p("A database release with similar label already exists: ", tags$strong(existing_label)),
                  tags$hr(),
                  tags$small("Each database release must have a unique label within its study (comparison ignores spaces and case).")
                ),
                footer = input_task_button(
                  ns("close_duplicate_release_edit_error"), 
                  tagList(bs_icon("x"), "Close"), 
                  class = "btn btn-secondary"
                ),
                easyClose = TRUE
              ))
              observeEvent(input$close_duplicate_release_edit_error, { 
                removeModal() 
              }, once = TRUE, ignoreInit = TRUE)
              return()
            }
            
            res <- update_database_release(r$id, list(study_id = r$study_id, database_release_label = lbl))
            if (!is.null(res$error)) {
              # Check if it's a duplicate error
              if (parse_error_for_duplicate(res$error)) {
                clean_msg <- extract_error_message(res$error)
                # First remove the current modal, then show error modal
                removeModal()
                Sys.sleep(0.1)  # Small delay to ensure modal is removed
                showModal(modalDialog(
                  title = tagList(bs_icon("exclamation-triangle"), "Database Release Already Exists"),
                  div(
                    class = "alert alert-warning",
                    tags$p(tags$strong("Cannot update database release:")),
                    tags$p(clean_msg),
                    tags$hr(),
                    tags$small("Each database release must have a unique label within its study.")
                  ),
                  footer = input_task_button(
                    ns("close_duplicate_release_edit_error"), 
                    tagList(bs_icon("x"), "Close"), 
                    class = "btn btn-secondary"
                  ),
                  easyClose = TRUE
                ))
                observeEvent(input$close_duplicate_release_edit_error, { 
                  removeModal() 
                }, once = TRUE, ignoreInit = TRUE)
              } else {
                showNotification(paste("Error updating release:", res$error), type = "error")
                removeModal()  # Also remove modal on other errors
                iv_edit$disable()
              }
            } else {
              showNotification("Database release updated", type = "message")
              removeModal()
              iv_edit$disable()  # Disable validation after successful update
              output$tree_display <- shinyTree::renderTree({ build_tree_data() })
              last_update(Sys.time())
            }
          }, once = TRUE, ignoreInit = TRUE)
              }
            }
          }
        }
      } else if (node$type == "effort") {
        # Find the effort using path information
        if (length(node$path) >= 3) {
          study_label <- node$path[1]
          release_label <- node$path[2]
          effort_label <- node$path[3]
          
          # Find the study first
          study_id <- NULL
          for (s in studies) {
            if (s$study_label == study_label) {
              study_id <- s$id
              break
            }
          }
          
          # Then find the release
          release_id <- NULL
          if (!is.null(study_id)) {
            for (r in releases) {
              if (r$database_release_label == release_label && r$study_id == study_id) {
                release_id <- r$id
                break
              }
            }
          }
          
          # Finally find the effort
          if (!is.null(release_id)) {
            for (e in efforts) {
              if (e$database_release_label == effort_label && e$database_release_id == release_id) {
          # Change input ID to edit_label for validation
          iv_edit$enable()  # Enable validation
          showModal(modalDialog(
            title = tagList(bs_icon("pencil"), "Edit Reporting Effort"),
            textInput(ns("edit_label"), NULL, value = e$database_release_label),
            footer = div(class = "d-flex justify-content-end gap-2",
              input_task_button(ns("cancel_edit_effort"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-secondary"),
              input_task_button(ns("save_edit_effort"), tagList(bs_icon("check"), "Save"), class = "btn btn-warning")
            )
          ))
          observeEvent(input$cancel_edit_effort, { 
            iv_edit$disable()  # Disable validation on cancel
            removeModal() 
          }, once = TRUE)
          observeEvent(input$save_edit_effort, {
            # Validate first
            if (!iv_edit$is_valid()) {
              return()  # Don't proceed if validation fails
            }
            
            lbl <- trimws(input$edit_label %||% "")
            if (!nzchar(lbl)) return()
            
            # Check for duplicate before sending to backend (exclude current effort)
            existing_label <- check_duplicate_effort(e$database_release_id, lbl, e$id)
            if (existing_label != FALSE) {
              # Show duplicate error modal
              removeModal()
              Sys.sleep(0.1)  # Small delay to ensure modal is removed
              showModal(modalDialog(
                title = tagList(bs_icon("exclamation-triangle"), "Reporting Effort Already Exists"),
                div(
                  class = "alert alert-warning",
                  tags$p(tags$strong("Cannot update reporting effort:")),
                  tags$p("A reporting effort with similar label already exists: ", tags$strong(existing_label)),
                  tags$hr(),
                  tags$small("Each reporting effort must have a unique label within its database release (comparison ignores spaces and case).")
                ),
                footer = input_task_button(
                  ns("close_duplicate_effort_edit_error"), 
                  tagList(bs_icon("x"), "Close"), 
                  class = "btn btn-secondary"
                ),
                easyClose = TRUE
              ))
              observeEvent(input$close_duplicate_effort_edit_error, { 
                removeModal() 
              }, once = TRUE, ignoreInit = TRUE)
              return()
            }
            
            res <- update_reporting_effort(e$id, list(study_id = e$study_id, database_release_id = e$database_release_id, database_release_label = lbl))
            if (!is.null(res$error)) {
              # Check if it's a duplicate error
              if (parse_error_for_duplicate(res$error)) {
                clean_msg <- extract_error_message(res$error)
                # First remove the current modal, then show error modal
                removeModal()
                Sys.sleep(0.1)  # Small delay to ensure modal is removed
                showModal(modalDialog(
                  title = tagList(bs_icon("exclamation-triangle"), "Reporting Effort Already Exists"),
                  div(
                    class = "alert alert-warning",
                    tags$p(tags$strong("Cannot update reporting effort:")),
                    tags$p(clean_msg),
                    tags$hr(),
                    tags$small("Each reporting effort must have a unique label within its database release.")
                  ),
                  footer = input_task_button(
                    ns("close_duplicate_effort_edit_error"), 
                    tagList(bs_icon("x"), "Close"), 
                    class = "btn btn-secondary"
                  ),
                  easyClose = TRUE
                ))
                observeEvent(input$close_duplicate_effort_edit_error, { 
                  removeModal() 
                }, once = TRUE, ignoreInit = TRUE)
              } else {
                showNotification(paste("Error updating reporting effort:", res$error), type = "error")
                removeModal()  # Also remove modal on other errors
                iv_edit$disable()
              }
            } else {
              showNotification("Reporting effort updated", type = "message")
              removeModal()
              iv_edit$disable()  # Disable validation after successful update
              output$tree_display <- shinyTree::renderTree({ build_tree_data() })
              last_update(Sys.time())
            }
          }, once = TRUE, ignoreInit = TRUE)
              }
            }
          }
        }
      }
    })

    # Delete selected item with child checks akin to data management modules
    observeEvent(input$delete_selected, {
      # Use the selected_node reactive that was set by the selection observer
      node <- selected_node()
      
      if (is.null(node$type)) {
        showNotification("Select an item to delete", type = "warning")
        return()
      }
      
      # Get data
      studies <- get_studies()
      releases <- get_database_releases()
      efforts <- get_reporting_efforts()
      
      # Handle based on type
      if (node$type == "study") {
        # Find the study
        for (s in studies) {
          if (s$study_label == node$label) {
        releases <- get_database_releases();
        rels <- Filter(function(r) r$study_id == s$id, if (!is.null(releases$error)) list() else releases)
        if (length(rels) > 0) {
          showModal(modalDialog(
            title = tagList(bs_icon("exclamation-triangle"), "Cannot Delete Study"),
            div(class = "alert alert-warning", "This study has associated database releases and cannot be deleted."),
            footer = input_task_button(ns("close_blocked"), tagList(bs_icon("x"), "Close"), class = "btn btn-secondary")
          ))
          observeEvent(input$close_blocked, { removeModal() }, once = TRUE)
        } else {
          showModal(modalDialog(
            title = tagList(bs_icon("exclamation-triangle"), "Confirm Deletion"),
            p("Delete study:", tags$strong(s$study_label), "?"),
            footer = div(class = "d-flex justify-content-end gap-2",
              input_task_button(ns("cancel_delete_study"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-outline-secondary"),
              input_task_button(ns("confirm_delete_study"), tagList(bs_icon("trash"), "Delete"), class = "btn btn-danger")
            )
          ))
          observeEvent(input$cancel_delete_study, { removeModal() }, once = TRUE)
          observeEvent(input$confirm_delete_study, {
            res <- delete_study(s$id)
            if (!is.null(res$error)) showNotification(paste("Error:", res$error), type = "error") else {
              showNotification("Study deleted", type = "message"); removeModal(); output$study_tree <- shinyTree::renderTree({ build_tree_data() }); last_update(Sys.time())
            }
          }, once = TRUE)
        }
            return()
          }
        }
      } else if (node$type == "release") {
        # Find the release using path information
        if (length(node$path) >= 2) {
          study_label <- node$path[1]
          release_label <- node$path[2]
          
          # Find the study first
          study_id <- NULL
          for (s in studies) {
            if (s$study_label == study_label) {
              study_id <- s$id
              break
            }
          }
          
          # Then find the release that belongs to this study
          if (!is.null(study_id)) {
            for (r in releases) {
              if (r$database_release_label == release_label && r$study_id == study_id) {
        efforts <- get_reporting_efforts();
        effs <- Filter(function(e) e$database_release_id == r$id, if (!is.null(efforts$error)) list() else efforts)
        if (length(effs) > 0) {
          showModal(modalDialog(
            title = tagList(bs_icon("exclamation-triangle"), "Cannot Delete Database Release"),
            div(class = "alert alert-warning", "This database release has associated reporting efforts and cannot be deleted."),
            footer = input_task_button(ns("close_blocked2"), tagList(bs_icon("x"), "Close"), class = "btn btn-secondary")
          ))
          observeEvent(input$close_blocked2, { removeModal() }, once = TRUE)
        } else {
          showModal(modalDialog(
            title = tagList(bs_icon("exclamation-triangle"), "Confirm Deletion"),
            p("Delete database release:", tags$strong(r$database_release_label), "?"),
            footer = div(class = "d-flex justify-content-end gap-2",
              input_task_button(ns("cancel_delete_release"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-outline-secondary"),
              input_task_button(ns("confirm_delete_release"), tagList(bs_icon("trash"), "Delete"), class = "btn btn-danger")
            )
          ))
          observeEvent(input$cancel_delete_release, { removeModal() }, once = TRUE)
          observeEvent(input$confirm_delete_release, {
            res <- delete_database_release(r$id)
            if (!is.null(res$error)) showNotification(paste("Error:", res$error), type = "error") else {
              showNotification("Database release deleted", type = "message"); removeModal(); output$study_tree <- shinyTree::renderTree({ build_tree_data() }); last_update(Sys.time())
            }
          }, once = TRUE)
        }
              }
            }
          }
        }
      } else if (node$type == "effort") {
        # Find the effort using path information
        if (length(node$path) >= 3) {
          study_label <- node$path[1]
          release_label <- node$path[2]
          effort_label <- node$path[3]
          
          # Find the study first
          study_id <- NULL
          for (s in studies) {
            if (s$study_label == study_label) {
              study_id <- s$id
              break
            }
          }
          
          # Then find the release
          release_id <- NULL
          if (!is.null(study_id)) {
            for (r in releases) {
              if (r$database_release_label == release_label && r$study_id == study_id) {
                release_id <- r$id
                break
              }
            }
          }
          
          # Finally find the effort
          if (!is.null(release_id)) {
            for (e in efforts) {
              if (e$database_release_label == effort_label && e$database_release_id == release_id) {
        showModal(modalDialog(
          title = tagList(bs_icon("exclamation-triangle"), "Confirm Deletion"),
          p("Delete reporting effort:", tags$strong(e$database_release_label), "?"),
          footer = div(class = "d-flex justify-content-end gap-2",
            input_task_button(ns("cancel_delete_effort"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-outline-secondary"),
            input_task_button(ns("confirm_delete_effort"), tagList(bs_icon("trash"), "Delete"), class = "btn btn-danger")
          )
        ))
        observeEvent(input$cancel_delete_effort, { removeModal() }, once = TRUE)
        observeEvent(input$confirm_delete_effort, {
          res <- delete_reporting_effort(e$id)
          if (!is.null(res$error)) showNotification(paste("Error:", res$error), type = "error") else {
            showNotification("Reporting effort deleted", type = "message"); removeModal(); output$study_tree <- shinyTree::renderTree({ build_tree_data() }); last_update(Sys.time())
          }
        }, once = TRUE)
              }
            }
          }
        }
      }
    })


    # Status outputs
    output$status_message <- renderText({
      "Use the toolbar to add/edit/delete items."
    })
    output$selection_display <- renderText({
      s <- selected_node()
      if (is.null(s$type) || is.null(s$label)) {
        return("Selection: none")
      }
      
      type_label <- switch(s$type,
        study = "Study",
        release = "Database Release",
        effort = "Reporting Effort",
        "Item"
      )
      
      paste0("Selection: ", type_label, " — ", s$label)
    })
    output$last_updated_display <- renderText({ paste("Updated:", format(last_update(), "%H:%M:%S")) })
  })
}


