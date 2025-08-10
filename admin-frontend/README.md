# PEARL Admin Frontend – R Shiny

R Shiny admin dashboard providing CRUD interface for the PEARL Studies management system.

## Overview

This R Shiny application provides a web-based admin interface for managing studies in the PEARL research data management system. It communicates with the FastAPI backend via REST API calls.

## Features

- **Entity Management**: Studies, Database Releases, Reporting Efforts, TNFP (Title/Footnote/Population/Acronyms)
- **Study Management Tree**: Hierarchical view using `shinyTree` for Study → Database Release → Reporting Effort with toolbar actions (Add Study, Add Child, Edit, Delete)
- **Real-time Updates**: WebSocket-based live data synchronization across multiple browser sessions
- **Modern UI**: Bootstrap 5 theming with `bslib`, dark/light mode, and responsive design
- **Data Tables**: Sorting, filtering (column filters on top), pagination; Actions column has minimal width
- **Form Validation**: `shinyvalidate` for consistent validation across forms
- **Connection Status**: Always-visible badges for WebSocket and API health in the navbar

## Prerequisites

- **R 4.3.0+** 
- **FastAPI Backend**: Must be running on `http://localhost:8000`
- **PostgreSQL**: Database backend (managed by FastAPI)

## Installation

### Using renv (Recommended)

This project uses `renv` for reproducible R package management:

#### First-time Setup
```bash
# Initialize renv environment (run once)
Rscript init_renv.R
```

#### Subsequent Setups (for other developers)
```r
# Restore packages from renv.lock
Rscript install_dependencies.R
# OR from R console:
renv::restore()
```

**Required Packages** (managed by renv):
- `shiny` - Core Shiny framework
- `bslib` - Modern Bootstrap 5 theming system
- `bsicons` - Icon system for modern UI
- `shinyWidgets` - Enhanced UI widgets
- `DT` - Interactive data tables
- `httr` - HTTP client for API calls
- `jsonlite` - JSON parsing
- `websocket` - WebSocket client for real-time updates
- `later` - Async scheduling for WebSocket reconnection
- `dplyr` - Data manipulation
- `lubridate` - Date handling
- `shinyTree` - Tree view for hierarchical Study Management

### Alternative: Manual Installation (Not Recommended)

```r
install.packages(c(
  "shiny", "shinydashboard", "shinyWidgets", "shinyBS",
  "DT", "httr", "jsonlite", "dplyr", "lubridate"
))
```

## Running the Application

### Method 1: Using the Runner Script
```bash
# Make executable (Linux/Mac)
chmod +x run_app.R

# Run the application
Rscript run_app.R
```

### Method 2: From R Console
```r
# Start R and run
shiny::runApp(".", port = 3838, host = "0.0.0.0")
```

### Method 3: RStudio
1. Open `app.R` in RStudio
2. Click "Run App" button
3. Or use `Ctrl+Shift+Enter`

## Application Access

- **Frontend URL**: http://localhost:3838
- **Backend API**: http://localhost:8000 (must be running)
- **API Documentation**: http://localhost:8000/docs

## Architecture

### File Structure (simplified)
```
admin-frontend/
├── app.R                    # Main Shiny application
├── run_app.R               # Application runner script
├── setup_environment.R     # Consolidated environment setup script
├── renv.lock               # Package version lock file (auto-generated)
├── .gitignore              # Git ignore file for renv
├── modules/
│   ├── api_client.R        # HTTP API client functions
│   ├── studies_ui.R        # Studies interface UI components
│   ├── studies_server.R    # Studies interface server logic
│   └── websocket_client.R  # R WebSocket client for real-time updates
├── www/                    # Static web assets (CSS, JS, images)
│   ├── websocket_client.js # JavaScript WebSocket client
│   └── style.css           # Custom CSS styling
└── README.md               # This file
```

### Module Architecture

**Main App (`app.R`)**:
- Application configuration and routing via `page_navbar`
- Grouped menus (Data Management, Packages) and right-aligned status badges
- Module integration and orchestration

**API Client (`modules/api_client.R`)**:
- HTTP client functions for all API endpoints
- Error handling and response parsing
- RESTful operations: GET, POST, PUT, DELETE

**Studies UI (`modules/studies_ui.R`)**:
- User interface for studies management
- Data table display with action buttons
- Modal forms for create/edit operations

**Studies Server (`modules/studies_server.R`)**:
- Server-side logic for studies operations
- Reactive data management
- Form validation and API integration
- WebSocket event handling and UI updates

