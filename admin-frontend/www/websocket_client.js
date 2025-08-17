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
            } else if (data.type.startsWith('comment_')) {
                data.module = 'tracker_comments';
                console.log('💬 COMMENT EVENT RECEIVED:', data.type, `tracker_id=${data.data?.tracker_id}`, data.data?.comment_text?.substring(0, 50) || 'unknown');
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