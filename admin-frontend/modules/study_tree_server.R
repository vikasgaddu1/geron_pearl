study_tree_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns

    last_update <- reactiveVal(Sys.time())
    selected_node <- reactiveVal(NULL)

    # Load hierarchical data from APIs and build tree structure
    build_tree_data <- function() {
      studies <- get_studies()
      if (!is.null(studies$error)) return(list())

      releases <- get_database_releases()
      if (!is.null(releases$error)) releases <- list()

      efforts <- get_reporting_efforts()
      if (!is.null(efforts$error)) efforts <- list()

      # index by study and release
      releases_by_study <- split(releases, vapply(releases, function(x) x$study_id, numeric(1)))
      efforts_by_release <- split(efforts, vapply(efforts, function(x) x$database_release_id, numeric(1)))

      # Build shinyTree expected nested named list
      tree <- lapply(studies, function(study) {
        study_id <- study$id
        study_label <- study$study_label

        study_children <- lapply(releases_by_study[[as.character(study_id)]] %||% list(), function(rel) {
          rel_id <- rel$id
          rel_label <- rel$database_release_label

          rel_children <- lapply(efforts_by_release[[as.character(rel_id)]] %||% list(), function(eff) {
            eff_id <- eff$id
            eff_label <- eff$database_release_label
            structure(list(), stinfo = list(type = "effort", id = eff_id, study_id = eff$study_id, release_id = eff$database_release_id), sticon = "journal-plus", names = eff_label)
          })

          structure(rel_children, stinfo = list(type = "release", id = rel_id, study_id = rel$study_id), sticon = "database", names = rel_label)
        })

        structure(study_children, stinfo = list(type = "study", id = study_id), sticon = "mortarboard", names = study_label)
      })

      names(tree) <- vapply(studies, function(s) s$study_label, character(1))
      tree
    }

    # Helper null-coalescing for lists
    `%||%` <- function(x, y) if (is.null(x)) y else x

    # Render tree
    output$study_tree <- shinyTree::renderTree({
      build_tree_data()
    })

    # Track selection; enable/disable buttons accordingly
    observeEvent(input$study_tree, {
      sel <- shinyTree::get_selected(input$study_tree, format = "names")
      # get node data via get_selected with format = "slices" is not available; we can use input$study_tree_full to inspect attributes
      selected_node(sel)
      # Disable Add Child when an effort is selected (only study or release allowed)
      node_info <- tryCatch({ shinyTree::get_selected(input$study_tree, format = "classid") }, error = function(e) NULL)
      # Fallback: use internal data stored in input$study_tree (tree with attributes)
      # We will compute on server side after resolving by name when performing actions
    })

    # Refresh tree
    observeEvent(input$refresh_tree, {
      output$study_tree <- shinyTree::renderTree({ build_tree_data() })
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

    observeEvent(input$cancel_add_study, { removeModal() })

    observeEvent(input$save_add_study, {
      label <- trimws(input$new_study_label %||% "")
      if (nzchar(label)) {
        res <- create_study(list(study_label = label))
        if (!is.null(res$error)) {
          showNotification(paste("Error creating study:", res$error), type = "error")
        } else {
          showNotification("Study created", type = "message")
          removeModal()
          output$study_tree <- shinyTree::renderTree({ build_tree_data() })
          last_update(Sys.time())
        }
      }
    })

    # Utility to find selected node metadata by walking built tree and matching name
    find_selected_info <- function() {
      sel <- shinyTree::get_selected(input$study_tree, format = "names")
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
      # Determine selection and type
      sel <- shinyTree::get_selected(input$study_tree, format = "names")
      if (length(sel) == 0) {
        showNotification("Select a study or database release to add a child", type = "warning")
        return()
      }

      # We will resolve by rebuilding and walking to find stinfo
      st <- shinyTree::get_selected(input$study_tree, format = "vector")
      # Use internal input$study_tree structure to get attributes
      # As a practical approach, offer a small chooser modal for ambiguous cases

      # Build reference maps for quick lookup
      releases <- get_database_releases()
      efforts <- get_reporting_efforts()
      studies <- get_studies()

      selected_label <- sel[[1]]

      # Try to match label to study first
      study_hit <- NULL
      for (s in studies) { if (identical(s$study_label, selected_label)) { study_hit <- s; break } }
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
        observeEvent(input$cancel_add_release, { removeModal() }, once = TRUE)
        observeEvent(input$save_add_release, {
          label <- trimws(input$new_release_label %||% "")
          if (!nzchar(label)) return()
          res <- create_database_release(list(study_id = study_hit$id, database_release_label = label))
          if (!is.null(res$error)) {
            showNotification(paste("Error creating release:", res$error), type = "error")
          } else {
            showNotification("Database release created", type = "message")
            removeModal()
            output$study_tree <- shinyTree::renderTree({ build_tree_data() })
            last_update(Sys.time())
          }
        }, once = TRUE)
        return()
      }

      # Try to match label to release
      release_hit <- NULL
      for (r in releases) { if (identical(r$database_release_label, selected_label)) { release_hit <- r; break } }
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
        observeEvent(input$cancel_add_effort, { removeModal() }, once = TRUE)
        observeEvent(input$save_add_effort, {
          label <- trimws(input$new_effort_label %||% "")
          if (!nzchar(label)) return()
          res <- create_reporting_effort(list(
            study_id = release_hit$study_id,
            database_release_id = release_hit$id,
            database_release_label = label
          ))
          if (!is.null(res$error)) {
            showNotification(paste("Error creating reporting effort:", res$error), type = "error")
          } else {
            showNotification("Reporting effort created", type = "message")
            removeModal()
            output$study_tree <- shinyTree::renderTree({ build_tree_data() })
            last_update(Sys.time())
          }
        }, once = TRUE)
        return()
      }

      # If the label matches a reporting effort, do nothing and warn
      effort_hit <- NULL
      for (e in efforts) { if (identical(e$database_release_label, selected_label)) { effort_hit <- e; break } }
      if (!is.null(effort_hit)) {
        showNotification("Add Child is disabled for Reporting Efforts", type = "warning")
        return()
      }

      showNotification("Please select a study or a database release", type = "warning")
    })

    # Edit selected item
    observeEvent(input$edit_selected, {
      sel <- shinyTree::get_selected(input$study_tree, format = "names")
      if (length(sel) == 0) { showNotification("Select an item to edit", type = "warning"); return() }
      selected_label <- sel[[1]]

      # Try study
      studies <- get_studies(); if (is.null(studies$error)) {
        for (s in studies) if (identical(s$study_label, selected_label)) {
          showModal(modalDialog(
            title = tagList(bs_icon("pencil"), "Edit Study"),
            textInput(ns("edit_study_label"), NULL, value = s$study_label),
            footer = div(class = "d-flex justify-content-end gap-2",
              input_task_button(ns("cancel_edit_study"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-secondary"),
              input_task_button(ns("save_edit_study"), tagList(bs_icon("check"), "Save"), class = "btn btn-warning")
            )
          ))
          observeEvent(input$cancel_edit_study, { removeModal() }, once = TRUE)
          observeEvent(input$save_edit_study, {
            lbl <- trimws(input$edit_study_label %||% "")
            if (!nzchar(lbl)) return()
            res <- update_study(s$id, list(study_label = lbl))
            if (!is.null(res$error)) {
              showNotification(paste("Error updating study:", res$error), type = "error")
            } else {
              showNotification("Study updated", type = "message"); removeModal(); output$study_tree <- shinyTree::renderTree({ build_tree_data() }); last_update(Sys.time())
            }
          }, once = TRUE)
          return()
        }
      }

      # Try release
      releases <- get_database_releases(); if (is.null(releases$error)) {
        for (r in releases) if (identical(r$database_release_label, selected_label)) {
          showModal(modalDialog(
            title = tagList(bs_icon("pencil"), "Edit Database Release"),
            textInput(ns("edit_release_label"), NULL, value = r$database_release_label),
            footer = div(class = "d-flex justify-content-end gap-2",
              input_task_button(ns("cancel_edit_release"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-secondary"),
              input_task_button(ns("save_edit_release"), tagList(bs_icon("check"), "Save"), class = "btn btn-warning")
            )
          ))
          observeEvent(input$cancel_edit_release, { removeModal() }, once = TRUE)
          observeEvent(input$save_edit_release, {
            lbl <- trimws(input$edit_release_label %||% "")
            if (!nzchar(lbl)) return()
            res <- update_database_release(r$id, list(study_id = r$study_id, database_release_label = lbl))
            if (!is.null(res$error)) {
              showNotification(paste("Error updating release:", res$error), type = "error")
            } else {
              showNotification("Database release updated", type = "message"); removeModal(); output$study_tree <- shinyTree::renderTree({ build_tree_data() }); last_update(Sys.time())
            }
          }, once = TRUE)
          return()
        }
      }

      # Try effort
      efforts <- get_reporting_efforts(); if (is.null(efforts$error)) {
        for (e in efforts) if (identical(e$database_release_label, selected_label)) {
          showModal(modalDialog(
            title = tagList(bs_icon("pencil"), "Edit Reporting Effort"),
            textInput(ns("edit_effort_label"), NULL, value = e$database_release_label),
            footer = div(class = "d-flex justify-content-end gap-2",
              input_task_button(ns("cancel_edit_effort"), tagList(bs_icon("x"), "Cancel"), class = "btn btn-secondary"),
              input_task_button(ns("save_edit_effort"), tagList(bs_icon("check"), "Save"), class = "btn btn-warning")
            )
          ))
          observeEvent(input$cancel_edit_effort, { removeModal() }, once = TRUE)
          observeEvent(input$save_edit_effort, {
            lbl <- trimws(input$edit_effort_label %||% "")
            if (!nzchar(lbl)) return()
            res <- update_reporting_effort(e$id, list(study_id = e$study_id, database_release_id = e$database_release_id, database_release_label = lbl))
            if (!is.null(res$error)) {
              showNotification(paste("Error updating reporting effort:", res$error), type = "error")
            } else {
              showNotification("Reporting effort updated", type = "message"); removeModal(); output$study_tree <- shinyTree::renderTree({ build_tree_data() }); last_update(Sys.time())
            }
          }, once = TRUE)
          return()
        }
      }

      showNotification("Unable to resolve selection for editing", type = "warning")
    })

    # Delete selected item with child checks akin to data management modules
    observeEvent(input$delete_selected, {
      sel <- shinyTree::get_selected(input$study_tree, format = "names")
      if (length(sel) == 0) { showNotification("Select an item to delete", type = "warning"); return() }
      selected_label <- sel[[1]]

      # Try study delete with release children check
      studies <- get_studies();
      for (s in studies) if (identical(s$study_label, selected_label)) {
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

      # Try release delete with effort children check
      releases <- get_database_releases();
      for (r in if (!is.null(releases$error)) list() else releases) if (identical(r$database_release_label, selected_label)) {
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
        return()
      }

      # Try effort delete (no child check needed)
      efforts <- get_reporting_efforts();
      for (e in if (!is.null(efforts$error)) list() else efforts) if (identical(e$database_release_label, selected_label)) {
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
        return()
      }

      showNotification("Unable to resolve selection for deletion", type = "warning")
    })

    # Status outputs
    output$status_message <- renderText({
      "Use the toolbar to add/edit/delete items."
    })
    output$last_updated_display <- renderText({ paste("Updated:", format(last_update(), "%H:%M:%S")) })
  })
}