**WebSocket Clients**:
- JavaScript (`www/websocket_client.js`) for browser-side real-time communication
- R helper available but currently not used for connection management

## API Integration

The application communicates with the FastAPI backend using these endpoints:

### REST API Endpoints
- `GET /api/v1/studies` - List all studies
- `GET /api/v1/studies/{id}` - Get single study
- `POST /api/v1/studies` - Create new study
- `PUT /api/v1/studies/{id}` - Update existing study
- `DELETE /api/v1/studies/{id}` - Delete study
- `GET /health` - Health check

### WebSocket Integration
- **Endpoint**: `ws://localhost:8000/api/v1/ws/studies`
- **Events**: `study_created`, `study_updated`, `study_deleted`, `studies_update`
- **Auto-reconnect**: 5-second intervals with exponential backoff
- **Keep-alive**: 30-second ping/pong mechanism

## Usage

### 1. Start Backend Services
```bash
# Navigate to backend directory
cd ../backend

# Start FastAPI server
uv run python run.py
```

### 2. Start Frontend Application
```r
# In R console or RStudio
shiny::runApp(".", port = 3838)
```

### 3. Access Application
- Open browser to http://localhost:3838
- Use the Studies tab to manage study records
- Check Health Check tab to verify backend connectivity

### 4. Study Operations

**Create Study**:
1. Click "Add Study" button
2. Fill in study label (required) and description (optional)
3. Click "Save"

**Edit Study**:
1. Select study from table
2. Click "Edit Selected" 
3. Modify fields
4. Click "Save"

**Delete Study**:
1. Select study from table
2. Click "Delete Selected"
3. Confirm deletion

### 5. Real-time Updates
The application provides live synchronization across multiple browser sessions:

**Multi-user Experience**:
- Open multiple browser tabs/windows to see real-time updates
- Changes made in one session appear instantly in all other sessions
- WebSocket status indicator shows connection health (🟢 Connected / 🔴 Disconnected)

**Real-time Features**:
- **Live Data Sync**: Study creation, updates, and deletions appear immediately
- **Auto-reconnect**: Connection automatically restores if network is interrupted
- **Cross-browser Updates**: Changes are synchronized across different browsers
- **Status Monitoring**: Visual indicators show WebSocket connection status

## Development

### renv Workflow

**Adding New Packages**:
```r
# Install new package
renv::install("package_name")

# Update renv.lock file
renv::snapshot()
```

**Updating Packages**:
```r
# Update all packages
renv::update()

# Update specific package
renv::update("package_name")

# Snapshot updated versions
renv::snapshot()
```

**Project Collaboration**:
```r
# New team member setup
renv::restore()  # Installs exact package versions from renv.lock

# After pulling changes with new packages
renv::restore()  # Sync with updated renv.lock
```

### Adding New Features

1. **UI Changes**: Modify `modules/studies_ui.R`
2. **Server Logic**: Update `modules/studies_server.R` 
3. **API Functions**: Extend `modules/api_client.R`
4. **Styling**: Add CSS to `www/` directory
5. **New Packages**: Use `renv::install()` and `renv::snapshot()`

### Debugging

**Enable Shiny Debugging**:
```r
options(shiny.reactlog = TRUE)
options(shiny.trace = TRUE)
```

**View API Responses**:
- Check browser network tab for HTTP requests
- Use `print()` statements in server functions
- Enable R console output for API errors

### Testing

**Manual Testing**:
1. Test all CRUD operations
2. Verify error handling with invalid data
3. Check responsiveness across screen sizes
4. Test with backend offline

**API Testing**:
Use the backend's simple test script:
```bash
cd ../backend
./test_crud_simple.sh
```

## Troubleshooting

### Common Issues

**"Cannot connect to backend"**:
- Ensure FastAPI server is running on port 8000
- Check firewall settings
- Verify API base URL in configuration

**"Packages not found"**:
- Run `Rscript install_dependencies.R` to restore renv environment
- Check R version compatibility (R 4.3.0+ required)
- If renv.lock is missing, run `Rscript init_renv.R` first

**"Port already in use"**:
- Change port in `run_app.R` or use different port:
  ```r
  runApp(".", port = 3839)
  ```

**Modal not opening**:
- Ensure `shinyBS` package is loaded
- Check browser console for JavaScript errors

**WebSocket Issues**:
- **Status shows "Initializing"**: JavaScript WebSocket client not loading properly
  - Check browser console (F12 → Console) for JavaScript errors
  - Verify `websocket_client.js` loads successfully in Network tab
  - Ensure Shiny module namespacing is correct (`studies-websocket_*` events)

