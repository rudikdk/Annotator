# PID Annotator Component Architecture Analysis

## Overview
The PID Annotator web application uses a **React 18 SPA** (Single Page Application) with session-based state management. The application implements three major feature components:
1. **Color Rules** - Tag and Excel column-based highlighting with priority ordering
2. **Excel Column Chooser** - Dynamic unique value extraction for header columns
3. **Active Filters** - Include/Exclude filtering with tag part and Excel column matching

---

## 1. COLOR RULES COMPONENT

### Location
**File:** `/mnt/c/Tools/Python vaerktoejer/Released python Tools/Annotator/Annotator/templates/index.html`
**Lines:** 2355-2900 (state definition), 5457-6000+ (JSX rendering)

### State Management

#### State Hooks (Lines 2355-2375)
```javascript
// Core color rules state
const [colorRules, setColorRules] = useState([]); 
  // Array of: {id, rule_type, part|column_name, value, match_type, color}

// Default highlight color (fallback when no rule matches)
const [defaultHighlightColor, setDefaultHighlightColor] = useState("#FFFF00");
const [enableDefaultColor, setEnableDefaultColor] = useState(true);

// Excel constraint mode - only highlight tags found in Excel
const [excelConstraintMode, setExcelConstraintMode] = useState(true);
const [excelConstraintLogic, setExcelConstraintLogic] = useState("AND");

// UI Panel states
const [colorRulePanelOpen, setColorRulePanelOpen] = useState(false);
const [colorRuleBuilderOpen, setColorRuleBuilderOpen] = useState(false);

// Rule builder form fields
const [newRuleType, setNewRuleType] = useState('tag_part'); // 'tag_part' or 'header_column'
const [newRulePart, setNewRulePart] = useState(1); // For tag_part rules (1-5)
const [newRuleColumn, setNewRuleColumn] = useState(''); // For header_column rules
const [newRuleValue, setNewRuleValue] = useState('');
const [newRuleMatchType, setNewRuleMatchType] = useState('contains'); // 'exact' or 'contains'
const [newRuleColor, setNewRuleColor] = useState('#FFFF00');

// Available header column values (loaded on demand)
const [ruleAvailableHeaderValues, setRuleAvailableHeaderValues] = useState([]);
  // Array of: {value, count} - unique values with occurrence count
const [ruleLoadingHeaderValues, setRuleLoadingHeaderValues] = useState(false);
const [showAllRuleValues, setShowAllRuleValues] = useState(false); // Show >20 values toggle

// Color presets (localStorage)
const [colorPresets, setColorPresets] = useState({});
const [showSaveColorPresetModal, setShowSaveColorPresetModal] = useState(false);
const [colorPresetName, setColorPresetName] = useState('');
const [selectedColorPreset, setSelectedColorPreset] = useState('');
```

### Data Structure

#### Color Rule Object
```javascript
{
  id: "rule_1699005123_abc123def",        // Unique identifier (timestamp + random)
  rule_type: "tag_part",                   // 'tag_part' or 'header_column'
  
  // For tag_part rules:
  part: 2,                                 // Which part of tag (1=A, 2=B, 3=C, 4=D, 5=E)
  
  // For header_column rules:
  column_name: "Equipment Type",           // Excel column name
  
  // Common to both:
  value: "PUMP",                           // Value to match
  match_type: "contains",                  // 'exact' or 'contains'
  color: "#FF0000"                         // Highlight color in hex
}
```

#### Available Header Values Response
```javascript
[
  { value: "Valve", count: 45 },
  { value: "Pump", count: 23 },
  { value: "Motor", count: 12 }
]
```

### Handler Functions

#### `handleAddColorRule()` (Line 2746)
- Validates inputs (value must not be empty, column required for header_column)
- Creates rule object with unique ID
- Appends to colorRules array
- Resets builder form
- Shows success toast

#### `handleRemoveColorRule(ruleId)` (Line 2823)
- Filters out rule by ID
- Shows success toast

#### `handleClearAllColorRules()` (Line 2829)
- Empties colorRules array

