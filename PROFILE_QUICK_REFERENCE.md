# Profile Quick Reference

## Quick Start

### Load a Template (30 seconds)
1. Open **Profile Management**
2. Select a built-in template from dropdown
3. Preview appears → Shows what it does
4. Click **"Load"** button
5. Upload files and process

### Save Your Configuration (1 minute)
1. Adjust all settings in the UI
2. Click **"Save New"** button
3. Enter profile name: `MyProject_ProductionSetup`
4. Add description: `Red highlights with location watermarks`
5. Click **"Save"**
6. Profile available for reuse

### Share with Team (30 seconds)
1. Select your profile
2. Click **"Export"**
3. Send `.json` file to team member
4. They click **"Import Profile"** and upload file
5. Profile ready to use

---

## When to Use Each Template

```
MINIMAL SETUP
├─ Use: Quick PDF reviews
├─ Best for: Testing configurations
├─ Output: PDF with yellow highlights only
└─ Speed: ⚡ Fastest

STANDARD DOCUMENTATION
├─ Use: Most annotation tasks
├─ Best for: Adding notes to PDFs
├─ Output: PDF with highlights + optional comments
└─ Speed: ⚡ Fast

QUICK REVIEW
├─ Use: Configuration validation
├─ Best for: Test runs before production
├─ Output: PDF with green highlights (test color)
└─ Speed: ⚡ Fastest

EXCEL FOCUS
├─ Use: Track found components
├─ Best for: Excel-first workflows
├─ Output: PDF highlights + Excel annotation
└─ Speed: ⚡⚡ Moderate

PRODUCTION READY
├─ Use: Final deliverables
├─ Best for: Complete documentation
├─ Output: PDF + watermarks + Excel annotation
└─ Speed: ⚡⚡ Moderate
```

---

## Profile Settings Explained (Simple Version)

| Setting | What It Does | Example |
|---------|-------------|---------|
| **Header Row** | Tells app which Excel row has column names | Row 6 |
| **Tag Column** | Which column has component IDs | "Tag" or auto |
| **Comment Columns** | Extra Excel columns to show in PDF | Description, Location |
| **Highlight Color** | PDF tag color | #FF0000 (red) |
| **Annotate Excel** | Highlight found tags in Excel | On/Off |
| **Watermark** | Add text to PDF pages | On/Off |
| **Watermark Text** | What to write on pages | Location, Date, etc. |

---

## Profile Complexity Levels

### 🟢 MINIMAL (Fastest)
- PDF highlights only
- No Excel changes
- No watermarks
- Perfect for: Quick tests, visual checks
- Processing: <5 seconds per PDF

### 🟡 MODERATE (Balanced)
- PDF highlights + Excel annotation
- OR highlights + watermarks
- Some Excel changes
- Perfect for: Production workflows
- Processing: 5-15 seconds per PDF

### 🔴 COMPREHENSIVE (Full Featured)
- PDF highlights + watermarks + Excel annotation
- All features enabled
- Perfect for: Final deliverables
- Processing: 10-20 seconds per PDF

---

## Decision Tree: Which Profile to Use

```
Start Here
   ↓
Is this for production?
   ├─ NO → Use "Quick Review" (test mode)
   └─ YES ↓
     Do you need Excel highlighting?
        ├─ NO → Use "Standard Documentation"
        └─ YES ↓
          Do you need watermarks?
             ├─ NO → Use "Excel Focus"
             └─ YES → Use "Production Ready"
```

---

## Common Profile Configurations

### Scenario 1: Fast Checking
```
Template: Minimal Setup
Changes: None needed
Highlight Color: Yellow
Time: 30 seconds per PDF
```

### Scenario 2: Documentation with Notes
```
Template: Standard Documentation
Changes: Add comment columns (Description, Location)
Highlight Color: Yellow
Time: 1 minute per PDF
```

### Scenario 3: Excel Tracking
```
Template: Excel Focus
Changes: Enable Excel annotation, set highlight color
Highlight Color: Light Green
Time: 1-2 minutes per PDF
```

### Scenario 4: Production Delivery
```
Template: Production Ready
Changes: Set watermark attributes (Location, Date, Responsible)
Highlight Color: Red
Time: 2-3 minutes per PDF
```

---

## Complexity Score Calculation

