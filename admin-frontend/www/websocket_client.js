// Custom JavaScript WebSocket Client for PEARL
// Handles real-time updates from FastAPI backend

class PearlWebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 5000; // 5 seconds
        this.reconnectTimer = null;
        this.isManualClose = false;
        this.messageHandlers = new Map();
        
        // WebSocket configuration
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = new URL(window.pearlApiUrl || 'http://localhost:8000');
        const wsPath = window.pearlWsPath || '/api/v1/ws/studies';
        this.wsUrl = `${wsProtocol}//${wsUrl.host}${wsPath}`;
        
        console.log('🔌 PearlWebSocketClient initialized');
    }
    
    // Initialize WebSocket connection
    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }
        
        console.log('🔌 Attempting to connect to:', this.wsUrl);
        
        try {
            this.ws = new WebSocket(this.wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error('❌ Failed to create WebSocket:', error);
            this.scheduleReconnect();
        }
    }
    
    // Set up WebSocket event handlers
    setupEventHandlers() {
        this.ws.onopen = (event) => {
            console.log('✅ WebSocket connected successfully');
            this.reconnectAttempts = 0;
            
            // Clear any pending reconnect timer
            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
                this.reconnectTimer = null;
            }
            
            // Update status in Shiny
            this.updateShinyStatus('Connected');
            
            // Send initial ping
            this.sendPing();
            
            // Set up keep-alive ping every 30 seconds
            this.setupKeepAlive();
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('📨 WebSocket message received:', data.type);
                
                // Handle different message types
                this.handleMessage(data);
                
            } catch (error) {
                console.error('❌ Error parsing WebSocket message:', error);
            }
        };
        
        this.ws.onclose = (event) => {
            console.log(`🔌 WebSocket closed. Code: ${event.code}, Reason: ${event.reason}`);
            this.updateShinyStatus('Disconnected');
            
            // Clear keep-alive timer
            if (this.keepAliveTimer) {
                clearInterval(this.keepAliveTimer);
                this.keepAliveTimer = null;
            }
            
            // Schedule reconnect if not manually closed
            if (!this.isManualClose) {
                this.scheduleReconnect();
            }
        };
        
        this.ws.onerror = (event) => {
            console.error('❌ WebSocket error occurred');
            this.updateShinyStatus('Error');
        };
    }
    
    // Handle incoming WebSocket messages
    handleMessage(data) {
        console.log('📨 WebSocket message received:', data.type, 'Data:', data);
        
        // **PHASE 2**: Route through Universal CRUD Manager if available
        if (typeof window.crudManager !== 'undefined') {
            console.log('🎯 Routing through Universal CRUD Manager:', data.type);
            
            // Convert WebSocket message to standardized CRUD event format
            const crudEvent = this.convertToCRUDEvent(data);
            
            // Let the Universal CRUD Manager handle the event
            window.crudManager.handleCRUDEvent(crudEvent);
            
            // Continue with legacy routing for backward compatibility during transition
            console.log('🔄 Also processing via legacy routing for compatibility');
        }
        
        // Determine module based on message type if not provided
        if (!data.module && data.type) {
            console.log('🔍 DEBUG: Processing message type:', JSON.stringify(data.type));
            
            // Route messages to appropriate module based on type
            if (data.type === 'studies_update' || 
                data.type.startsWith('study_')) {
                data.module = 'studies';
                console.log('📚 Studies update received:', Array.isArray(data.data) ? data.data.length : 0, 'studies');
            } else if (data.type.startsWith('reporting_effort_tracker_')) {
                // IMPORTANT: This must come BEFORE 'reporting_effort_' to avoid incorrect routing
                data.module = 'reporting_effort_tracker';
                console.log('📊 TRACKER EVENT RECEIVED:', data.type, data.data?.tracker?.id || data.data?.id || 'unknown');
                
                // Handle optimized surgical delete operations
                if (data.type === 'reporting_effort_tracker_deleted') {
                    console.log('🔪 Processing optimized tracker deletion');
                    
                    // Extract tracker ID and context from enhanced message
                    const trackerId = data.data?.tracker?.id;
                    const deleteContext = {
                        deleted_by: data.data?.deleted_by,
                        item: data.data?.item,
                        tracker: data.data?.tracker,
                        deleted_at: data.data?.deleted_at
                    };
                    
                    if (trackerId) {
                        console.log('✂️ Attempting surgical row removal for tracker:', trackerId);
                        
                        // Try surgical removal first (local optimization)
                        const surgicalSuccess = window.removeTrackerRowSurgically(trackerId, deleteContext);
                        
                        if (surgicalSuccess) {
                            console.log('✅ Surgical removal successful locally');
                            // Continue routing to ensure cross-browser synchronization
                        } else {
                            console.log('⚠️ Surgical removal failed - will use full refresh via Shiny');
                        }
                    } else {
                        console.log('⚠️ No tracker ID in delete message - using full refresh');
                    }
                    
                    // GLOBAL CROSS-BROWSER ROUTING for tracker deletion
                    // Send to global observer for cross-browser synchronization (similar to comments)
                    console.log('🌐 Routing tracker deletion to global observer for cross-browser sync');
                    this.notifyShinyGlobal(data.type, data.data, 'tracker_deletion');
                }
            } else if (data.type.startsWith('reporting_effort_')) {
                data.module = 'reporting_efforts';
                console.log('🔴 REPORTING EFFORT UPDATED EVENT RECEIVED:', data.data?.database_release_label || 'unknown');
            } else if (data.type.startsWith('database_release_')) {
                data.module = 'database_releases';
            } else if (data.type.startsWith('text_element_')) {
                data.module = 'tnfp';
                console.log('📝 TNFP EVENT RECEIVED:', data.type, data.data?.label || 'unknown');
            } else if (data.type.startsWith('package_')) {
                data.module = 'packages';
                console.log('📦 PACKAGE EVENT RECEIVED:', data.type, data.data?.package_name || 'unknown');
            } else if (data.type.startsWith('package_item_')) {
                data.module = 'packages';
                console.log('📦 PACKAGE ITEM EVENT RECEIVED:', data.type, data.data?.item_code || 'unknown');
            } else if (data.type.startsWith('user_')) {
                data.module = 'users';
                console.log('👤 USER EVENT RECEIVED:', data.type, data.data?.username || 'unknown');
            } else if (data.type.startsWith('comment_')) {
                // Route comment events to reporting effort tracker module for real-time badge updates
                data.module = 'reporting_effort_tracker';
                console.log('💬 COMMENT EVENT RECEIVED (routing to reporting_effort_tracker):', data.type, `tracker_id=${data.data?.tracker_id}`, `unresolved_count=${data.data?.unresolved_count}`);
                
                // GLOBAL CROSS-BROWSER ROUTING for comment events
                // Send to global observer for cross-browser badge synchronization
                console.log('🌐 Routing comment event to global observer for cross-browser sync');
                this.notifyShinyGlobal(data.type, data.data, 'tracker_comments');
            }
        }
        
        // Route data messages with module property
        if (data.module) {
            this.notifyShinyModule(data.type, data.data, data.module);
        }
        
        // Handle non-module-specific messages
        switch (data.type) {
            case 'pong':
                console.log('🏓 Pong received - connection alive');
                break;
            case 'error':
                console.error('❌ Server error:', data.message);
                this.showNotification(`Server error: ${data.message}`, 'error');
                break;
            default:
                if (!data.module) {
                    console.log('❓ Received message without a module for routing:', data);
                }
        }
    }
    
    // **PHASE 2**: Convert WebSocket message to standardized CRUD event format
    convertToCRUDEvent(wsMessage) {
        // Extract operation from message type (e.g., 'study_created' -> 'create')
        let operation = 'read'; // default
        let entityType = 'unknown';
        
        // Parse message type to extract entity and operation
        if (wsMessage.type) {
            const parts = wsMessage.type.split('_');
            if (parts.length >= 2) {
                // Handle compound entity types (e.g., 'reporting_effort_tracker')
                if (parts[0] === 'reporting' && parts[1] === 'effort' && parts[2] === 'tracker') {
                    entityType = 'tracker';
                    operation = this.mapOperation(parts[3] || 'update');
                } else if (parts[0] === 'reporting' && parts[1] === 'effort') {
                    entityType = 'reporting_effort';
                    operation = this.mapOperation(parts[2] || 'update');
                } else if (parts[0] === 'database' && parts[1] === 'release') {
                    entityType = 'database_release';
                    operation = this.mapOperation(parts[2] || 'update');
                } else if (parts[0] === 'text' && parts[1] === 'element') {
                    entityType = 'text_element';
                    operation = this.mapOperation(parts[2] || 'update');
                } else if (parts[0] === 'package' && parts[1] === 'item') {
                    entityType = 'package_item';
                    operation = this.mapOperation(parts[2] || 'update');
                } else {
                    // Simple entity types
                    entityType = parts[0];
                    operation = this.mapOperation(parts[1] || 'update');
                }
            }
        }
        
        // Handle special cases
        if (wsMessage.type === 'studies_update') {
            entityType = 'study';
            operation = 'read'; // bulk read operation
        }
        
        return {
            type: wsMessage.type,
            operation: operation,
            entity: {
                type: entityType,
                id: this.extractEntityId(wsMessage),
                data: wsMessage.data
            },
            context: {
                timestamp: Date.now(),
                source: 'websocket',
                originalType: wsMessage.type
            }
        };
    }
    
    // Map WebSocket operation suffixes to standard CRUD operations
    mapOperation(suffix) {
        const operationMap = {
            'created': 'create',
            'updated': 'update', 
            'deleted': 'delete',
            'update': 'read',  // bulk updates are read operations
            'read': 'read'
        };
        return operationMap[suffix] || 'read';
    }
    
    // Extract entity ID from WebSocket message data
    extractEntityId(wsMessage) {
        if (!wsMessage.data) return null;
        
        // Try different ID fields based on entity type
        return wsMessage.data.id || 
               wsMessage.data.tracker_id ||
               wsMessage.data.study_id ||
               wsMessage.data.user_id ||
               wsMessage.data.package_id ||
               null;
    }
    
    // Send message to WebSocket server
    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
            return true;
        } else {
            console.warn('⚠️ WebSocket not connected, cannot send message');
            return false;
        }
    }
    
    // Send ping to keep connection alive
    sendPing() {
        this.sendMessage({ action: 'ping' });
    }
    
    // Request data refresh
    requestRefresh() {
        this.sendMessage({ action: 'refresh' });
    }
    
    // Set up keep-alive mechanism
    setupKeepAlive() {
        if (this.keepAliveTimer) {
            clearInterval(this.keepAliveTimer);
        }
        
        this.keepAliveTimer = setInterval(() => {
            this.sendPing();
        }, 30000); // 30 seconds
    }
    
    // Schedule reconnection attempt
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('❌ Max reconnection attempts reached. Giving up.');
            this.updateShinyStatus('Failed');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectInterval * this.reconnectAttempts;
        
        console.log(`🔄 Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay/1000}s`);
        this.updateShinyStatus('Reconnecting');
        
        this.reconnectTimer = setTimeout(() => {
            console.log(`🔄 Reconnection attempt ${this.reconnectAttempts}`);
            this.connect();
        }, delay);
    }
    
    // Close WebSocket connection
    close() {
        this.isManualClose = true;
        
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        if (this.keepAliveTimer) {
            clearInterval(this.keepAliveTimer);
            this.keepAliveTimer = null;
        }
        
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        this.updateShinyStatus('Disconnected');
        console.log('🔌 WebSocket connection closed manually');
    }
    
    // Get current connection status
    getStatus() {
        if (!this.ws) return 'Disconnected';
        
        switch (this.ws.readyState) {
            case WebSocket.CONNECTING: return 'Connecting';
            case WebSocket.OPEN: return 'Connected';
            case WebSocket.CLOSING: return 'Closing';
            case WebSocket.CLOSED: return 'Disconnected';
            default: return 'Unknown';
        }
    }
    
    // Update Shiny with WebSocket status
    updateShinyStatus(status) {
        if (typeof Shiny !== 'undefined') {
            console.log('🔄 Updating Shiny status:', status);
            Shiny.setInputValue('websocket_status', status, {priority: 'event'});
        } else {
            console.log('⚠️ Shiny not available for status update');
        }
    }
    
    // Notify Shiny of WebSocket events, routing to the correct module
    notifyShiny(data) {
        if (typeof Shiny !== 'undefined' && data.module) {
            const inputId = `${data.module}-websocket_event`;
            console.log(`📤 Routing event to Shiny input: '${inputId}'`, data);
            Shiny.setInputValue(inputId, {
                type: data.type,
                data: data.data,
                timestamp: Date.now()
            }, {priority: 'event'});
        } else {
            console.log('⚠️ Shiny not available or message has no module for routing:', data);
        }
    }
    
    // Show notification in Shiny, routing to the correct module if specified
    showNotification(message, type = 'info', module = null) {
        if (typeof Shiny !== 'undefined') {
            const inputId = module ? `${module}-websocket_notification` : 'websocket_notification';
            Shiny.setInputValue(inputId, {
                message: message,
                type: type,
                timestamp: Date.now()
            }, {priority: 'event'});
        }
    }
    
    // Notify Shiny module with specific event type and data
    notifyShinyModule(eventType, data, module) {
        if (typeof Shiny !== 'undefined') {
            const inputId = `${module}-websocket_event`;
            console.log(`📨 Sending event to Shiny: ${eventType} with data:`, data);
            Shiny.setInputValue(inputId, {
                type: eventType,
                data: data,
                timestamp: Date.now()
            }, {priority: 'event'});
        } else {
            console.log('⚠️ Shiny not available for event:', eventType);
        }
    }
    
    // Notify Shiny global observer with specific event type and data (for cross-browser sync)
    notifyShinyGlobal(eventType, data, globalHandler) {
        if (typeof Shiny !== 'undefined') {
            const inputId = `${globalHandler}-websocket_event`;
            console.log(`🌍 Sending GLOBAL event to Shiny: ${eventType} with data:`, data, `-> ${inputId}`);
            Shiny.setInputValue(inputId, {
                type: eventType,
                data: data,
                timestamp: Date.now()
            }, {priority: 'event'});
        } else {
            console.log('⚠️ Shiny not available for global event:', eventType);
        }
    }
    
    // Check if WebSocket is connected
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Global WebSocket client instance
let pearlWsClient = null;