#### `handleMoveColorRule(ruleId, direction)` (Line 2834)
- Reorders rules (changes priority)
- Supports 'up' and 'down' directions
- Respects array boundaries

#### `handleFetchHeaderValuesForRule(columnName)` (Lines 2802-2831)
- Calls `/get_header_unique_values` API endpoint
- Sets loading state
- Populates ruleAvailableHeaderValues dropdown
- Handles errors gracefully

#### `handleSaveColorPreset()` (Line 2851)
- Serializes all color rules + settings to localStorage
- Creates preset object with timestamp

#### `handleLoadColorPreset(presetName)` (Line 2866)
- Restores all color rules and settings from localStorage
- Overwrites current state completely

#### `handleDeleteColorPreset(presetName)` (Line 2879)
- Removes preset from localStorage

### JSX Rendering (Lines 5457-6000+)

#### Structure
```
Color Rules Card (expandable)
├── Helper Functions (getPartLabel, formatRuleDisplay)
├── Default Highlight Color Section
│   ├── Enable/Disable Checkbox
│   └── Color Picker
├── Excel Constraint Mode Section
│   ├── Enable/Disable Checkbox
│   └── Logic Mode (AND/OR)
├── Active Color Rules Section
│   ├── Rule List
│   │   ├── Color Swatch
│   │   ├── Rule Description (via formatRuleDisplay)
│   │   └── Control Buttons (Move Up, Move Down, Delete)
│   ├── Add Rule Button
│   └── Clear All Button
├── Color Rule Builder (conditional)
│   ├── Rule Type Selector (Tag Part vs Excel Column)
│   ├── Tag Part Selector (dropdown 1-5)
│   ├── Excel Column Selector (with value loading)
│   │   ├── Column Dropdown (excelColumns)
│   │   ├── Available Values Helper (clickable buttons)
│   │   └── Show More Toggle (>20 values)
│   ├── Value Input
│   ├── Match Type Selector (Exact vs Contains)
│   ├── Color Picker
│   └── Action Buttons (Add Rule, Cancel)
├── Color Presets Sub-Section
│   ├── Preset Selector Dropdown
│   ├── Load Button
│   ├── Save Button (opens modal)
│   ├── Delete Button
│   └── Clear All Button
└── Color Preview Sub-Section
    └── [Not shown - separate large section]
```

#### Key Display Helper
**formatRuleDisplay(rule)** (Line 5467)
```javascript
// Tag Part Example:
"Part B ≈ "PUMP""  // (≈ = contains, = = exact)

// Excel Column Example:
"Equipment Type = "Valve""
```

### API Integration

#### Endpoint: `/get_header_unique_values` (POST)
**Location:** `app.py` line 340

**Request:**
```json
{
  "selected_excel": "file.xlsx",
  "column_name": "Equipment Type",
  "header_row": 6
}
```

**Response:**
```json
{
  "values": [
    {"value": "Valve", "count": 45},
    {"value": "Pump", "count": 23}
  ],
  "error": null
}
```

#### Endpoint: `/preview_color_rules` (POST)
**Location:** `app.py` line 1533

**Request:**
```json
{
  "pdf_file": "drawing.pdf",
  "excel_file": "parts.xlsx",
  "tag_column": "Component ID",
  "header_row": 6,
  "color_rules": [...],
  "default_highlight_color": "#FFFF00",
  "enable_default_color": true,
  "excel_constraint_mode": true,
  "excel_constraint_logic": "AND",
  "tag_filters": [...],
  "filter_logic": "AND",
  "tag_matching_config": {...},
  "page_number": 5
}
```

**Response:**
```json
{
  "success": true,
  "preview_image": "data:image/png;base64,...",
  "page_number": 5,
  "total_pages": 150,
  "annotations_found": 42
}
```

### Data Flow

