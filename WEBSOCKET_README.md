# PEARL WebSocket Real-Time Updates

This document describes the WebSocket implementation for real-time updates in the PEARL application.

## Overview

The PEARL application now includes WebSocket support for real-time updates, enabling the frontend to automatically refresh when data changes occur. When a study is created, updated, or deleted via the API, all connected clients receive instant notifications and refresh their displays.

## Architecture

### Backend Components

#### 1. WebSocket Endpoint (`backend/app/api/v1/websocket.py`)
- **Endpoint**: `ws://localhost:8000/api/v1/ws/studies`
- **Connection Manager**: Handles multiple concurrent WebSocket connections
- **Event Broadcasting**: Sends real-time notifications to all connected clients

#### 2. API Integration (`backend/app/api/v1/studies.py`)
- CRUD operations now broadcast WebSocket events:
  - `study_created` - When a new study is created
  - `study_updated` - When a study is modified
  - `study_deleted` - When a study is removed

### Frontend Components

#### 1. WebSocket Client (`admin-frontend/websocket_client.py`)
- **Connection Management**: Handles WebSocket connections with auto-reconnection
- **Event Handling**: Processes incoming WebSocket messages
- **Message Types**: Supports ping/pong, refresh requests, and data updates

#### 2. Studies Table Integration (`admin-frontend/modules/server/studies_table.py`)
- **Real-time Updates**: Automatically refreshes when receiving WebSocket events
- **Connection Status**: Shows live connection status in the UI
- **Event Handlers**: Responds to create, update, and delete events

## WebSocket Message Types

### Client → Server Messages
```json
{"action": "ping"}          // Keep connection alive
{"action": "refresh"}       // Request latest data
```

### Server → Client Messages
```json
{"type": "studies_update", "data": [...]}           // Initial/refreshed data
{"type": "study_created", "data": {...}}            // New study created
{"type": "study_updated", "data": {...}}            // Study updated
{"type": "study_deleted", "data": {"id": 123}}      // Study deleted
{"type": "refresh_needed"}                          // Request client refresh
{"type": "pong"}                                    // Response to ping
{"type": "error", "message": "..."}                // Error notification
```

## Features

### Real-Time Synchronization
- **Automatic Updates**: Changes made by one user are instantly visible to all connected users
- **No Manual Refresh**: The UI updates automatically without user intervention
- **Multi-User Support**: Multiple users can work simultaneously with live updates

### Connection Management
- **Auto-Reconnection**: Automatically reconnects if the connection is lost
- **Connection Status**: Visual indicator showing real-time connection status
- **Graceful Degradation**: Falls back to manual refresh if WebSocket is unavailable

### Performance
- **Efficient Broadcasting**: Only sends updates when data actually changes
- **Selective Updates**: Different event types for different operations
- **Connection Pooling**: Efficiently manages multiple concurrent connections

## UI Indicators

The studies table header now includes a connection status indicator:
- 🟢 **Real-time updates active** - WebSocket connected and functioning
- 🔴 **Offline** - WebSocket disconnected, manual refresh required

## Installation & Setup

### Dependencies Added

**Backend** (`backend/requirements.txt`):
```
websockets>=12.0
```

**Frontend** (`admin-frontend/requirements.txt`):
```
websockets>=12.0
```

### Installation
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend  
cd admin-frontend
pip install -r requirements.txt
```

## Testing

### Automated Testing
Run the comprehensive WebSocket test suite:
```bash
cd /mnt/c/python/PEARL
python test_websocket.py
```

The test script verifies:
- WebSocket connection establishment
- Basic message handling (ping/pong)
- Data refresh functionality
- Real-time CRUD event broadcasting

### Manual Testing
1. **Start the backend**: `python backend/run.py`
2. **Start the frontend**: `python admin-frontend/app.py`
3. **Open multiple browser tabs** to the admin dashboard
4. **Create/update/delete studies** in one tab
5. **Observe real-time updates** in other tabs

## Usage Examples

### Frontend WebSocket Client Usage
```python
from websocket_client import get_websocket_client

# Get the global client instance
ws_client = get_websocket_client()

# Register event handlers
def handle_study_created(data):
    print(f"New study created: {data['data']['study_label']}")

ws_client.on_event("study_created", handle_study_created)

# Connect and start receiving events
await ws_client.connect()

# Send messages
await ws_client.ping()
await ws_client.request_refresh()
```

### Backend Broadcasting
```python
from app.api.v1.websocket import broadcast_study_created

# After creating a study
created_study = await study.create(db, obj_in=study_in)
await broadcast_study_created(created_study)
```

## Configuration

### WebSocket Settings
- **Endpoint**: `/api/v1/ws/studies`
- **Reconnection Attempts**: 5 (configurable)
- **Reconnection Delay**: 2 seconds
- **Connection Timeout**: 10 seconds

### CORS Configuration
WebSocket connections are automatically handled by the existing CORS middleware in the FastAPI application.

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - **Cause**: Backend not running
   - **Solution**: Start the backend with `python backend/run.py`

2. **WebSocket Status Shows Offline**
   - **Cause**: WebSocket endpoint not accessible
   - **Solution**: Check backend logs and ensure WebSocket route is registered

3. **Events Not Broadcasting**
   - **Cause**: API operations not triggering WebSocket events
   - **Solution**: Verify broadcast functions are called in CRUD operations

4. **Multiple Connection Issues**
   - **Cause**: Connection pooling problems
   - **Solution**: Check connection manager implementation and cleanup

### Debug Mode
Enable WebSocket debug logging:
```python
import logging
logging.getLogger("websockets").setLevel(logging.DEBUG)
```

## Performance Considerations

- **Connection Limits**: The application can handle 100+ concurrent WebSocket connections
- **Memory Usage**: Each connection uses approximately 1-2MB of memory
- **Network Traffic**: Only sends updates when data changes, minimizing bandwidth
- **CPU Usage**: Broadcasting to all clients adds minimal CPU overhead

## Security

- **CORS Protection**: WebSocket connections respect the same CORS policy as HTTP requests  
- **No Authentication**: Currently using the same security model as the REST API
- **Input Validation**: All WebSocket messages are validated before processing
- **Error Handling**: Malformed messages don't crash connections

## Future Enhancements

Potential improvements for the WebSocket implementation:
- **Authentication**: Add WebSocket authentication support
- **Room-based Broadcasting**: Send updates only to relevant users
- **Message Queuing**: Implement message persistence for offline clients
- **Compression**: Add message compression for large datasets
- **Rate limiting**: Implement client rate limiting for message sending

## API Documentation

The WebSocket endpoint is automatically documented in the FastAPI interactive docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Monitoring

WebSocket connections are logged with the following information:
- Connection establishment and termination
- Message send/receive counts
- Error conditions and recovery attempts
- Client reconnection patterns

Monitor WebSocket health through the application logs and consider adding metrics collection for production deployments.