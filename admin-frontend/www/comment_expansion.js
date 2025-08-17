/**
 * Comment Expansion JavaScript Functions
 * Provides expandable row functionality for DataTables with inline comment forms
 */

// Global comment expansion functions for DataTables
window.createCommentExpansion = function(trackerId) {
  return `
    <div class="comment-expansion-container" style="padding: 15px; background-color: #f8f9fa; border-left: 4px solid #007bff;">
      <div class="card border-0">
        <div class="card-header bg-transparent border-bottom-0 pb-2">
          <h6 class="mb-0"><i class="fa fa-comments me-2"></i>Comments for Tracker ID: ${trackerId}</h6>
        </div>
        <div class="card-body pt-2">
          <div class="row">
            <div class="col-md-8">
              <div class="comments-list" id="comments-list-${trackerId}">
                <div class="loading-comments text-muted">
                  <i class="fa fa-spinner fa-spin me-2"></i>Loading comments...
                </div>
              </div>
            </div>
            <div class="col-md-4">
              <div class="comment-form" id="comment-form-${trackerId}" style="display: none;">
                <h6 class="mb-3">Add Comment</h6>
                <form>
                  <div class="mb-3">
                    <label for="comment-type-${trackerId}" class="form-label">Type</label>
                    <select class="form-select" id="comment-type-${trackerId}">
                      <option value="qc_comment">QC Comment</option>
                      <option value="prod_comment">Production Comment</option>
                      <option value="biostat_comment">Biostat Comment</option>
                    </select>
                  </div>
                  <div class="mb-3">
                    <label for="comment-text-${trackerId}" class="form-label">Comment</label>
                    <textarea class="form-control" id="comment-text-${trackerId}" rows="3" 
                              placeholder="Enter your comment here..."></textarea>
                    <div class="invalid-feedback" id="comment-validation-${trackerId}"></div>
                  </div>
                  <div class="mb-3 form-check">
                    <input type="checkbox" class="form-check-input" id="track-comment-${trackerId}">
                    <label class="form-check-label" for="track-comment-${trackerId}">
                      Track this comment
                    </label>
                  </div>
                  <div class="d-grid gap-2 d-md-flex">
                    <button type="button" class="btn btn-primary" id="submit-comment-${trackerId}">
                      <i class="fa fa-plus me-1"></i>Add Comment
                    </button>
                    <button type="button" class="btn btn-secondary" id="cancel-comment-${trackerId}">
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
              <div class="comment-actions" id="comment-actions-${trackerId}">
                <button type="button" class="btn btn-outline-primary btn-sm" id="add-comment-btn-${trackerId}">
                  <i class="fa fa-plus me-1"></i>Add Comment
                </button>
                <button type="button" class="btn btn-outline-secondary btn-sm ms-2" id="refresh-comments-${trackerId}">
                  <i class="fa fa-refresh me-1"></i>Refresh
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
};

// Initialize comment handlers for a specific tracker
window.initializeCommentHandlers = function(trackerId) {
  // Add comment button
  $(`#add-comment-btn-${trackerId}`).off('click').on('click', function() {
    $(`#comment-actions-${trackerId}`).hide();
    $(`#comment-form-${trackerId}`).show();
    $(`#comment-text-${trackerId}`).focus();
  });

  // Cancel comment button
  $(`#cancel-comment-${trackerId}`).off('click').on('click', function() {
    $(`#comment-form-${trackerId}`).hide();
    $(`#comment-actions-${trackerId}`).show();
    $(`#comment-text-${trackerId}`).val('');
    $(`#comment-text-${trackerId}`).removeClass('is-invalid');
    $(`#comment-validation-${trackerId}`).text('');
  });

  // Submit comment button
  $(`#submit-comment-${trackerId}`).off('click').on('click', function() {
    const commentText = $(`#comment-text-${trackerId}`).val().trim();
    const commentType = $(`#comment-type-${trackerId}`).val();
    const isTracked = $(`#track-comment-${trackerId}`).is(':checked');

    // Validation
    if (!commentText) {
      $(`#comment-text-${trackerId}`).addClass('is-invalid');
      $(`#comment-validation-${trackerId}`).text('Please enter a comment');
      return;
    }

    // Clear validation
    $(`#comment-text-${trackerId}`).removeClass('is-invalid');
    $(`#comment-validation-${trackerId}`).text('');

    // Submit comment via API
    submitComment(trackerId, {
      comment_text: commentText,
      comment_type: commentType,
      is_tracked: isTracked
    });
  });

  // Refresh comments button
  $(`#refresh-comments-${trackerId}`).off('click').on('click', function() {
    loadCommentsForTracker(trackerId);
  });
};