```
User Input (Rule Builder)
    ↓
handleAddColorRule()
    ├─ Validate inputs
    ├─ Create rule object with unique ID
    ├─ setColorRules([...colorRules, newRule])
    └─ Reset form fields
    
User Selects Column (Excel Column Rule)
    ↓
onChange → handleFetchHeaderValuesForRule(columnName)
    ├─ POST /get_header_unique_values
    ├─ setRuleAvailableHeaderValues(response.values)
    └─ Display clickable value buttons
    
User Clicks Value Button
    ↓
setNewRuleValue(val.value)
    └─ Prefills value input field
    
User Saves Preset
    ↓
handleSaveColorPreset()
    ├─ Serialize to localStorage
    └─ localStorage.setItem('colorPresets', JSON.stringify(updatedPresets))
    
User Previews Colors
    ↓
handlePreviewColorRules()
    ├─ Gather all settings
    ├─ POST /preview_color_rules
    └─ Display annotated PDF page with color highlighting
```

---

## 2. EXCEL COLUMN CHOOSER (Part of Filter/Color Rule Builders)

### Location
**File:** `/mnt/c/Tools/Python vaerktoejer/Released python Tools/Annotator/Annotator/templates/index.html`
**Lines:** 
- Color Rule Builder: 5700-5820 (select + value loading)
- Filter Builder: 4754-4870 (select + value loading)

### Implementation Pattern

#### For Color Rule Builder
```jsx
{newRuleType === 'header_column' && (
  <div className="space-y-2">
    <label className="block text-sm font-medium">Excel Column</label>
    <select
      value={newRuleColumn}
      onChange={(e) => {
        setNewRuleColumn(e.target.value);
        handleFetchHeaderValuesForRule(e.target.value);
      }}
      className="w-full rounded-lg border..."
    >
      <option value="">-- Select column --</option>
      {excelColumns.map(col => (
        <option key={col} value={col}>{col}</option>
      ))}
    </select>
    
    {/* Available Values Helper - LOADED ON DEMAND */}
    {newRuleColumn && (
      <div className="mt-2">
        {ruleLoadingHeaderValues ? (
          <div>Loading values...</div>
        ) : ruleAvailableHeaderValues.length > 0 ? (
          <div className="text-xs">
            <div>Available values (click to use):</div>
            <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
              {ruleAvailableHeaderValues.slice(0, showAllRuleValues ? undefined : 20).map((val, idx) => (
                <button
                  key={val.value || idx}
                  onClick={() => setNewRuleValue(val.value)}
                  className="px-2 py-0.5 rounded bg-zinc-200/70..."
                  title={`Click to use "${val.value}" (found ${val.count} times)`}
                >
                  {val.value} <span>({val.count})</span>
                </button>
              ))}
              {ruleAvailableHeaderValues.length > 20 && (
                <button
                  onClick={() => setShowAllRuleValues(!showAllRuleValues)}
                  className="..."
                >
                  {showAllRuleValues ? '- Show less' : `+ ${ruleAvailableHeaderValues.length - 20} more`}
                </button>
              )}
            </div>
          </div>
        ) : (
          <div>No values found in this column</div>
        )}
      </div>
    )}
  </div>
)}
```

#### For Filter Builder (Similar Pattern)
```jsx
{newFilterType === 'header_column' && (
  <div className="space-y-2">
    <label className="block text-sm font-medium">Excel Column</label>
    <select
      value={newFilterColumn}
      onChange={(e) => {
        setNewFilterColumn(e.target.value);
        // Fetch available values for this column
        if (e.target.value && selectedExcel) {
          handleFetchHeaderValuesForFilter(e.target.value);
        }
      }}
      className="w-full rounded-lg border..."
    >
      <option value="">-- Select column --</option>
      {excelColumns.map(col => (
        <option key={col} value={col}>{col}</option>
      ))}
    </select>
    
    {/* Available Values Helper - SHOWN BELOW SELECT */}
    {newFilterColumn && (
      <div className="mt-2">
        {loadingHeaderValues ? (
          <div>Loading values...</div>
        ) : availableHeaderValues.length > 0 ? (
          <div className="text-xs">
            <div>Available values ({availableHeaderValues.length}):</div>
            <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
              {availableHeaderValues.slice(0, 20).map((val, idx) => (
                <button
                  key={idx}
                  onClick={() => setNewFilterValue(val)}
                  className="px-2 py-0.5 rounded bg-zinc-200/70..."
                  title="Click to use this value"
                >
                  {val}
                </button>
              ))}
              {availableHeaderValues.length > 20 && (
                <span className="text-zinc-400 text-xs px-2 py-0.5">
                  +{availableHeaderValues.length - 20} more
                </span>
              )}
            </div>
          </div>
        ) : null}
      </div>
    )}
  </div>
)}
```

