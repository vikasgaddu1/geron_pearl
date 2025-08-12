# TODO: Package Module Frontend Implementation

## Phase 1: Update TNFP Module for ICH Category

### 1.1 TNFP UI Updates (`admin-frontend/modules/tnfp_ui.R`)
- [ ] Add "ICH Category" to type dropdown
  ```r
  choices = list(
    "Title" = "title",
    "Footnote" = "footnote",
    "Population Set" = "population_set",
    "Acronyms Set" = "acronyms_set",
    "ICH Category" = "ich_category"  # NEW
  )
  ```

### 1.2 TNFP Server Updates (`admin-frontend/modules/tnfp_server.R`)
- [ ] Update convert_text_elements_to_df to handle ich_category display
- [ ] Test creating/editing/deleting ich_category items
- [ ] Verify WebSocket updates work for ich_category

## Phase 2: Simple Packages Module

### 2.1 Create packages_ui.R (Follow users_ui.R pattern)
- [ ] Card layout with 1200px max-width, 700px height
- [ ] Header with icon, title, description
- [ ] Refresh button (follow users module pattern)
- [ ] Add Package button (toggles sidebar - CRITICAL!)
- [ ] Sidebar with 450px width containing form
  - [ ] Package name input with validation
  - [ ] Save and Cancel buttons
- [ ] DataTable for packages list
- [ ] Footer with last updated time

### 2.2 Create packages_server.R (Follow users_server.R pattern)
- [ ] Reactive values for packages data
- [ ] Load packages function with error handling
- [ ] DataTable render with action buttons
  ```r
  # CRITICAL: Action buttons pattern from users_server.R
  current_packages$Actions <- sapply(current_packages$ID, function(package_id) {
    sprintf(
      '<button class="btn btn-warning btn-sm me-1" data-action="edit" data-id="%s" title="Edit package">
        <i class="fa fa-pencil"></i>
      </button>
      <button class="btn btn-danger btn-sm" data-action="delete" data-id="%s" title="Delete package">
        <i class="fa fa-trash"></i>
      </button>',
      package_id, package_id
    )
  })
  ```
- [ ] observeEvent for toggle_add_package (CRITICAL - Often missed!)
  ```r
  observeEvent(input$toggle_add_package, {
    # Reset form
    updateTextInput(session, "new_package_name", value = "")
    # Toggle sidebar
    sidebar_toggle(id = "packages_sidebar")
    # Disable validation until save
    iv_package$disable()
  })
  ```
- [ ] observeEvent for package_action_click (CRITICAL - Edit/Delete buttons)
  ```r
  observeEvent(input$package_action_click, {
    info <- input$package_action_click
    if (info$action == "edit") {
      # Show edit modal
    } else if (info$action == "delete") {
      # Show delete confirmation
    }
  })
  ```
- [ ] Form validation with deferred pattern
  ```r
  iv_package <- InputValidator$new()
  iv_package$add_rule("new_package_name", sv_required())
  
  observeEvent(input$save_package, {
    iv_package$enable()  # Enable only on save
    if (iv_package$is_valid()) {
      # Save logic
      iv_package$disable()
    }
  })
  ```
- [ ] Duplicate error handling (CRITICAL!)
  ```r
  format_error_message <- function(error_string) {
    if (grepl("HTTP 400", error_string)) {
      json_part <- gsub("^.*HTTP 400[^-]*- ", "", error_string)
      tryCatch({
        error_data <- jsonlite::fromJSON(json_part)
        return(error_data$detail)
      }, error = function(e) {
        return(error_string)
      })
    }
    return(error_string)
  }
  ```
- [ ] WebSocket event handling
- [ ] Edit modal implementation
- [ ] Delete confirmation modal
- [ ] Refresh button functionality

## Phase 3: Complex Package Items Module

### 3.1 Create package_items_ui.R
- [ ] Card layout with standard dimensions
- [ ] Package selector dropdown in header
- [ ] Tab navigation (navset_pill) for TLF and Dataset
- [ ] TLF Tab structure
  - [ ] Add TLF button
  - [ ] Bulk Upload button
  - [ ] Download Template button
  - [ ] DataTable for TLF items
- [ ] Dataset Tab structure
  - [ ] Add Dataset button
  - [ ] Bulk Upload button
  - [ ] Download Template button
  - [ ] DataTable for dataset items
- [ ] Footer with item count and last updated

### 3.2 Create package_items_server.R - Core Setup
- [ ] Reactive values for selected package
- [ ] Reactive values for TLF items and Dataset items
- [ ] Reactive values for text elements by type
  ```r
  titles <- reactiveVal()
  footnotes <- reactiveVal()
  population_flags <- reactiveVal()
  acronyms <- reactiveVal()
  ich_categories <- reactiveVal()
  ```
