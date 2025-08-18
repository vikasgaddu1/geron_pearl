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
        
        // Determine module based on message type if not provided
        if (!data.module && data.type) {
            console.log('🔍 DEBUG: Processing message type:', JSON.stringify(data.type));
            
            // Route messages to appropriate module based on type
            if (data.type === 'studies_update' || 
                data.type.startsWith('study_')) {
                data.module = 'studies';
                console.log('📚 Studies update received:', Array.isArray(data.data) ? data.data.length : 0, 'studies');
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
            } else if (data.type.startsWith('reporting_effort_tracker_')) {
                data.module = 'reporting_effort_tracker';
                console.log('📊 TRACKER EVENT RECEIVED:', data.type, data.data?.id || 'unknown');
            } else if (data.type.startsWith('comment_')) {
                // Route comment events to reporting effort tracker module for real-time badge updates
                data.module = 'reporting_effort_tracker';
                console.log('💬 COMMENT EVENT RECEIVED (routing to reporting_effort_tracker):', data.type, `tracker_id=${data.data?.tracker_id}`, `unresolved_count=${data.data?.unresolved_count}`);
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