### State for Column Chooser

```javascript
// Color Rule Builder
const [newRuleColumn, setNewRuleColumn] = useState('');
const [ruleAvailableHeaderValues, setRuleAvailableHeaderValues] = useState([]);
  // [{ value: "Valve", count: 45 }, ...]
const [ruleLoadingHeaderValues, setRuleLoadingHeaderValues] = useState(false);
const [showAllRuleValues, setShowAllRuleValues] = useState(false);

// Filter Builder
const [newFilterColumn, setNewFilterColumn] = useState('');
const [availableHeaderValues, setAvailableHeaderValues] = useState([]);
  // ["Valve", "Pump", "Motor", ...] - Note: simpler format (string array only)
const [loadingHeaderValues, setLoadingHeaderValues] = useState(false);
```

### Data Structure

#### Color Rule Column Values
```javascript
// State: ruleAvailableHeaderValues
[
  { value: "Valve Type A", count: 23 },
  { value: "Pump Standard", count: 15 },
  { value: "Motor Industrial", count: 8 }
]
// Why count? Shows frequency of values in Excel
// Limited to top 100 values (by count)
```

#### Filter Column Values
```javascript
// State: availableHeaderValues
[
  "Valve Type A",
  "Pump Standard",
  "Motor Industrial"
]
// Simpler: just the unique values (no count)
// But same API endpoint returns both
```

### Handler Functions

#### `handleFetchHeaderValuesForRule(columnName)` (Lines 2802-2831)
```javascript
function handleFetchHeaderValuesForRule(columnName) {
  if (!columnName) {
    setRuleAvailableHeaderValues([]);
    return;
  }

  setRuleLoadingHeaderValues(true);
  fetch("/get_header_unique_values", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      selected_excel: selectedExcel,
      column_name: columnName,
      header_row: headerRow
    })
  })
    .then((r) => r.json())
    .then((data) => {
      setRuleLoadingHeaderValues(false);
      if (data.error) {
        setToast({ type: "error", text: data.error });
        setRuleAvailableHeaderValues([]);
      } else {
        setRuleAvailableHeaderValues(data.values || []);
        logToConsole(`Loaded ${data.values?.length || 0} unique values for column '${columnName}'`);
      }
    })
    .catch((err) => {
      setRuleLoadingHeaderValues(false);
      setToast({ type: "error", text: "Error fetching column values" });
      setRuleAvailableHeaderValues([]);
      logToConsole(`Error fetching header values: ${err.message}`);
    });
}
```

#### `handleFetchHeaderValuesForFilter(columnName)` (Lines 2585-2619)
```javascript
function handleFetchHeaderValuesForFilter(columnName) {
  if (!columnName) {
    setAvailableHeaderValues([]);
    return;
  }

  setLoadingHeaderValues(true);
  fetch("/get_header_unique_values", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      selected_excel: selectedExcel,
      column_name: columnName,
      header_row: headerRow
    })
  })
    .then((r) => r.json())
    .then((data) => {
      setLoadingHeaderValues(false);
      if (data.error) {
        setToast({ type: "error", text: data.error });
        setAvailableHeaderValues([]);
      } else {
        // Extract just the values (ignore count for filters)
        setAvailableHeaderValues(data.values || []);
        logToConsole(`Loaded ${data.values?.length || 0} unique values for column '${columnName}'`);
      }
    })
    .catch((err) => {
      setLoadingHeaderValues(false);
      setToast({ type: "error", text: "Error fetching column values" });
      setAvailableHeaderValues([]);
      logToConsole(`Error fetching header values: ${err.message}`);
    });
}
```

### Data Flow

