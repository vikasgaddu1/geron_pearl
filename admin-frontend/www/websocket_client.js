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
        switch (data.type) {
            case 'studies_update':
                console.log('📊 Studies update received:', data.data.length, 'studies');
                this.notifyShiny('studies_update', data.data);
                break;
                
            case 'study_created':
                console.log('➕ Study created:', data.data.study_label);
                this.notifyShiny('study_created', data.data);
                this.showNotification('New study created: ' + data.data.study_label, 'success');
                break;
                
            case 'study_updated':
                console.log('✏️ Study updated:', data.data.study_label);
                this.notifyShiny('study_updated', data.data);
                this.showNotification('Study updated: ' + data.data.study_label, 'info');
                break;
                
            case 'study_deleted':
                console.log('🗑️ Study deleted, ID:', data.data.id);
                this.notifyShiny('study_deleted', data.data);
                this.showNotification('Study deleted (ID: ' + data.data.id + ')', 'warning');
                break;
                
            case 'refresh_needed':
                console.log('🔄 Refresh needed signal received');
                this.requestRefresh();
                break;
                
            case 'database_release_created':
                console.log('➕ Database release created:', data.data.database_release_label);
                this.notifyShiny('database_release_created', data.data);
                this.showNotification('New database release created: ' + data.data.database_release_label, 'success');
                break;
                
            case 'database_release_updated':
                console.log('✏️ Database release updated:', data.data.database_release_label);
                this.notifyShiny('database_release_updated', data.data);
                this.showNotification('Database release updated: ' + data.data.database_release_label, 'info');
                break;
                
            case 'database_release_deleted':
                console.log('🗑️ Database release deleted, ID:', data.data.id);
                this.notifyShiny('database_release_deleted', data.data);
                this.showNotification('Database release deleted (ID: ' + data.data.id + ')', 'warning');
                break;
                
            case 'pong':
                console.log('🏓 Pong received - connection alive');
                break;
                
            case 'error':
                console.error('❌ Server error:', data.message);
                this.showNotification(`Server error: ${data.message}`, 'error');
                break;
                
            default:
                console.log('❓ Unknown message type:', data.type);
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
    
    // Notify Shiny of WebSocket events
    notifyShiny(eventType, data) {
        if (typeof Shiny !== 'undefined') {
            console.log('📤 Sending event to Shiny:', eventType, 'with data:', data);
            
            // Send to studies module for studies-related events
            if (eventType.startsWith('study') || eventType === 'studies_update') {
                Shiny.setInputValue('studies-websocket_event', {
                    type: eventType,
                    data: data,
                    timestamp: Date.now()
                });
            }
            
            // Send to database_releases module for database release events and studies updates (for reference data)
            if (eventType.startsWith('database_release') || eventType === 'studies_update') {
                Shiny.setInputValue('database_releases-websocket_event', {
                    type: eventType,
                    data: data,
                    timestamp: Date.now()
                });
            }
        } else {
            console.log('⚠️ Shiny not available for event:', eventType);
        }
    }
    
    // Show notification in Shiny
    showNotification(message, type = 'info') {
        if (typeof Shiny !== 'undefined') {
            Shiny.setInputValue('studies-websocket_notification', {
                message: message,
                type: type,
                timestamp: Date.now()
            });
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