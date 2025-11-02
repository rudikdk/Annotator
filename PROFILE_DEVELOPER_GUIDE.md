# Profile System Developer Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (React)                   │
│  Profile Selector → Preview Display → Profile Management   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/JSON
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                   Flask Backend (app.py)                    │
│                                                             │
│  Routes:                                                    │
│  ├─ GET  /get_builtin_templates        → List templates    │
│  ├─ GET  /load_profiles                → List saved        │
│  ├─ GET  /load_profile/<filename>      → Load one          │
│  ├─ POST /save_profile                 → Save             │
│  ├─ POST /preview_profile              → Generate preview  │
│  ├─ POST /export_profile               → Download JSON     │
│  ├─ POST /import_profile               → Upload JSON       │
│  └─ DELETE /delete_profile/<filename>  → Delete           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│           File System (./data/profiles/)                    │
│  ├─ profile_name1.json                                     │
│  ├─ profile_name2.json                                     │
│  └─ ...                                                     │
└─────────────────────────────────────────────────────────────┘
```

## Core Functions

### 1. Profile Preview Generation

**File:** `app.py:2039-2134`
**Function:** `generate_profile_preview(profile)`

```python
def generate_profile_preview(profile):
    """Generate a detailed human-readable preview of a profile"""

    # Input: profile dict with 'name', 'description', 'settings'
    # Output: preview dict with formatted display values
```

**Process Flow:**
```
Input Profile
  ↓
Validate structure
  ↓
Extract settings
  ↓
Format values for display
  ├─ Boolean → "Enabled"/"Disabled"
  ├─ List → "Item1, Item2"
  ├─ Integer → "Row X"
  └─ Hex color → "#RRGGBB"
  ↓
Calculate complexity score
  ├─ Excel annotation: +2
  ├─ Watermark: +3
  └─ Comments: +1
  ↓
Create detailed settings array
  ├─ Each setting gets: key, label, value, display_value, description
  ↓
Return formatted preview object
```

### 2. Profile Preview Endpoint

**File:** `app.py:2441-2466`
**Endpoint:** `POST /preview_profile`

```python
@app.route('/preview_profile', methods=['POST'])
def preview_profile():
    """Generate a detailed preview of a profile"""
    # Request: {"profile": {...}}
    # Response: {"success": true, "preview": {...}}
```

**Validation:**
- Checks for 'profile' key in JSON
- Calls `generate_profile_preview()`
- Returns formatted JSON response

### 3. Profile Management

**File:** `app.py:2138-2342`

#### GET /get_builtin_templates
```
get_builtin_templates()
  ↓
Return 5 pre-configured templates
```

#### GET /load_profiles
```
os.listdir(PROFILES_FOLDER)
  ↓ (for each .json file)
json.load(file)
  ↓
Add metadata (filename, builtin=False)
  ↓
Return array of profiles
```

#### POST /save_profile
```
request.get_json()
  ↓
validate_profile_data()
  ↓
Create profile object with metadata
  ↓
secure_filename(name) → sanitize path
  ↓
json.dump() → save to file
  ↓
Return success response
```

#### POST /import_profile
```
FormData upload
  ↓
file.read() → JSON content
  ↓
json.loads() → parse
  ↓
validate_profile_data()
  ↓
Add "imported_at" timestamp
  ↓
Save to profiles folder
  ↓
