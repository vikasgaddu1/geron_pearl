// Custom message handlers for WebSocket integration
$(document).on('shiny:connected', function (event) {
  console.log('Shiny connected - WebSocket should be initializing...');
});

// Handle WebSocket refresh requests from Shiny
Shiny.addCustomMessageHandler('websocket_refresh', function (message) {
  if (window.pearlWebSocket && window.pearlWebSocket.isConnected()) {
    window.pearlWebSocket.refresh();
    console.log('WebSocket refresh requested');
  } else {
    console.log('WebSocket not connected, skipping refresh');
  }
});

// Toggle selection highlight for reporting effort selector wrappers
Shiny.addCustomMessageHandler('toggleEffortSelection', function (message) {
  try {
    var el = document.getElementById(message.selector_id);
    if (!el) return;
    if (message.has_selection) el.classList.add('has-selection');
    else el.classList.remove('has-selection');
  } catch (e) {
    console.warn('toggleEffortSelection error', e);
  }
});

// Handle real-time comment updates from WebSocket - Enhanced for new simplified system
function refreshCommentsHandler(message) {
  try {
    console.log('📬 Received refresh comments message from WebSocket:', message);
    const trackerId = message.tracker_id;
    const eventType = message.event_type;
    const unresolvedCount = message.unresolved_count || 0;
    
    // Update smart comment button with new count using simplified system
    if (typeof updateSmartCommentButton === 'function') {
      updateSmartCommentButton(trackerId, unresolvedCount);
    }
    
    // Check if this tracker's comments are currently displayed and refresh them
    const commentsContainer = $(`#comments-list-${trackerId}`);
    if (commentsContainer.length > 0) {
      console.log(`🔄 Refreshing comments for tracker ${trackerId} due to ${eventType}`);
      if (typeof loadCommentsForTracker === 'function') {
        loadCommentsForTracker(trackerId);
      }
    }
    
    // Show brief notification for real-time updates
    if (eventType === 'comment_created') {
      if (typeof showCommentNotification === 'function') {
        showCommentNotification(`New comment added to tracker ${trackerId}`, 'success');
      }
    } else if (eventType === 'comment_updated') {
      if (typeof showCommentNotification === 'function') {
        showCommentNotification(`Comment updated in tracker ${trackerId}`, 'info');
      }
    } else if (eventType === 'comment_resolved') {
      if (typeof showCommentNotification === 'function') {
        showCommentNotification(`Comment resolved in tracker ${trackerId}`, 'success');
      }
    }
    
  } catch (e) {
    console.error('❌ Error handling real-time comment refresh:', e);
  }
}

// Register both as Shiny message handler and global function
Shiny.addCustomMessageHandler('refreshComments', refreshCommentsHandler);
window.refreshCommentsHandler = refreshCommentsHandler;

// Debug: Add WebSocket connection status indicator
Shiny.addCustomMessageHandler('websocket_debug_info', function(message) {
  try {
    console.log('🔧 WebSocket Debug Info:', message);
    
    // Show connection status in console
    if (window.pearlWebSocket) {
      console.log('🔌 WebSocket Status:', window.pearlWebSocket.getStatus());
      console.log('🔌 Is Connected:', window.pearlWebSocket.isConnected());
    }
    
  } catch (e) {
    console.error('Error in WebSocket debug:', e);
  }
});

// Cache for comment summaries so we can apply after tables render
window.pearlCommentSummaries = window.pearlCommentSummaries || {};

// Helper to apply cached summaries to any buttons currently in the DOM
function applyCommentSummariesToButtons() {
  try {
    const map = window.pearlCommentSummaries || {};
    const buttons = document.querySelectorAll('.comment-btn[data-tracker-id]');
    buttons.forEach(btn => {
      const idStr = btn.getAttribute('data-tracker-id');
      if (!idStr) return;
      const id = parseInt(idStr, 10);
      const count = map[id];
      if (typeof count !== 'undefined' && typeof updateSmartCommentButton === 'function') {
        updateSmartCommentButton(id, Number(count));
      }
    });
  } catch (e) {
    console.error('❌ Error applying comment summaries to buttons:', e);
  }
}

// Re-apply cached unresolved counts after any DataTable draw or Shiny output recalculation
$(document).on('draw.dt', 'table.dataTable', function () {
  try { applyCommentSummariesToButtons(); } catch (e) { console.warn('Badge reapply on draw error', e); }
});
$(document).on('shiny:recalculated', function () {
  try { applyCommentSummariesToButtons(); } catch (e) { console.warn('Badge reapply on recalculated error', e); }
});

