#!/usr/bin/env python3
"""
Simple WebSocket test script to verify cross-browser comment synchronization
"""

import asyncio
import websockets
import json
import sys

async def test_websocket_connection():
    """Test WebSocket connection and comment event broadcasting"""
    
    uri = "ws://localhost:8000/api/v1/ws/studies"
    
    try:
        print(f"🔌 Connecting to WebSocket: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send a ping to keep connection alive
            ping_message = json.dumps({"action": "ping"})
            await websocket.send(ping_message)
            print("📤 Sent ping message")
            
            # Listen for messages
            print("🔊 Listening for WebSocket messages...")
            print("   (This will help debug cross-browser comment synchronization)")
            print("   Press Ctrl+C to stop")
            
            message_count = 0
            while message_count < 10:  # Listen for up to 10 messages
                try:
                    # Wait for a message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    message_data = json.loads(message)
                    
                    print(f"📨 Message {message_count + 1} received:")
                    print(f"   Type: {message_data.get('type', 'unknown')}")
                    
                    # Check if it's a comment event
                    if message_data.get('type', '').startswith('comment_'):
                        print(f"   🎯 COMMENT EVENT DETECTED!")
                        print(f"   Tracker ID: {message_data.get('data', {}).get('tracker_id', 'unknown')}")
                        print(f"   Comment Type: {message_data.get('data', {}).get('comment_type', 'unknown')}")
                    
                    message_count += 1
                    
                except asyncio.TimeoutError:
                    print("⏰ No messages received in 30 seconds")
                    break
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse message as JSON: {e}")
                    continue
            
            print("🔄 WebSocket test completed")
            
    except ConnectionRefusedError:
        print("❌ Connection refused - is the backend server running?")
        print("   Start backend with: cd backend && uv run python run.py")
        return False
    except Exception as e:
        print(f"❌ WebSocket connection error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 PEARL WebSocket Cross-Browser Sync Test")
    print("=" * 50)
    
    # Run the WebSocket test
    success = asyncio.run(test_websocket_connection())
    
    if success:
        print("✅ WebSocket connection test passed")
        print("\nTo test cross-browser comment sync:")
        print("1. Open PEARL in two different browsers")
        print("2. Add a comment in one browser")  
        print("3. Check if badge updates appear in the other browser")
    else:
        print("❌ WebSocket connection test failed")
        print("Check that backend is running on port 8000")
    
    sys.exit(0 if success else 1)
