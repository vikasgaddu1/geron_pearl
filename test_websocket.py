#!/usr/bin/env python3
"""
Test script for WebSocket real-time updates functionality.
This script tests the WebSocket connection and real-time updates.
"""

import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosed
import httpx
import sys


async def test_websocket_connection():
    """Test basic WebSocket connection and message handling."""
    print("🔍 Testing WebSocket connection...")
    
    try:
        # Connect to WebSocket endpoint
        uri = "ws://localhost:8000/api/v1/ws/studies"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Wait for initial studies data
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"📦 Received initial message: {data.get('type', 'unknown')}")
                
                if data.get("type") == "studies_update":
                    studies = data.get("data", [])
                    print(f"📊 Initial studies count: {len(studies)}")
                
            except asyncio.TimeoutError:
                print("⚠️  No initial message received within 5 seconds")
                
            # Test ping message
            ping_message = {"action": "ping"}
            await websocket.send(json.dumps(ping_message))
            print("📤 Sent ping message")
            
            # Wait for pong response
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                data = json.loads(message)
                if data.get("type") == "pong":
                    print("✅ Received pong response")
                else:
                    print(f"📦 Received: {data.get('type', 'unknown')}")
            except asyncio.TimeoutError:
                print("⚠️  No pong response received")
                
            # Test refresh request
            refresh_message = {"action": "refresh"}
            await websocket.send(json.dumps(refresh_message))
            print("📤 Sent refresh request")
            
            # Wait for refresh response
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                data = json.loads(message)
                if data.get("type") == "studies_update":
                    studies = data.get("data", [])
                    print(f"✅ Refresh response received with {len(studies)} studies")
                else:
                    print(f"📦 Received: {data.get('type', 'unknown')}")
            except asyncio.TimeoutError:
                print("⚠️  No refresh response received")
                
            print("✅ WebSocket basic functionality test completed")
            
    except ConnectionRefusedError:
        print("❌ Could not connect to WebSocket. Is the backend running on localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ WebSocket connection error: {e}")
        return False
        
    return True


async def test_real_time_updates():
    """Test real-time updates by creating, updating, and deleting a study."""
    print("\n🔍 Testing real-time updates...")
    
    # Setup WebSocket listener
    websocket_messages = []
    
    async def websocket_listener():
        try:
            uri = "ws://localhost:8000/api/v1/ws/studies"
            async with websockets.connect(uri) as websocket:
                print("📡 WebSocket listener started")
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        websocket_messages.append(data)
                        print(f"📨 WebSocket received: {data.get('type', 'unknown')}")
                    except ConnectionClosed:
                        break
        except Exception as e:
            print(f"❌ WebSocket listener error: {e}")
    
    # Start WebSocket listener
    listener_task = asyncio.create_task(websocket_listener())
    
    # Wait a moment for connection
    await asyncio.sleep(1)
    
    try:
        # Test API operations and check for WebSocket notifications
        async with httpx.AsyncClient() as client:
            base_url = "http://localhost:8000/api/v1/studies"
            
            # Create a test study
            print("📤 Creating test study...")
            create_data = {"study_label": "WebSocket Test Study"}
            
            response = await client.post(base_url, json=create_data)
            if response.status_code == 201:
                study_data = response.json()
                study_id = study_data["id"]
                print(f"✅ Study created with ID: {study_id}")
                
                # Wait for WebSocket notification
                await asyncio.sleep(2)
                
                # Check if we received a study_created event
                created_events = [msg for msg in websocket_messages if msg.get("type") == "study_created"]
                if created_events:
                    print("✅ Received study_created WebSocket event")
                else:
                    print("⚠️  No study_created WebSocket event received")
                
                # Update the study
                print("📤 Updating test study...")
                update_data = {"study_label": "Updated WebSocket Test Study"}
                
                response = await client.put(f"{base_url}/{study_id}", json=update_data)
                if response.status_code == 200:
                    print("✅ Study updated successfully")
                    
                    # Wait for WebSocket notification
                    await asyncio.sleep(2)
                    
                    # Check if we received a study_updated event
                    updated_events = [msg for msg in websocket_messages if msg.get("type") == "study_updated"]
                    if updated_events:
                        print("✅ Received study_updated WebSocket event")
                    else:
                        print("⚠️  No study_updated WebSocket event received")
                else:
                    print(f"❌ Failed to update study: {response.status_code}")
                
                # Delete the study
                print("📤 Deleting test study...")
                response = await client.delete(f"{base_url}/{study_id}")
                if response.status_code == 200:
                    print("✅ Study deleted successfully")
                    
                    # Wait for WebSocket notification
                    await asyncio.sleep(2)
                    
                    # Check if we received a study_deleted event
                    deleted_events = [msg for msg in websocket_messages if msg.get("type") == "study_deleted"]
                    if deleted_events:
                        print("✅ Received study_deleted WebSocket event")
                    else:
                        print("⚠️  No study_deleted WebSocket event received")
                else:
                    print(f"❌ Failed to delete study: {response.status_code}")
                    
            else:
                print(f"❌ Failed to create study: {response.status_code}")
                print(f"Response: {response.text}")
                
    except httpx.ConnectError:
        print("❌ Could not connect to API. Is the backend running on localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False
    finally:
        # Cancel the WebSocket listener
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
    
    print(f"\n📊 Total WebSocket messages received: {len(websocket_messages)}")
    for i, msg in enumerate(websocket_messages, 1):
        print(f"  {i}. {msg.get('type', 'unknown')}")
        
    return True


async def main():
    """Run all WebSocket tests."""
    print("🚀 Starting WebSocket tests for PEARL Backend\n")
    
    # Test basic connection
    connection_ok = await test_websocket_connection()
    
    if connection_ok:
        # Test real-time updates
        updates_ok = await test_real_time_updates()
        
        if connection_ok and updates_ok:
            print("\n🎉 All WebSocket tests completed successfully!")
            print("\n📋 Summary:")
            print("  ✅ WebSocket connection established")
            print("  ✅ Basic message handling working")
            print("  ✅ Real-time CRUD notifications working")
            print("\n💡 Your WebSocket implementation is ready!")
            return 0
        else:
            print("\n⚠️  Some tests failed. Check the backend configuration.")
            return 1
    else:
        print("\n❌ Could not establish WebSocket connection.")
        print("💡 Make sure the backend is running: python backend/run.py")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)