// Initialize WebSocket when page loads or immediately if DOM is ready
function initializeWebSocket() {
    console.log('🚀 Initializing PEARL WebSocket client');
    pearlWsClient = new PearlWebSocketClient();
    pearlWsClient.connect();
    
    // Update window object for debugging
    window.pearlWebSocket = {
        connect: () => pearlWsClient?.connect(),
        disconnect: () => pearlWsClient?.close(),
        refresh: () => pearlWsClient?.requestRefresh(),
        getStatus: () => pearlWsClient?.getStatus() || 'Not initialized',
        isConnected: () => pearlWsClient?.isConnected() || false
    };
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeWebSocket);
} else {
    // DOM is already ready
    initializeWebSocket();
}

// Clean up when page unloads
window.addEventListener('beforeunload', function() {
    if (pearlWsClient) {
        pearlWsClient.close();
    }
});

// =============================================================================
// SURGICAL UPDATE FUNCTIONS FOR OPTIMIZED DELETE HANDLING
// =============================================================================

/**
 * Smoothly removes a row from a DataTable by tracker ID with enhanced context and animations
 * @param {string} trackerId - The tracker ID to remove
 * @param {Object} deleteContext - Additional context from delete event
 */
window.removeTrackerRowSurgically = function(trackerId, deleteContext = {}) {
    console.log('🔪 Surgical row removal for tracker ID:', trackerId);
    console.log('📄 Delete context:', deleteContext);
    
    // Find all DataTable instances on the page
    const dataTableSelectors = [
        '#reporting_effort_tracker-tracker_table_tlf',
        '#reporting_effort_tracker-tracker_table_sdtm', 
        '#reporting_effort_tracker-tracker_table_adam'
    ];
    
    let removedCount = 0;
    let animationPromises = [];
    
    dataTableSelectors.forEach(selector => {
        const tableElement = $(selector);
        if (tableElement.length && $.fn.DataTable.isDataTable(tableElement[0])) {
            const dataTable = tableElement.DataTable();
            
            // Find row by tracker ID in data-id attributes
            const rows = dataTable.rows().nodes();
            for (let i = 0; i < rows.length; i++) {
                const row = $(rows[i]);
                const deleteBtn = row.find('button[data-action="delete"]');
                
                if (deleteBtn.length && deleteBtn.attr('data-id') === trackerId) {
                    console.log(`✂️ Found tracker ${trackerId} in table ${selector}, removing row ${i}`);
                    
                    // Enhance delete button with loading state
                    deleteBtn.addClass('btn-deleting').prop('disabled', true);
                    
                    // Add removal animation with enhanced timing
                    row.addClass('tracker-row-removing');
                    
                    // Create animation promise for better timing control
                    const animationPromise = new Promise((resolve) => {
                        setTimeout(() => {
                            row.fadeOut(400, function() {
                                // Add success indication to nearby rows
                                row.prev().addClass('tracker-surgical-success');
                                row.next().addClass('tracker-surgical-success');
                                
                                // Remove the row from DataTable
                                dataTable.row(rows[i]).remove();
                                dataTable.draw(false); // Redraw without resetting pagination
                                removedCount++;
                                
                                // Clean up success indicators
                                setTimeout(() => {
                                    $('.tracker-surgical-success').removeClass('tracker-surgical-success');
                                }, 1000);
                                
                                resolve();
                            });
                        }, 200); // Small delay for smoother animation staging
                    });
                    
                    animationPromises.push(animationPromise);
                    break;
                }
            }
        }
    });
    
    // Wait for all animations to complete before showing notifications
    Promise.all(animationPromises).then(() => {
        if (removedCount > 0) {
            console.log(`✅ Successfully removed ${removedCount} tracker row(s) with enhanced animations`);
            
            // Show enhanced user-friendly notification with context
            if (deleteContext.deleted_by || deleteContext.item) {
                showDeleteNotification(deleteContext);
            }
            
            // Show subtle success feedback
            showSurgicalSuccessIndicator(removedCount);
        }
    });
    
    if (removedCount === 0) {
        console.log('⚠️ No tracker row found with ID:', trackerId);
        // Fall back to full table refresh if surgical removal failed
        console.log('🔄 Falling back to full table refresh');
        if (window.Shiny) {
            Shiny.setInputValue('reporting_effort_tracker-surgical_removal_fallback', {
                tracker_id: trackerId,
                timestamp: Date.now()
            }, {priority: 'event'});
        }
    }
    
    return removedCount > 0;
};