```
User Selects Column from Dropdown
    ↓
onChange → setNewRuleColumn(value) + handleFetchHeaderValuesForRule(value)
    ↓
setRuleLoadingHeaderValues(true)
    ↓
POST /get_header_unique_values
    │
    ├─ Input: { selected_excel, column_name, header_row }
    │
    └─ Output: { values: [{value, count}, ...], error }
    ↓
setRuleLoadingHeaderValues(false)
setRuleAvailableHeaderValues(data.values)
    ↓
Render: Loading spinner → Value buttons (top 20) → "Show more" button if >20
    ↓
User Clicks Value Button
    ↓
onClick → setNewRuleValue(val.value)
    └─ Populates value input field
```

### Limitations & Design Decisions

1. **Top 20 Default Display**: Shows first 20 values, "Show more" expands all
2. **Count Included (Color Rules)**: Helps user understand frequency
3. **Count Excluded (Filters)**: Simpler UI for filters (just strings)
4. **Loading Spinner**: Shows only when fetching (good UX)
5. **Error Handling**: Shows toast + empty list on failure
6. **Lazy Loading**: Values loaded only when column selected
7. **API Limit**: Returns top 100 unique values max

---

## 3. ACTIVE FILTERS CARD

### Location
**File:** `/mnt/c/Tools/Python vaerktoejer/Released python Tools/Annotator/Annotator/templates/index.html`
**Lines:** 4679-5100 (Active Filters section + Filter Builder)

### State Management

#### State Hooks (Lines 2422-2441)
```javascript
// Core filtering state
const [tagFilters, setTagFilters] = useState([]); 
  // Array of: {filter_type, part|column_name, value, match_type, action}

const [filterLogic, setFilterLogic] = useState('AND'); // 'AND' or 'OR'

// UI Panel states
const [tagFilterPanelOpen, setTagFilterPanelOpen] = useState(false);
const [tagFiltersExpanded, setTagFiltersExpanded] = useState(false);

// Filter builder form fields
const [filterBuilderOpen, setFilterBuilderOpen] = useState(false);
const [newFilterType, setNewFilterType] = useState('tag_part'); 
  // 'tag_part' or 'header_column' or 'value'

const [newFilterPart, setNewFilterPart] = useState(1); // For tag_part filters (1-5)
const [newFilterColumn, setNewFilterColumn] = useState(''); // For header_column filters
const [newFilterValue, setNewFilterValue] = useState('');
const [newFilterMatchType, setNewFilterMatchType] = useState('exact'); 
  // 'exact' or 'contains'

const [newFilterAction, setNewFilterAction] = useState('include'); 
  // 'include' or 'exclude'

// Available header column values (loaded on demand)
const [availableHeaderValues, setAvailableHeaderValues] = useState([]);
  // ["Valve", "Pump", "Motor", ...] - simple string array
const [loadingHeaderValues, setLoadingHeaderValues] = useState(false);

// Filter preview
const [filterMatchingCount, setFilterMatchingCount] = useState(null);
const [filterPreviewOpen, setFilterPreviewOpen] = useState(false);
const [filterPreviewTags, setFilterPreviewTags] = useState([]);
const [filterPreviewExpanded, setFilterPreviewExpanded] = useState(false);
const [filterPreviewLoading, setFilterPreviewLoading] = useState(false);
```

### Data Structure

#### Filter Object
```javascript
{
  filter_type: "tag_part",  // 'tag_part', 'header_column', or 'value'
  
  // For tag_part filters:
  part: 2,                  // Which part of tag (1=A, 2=B, etc.)
  
  // For header_column filters:
  column_name: "Equipment Type",
  
  // Common to all:
  value: "PUMP",            // Value to match
  match_type: "exact",      // 'exact' or 'contains'
  action: "include"         // 'include' or 'exclude'
}
```

#### Filter Display Format
Helper function **formatFilterDisplay(filter)** (Line 4578)
```javascript
{
  action: "INCLUDE",                    // or "EXCLUDE"
  actionClass: "text-success bg-success/10", // or "text-danger bg-danger/10"
  description: "Part B = \"PUMP\""      // User-friendly display
}
```

