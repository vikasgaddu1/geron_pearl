/**
 * DataTable Callback Utilities
 * Phase 2B - Medium Priority Implementation
 * 
 * Provides standardized JavaScript utilities for DataTable drawCallback functions
 * to eliminate duplicate button event handler patterns across modules.
 */

// =============================================================================
// DATATABLE CALLBACK PATTERNS (Phase 2B - Medium Priority)
// =============================================================================

/**
 * Creates a standardized drawCallback function for DataTables with action buttons
 * @param {string} tableId - The ID of the DataTable (without # prefix)
 * @param {string} moduleNamespace - The Shiny module namespace 
 * @param {Array} actionTypes - Array of action types to handle (e.g., ['edit', 'delete'])
 * @param {Function} customCallback - Optional custom callback function
 * @returns {Function} drawCallback function for DataTable options
 */
function createStandardDrawCallback(tableId, moduleNamespace, actionTypes = ['edit', 'delete'], customCallback = null) {
  return function() {
    const tableSelector = '#' + tableId;
    const $table = $(tableSelector);
    
    // Debug logging
    console.log(`🔧 Setting up action handlers for table: ${tableId}, module: ${moduleNamespace}`);
    
    // Attach handlers for each action type
    actionTypes.forEach(action => {
      const buttonSelector = `button[data-action='${action}']`;
      
      // Remove existing handlers to prevent duplicates
      $table.find(buttonSelector).off('click');
      
      // Attach new click handler
      $table.find(buttonSelector).on('click', function() {
        const itemId = $(this).attr('data-id');
        const inputName = moduleNamespace ? `${moduleNamespace}-action_click` : 'action_click';
        
        console.log(`📤 ${action.toUpperCase()} button clicked:`, {
          action: action,
          id: itemId,
          table: tableId,
          module: moduleNamespace
        });
        
        // Send to Shiny
        if (window.Shiny && window.Shiny.setInputValue) {
          Shiny.setInputValue(inputName, {
            action: action,
            id: itemId,
            timestamp: Date.now()
          }, {priority: 'event'});
        } else {
          console.warn('⚠️ Shiny not available for action:', action);
        }
      });
    });
    
    // Execute custom callback if provided
    if (customCallback && typeof customCallback === 'function') {
      customCallback.call(this, tableId, moduleNamespace);
    }
    
    console.log(`✅ Action handlers attached for ${actionTypes.length} action types on table: ${tableId}`);
  };
}

/**
 * Simplified function to attach action button handlers to existing DataTable
 * @param {string} tableId - The ID of the DataTable (without # prefix)
 * @param {Array} actions - Array of action configurations {type, inputName}
 * @param {Function} callback - Optional callback for additional processing
 */
function attachActionButtonHandlers(tableId, actions, callback = null) {
  const tableSelector = '#' + tableId;
  const $table = $(tableSelector);
  
  actions.forEach(actionConfig => {
    const { type, inputName } = actionConfig;
    const buttonSelector = `button[data-action='${type}']`;
    
    // Remove existing handlers
    $table.find(buttonSelector).off('click');
    
    // Attach new handler
    $table.find(buttonSelector).on('click', function() {
      const itemId = $(this).attr('data-id');
      
      console.log(`📤 ${type.toUpperCase()} clicked: ID ${itemId}`);
      
      if (window.Shiny && window.Shiny.setInputValue) {
        Shiny.setInputValue(inputName, {
          action: type,
          id: itemId,
          timestamp: Date.now()
        }, {priority: 'event'});
      }
    });
  });
  
  // Execute callback if provided
  if (callback) {
    callback(tableId, actions);
  }
}

/**
 * Creates a debug console logger for module events
 * @param {string} moduleName - Name of the module for logging context
 * @param {Array} eventTypes - Array of event types to log
 * @returns {Function} Logger function
 */
function createDebugConsoleLogger(moduleName, eventTypes = []) {
  return function(eventType, data = {}, source = 'unknown') {
    // Only log if this is a relevant event type
    if (eventTypes.length === 0 || eventTypes.includes(eventType)) {
      console.log(`🐛 [${moduleName}] ${eventType} from ${source}:`, data);
    }
  };
}