// Handle initial smart comment button updates from R server
Shiny.addCustomMessageHandler('updateSmartCommentButtons', function(message) {
  try {
    console.log('🎯 Received smart comment button update message:', message);

    // Accept either an array or an object map keyed by tracker_id
    const summaries = message && message.summaries
      ? (Array.isArray(message.summaries) ? message.summaries : Object.values(message.summaries))
      : [];

    if (!summaries.length) {
      console.log('No summaries data provided');
      return;
    }

    // Build cache map and persist globally for later draw callbacks
    const summaryMap = {};

    // Update each smart comment button with the actual unresolved count
    summaries.forEach(summary => {
      const trackerId = summary.tracker_id ?? summary.trackerId ?? summary.id;
      const unresolvedCount = summary.unresolved_count ?? summary.unresolved_comments ?? 0;

      console.log(`🔧 Updating smart button for tracker ${trackerId} with count ${unresolvedCount}`);

      // Update the smart comment button using the existing function
      if (trackerId != null && typeof updateSmartCommentButton === 'function') {
        updateSmartCommentButton(trackerId, unresolvedCount);
        summaryMap[Number(trackerId)] = Number(unresolvedCount);
      } else if (trackerId == null) {
        console.log('⚠️ Missing trackerId in summary:', summary);
      } else {
        console.log('updateSmartCommentButton function not available');
      }
    });

    // Save and re-apply after this message in case tables render after
    window.pearlCommentSummaries = summaryMap;
    applyCommentSummariesToButtons();

  } catch (e) {
    console.error('❌ Error updating smart comment buttons:', e);
  }
});

// Helper function for optimistic badge updates (used by comment_expansion.js)
function updateTrackerBadgeOptimistic(trackerId, eventType, commentData) {
  try {
    console.log(`🔄 Optimistic badge update: tracker=${trackerId}, event=${eventType}`);
    
    // Find the smart comment button for this tracker
    const button = $(`.comment-btn[data-tracker-id="${trackerId}"]`);
    if (button.length === 0) {
      console.log(`No comment button found for tracker ${trackerId}`);
      return;
    }
    
    // Get current count from button
    let currentCount = parseInt(button.attr('data-unresolved-count') || '0');
    
    // Update count based on event type
    if (eventType === 'comment_created' && !commentData.is_resolved) {
      currentCount++;
    } else if (eventType === 'comment_resolved' && commentData.is_resolved) {
      currentCount = Math.max(0, currentCount - 1);
    } else if (eventType === 'comment_unresolved' && !commentData.is_resolved) {
      currentCount++;
    } else if (eventType === 'comment_deleted' && !commentData.is_resolved) {
      currentCount = Math.max(0, currentCount - 1);
    }
    
    // Update the smart comment button
    if (typeof updateSmartCommentButton === 'function') {
      updateSmartCommentButton(trackerId, currentCount);
    }
    
  } catch (e) {
    console.error('❌ Error in optimistic badge update:', e);
  }
}

// Unified badge update handler for cross-browser synchronization
Shiny.addCustomMessageHandler('unifiedCommentBadgeUpdate', function(message) {
  try {
    console.log('🎯 Unified cross-browser badge update:', message);
    
    const trackerId = message.tracker_id;
    const unresolvedCount = message.unresolved_count;
    const source = message.source || 'unknown';
    
    console.log(`🔄 Cross-browser badge update: tracker=${trackerId}, count=${unresolvedCount}, source=${source}`);
    
    // Always use the most recent count value for cross-browser sync
    if (typeof updateSmartCommentButton === 'function') {
      updateSmartCommentButton(trackerId, unresolvedCount);
    } else {
      console.log('⚠️ updateSmartCommentButton function not available');
    }
    
    // Store update metadata for debugging
    const button = $(`.comment-btn[data-tracker-id="${trackerId}"]`);
    if (button.length > 0) {
      button.attr('data-last-update-source', source);
      button.attr('data-last-update-time', Date.now());
      button.attr('data-cross-browser-sync', 'true');
    }
    
  } catch (e) {
    console.error('❌ Error in unified cross-browser badge update:', e);
  }
});

// Dashboard summary card toggle handler
Shiny.addCustomMessageHandler('toggleDashboardCard', function(message) {
  try {
    console.log('📊 Dashboard card toggle:', message);
    
    const cardElement = document.querySelector('[id*="dashboard_summary_card"]');
    const countElement = document.querySelector('[id*="attention_count"]');
    
    if (cardElement) {
      if (message.show && message.count > 0) {
        cardElement.style.display = 'block';
        if (countElement) {
          countElement.textContent = message.count;
          // Update badge color based on urgency
          countElement.className = message.count > 5 ? 
            'badge bg-danger text-white fs-6' : 
            'badge bg-warning text-dark fs-6';
        }
      } else {
        cardElement.style.display = 'none';
      }
    } else {
      console.log('⚠️ Dashboard card element not found');
    }
    
  } catch (e) {
    console.error('❌ Error toggling dashboard card:', e);
  }
});

console.log('✅ Simplified shiny_handlers.js loaded - legacy periodic refresh system removed');