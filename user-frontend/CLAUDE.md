# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the R Shiny user frontend for the PEARL research data management system. It provides a user-facing interface for viewing and managing reporting effort tracking data with role-based access control.

## Status

**⚠️ NOT YET IMPLEMENTED**: This frontend is planned but not yet developed. It will include:

## Planned Features

### Authentication & Authorization
- Posit Connect session integration
- Development user switching
- Role-based UI rendering
- Permission enforcement

### User Tracker Interface
- Read-only mode for viewers
- Edit capabilities for editors
- Filtering and sorting
- Inline editing where appropriate

### Comment System
- Blog-style display
- Programmer/biostat thread separation
- Threaded replies
- Real-time updates via WebSocket
- @mentions functionality

### User Dashboard
- Task summary cards
- Overdue/upcoming views
- Workload breakdown by effort
- Progress visualizations (plotly)
- Priority items table (GT)

## Technology Stack (Planned)

- **R Shiny** with modular architecture
- **bslib** for Bootstrap 5 theming
- **httr2** for API integration
- **WebSocket** for real-time updates
- **plotly** for interactive visualizations
- **GT** for advanced tables
- **shinyvalidate** for form validation

## Development Guidelines

When implementing this frontend:

1. **Follow Admin Frontend Patterns**: Use the admin-frontend as a reference for:
   - Module structure (UI/Server separation)
   - API client patterns
   - WebSocket integration
   - Environment variable usage

2. **Implement Role-Based Access**: 
   - Viewers: Read-only access
   - Editors: Can modify assigned items
   - Admins: Full access (redirect to admin-frontend)

3. **User Experience Focus**:
   - Simplified interface compared to admin
   - Task-focused dashboards
   - Mobile-responsive design
   - Clear visual hierarchy

4. **Real-time Collaboration**:
   - WebSocket events for all updates
   - Live comment threads
   - Instant status changes
   - Multi-user awareness

## File Structure (Planned)

```
user-frontend/
├── CLAUDE.md           # This file
├── README.md           # User documentation
├── app.R               # Main application
├── modules/
│   ├── auth_ui.R       # Authentication UI
│   ├── auth_server.R   # Authentication logic
│   ├── dashboard_ui.R  # Dashboard interface
│   ├── dashboard_server.R
│   ├── tracker_ui.R    # Tracker interface
│   ├── tracker_server.R
│   ├── comments_ui.R   # Comments system
│   ├── comments_server.R
│   ├── api_client.R    # API integration
│   └── websocket_client.R
└── www/
    ├── style.css       # Custom styles
    └── websocket_client.js
```

## Implementation Priority

1. **Phase 1**: Authentication system
2. **Phase 2**: Read-only tracker view
3. **Phase 3**: Dashboard with visualizations
4. **Phase 4**: Comment system
5. **Phase 5**: Edit capabilities for editors

## Notes for Implementation

- Start with authentication to ensure security
- Build read-only views first, then add editing
- Test with multiple user roles simultaneously
- Ensure mobile responsiveness from the start
- Follow deferred validation patterns from admin-frontend