/**
 * Standard DataTable configuration generator for common use cases
 * @param {Object} config - Configuration object
 * @returns {Object} DataTable options object
 */
function createStandardDataTableConfig(config = {}) {
  const defaults = {
    pageLength: 25,
    searching: true,
    searchPlaceholder: "Search (regex supported):",
    emptyMessage: "No data available",
    showEntries: true,
    showPagination: true,
    actionsColumnWidth: "120px"
  };
  
  const options = Object.assign({}, defaults, config);
  
  return {
    dom: options.showEntries && options.showPagination ? 'frtip' : 'frt',
    pageLength: options.pageLength,
    searching: options.searching,
    autoWidth: false,
    language: {
      search: "",
      searchPlaceholder: options.searchPlaceholder,
      emptyTable: options.emptyMessage,
      info: "Showing _START_ to _END_ of _TOTAL_ entries",
      infoEmpty: "Showing 0 to 0 of 0 entries",
      infoFiltered: "(filtered from _MAX_ total entries)"
    },
    search: {
      regex: true,
      caseInsensitive: true,
      search: ""
    },
    columnDefs: options.actionsColumn ? [{
      targets: -1,  // Last column (Actions)
      searchable: false,
      orderable: false,
      width: options.actionsColumnWidth,
      className: "text-center"
    }] : []
  };
}

/**
 * Utility to create consistent action button HTML
 * @param {number|string} itemId - The ID of the item
 * @param {Array} actions - Array of action configurations
 * @returns {string} HTML string for action buttons
 */
function generateActionButtonsHTML(itemId, actions = [{type: 'edit', class: 'btn-primary', icon: 'pencil', title: 'Edit'}, {type: 'delete', class: 'btn-danger', icon: 'trash', title: 'Delete'}]) {
  return actions.map(action => {
    return `<button class="btn ${action.class} btn-sm me-1" data-action="${action.type}" data-id="${itemId}" title="${action.title}">
              <i class="bi bi-${action.icon}"></i>
            </button>`;
  }).join(' ');
}

/**
 * Enhanced drawCallback that includes debugging and error handling
 * @param {string} tableId - DataTable ID
 * @param {string} moduleNamespace - Shiny module namespace
 * @param {Array} actionTypes - Action types to handle
 * @param {Object} options - Additional options {debug, errorHandler, customActions}
 */
function createEnhancedDrawCallback(tableId, moduleNamespace, actionTypes = ['edit', 'delete'], options = {}) {
  const { debug = false, errorHandler = null, customActions = {} } = options;
  
  return function() {
    try {
      const tableSelector = '#' + tableId;
      const $table = $(tableSelector);
      
      if (debug) {
        console.log(`🔧 Enhanced callback executing for: ${tableId}`);
      }
      
      // Standard action handlers
      actionTypes.forEach(action => {
        const buttonSelector = `button[data-action='${action}']`;
        
        $table.find(buttonSelector).off('click').on('click', function(e) {
          e.preventDefault();
          e.stopPropagation();
          
          const itemId = $(this).attr('data-id');
          const inputName = `${moduleNamespace}-action_click`;
          
          if (debug) {
            console.log(`📤 Action triggered:`, { action, itemId, module: moduleNamespace });
          }
          
          if (window.Shiny && window.Shiny.setInputValue) {
            Shiny.setInputValue(inputName, {
              action: action,
              id: itemId,
              timestamp: Date.now()
            }, {priority: 'event'});
          } else if (debug) {
            console.warn('⚠️ Shiny not available for action:', action);
          }
        });
      });
      
      // Custom action handlers
      Object.keys(customActions).forEach(selector => {
        const handler = customActions[selector];
        $table.find(selector).off('click').on('click', handler);
      });
      
      if (debug) {
        console.log(`✅ Enhanced callback complete for: ${tableId}`);
      }
      
    } catch (error) {
      console.error(`❌ Error in drawCallback for ${tableId}:`, error);
      if (errorHandler) {
        errorHandler(error, tableId, moduleNamespace);
      }
    }
  };
}

// Export functions for global access
window.DataTableUtils = {
  createStandardDrawCallback,
  attachActionButtonHandlers,
  createDebugConsoleLogger,
  createStandardDataTableConfig,
  generateActionButtonsHTML,
  createEnhancedDrawCallback
};