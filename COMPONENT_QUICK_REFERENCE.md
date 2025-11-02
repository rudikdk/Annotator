# PID Annotator Components - Quick Reference

## File Locations

| Component | Frontend | Backend |
|-----------|----------|---------|
| **Color Rules** | `templates/index.html:2355-2900, 5457-6000+` | `app.py:340, 1533` |
| **Filters (Active)** | `templates/index.html:4679-5100, 2422-2441` | `app.py:375` |
| **Excel Column Chooser** | `templates/index.html:5700-5820, 4754-4870` | `app.py:340` |
| **Core Processing** | N/A | `pid_annotator_core.py:244, 602` |

---

## State Variables Quick Map

### Color Rules (20+ hooks)
```javascript
colorRules[]              // Main array
newRuleType             // 'tag_part' or 'header_column'
newRulePart             // 1-5
newRuleColumn           // Column name
newRuleValue            // Value to match
newRuleMatchType        // 'exact' or 'contains'
newRuleColor            // Hex color
defaultHighlightColor   // Fallback color
enableDefaultColor      // Boolean
excelConstraintMode     // Restrict to Excel
excelConstraintLogic    // 'AND' or 'OR'
colorRulePanelOpen      // UI state
colorRuleBuilderOpen    // Builder visible
ruleAvailableHeaderValues[] // [{value, count}]
ruleLoadingHeaderValues // Loading spinner
showAllRuleValues       // Show >20 toggle
colorPresets{}          // localStorage cache
```

### Active Filters (12+ hooks)
```javascript
tagFilters[]            // Main array
newFilterType           // 'tag_part', 'header_column', 'value'
newFilterPart           // 1-5
newFilterColumn         // Column name
newFilterValue          // Value to match
newFilterMatchType      // 'exact' or 'contains'
newFilterAction         // 'include' or 'exclude'
filterLogic             // 'AND' or 'OR'
filterBuilderOpen       // Builder visible
availableHeaderValues[] // [strings]
loadingHeaderValues     // Loading spinner
filterPreviewOpen       // Preview visible
filterPreviewTags[]     // Results
```

### Excel Column Chooser (4 hooks)
```javascript
excelColumns[]          // Available columns
newRuleColumn           // Selected column
ruleAvailableHeaderValues[] // Values
ruleLoadingHeaderValues // Loading state
```

---

## Data Structure Cheat Sheet

### Color Rule Object
```javascript
{
  id: "rule_1699005123_abc123",
  rule_type: "tag_part" | "header_column",
  part?: 1-5,                         // If tag_part
  column_name?: "Equipment Type",     // If header_column
  value: "PUMP",
  match_type: "exact" | "contains",
  color: "#FFFF00"
}
```

### Filter Object
```javascript
{
  filter_type: "tag_part" | "header_column" | "value",
  part?: 1-5,                         // If tag_part
  column_name?: "Equipment Type",     // If header_column
  value: "PUMP",
  match_type: "exact" | "contains",
  action: "include" | "exclude"
}
```

### Header Value Response
```javascript
// From /get_header_unique_values
[
  { value: "Valve", count: 45 },
  { value: "Pump", count: 23 }
]
// Top 100 by count, sorted descending
```

---

## Handler Functions Quick Reference

### Color Rules Handlers
| Function | Action | Lines |
|----------|--------|-------|
| `handleAddColorRule()` | Add rule to array | 2746 |
| `handleRemoveColorRule()` | Remove by ID | 2823 |
| `handleClearAllColorRules()` | Empty array | 2829 |
| `handleMoveColorRule()` | Reorder rule | 2834 |
| `handleFetchHeaderValuesForRule()` | Load values | 2802 |
| `handleSaveColorPreset()` | Save to localStorage | 2851 |
| `handleLoadColorPreset()` | Load from localStorage | 2866 |
| `handleDeleteColorPreset()` | Remove from localStorage | 2879 |

### Filter Handlers
| Function | Action | Lines |
|----------|--------|-------|
| `handleAddFilter()` | Add filter to array | 2525 |
| `handleRemoveFilter()` | Remove by index | 2557 |
| `handleClearAllFilters()` | Empty array | 2561 |
| `handlePreviewFilters()` | Fetch matching tags | 2566 |
| `handleFetchHeaderValuesForFilter()` | Load values | 2585 |

---

## API Endpoints

### `/get_header_unique_values` (POST)
- **Purpose**: Load unique values for dropdown
- **Called by**: Color Rule Builder, Filter Builder
- **Input**: `{selected_excel, column_name, header_row}`
- **Output**: `{values: [{value, count}]}`
- **Line**: app.py:340

### `/preview_filtered_tags` (POST)
- **Purpose**: Show matching tags preview
- **Called by**: Filter Builder "Preview Tags" button
- **Input**: `{selected_excel, tag_column, tag_filters, filter_logic}`
- **Output**: `{matching_tags, total_tags}`
- **Line**: app.py:375

### `/preview_color_rules` (POST)
- **Purpose**: Show annotated PDF preview
- **Called by**: Color Rules "Generate Preview" button
- **Input**: All color + filter + tag matching settings
- **Output**: `{preview_image: base64, page_number, total_pages}`
- **Line**: app.py:1533

