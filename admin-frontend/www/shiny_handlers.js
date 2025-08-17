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

// Helper function to render badges based on summary data
function renderCommentBadges(summary) {
  var badgesHtml = '';
  
  // PRIORITY: Unresolved comments badge (most important - always show first)
  if (summary.unresolved_comments && summary.unresolved_comments > 0) {
    badgesHtml += '<span class="badge bg-warning text-dark me-1" title="⚠️ ' + summary.unresolved_comments + ' Unaddressed Comments - Action Required!" style="font-weight: bold;">' + 
                 '<i class="fa fa-exclamation-triangle me-1"></i>' + summary.unresolved_comments + '</span>';
  }
  
  // Add total comments badge if there are any comments (but less prominent)
  if (summary.total_comments && summary.total_comments > 0) {
    badgesHtml += '<span class="badge bg-info me-1" title="Total Comments">' + 
                 summary.total_comments + '</span>';
  }
  
  // Add pinned comments badge if there are any
  if (summary.pinned_comments && summary.pinned_comments > 0) {
    badgesHtml += '<span class="badge bg-danger" title="Pinned Comments">' + 
                 '<i class="fa fa-thumb-tack me-1"></i>' + summary.pinned_comments + '</span>';
  }
  
  return badgesHtml;
}

// Helper function to update button styling based on comments
function updateCommentButtonStyle(trackerId, summary) {
  var badgeContainer = document.getElementById('badges-' + trackerId);
  if (!badgeContainer) return;
  
  var commentButton = badgeContainer.closest('.comment-column').querySelector('.comment-add-btn');
  if (commentButton && summary.unresolved_comments && summary.unresolved_comments > 0) {
    // Add a subtle pulsing animation to draw attention
    commentButton.classList.add('btn-warning');
    commentButton.classList.remove('btn-success');
    commentButton.style.animation = 'subtle-pulse 2s infinite';
    commentButton.title = 'Add Comment - ' + summary.unresolved_comments + ' unaddressed comment(s) need attention!';
  } else if (commentButton) {
    // Reset to normal state
    commentButton.classList.add('btn-success');
    commentButton.classList.remove('btn-warning');
    commentButton.style.animation = '';
    commentButton.title = 'Add Comment';
  }
}

// Optimistic badge update for single tracker (immediate feedback)
function updateTrackerBadgeOptimistic(trackerId, changeType, commentData) {
  console.log('🚀 Optimistic badge update for tracker', trackerId, 'change:', changeType);
  
  var badgeContainer = document.getElementById('badges-' + trackerId);
  if (!badgeContainer) {
    console.warn('Badge container not found for tracker', trackerId);
    return;
  }
  
  // Get current counts from existing badges or start with zeros
  var currentSummary = getCurrentBadgeCounts(trackerId);
  
  // Apply optimistic changes based on comment type
  switch (changeType) {
    case 'comment_created':
      currentSummary.total_comments++;
      // New comments are unresolved by default unless specified otherwise
      if (!commentData.is_resolved) {
        currentSummary.unresolved_comments++;
      }
      if (commentData.is_pinned) {
        currentSummary.pinned_comments++;
      }
      break;
      
    case 'comment_resolved':
      if (commentData.is_resolved) {
        currentSummary.unresolved_comments = Math.max(0, currentSummary.unresolved_comments - 1);
      } else {
        currentSummary.unresolved_comments++;
      }
      break;
      
    case 'comment_deleted':
      currentSummary.total_comments = Math.max(0, currentSummary.total_comments - 1);
      if (!commentData.is_resolved) {
        currentSummary.unresolved_comments = Math.max(0, currentSummary.unresolved_comments - 1);
      }
      if (commentData.is_pinned) {
        currentSummary.pinned_comments = Math.max(0, currentSummary.pinned_comments - 1);
      }
      break;
  }
  
  // Update the badges immediately
  updateSingleTrackerBadge(trackerId, currentSummary);
  
  console.log('✅ Optimistic update complete for tracker', trackerId);
}