// Load comments for a specific tracker
window.loadCommentsForTracker = function(trackerId) {
  // Handle invalid or placeholder tracker IDs
  if (!trackerId || trackerId === 'NA' || trackerId === 'undefined' || isNaN(parseInt(trackerId))) {
    $(`#comments-list-${trackerId}`).html(`
      <div class="text-muted text-center py-3">
        <i class="fa fa-info-circle me-2"></i>No comments yet. Add one to get started!
        <br><small class="text-muted">Create a tracker first to enable comments.</small>
      </div>
    `);
    return;
  }

  // Show loading state
  $(`#comments-list-${trackerId}`).html(`
    <div class="loading-comments text-muted">
      <i class="fa fa-spinner fa-spin me-2"></i>Loading comments...
    </div>
  `);

  // Make API call to load comments
  fetch(`${getApiBaseUrl()}/api/v1/tracker-comments/tracker/${trackerId}`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .then(comments => {
      displayComments(trackerId, comments);
    })
    .catch(error => {
      console.error('Error loading comments:', error);
      $(`#comments-list-${trackerId}`).html(`
        <div class="text-danger">
          <i class="fa fa-exclamation-triangle me-2"></i>Error loading comments: ${error.message}
        </div>
      `);
    });
};

// Display comments in the comments list
function displayComments(trackerId, comments) {
  const container = $(`#comments-list-${trackerId}`);
  
  if (!comments || comments.length === 0) {
    container.html(`
      <div class="text-muted text-center py-3">
        <i class="fa fa-comment-o me-2"></i>No comments yet. Add one to get started!
      </div>
    `);
    return;
  }

  let html = '';
  comments.forEach(comment => {
    const createdAt = new Date(comment.created_at);
    const timeAgo = getTimeAgo(createdAt);
    const typeClass = getCommentTypeClass(comment.comment_type);
    const statusBadges = getStatusBadges(comment);
    
    html += `
      <div class="comment-card mb-3 p-3 border-start border-3 ${typeClass}" style="border-radius: 0.375rem; background-color: #fefefe;">
        <div class="d-flex justify-content-between align-items-start mb-2">
          <div>
            <span class="badge bg-${getCommentTypeBadge(comment.comment_type)} me-2">${formatCommentType(comment.comment_type)}</span>
            ${statusBadges}
          </div>
          <small class="text-muted">${timeAgo}</small>
        </div>
        <p class="mb-2">${escapeHtml(comment.comment_text)}</p>
        <div class="d-flex justify-content-between align-items-center">
          <small class="text-muted">
            <i class="fa fa-user me-1"></i>User ${comment.user_id}
          </small>
          <div class="comment-actions">
            <button class="btn btn-sm btn-outline-secondary me-1" onclick="replyToComment(${trackerId}, ${comment.id})">
              <i class="fa fa-reply"></i>
            </button>
            ${comment.is_pinned ? '' : `
              <button class="btn btn-sm btn-outline-warning" onclick="pinComment(${trackerId}, ${comment.id})">
                <i class="fa fa-thumb-tack"></i>
              </button>
            `}
            ${comment.is_resolved ? '' : `
              <button class="btn btn-sm btn-outline-success" onclick="resolveComment(${trackerId}, ${comment.id})">
                <i class="fa fa-check"></i>
              </button>
            `}
          </div>
        </div>
      </div>
    `;
  });
  
  container.html(html);
}

// Submit a new comment
function submitComment(trackerId, commentData) {
  if (!trackerId || trackerId === 'NA' || trackerId === 'undefined' || isNaN(parseInt(trackerId))) {
    alert('Cannot add comment: Please create a tracker first before adding comments.');
    return;
  }

  // Show loading state
  $(`#submit-comment-${trackerId}`).html('<i class="fa fa-spinner fa-spin me-1"></i>Adding...');
  $(`#submit-comment-${trackerId}`).prop('disabled', true);

  // Prepare data
  const payload = {
    tracker_id: parseInt(trackerId),
    ...commentData
  };

  fetch(`${getApiBaseUrl()}/api/v1/tracker-comments/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': '1', // TODO: Get from session
      'X-User-Role': 'admin' // TODO: Get from session
    },
    body: JSON.stringify(payload)
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  })
  .then(result => {
    // Reset form
    $(`#comment-text-${trackerId}`).val('');
    $(`#track-comment-${trackerId}`).prop('checked', false);
    $(`#comment-form-${trackerId}`).hide();
    $(`#comment-actions-${trackerId}`).show();
    
    // Reload comments
    loadCommentsForTracker(trackerId);
    
    // Update comment button in table
    updateCommentButton(trackerId);
  })
  .catch(error => {
    console.error('Error submitting comment:', error);
    alert(`Error adding comment: ${error.message}`);
  })
  .finally(() => {
    $(`#submit-comment-${trackerId}`).html('<i class="fa fa-plus me-1"></i>Add Comment');
    $(`#submit-comment-${trackerId}`).prop('disabled', false);
  });
}

