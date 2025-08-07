# Packages Frontend Implementation

## Overview

The Packages frontend module has been successfully implemented for the PEARL research data management system. This module provides a comprehensive interface for managing TLF (Tables, Listings, Figures) and Dataset packages with full CRUD operations and real-time WebSocket synchronization.

## Features Implemented

### 1. Package Management
- **Create Packages**: Add new packages with unique names
- **View Packages**: List all packages with creation timestamps
- **Edit Packages**: Update package names (UI buttons ready, functionality to be added)
- **Delete Packages**: Remove packages with deletion protection (prevents deletion if items exist)

### 2. Package Items Management
- **Add TLF Items**: Create Table, Listing, or Figure items with TLF IDs
- **Add Dataset Items**: Create SDTM or ADaM dataset items with labels
- **View Items**: Display items grouped by package with study associations
- **Delete Items**: Remove individual items from packages

### 3. Real-time Updates
- **WebSocket Integration**: All CRUD operations broadcast real-time events
- **Multi-user Sync**: Changes appear instantly across all browser sessions
- **Event Types**: 
  - `package_created`, `package_updated`, `package_deleted`
  - `package_item_created`, `package_item_updated`, `package_item_deleted`

## File Structure

```
admin-frontend/
├── modules/
│   ├── packages_ui.R        # UI components (tabs, forms, tables)
│   ├── packages_server.R     # Server logic and event handling
│   └── api_client.R          # API endpoints (updated with package functions)
├── www/
│   └── websocket_client.js  # WebSocket client (updated for package events)
└── app.R                     # Main app (updated to include packages module)
```

## UI Components

### Main Interface
- **Location**: Package Registry tab in sidebar navigation
- **Layout**: Tabbed interface with "Packages" and "Package Items" tabs
- **Styling**: Consistent with existing modules using bslib and Bootstrap 5

### Package Tab
- **Data Table**: Interactive table with search and pagination
- **Actions**: Edit and Delete buttons for each package
- **Add Form**: Sliding sidebar form for creating new packages

### Package Items Tab
- **Package Selector**: Dropdown to select active package
- **Add Item Button**: Opens modal for creating new items
- **Item Types**: Support for both TLF and Dataset items
- **Item Table**: Displays items with study, type, subtype, and code

## API Integration

### Endpoints Used
- `GET /api/v1/packages/` - List all packages
- `POST /api/v1/packages/` - Create new package
- `PUT /api/v1/packages/{id}` - Update package
- `DELETE /api/v1/packages/{id}` - Delete package
- `GET /api/v1/packages/{id}/items` - Get package items
- `POST /api/v1/packages/{id}/items` - Create package item
- `DELETE /api/v1/packages/items/{id}` - Delete package item

### Backend Enhancements
- Added `study_label` field to PackageItem schema for frontend display
- Updated CRUD operations to include study relationship loading
- Ensured proper WebSocket broadcasting for all operations

## Testing

### Test Script
A test script is provided at `/test_packages_frontend.sh` to verify functionality:

```bash
chmod +x test_packages_frontend.sh
./test_packages_frontend.sh
```

This script:
1. Creates a test package
2. Creates a test study (if needed)
3. Adds TLF and Dataset items
4. Verifies WebSocket broadcasting

### Manual Testing Steps
1. Start backend: `cd backend && uv run python run.py`
2. Start frontend: `cd admin-frontend && Rscript run_app.R`
3. Navigate to Package Registry tab
4. Test CRUD operations:
   - Create a package using "Add Package" button
   - Switch to Package Items tab
   - Select the package from dropdown
   - Add TLF and Dataset items
   - Delete items and packages

## Usage Instructions

### Creating a Package
1. Click "Add Package" button in Package Registry tab
2. Enter a unique package name
3. Click "Create" to save

### Adding Package Items
1. Go to Package Items tab
2. Select a package from the dropdown
3. Click "Add Item" button
4. Fill in the form:
   - Select Study
   - Choose Type (TLF or Dataset)
   - For TLF: Select subtype (Table/Listing/Figure) and enter TLF ID
   - For Dataset: Select subtype (SDTM/ADaM), enter dataset name and label
5. Click "Save"

### Deleting Items
1. Click the trash icon next to any item
2. Confirm deletion in the modal

### Deleting Packages
1. Packages can only be deleted if they have no items
2. Delete all items first, then delete the package

## Known Limitations

1. **Edit Functionality**: Edit buttons are present but functionality needs implementation
2. **Filtering**: No filtering by study or type yet
3. **Bulk Operations**: No bulk delete or import functionality
4. **Export**: No export to CSV/Excel functionality

## Future Enhancements

1. **Edit Modal**: Implement edit functionality for packages and items
2. **Advanced Filtering**: Add filters by study, type, and subtype
3. **Bulk Operations**: Multi-select for bulk delete
4. **Import/Export**: CSV upload and download functionality
5. **Validation**: Enhanced form validation with real-time feedback
6. **Sorting**: Custom sorting options for items
7. **Statistics**: Dashboard showing package statistics

## WebSocket Event Flow

```
User Action → R Shiny → API Call → Backend
                ↓
         WebSocket Broadcast
                ↓
All Connected Clients ← JavaScript Client ← WebSocket Server
                ↓
         Shiny Module Update
                ↓
            UI Refresh
```

## Dependencies

### R Packages Required
- shiny (≥1.8.0)
- bslib (≥0.6.0)
- httr2 (≥1.0.0)
- DT (≥0.30)
- shinyvalidate (≥0.1.3)
- jsonlite
- bsicons

### Backend Requirements
- FastAPI with packages endpoints
- PostgreSQL with packages tables
- WebSocket broadcasting enabled

## Troubleshooting

### Common Issues

1. **"No packages found"**
   - Verify backend is running
   - Check API endpoint connectivity
   - Create a package using the test script

2. **Items not showing**
   - Ensure a package is selected in dropdown
   - Refresh the page
   - Check browser console for errors

3. **WebSocket not updating**
   - Check WebSocket connection status
   - Verify backend WebSocket endpoint
   - Check browser console for WebSocket errors

4. **Delete fails**
   - Ensure no items exist before deleting package
   - Check for referential integrity constraints
   - View error message for details

## Code Quality

The implementation follows established patterns:
- Modular design with separate UI and server components
- Consistent with existing modules (studies, database_releases, etc.)
- Proper error handling and user feedback
- Real-time WebSocket integration
- Bootstrap 5 styling with bslib
- Form validation using shinyvalidate

## Summary

The Packages frontend successfully provides a complete interface for managing TLF and Dataset packages in the PEARL system. It maintains consistency with existing modules while adding new functionality specific to package management. The real-time WebSocket integration ensures all users see updates immediately, making it suitable for multi-user environments.