/**
 * Show subtle success indicator for surgical updates
 * @param {number} count - Number of rows successfully removed
 */
function showSurgicalSuccessIndicator(count) {
    // Create temporary success indicator
    const indicator = document.createElement('div');
    indicator.className = 'position-fixed';
    indicator.style.cssText = `
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #4caf50, #66bb6a);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
        z-index: 9999;
        animation: surgicalSuccess 2s ease-out forwards;
        opacity: 0;
        transform: translateX(100%);
    `;
    indicator.innerHTML = `
        <i class="fa fa-check-circle me-2"></i>
        ${count} tracker${count > 1 ? 's' : ''} updated smoothly
    `;
    
    document.body.appendChild(indicator);
    
    // Animate in
    setTimeout(() => {
        indicator.style.opacity = '1';
        indicator.style.transform = 'translateX(0)';
    }, 10);
    
    // Remove after animation
    setTimeout(() => {
        if (indicator.parentNode) {
            indicator.parentNode.removeChild(indicator);
        }
    }, 2500);
}

/**
 * Show enhanced user notification for tracker deletion with user context
 * @param {Object} deleteContext - Context from enhanced WebSocket delete message
 */
function showDeleteNotification(deleteContext) {
    const { deleted_by, item, tracker } = deleteContext;
    
    let message = 'Tracker deleted';
    
    if (item && item.item_code) {
        message = `Tracker for ${item.item_code} deleted`;
    }
    
    if (deleted_by && deleted_by.username) {
        if (deleted_by.username !== getCurrentUsername()) {
            message += ` by ${deleted_by.username}`;
        }
    }
    
    // Use Shiny notification system with enhanced styling
    if (typeof Shiny !== 'undefined') {
        Shiny.setInputValue('reporting_effort_tracker-delete_notification', {
            message: message,
            type: 'surgical_delete',
            context: deleteContext,
            timestamp: Date.now()
        }, {priority: 'event'});
    }
    
    console.log('📢 Delete notification:', message);
}