- [ ] Load text elements function
  ```r
  load_text_elements <- function() {
    # Load each type separately
    titles_result <- get_text_elements_by_type("title")
    # Extract labels for selectize choices
  }
  ```

### 3.3 Package Selector Implementation
- [ ] Update selectizeInput choices when packages load
- [ ] observeEvent for package selection change
- [ ] Load items when package selected
- [ ] Clear tables when no package selected

### 3.4 TLF Tab - Add/Edit Modal
- [ ] Modal structure following existing patterns
- [ ] Selectize inputs with create option for each field
  ```r
  selectizeInput(ns("tlf_title_modal"), NULL,
    choices = titles(),
    options = list(
      create = TRUE,
      createOnBlur = TRUE,
      persist = FALSE,
      placeholder = "Select existing or type new title..."
    ),
    width = "100%"
  )
  ```
- [ ] observeEvent for each selectize field to handle new items
  ```r
  observeEvent(input$tlf_title_modal, {
    title_text <- trimws(input$tlf_title_modal)
    if (nzchar(title_text) && !(title_text %in% titles())) {
      # Create new text_element
      result <- create_text_element(list(
        type = "title",
        label = title_text
      ))
      if (is.null(result$error)) {
        titles(c(titles(), title_text))
        updateSelectizeInput(session, "tlf_title_modal",
          choices = titles(), selected = title_text, server = TRUE
        )
        showNotification(paste("Added title:", title_text), type = "message")
      }
    }
  })
  ```
- [ ] Repeat for footnotes (multiple), population_flag, acronyms (multiple), ich_category
- [ ] Form validation (deferred pattern)
- [ ] Save button logic with duplicate handling
- [ ] Cancel button logic

### 3.5 TLF Tab - DataTable
- [ ] Render DataTable with proper configuration
- [ ] Action buttons (Edit/Delete) - CRITICAL!
- [ ] observeEvent for tlf_action_click
- [ ] Edit functionality - populate modal with existing values
- [ ] Delete confirmation modal
- [ ] Handle empty state

### 3.6 Dataset Tab - Add/Edit Modal
- [ ] Simple modal without selectize dropdowns
- [ ] Radio buttons for SDTM/ADaM
- [ ] Text input for dataset name (auto-uppercase)
  ```r
  observeEvent(input$dataset_name_modal, {
    updateTextInput(session, "dataset_name_modal", 
      value = toupper(input$dataset_name_modal))
  })
  ```
- [ ] Text input for label
- [ ] Numeric input for sorting order
- [ ] Form validation
- [ ] Save with duplicate handling
- [ ] Cancel functionality

### 3.7 Dataset Tab - DataTable
- [ ] Render DataTable
- [ ] Action buttons
- [ ] observeEvent for dataset_action_click
- [ ] Edit/Delete functionality

### 3.8 Bulk Upload - TLF
- [ ] File input modal
- [ ] File validation
  ```r
  validate_tlf_file <- function(file_path) {
    df <- readxl::read_excel(file_path)
    errors <- list()
    
    # Check required columns
    required <- c("tlf_type", "tlf_code", "title")
    missing <- setdiff(required, names(df))
    if (length(missing) > 0) {
      errors <- c(errors, paste("Missing columns:", paste(missing, collapse = ", ")))
    }
    
    # Return validation result
    list(valid = length(errors) == 0, errors = errors, data = df)
  }
  ```
- [ ] Display validation errors in modal
- [ ] Process upload with progress indicator
- [ ] Handle backend errors
- [ ] Refresh table after successful upload

### 3.9 Bulk Upload - Dataset
- [ ] File input modal
- [ ] File validation
- [ ] Process upload
- [ ] Error handling
- [ ] Refresh table

### 3.10 Download Templates
- [ ] Create Excel templates in www/templates/
  - [ ] tlf_upload_template.xlsx
  - [ ] dataset_upload_template.xlsx
- [ ] Download button handlers
  ```r
  output$download_tlf_template <- downloadHandler(
    filename = "tlf_upload_template.xlsx",
    content = function(file) {
      file.copy("www/templates/tlf_upload_template.xlsx", file)
    }
  )
  ```

## Phase 4: API Client Updates

### 4.1 Update api_client.R
- [ ] Add get_text_elements_by_type function
  ```r
  get_text_elements_by_type <- function(type) {
    endpoint <- paste0(get_text_elements_endpoint(), "?type=", type)
    # ... implementation
  }
  ```
