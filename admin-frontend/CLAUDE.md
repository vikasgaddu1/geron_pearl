# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **📖 For comprehensive project documentation, features, installation, and usage instructions, see [README.md](README.md)**

## Project Overview

This is the R Shiny admin frontend for the PEARL research data management system. It provides a modern, real-time CRUD interface for managing studies that communicates with the FastAPI backend via REST API and WebSocket connections.

**Key Features**: Real-time WebSocket updates, modern Bootstrap 5 UI, multi-user synchronization
**Technology Stack**: R Shiny + bslib + WebSocket (JavaScript/R dual clients)

## Architecture

> **📋 See [README.md - Architecture](README.md#architecture) for detailed file structure and module descriptions**

### Modern R Shiny Stack
- **Framework**: R Shiny with modern bslib Bootstrap 5 theming
- **UI Library**: bslib + bsicons for contemporary design
- **HTTP Client**: httr for REST API communication  
- **Real-time**: WebSocket integration (JavaScript primary, R secondary)
- **Package Management**: renv for reproducible environments

## Development Commands

> **🚀 See [README.md - Installation & Running](README.md#installation) for complete setup and execution instructions**

### Quick Reference
```bash
# Environment setup
Rscript setup_environment.R

# Run application  
Rscript run_app.R

# Access at: http://localhost:3838
```

## Key Architecture Patterns

### API Integration Pattern
- **Centralized Client**: All API calls go through `modules/api_client.R`
- **Error Handling**: Consistent error handling with httr2
- **Modern HTTP**: Uses httr2 pipe syntax for requests
- **JSON Processing**: Built-in JSON parsing with error recovery

### Real-time Communication
- **Dual WebSocket Implementation**: 
  - R client (`modules/websocket_client.R`) for server-side integration
  - JavaScript client (`www/websocket_client.js`) for frontend responsiveness
- **Auto-reconnection**: Exponential backoff with 5-second intervals
- **Event Types**: `study_created`, `study_updated`, `study_deleted`, `refresh_needed`
- **Keep-alive**: 30-second ping/pong mechanism

### Module Structure
```
modules/
├── api_client.R        # HTTP client functions (httr2-based)
├── studies_ui.R        # UI components and layouts
├── studies_server.R    # Server logic and reactivity
└── websocket_client.R  # R WebSocket client
```

### Modern UI Components
- **bslib Framework**: Bootstrap 5 with custom theming
- **Icons**: bsicons for consistent iconography  
- **Layout**: page_sidebar with responsive design
- **Cards**: Modern card-based layouts
- **Interactive Tables**: DT with custom styling

## Backend Dependencies

> **🔗 See [README.md - API Integration](README.md#api-integration) for complete endpoint documentation and WebSocket details**

### Required Services
- **FastAPI Backend**: `http://localhost:8000` (must be running)
- **WebSocket Endpoint**: `ws://localhost:8000/api/v1/ws/studies`
- **Database**: PostgreSQL (managed by backend)

## Package Ecosystem

> **📦 See [README.md - Required Packages](README.md#installation) for complete package list and versions**

### Key Dependencies
- `shiny` + `bslib` + `bsicons` - Modern UI framework
- `httr` + `jsonlite` - API communication  
- `websocket` + `later` - Real-time features
- `DT` + `shinyWidgets` - Enhanced UI components

## Application Configuration

> **⚙️ See [README.md - Configuration](README.md#configuration) for complete configuration options**

### Critical Configuration Files
- **API URL**: `app.R` → `API_BASE_URL`
- **WebSocket URLs**: `www/websocket_client.js` + `modules/websocket_client.R`  
- **App Port**: `run_app.R` → `port = 3838`

## Development Workflow

> **🛠️ See [README.md - Development](README.md#development) for complete development workflow and patterns**

### Key Development Guidelines
1. **UI/Server Separation**: Use modular architecture in `modules/`
2. **API Integration**: Centralize HTTP calls in `modules/api_client.R`
3. **Real-time Updates**: Handle WebSocket events in JavaScript + R layers
4. **Modern Patterns**: Use bslib + renv + namespace separation

## Critical WebSocket Implementation Details

> **🚨 See [README.md - Real-time Updates Lessons Learned](README.md#real-time-updates-lessons-learned) for comprehensive WebSocket troubleshooting and implementation details**

### Most Important Implementation Points
1. **Shiny Module Namespacing**: Events must be `studies-websocket_*` format
2. **Data Conversion**: SQLAlchemy → Pydantic conversion in broadcast functions  
3. **Dual Client Architecture**: JavaScript (primary) + R (secondary) WebSocket clients
4. **Connection Management**: DOM ready state + auto-reconnect + keep-alive

### Debugging WebSocket Issues
- **Browser Console**: F12 → Console for JavaScript WebSocket logs
- **R Console**: Server-side reactive processing and data conversion logs  
- **Backend Logs**: WebSocket broadcast function calls and connection management
- **Network Tab**: F12 → Network → WS tab for connection establishment

### Testing Real-time Updates
```bash
# Test WebSocket broadcasting
cd ../backend  
uv run python ../test_websocket_broadcast.py

# Manual testing: Open multiple browser sessions and test CRUD operations
```