/**
 * Get current username (placeholder - would integrate with auth system)
 * @returns {string} Current user's username
 */
function getCurrentUsername() {
    // This would integrate with your authentication system
    // For now, return a placeholder
    return window.currentUser?.username || 'current_user';
}

/**
 * Bulk refresh tracker data using optimized bulk endpoint
 * @param {number} reportingEffortId - The reporting effort ID to refresh
 */
window.refreshTrackersOptimized = function(reportingEffortId) {
    console.log('⚡ Optimized tracker refresh for effort:', reportingEffortId);
    
    if (typeof Shiny !== 'undefined') {
        Shiny.setInputValue('reporting_effort_tracker-bulk_refresh_request', {
            effort_id: reportingEffortId,
            timestamp: Date.now()
        }, {priority: 'event'});
    }
};

/**
 * Add CSS animations for smooth row removal and UX enhancements
 */
function addTrackerRowAnimations() {
    if (!document.getElementById('tracker-row-animations')) {
        const style = document.createElement('style');
        style.id = 'tracker-row-animations';
        style.textContent = `
            /* Smooth row removal animations */
            .tracker-row-removing {
                background: linear-gradient(90deg, #ffebee 0%, #ffcdd2 50%, #ffebee 100%) !important;
                background-size: 200% 100%;
                animation: trackerRowRemoving 0.8s ease-in-out;
                transition: all 0.3s ease-out;
            }
            
            .tracker-row-removing td {
                border-color: #ffcdd2 !important;
                color: #d32f2f !important;
            }
            
            /* Notification enhancements */
            .tracker-delete-notification {
                border-left: 4px solid #ff7043;
                background-color: #fff3e0;
                box-shadow: 0 2px 8px rgba(255, 112, 67, 0.2);
                border-radius: 4px;
            }
            
            /* Delete action feedback */
            .tracker-delete-animation {
                animation: trackerDeletePulse 0.6s ease-in-out;
            }
            
            /* Success indicators for surgical updates */
            .tracker-surgical-success {
                animation: surgicalSuccess 1s ease-out;
            }
            
            /* DataTable row hover enhancements */
            .dataTables_wrapper table.dataTable tbody tr:hover {
                background-color: #f8f9fa !important;
                transition: background-color 0.2s ease;
            }
            
            /* Button loading states */
            .btn-deleting {
                position: relative;
                color: transparent !important;
            }
            
            .btn-deleting::after {
                content: '';
                position: absolute;
                width: 16px;
                height: 16px;
                top: 50%;
                left: 50%;
                margin-left: -8px;
                margin-top: -8px;
                border: 2px solid #ffffff;
                border-radius: 50%;
                border-top-color: transparent;
                animation: btnSpin 0.8s linear infinite;
            }
            
            /* Enhanced loading spinner */
            @keyframes btnSpin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* Row removal animation */
            @keyframes trackerRowRemoving {
                0% { 
                    background-position: 0% 50%;
                    opacity: 1;
                    transform: scale(1);
                }
                50% { 
                    background-position: 100% 50%;
                    opacity: 0.8;
                    transform: scale(0.98);
                }
                100% { 
                    background-position: 200% 50%;
                    opacity: 0.6;
                    transform: scale(0.95);
                }
            }
            
            /* Delete confirmation pulse */
            @keyframes trackerDeletePulse {
                0% { opacity: 1; transform: scale(1); }
                25% { opacity: 0.8; transform: scale(1.02); }
                50% { opacity: 0.6; transform: scale(0.98); }
                75% { opacity: 0.8; transform: scale(1.01); }
                100% { opacity: 1; transform: scale(1); }
            }
            
            /* Success feedback animation */
            @keyframes surgicalSuccess {
                0% { 
                    background-color: #e8f5e8;
                    transform: scale(1);
                }
                50% { 
                    background-color: #c8e6c9;
                    transform: scale(1.01);
                }
                100% { 
                    background-color: transparent;
                    transform: scale(1);
                }
            }
            
            /* Toast notification enhancements */
            .shiny-notification {
                border-radius: 6px !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
                animation: notificationSlideIn 0.3s ease-out !important;
            }
            
            @keyframes notificationSlideIn {
                from {
                    opacity: 0;
                    transform: translateX(100%);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            /* Multi-user context indicators */
            .delete-by-other-user {
                border-left: 4px solid #2196f3 !important;
                background-color: #e3f2fd !important;
            }
            
            .delete-by-current-user {
                border-left: 4px solid #4caf50 !important;
                background-color: #e8f5e8 !important;
            }
        `;
        document.head.appendChild(style);
    }
}