### JSX Rendering

#### Structure (Lines 4679-4750)
```
Active Filters Section (expandable)
├── Header with Count Badge
├── Clear All Button (if filters exist)
├── Filter List
│   ├── Action Badge (green INCLUDE or red EXCLUDE)
│   ├── Filter Description (via formatFilterDisplay)
│   └── Delete Button
├── Add Filter + Preview Buttons (grid 2 cols)
│   ├── Add Filter Button
│   └── Preview Tags Button
│
Filter Builder Sub-Section (conditional - Lines 4730-5100)
├── Close Button
├── Action Toggle (INCLUDE vs EXCLUDE)
├── Filter Type Selector (Tag Part vs Excel Column vs Value)
├── Tag Part Selector (for tag_part type)
├── Excel Column Selector (for header_column type)
│   ├── Column Dropdown
│   ├── Available Values Helper
│   └── Show More Toggle
├── Value Input
├── Match Type Selector (Exact vs Contains)
└── Action Buttons (Add Filter, Cancel)
```

### Handler Functions

#### `handleAddFilter()` (Line 2525)
```javascript
function handleAddFilter() {
  if (!newFilterValue.trim()) {
    setToast({ type: "error", text: "Please enter a filter value" });
    return;
  }

  // Validate header_column filter has column selected
  if (newFilterType === 'header_column' && !newFilterColumn) {
    setToast({ type: "error", text: "Please select a column for header-based filtering" });
    return;
  }

  // Build filter object based on filter type
  const newFilter = {
    filter_type: newFilterType,
    value: newFilterValue.trim(),
    match_type: newFilterMatchType,
    action: newFilterAction
  };

  // Add type-specific fields
  if (newFilterType === 'tag_part') {
    newFilter.part = newFilterPart;
  } else if (newFilterType === 'header_column') {
    newFilter.column_name = newFilterColumn;
  }

  setTagFilters([...tagFilters, newFilter]);
  setFilterBuilderOpen(false);
  // Reset builder fields
  setNewFilterType('tag_part');
  setNewFilterPart(1);
  setNewFilterColumn('');
  setNewFilterValue('');
  setNewFilterMatchType('exact');
  setNewFilterAction('include');
  setAvailableHeaderValues([]);
  setToast({ type: "success", text: "Filter added successfully" });
}
```

#### `handleRemoveFilter(index)` (Line 2557)
```javascript
function handleRemoveFilter(index) {
  const updated = tagFilters.filter((_, i) => i !== index);
  setTagFilters(updated);
}
```

#### `handleClearAllFilters()` (Line 2561)
```javascript
function handleClearAllFilters() {
  setTagFilters([]);
  setFilterMatchingCount(null);
  setFilterPreviewTags([]);
  setFilterPreviewOpen(false);
  setToast({ type: "success", text: "All filters cleared" });
}
```

#### `handlePreviewFilters()` (Line 2566)
```javascript
function handlePreviewFilters() {
  if (!selectedExcel || !tagColumn) {
    setToast({ type: "error", text: "Please select an Excel file and tag column first" });
    return;
  }

  if (tagFilters.length === 0) {
    setToast({ type: "info", text: "No filters to preview. All tags will be processed." });
    return;
  }

  setFilterPreviewLoading(true);
  setFilterPreviewOpen(true);

  fetch("/preview_filtered_tags", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      selected_excel: selectedExcel,
      tag_column: tagColumn,
      header_row: headerRow,
      tag_filters: tagFilters,
      filter_logic: filterLogic
    })
  })
    .then((r) => r.json())
    .then((data) => {
      setFilterPreviewLoading(false);
      if (data.success) {
        setFilterPreviewTags(data.matching_tags);
        setFilterMatchingCount(data.matching_tags.length);
        logToConsole(`Filter preview: ${data.matching_tags.length}/${data.total_tags} tags match`);
      } else {
        setToast({ type: "error", text: data.message || "Failed to preview filters" });
        logToConsole(`Error previewing filters: ${data.message}`);
      }
    })
    .catch((err) => {
      setFilterPreviewLoading(false);
      setToast({ type: "error", text: "Error fetching filter preview" });
      logToConsole(`Error previewing filters: ${err.message}`);
    });
}
```