// Get current badge counts from the DOM
function getCurrentBadgeCounts(trackerId) {
  var badgeContainer = document.getElementById('badges-' + trackerId);
  var summary = {
    total_comments: 0,
    unresolved_comments: 0,
    pinned_comments: 0
  };
  
  if (!badgeContainer) return summary;
  
  // Parse existing badges to get current counts
  var totalBadge = badgeContainer.querySelector('.badge.bg-info');
  var unresolvedBadge = badgeContainer.querySelector('.badge.bg-warning');
  var pinnedBadge = badgeContainer.querySelector('.badge.bg-danger');
  
  if (totalBadge) {
    summary.total_comments = parseInt(totalBadge.textContent.trim()) || 0;
  }
  
  if (unresolvedBadge) {
    // Extract number from text content, accounting for the icon
    var text = unresolvedBadge.textContent.replace(/[^\d]/g, '');
    summary.unresolved_comments = parseInt(text) || 0;
  }
  
  if (pinnedBadge) {
    // Extract number from text content, accounting for the icon
    var text = pinnedBadge.textContent.replace(/[^\d]/g, '');
    summary.pinned_comments = parseInt(text) || 0;
  }
  
  return summary;
}

// Update badges for a single tracker
function updateSingleTrackerBadge(trackerId, summary) {
  var badgeContainer = document.getElementById('badges-' + trackerId);
  if (!badgeContainer) {
    console.warn('Badge container not found for tracker', trackerId);
    return;
  }
  
  badgeContainer.innerHTML = renderCommentBadges(summary);
  updateCommentButtonStyle(trackerId, summary);
  
  // Add a subtle flash effect to indicate update
  badgeContainer.style.opacity = '0.7';
  setTimeout(() => {
    badgeContainer.style.opacity = '1';
  }, 150);
}

// Update comment badges with summaries from the API
Shiny.addCustomMessageHandler('updateCommentBadges', function (message) {
  try {
    console.log('updateCommentBadges called with:', message);
    if (!message.summaries) {
      console.log('No summaries in message');
      return;
    }
    
    console.log('Processing summaries for trackers:', Object.keys(message.summaries));
    
    // Iterate through all comment badge containers
    Object.keys(message.summaries).forEach(function(trackerId) {
      var summary = message.summaries[trackerId];
      updateSingleTrackerBadge(trackerId, summary);
    });
    
    console.log('Updated comment badges for', Object.keys(message.summaries).length, 'trackers');
  } catch (e) {
    console.warn('updateCommentBadges error', e);
  }
});

// Handle real-time comment updates from WebSocket - ENHANCED for cross-browser sync
Shiny.addCustomMessageHandler('updateCommentBadgeRealtime', function(message) {
  try {
    // Enhanced logging for cross-browser debugging
    if (message.is_cross_browser) {
      console.log('🌍 CROSS-BROWSER WebSocket badge update received:', message);
    } else {
      console.log('🔄 Local real-time comment badge update:', message);
    }
    
    if (!message.tracker_id) {
      console.warn('No tracker_id in real-time badge update message');
      return;
    }
    
    // Determine the change type and comment data
    var changeType = message.event_type;
    var commentData = message.comment_data || {};
    var source = message.source || 'local';
    
    console.log(`📊 Processing badge update: tracker=${message.tracker_id}, type=${changeType}, source=${source}`);
    
    // Apply badge update (optimistic for local, authoritative for cross-browser)
    updateTrackerBadgeOptimistic(message.tracker_id, changeType, commentData);
    
    // Add visual indication for cross-browser updates
    if (message.is_cross_browser) {
      var badgeContainer = document.getElementById('badges-' + message.tracker_id);
      if (badgeContainer) {
        // Add brief flash effect to show cross-browser update
        badgeContainer.style.backgroundColor = '#e3f2fd';
        badgeContainer.style.transition = 'background-color 0.3s';
        setTimeout(() => {
          badgeContainer.style.backgroundColor = '';
        }, 1000);
      }
    }
    
  } catch (e) {
    console.error('❌ Error in real-time comment badge update:', e);
  }
});

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