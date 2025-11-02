# Configuration Profiles Guide

## Overview

Configuration profiles in PID Annotator allow you to save and reuse annotation settings across multiple projects. Each profile encapsulates all your preferences for highlighting, watermarks, Excel annotations, and tag matching behavior.

## What Gets Saved in a Profile

### Core Annotation Settings
| Setting | Description | Example |
|---------|-------------|---------|
| **Header Row** | Which Excel row contains column headers | Row 6 (typical for many Excel templates) |
| **Tag Column** | Excel column containing component identifiers | "Tag" or auto-detected |
| **Comment Columns** | Additional Excel columns to include in PDF notes | Description, Location, Responsible |
| **Highlight Color** | Color used for PDF tag highlights | #FF0000 (Red), #FFFF00 (Yellow), #00FF00 (Green) |

### Excel Output Settings
| Setting | Description | Impact |
|---------|-------------|--------|
| **Annotate Excel** | Enable/disable highlighting found tags in Excel output | When enabled, found components are highlighted in green |
| **Highlight Column** | Excel column used for conditional highlighting | Can filter by status (Critical, Normal, etc.) |

### PDF Watermark Settings
| Setting | Description | Impact |
|---------|-------------|--------|
| **Watermark Enabled** | Enable/disable text watermarks on PDF pages | Adds metadata text to each PDF page |
| **Watermark Attributes** | Excel columns to include in watermark text | e.g., Component Location, Installation Date |
| **Watermark Color** | Text color for watermarks | Hex color code (#000000 = black) |

### Advanced Tag Matching
| Setting | Description | Default |
|---------|-------------|---------|
| **Tag Matching Preset** | Pre-configured tag matching rules | Standard (3-5 part hierarchical) |
| **Min/Max Parts** | Minimum and maximum tag parts allowed | 3-5 parts |
| **Separators** | Characters used to split tag parts | `-` (dash), `.` (dot) |
| **Part Length** | Min/max characters per tag part | 1-5 characters |
| **Custom Regex** | Custom regular expression for tag matching | Optional, overrides presets |

## Built-in Profile Templates

### 1. **Minimal Setup** (Fast & Simple)
**Best for:** Quick reviews of small PDFs
- **Highlights:** Yellow only
- **Excel Annotation:** Disabled
- **Watermarks:** Disabled
- **Use case:** Testing configurations, quick visual checks

```
Complexity: Minimal
Processing Speed: Fastest
Features: PDF highlights only
```

### 2. **Standard Documentation** (Balanced)
**Best for:** Most documentation and annotation tasks
- **Highlights:** Yellow with optional comments
- **Excel Annotation:** Disabled
- **Watermarks:** Disabled
- **Use case:** Adding notes to highlighted components

```
Complexity: Minimal
Processing Speed: Fast
Features: PDF highlights + optional comments
```

### 3. **Quick Review** (Testing Mode)
**Best for:** Validating configurations before production
- **Highlights:** Green (visually distinct)
- **Excel Annotation:** Disabled
- **Watermarks:** Disabled
- **Use case:** Configuration validation, test runs

```
Complexity: Minimal
Processing Speed: Fastest
Features: PDF highlights only (test color)
```

### 4. **Excel Focus** (Excel-Centric)
**Best for:** Projects where Excel is the primary deliverable
- **Highlights:** Light green
- **Excel Annotation:** Enabled
- **Watermarks:** Disabled
- **Use case:** Tracking found components in Excel

```
Complexity: Moderate
Processing Speed: Fast
Features: PDF highlights + Excel annotation
```

### 5. **Production Ready** (Full Featured)
**Best for:** Final deliverables requiring comprehensive documentation
- **Highlights:** Red (high visibility)
- **Excel Annotation:** Enabled
- **Watermarks:** Enabled
- **Use case:** Complete project documentation

```
Complexity: Comprehensive
Processing Speed: Moderate
Features: All options enabled
```

## Creating Custom Profiles

### Step 1: Configure Settings
1. Open PID Annotator
2. Select a starting template or configure from scratch
3. Adjust all settings as needed:
   - Set the correct Excel header row
   - Choose tag and comment columns
   - Select highlight color
   - Configure watermark attributes
   - Set tag matching rules

### Step 2: Save Profile
1. Click **"Save New"** button in the Profile Management section
2. Enter a descriptive profile name
   - Good: "Production_US_East_Facility"
   - Avoid: "My Config 1"
3. Optionally add a description
   - Example: "Red highlights with location watermarks for US East facility"
4. Click **"Save"**

### Step 3: Reuse Profile
1. Select your saved profile from dropdown
2. View the preview to confirm settings
3. Click **"Load"** to apply all settings
4. Upload files and process

## Understanding Profile Preview

When you select a profile, a preview panel shows:

### Profile Header
- **Name:** Profile display name
- **Description:** User-provided description of the profile's purpose
- **Complexity Badge:**
  - 🟢 **Minimal** - Basic highlighting only
  - 🟡 **Moderate** - Mix of features (e.g., highlighting + Excel annotation)
  - 🔴 **Comprehensive** - All features enabled (watermarks + Excel + comments)

### Settings Grid
Each setting shows:
- **Setting Name** - e.g., "Highlight Color"
- **Current Value** - e.g., "#FF0000" or "Row 6"
- **Description** - What this setting does

## Sharing Profiles

### Export Profile
1. Select your profile
2. Click **"Export"**
3. Save the `.json` file to your computer
4. Share via email, cloud storage, or version control

### Import Profile
1. Click **"Import Profile"** in the Profile Management section
2. Select a `.json` profile file
3. Profile is validated and saved locally
4. Now available in your profile list

## Profile Best Practices

### Naming Convention
- Use descriptive names with context
- Include facility/project name if relevant
- Examples:
  - ✅ `Production_RedHighlight_WithWatermarks`
  - ✅ `TestRun_YellowHighlight_Minimal`
  - ✅ `ClientA_GreenHighlight_ExcelOnly`
  - ❌ `Profile1`, `My Config`, `Test`

### Version Control
- Keep exported profiles in version control
- Version your profiles along with your Excel templates
- Document changes in commit messages

### Testing Workflow
1. Create a "TestRun" profile with Minimal complexity
2. Test with your Excel and PDF files
3. Validate results
4. Copy to production profile when ready

### Multi-Project Setup
Create separate profiles for each:
- Different facilities or locations
- Different client requirements
- Different processing priorities

Example structure:
```
profiles/
├── Test_Minimal.json
├── Production_Facility_A.json
├── Production_Facility_B.json
├── Client_UK_Emphasis.json
└── Archive_Project_2024.json
```

## Troubleshooting Profile Issues

### Profile Won't Load
- Check that all required Excel columns exist
- Verify header row number matches your Excel file
- Ensure tag format matches the regex pattern

### Preview Not Showing
- Make sure a profile is selected
- Check browser console for errors
- Refresh the page and try again

### Changes Not Applied
- Profile loads settings but doesn't create files yet
- Upload PDF and Excel files after loading profile
- Click "Load" button (not just selecting the dropdown)

### Tag Matching Not Working
- Verify tag format matches the regex pattern
- Check min/max parts constraints
- Use "Quick Review" template to test with visual feedback

## Profile Storage

### Local Storage
- Profiles stored in: `./data/profiles/` directory
- File format: JSON
- Files named: `{profile_name}.json` (with special characters sanitized)
- Accessed in: `Profile Management` section of UI

### Backup
Periodically backup your profiles:
```bash
# Backup all profiles
cp -r data/profiles/ data/profiles_backup/
```

## Advanced: Customizing Tag Matching

Profiles support advanced tag matching configuration:

### Presets Available
- **Standard** (Default) - 3-5 part tags like A-B-C or SYS.PUMP.01
- **Permissive** - 2-6 parts, allows various separators
- **Strict** - Exactly 4 parts, specific format
- **Custom** - Define your own regex pattern

### Custom Regex Example
Pattern matching tags like `TANK_001_A`:
```regex
\b[A-Z]+_\d{3}_[A-Z]\b
```

When using custom regex:
1. Test thoroughly with sample PDFs
2. Save as separate profile for testing
3. Document the regex pattern in description

## Environment-Specific Profiles

### Development
- **Minimal Setup** for quick testing
- Green highlights for easy visibility
- No watermarks (faster processing)

### Staging
- **Standard Documentation** with comments
- Yellow highlights
- Excel annotation enabled for tracking

### Production
- **Production Ready** with all features
- Red highlights for emphasis
- Watermarks with location/date information
- Excel annotation for final tracking

## Integration with CI/CD

Profiles work well with automated workflows:

1. **Export** your production profile
2. **Commit** to version control with your Excel template
3. **Share** across team via repository
4. **Import** in CI/CD pipelines for consistent processing

Example structure in repo:
```
project/
├── config/
│   └── annotation_profile.json
├── templates/
│   └── component_list.xlsx
└── README.md
```

## Tips & Tricks

### Copy & Modify
1. Export a built-in template
2. Modify in JSON editor
3. Change name and description
4. Import as new profile
5. Customize further in UI

### Quick Validation
1. Load "Quick Review" template
2. Process one PDF with your Excel
3. Check results before production

### Color Consistency
Use standard colors across team:
- Red (#FF0000) - Critical components
- Yellow (#FFFF00) - Important components
- Green (#00FF00) - Standard components
- Orange (#FFA500) - Warning/Caution

### Watermark Strategy
Include in watermarks:
- Component location/area
- Installation date
- Responsible technician
- Facility identifier

## Support & Feedback

For issues or feature requests:
- GitHub: https://github.com/rudikdk/PID-Annotator
- Contact: rudikdk@gmail.com

---

**Last Updated:** 2025-01-23
**Version:** 1.0
