/**
 * Simplified Comment System JavaScript
 * Blog-style modal comments with parent/reply threading
 * Supports filtering by comment type (Programming/Biostat)
 */

// Global variables
window.currentCommentTrackerId = null;
window.currentCommentModalReplyTo = null;
window.allCommentsCache = [];  // Store all comments for filtering
window.currentCommentTypeFilter = 'programming';  // Default filter

// Helper function to get API base URL
function getApiBaseUrl() {
  return window.PEARL_API_URL || 'http://localhost:8000';
}

// Create and show simplified comment modal
window.showSimplifiedCommentModal = function(trackerId) {
  window.currentCommentTrackerId = trackerId;
  window.currentCommentModalReplyTo = null;
  window.currentCommentTypeFilter = 'programming';  // Reset to default
  
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
      // Cache all comments for filtering
      window.allCommentsCache = comments;
      
      // Update count badges
      updateTypeCountBadges(comments);
      
      // Display comments filtered by current type
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

// Update type count badges in the filter section
function updateTypeCountBadges(comments) {
  let progTotal = 0;
  let progUnresolved = 0;
  let biostatTotal = 0;
  let biostatUnresolved = 0;
  
  // Count ALL parent comments by type (for filter badges)
  comments.forEach(comment => {
    const type = comment.comment_type || 'programming';
    if (type === 'programming') {
      progTotal++;
      if (!comment.is_resolved) progUnresolved++;
    } else if (type === 'biostat') {
      biostatTotal++;
      if (!comment.is_resolved) biostatUnresolved++;
    }
  });
  
  // Update badges - show total count, with unresolved indicator if any
  const progBadge = document.getElementById('prog-count-badge');
  const biostatBadge = document.getElementById('biostat-count-badge');
  
  if (progBadge) {
    if (progUnresolved > 0) {
      progBadge.textContent = `${progUnresolved}/${progTotal}`;
      progBadge.className = 'badge bg-warning text-dark ms-1';
    } else {
      progBadge.textContent = progTotal;
      progBadge.className = progTotal > 0 ? 'badge bg-success ms-1' : 'badge bg-dark ms-1';
    }
  }
  
  if (biostatBadge) {
    if (biostatUnresolved > 0) {
      biostatBadge.textContent = `${biostatUnresolved}/${biostatTotal}`;
      biostatBadge.className = 'badge bg-info ms-1';
    } else {
      biostatBadge.textContent = biostatTotal;
      biostatBadge.className = biostatTotal > 0 ? 'badge bg-success ms-1' : 'badge bg-dark ms-1';
    }
  }
}

// Filter comments by type (called when filter radio button clicked)
window.filterCommentsByType = function(type) {
  window.currentCommentTypeFilter = type;
  
  // Update the "Add New" label to show current type
  updateCommentTypeLabel(type);
  
  // Re-display comments with new filter
  displayCommentsInModal(window.allCommentsCache);
  
  // Cancel any active reply
  cancelReply();
};

// Update the comment type label in the form
function updateCommentTypeLabel(type) {
  const typeLabel = document.getElementById('comment-type-label');
  if (typeLabel) {
    if (type === 'biostat') {
      typeLabel.textContent = 'Biostat';
      typeLabel.className = 'badge bg-info ms-1';
    } else {
      typeLabel.textContent = 'Programming';
      typeLabel.className = 'badge bg-warning text-dark ms-1';
    }
  }
}

// Display comments in the modal with blog-style threading
function displayCommentsInModal(comments) {
  const commentsContainer = document.getElementById('modal-comments-list');
  if (!commentsContainer) return;
  
  // Filter comments by current type
  const filteredComments = comments.filter(comment => {
    const type = comment.comment_type || 'programming';
    return type === window.currentCommentTypeFilter;
  });
  
  if (!filteredComments || filteredComments.length === 0) {
    const typeLabel = window.currentCommentTypeFilter === 'biostat' ? 'Biostat' : 'Programming';
    commentsContainer.innerHTML = `
      <div class="text-center p-4 text-muted">
        <i class="fa fa-comment-o fa-2x mb-3"></i>
        <div>No ${typeLabel} comments yet.</div>
        <div class="small">Be the first to add a ${typeLabel.toLowerCase()} comment!</div>
      </div>
    `;
    return;
  }
  
  let html = '';
  filteredComments.forEach(comment => {
    html += renderCommentThread(comment, 0, comment.is_resolved);
  });
  
  commentsContainer.innerHTML = html;
  
  // Initialize action handlers
  initializeCommentActions();
}

// Get comment type badge HTML
function getCommentTypeBadge(commentType) {
  if (commentType === 'biostat') {
    return '<span class="badge bg-info me-2"><i class="fa fa-chart-bar me-1"></i>Biostat</span>';
  }
  return '<span class="badge bg-warning text-dark me-2"><i class="fa fa-code me-1"></i>Programming</span>';
}

// Get comment type CSS class for background styling
function getCommentTypeClass(commentType) {
  return commentType === 'biostat' ? 'comment-biostat' : 'comment-programming';
}

// Render a comment thread (parent + nested replies)
// parentResolved: if true, this comment is part of a resolved thread
function renderCommentThread(comment, depth, parentResolved = false) {
  const marginLeft = depth * 20;
  const isParent = depth === 0;
  const commentType = comment.comment_type || 'programming';
  const typeClass = getCommentTypeClass(commentType);
  
  // Determine if this comment thread is resolved (parent is resolved means whole thread is closed)
  const isInResolvedThread = parentResolved || comment.is_resolved;
  
  // Styling based on resolved state
  const resolvedClass = isInResolvedThread ? 'comment-resolved' : '';
  const borderClass = isParent 
    ? (commentType === 'biostat' ? 'border-start border-info border-3' : 'border-start border-warning border-3')
    : 'border-start border-secondary border-2';
  
  // Format timestamp
  const createdAt = new Date(comment.created_at);
  const timeAgo = getTimeAgo(createdAt);
  
  // Build comment HTML
  let html = `
    <div class="comment-item mb-3 p-3 ${borderClass} ${typeClass} ${resolvedClass}" 
         style="margin-left: ${marginLeft}px; border-radius: 0.375rem;"
         data-comment-id="${comment.id}"
         data-comment-type="${commentType}"
         data-resolved="${isInResolvedThread}">
      <div class="d-flex justify-content-between align-items-start mb-2">
        <div class="d-flex align-items-center flex-wrap">
          ${!isParent ? '<i class="fa fa-reply me-2 text-muted"></i>' : ''}
          <strong class="text-primary">${escapeHtml(comment.username)}</strong>
          ${comment.is_resolved ? '<span class="badge bg-success ms-2"><i class="fa fa-check me-1"></i>Resolved</span>' : ''}
          ${isInResolvedThread && !comment.is_resolved ? '<span class="badge bg-secondary ms-2"><i class="fa fa-lock me-1"></i>Closed</span>' : ''}
        </div>
        <small class="text-muted">${timeAgo}</small>
      </div>
      
      <div class="comment-text mb-2">${escapeHtml(comment.comment_text)}</div>
      
      ${!isInResolvedThread ? `
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
      ` : `
        <div class="comment-actions">
          <small class="text-muted"><i class="fa fa-lock me-1"></i>This conversation is closed</small>
        </div>
      `}
    </div>
  `;
  
  // Add nested replies (pass down resolved state)
  if (comment.replies && comment.replies.length > 0) {
    comment.replies.forEach(reply => {
      html += renderCommentThread(reply, depth + 1, isInResolvedThread);
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
  const cancelBtn = document.getElementById('comment-cancel-reply-btn');
  
  if (formTitle) {
    const typeLabel = document.getElementById('comment-type-label');
    const typeBadgeHtml = typeLabel ? typeLabel.outerHTML : '';
    formTitle.innerHTML = `<i class="fa fa-reply me-2"></i>Reply to <strong>${escapeHtml(parentUsername)}</strong> ${typeBadgeHtml}`;
  }
  
  if (submitBtn) {
    submitBtn.innerHTML = '<i class="fa fa-reply me-1"></i>Submit Reply';
  }
  
  // Show cancel button
  if (cancelBtn) {
    cancelBtn.style.display = 'inline-block';
  }
  
  // Focus on textarea and scroll it into view
  const textarea = document.getElementById('comment-text-input');
  if (textarea) {
    textarea.focus();
    textarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
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
    const typeLabel = document.getElementById('comment-type-label');
    const typeBadgeHtml = typeLabel ? typeLabel.outerHTML : '';
    formTitle.innerHTML = `<i class="fa fa-plus me-2"></i>Add New ${typeBadgeHtml} Comment`;
  }
  
  if (submitBtn) {
    submitBtn.innerHTML = '<i class="fa fa-paper-plane me-1"></i>Submit Comment';
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

// Get selected comment type from filter radio buttons
function getSelectedCommentType() {
  const selectedRadio = document.querySelector('input[name="comment-type-filter"]:checked');
  return selectedRadio ? selectedRadio.value : 'programming';
}

// Submit comment or reply
window.submitComment = function() {
  const textarea = document.getElementById('comment-text-input');
  const submitBtn = document.getElementById('comment-submit-btn');
  
  if (!textarea || !window.currentCommentTrackerId) return;
  
  const commentText = textarea.value.trim();
  if (!commentText) {
    showCommentNotification('Please enter a comment.', 'error');
    textarea.focus();
    return;
  }
  
  // Get the selected comment type from filter
  const commentType = getSelectedCommentType();
  
  // Show loading state
  const originalText = submitBtn.innerHTML;
  submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin me-1"></i>Saving...';
  submitBtn.disabled = true;
  
  // Prepare API payload
  const payload = {
    tracker_id: parseInt(window.currentCommentTrackerId),
    comment_text: commentText,
    comment_type: commentType
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
    
    // Reload comments (will apply current filter)
    loadCommentsForModal(window.currentCommentTrackerId);
    
    // Show success message
    const typeLabel = commentType === 'biostat' ? 'Biostat' : 'Programming';
    showCommentNotification(`${typeLabel} comment added successfully!`, 'success');
    
    // Update button badge via Shiny
    if (typeof Shiny !== 'undefined') {
      Shiny.setInputValue('comment_added_event', {
        tracker_id: window.currentCommentTrackerId,
        comment_type: commentType,
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
  if (!confirm('Resolve this comment? This will close the entire conversation thread and prevent further replies.')) {
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
    showCommentNotification('Comment resolved! Conversation thread is now closed.', 'success');
    
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

// Update comment button badge with separate counts for programming and biostat
// totalComments: total number of comments (to distinguish "no comments" from "all resolved")
window.updateCommentButtonBadge = function(trackerId, unresolvedCount, programmingCount, biostatCount, totalComments) {
  const button = document.querySelector(`button.comment-btn[data-tracker-id="${trackerId}"]`);
  if (!button) return;
  
  const icon = button.querySelector('i');
  const progBadge = button.querySelector('.comment-badge-prog');
  const biostatBadge = button.querySelector('.comment-badge-biostat');
  
  // Handle legacy calls with only unresolvedCount (backward compatibility)
  if (programmingCount === undefined && biostatCount === undefined) {
    programmingCount = unresolvedCount;
    biostatCount = 0;
  }
  
  const totalUnresolved = (programmingCount || 0) + (biostatCount || 0);
  const hasAnyComments = (totalComments !== undefined) ? totalComments > 0 : totalUnresolved > 0;
  
  if (!hasAnyComments) {
    // NO COMMENTS AT ALL - Gray outline, empty comment icon
    button.className = 'btn btn-outline-secondary btn-sm comment-btn';
    button.title = 'No comments yet';
    if (icon) icon.className = 'fa fa-comment-o';
    if (progBadge) progBadge.style.display = 'none';
    if (biostatBadge) biostatBadge.style.display = 'none';
  } else if (totalUnresolved === 0) {
    // ALL COMMENTS RESOLVED - Green button, filled comment icon
    button.className = 'btn btn-success btn-sm comment-btn';
    button.title = 'All comments resolved';
    if (icon) icon.className = 'fa fa-comments';
    if (progBadge) progBadge.style.display = 'none';
    if (biostatBadge) biostatBadge.style.display = 'none';
  } else {
    // HAS UNRESOLVED COMMENTS - Show badges with counts
    if (icon) icon.className = 'fa fa-comments';
    
    // Color based on which types have unresolved comments
    if (programmingCount > 0 && biostatCount > 0) {
      // Both types - use mixed style
      button.className = 'btn btn-outline-dark btn-sm comment-btn has-comments';
      button.title = `${programmingCount} Programming + ${biostatCount} Biostat unresolved`;
    } else if (programmingCount > 0) {
      // Only programming comments - yellow
      button.className = 'btn btn-warning btn-sm comment-btn has-comments';
      button.title = `${programmingCount} Programming comment(s) unresolved`;
    } else {
      // Only biostat comments - blue
      button.className = 'btn btn-info btn-sm comment-btn has-comments';
      button.title = `${biostatCount} Biostat comment(s) unresolved`;
    }
    
    // Update programming badge
    if (progBadge) {
      if (programmingCount > 0) {
        progBadge.textContent = `P:${programmingCount}`;
        progBadge.style.display = 'inline';
      } else {
        progBadge.style.display = 'none';
      }
    }
    
    // Update biostat badge
    if (biostatBadge) {
      if (biostatCount > 0) {
        biostatBadge.textContent = `B:${biostatCount}`;
        biostatBadge.style.display = 'inline';
      } else {
        biostatBadge.style.display = 'none';
      }
    }
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
  toast.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 99999; min-width: 300px;';
  
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
  console.log('Simplified comment system loaded with type filtering');
});

// Handle custom message from R Shiny for updating comment badges
if (typeof Shiny !== 'undefined') {
  Shiny.addCustomMessageHandler('updateCommentBadges', function(data) {
    console.log('Received updateCommentBadges message:', data);
    
    if (data && data.summaries) {
      console.log('Processing summaries:', data.summaries);
      
      // Handle both array and object formats
      let summaries;
      if (Array.isArray(data.summaries)) {
        summaries = data.summaries;
      } else {
        summaries = Object.values(data.summaries);
      }
      
      console.log('Processing', summaries.length, 'summaries');
      
      summaries.forEach(function(summary, index) {
        console.log(`Processing summary ${index}:`, summary);
        
        if (summary && typeof summary === 'object') {
          const trackerId = summary.tracker_id;
          const unresolvedCount = summary.unresolved_count || 0;
          const programmingCount = summary.programming_unresolved_count || 0;
          const biostatCount = summary.biostat_unresolved_count || 0;
          const totalComments = summary.total_comments || 0;
          
          if (trackerId !== undefined) {
            console.log(`Updating button for tracker ${trackerId}: total=${totalComments}, prog=${programmingCount}, biostat=${biostatCount}`);
            updateCommentButtonBadge(trackerId, unresolvedCount, programmingCount, biostatCount, totalComments);
          } else {
            console.warn('Missing tracker_id in summary:', summary);
          }
        } else {
          console.warn('Invalid summary format:', summary);
        }
      });
    } else {
      console.warn('No summaries found in updateCommentBadges data:', data);
    }
  });
}