// Add animations when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addTrackerRowAnimations);
} else {
    addTrackerRowAnimations();
}

// =============================================================================
// WEBSOCKET DEBUGGING AND TESTING FUNCTIONS
// =============================================================================

// Quick WebSocket connection check
window.checkWebSocketStatus = function() {
    console.log('🔍 Quick WebSocket Status Check');
    console.log('-'.repeat(40));
    
    if (pearlWsClient) {
        console.log('✅ WebSocket client exists');
        console.log('   Status:', pearlWsClient.getStatus());
        console.log('   Connected:', pearlWsClient.isConnected());
        console.log('   URL:', pearlWsClient.wsUrl || 'unknown');
        console.log('   Active connections would be handled by backend');
        
        if (pearlWsClient.isConnected()) {
            console.log('   ✅ Ready for cross-browser synchronization');
        } else {
            console.log('   ❌ Not connected - cross-browser sync won\'t work');
            console.log('   Try: window.pearlWebSocket.connect()');
        }
    } else {
        console.log('❌ WebSocket client not found');
        console.log('   WebSocket may not be initialized properly');
    }
};

// Test WebSocket Cross-Browser Synchronization
window.testWebSocketCrossBrowserSync = function() {
    console.log('🧪 PEARL WebSocket Cross-Browser Sync Test Starting...');
    console.log('='.repeat(60));
    
    // Check if existing WebSocket is connected
    if (pearlWsClient) {
        console.log('🔌 Existing WebSocket Status:', pearlWsClient.getStatus());
        console.log('🔌 Is Connected:', pearlWsClient.isConnected());
        
        if (pearlWsClient.isConnected()) {
            console.log('✅ WebSocket is already connected and ready');
            
            // Test message sending
            console.log('📤 Testing WebSocket message sending...');
            
            // Request a refresh to test communication
            setTimeout(() => {
                if (pearlWsClient.isConnected()) {
                    pearlWsClient.sendMessage({
                        action: 'ping',
                        test: 'cross-browser-sync-test',
                        timestamp: Date.now()
                    });
                    console.log('📤 Test ping message sent');
                }
            }, 1000);
            
        } else {
            console.log('🔄 WebSocket not connected, attempting to connect...');
            pearlWsClient.connect();
        }
    } else {
        console.log('❌ No WebSocket client found - WebSocket may not be initialized');
        return false;
    }
    
    // Monitor WebSocket messages for next 30 seconds
    console.log('🔊 Monitoring WebSocket messages for 30 seconds...');
    console.log('   Now add a comment in another browser tab/window');
    console.log('   We should see comment events appear here');
    
    let messageCount = 0;
    let commentEventCount = 0;
    
    // Create a temporary message handler to monitor events
    const originalHandleMessage = pearlWsClient ? pearlWsClient.handleMessage : null;
    
    if (originalHandleMessage) {
        pearlWsClient.handleMessage = function(data) {
            messageCount++;
            console.log(`📨 WebSocket Message #${messageCount}:`, data.type);
            
            // Detect comment events
            if (data.type && data.type.startsWith('comment_')) {
                commentEventCount++;
                console.log(`🎯 COMMENT EVENT #${commentEventCount} DETECTED!`);
                console.log(`   Type: ${data.type}`);
                console.log(`   Tracker ID: ${data.data?.tracker_id || 'unknown'}`);
                console.log(`   Comment Type: ${data.data?.comment_type || 'unknown'}`);
                console.log('   ✅ Cross-browser sync should work!');
            }
            
            // Call original handler
            originalHandleMessage.call(this, data);
        };
        
        // Restore original handler after 30 seconds
        setTimeout(() => {
            if (pearlWsClient) {
                pearlWsClient.handleMessage = originalHandleMessage;
            }
            
            console.log('⏰ WebSocket monitoring completed');
            console.log(`📊 Results:`);
            console.log(`   Total messages received: ${messageCount}`);
            console.log(`   Comment events detected: ${commentEventCount}`);
            
            if (commentEventCount > 0) {
                console.log('✅ WebSocket comment events are working!');
                console.log('   Cross-browser synchronization should be functional');
            } else if (messageCount > 0) {
                console.log('⚠️  WebSocket is receiving messages but no comment events detected');
                console.log('   Try adding a comment in another browser window');
            } else {
                console.log('❌ No WebSocket messages received');
                console.log('   WebSocket connection may have issues');
            }
            
        }, 30000);
        
    } else {
        console.log('❌ Could not monitor WebSocket messages');
    }
    
    // Instructions for user
    console.log('');
    console.log('🧪 TEST INSTRUCTIONS:');
    console.log('1. Keep this console open');
    console.log('2. Open PEARL in another browser tab/window');
    console.log('3. Add a comment to any tracker item');
    console.log('4. Watch this console for comment events');
    console.log('5. Check if badges update in BOTH browser windows');
    console.log('');
    
    return true;
};

