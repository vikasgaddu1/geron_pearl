#!/usr/bin/env python3
"""
Test WebSocket connection management improvements.
This script tests the stale connection cleanup functionality.
"""

import asyncio
import websockets
import json
import time

async def test_websocket_connection():
    """Test WebSocket connection and simulate disconnection."""
    uri = "ws://localhost:8000/api/v1/ws/studies"
    
    print("🔌 Connecting to WebSocket...")
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully")
            
            # Send ping message
            ping_message = {"action": "ping"}
            await websocket.send(json.dumps(ping_message))
            print("📤 Sent ping message")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Received: {data}")
            
            # Simulate keeping connection open for a bit
            print("⏳ Keeping connection open for 5 seconds...")
            await asyncio.sleep(5)
            
            # Close connection gracefully
            print("🔌 Closing connection...")
            
    except websockets.exceptions.ConnectionClosed:
        print("🔌 Connection closed by server")
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_multiple_connections():
    """Test multiple connections to verify connection management."""
    uri = "ws://localhost:8000/api/v1/ws/studies"
    
    print("🔌 Testing multiple connections...")
    
    async def create_connection(conn_id):
        try:
            async with websockets.connect(uri) as websocket:
                print(f"✅ Connection {conn_id} established")
                
                # Send ping
                await websocket.send(json.dumps({"action": "ping"}))
                response = await websocket.recv()
                print(f"📥 Connection {conn_id} received: {json.loads(response)['type']}")
                
                # Keep connection open for different durations
                await asyncio.sleep(conn_id * 2)
                print(f"🔌 Connection {conn_id} closing...")
                
        except Exception as e:
            print(f"❌ Connection {conn_id} error: {e}")
    
    # Create 3 connections simultaneously
    tasks = [create_connection(i) for i in range(1, 4)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("🧪 Testing WebSocket connection management improvements...")
    print("📋 Make sure the backend server is running on localhost:8000")
    
    # Test single connection
    asyncio.run(test_websocket_connection())
    
    print("\n" + "="*50 + "\n")
    
    # Test multiple connections
    asyncio.run(test_multiple_connections())
    
    print("\n✅ WebSocket connection tests completed")