// Utility functions
function getCommentTypeClass(type) {
  const classes = {
    'qc_comment': 'border-primary',
    'prod_comment': 'border-success', 
    'biostat_comment': 'border-warning'
  };
  return classes[type] || 'border-secondary';
}

function getCommentTypeBadge(type) {
  const badges = {
    'qc_comment': 'primary',
    'prod_comment': 'success',
    'biostat_comment': 'warning'
  };
  return badges[type] || 'secondary';
}

function formatCommentType(type) {
  const types = {
    'qc_comment': 'QC Comment',
    'prod_comment': 'Production Comment',
    'biostat_comment': 'Biostat Comment'
  };
  return types[type] || type;
}

function getStatusBadges(comment) {
  let badges = '';
  if (comment.is_pinned) {
    badges += '<span class="badge bg-warning text-dark me-1"><i class="fa fa-thumb-tack me-1"></i>Pinned</span>';
  }
  if (comment.is_resolved) {
    badges += '<span class="badge bg-success me-1"><i class="fa fa-check me-1"></i>Resolved</span>';
  }
  if (comment.is_tracked) {
    badges += '<span class="badge bg-info me-1"><i class="fa fa-eye me-1"></i>Tracked</span>';
  }
  return badges;
}

function getTimeAgo(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function getApiBaseUrl() {
  return window.PEARL_API_URL || 'http://localhost:8000';
}

function updateCommentButton(trackerId) {
  // TODO: Refresh the comment count in the button
  // This would require getting the updated count from the API
  console.log('TODO: Update comment button for tracker', trackerId);
}

// Comment action functions
function replyToComment(trackerId, commentId) {
  // TODO: Implement reply functionality
  console.log('TODO: Reply to comment', commentId, 'in tracker', trackerId);
}

function pinComment(trackerId, commentId) {
  fetch(`${getApiBaseUrl()}/api/v1/tracker-comments/${commentId}/pin`, {
    method: 'POST',
    headers: {
      'X-User-Id': '1',
      'X-User-Role': 'admin'
    }
  })
  .then(response => {
    if (response.ok) {
      loadCommentsForTracker(trackerId);
    }
  })
  .catch(error => console.error('Error pinning comment:', error));
}

function resolveComment(trackerId, commentId) {
  fetch(`${getApiBaseUrl()}/api/v1/tracker-comments/${commentId}/resolve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': '1',
      'X-User-Role': 'admin'
    },
    body: JSON.stringify({
      comment_id: commentId,
      is_resolved: true
    })
  })
  .then(response => {
    if (response.ok) {
      loadCommentsForTracker(trackerId);
    }
  })
  .catch(error => console.error('Error resolving comment:', error));
}

// Initialize Shiny custom message handlers when document is ready
$(document).ready(function() {
  // Handle real-time comment refresh messages from WebSocket
  if (typeof Shiny !== 'undefined') {
    Shiny.addCustomMessageHandler('refreshComments', function(message) {
      console.log('📬 Received refresh comments message:', message);
      const trackerId = message.tracker_id;
      const eventType = message.event_type;
      
      // Check if this tracker's comments are currently displayed
      const commentsContainer = $(`#comments-list-${trackerId}`);
      if (commentsContainer.length > 0) {
        console.log(`🔄 Refreshing comments for tracker ${trackerId} due to ${eventType}`);
        loadCommentsForTracker(trackerId);
      }
      
      // Show a brief notification for real-time updates
      if (eventType === 'comment_created') {
        showCommentNotification(`New comment added to tracker ${trackerId}`, 'success');
      } else if (eventType === 'comment_updated') {
        showCommentNotification(`Comment updated in tracker ${trackerId}`, 'info');
      } else if (eventType === 'comment_resolved') {
        showCommentNotification(`Comment resolved in tracker ${trackerId}`, 'success');
      }
    });
  }
});

// Show brief notifications for comment events
function showCommentNotification(message, type = 'info') {
  // Create a simple notification that appears briefly
  const notification = $(`
    <div class="comment-notification alert alert-${type === 'success' ? 'success' : type === 'info' ? 'info' : 'primary'} alert-dismissible fade show" 
         style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
      <i class="fa fa-comment me-2"></i>${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
  `);
  
  $('body').append(notification);
  
  // Auto-remove after 3 seconds
  setTimeout(() => {
    notification.alert('close');
  }, 3000);
}