/**
 * PEARL WebSocket Cross-Browser Synchronization Test
 * 
 * Paste this into your browser's developer console while PEARL is running
 * to test WebSocket connectivity and cross-browser comment synchronization
 */

// Test WebSocket Connection and Comment Event Broadcasting
window.testWebSocketCrossBrowserSync = function() {
    console.log('🧪 PEARL WebSocket Cross-Browser Sync Test Starting...');
    console.log('=' * 60);
    
    // Check if existing WebSocket is connected
    if (window.pearlWebSocket) {
        console.log('🔌 Existing WebSocket Status:', window.pearlWebSocket.getStatus());
        console.log('🔌 Is Connected:', window.pearlWebSocket.isConnected());
        
        if (window.pearlWebSocket.isConnected()) {
            console.log('✅ WebSocket is already connected and ready');
            
            // Test message sending
            console.log('📤 Testing WebSocket message sending...');
            window.pearlWebSocket.connect();
            
            // Request a refresh to test communication
            setTimeout(() => {
                if (window.pearlWebSocket.isConnected()) {
                    window.pearlWebSocket.sendMessage({
                        action: 'ping',
                        test: 'cross-browser-sync-test',
                        timestamp: Date.now()
                    });
                    console.log('📤 Test ping message sent');
                }
            }, 1000);
            
        } else {
            console.log('🔄 WebSocket not connected, attempting to connect...');
            window.pearlWebSocket.connect();
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
    const originalHandleMessage = window.pearlWebSocket ? window.pearlWebSocket.handleMessage : null;
    
    if (originalHandleMessage) {
        window.pearlWebSocket.handleMessage = function(data) {
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
            if (window.pearlWebSocket) {
                window.pearlWebSocket.handleMessage = originalHandleMessage;
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

// Quick WebSocket connection check
window.checkWebSocketStatus = function() {
    console.log('🔍 Quick WebSocket Status Check');
    console.log('-'.repeat(40));
    
    if (window.pearlWebSocket) {
        console.log('✅ WebSocket client exists');
        console.log('   Status:', window.pearlWebSocket.getStatus());
        console.log('   Connected:', window.pearlWebSocket.isConnected());
        
        if (window.pearlWebSocket.isConnected()) {
            console.log('   URL:', window.pearlWebSocket.wsUrl || 'unknown');
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

// Auto-run quick check
window.checkWebSocketStatus();

console.log('');
console.log('🧪 WebSocket Test Functions Available:');
console.log('   window.checkWebSocketStatus() - Quick status check');
console.log('   window.testWebSocketCrossBrowserSync() - Full 30-second test');
console.log('');
