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
    
    // Always update smart comment button (non-disruptive)
    if (typeof updateSmartCommentButton === 'function') {
      updateSmartCommentButton(trackerId, unresolvedCount);
    }
    
    // Check if this tracker's comments are currently displayed and refresh them
    const commentsContainer = $(`#comments-list-${trackerId}`);
    if (commentsContainer.length > 0) {
      // SMART REFRESH: Check if user is actively working in comments
      if (isUserActivelyWorking()) {
        console.log(`🚫 User is actively working - deferring comment refresh for tracker ${trackerId}`);
        queueDeferredUpdate('comment_refresh', {trackerId, eventType});
        
        // Show subtle notification
        if (typeof Shiny !== 'undefined') {
          Shiny.notifications.show({
            html: `Comments updated for tracker ${trackerId}. <small>Will refresh when you're idle.</small>`,
            type: 'info',
            duration: 4000
          });
        }
      } else {
        console.log(`🔄 Safe to refresh comments for tracker ${trackerId} due to ${eventType}`);
        if (typeof loadCommentsForTracker === 'function') {
          loadCommentsForTracker(trackerId);
        }
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

// Handle cross-browser tracker deletion synchronization
function syncTrackerDeletionHandler(message) {
  try {
    console.log('🌍 Cross-browser tracker deletion sync received:', message);
    const trackerId = message.tracker_id;
    const eventType = message.event_type;
    const deletionData = message.deletion_data;
    
    if (trackerId && eventType === 'reporting_effort_tracker_deleted') {
      console.log(`🔄 Syncing tracker deletion across browsers for tracker ${trackerId}`);
      
      // Enhanced cross-browser surgical removal
      const success = removeCrossBrowserTrackerRow(trackerId, deletionData);
      if (success) {
        console.log('✅ Cross-browser surgical removal successful for tracker:', trackerId);
        
        // Show brief notification
        if (typeof Shiny !== 'undefined') {
          Shiny.notifications.show({
            html: `Tracker ${trackerId} was deleted in another session`,
            type: 'message',
            duration: 3000
          });
        }
        return;
      }
      
      // Fallback to table refresh trigger - BUT CHECK FOR USER ACTIVITY FIRST
      console.log('⚠️ Cross-browser surgical removal failed, checking if safe to refresh...');
      
      if (isUserActivelyWorking()) {
        console.log('🚫 User is actively working - deferring table refresh');
        queueDeferredUpdate('tracker_deleted', {trackerId, deletionData});
        
        // Show non-intrusive notification
        if (typeof Shiny !== 'undefined') {
          Shiny.notifications.show({
            html: `Tracker ${trackerId} was deleted. <button onclick="applyDeferredUpdates()" class="btn btn-sm btn-outline-primary">Refresh now</button> or it will auto-refresh when you're idle.`,
            type: 'warning',
            duration: 8000
          });
        }
      } else {
        console.log('✅ User is idle - safe to refresh table');
        if (typeof Shiny !== 'undefined') {
          // Trigger module refresh
          Shiny.setInputValue('reporting_effort_tracker-force_refresh', Date.now(), {priority: 'event'});
          
          // Show notification
          Shiny.notifications.show({
            html: `Tracker deleted in another session - refreshing view`,
            type: 'message',
            duration: 3000
          });
        }
      }
    }
    
  } catch (e) {
    console.error('❌ Error handling cross-browser tracker deletion sync:', e);
  }
}

// Enhanced cross-browser surgical removal function
function removeCrossBrowserTrackerRow(trackerId, deletionData) {
  console.log('🔪 Cross-browser surgical removal for tracker:', trackerId);
  
  // Find and remove from all DataTable instances
  const tableSelectors = [
    '#reporting_effort_tracker-tracker_table_tlf',
    '#reporting_effort_tracker-tracker_table_sdtm', 
    '#reporting_effort_tracker-tracker_table_adam'
  ];
  
  let removedCount = 0;
  
  tableSelectors.forEach(selector => {
    try {
      const $table = $(selector);
      if ($table.length && $.fn.DataTable.isDataTable($table[0])) {
        const dataTable = $table.DataTable();
        
        // Find and remove rows by tracker ID
        dataTable.rows().every(function(rowIdx) {
          const rowNode = this.node();
          const $row = $(rowNode);
          
          // Look for delete button with matching data-id
          const $deleteBtn = $row.find('button[data-action="delete"][data-id="' + trackerId + '"]');
          
          if ($deleteBtn.length > 0) {
            console.log(`✂️ Found tracker ${trackerId} in table ${selector}, removing...`);
            
            // Smooth animation for cross-browser removal
            $row.addClass('table-warning').fadeOut(600, () => {
              // Remove from DataTable
              this.remove();
              dataTable.draw(false); // Redraw without resetting pagination
              removedCount++;
              console.log(`✅ Removed tracker ${trackerId} from ${selector}`);
            });
            
            return false; // Break out of loop
          }
        });
      }
    } catch (error) {
      console.error(`❌ Error processing table ${selector}:`, error);
    }
  });
  
  // Also try simpler row removal by item code if DataTable approach failed
  if (removedCount === 0 && deletionData?.tracker?.item_code) {
    const itemCode = deletionData.tracker.item_code;
    console.log('🔍 Trying alternative removal by item code:', itemCode);
    
    $('tr').each(function() {
      const $row = $(this);
      const firstCell = $row.find('td:first-child').text().trim();
      
      if (firstCell === itemCode) {
        console.log(`✂️ Found tracker by item code ${itemCode}, removing...`);
        $row.addClass('table-warning').fadeOut(600, () => {
          $row.remove();
          removedCount++;
        });
        return false; // Break out of each
      }
    });
  }
  
  if (removedCount === 0) {
    console.log('⚠️ No tracker rows found to remove for ID:', trackerId);
    return false;
  }
  
  console.log(`✅ Cross-browser removal completed: ${removedCount} row(s) removed`);
  return true;
}

// Register tracker deletion sync handler
Shiny.addCustomMessageHandler('syncTrackerDeletion', syncTrackerDeletionHandler);
window.refreshCommentsHandler = refreshCommentsHandler;

// =============================================================================
// SMART USER ACTIVITY DETECTION & DEFERRED UPDATES
// =============================================================================

let deferredUpdates = [];
let lastUserActivity = Date.now();
let userActivityTimer = null;

// Track user activity to prevent disruptive updates
function trackUserActivity() {
  lastUserActivity = Date.now();
  
  // Clear existing timer
  if (userActivityTimer) {
    clearTimeout(userActivityTimer);
  }
  
  // Set timer to apply deferred updates after 10 seconds of inactivity
  userActivityTimer = setTimeout(() => {
    if (deferredUpdates.length > 0) {
      console.log('⏰ User idle detected - applying deferred updates');
      applyDeferredUpdates();
    }
  }, 10000); // 10 seconds of inactivity
}

// Detect if user is actively working (typing, modal open, etc.)
function isUserActivelyWorking() {
  try {
    // Check if any text inputs/textareas are focused
    const activeElement = document.activeElement;
    if (activeElement && (
      activeElement.tagName === 'INPUT' || 
      activeElement.tagName === 'TEXTAREA' || 
      activeElement.contentEditable === 'true'
    )) {
      console.log('🖊️ User is typing in:', activeElement.tagName, activeElement.id || activeElement.className);
      return true;
    }
    
    // Check if any modals or dialogs are open
    const openModals = document.querySelectorAll('.modal.show, .swal2-container, [role="dialog"]:not([hidden])');
    if (openModals.length > 0) {
      console.log('📋 User has open modal/dialog');
      return true;
    }
    
    // Check if user has typed/clicked recently (within 5 seconds)
    const timeSinceActivity = Date.now() - lastUserActivity;
    if (timeSinceActivity < 5000) {
      console.log('⚡ Recent user activity detected:', timeSinceActivity, 'ms ago');
      return true;
    }
    
    // Check if comment expansion is open
    const openComments = document.querySelectorAll('#comments-modal.show, .comment-form:not([style*="display: none"])');
    if (openComments.length > 0) {
      console.log('💬 User has comment interface open');
      return true;
    }
    
    return false;
    
  } catch (e) {
    console.error('❌ Error checking user activity:', e);
    return true; // Err on the side of caution
  }
}

// Queue updates for later application
function queueDeferredUpdate(updateType, updateData) {
  deferredUpdates.push({
    type: updateType,
    data: updateData,
    timestamp: Date.now()
  });
  
  console.log(`📥 Queued deferred update: ${updateType}`, updateData);
  console.log(`📊 Total deferred updates: ${deferredUpdates.length}`);
  
  // Add subtle visual indicator for pending updates
  updateDeferredUpdatesIndicator();
}

// Show/hide visual indicator for deferred updates
function updateDeferredUpdatesIndicator() {
  const count = deferredUpdates.length;
  
  // Remove existing indicator
  $('.deferred-updates-indicator').remove();
  
  if (count > 0) {
    // Add small indicator near the actions button
    const indicator = $(`
      <span class="deferred-updates-indicator badge bg-warning text-dark ms-2" 
            title="${count} update${count > 1 ? 's' : ''} pending - will apply when you're idle">
        ${count} pending
      </span>
    `);
    
    // Find a good place to show it (near the Actions button)
    const actionsButton = $('button:contains("Actions")').first();
    if (actionsButton.length > 0) {
      actionsButton.parent().append(indicator);
    } else {
      // Fallback: add to page somewhere visible
      $('body').append($(`
        <div class="deferred-updates-indicator position-fixed top-0 end-0 m-3 alert alert-warning alert-dismissible" 
             style="z-index: 9999; max-width: 300px;">
          <strong>${count} update${count > 1 ? 's' : ''} pending</strong><br>
          <small>Changes from other users will apply when you're idle</small>
          <button type="button" class="btn btn-sm btn-outline-dark mt-1" onclick="applyDeferredUpdates()">
            Apply now
          </button>
        </div>
      `));
    }
  }
}

// Apply all deferred updates
function applyDeferredUpdates() {
  if (deferredUpdates.length === 0) {
    console.log('📭 No deferred updates to apply');
    return;
  }
  
  console.log(`🔄 Applying ${deferredUpdates.length} deferred updates`);
  
  const updateCount = deferredUpdates.length;
  deferredUpdates.forEach(update => {
    if (update.type === 'tracker_deleted') {
      const {trackerId, deletionData} = update.data;
      console.log('🔄 Applying deferred tracker deletion:', trackerId);
      
      // Force table refresh as final fallback
      if (typeof Shiny !== 'undefined') {
        Shiny.setInputValue('reporting_effort_tracker-force_refresh', Date.now(), {priority: 'event'});
      }
    } else if (update.type === 'comment_refresh') {
      const {trackerId, eventType} = update.data;
      console.log('🔄 Applying deferred comment refresh:', trackerId);
      
      // Refresh comments for this tracker
      if (typeof loadCommentsForTracker === 'function') {
        loadCommentsForTracker(trackerId);
      }
    }
  });
  
  // Clear the queue
  deferredUpdates = [];
  
  // Remove visual indicator
  updateDeferredUpdatesIndicator();
  
  // Show completion notification
  if (typeof Shiny !== 'undefined') {
    Shiny.notifications.show({
      html: `Applied ${updateCount} deferred update${updateCount > 1 ? 's' : ''} - view refreshed`,
      type: 'success',
      duration: 3000
    });
  }
}

// Set up activity tracking - initialize when DOM is ready
$(document).ready(function() {
  document.addEventListener('keydown', trackUserActivity);
  document.addEventListener('mousedown', trackUserActivity);
  document.addEventListener('focus', trackUserActivity, true);
  document.addEventListener('input', trackUserActivity);
  
  // Track activity in comment modals specifically
  $(document).on('focus', 'textarea, input[type="text"], input[type="email"]', trackUserActivity);
  $(document).on('input', 'textarea, input[type="text"], input[type="email"]', trackUserActivity);
  
  console.log('🎯 Smart activity tracking initialized - user work will be protected');
});

// Make functions globally available
window.applyDeferredUpdates = applyDeferredUpdates;
window.isUserActivelyWorking = isUserActivelyWorking;
window.deferredUpdatesCount = () => deferredUpdates.length;

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

// Smart comment button update function (bridges to updateCommentButtonBadge)
window.updateSmartCommentButton = function(trackerId, unresolvedCount) {
  console.log(`🔧 updateSmartCommentButton: tracker=${trackerId}, count=${unresolvedCount}`);
  
  // Use the existing badge update function if available
  if (typeof window.updateCommentButtonBadge === 'function') {
    window.updateCommentButtonBadge(trackerId, unresolvedCount);
    return;
  }
  
  // Fallback implementation for button update
  const button = document.querySelector(`[data-tracker-id="${trackerId}"]`);
  if (!button) {
    console.warn(`No comment button found for tracker ${trackerId}`);
    return;
  }
  
  // Store the count as data attribute
  button.setAttribute('data-unresolved-count', unresolvedCount);
  
  if (unresolvedCount === 0) {
    // Green button with just "+"
    button.className = 'btn btn-success btn-sm comment-btn';
    button.innerHTML = '<i class="fa fa-plus"></i>';
    button.title = 'Add Comment';
  } else {
    // Yellow button with "+N" 
    button.className = 'btn btn-warning btn-sm comment-btn';
    button.innerHTML = `<i class="fa fa-plus"></i> ${unresolvedCount}`;
    button.title = `${unresolvedCount} Unresolved Comments`;
  }
};

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
      const unresolvedCount = summary.unresolved_count ?? 0;

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