### API Integration

#### Endpoint: `/preview_filtered_tags` (POST)
**Location:** `app.py` line 375

**Request:**
```json
{
  "selected_excel": "parts.xlsx",
  "tag_column": "Component ID",
  "header_row": 6,
  "tag_filters": [
    {
      "filter_type": "tag_part",
      "part": 2,
      "value": "PUMP",
      "match_type": "contains",
      "action": "include"
    },
    {
      "filter_type": "header_column",
      "column_name": "Status",
      "value": "Active",
      "match_type": "exact",
      "action": "exclude"
    }
  ],
  "filter_logic": "AND"
}
```

**Response:**
```json
{
  "success": true,
  "matching_tags": ["A-B-C-D", "X-Y-Z", "P-Q-R"],
  "total_tags": 150,
  "message": "3 tags match the filter criteria"
}
```

### Core Processing (Backend)

**Function:** `apply_tag_filters()` in `pid_annotator_core.py` (Line 244)

**Key Logic:**
```python
def apply_tag_filters(tag, filters, filter_logic="AND", row_data=None):
  """
  Check if a tag matches the filter criteria.
  
  Filter Logic:
  - Exclude filters checked FIRST: if any exclude matches → return False (filtered out)
  - Include filters checked SECOND: 
    - If filter_logic='AND': ALL include filters must match
    - If filter_logic='OR': ANY include filter must match
  
  Examples:
  - No filters → all tags pass
  - Include Part B="PUMP" → only tags with PUMP in 2nd part pass
  - Exclude Status="Inactive" → tags with Status=Inactive are filtered
  - AND logic with 2 includes → both must match
  - OR logic with 2 includes → either can match
  """
```

### Data Flow

```
User Adds Filter (Filter Builder)
    ↓
handleAddFilter()
    ├─ Validate value not empty
    ├─ Validate column selected (for header_column type)
    ├─ Create filter object
    └─ setTagFilters([...tagFilters, newFilter])
    
User Clicks "Preview Tags"
    ↓
handlePreviewFilters()
    ├─ Validate Excel file + tag column selected
    ├─ POST /preview_filtered_tags with all filter settings
    └─ Display matching tags list
    
Backend Processing
    ↓
/preview_filtered_tags endpoint
    ├─ Load Excel file
    ├─ Extract all tags from tag column
    ├─ For each tag:
    │   └─ apply_tag_filters(tag, tag_filters, filter_logic)
    │       ├─ Check EXCLUDE filters first
    │       ├─ If any exclude matches → filter out
    │       ├─ Check INCLUDE filters with logic (AND/OR)
    │       └─ Return True if passes, False if filtered
    └─ Return matching tags + count
    
Display Results
    ↓
setFilterPreviewTags(data.matching_tags)
setFilterMatchingCount(data.matching_tags.length)
    └─ Show user how many tags match (e.g., "42 out of 150 tags match")
```

---

## 4. FILTER TYPES COMPARISON

| Filter Type | Input | Matches Against | Example |
|-----------|-------|-----------------|---------|
| **tag_part** | Part number (1-5) | Specific part of tag (A/B/C/D/E) | Part B = "PUMP" |
| **header_column** | Column name from Excel | Excel row value | Status = "Active" |
| **value** | Text string | Any part of tag | Value contains "XYZ" |

---

## 5. UNIQUE VALUES DATA FLOW

### Sources of Unique Values

#### 1. PDF Tags (Extracted during Preview)
**Endpoint:** `/preview_tag_matching` (Line 446 in app.py)
**Used by:** Tag Filter Preview, Color Preview
**Returns:** List of unique tags found in PDF

#### 2. Excel Column Values (On-Demand)
**Endpoint:** `/get_header_unique_values` (Line 340 in app.py)
**Used by:** Color Rule Builder, Filter Builder
**Returns:** Top 100 unique values with occurrence count