- [ ] Update create_package_item to not include study_id
- [ ] Add bulk_create_tlf_items function
- [ ] Add bulk_create_dataset_items function
- [ ] Ensure all error handling follows existing patterns

## Phase 5: Navigation Update

### 5.1 Update app.R
- [ ] Source new module files
  ```r
  source("modules/package_items_ui.R")
  source("modules/package_items_server.R")
  ```
- [ ] Update navigation menu
  ```r
  nav_menu(
    "Packages",
    nav_panel("Packages", value = "packages_tab", packages_ui("packages")),
    nav_panel("Package Items", value = "package_items_tab", package_items_ui("package_items"))
  )
  ```
- [ ] Add server module calls
  ```r
  packages_server("packages")
  package_items_server("package_items")
  ```

## Phase 6: WebSocket Integration

### 6.1 WebSocket Event Handling
- [ ] Handle package events in packages module
- [ ] Handle package_item events in package_items module
- [ ] Handle text_element events to refresh dropdowns
- [ ] Test real-time synchronization

## Phase 7: Playwright Testing

### 7.1 Test Packages Module
```python
# Navigate to Packages
mcp__playwright__browser_click(element="Packages menu", ref="...")
mcp__playwright__browser_click(element="Packages", ref="...")

# Test Add Package
mcp__playwright__browser_click(element="Add Package button", ref="...")
# Verify sidebar opens
mcp__playwright__browser_type(element="Package name input", ref="...", text="Test Package")
mcp__playwright__browser_click(element="Create button", ref="...")
# Verify package appears in table

# Test Edit Package
mcp__playwright__browser_click(element="Edit button for Test Package", ref="...")
# Verify modal opens with current values
mcp__playwright__browser_type(element="Package name in modal", ref="...", text="Updated Package")
mcp__playwright__browser_click(element="Update button", ref="...")

# Test Delete Package
mcp__playwright__browser_click(element="Delete button", ref="...")
# Verify confirmation modal
mcp__playwright__browser_click(element="Confirm delete", ref="...")
```

### 7.2 Test Package Items Module
```python
# Navigate to Package Items
mcp__playwright__browser_click(element="Package Items", ref="...")

# Select a package
mcp__playwright__browser_click(element="Package dropdown", ref="...")
mcp__playwright__browser_click(element="Test Package option", ref="...")

# Test TLF Tab
mcp__playwright__browser_click(element="Add TLF button", ref="...")
# Test selectize with create
mcp__playwright__browser_type(element="Title dropdown", ref="...", text="New Title")
# Press Enter to create
mcp__playwright__browser_press_key(key="Enter")
# Verify notification shows

# Test Dataset Tab
mcp__playwright__browser_click(element="Dataset tab", ref="...")
mcp__playwright__browser_click(element="Add Dataset button", ref="...")
# Fill form and save

# Test Bulk Upload
mcp__playwright__browser_click(element="Bulk Upload button", ref="...")
# Upload file and verify
```

### 7.3 Test WebSocket Synchronization
- [ ] Open two browser windows
- [ ] Create item in one window
- [ ] Verify appears in other window
- [ ] Test edit/delete synchronization

## Common Frontend Pitfalls to Avoid

1. **Sidebar Toggle**: Must use `sidebar_toggle(id = "sidebar_id")` without namespace
2. **Action Buttons**: Must use JavaScript callback pattern from users module
3. **Form Validation**: Only enable on save, disable after success/cancel
4. **Error Messages**: Parse HTTP 400 errors to get backend detail message
5. **Selectize Server-Side**: Use `server = TRUE` for large lists
6. **Modal IDs**: Use namespace for all input IDs in modals
7. **WebSocket Events**: Check for null before processing
8. **DataTable Callbacks**: Use drawCallback for button event binding
9. **Reactive Updates**: Assign reactive values to variables before use
10. **Download Handlers**: Must be in server function, not observers

## Success Criteria

- [ ] All UI elements follow existing design patterns
- [ ] Sidebar toggle works for Packages module
- [ ] Edit/Delete buttons work in all tables
- [ ] Modals open and close properly
- [ ] Form validation shows appropriate messages
- [ ] Duplicate errors display user-friendly messages
- [ ] Selectize dropdowns allow creating new items
- [ ] New text_elements persist and appear in dropdowns
- [ ] Bulk upload validates and shows errors
- [ ] Templates download correctly
- [ ] WebSocket updates work in real-time
- [ ] Playwright tests pass
- [ ] No console errors in browser
- [ ] Responsive layout works on different screen sizes