```
Base Score = 0

If Excel Annotation Enabled: +2
If Watermark Enabled: +3
If Comment Columns Added: +1

Results:
0-1 → Minimal (🟢)
2-4 → Moderate (🟡)
5-6 → Comprehensive (🔴)
```

---

## Profile Colors Guide

| Color | Hex | Use Case |
|-------|-----|----------|
| 🔴 Red | #FF0000 | Critical components, high priority |
| 🟡 Yellow | #FFFF00 | Standard annotations, general use |
| 🟢 Green | #00FF00 | Testing, validation, normal priority |
| 🟠 Orange | #FFA500 | Warning components, caution items |
| 🔵 Blue | #0000FF | Special components, references |

---

## Naming Patterns for Custom Profiles

### ✅ Good Names
- `Production_Facility_A_RedHighlight`
- `TestRun_YellowHighlight_NoWatermark`
- `Client_ProjectX_GreenHighlight_ExcelFocus`
- `Archive_2024_Q1_Complete`

### ❌ Avoid
- `Profile1`, `Config2`, `Test`
- `My Setup`, `Untitled`
- Ambiguous project names

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Load Profile | (Planned) `Ctrl+L` |
| Save Profile | (Planned) `Ctrl+S` |
| Export Profile | (Planned) `Ctrl+E` |
| Import Profile | (Planned) `Ctrl+I` |

---

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| Preview not showing | Select a profile from dropdown |
| Can't find column | Check Excel header row is correct |
| Highlights wrong color | Reload profile after changing color |
| Export button disabled | Make sure profile is saved (not template) |
| Tags not matching | Check tag format matches regex pattern |

---

## Profile File Format

Profiles are JSON files:
```json
{
  "name": "My Profile",
  "description": "What it does",
  "version": "1.0",
  "created_at": "2025-01-23T10:30:00",
  "settings": {
    "header_row": 6,
    "tag_column": "Tag",
    "comment_columns": ["Description"],
    "highlight_column": "",
    "highlight_color": "#FFFF00",
    "annotate_excel": false,
    "watermark_enabled": false,
    "watermark_attributes": [],
    "watermark_text_color": "#000000"
  }
}
```

---

## Pro Tips

1. **Create Test Profiles**
   - Save a "TestRun" profile
   - Use green highlights for visibility
   - Validate configs safely

2. **Version Your Profiles**
   - `MyProject_v1_Initial`
   - `MyProject_v2_MoreComments`
   - Track evolution of configurations

3. **Document Everything**
   - Use descriptive names
   - Add detailed descriptions
   - Helps team understand intent

4. **Regular Backups**
   - Export important profiles monthly
   - Store in version control
   - Protect against data loss

5. **Standardize Colors**
   - Red = Critical
   - Yellow = Standard
   - Green = Test/Normal
   - Team consistency matters

---

## Common Mistakes to Avoid

❌ **Don't:** Create profile named "Config1"
✅ **Do:** Name it `Production_RedHighlight_WithWatermarks`

❌ **Don't:** Use "Minimal" template then complain it has no Excel output
✅ **Do:** Use "Excel Focus" or "Production Ready" for Excel features

❌ **Don't:** Save a profile without testing it first
✅ **Do:** Test with sample files, then save configuration

❌ **Don't:** Share profiles without adding description
✅ **Do:** Include what it does and when to use it

❌ **Don't:** Use custom regex without testing
✅ **Do:** Test with sample PDFs first, verify matches

---

## Where to Find Everything

| Item | Location |
|------|----------|
| Profile Manager | Settings → Profile Management |
| Save Profile | Click "Save New" button |
| Load Profile | Select from dropdown, click "Load" |
| Export Profile | Select profile, click "Export" |
| Import Profile | Click "Import Profile" button |
| Guide (Detailed) | `CONFIGURATION_PROFILES_GUIDE.md` |
| This Document | `PROFILE_QUICK_REFERENCE.md` |

---

## Related Documentation

- **Full Guide:** `CONFIGURATION_PROFILES_GUIDE.md`
- **Improvements:** `PROFILE_IMPROVEMENTS_SUMMARY.md`
- **Project README:** `README.md`
- **Architecture:** `CLAUDE.md`

---

**Need more help?** See `CONFIGURATION_PROFILES_GUIDE.md` for comprehensive information.

Last Updated: 2025-01-23