### Core Function: `analyze_header_unique_values()`
**Location:** `pid_annotator_core.py` line 602

```python
def analyze_header_unique_values(excel_path, column_name, header_row=6, top_n=100):
  """
  Returns: [
    {"value": "Valve", "count": 45},
    {"value": "Pump", "count": 23}
  ]
  
  Sorted by count (descending) - most common values first
  Limited to top_n (default 100)
  """
```

---

## 6. LOCALSTORAGE PERSISTENCE

### Color Presets Storage
```javascript
localStorage.setItem('colorPresets', JSON.stringify({
  "My Pump Colors": {
    name: "My Pump Colors",
    rules: [...],  // Full color rules array
    defaultColor: "#FFFF00",
    enableDefaultColor: true,
    excelConstraintMode: true,
    excelConstraintLogic: "AND",
    savedAt: "2024-11-01T14:30:00Z"
  }
}))
```

**Note:** Filters and tag matching settings are NOT persisted - they are session-only.

---

## 7. KEY ARCHITECTURAL PATTERNS

### Pattern 1: Lazy Loading with Loading States
```javascript
// 1. User triggers action
setLoadingHeaderValues(true);

// 2. Fetch data
fetch('/api/endpoint')

// 3. Update state + clear loading
setLoadingHeaderValues(false);
setAvailableHeaderValues(data.values);

// 4. Render with conditional
{loadingHeaderValues ? <Spinner /> : <Values />}
```

### Pattern 2: Form Builder with Reset
```javascript
// Open builder
setFilterBuilderOpen(true);

// On success, reset ALL fields
setNewFilterType('tag_part');
setNewFilterPart(1);
setNewFilterColumn('');
setNewFilterValue('');
setNewFilterMatchType('exact');
setNewFilterAction('include');
setAvailableHeaderValues([]);
setFilterBuilderOpen(false);
```

### Pattern 3: Helper Display Formatting
```javascript
// Store raw data
const filter = {
  filter_type: "tag_part",
  part: 2,
  value: "PUMP",
  match_type: "contains",
  action: "include"
};

// Format for display
const { action, actionClass, description } = formatFilterDisplay(filter);
// → description = "Part B ≈ \"PUMP\"" (user-friendly)
```

### Pattern 4: Constraint Logic
```javascript
// Default: restrict to Excel data
excelConstraintMode: true  // Only highlight tags found in Excel

// Logic selection
excelConstraintLogic: "AND"  // Tags must match multiple conditions
excelConstraintLogic: "OR"   // Tags can match any condition
```

---

## 8. SUMMARY TABLE

| Component | State Hooks Count | API Endpoints | Data Format | Persistence |
|-----------|------------------|---------------|-------------|------------|
| **Color Rules** | 20+ | `/get_header_unique_values`, `/preview_color_rules` | Objects with id, part/column_name, value, color | localStorage (presets) |
| **Excel Column Chooser** | 4-6 | `/get_header_unique_values` | `[{value, count}]` or `[strings]` | None (session) |
| **Active Filters** | 12+ | `/get_header_unique_values`, `/preview_filtered_tags` | Objects with filter_type, part/column_name, action | None (session) |
| **Tag Matching** | 8+ | `/preview_tag_matching` | Custom regex config object | None (session) |

---

## 9. UNIQUE VALUES LOADING TIMELINE

```
Page Load
├─ Excel file uploaded
│  └─ onColumnsLoaded() → setExcelColumns(columns)
│     └─ excelColumns state now populated
│
User Opens Color Rule Builder
├─ Selects rule type
│  └─ If header_column:
│     ├─ Shows excelColumns dropdown (pre-populated)
│     └─ Ready for column selection
│
User Selects Column
├─ onChange → handleFetchHeaderValuesForRule(columnName)
│  ├─ setRuleLoadingHeaderValues(true)
│  ├─ POST /get_header_unique_values
│  └─ setRuleAvailableHeaderValues(response.values)
│     └─ Shows loading spinner → value buttons
│
User Clicks Value
└─ onClick → setNewRuleValue(val.value)
   └─ Populates value input field
```