---

## Core Processing Functions

### `analyze_header_unique_values()` (pid_annotator_core.py:602)
Returns unique values from Excel column with counts
```python
analyze_header_unique_values(excel_path, column_name, header_row=6, top_n=100)
# Returns: [{"value": "...", "count": 45}, ...]
```

### `apply_tag_filters()` (pid_annotator_core.py:244)
Checks if tag passes filter criteria
```python
apply_tag_filters(tag, filters, filter_logic="AND", row_data=None)
# Returns: True (process) or False (filter out)
# Logic: Exclude first, then Include with AND/OR
```

---

## UI Component Structure

### Color Rules Panel (Lines 5457-6100)
```
Color Rules Card (expandable)
├─ Default Highlight Color Section
├─ Excel Constraint Mode Section
├─ Active Color Rules Section
│  ├─ Rule List (color swatch + description + controls)
│  └─ Add Rule Button
├─ Color Rule Builder (if open)
│  ├─ Rule Type Selector
│  ├─ Part/Column Selector
│  ├─ Excel Column Values Helper (lazy loaded)
│  ├─ Value Input
│  ├─ Match Type Selector
│  ├─ Color Picker
│  └─ Action Buttons
├─ Color Presets Sub-Section
└─ Color Preview Sub-Section
```

### Active Filters Panel (Lines 4679-5100)
```
Tag Filters Card (expandable)
├─ Active Filters Section
│  ├─ Filter List (action badge + description + delete)
│  ├─ Add Filter Button
│  └─ Preview Tags Button
└─ Filter Builder (if open)
   ├─ Action Toggle (INCLUDE/EXCLUDE)
   ├─ Filter Type Selector
   ├─ Part/Column/Value Selector
   ├─ Excel Column Values Helper (lazy loaded)
   ├─ Value Input
   ├─ Match Type Selector
   └─ Action Buttons
```

### Excel Column Chooser (Embedded)
**Location**: Inside builders (not standalone)
```
Column Dropdown (excelColumns)
├─ onChange → fetch unique values
└─ Loading spinner + value buttons + "Show more"
```

---

## Helper Functions

### `getPartLabel(partNum)`
Converts 1-5 to A-E
```javascript
getPartLabel(2) → "B"
```

### `formatRuleDisplay(rule)`
Returns: `{action, actionClass, description}`
```javascript
// Example output:
{
  action: "INCLUDE",
  actionClass: "text-success bg-success/10",
  description: "Part B ≈ \"PUMP\""
}
```

### `formatFilterDisplay(filter)`
Same as above but for filters
```javascript
// Examples:
"Part B = \"PUMP\""
"Equipment Type ≈ \"Valve\""
"Value contains \"XYZ\""
```

---

## localStorage Keys

```javascript
// Color Presets (PERSISTED)
localStorage.getItem('colorPresets')
// Returns: { "presetName": { rules, defaultColor, ... }, ... }

// Note: Filters and tag matching settings are NOT persisted
```

---

## Loading States Pattern

### For Header Values
```javascript
// 1. User selects column
setRuleLoadingHeaderValues(true);

// 2. Render spinner
{ruleLoadingHeaderValues && <Spinner />}

// 3. After fetch
setRuleLoadingHeaderValues(false);
setRuleAvailableHeaderValues(data.values);

// 4. Show values
{!ruleLoadingHeaderValues && ruleAvailableHeaderValues.map(...)}
```

---

## Validation Checklist

### Before Adding Color Rule
- [x] Value not empty
- [x] Column selected (if header_column type)
- [x] Color selected

### Before Adding Filter
- [x] Value not empty
- [x] Column selected (if header_column type)
- [x] Match type selected

### Before Preview
- [x] Excel file selected
- [x] Tag column selected
- [x] At least one filter/rule configured

---

## Common Issues & Solutions

### Issue: Excel column values not loading
**Solution**: Check if `/get_header_unique_values` endpoint is called
- Add console.log in fetch
- Verify column name in excelColumns
- Check header_row value

### Issue: Filters not working
**Solution**: Check backend `apply_tag_filters()` logic
- Exclude filters checked first
- Include filters respect AND/OR logic
- Validate row_data for header_column filters

### Issue: Color preview blank
**Solution**: Check `/preview_color_rules` response
- Verify PDF/Excel files exist
- Check page_number bounds
- Ensure color rules valid

---

## Performance Tips

1. **Limit visible values**: Top 20 by default, "Show more" expands
2. **API limit**: Returns top 100 values max
3. **Lazy loading**: Values loaded only when column selected
4. **Caching**: Color presets cached in localStorage
5. **Debounce**: Consider debouncing column selection fetch

---

## Testing Checklist

- [ ] Add color rule (tag_part)
- [ ] Add color rule (header_column)
- [ ] Save color preset
- [ ] Load color preset
- [ ] Delete color preset
- [ ] Add filter (tag_part)
- [ ] Add filter (header_column)
- [ ] Preview filters
- [ ] Load header values
- [ ] Click value button (auto-fill)
- [ ] Show/hide all values toggle
- [ ] Move color rule up/down
- [ ] Delete color rule
- [ ] Clear all filters
- [ ] Clear all color rules

