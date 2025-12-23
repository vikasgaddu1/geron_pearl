# Advanced Table Filtering Implementation Guide

## ✅ Completed Components

### Core Infrastructure
1. **Filter Utilities** (`src/lib/filterUtils.ts`)
   - Wildcard matching (`*` support)
   - Regex pattern matching
   - Date range filtering
   - Multi-select filtering
   - Auto-detection of filter modes

2. **UI Components**
   - `Popover` and `Calendar` (shadcn/ui compatible)
   - `TextColumnFilter` - Text input with wildcard/regex toggle
   - `SelectColumnFilter` - Searchable multi-select with type-ahead
   - `DateRangeFilter` - Calendar picker with presets
   - `ColumnFilterPopover` - Wrapper for column filter UI
   - `HelpIcon` - Contextual help popovers
   - `TooltipWrapper` - Consistent tooltip implementation

3. **DataTable Component** (`src/components/common/DataTable.tsx`)
   - TanStack Table v8 integration
   - Per-column filtering with popover triggers
   - Sortable columns
   - Active filter indicators
   - Filter summary chips
   - "Clear All Filters" functionality
   - Pagination support (optional)
   - Custom cell rendering
   - Help icons in column headers

## ✅ Migrated Pages

### 1. User Management
**File:** `src/features/users/UserManagement.tsx`

**Filters Applied:**
- Username: Text filter (wildcard/regex)
- Role: Select filter (multi-select)
- Department: Text filter
- Created: Date range filter

**Enhancements:**
- Tooltips on all action buttons
- Help icon explaining user roles
- Enhanced form field placeholders
- Contextual help on each field

### 2. Packages List  
**File:** `src/features/packages/PackagesList.tsx`

**Filters Applied:**
- Package Name: Text filter
- Study Indication: Select filter
- Therapeutic Area: Select filter
- Created: Date range filter

**Enhancements:**
- Tooltips on View/Edit/Delete actions
- Help icon explaining packages
- Form field guidance

### 3. TFL Properties
**File:** `src/features/tfl-properties/TFLProperties.tsx`

**Filters Applied:**
- Label: Text filter (wildcard support)
- Content: Text filter (regex support)

**Enhancements:**
- Tab-specific descriptions
- Help icon explaining each text element type
- Tooltips on all actions
- Enhanced form guidance

## 📋 Implementation Pattern for Remaining Pages

For **PackageItems**, **ReportingEffortItems**, and **TrackerManagement**, follow this pattern:

### Step 1: Import Required Components

```typescript
import { DataTable, ColumnDef } from '@/components/common/DataTable'
import { TooltipWrapper } from '@/components/common/TooltipWrapper'
import { HelpIcon } from '@/components/common/HelpIcon'
```

### Step 2: Define Column Definitions

```typescript
const columns: ColumnDef<YourDataType>[] = [
  {
    id: 'columnId',
    header: 'Column Name',
    accessorKey: 'dataKey',
    filterType: 'text' | 'select' | 'date' | 'none',
    filterOptions: ['option1', 'option2'], // For select filters
    helpText: 'Description of this column',
    cell: (value, row) => {
      // Custom rendering
      return <span>{value}</span>
    },
    enableSorting: true, // Default is true
  },
  // Actions column example
  {
    id: 'actions',
    header: 'Actions',
    accessorKey: 'id',
    filterType: 'none',
    enableSorting: false,
    cell: (_, row) => (
      <div className="flex justify-end gap-2">
        <TooltipWrapper content="Edit item">
          <Button onClick={() => handleEdit(row)}>
            <Edit className="h-4 w-4" />
          </Button>
        </TooltipWrapper>
        <TooltipWrapper content="Delete item">
          <Button onClick={() => handleDelete(row)}>
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </TooltipWrapper>
      </div>
    ),
  },
]
```

### Step 3: Replace Table with DataTable

```typescript
// OLD:
<Table>
  <TableHeader>...</TableHeader>
  <TableBody>...</TableBody>
</Table>

// NEW:
<DataTable 
  data={yourData} 
  columns={columns}
  enablePagination={false} // Optional
/>
```

### Step 4: Remove Manual Search/Filter Logic

The DataTable handles filtering internally, so remove:
- Manual search state
- Filter functions
- Search input UI (filtering is now per-column)

### Step 5: Add Help Icons and Tooltips

```typescript
// Page header
<div className="flex items-center gap-2">
  <CardTitle>Your Title</CardTitle>
  <HelpIcon
    title="Feature Name"
    content={
      <div className="space-y-2">
        <p>Description...</p>
        <ul className="list-disc list-inside">
          <li>Point 1</li>
          <li>Point 2</li>
        </ul>
      </div>
    }
  />
</div>

// Form fields
<div className="flex items-center gap-2">
  <Label htmlFor="field">Field Name</Label>
  <HelpIcon content="Help text for this field" />
</div>
<Input
  id="field"
  placeholder="e.g., Example value"
  {...props}
/>
```

## 🎯 Filter Type Guidelines