Return success response
```

## Data Structures

### Profile Object
```python
{
    "name": str,              # Profile display name
    "description": str,       # Optional description
    "version": str,           # "1.0"
    "created_at": str,        # ISO timestamp
    "imported_at": str,       # ISO timestamp (optional)
    "builtin": bool,          # True for built-in templates
    "filename": str,          # Sanitized filename (optional)
    "settings": {
        "header_row": int,
        "tag_column": str | null,
        "comment_columns": list[str],
        "highlight_column": str,
        "highlight_color": str,  # Hex color
        "annotate_excel": bool,
        "watermark_enabled": bool,
        "watermark_attributes": list[str],
        "watermark_text_color": str,  # Hex color
        "tag_matching_preset": str,    # Optional
        "tag_matching_custom_regex": str  # Optional
    }
}
```

### Preview Object
```python
{
    "name": str,
    "description": str,
    "builtin": bool,
    "created_at": str,
    "complexity": str,        # "Minimal" | "Moderate" | "Comprehensive"
    "complexity_score": int,  # 0-6
    "settings_detail": [
        {
            "key": str,                    # Setting identifier
            "label": str,                  # Display name
            "value": any,                  # Raw value
            "display_value": str,          # Formatted for display
            "description": str             # What it does
        },
        ...
    ]
}
```

## React State Management

**File:** `templates/index.html`

### State Variables
```javascript
const [selectedProfile, setSelectedProfile] = useState("");
const [profilePreview, setProfilePreview] = useState(null);
const [builtinTemplates, setBuiltinTemplates] = useState([]);
const [savedProfiles, setSavedProfiles] = useState([]);
```

### Key Functions

#### `loadProfilesAndTemplates()`
- Loads built-in templates from `/get_builtin_templates`
- Loads saved profiles from `/load_profiles`
- Updates state with both lists

#### `generateProfilePreview(profile)`
- POST request to `/preview_profile`
- Receives formatted preview data
- Updates `profilePreview` state
- Triggers re-render

#### `loadSelectedProfile()`
- Applies profile settings to form fields
- Updates all config values
- Logs action to console

#### `applyProfileSettings(settings)`
- Maps profile settings to React state
- Updates all UI form inputs
- Handles optional fields gracefully

### UI Components

#### Profile Selector
```jsx
<select
  value={selectedProfile}
  onChange={(e) => {
    // Update selection
    // Fetch preview
  }}
>
  {/* Built-in templates */}
  {/* Saved profiles */}
</select>
```

#### Preview Panel
```jsx
{profilePreview && (
  <div className="profile-preview">
    {/* Title + Badge */}
    {/* Settings Grid */}
    {/* Descriptions */}
  </div>
)}
```

## Setting Descriptions Map

**File:** `app.py:2044-2090`

Maps setting keys to human-readable descriptions:
```python
setting_descriptions = {
    'header_row': {
        'label': 'Header Row',
        'description': 'Which Excel row...',
        'value_formatter': lambda v: f'Row {v}'
    },
    'tag_column': {
        'label': 'Tag Column',
        'description': 'Excel column...',
        'value_formatter': lambda v: v if v else 'Auto-detect'
    },
    # ... more settings
}
```

**Formatter Functions:**
- Convert raw values to readable format
- Handle null/empty values
- Format lists, booleans, colors, etc.

## Complexity Scoring Algorithm

```python
complexity_score = 0

# Feature weights
if annotate_excel: score += 2    # Excel output
if watermark_enabled: score += 3 # Page watermarks
if comment_columns: score += 1   # Extra metadata

# Map to levels
0-1  → "Minimal"
2-4  → "Moderate"
5-6  → "Comprehensive"
```

**Rationale:**
- Watermarks are most computationally expensive
- Excel annotation adds moderate complexity
- Comments add minimal overhead

## File Storage & Security

### Path Handling
```python
PROFILES_FOLDER = APP_ROOT / 'data' / 'profiles'
os.makedirs(PROFILES_FOLDER, exist_ok=True)

# Filename sanitization
filename = secure_filename(name) + '.json'
filepath = os.path.join(PROFILES_FOLDER, filename)
```

### Security Measures
- `secure_filename()` prevents path traversal
- No access outside profiles folder
- `.json` extension enforced
- File validation on load

### File Format
```json
{
  "name": "Profile Name",
  "description": "Optional description",
  "version": "1.0",
  "created_at": "2025-01-23T10:30:00",
  "imported_at": "2025-01-23T10:35:00",  // If imported
  "settings": { ... }
}
```

## Validation System

**Function:** `validate_profile_data(data)` (app.py:2136-2175)

```python
Required fields:
├─ name (str)
└─ settings (dict with all keys)

