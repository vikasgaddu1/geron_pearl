# Comment Expansion Component for DT Tables
# Provides expandable row functionality for inline comment display

library(DT)
library(htmltools)

# Enhanced DT datatable with comment expansion capability
create_expandable_datatable <- function(data, 
                                      comment_column = "Comments", 
                                      tracker_id_column = "tracker_id",
                                      container = NULL,
                                      options = list(),
                                      ...) {
  
  # Add comment button column if not present
  if (!comment_column %in% names(data)) {
    data[[comment_column]] <- sapply(data[[tracker_id_column]], function(tracker_id) {
      create_comment_button_html(tracker_id)
    })
  }
  
  # Enhanced options for row expansion
  enhanced_options <- modifyList(list(
    dom = 'frtip',
    pageLength = 25,
    ordering = TRUE,
    autoWidth = TRUE,
    search = list(regex = TRUE, caseInsensitive = TRUE),
    # Custom callback for row expansion
    drawCallback = htmlwidgets::JS("
      function(settings) {
        // Add click handlers for comment buttons
        $(this.api().table().node()).on('click', '.comment-expand-btn', function() {
          var tr = $(this).closest('tr');
          var row = settings.oInstance.api().row(tr);
          var tracker_id = $(this).data('tracker-id');
          
          if (row.child.isShown()) {
            // Collapse the row
            row.child.hide();
            tr.removeClass('shown');
            $(this).removeClass('btn-warning').addClass('btn-outline-secondary')
                   .find('i').removeClass('bi-chevron-up').addClass('bi-chat');
          } else {
            // Expand the row
            var comment_html = createCommentContainer(tracker_id);
            row.child(comment_html).show();
            tr.addClass('shown');
            $(this).removeClass('btn-outline-secondary').addClass('btn-warning')
                   .find('i').removeClass('bi-chat').addClass('bi-chevron-up');
            
            // Initialize comment data for this row
            loadCommentsForRow(tracker_id);
          }
        });
      }
    ")
  ), options)
  
  DT::datatable(
    data,
    container = container,
    options = enhanced_options,
    escape = FALSE,
    selection = 'none',
    rownames = FALSE,
    ...
  )
}

# Create comment button HTML for each tracker row
create_comment_button_html <- function(tracker_id, comment_count = 0, status = "none") {
  # Determine button styling based on comment status
  button_class <- switch(status,
    "unread" = "btn-danger",
    "resolved" = "btn-success", 
    "pending" = "btn-warning",
    "btn-outline-secondary"  # default
  )
  
  icon_class <- switch(status,
    "unread" = "bi-chat-dots-fill",
    "resolved" = "bi-chat-check",
    "pending" = "bi-chat-text",
    "bi-chat"  # default
  )
  
  # Button text based on status
  button_text <- if (comment_count > 0) {
    switch(status,
      "unread" = paste(comment_count, "New"),
      "resolved" = "Resolved", 
      "pending" = paste(comment_count, "Pending"),
      paste(comment_count, "Comments")
    )
  } else {
    "No Comments"
  }
  
  sprintf(
    '<button class="btn %s btn-sm comment-expand-btn" data-tracker-id="%s" title="Click to expand comments">
       <i class="%s"></i> %s
     </button>',
    button_class, tracker_id, icon_class, button_text
  )
}

# JavaScript function to create comment container HTML
comment_expansion_js <- function(ns) {
  tags$script(HTML(sprintf("
    // Create comment container for expanded row
    function createCommentContainer(tracker_id) {
      return `
        <div class='comment-expansion-container' data-tracker-id='${tracker_id}'>
          <div class='card border-light'>
            <div class='card-header bg-light py-2'>
              <div class='row'>
                <div class='col-md-8'>
                  <h6 class='mb-0 text-primary'>
                    <i class='bi bi-chat-dots'></i> Comments for Tracker ID: ${tracker_id}
                  </h6>
                </div>
                <div class='col-md-4 text-end'>
                  <button class='btn btn-primary btn-sm' onclick='showAddCommentForm(\"${tracker_id}\")'>
                    <i class='bi bi-plus'></i> Add Comment
                  </button>
                </div>
              </div>
            </div>
            <div class='card-body p-3'>
              <div id='comment-form-${tracker_id}' class='comment-form' style='display: none;'>
                <div class='row mb-3'>
                  <div class='col-md-6'>
                    <select class='form-select form-select-sm' id='comment-type-${tracker_id}'>
                      <option value='qc_comment'>QC Comment</option>
                      <option value='prod_comment'>Production Comment</option>
                      <option value='biostat_comment'>Biostat Comment</option>
                    </select>
                  </div>
                  <div class='col-md-6'>
                    <div class='form-check'>
                      <input class='form-check-input' type='checkbox' id='track-comment-${tracker_id}'>
                      <label class='form-check-label text-sm' for='track-comment-${tracker_id}'>
                        Track this comment
                      </label>
                    </div>
                  </div>
                </div>
                <div class='mb-3'>
                  <textarea class='form-control' id='comment-text-${tracker_id}' rows='3' 
                            placeholder='Enter your comment here... (Markdown supported)'></textarea>
                </div>
                <div class='text-end'>
                  <button class='btn btn-secondary btn-sm me-2' onclick='hideAddCommentForm(\"${tracker_id}\")'>
                    Cancel
                  </button>
                  <button class='btn btn-success btn-sm' onclick='submitComment(\"${tracker_id}\")'>
                    <i class='bi bi-check'></i> Add Comment
                  </button>
                </div>
                <hr class='my-3'>
              </div>
              <div id='comments-list-${tracker_id}' class='comments-list'>
                <div class='text-center text-muted py-3'>
                  <i class='bi bi-hourglass-split'></i> Loading comments...
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    }
    
    // Show add comment form
    function showAddCommentForm(tracker_id) {
      document.getElementById('comment-form-' + tracker_id).style.display = 'block';
      document.getElementById('comment-text-' + tracker_id).focus();
    }
    
    // Hide add comment form
    function hideAddCommentForm(tracker_id) {
      document.getElementById('comment-form-' + tracker_id).style.display = 'none';
      document.getElementById('comment-text-' + tracker_id).value = '';
    }
    
    // Submit new comment
    function submitComment(tracker_id) {
      var comment_text = document.getElementById('comment-text-' + tracker_id).value.trim();
      var comment_type = document.getElementById('comment-type-' + tracker_id).value;
      var tracked = document.getElementById('track-comment-' + tracker_id).checked;
      
      if (!comment_text) {
        alert('Please enter a comment');
        return;
      }
      
      // Send to Shiny server
      Shiny.setInputValue('%s', {
        tracker_id: tracker_id,
        comment_text: comment_text,
        comment_type: comment_type,
        tracked: tracked,
        action: 'create'
      }, {priority: 'event'});
      
      // Reset form
      hideAddCommentForm(tracker_id);
    }
    
    // Load comments for expanded row
    function loadCommentsForRow(tracker_id) {
      // Send request to load comments
      Shiny.setInputValue('%s', {
        tracker_id: tracker_id,
        action: 'load'
      }, {priority: 'event'});
    }
    
    // Update comments display
    function updateCommentsDisplay(tracker_id, comments_html) {
      var comments_container = document.getElementById('comments-list-' + tracker_id);
      if (comments_container) {
        comments_container.innerHTML = comments_html;
      }
    }
    
    // Mark comment as addressed
    function markCommentAddressed(comment_id, tracker_id) {
      Shiny.setInputValue('%s', {
        comment_id: comment_id,
        tracker_id: tracker_id,
        action: 'mark_addressed'
      }, {priority: 'event'});
    }
    
    // Pin comment
    function pinComment(comment_id, tracker_id) {
      Shiny.setInputValue('%s', {
        comment_id: comment_id,
        tracker_id: tracker_id,
        action: 'pin'
      }, {priority: 'event'});
    }
    
    // Unpin comment
    function unpinComment(comment_id, tracker_id) {
      Shiny.setInputValue('%s', {
        comment_id: comment_id,
        tracker_id: tracker_id,
        action: 'unpin'
      }, {priority: 'event'});
    }
  ", ns("comment_action"), ns("load_comments"), ns("comment_action"), ns("comment_action"), ns("comment_action"))))
}

# Generate HTML for comments list
generate_comments_html <- function(comments) {
  if (length(comments) == 0) {
    return('<div class="text-center text-muted py-3">
              <i class="bi bi-chat"></i> No comments yet. Be the first to add one!
            </div>')
  }
  
  comments_html <- ""
  for (comment in comments) {
    comment_class <- switch(comment$comment_type,
      "qc_comment" = "border-danger",
      "prod_comment" = "border-primary", 
      "biostat_comment" = "border-success",
      "border-secondary"
    )
    
    type_badge <- switch(comment$comment_type,
      "qc_comment" = '<span class="badge bg-danger">QC</span>',
      "prod_comment" = '<span class="badge bg-primary">PROD</span>',
      "biostat_comment" = '<span class="badge bg-success">Biostat</span>',
      '<span class="badge bg-secondary">General</span>'
    )
    
    # Comment action buttons
    action_buttons <- ""
    
    # Add pin/unpin button
    if (isTRUE(comment$is_pinned)) {
      action_buttons <- paste0(action_buttons, sprintf(
        '<button class="btn btn-outline-warning btn-sm me-1" onclick="unpinComment(%s, %s)" title="Unpin comment">
           <i class="bi bi-pin-fill"></i> Unpin
         </button>', comment$id, comment$tracker_id))
    } else {
      action_buttons <- paste0(action_buttons, sprintf(
        '<button class="btn btn-outline-secondary btn-sm me-1" onclick="pinComment(%s, %s)" title="Pin comment">
           <i class="bi bi-pin"></i> Pin
         </button>', comment$id, comment$tracker_id))
    }
    
    # Address tracking buttons
    addressed_info <- if (isTRUE(comment$addressed)) {
      '<div class="text-success small mt-2">
         <i class="bi bi-check-circle"></i> Addressed
       </div>'
    } else if (isTRUE(comment$tracked)) {
      sprintf('<div class="mt-2">
                 <button class="btn btn-outline-success btn-sm" onclick="markCommentAddressed(%s, %s)">
                   <i class="bi bi-check"></i> Mark Addressed
                 </button>
               </div>', comment$id, comment$tracker_id)
    } else {
      ""
    }
    
    # Combine action buttons with addressed info
    if (action_buttons != "") {
      addressed_info <- paste0('<div class="mt-2">', action_buttons, '</div>', addressed_info)
    }
    
    comments_html <- paste0(comments_html, sprintf('
      <div class="card mb-2 %s">
        <div class="card-body py-2">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <div>
              <strong>%s</strong> %s
              <small class="text-muted">%s</small>
            </div>
            %s
          </div>
          <div class="comment-text">%s</div>
          %s
        </div>
      </div>
    ', comment_class, 
       comment$user$username %||% "Unknown User",
       type_badge,
       format(as.POSIXct(comment$created_at), "%Y-%m-%d %H:%M"),
       if(isTRUE(comment$is_pinned)) '<i class="bi bi-pin text-warning" title="Pinned"></i>' else "",
       comment$comment_text,
       addressed_info))
  }
  
  return(comments_html)
}

# CSS for comment expansion styling
comment_expansion_css <- function() {
  tags$style(HTML("
    .comment-expansion-container {
      background-color: #f8f9fa;
      padding: 15px;
      margin: 10px 0;
      border-radius: 8px;
      border-left: 4px solid #007bff;
    }
    
    .comment-expansion-container .card {
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .comments-list {
      max-height: 400px;
      overflow-y: auto;
    }
    
    .comment-form {
      background-color: #fff;
      border: 1px solid #dee2e6;
      border-radius: 6px;
      padding: 15px;
      margin-bottom: 15px;
    }
    
    .comment-expand-btn {
      transition: all 0.2s ease;
    }
    
    .comment-expand-btn:hover {
      transform: scale(1.05);
    }
    
    /* Row highlighting for expanded rows */
    tr.shown {
      background-color: rgba(0, 123, 255, 0.05);
    }
    
    /* Comment status indicators */
    .border-danger { border-left: 4px solid #dc3545 !important; }
    .border-primary { border-left: 4px solid #0d6efd !important; }
    .border-success { border-left: 4px solid #198754 !important; }
    .border-secondary { border-left: 4px solid #6c757d !important; }
  "))
}