// Force WebSocket reconnection
window.reconnectWebSocket = function() {
    console.log('🔄 Forcing WebSocket reconnection...');
    
    if (pearlWsClient) {
        pearlWsClient.close();
        setTimeout(() => {
            pearlWsClient.connect();
            console.log('🔌 WebSocket reconnection initiated');
        }, 1000);
    } else {
        console.log('❌ No WebSocket client to reconnect');
    }
};

// Show available debug functions
window.showWebSocketDebugHelp = function() {
    console.log('🛠️  PEARL WebSocket Debug Functions Available:');
    console.log('   window.checkWebSocketStatus() - Quick status check');
    console.log('   window.testWebSocketCrossBrowserSync() - Full 30-second test');
    console.log('   window.reconnectWebSocket() - Force reconnection');
    console.log('   window.showWebSocketDebugHelp() - Show this help');
    console.log('');
    console.log('💡 For cross-browser testing:');
    console.log('   1. Run window.testWebSocketCrossBrowserSync()');
    console.log('   2. Open second browser window');
    console.log('   3. Add comment in second window');
    console.log('   4. Watch console for events');
};

// Auto-show help when page loads
console.log('🧪 PEARL WebSocket Debug Tools Loaded!');
console.log('   Type: window.showWebSocketDebugHelp() for available functions');