Settings validation:
├─ header_row (int, > 0)
├─ comment_columns (list)
├─ annotate_excel (bool)
├─ watermark_enabled (bool)
└─ watermark_attributes (list)
```

**Returns:** `(is_valid: bool, message: str)`

## Error Handling

### API Errors
```python
try:
    # Operation
except Exception as e:
    return jsonify({
        'success': False,
        'message': f'Error: {str(e)}'
    })
```

### Frontend Errors
```javascript
.catch((err) => {
  setToast({ type: "error", text: err.message });
  logToConsole(`Error: ${err.message}`);
})
```

## Extending the System

### Adding a New Setting

1. **Backend (app.py):**
   ```python
   # Add to built-in templates
   "new_setting": value

   # Add to validation
   settings_fields.append('new_setting')

   # Add description
   setting_descriptions['new_setting'] = {
       'label': 'Display Name',
       'description': 'What it does',
       'value_formatter': lambda v: format_value(v)
   }
   ```

2. **Frontend (index.html):**
   ```javascript
   // Add state
   const [newSetting, setNewSetting] = useState(default)

   // Add to profile data
   settings: {
       // ... other settings
       new_setting: newSetting
   }

   // Apply from profile
   if (settings.new_setting !== undefined)
       setNewSetting(settings.new_setting)
   ```

### Custom Validation

```python
# In validate_profile_data()
if not isinstance(settings['new_setting'], expected_type):
    return False, "Invalid type for new_setting"
```

### Custom Formatters

```python
'new_setting': {
    'label': 'Label',
    'description': 'Desc',
    'value_formatter': lambda v: custom_format(v)
}
```

## Performance Considerations

### Preview Generation
- **Complexity:** O(n) where n = number of settings
- **Time:** ~5-10ms per profile
- **Bottleneck:** I/O (file read), not computation

### List Operations
- **Load profiles:** O(n) file reads
- **Filter templates:** O(1) in-memory lookup
- **Search profiles:** Linear search on name

### Caching Strategy
- Built-in templates cached in React state
- Profiles reloaded on save/import/delete
- Preview generated on-demand (fast enough)

## Testing Guide

### Unit Tests (Python)
```python
def test_generate_profile_preview():
    profile = get_builtin_templates()[0]
    preview = generate_profile_preview(profile)
    assert 'name' in preview
    assert 'complexity' in preview
    assert len(preview['settings_detail']) > 0

def test_validate_profile_data():
    valid_data = { ... }
    is_valid, msg = validate_profile_data(valid_data)
    assert is_valid is True
```

### Integration Tests (Frontend)
```javascript
// Test preview generation
const response = await fetch('/preview_profile', {
  method: 'POST',
  body: JSON.stringify({ profile })
})
const data = await response.json()
assert(data.success === true)
assert(data.preview.complexity !== undefined)

// Test profile loading
const profiles = await fetch('/load_profiles')
assert(Array.isArray(profiles.profiles))
```

### Manual Testing
1. Load each template → Verify preview appears
2. Modify settings → Save profile → Reload → Verify
3. Export profile → Import → Verify values match
4. Delete profile → Verify removed from list

## Debugging Tips

### Enable Logging
```javascript
// In browser console
localStorage.debug = 'pid-annotator:*'
```

### Check Network
```javascript
// Monitor API calls
window.fetch
// Check Response tab in DevTools
```

### Inspect State
```javascript
// React DevTools extension
// View profilePreview state
console.log(profilePreview)
```

### Backend Logging
```python
# Already in place
print(f"[PROFILE] Saved profile: {data['name']}")
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-23 | Initial implementation |

## Future Enhancements

1. **Profile Versioning**
   - Track changes over time
   - Rollback functionality

2. **Profile Validation**
   - Validate against Excel structure
   - Warn if columns don't exist

3. **Smart Defaults**
   - Auto-detect header row
   - Suggest tag column based on data

4. **Profile Merging**
   - Combine multiple profiles
   - Conflict resolution

5. **Cloud Sync**
   - Sync profiles across devices
   - Collaborative editing

---

**Last Updated:** 2025-01-23
**Difficulty Level:** Intermediate
**Related Files:** app.py, index.html, pid_annotator_core.py
