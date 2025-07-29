# PEARL Admin Frontend - bslib Migration Guide

This guide explains the modernization from shinydashboard to bslib for the PEARL Admin Frontend.

## What Changed

### 🎨 UI Framework
- **Before**: shinydashboard with AdminLTE theme
- **After**: bslib with modern Bootstrap 5 and Flatly theme

### 📦 New Dependencies
- Added `bslib` for modern Bootstrap themes and layouts
- Added `bsicons` for Bootstrap icon system
- Removed `shinydashboard` dependency
- Removed `shinyBS` dependency (replaced with native bslib modals)

### 🏗️ Architecture Improvements
- Migrated from `dashboardPage()` to `page_navbar()`
- Replaced `box()` components with modern `card()` components
- Added `value_box()` components for key metrics display
- Enhanced responsive design with `layout_columns()`
- Improved modal dialogs with native bslib modals

## Key Features

### 🎯 Modern UI Components
- **Value Boxes**: Display key metrics (Total Studies, Active Sessions, etc.)
- **Cards**: Modern card-based layout with headers and footers
- **Navigation**: Clean navbar with Bootstrap icons
- **Buttons**: Enhanced button styling with icons and proper spacing
- **Modals**: Native bslib modals with better UX

### 🎨 Visual Enhancements
- Modern Flatly theme with custom color scheme
- Google Fonts integration (Inter + Fira Code)
- Hover effects and smooth transitions
- Improved responsive design for mobile devices
- Dark mode support preparation

### 📊 Data Table Improvements
- Enhanced DataTable styling with Bootstrap classes
- Export buttons (Copy, CSV, Excel, PDF, Print)
- Better column sizing and responsive behavior
- Improved selection highlighting

## Migration Steps

### 1. Update Dependencies
```r
# Run the update script
Rscript update_dependencies.R
```

### 2. Key Code Changes

#### Navigation Structure
```r
# Before (shinydashboard)
dashboardPage(
  dashboardHeader(title = "PEARL Studies Manager"),
  dashboardSidebar(sidebarMenu(...)),
  dashboardBody(tabItems(...))
)

# After (bslib)
page_navbar(
  title = "PEARL Studies Manager", 
  theme = pearl_theme,
  nav_panel("Studies", ...),
  nav_panel("Health Check", ...)
)
```

#### Cards and Layout
```r
# Before (shinydashboard)
box(title = "Studies Management", status = "primary", ...)

# After (bslib)
card(
  card_header("Studies Management"),
  card_body(...),
  card_footer(...)
)
```

#### Modals
```r
# Before (shinyBS)
shinyBS::bsModal(id = "modal", title = "Form", ...)

# After (native Shiny)
showModal(modalDialog(
  title = tagList(bs_icon("plus"), "Add Study"),
  ...
))
```

### 3. CSS Updates
- Updated `www/style.css` for bslib compatibility
- Added Bootstrap 5 variable usage
- Enhanced responsive design
- Improved accessibility

## API Compatibility

✅ **Full Backward Compatibility**
- All API client functions remain unchanged
- HTTP requests to FastAPI backend work identically
- WebSocket integration preserved
- No backend changes required

## Features Preserved

- ✅ CRUD operations for studies
- ✅ Real-time data refresh
- ✅ Form validation
- ✅ Error handling and notifications
- ✅ Responsive design
- ✅ Health check functionality
- ✅ Modular architecture

## New Features Added

- 📊 **Value Boxes**: Key metrics dashboard
- 🎨 **Modern Theming**: Professional appearance
- 📱 **Better Mobile**: Enhanced responsive design
- 🔧 **Export Options**: DataTable export functionality
- ⚡ **Performance**: Smoother animations and transitions
- 🌙 **Dark Mode Ready**: Prepared for dark theme support

## Testing the Migration

### 1. Start the Backend
```bash
cd backend
uv run python run.py
```

### 2. Update Frontend Dependencies
```bash
cd admin-frontend
Rscript update_dependencies.R
```

### 3. Run the Modernized Frontend
```bash
Rscript run_app.R
```

### 4. Verify Functionality
- ✅ Studies table loads correctly
- ✅ Add new study works
- ✅ Edit existing study works  
- ✅ Delete study works
- ✅ Health check displays backend status
- ✅ Value boxes show correct metrics
- ✅ Responsive design works on mobile

## Troubleshooting

### Common Issues

**Missing Dependencies**
```r
# Solution: Install missing packages
install.packages(c("bslib", "bsicons"))
```

**Theme Not Loading**
```r
# Solution: Ensure bslib version is recent
install.packages("bslib")
```

**Icons Not Displaying**
```r
# Solution: Install bsicons
install.packages("bsicons")
```

### Performance Tips
- Clear browser cache if styling looks incorrect
- Restart R session if packages don't load properly
- Check browser console for JavaScript errors

## Rollback Plan

If you need to rollback to the original shinydashboard version:

1. Restore original files from git
2. Install original dependencies: `install.packages("shinydashboard")`
3. Run the original application

## Support

The modernized application maintains full API compatibility while providing a significantly improved user experience. All core functionality remains unchanged, with enhanced visual design and better responsive behavior.

For issues, check:
1. R console for error messages
2. Browser developer tools for JavaScript errors
3. Backend API health status at `/health`