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

// ============================================================================
// UNIVERSAL CRUD EVENT HANDLER (Phase 3)
// ============================================================================

/**
 * Universal handler for all CRUD events from R server modules
 * Replaces entity-specific WebSocket observers with unified pattern
 */
Shiny.addCustomMessageHandler('universal_crud_refresh', function(message) {
  console.log('🌍 Universal CRUD refresh received:', message);
  
  if (!message || !message.entity_type) {
    console.warn('⚠️ Invalid universal CRUD message:', message);
    return;
  }
  
  // Route to appropriate Universal CRUD Manager if available
  if (window.crudManager) {
    const crudEvent = {
      type: `${message.entity_type}_refresh`,
      operation: 'refresh',
      entity: {
        type: message.entity_type,
        id: message.entity_id || null,
        data: message.data || null
      },
      source: 'shiny_server',
      timestamp: Date.now()
    };
    
    console.log('📤 Routing to Universal CRUD Manager:', crudEvent);
    window.crudManager.handleCRUDEvent(crudEvent);
  } else {
    console.warn('⚠️ Universal CRUD Manager not available, falling back to legacy');
    // Fallback to direct Shiny refresh if CRUD manager not available
    if (window.Shiny && window.Shiny.setInputValue && message.refresh_input) {
      Shiny.setInputValue(message.refresh_input, Date.now(), {priority: 'event'});
    } else if (!window.Shiny.setInputValue) {
      console.log('⚠️ Shiny.setInputValue not available yet - fallback refresh deferred');
    }
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

// ============================================================================
// LEGACY COMMENT HANDLERS (Replaced by Universal CRUD Manager in Phase 3)
// ============================================================================
// Note: Comment handling now routed through Universal CRUD Manager
// Legacy handlers kept for backward compatibility during transition

// Legacy tracker deletion handlers moved to Universal CRUD Manager
// These functions are now handled by the context-aware system

// =============================================================================
// ACTIVITY TRACKING (Moved to Universal CRUD Manager in Phase 3)
// =============================================================================
// Note: Activity detection and deferred updates now handled by Universal CRUD Manager
// Legacy functions kept for backward compatibility only

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

// Custom handler for package cross-browser synchronization
Shiny.addCustomMessageHandler('triggerPackageRefresh', function(message) {
  try {
    console.log('📦 Package refresh triggered from global observer:', message);
    
    // Trigger the packages module's CRUD refresh input
    // This simulates the Universal CRUD Manager triggering a refresh
    if (window.Shiny && window.Shiny.setInputValue) {
      Shiny.setInputValue('packages-crud_refresh', Math.random(), {priority: 'event'});
      console.log('✅ Package module refresh triggered for cross-browser sync');
    } else {
      console.log('⚠️ Shiny.setInputValue not available yet - package refresh deferred');
    }
    
  } catch (e) {
    console.error('❌ Error triggering package refresh:', e);
  }
});

// Custom handler for study cross-browser synchronization
Shiny.addCustomMessageHandler('triggerStudyRefresh', function(message) {
  try {
    console.log('📚 Study refresh triggered from global observer:', message);
    
    // Trigger the study_tree module's CRUD refresh input
    if (window.Shiny && window.Shiny.setInputValue) {
      Shiny.setInputValue('study_tree-crud_refresh', Math.random(), {priority: 'event'});
      console.log('✅ Study Tree module refresh triggered for cross-browser sync');
    } else {
      console.log('⚠️ Shiny.setInputValue not available yet - study refresh deferred');
    }
    
  } catch (e) {
    console.error('❌ Error triggering study refresh:', e);
  }
});

// Custom handler for package item cross-browser synchronization
Shiny.addCustomMessageHandler('triggerPackageItemRefresh', function(message) {
  try {
    console.log('📦 Package Item refresh triggered from global observer:', message);
    
    // Simple approach matching the working tracker pattern
    if (window.Shiny && window.Shiny.setInputValue) {
      Shiny.setInputValue('package_items-crud_refresh', Math.random(), {priority: 'event'});
      console.log('✅ Package Items module refresh triggered for cross-browser sync');
    } else {
      console.log('⚠️ Shiny.setInputValue not available yet - package items refresh deferred');
    }
    
  } catch (e) {
    console.error('❌ Error triggering package item refresh:', e);
  }
});

// Custom handler for tracker update cross-browser synchronization
Shiny.addCustomMessageHandler('triggerTrackerRefresh', function(message) {
  try {
    console.log('📊 Tracker refresh triggered from global observer:', message);
    
    // Trigger the reporting_effort_tracker module's CRUD refresh input
    if (window.Shiny && window.Shiny.setInputValue) {
      Shiny.setInputValue('reporting_effort_tracker-crud_refresh', Math.random(), {priority: 'event'});
      console.log('✅ Tracker module refresh triggered for cross-browser sync');
    } else {
      console.log('⚠️ Shiny.setInputValue not available yet - tracker refresh deferred');
    }
    
  } catch (e) {
    console.error('❌ Error triggering tracker refresh:', e);
  }
});


// =============================================================================
// DATATABLE ROW SELECTION UTILITIES
// =============================================================================

/**
 * Custom message handler to get visible row indices after all filtering
 * and trigger selection via callback. This ensures "Select All" only selects
 * rows that are visible after both server-side (comment filter) and client-side
 * (DataTable search box) filters are applied.
 */
Shiny.addCustomMessageHandler('getAndSelectVisibleRows', function(message) {
  var tableId = message.tableId;
  var callbackId = message.callbackId;

  console.log('Getting visible rows for table:', tableId);

  var $table = $('#' + tableId);
  if ($table.length === 0) {
    console.warn('Table not found:', tableId);
    return;
  }

  var table = $table.DataTable();
  if (!table) {
    console.warn('DataTable instance not found for:', tableId);
    return;
  }

  // Get indices of rows visible after all filtering (search box, etc.)
  // { search: 'applied' } returns only rows matching current search/filter state
  var visibleRows = table.rows({ search: 'applied' });
  var visibleIndices = visibleRows.indexes().toArray();

  if (visibleIndices.length === 0) {
    console.log('No visible rows to select');
    // Still send back empty array so R can show notification
    if (window.Shiny && window.Shiny.setInputValue) {
      Shiny.setInputValue(callbackId, [], { priority: 'event' });
    }
    return;
  }

  // Convert to 1-based indices for R compatibility
  var rIndices = visibleIndices.map(function(i) { return i + 1; });

  console.log('Found', rIndices.length, 'visible rows to select:', rIndices);

  // Send indices back to Shiny to trigger selection via DT proxy
  if (window.Shiny && window.Shiny.setInputValue) {
    Shiny.setInputValue(callbackId, rIndices, { priority: 'event' });
  }
});

// =============================================================================
// PROGRAMMER DASHBOARD ACTION BUTTON HANDLERS
// =============================================================================

/**
 * Handler for quick status update buttons in the Programmer Dashboard
 * Sends click data to Shiny server for processing
 */
$(document).on('click', '.quick-status-btn', function(e) {
  e.preventDefault();
  e.stopPropagation();

  var $btn = $(this);
  var trackerId = $btn.data('tracker-id');
  var newStatus = $btn.data('status');
  var statusType = $btn.data('type'); // 'production' or 'qc'

  console.log('🚀 Quick status update:', { trackerId, newStatus, statusType });

  if (window.Shiny && window.Shiny.setInputValue) {
    Shiny.setInputValue('admin_dashboard-quick_status_click', {
      tracker_id: trackerId,
      new_status: newStatus,
      status_type: statusType,
      timestamp: Date.now()
    }, { priority: 'event' });
  }
});

/**
 * Handler for "Go to Tracker" button in the Programmer Dashboard
 * Stores navigation params and triggers tab switch + row highlight
 */
$(document).on('click', '.go-to-tracker-btn', function(e) {
  e.preventDefault();
  e.stopPropagation();

  var $btn = $(this);
  var reportingEffortId = $btn.data('reporting-effort-id');
  var itemCode = $btn.data('item-code');

  console.log('🔗 Navigate to Tracker:', { reportingEffortId, itemCode });

  // Store navigation params in sessionStorage for retrieval after tab switch
  sessionStorage.setItem('dashboard_nav_re_id', reportingEffortId);
  sessionStorage.setItem('dashboard_nav_item_code', itemCode);

  if (window.Shiny && window.Shiny.setInputValue) {
    Shiny.setInputValue('dashboard_navigate_to_tracker', {
      reporting_effort_id: reportingEffortId,
      item_code: itemCode,
      timestamp: Date.now()
    }, { priority: 'event' });
  }
});

/**
 * Show/hide loading overlay during navigation
 */
function showNavigationLoadingOverlay(show, message) {
  var overlayId = 'navigation-loading-overlay';
  var overlay = document.getElementById(overlayId);
  
  if (show) {
    // Create overlay if it doesn't exist
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = overlayId;
      overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; ' +
        'background: rgba(255, 255, 255, 0.85); z-index: 9999; display: flex; ' +
        'flex-direction: column; justify-content: center; align-items: center; ' +
        'backdrop-filter: blur(2px);';
      
      var spinner = document.createElement('div');
      spinner.className = 'spinner-border text-primary';
      spinner.setAttribute('role', 'status');
      spinner.style.cssText = 'width: 3rem; height: 3rem;';
      
      var spinnerText = document.createElement('span');
      spinnerText.className = 'visually-hidden';
      spinnerText.textContent = 'Loading...';
      spinner.appendChild(spinnerText);
      
      var messageDiv = document.createElement('div');
      messageDiv.id = 'navigation-loading-message';
      messageDiv.style.cssText = 'margin-top: 1rem; font-size: 1.1rem; color: #333; font-weight: 500;';
      messageDiv.textContent = message || 'Navigating to Tracker...';
      
      overlay.appendChild(spinner);
      overlay.appendChild(messageDiv);
      document.body.appendChild(overlay);
    } else {
      // Update message if overlay exists
      var msgDiv = document.getElementById('navigation-loading-message');
      if (msgDiv && message) {
        msgDiv.textContent = message;
      }
      overlay.style.display = 'flex';
    }
    console.log('🔄 Showing navigation loading overlay');
  } else {
    // Hide overlay
    if (overlay) {
      overlay.style.display = 'none';
      console.log('✅ Hiding navigation loading overlay');
    }
  }
}

/**
 * Close any open Bootstrap dropdown menus
 */
function closeAllDropdowns() {
  // Close Bootstrap 5 dropdowns
  var openDropdowns = document.querySelectorAll('.dropdown-menu.show');
  openDropdowns.forEach(function(dropdown) {
    dropdown.classList.remove('show');
  });
  
  // Also remove 'show' class from dropdown toggles
  var dropdownToggles = document.querySelectorAll('.nav-link[aria-expanded="true"]');
  dropdownToggles.forEach(function(toggle) {
    toggle.setAttribute('aria-expanded', 'false');
    toggle.classList.remove('show');
  });
  
  // Click elsewhere to close dropdowns (fallback)
  document.body.click();
  
  console.log('📂 Closed dropdown menus');
}

/**
 * Custom message handler to handle navigation from Dashboard to Tracker Management
 * First switches to the Tracker Management tab, then sets the reporting effort dropdown
 * and triggers row highlighting
 */
Shiny.addCustomMessageHandler('dashboardNavToTracker', function(message) {
  try {
    console.log('📍 Dashboard navigation to tracker:', message);

    var reportingEffortId = message.reporting_effort_id;
    var itemCode = message.item_code;

    if (!reportingEffortId) {
      console.warn('No reporting_effort_id provided for navigation');
      return;
    }

    // Show loading overlay immediately
    showNavigationLoadingOverlay(true, 'Navigating to Tracker Management...');

    // Step 1: Switch to the Tracker Management tab
    // The tab is nested inside "Reporting Management" nav_menu (Bootstrap 5 dropdown)
    // We need to find and click on the specific tab
    
    var switchToTrackerTab = function() {
      // First, try to find Tracker Management tab in the navbar
      // In bslib page_navbar with nav_menu, the dropdown items are structured differently
      
      // Try multiple selectors to find the Tracker Management link/button
      var trackerTab = null;
      
      // Check for visible Tracker Management tab first
      var visibleTab = document.querySelector('a.nav-link[data-value="reporting_effort_tracker_tab"], button.nav-link[data-value="reporting_effort_tracker_tab"]');
      if (visibleTab) {
        trackerTab = visibleTab;
        console.log('🎯 Found Tracker Management tab by data-value');
      }
      
      // If not found, look inside dropdown menu
      if (!trackerTab) {
        // Look for dropdown items with Tracker Management text
        var dropdownItems = document.querySelectorAll('.dropdown-menu .nav-link, .dropdown-menu a');
        dropdownItems.forEach(function(item) {
          if (item.textContent.includes('Tracker Management')) {
            trackerTab = item;
            console.log('🎯 Found Tracker Management tab in dropdown');
          }
        });
      }
      
      // If still not found, we need to open the Reporting Management dropdown first
      if (!trackerTab) {
        console.log('🔓 Opening Reporting Management dropdown first');
        
        // Find the Reporting Management dropdown toggle
        var dropdownToggle = null;
        document.querySelectorAll('.nav-link').forEach(function(link) {
          if (link.textContent.includes('Reporting Management')) {
            dropdownToggle = link;
          }
        });
        
        if (dropdownToggle) {
          // Click to open dropdown
          dropdownToggle.click();
          
          // Wait for dropdown to open, then find and click Tracker Management
          setTimeout(function() {
            var items = document.querySelectorAll('.dropdown-menu .nav-link, .dropdown-menu a, .nav-link');
            items.forEach(function(item) {
              if (item.textContent.includes('Tracker Management')) {
                console.log('🎯 Clicking Tracker Management tab after dropdown opened');
                item.click();
                
                // Close the dropdown after clicking the tab
                setTimeout(closeAllDropdowns, 100);
              }
            });
          }, 200);
        } else {
          console.warn('❌ Could not find Reporting Management dropdown');
          showNavigationLoadingOverlay(false);
        }
      } else {
        // Click the found tab
        console.log('🎯 Clicking Tracker Management tab');
        trackerTab.click();
        
        // Close the dropdown after clicking the tab
        setTimeout(closeAllDropdowns, 100);
      }
    };
    
    // Update loading message
    showNavigationLoadingOverlay(true, 'Switching to Tracker Management...');
    
    // Switch tab first
    switchToTrackerTab();

    // Step 2: After tab switch, send the reporting effort ID to Shiny
    // Use a longer delay to ensure the tab has fully loaded
    setTimeout(function() {
      // Update loading message
      showNavigationLoadingOverlay(true, 'Loading tracker data...');
      
      if (window.Shiny && window.Shiny.setInputValue) {
        console.log('📤 Sending dashboard_nav_select to Shiny');
        Shiny.setInputValue('reporting_effort_tracker-dashboard_nav_select', {
          reporting_effort_id: reportingEffortId,
          item_code: itemCode,
          timestamp: Date.now()
        }, { priority: 'event' });
      }
    }, 800);

  } catch (e) {
    console.error('❌ Error in dashboard navigation to tracker:', e);
    showNavigationLoadingOverlay(false);
  }
});

/**
 * Custom message handler to filter and highlight a specific row in the Tracker table
 * Called after navigation from Dashboard to Tracker Management
 * Now filters the table first, then highlights the matching row
 */
Shiny.addCustomMessageHandler('highlightTrackerRow', function(message) {
  try {
    console.log('✨ Filter and highlight tracker row:', message);

    var itemCode = message.item_code;
    if (!itemCode) {
      console.warn('No item_code provided for filtering/highlighting');
      showNavigationLoadingOverlay(false);
      return;
    }

    // Update loading message to show filtering in progress
    showNavigationLoadingOverlay(true, 'Filtering for ' + itemCode + '...');

    // Clear previous highlights
    $('table.dataTable tr').removeClass('highlight-row');

    // Wait for table to render, then filter and highlight
    setTimeout(function() {
      // Find all DataTables on the page
      var tables = $.fn.dataTable.tables();
      var found = false;

      // Apply filter to each DataTable
      $(tables).each(function() {
        var table = $(this).DataTable();
        
        // Apply search filter with the item code
        table.search(itemCode).draw();
        console.log('🔍 Applied search filter for:', itemCode);
      });

      // After filtering, wait a moment then highlight and scroll
      setTimeout(function() {
        var $rows = $('table.dataTable tbody tr');
        
        $rows.each(function() {
          var $row = $(this);
          var rowText = $row.text();

          // Check if this row contains the item code
          if (rowText.indexOf(itemCode) !== -1) {
            $row.addClass('highlight-row');

            // Scroll row into view
            var rowOffset = $row.offset();
            if (rowOffset) {
              $('html, body').animate({
                scrollTop: rowOffset.top - 200
              }, 300);
            }

            console.log('✅ Row filtered and highlighted for item:', itemCode);
            found = true;
            return false; // Break the loop
          }
        });

        if (!found) {
          console.log('⚠️ No row found containing:', itemCode);
        }

        // Hide the loading overlay - navigation complete
        showNavigationLoadingOverlay(false);

        // Remove highlight after 8 seconds, but keep filter
        setTimeout(function() {
          $('table.dataTable tr').removeClass('highlight-row');
        }, 8000);

      }, 300); // Wait for filter to apply

    }, 800); // Wait for table to render

  } catch (e) {
    console.error('❌ Error filtering/highlighting tracker row:', e);
    showNavigationLoadingOverlay(false);
  }
});

console.log('✅ Simplified shiny_handlers.js loaded - legacy periodic refresh system removed');