### Text Filters
Use for: Free-text fields, codes, names, descriptions

**Features:**
- Wildcard support: `*001`, `TEST*`, `*ABC*`
- Regex toggle for advanced patterns
- Real-time filtering as you type

### Select Filters
Use for: Categorical data with limited options

**Features:**
- Type-ahead search
- Multi-select with checkboxes
- "Select All" / "Clear All" buttons
- Wildcard support in search

### Date Filters
Use for: Date/timestamp columns

**Features:**
- Calendar popup
- Quick presets (Today, Last 7 days, etc.)
- From/To range validation
- Handles empty dates gracefully

## 🎨 UX Best Practices

### Help Text Guidelines
1. **Column Help Text:** Explain what the column contains and how filtering works
2. **Form Field Help:** Provide examples and expected format
3. **Page-Level Help:** Give overview of the feature and its purpose

### Tooltip Guidelines
1. **Action Buttons:** Clearly state what the action does
   - ✅ "Edit user details"
   - ❌ "Edit"

2. **Icon Buttons:** Always include tooltips
3. **Timing:** 300ms delay (default in TooltipWrapper)

### Placeholder Guidelines
Use specific examples:
- ✅ `placeholder="e.g., STUDY-001"`
- ❌ `placeholder="Enter value"`

## 📊 Filter Examples

### Wildcard Patterns
- `*001` → Matches anything ending with 001
- `TEST*` → Matches anything starting with TEST
- `*ABC*` → Matches anything containing ABC
- `STUDY-*-001` → Matches STUDY-(anything)-001

### Regex Patterns
- `^STUDY-\d{3}$` → STUDY- followed by exactly 3 digits
- `(Table|Listing)` → Either "Table" or "Listing"
- `\d{4}-\d{2}-\d{2}` → Date pattern YYYY-MM-DD

### Date Range Presets
- **Today:** Current day only
- **Last 7 days:** Rolling 7-day window
- **Last 30 days:** Rolling 30-day window
- **This month:** Start to end of current month
- **Custom:** Manual from/to selection

## 🔧 Advanced Features

### Filter State Persistence
The DataTable component maintains filter state internally. For URL persistence:

```typescript
// TODO: Implement URL query param sync
const [searchParams, setSearchParams] = useSearchParams()

// Serialize filters to URL
const syncFiltersToURL = (filters) => {
  const params = new URLSearchParams()
  // ... encode filters
  setSearchParams(params)
}

// Restore filters from URL
useEffect(() => {
  const filters = parseFiltersFromURL(searchParams)
  // ... apply to table
}, [searchParams])
```

### Custom Filter Functions
For complex filtering logic, extend the `filterFn` in DataTable:

```typescript
filterFn: (row, columnId, filterValue) => {
  // Custom logic here
  return true // or false
}
```

### Pagination
Enable for large datasets:

```typescript
<DataTable 
  data={largeDataset}
  columns={columns}
  enablePagination={true}
  pageSize={25}
/>
```

## 🐛 Troubleshooting

### Filter Not Working
1. Check `filterType` is set correctly
2. Verify `accessorKey` matches data property
3. Ensure data is array of objects

### Select Filter Empty
1. Provide `filterOptions` array, or
2. Ensure data has values for auto-extraction

### Date Filter Issues
1. Dates must be ISO strings or Date objects
2. Check date format in data
3. Verify `matchDateRange` function usage

## 📝 Remaining Implementation Tasks

### PackageItems
- Apply DataTable to TLF, SDTM, and ADaM tabs
- Add tooltips to bulk actions
- Enhance upload dialog with help text

### ReportingEffortItems
- Apply DataTable to item listing
- Add status filter (select)
- Tooltip bulk edit actions

### TrackerManagement
- Apply DataTable with all filter types
- Priority filter (select)
- Status filters (select)
- Due date filter (date range)
- Tooltip comment indicators

## 🎓 Testing Checklist

- [ ] Wildcard patterns work in text filters
- [ ] Regex toggle enables/disables properly
- [ ] Invalid regex shows error message
- [ ] Select filter type-ahead works
- [ ] Multi-select reflects in filter summary
- [ ] Date range validation (from < to)
- [ ] Date presets populate correctly
- [ ] Filter summary chips display
- [ ] Individual filter clear works
- [ ] "Clear All Filters" works
- [ ] Active filter indicators show
- [ ] Sorting works on all columns
- [ ] Tooltips appear on hover
- [ ] Help icons show correct content
- [ ] Mobile responsive
- [ ] Keyboard navigation (Tab, Enter, Esc)
- [ ] Screen reader accessible

## 📚 Additional Resources

- [TanStack Table Docs](https://tanstack.com/table/v8)
- [Radix UI Tooltip](https://www.radix-ui.com/primitives/docs/components/tooltip)
- [React Day Picker](https://react-day-picker.js.org/)
- [Date-fns](https://date-fns.org/)

---

**Last Updated:** December 22, 2025
**Status:** Core infrastructure complete, 3 main pages migrated, pattern established for remaining pages


