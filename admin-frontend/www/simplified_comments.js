/**
 * Simplified Comment System JavaScript
 * Blog-style modal comments with parent/reply threading
 */

// Global variables
window.currentCommentTrackerId = null;
window.currentCommentModalReplyTo = null;

// Helper function to get API base URL
function getApiBaseUrl() {
  return window.PEARL_API_URL || 'http://localhost:8000';
}

// Create and show simplified comment modal
window.showSimplifiedCommentModal = function(trackerId) {
  window.currentCommentTrackerId = trackerId;
  window.currentCommentModalReplyTo = null;
  
  // Show Shiny modal trigger with module namespace
  if (typeof Shiny !== 'undefined') {
    Shiny.setInputValue('reporting_effort_tracker-comment_modal_trigger', {
      tracker_id: trackerId,
      timestamp: new Date().getTime()
    }, {priority: 'event'});
  }
};

// Load comments for the modal
window.loadCommentsForModal = function(trackerId) {
  const commentsContainer = document.getElementById('modal-comments-list');
  if (!commentsContainer) return;
  
  // Show loading state
  commentsContainer.innerHTML = `
    <div class="text-center p-3">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading comments...</span>
      </div>
      <div class="mt-2 text-muted">Loading comments...</div>
    </div>
  `;
  
  // Fetch comments from API
  fetch(`${getApiBaseUrl()}/api/v1/tracker-comments/tracker/${trackerId}/threaded`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .then(comments => {
      displayCommentsInModal(comments);
    })
    .catch(error => {
      console.error('Error loading comments:', error);
      commentsContainer.innerHTML = `
        <div class="alert alert-danger">
          <i class="fa fa-exclamation-triangle me-2"></i>
          Error loading comments: ${error.message}
        </div>
      `;
    });
};

// Display comments in the modal with blog-style threading
function displayCommentsInModal(comments) {
  const commentsContainer = document.getElementById('modal-comments-list');
  if (!commentsContainer) return;
  
  if (!comments || comments.length === 0) {
    commentsContainer.innerHTML = `
      <div class="text-center p-4 text-muted">
        <i class="fa fa-comment-o fa-2x mb-3"></i>
        <div>No comments yet.</div>
        <div class="small">Be the first to add a comment!</div>
      </div>
    `;
    return;
  }
  
  let html = '';
  comments.forEach(comment => {
    html += renderCommentThread(comment, 0);
  });
  
  commentsContainer.innerHTML = html;
  
  // Initialize action handlers
  initializeCommentActions();
}

// Render a comment thread (parent + nested replies)
function renderCommentThread(comment, depth) {
  const marginLeft = depth * 20;
  const isParent = depth === 0;
  const borderClass = isParent ? 'border-start border-primary border-3' : 'border-start border-info border-2';
  const bgClass = isParent ? 'bg-light' : 'bg-white';
  
  // Format timestamp
  const createdAt = new Date(comment.created_at);
  const timeAgo = getTimeAgo(createdAt);
  
  // Build comment HTML
  let html = `
    <div class="comment-item mb-3 p-3 ${borderClass} ${bgClass}" 
         style="margin-left: ${marginLeft}px; border-radius: 0.375rem;"
         data-comment-id="${comment.id}">
      <div class="d-flex justify-content-between align-items-start mb-2">
        <div class="d-flex align-items-center">
          ${!isParent ? '<i class="fa fa-reply me-2 text-info"></i>' : ''}
          <strong class="text-primary">${escapeHtml(comment.username)}</strong>
          ${comment.is_resolved ? '<span class="badge bg-success ms-2"><i class="fa fa-check me-1"></i>Resolved</span>' : ''}
        </div>
        <small class="text-muted">${timeAgo}</small>
      </div>
      
      <div class="comment-text mb-3">${escapeHtml(comment.comment_text)}</div>
      
      <div class="comment-actions d-flex gap-2">
        <button class="btn btn-outline-primary btn-sm reply-btn" 
                data-comment-id="${comment.id}" 
                data-comment-username="${escapeHtml(comment.username)}">
          <i class="fa fa-reply me-1"></i>Reply
        </button>
        
        ${isParent && !comment.is_resolved ? `
          <button class="btn btn-outline-success btn-sm resolve-btn" 
                  data-comment-id="${comment.id}">
            <i class="fa fa-check me-1"></i>Resolve
          </button>
        ` : ''}
      </div>
    </div>
  `;
  
  // Add nested replies
  if (comment.replies && comment.replies.length > 0) {
    comment.replies.forEach(reply => {
      html += renderCommentThread(reply, depth + 1);
    });
  }
  
  return html;
}

// Initialize comment action handlers
function initializeCommentActions() {
  // Reply button handlers
  document.querySelectorAll('.reply-btn').forEach(button => {
    button.addEventListener('click', function() {
      const commentId = this.getAttribute('data-comment-id');
      const username = this.getAttribute('data-comment-username');
      showReplyForm(commentId, username);
    });
  });
  
  // Resolve button handlers
  document.querySelectorAll('.resolve-btn').forEach(button => {
    button.addEventListener('click', function() {
      const commentId = this.getAttribute('data-comment-id');
      resolveComment(commentId);
    });
  });
}

// Show reply form
function showReplyForm(parentCommentId, parentUsername) {
  window.currentCommentModalReplyTo = parentCommentId;
  
  // Update form title and button text
  const formTitle = document.getElementById('comment-form-title');
  const submitBtn = document.getElementById('comment-submit-btn');
  
  if (formTitle) {
    formTitle.innerHTML = `<i class="fa fa-reply me-2"></i>Reply to ${escapeHtml(parentUsername)}`;
  }
  
  if (submitBtn) {
    submitBtn.innerHTML = '<i class="fa fa-reply me-1"></i>Add Reply';
  }
  
  // Focus on textarea
  const textarea = document.getElementById('comment-text-input');
  if (textarea) {
    textarea.focus();
  }
  
  // Show cancel reply button
  showCancelReplyButton();
}

// Show cancel reply button
function showCancelReplyButton() {
  const cancelBtn = document.getElementById('comment-cancel-reply-btn');
  if (cancelBtn) {
    cancelBtn.style.display = 'inline-block';
  }
}

// Cancel reply (reset to parent comment mode)
window.cancelReply = function() {
  window.currentCommentModalReplyTo = null;
  
  // Reset form title and button text
  const formTitle = document.getElementById('comment-form-title');
  const submitBtn = document.getElementById('comment-submit-btn');
  const cancelBtn = document.getElementById('comment-cancel-reply-btn');
  
  if (formTitle) {
    formTitle.innerHTML = '<i class="fa fa-plus me-2"></i>Add New Comment';
  }
  
  if (submitBtn) {
    submitBtn.innerHTML = '<i class="fa fa-plus me-1"></i>Add Comment';
  }
  
  if (cancelBtn) {
    cancelBtn.style.display = 'none';
  }
  
  // Clear textarea
  const textarea = document.getElementById('comment-text-input');
  if (textarea) {
    textarea.value = '';
  }
};

// Submit comment or reply
window.submitComment = function() {
  const textarea = document.getElementById('comment-text-input');
  const submitBtn = document.getElementById('comment-submit-btn');
  
  if (!textarea || !window.currentCommentTrackerId) return;
  
  const commentText = textarea.value.trim();
  if (!commentText) {
    alert('Please enter a comment.');
    return;
  }
  
  // Show loading state
  const originalText = submitBtn.innerHTML;
  submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin me-1"></i>Saving...';
  submitBtn.disabled = true;
  
  // Prepare API payload
  const payload = {
    tracker_id: parseInt(window.currentCommentTrackerId),
    comment_text: commentText
  };
  
  // Add parent_comment_id if this is a reply
  if (window.currentCommentModalReplyTo) {
    payload.parent_comment_id = parseInt(window.currentCommentModalReplyTo);
  }
  
  // Submit to API
  fetch(`${getApiBaseUrl()}/api/v1/tracker-comments/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': '1' // TODO: Get from session
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
    // Success! Clear form and reload comments
    textarea.value = '';
    cancelReply(); // Reset form state
    
    // Reload comments
    loadCommentsForModal(window.currentCommentTrackerId);
    
    // Show success message
    showCommentNotification('Comment added successfully!', 'success');
    
    // Update button badge via Shiny
    if (typeof Shiny !== 'undefined') {
      Shiny.setInputValue('comment_added_event', {
        tracker_id: window.currentCommentTrackerId,
        timestamp: new Date().getTime()
      }, {priority: 'event'});
    }
  })
  .catch(error => {
    console.error('Error submitting comment:', error);
    showCommentNotification(`Error adding comment: ${error.message}`, 'error');
  })
  .finally(() => {
    // Reset button state
    submitBtn.innerHTML = originalText;
    submitBtn.disabled = false;
  });
};

// Resolve a comment
function resolveComment(commentId) {
  if (!confirm('Are you sure you want to resolve this comment?')) {
    return;
  }
  
  fetch(`${getApiBaseUrl()}/api/v1/tracker-comments/${commentId}/resolve`, {
    method: 'POST',
    headers: {
      'X-User-Id': '1' // TODO: Get from session
    }
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  })
  .then(result => {
    // Success! Reload comments
    loadCommentsForModal(window.currentCommentTrackerId);
    
    // Show success message
    showCommentNotification('Comment resolved successfully!', 'success');
    
    // Update button badge via Shiny
    if (typeof Shiny !== 'undefined') {
      Shiny.setInputValue('comment_resolved_event', {
        tracker_id: window.currentCommentTrackerId,
        comment_id: commentId,
        timestamp: new Date().getTime()
      }, {priority: 'event'});
    }
  })
  .catch(error => {
    console.error('Error resolving comment:', error);
    showCommentNotification(`Error resolving comment: ${error.message}`, 'error');
  });
}

// Update comment button badge
window.updateCommentButtonBadge = function(trackerId, unresolvedCount) {
  const button = document.querySelector(`[data-tracker-id="${trackerId}"]`);
  if (!button) return;
  
  const badge = button.querySelector('.comment-badge');
  if (!badge) return;
  
  if (unresolvedCount === 0) {
    // Green button, no badge
    button.className = 'btn btn-success btn-sm comment-btn';
    badge.style.display = 'none';
  } else {
    // Yellow button with count badge
    button.className = 'btn btn-warning btn-sm comment-btn';
    badge.textContent = `+${unresolvedCount}`;
    badge.style.display = 'inline';
  }
};

// Utility functions
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

function showCommentNotification(message, type = 'info') {
  // Create Bootstrap toast notification
  const toastClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-info';
  const icon = type === 'success' ? 'fa-check' : type === 'error' ? 'fa-exclamation-triangle' : 'fa-info';
  
  const toast = document.createElement('div');
  toast.className = `toast align-items-center text-white ${toastClass} border-0`;
  toast.setAttribute('role', 'alert');
  toast.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
  
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        <i class="fa ${icon} me-2"></i>${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  
  document.body.appendChild(toast);
  
  // Show toast
  const bsToast = new bootstrap.Toast(toast);
  bsToast.show();
  
  // Remove element after it's hidden
  toast.addEventListener('hidden.bs.toast', () => {
    document.body.removeChild(toast);
  });
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
  console.log('Simplified comment system loaded');
});