- **Status shows "Disconnected"**: Backend WebSocket endpoint not available
  - Verify backend is running: `curl http://localhost:8000/health`
  - Check WebSocket endpoint: Browser → F12 → Network → WS tab
  - Ensure WebSocket URL matches backend configuration

- **Connected but no real-time updates**: Data flow broken in processing chain
  - Check browser console for WebSocket message logs
  - Verify R console shows WebSocket event processing logs
  - Test manual CRUD operations to trigger WebSocket broadcasts
  - Check backend logs for broadcast function calls

### Real-time Updates Lessons Learned

**Critical WebSocket Implementation Points**:

1. **Dual Client Architecture**: 
   - JavaScript client handles browser-side WebSocket connection and UI responsiveness
   - R client (unused in current implementation) provides server-side integration option
   - JavaScript approach chosen for better browser compatibility and debugging

2. **Shiny Module Namespacing**:
   - WebSocket events must be namespaced correctly: `studies-websocket_status`, `studies-websocket_event`
   - JavaScript `Shiny.setInputValue()` calls must match R `input$websocket_*` observers
   - Module namespace prefix (`studies-`) is automatically added by Shiny

3. **Data Type Conversion Issues**:
   - Backend SQLAlchemy models don't have `model_dump()` method (Pydantic only)
   - Must convert: `Study.model_validate(sqlalchemy_model).model_dump()` in broadcast functions
   - Same conversion needed in both WebSocket endpoint and broadcast functions

4. **Connection Management**:
   - DOM ready state checking prevents initialization failures
   - Auto-reconnection with exponential backoff prevents connection storms
   - Keep-alive ping/pong mechanism prevents idle connection timeouts
   - Proper cleanup on page unload prevents memory leaks

5. **Debugging Strategy**:
   - Browser console shows JavaScript WebSocket events and data flow
   - R console shows server-side reactive processing and data conversion
   - Backend logs show WebSocket broadcasts and connection management
   - Network tab shows WebSocket connection establishment and message flow

6. **Error Handling Patterns**:
   - Graceful degradation when WebSocket unavailable (falls back to HTTP polling)
   - Try-catch blocks around all WebSocket operations to prevent crashes
   - User-friendly status indicators for connection health
   - Automatic retry with backoff for failed connections

### Getting Help

1. Check R console for error messages and WebSocket event processing logs
2. Verify backend API is responding: http://localhost:8000/health
3. Test API endpoints directly with curl or browser
4. Check browser developer tools for network errors and WebSocket messages
5. Monitor backend logs for WebSocket broadcast function calls and errors

## Configuration

### API Configuration
Edit `app.R` to change API settings:
```r
API_BASE_URL <- "http://localhost:8000/api/v1"
```

### Port Configuration
Edit `run_app.R` to change application port:
```r
runApp(port = 3838)  # Change to desired port
```

### WebSocket Configuration
Configure WebSocket endpoints in two places:

**JavaScript Client (`www/websocket_client.js`)**:
```javascript
this.wsUrl = 'ws://localhost:8000/api/v1/ws/studies';
```

**R Client (`modules/websocket_client.R`)** (if used):
```r
WS_URL <- "ws://localhost:8000/api/v1/ws/studies"
```

### Styling
Add custom CSS files to `www/` directory and reference in UI.

## Testing Real-time Updates

### Manual Testing
1. **Open multiple browser sessions** to the frontend (different tabs/windows/browsers)
2. **Create a study** in one session - should appear instantly in all sessions
3. **Update a study** in one session - should update instantly in all sessions  
4. **Delete a study** in one session - should disappear instantly from all sessions
5. **Check WebSocket status** - should show 🟢 Connected in all sessions

### Automated Testing
Use the backend test script to trigger WebSocket events:
```bash
cd ../backend
uv run python ../test_websocket_broadcast.py
```

This script creates, updates, and deletes a test study while you watch the frontend for real-time updates.

### WebSocket Debug Testing
Check browser console logs for WebSocket activity:
1. Open Developer Tools (F12)
2. Go to Console tab
3. Look for WebSocket connection and message logs
4. Verify data flow: Backend → JavaScript → Shiny → UI

### Connection Health Monitoring
Monitor WebSocket connection status:
- **🟢 Connected**: Real-time updates active
- **🟡 Connecting**: Establishing connection  
- **🔴 Disconnected**: Connection lost, attempting reconnection
- **Reconnecting**: Auto-recovery in progress