# PEARL Admin Frontend - R Shiny

R Shiny admin dashboard providing CRUD interface for the PEARL Studies management system.

## Overview

This R Shiny application provides a web-based admin interface for managing studies in the PEARL research data management system. It communicates with the FastAPI backend via REST API calls.

## Features

- **Studies Management**: Complete CRUD operations (Create, Read, Update, Delete)
- **Real-time Data**: Direct API communication with FastAPI backend
- **Responsive Design**: Bootstrap-based dashboard interface
- **Data Tables**: Interactive tables with sorting, filtering, and pagination
- **Form Validation**: Client-side and server-side validation
- **Health Monitoring**: Backend API health check

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
- `shinydashboard` - Dashboard layout
- `shinyWidgets` - Enhanced UI widgets
- `shinyBS` - Bootstrap components
- `DT` - Interactive data tables
- `httr` - HTTP client for API calls
- `jsonlite` - JSON parsing
- `dplyr` - Data manipulation
- `lubridate` - Date handling

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

### File Structure
```
admin-frontend/
├── app.R                    # Main Shiny application
├── run_app.R               # Application runner script
├── init_renv.R             # renv initialization script
├── install_dependencies.R  # renv restore script
├── renv.lock               # Package version lock file (auto-generated)
├── .gitignore              # Git ignore file for renv
├── modules/
│   ├── api_client.R       # HTTP API client functions
│   ├── studies_ui.R       # Studies interface UI
│   └── studies_server.R   # Studies interface server logic
├── www/                   # Static web assets (CSS, JS, images)
│   └── style.css          # Custom CSS styling
└── README.md              # This file
```

### Module Architecture

**Main App (`app.R`)**:
- Application configuration and routing
- Dashboard layout with sidebar navigation
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

## API Integration

The application communicates with the FastAPI backend using these endpoints:

- `GET /api/v1/studies` - List all studies
- `GET /api/v1/studies/{id}` - Get single study
- `POST /api/v1/studies` - Create new study
- `PUT /api/v1/studies/{id}` - Update existing study
- `DELETE /api/v1/studies/{id}` - Delete study
- `GET /health` - Health check

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

### Getting Help

1. Check R console for error messages
2. Verify backend API is responding: http://localhost:8000/health
3. Test API endpoints directly with curl or browser
4. Check browser developer tools for network errors

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

### Styling
Add custom CSS files to `www/` directory and reference in UI.