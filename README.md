# PID Annotator Web Application

A powerful web-based tool for automatically annotating P&ID (Piping & Instrumentation Diagram) PDF documents with metadata from Excel component lists. Optimized for Raspberry Pi 5 deployment with Docker/CasaOS, but works on any system with Docker support.

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [HTML Report Generation](#html-report-generation)
- [Common Workflows](#common-workflows)
- [Interactive Tutorial](#interactive-tutorial)
- [Configuration](#configuration)
- [Configuration Profiles](#configuration-profiles)
- [Performance & Optimization](#performance--optimization)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Known Limitations](#known-limitations)
- [Support](#support)
- [Recent Updates](#recent-updates)

---

## Features

- **Same Functionality**: Identical features to the desktop version
- **Web Interface**: Modern, responsive web UI with dark theme
- **Real-time Progress**: Live progress updates via WebSockets
- **File Upload**: Drag & drop support for PDF and Excel files
- **Multi-File Processing**: Support for multiple PDFs with single Excel file
- **Excel Annotation**: Automatically highlights found tags in Excel file
- **HTML Report Generation**: Interactive reports with search, sort, filter, and Excel export
- **Configuration Profiles**: Save/load configuration presets with built-in templates
- **Interactive Tutorial**: Step-by-step onboarding for new users
- **Performance Optimized**: Adaptive processing with parallel indexing and streaming for large files
- **Docker Ready**: Optimized for ARM64 architecture (Raspberry Pi 5) and AMD64
- **CasaOS Compatible**: Easy deployment on CasaOS systems
- **Session-Based**: Isolated file processing per user with UUID sessions
- **Auto-Cleanup**: Automatic file cleanup after 24 hours

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Raspberry Pi 5 with 64-bit OS (recommended) or any Linux/Windows system
- At least 2GB RAM available
- Python 3.11+ (for local development)

### Deployment

1. **Clone or copy the application files to your system**

2. **Build and run with Docker Compose:**
   ```bash
   cd Annotator
   docker-compose up -d --build
   ```

3. **Access the application:**
   - Open your browser and go to: `http://your-ip:8080`
   - The application will be available on port 8080 by default

**For Raspberry Pi 5 specific quick start, see [RASPBERRY_PI_QUICKSTART.md](RASPBERRY_PI_QUICKSTART.md)**

### Manual Docker Build

If you prefer to build manually:

```bash
# Build the image
docker build -t pid-annotator-web .

# Run the container
docker run -d \
  --name pid-annotator-web \
  -p 8080:8080 \
  -v $(pwd)/persistent_uploads:/app/uploads \
  -v $(pwd)/persistent_output:/app/output \
  --restart unless-stopped \
  pid-annotator-web
```

## Usage

1. **First-Time Users - Tutorial:**
   - An interactive tutorial will automatically start on your first visit
   - Follow the step-by-step guide to learn all features
   - You can replay the tutorial anytime from the FAQ section
   - Tutorial can be skipped if you're already familiar

2. **Upload Files:**
   - Drag & drop or click to upload your PID PDF file(s) - supports multiple PDFs
   - Drag & drop or click to upload your Excel component list (one Excel file)

3. **Quick Setup with Profiles:**
   - **Load Built-in Templates**: Choose from 5 pre-configured templates
     - Minimal Setup
     - Standard Documentation
     - Production Ready
     - Quick Review
     - Excel Focus
   - **Save Custom Profiles**: Save your current settings for reuse
   - **Export/Import**: Share profiles with team members as JSON files

4. **Configure Settings (Manual or from Profile):**
   - Set the header row (default: 6)
   - Select the tag column
   - Choose comment columns to include
   - Configure highlighting colors
   - Enable/disable watermark feature
   - Enable/disable Excel annotation (highlights found tags)

5. **Process:**
   - Click "Start" for full processing
   - Click "Test Run" to process only 100 tags for testing

6. **Download:**
   - Download the annotated PDF(s) when processing completes
   - Download the annotated Excel file if Excel annotation is enabled
   - Download the interactive HTML report for detailed analysis
   - Files are automatically cleaned up after 24 hours

---

## HTML Report Generation

### Interactive Processing Reports

After processing completes, the application automatically generates a comprehensive **HTML Report** that provides detailed analysis of the annotation process:

#### Report Features

1. **Visual Dashboard**
   - Summary statistics with color-coded cards
   - Found vs. Not Found tags with percentages
   - Duplicate tag detection
   - Validation warnings count

2. **Interactive Data Tables**
   - **Found Tags Table**: Shows tag name, pages found, bookmarks, occurrence count, and Excel row
   - **Not Found Tags Table**: Lists missing tags with reasons
   - **Duplicate Tags Table**: Identifies tags appearing multiple times in Excel
   - **Validation Warnings Table**: Highlights potential data issues

3. **Search & Filter**
   - Real-time search across all tables
   - Filter by any column value
   - Instant results as you type

4. **Sortable Columns**
   - Click column headers to sort ascending/descending
   - Works on all columns (tags, pages, occurrences, etc.)
   - Numeric and alphabetic sorting supported

5. **Export Capabilities**
   - **Excel Export**: Download filtered data to Excel with formatting
   - **Print-Ready**: Optimized for printing with clean layout
   - **Collapsible Sections**: Hide/show sections for focused viewing

6. **Bookmark Integration**
   - Shows PDF bookmark names where tags were found
   - Helps locate tags in specific sections (e.g., "Sheet 1", "Process Flow")
   - Displays "N/A" for tags not found in bookmarks

#### Report Contents

**Summary Section:**
- Total tags processed
- Found tags (count and percentage)
- Not found tags (count and percentage)
- Duplicate tags detected
- Validation warnings

**Found Tags Details:**
- Tag identifier
- Page numbers where found (comma-separated list)
- Bookmark names (section/drawing references)
- Number of occurrences in PDF
- Corresponding Excel row number

**Not Found Tags Details:**
- Tag identifier
- Excel row number
- Reason (e.g., "not_in_pdf", "invalid_format")

**Duplicate Tags Details:**
- Tag identifier
- Excel row numbers (all occurrences)
- Total count of duplicates

**Validation Warnings:**
- Tag identifier
- Excel row number
- Warning message (e.g., "Tag format invalid", "Missing required field")

**Processing Settings:**
- Tag column used
- Header row configuration
- Watermark status
- Excel annotation status

#### Using the Report

1. **Download the Report**
   - After processing completes, click "Download HTML Report"
   - Opens in any modern web browser (Chrome, Firefox, Safari, Edge)
   - No internet connection required (fully self-contained)

2. **Search for Specific Tags**
   - Type in the search box at the top
   - Results filter in real-time across all tables
   - Clear search to restore full view

3. **Sort Data**
   - Click column headers to sort
   - First click: ascending order
   - Second click: descending order
   - Visual indicator shows sorted column

4. **Export Filtered Data**
   - Apply search filters as needed
   - Click "Export Filtered Data (Excel)"
   - Downloads Excel file with only visible/filtered rows
   - Includes all sections (Found, Not Found, Duplicates, Warnings)

5. **Collapse/Expand Sections**
   - Click section headers to collapse/expand
   - Useful for focusing on specific data
   - All sections expanded when printing

6. **Print Report**
   - Click "Print Report" button
   - Auto-formatted for clean printing
   - All sections visible in print mode
   - Headers and footers included

#### Technical Details

- **Format**: Self-contained HTML file with embedded CSS and JavaScript
- **Dependencies**: Uses SheetJS library (CDN) for Excel export
- **File Size**: Typically 200-500 KB depending on tag count
- **Browser Compatibility**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Offline Usage**: Fully functional offline (Excel export requires internet for CDN)

#### Example Use Cases

**Quality Control:**
- Review which tags were successfully annotated
- Identify patterns in not-found tags
- Detect duplicate entries in source data
- Validate Excel file structure

**Project Reporting:**
- Share processing results with team
- Document annotation coverage
- Track missing tags for follow-up
- Provide evidence of processing completeness

**Troubleshooting:**
- Identify why specific tags weren't found
- Check tag format consistency
- Verify Excel structure issues
- Review validation warnings

**Data Analysis:**
- Export found tags to Excel for further analysis
- Compare bookmark locations across tags
- Analyze occurrence patterns
- Generate metrics for documentation quality

---

## Common Workflows

### Workflow 1: Quick Test Run with Built-in Template

Perfect for first-time users or quick validation:

1. **Upload Files**
   - Upload your Excel component list
   - Upload one or more P&ID PDF files

2. **Load Template**
   - Click "Configuration Profiles" section
   - Select "Quick Review" from dropdown
   - Click "Load Profile"

3. **Test Run**
   - Click "Test Run" button (processes first 100 tags only)
   - Review results in ~10-30 seconds
   - Download annotated PDF to verify

4. **Full Processing**
   - If satisfied, click "Start" for complete processing
   - Download all annotated files when complete

### Workflow 2: Production-Ready with Custom Settings

For production documentation with all features:

1. **Upload & Configure**
   - Upload your Excel and PDF files
   - Set header row to match your Excel structure
   - Select the tag column containing component IDs

2. **Configure Features**
   - **Comment Columns**: Select all relevant data columns (Description, Location, etc.)
   - **Conditional Highlighting**: Choose attribute column and highlight color
   - **Excel Annotation**: Enable to highlight found tags in Excel
   - **Watermark**: Enable and select attributes to display near tags

3. **Save Profile**
   - Click "Save" in Configuration Profiles
   - Name it (e.g., "Project XYZ Standard")
   - Add description for team reference
   - Export as JSON for team sharing

4. **Process & Download**
   - Click "Start" for full processing
   - Monitor real-time progress
   - Download annotated PDFs and Excel file

### Workflow 3: Batch Processing Multiple PDFs

Process an entire project's P&ID set:

1. **Upload Multiple PDFs**
   - Drag and drop all PDF files at once
   - Upload single Excel file with all tags
   - Verify all PDFs are selected (checkboxes)

2. **Load Saved Profile**
   - Select your project profile from dropdown
   - Click "Load" to apply all settings instantly

3. **Batch Process**
   - Click "Start"
   - Progress shown for all files combined
   - Each PDF processed sequentially

4. **Download All**
   - Download each annotated PDF individually
   - Or download the zip of all files (if available)

### Workflow 4: Troubleshooting Tag Matching

When tags aren't being found:

1. **Run Test Mode**
   - Use "Test Run" with 100 tags
   - Review which tags were found/not found

2. **Check Excel**
   - Verify header row is correct
   - Ensure tag column selected correctly
   - Check for extra spaces or formatting

3. **Check Tag Format**
   - Verify delimiter (hyphen `-` vs period `.`)
   - Ensure 3-5 part hierarchy (A-B-C or A-B-C-D-E)
   - Check case consistency

4. **Adjust & Retest**
   - Clear previous files
   - Re-upload with corrections
   - Run another test to verify

### Workflow 5: Quality Analysis with HTML Report

Analyze processing results for quality control:

1. **Complete Processing**
   - Upload files and configure settings
   - Run full processing (not test mode)
   - Wait for completion notification

2. **Download HTML Report**
   - Click "Download HTML Report" button
   - Open report in web browser
   - Review summary dashboard

3. **Analyze Results**
   - **Success Rate**: Check percentage of found vs. not found tags
   - **Duplicates**: Review duplicate tags table for data quality issues
   - **Warnings**: Check validation warnings for potential problems
   - **Bookmarks**: Review where tags were found (section references)

4. **Search & Filter**
   - Search for specific tag patterns
   - Sort by occurrence count to find frequently used tags
   - Filter by Excel row to cross-reference source data

5. **Export Findings**
   - Apply filters to show only relevant data
   - Click "Export Filtered Data (Excel)"
   - Share Excel file with team for review
   - Use exported data for follow-up corrections

6. **Take Action**
   - **High Not Found Rate**: Review tag format in PDF
   - **Many Duplicates**: Clean up source Excel file
   - **Validation Warnings**: Fix Excel structure issues
   - **Bookmark Anomalies**: Verify PDF structure

---

## Interactive Tutorial

### First-Time User Experience

The PID Annotator includes a **comprehensive interactive tutorial** that automatically launches for new users:

- **Auto-Start**: Appears 1 second after first page load (can be skipped)
- **10 Step Guide**: Covers all features from file upload to downloading results
- **Smart Positioning**: Tooltips appear next to the features they explain with animated arrows
- **Animated Spotlight**: Highlights target elements with pulsing effects
- **Keyboard Navigation**: Use arrow keys (←/→) to navigate, ESC to skip
- **Persistent Tracking**: Tutorial completion stored in browser localStorage

### Tutorial Features

1. **Dynamic Tooltips**
   - Positioned intelligently near target elements
   - Arrow pointers connect tooltip to feature
   - Viewport boundary detection prevents off-screen placement
   - Smooth transitions and fade-in animations

2. **Interactive Elements**
   - Spotlight effect highlights current feature
   - Progress dots show current step (e.g., 3 of 10)
   - Next/Previous navigation buttons
   - Skip option available anytime

3. **Keyboard Shortcuts**
   - `→` or `Enter`: Next step
   - `←`: Previous step
   - `ESC`: Skip tutorial
   - Hints displayed in bottom-right corner

4. **Replayable**
   - Access anytime from FAQ modal
   - Click "Start Tutorial" button
   - Perfect for training new team members

### Tutorial Coverage

The tutorial walks through:
- File upload area (drag & drop)
- Header row configuration
- Tag column selection
- Configuration profiles and templates
- Comment columns selection
- Conditional highlighting
- Excel annotation feature
- Watermark feature
- Start vs Test Run buttons
- FAQ and help resources

---

## Performance & Optimization

### Adaptive Processing Modes

The application automatically selects the optimal processing mode based on file size:

1. **Standard Mode** (< 50MB)
   - Fast, memory-loaded processing
   - Best for small to medium PDFs
   - Full document loaded in memory

2. **Streaming Mode** (≥ 50MB)
   - Chunk-based processing for large files
   - Reduced memory footprint
   - Document close/reopen between phases

3. **Parallel Indexing** (> 20 pages)
   - Multi-threaded page processing
   - Utilizes CPU cores efficiently
   - Configurable worker threads

### Performance Configuration

See [pid_annotator_core.py](pid_annotator_core.py) for configuration:

```python
PARALLEL_INDEXING_ENABLED = True       # Multi-core processing
MAX_WORKERS = os.cpu_count() - 1       # CPU cores to use
STREAMING_THRESHOLD_MB = 50            # File size for streaming mode
MEMORY_CLEANUP_BATCH_SIZE = 100        # Pages between gc.collect()
PROGRESS_UPDATE_INTERVAL = 2           # Progress update frequency (%)
```

### Benchmarks

Real-world performance (measured on Raspberry Pi 5):

| File Size | Pages | Processing Time | Mode |
|-----------|-------|----------------|------|
| 5MB | 10 | ~7 seconds | Standard |
| 25MB | 100 | ~18 seconds | Standard + Parallel (2.5x faster) |
| 80MB | 500 | ~2:30 minutes | Streaming + Parallel |
| 200MB | 1000 | ~6 minutes | Streaming + Parallel |

For more details, see [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md).

## Configuration

### Port Configuration

**Standard Port**: 8080

- **Internal container port**: 8080 (Dockerfile EXPOSE 8080)
- **Default external port**: 8080 (docker-compose.yml)
- **CasaOS configurable**: Change external port in CasaOS UI

**Port Mapping Examples**:
- `8080:8080` - Direct mapping (default)
- `9000:8080` - Custom external port 9000
- `YOUR_PORT:8080` - Any available port you choose

**Accessing the Application**:
- **Default**: `http://your-ip:8080`
- **Custom port**: `http://your-ip:YOUR_PORT` (if you changed the external port)
- **Local development**: `http://localhost:5001` (Flask debug server)

**Changing the Port**:

Edit `docker-compose.yml`:
```yaml
ports:
  - "9000:8080"  # Use external port 9000 instead of 8080
```

Then restart the container:
```bash
docker-compose down
docker-compose up -d
```

### Resource Limits

The application is configured with resource limits suitable for Raspberry Pi 5:

**4GB Model (Default)**:
- Memory limit: 1792MB (1.75GB)
- Memory reservation: 512MB
- CPU limit: 2.5 cores
- Gunicorn workers: 1

**8GB Model (Recommended changes)**:
- Memory limit: 2560MB (2.5GB)
- Memory reservation: 768MB
- CPU limit: 3.0 cores
- Gunicorn workers: 2

To configure for 8GB model, edit `docker-compose.yml`:
```yaml
environment:
  - GUNICORN_WORKERS=2  # Change from 1 to 2
mem_limit: 2560m  # Change from 1792m
mem_reservation: 768m  # Change from 512m
cpus: 3.0  # Change from 2.5
```

### Persistent Storage

The following directories are mounted for persistent data:
- `./persistent_uploads` → `/app/uploads` (uploaded files)
- `./persistent_output` → `/app/output` (generated PDFs)

### Tag Format Support

The application accepts tags in multiple formats:
- Delimiter support: `-` and `.` (e.g., `A-B-C` or `A.B.C`)
- Hierarchical tags: 3-5 parts (e.g., `TAG-001-A`, `SYS.PUMP.01`)
- Case-insensitive matching
- Multiple variant lookup

## Architecture

### Technology Stack

- **Backend**: Flask with SocketIO for real-time updates
- **Frontend**: HTML5, CSS3, JavaScript with Bootstrap
- **PDF Processing**: PyMuPDF (same as desktop version)
- **Excel Processing**: pandas + openpyxl (same as desktop version)
- **Containerization**: Docker with multi-stage build
- **Web Server**: Gunicorn with eventlet workers

### File Structure

```
pid-web-app/
├── app.py                 # Main Flask application
├── pid_annotator_core.py  # Core processing logic (from desktop app)
├── templates/
│   └── index.html         # Web interface
├── static/               # Static assets (auto-created)
├── uploads/              # Temporary file uploads
├── output/               # Generated PDF files
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container build instructions
├── docker-compose.yml   # Docker Compose configuration
├── entrypoint.sh        # Container startup script with safety checks
├── .dockerignore        # Docker build exclusions
└── README.md           # This file
```

### Key Architectural Patterns

1. **Session Isolation**
   - Each client gets UUID session ID
   - Files namespaced per session: `{session_id}_{original_filename}`
   - Prevents cross-user file conflicts

2. **Background Task Processing**
   - Long operations run in separate threads
   - Non-blocking HTTP responses
   - Real-time progress via WebSocket emissions

3. **Memory Management**
   - Explicit garbage collection every 100 pages
   - PyMuPDF cache shrinking: `fitz.TOOLS.store_shrink(100)`
   - Document close/reopen between phases in streaming mode
   - MALLOC_ARENA_MAX=2 to reduce memory fragmentation

4. **Watermark Implementation**
   - ReportLab generates overlay PDF
   - PyPDF2 merges overlay onto base PDF
   - Handles page rotations by drawing on unrotated canvas

5. **Configuration Profiles System**
   - JSON-based profile storage in `./data/profiles/`
   - Built-in templates embedded in application
   - Profile validation ensures data integrity
   - Session-independent persistence

6. **Interactive Tutorial System**
   - LocalStorage tracking for completion status
   - Auto-trigger for first-time users (dismissible)
   - Step-by-step overlay with spotlight effects
   - Replayable from FAQ section

7. **Entrypoint Safety Checks** (entrypoint.sh)
   - Architecture verification (ARM64 check)
   - Memory availability validation
   - Disk space monitoring
   - CPU temperature checks (Raspberry Pi)
   - Port and worker count validation
   - Automatic permission fixes for mounted volumes
   - Comprehensive startup logging

## Configuration Profiles

### Built-in Templates

The application includes 5 pre-configured templates:

1. **Minimal Setup**
   - Only tag highlighting
   - No comments or watermarks
   - Fastest processing
   - Yellow highlights

2. **Standard Documentation**
   - Tag highlighting with basic comments
   - No watermarks
   - Balanced performance
   - Yellow highlights

3. **Production Ready**
   - All features enabled
   - Excel annotation included
   - Watermark overlays
   - Red highlights for visibility
   - Comprehensive documentation

4. **Quick Review**
   - Optimized for test runs
   - Fast validation setup
   - Green highlights
   - Minimal overhead

5. **Excel Focus**
   - Prioritizes Excel annotation
   - Highlights found tags in Excel
   - Light green highlights
   - No watermarks for speed

### Managing Profiles

**Save a Profile:**
1. Configure all settings as desired
2. Click "Save" in Configuration Profiles section
3. Enter name and description
4. Profile saved to `./data/profiles/`

**Load a Profile:**
1. Select from dropdown (templates or saved)
2. Click "Load"
3. All settings populated automatically

**Export/Import:**
- **Export**: Download profile as JSON for backup/sharing
- **Import**: Upload JSON profile from team members
- Profiles are validated on import

**Delete:**
- Remove saved profiles (built-in templates cannot be deleted)
- Confirmation dialog prevents accidental deletion

### Profile Structure

```json
{
  "name": "My Custom Profile",
  "description": "Optimized for project XYZ",
  "version": "1.0",
  "created_at": "2025-01-23T10:30:00",
  "settings": {
    "header_row": 6,
    "tag_column": "Tag",
    "comment_columns": ["Description", "Location"],
    "highlight_column": "Critical",
    "highlight_color": "#FF0000",
    "annotate_excel": true,
    "watermark_enabled": true,
    "watermark_attributes": ["Location"],
    "watermark_text_color": "#000000"
  }
}
```

## Deployment Comparison

| Feature | Local Server (localhost:5001) | Docker/Web Deployment |
|---------|-------------------------------|----------------------|
| PDF Annotation | ✅ | ✅ |
| Excel Integration | ✅ | ✅ |
| Excel Annotation | ✅ | ✅ |
| HTML Report Generation | ✅ | ✅ |
| Tag Column Selection | ✅ | ✅ |
| Comment Columns | ✅ | ✅ |
| Highlight Colors | ✅ | ✅ |
| Watermark Feature | ✅ | ✅ |
| Configuration Profiles | ✅ | ✅ |
| Built-in Templates | ✅ | ✅ |
| Export/Import Profiles | ✅ | ✅ |
| Interactive Tutorial | ✅ | ✅ |
| Test Run (100 tags) | ✅ | ✅ |
| Progress Tracking | ✅ (Real-time) | ✅ (Real-time) |
| Dark Theme | ✅ (with persistence) | ✅ (with persistence) |
| File Drag & Drop | ✅ | ✅ |
| Multi-PDF Support | ✅ | ✅ |
| Parallel Processing | ✅ | ✅ |
| Streaming Mode | ✅ | ✅ |
| Multi-user Support | Limited | ✅ (session-based) |
| Remote Access | ❌ (localhost only) | ✅ |
| Auto-restart | ❌ | ✅ (with Docker) |
| Production Ready | ❌ | ✅ (Gunicorn) |

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs pid-annotator

# Check container status
docker ps -a

# Check Docker daemon
systemctl status docker
```

### Port Already in Use

```bash
# Check what's using port 8080 (Linux)
sudo netstat -tulpn | grep 8080

# Check on Windows
netstat -ano | findstr :8080

# Or change the port in docker-compose.yml
ports:
  - "9000:8080"  # Use different external port
```

### Memory Issues

```bash
# Check system memory
free -h  # Linux
systeminfo | findstr /C:"Available Physical Memory"  # Windows

# Reduce memory limits in docker-compose.yml if needed
deploy:
  resources:
    limits:
      memory: 1G  # Reduce from 1792m if necessary
```

### File Upload Issues

- Check that upload directories exist and have proper permissions
- Ensure sufficient disk space is available
- Check file size limits (default: 100MB in Flask)
- Review session ID in browser console

### Processing Errors

- Check that Excel file has the correct header row
- Verify tag column contains valid tag formats
- Ensure PDF is not password-protected
- Check Docker logs for Python errors

### Performance Issues

- For large files (>50MB), streaming mode activates automatically
- Ensure sufficient CPU cores are available
- Check memory usage with `docker stats`
- Consider disabling parallel processing for debugging:
  ```python
  import pid_annotator_core
  pid_annotator_core.PARALLEL_INDEXING_ENABLED = False
  ```

### Raspberry Pi Specific Issues

**Temperature Throttling:**
- Monitor temperature: `vcgencmd measure_temp`
- Warning threshold: 65°C
- Throttling threshold: 75°C
- Solution: Improve cooling (heatsink/fan)

**SD Card Performance:**
- Use Class 10 or UHS-I SD card
- Consider SSD via USB 3.0 for better performance
- Monitor disk I/O with `iostat`

**Memory Pressure:**
- Reduce Gunicorn workers from 2 to 1
- Lower memory limit in docker-compose.yml
- Close unnecessary services

For Raspberry Pi specific quick start and troubleshooting, see [RASPBERRY_PI_QUICKSTART.md](RASPBERRY_PI_QUICKSTART.md).

## Security Notes

- The application runs as a non-root user (`appuser`) inside the container
- File uploads are validated with `werkzeug.utils.secure_filename()`
- Session-based file isolation prevents user conflicts
- Resource limits prevent resource exhaustion
- Filenames are namespaced with session IDs
- Automatic file cleanup after 24 hours
- Entrypoint script performs security validation before startup

## WebSocket Events

Real-time communication between client and server:

**Server emits:**
```python
socketio.emit('progress_update', {
    'status': 'processing',
    'progress': 50,
    'message': 'Processing page 50/100'
}, room=session_id)
```

**Client listens:**
```javascript
socket.on('progress_update', handleProgressUpdate)
```

## Excel File Requirements

The application expects Excel files with:
- **Header row** (default: row 6, configurable)
- **Tag column** containing component identifiers
- **Comment columns** (optional) with additional metadata

Tag formats accepted: `A-B-C`, `A.B.C`, `TAG-001-A`, `SYS.PUMP.01`

## Multi-File Processing

The application supports:
- **Multiple PDFs** - All PDFs processed with same Excel file
- **Single Excel** - One Excel file per session
- **Batch processing** - Sequential processing with aggregated progress
- **Session isolation** - Each user's files are isolated by UUID

See `process_files()` in [app.py](app.py:200) for implementation details.

---

## FAQ

The web application includes a **comprehensive FAQ modal** with categorized help topics. Below are the most frequently asked questions:

### Getting Started

**Q1: How do I start using the PID Annotator?**

A: Follow these steps:
1. Upload your Excel file containing component tags
2. Upload one or more PDF files you want to annotate
3. Configure the header row (default is row 6)
4. Select which column contains your tags
5. (Optional) Load a configuration profile for quick setup
6. Click "Start" to begin processing

For first-time users, an interactive tutorial will guide you through the process.

**Q2: What is the header row and how do I set it?**

A: The header row is the row in your Excel file that contains column names (like "Tag", "Description", "Location"). By default, the application expects it to be row 6, but you can change it in the configuration section. The header row number refers to the Excel row number (visible in Excel), not a zero-based index.

**Q3: How do I select the tag column?**

A: After uploading your Excel file and setting the header row, a dropdown menu will appear showing all available columns. Select the column that contains your component tags (e.g., "Tag", "Component ID", etc.). This is the column the application will use to search for tags in your PDF.

**Q4: What are configuration profiles and how do I use them?**

A: Configuration profiles let you save and reuse your settings. The application includes 5 built-in templates:
- **Minimal Setup**: Fast processing with just tag highlighting
- **Standard Documentation**: Balanced features for typical use
- **Production Ready**: All features enabled for comprehensive documentation
- **Quick Review**: Optimized for test runs
- **Excel Focus**: Prioritizes Excel annotation

You can also create custom profiles by configuring your settings and clicking "Save" in the Configuration Profiles section.

---

### Features & Configuration

**Q5: What's the difference between "Start" and "Test Run"?**

A:
- **Start**: Processes all tags from your Excel file and creates complete annotated PDFs
- **Test Run**: Processes only the first 100 tags for quick validation

Use Test Run to verify your configuration before running the full processing job, especially for large files.

**Q6: What does Excel annotation do?**

A: When Excel annotation is enabled, the application highlights tags in your Excel file with a green background color to indicate which tags were successfully found in the PDF. This provides a quick visual reference of annotation coverage. The annotated Excel file is available for download after processing completes.

**Q7: How does the watermark feature work?**

A: The watermark feature adds text overlays near each found tag in the PDF. You can select which Excel columns to display (e.g., "Description", "Location") and customize the text color. Watermarks are positioned automatically near the tag location and help provide context without opening the Excel file.

**Q8: What is conditional highlighting?**

A: Conditional highlighting allows you to change the highlight color based on values in a specific Excel column. For example, you could highlight all "Critical" components in red while keeping others yellow. Select the attribute column and choose the highlight color in the configuration section.

**Q9: Can I process multiple PDF files at once?**

A: Yes! The application supports batch processing of multiple PDFs with a single Excel file. Simply drag and drop or select multiple PDF files when uploading. All PDFs will be processed sequentially, and each will get its own annotated output file. Progress is shown for all files combined.

**Q10: What is the HTML Report and how do I use it?**

A: The HTML Report is an interactive document generated after processing that shows:
- Summary statistics (found/not found tags, duplicates, warnings)
- Detailed tables of all tags with page locations and bookmarks
- Real-time search and filter capabilities
- Export to Excel functionality
- Print-ready formatting

Download the report after processing completes and open it in any web browser. You can search for specific tags, sort by any column, filter results, and export filtered data to Excel for further analysis.

**Q11: How do I export HTML Report data to Excel?**

A: In the HTML Report:
1. (Optional) Use the search box to filter results
2. Click the "Export Filtered Data (Excel)" button
3. The browser will download an Excel file containing all visible/filtered data
4. The Excel file includes all sections: Found Tags, Not Found, Duplicates, and Warnings

Note: Export functionality requires internet connection for the SheetJS library (loaded via CDN).

---

### Troubleshooting

**Q12: Why aren't my tags being found in the PDF?**

A: Common reasons and solutions:
- **Wrong tag format**: Tags must be 3-5 parts with hyphens or periods (e.g., A-B-C, A.B.C)
- **OCR quality**: If your PDF is scanned, poor OCR quality can affect tag recognition
- **Case sensitivity**: Try normalizing case in your Excel file
- **Extra spaces**: Remove leading/trailing spaces in Excel tags
- **Wrong column**: Verify you selected the correct tag column

Run a Test Run with 100 tags to quickly identify the issue before processing all tags.

**Q13: Processing is slow for large files. Is this normal?**

A: Yes, processing time depends on file size and page count:
- Small files (10 pages): ~7 seconds
- Medium files (100 pages): ~18 seconds
- Large files (500 pages): ~2-3 minutes
- Very large files (1000 pages): ~6 minutes

For files over 50MB, the application automatically switches to streaming mode which is slower but uses less memory. Enable parallel processing to speed up large files (enabled by default for files with >20 pages).

**Q14: What are the file size limits?**

A:
- **Upload limit**: 100MB per file (configurable in Flask)
- **Recommended**: Under 200MB for optimal performance
- **Streaming mode**: Automatically activated for files ≥50MB
- **Very large files** (>200MB): May take 10+ minutes to process

If you need to process larger files, consider splitting them into smaller PDFs or increasing the upload limit and resource allocation.

**Q15: How long are my files stored?**

A: Files are automatically deleted after 24 hours. This includes:
- Uploaded PDFs and Excel files
- Generated annotated PDFs
- HTML reports

Download important files immediately after processing. Use the "Clear All" button to manually delete files sooner if needed.

**Q16: Can I use different Excel structures?**

A: Yes! The application is flexible:
- Set the correct header row number (default: 6)
- Choose any column as the tag column
- Select multiple comment columns
- Tag format must still be 3-5 part hierarchical format (A-B-C)

The application will parse your Excel structure based on your configuration.

**Q17: Why won't my HTML Report download?**

A: Common issues:
- **Browser popup blocker**: Allow popups for the application URL
- **Insufficient disk space**: Free up space on your computer
- **Large report size**: Reports with 10,000+ tags may be slow to generate
- **Browser compatibility**: Use Chrome 90+, Firefox 88+, Safari 14+, or Edge 90+

Check the browser console (F12) for specific error messages.

---

### Technical Details

**Q18: What tag formats are supported?**

A: The application supports hierarchical tags with 3-5 parts:
- **Delimiters**: Hyphens (`-`) or periods (`.`)
- **Examples**:
  - `A-B-C` (3 parts)
  - `TAG-001-A` (3 parts)
  - `SYS.PUMP.01` (3 parts)
  - `A-B-C-D` (4 parts)
  - `A.B.C.D.E` (5 parts)
- **Not supported**: Tags with fewer than 3 or more than 5 parts

Tags are matched case-insensitively, and both delimiters are accepted regardless of which is used in the Excel file.

**Q19: What information is added to the PDF annotations?**

A: Each annotation includes:
- **Highlight**: Yellow (or custom color) highlight around the tag
- **Note/Comment**: Contains selected comment columns from Excel (e.g., Description, Location)
- **Watermark** (if enabled): Text overlay near tag with selected attributes
- **Bookmark reference**: Tagged with PDF bookmark name if available

Annotations are visible when opening the PDF in any standard PDF reader.

**Q20: Where are output files stored?**

A: Files are stored in session-namespaced directories:
- **Uploads**: `/app/uploads/{session_id}_{filename}`
- **Output**: `/app/output/{session_id}_{filename}`
- **Persistent volumes**: Mapped to host directories via Docker volumes

Files are isolated by session ID to prevent conflicts between users. After 24 hours, files are automatically deleted.

**Q21: What is parallel processing and how does it work?**

A: Parallel processing uses multiple CPU cores to process PDF pages simultaneously:
- **Enabled by default** for PDFs with >20 pages
- **Worker count**: Automatically set to CPU cores minus 1
- **Speed improvement**: Up to 2.5x faster for medium/large files
- **Memory usage**: Slightly higher but still within limits

On Raspberry Pi 5, parallel processing is optimized for 4-core CPU with configurable worker count (1 for 4GB model, 2 for 8GB model).

**Q22: What is streaming mode?**

A: Streaming mode is automatically activated for files ≥50MB:
- **Chunk-based processing**: Processes file in segments rather than loading entirely into memory
- **Memory efficiency**: Reduces RAM usage for very large files
- **Document reopen**: Closes and reopens PDF between processing phases
- **Explicit garbage collection**: Runs every 100 pages to free memory

This allows processing of files up to 200MB+ on Raspberry Pi 5 without running out of memory.

**Q23: How are bookmarks used in the HTML Report?**

A: PDF bookmarks (section markers) are extracted during processing:
- Each tag is associated with the bookmark of the page where it's found
- The HTML Report shows bookmark names in the "Bookmarks" column (e.g., "Sheet 1", "Process Flow")
- Helps identify which drawing section contains each tag
- If no bookmarks exist in the PDF, "N/A" is displayed

Bookmarks provide context for where components are located in large multi-sheet PDFs.

---

### Deployment & Docker

**Q24: Why use Docker instead of running locally?**

A: Docker deployment offers several advantages:
- **Consistency**: Same environment on any system
- **Isolation**: No conflicts with other Python applications
- **Auto-restart**: Container automatically restarts if it crashes
- **Multi-user**: Session-based isolation for concurrent users
- **Production-ready**: Gunicorn server with proper resource limits
- **Easy updates**: Pull new version and restart
- **CasaOS integration**: One-click installation on compatible systems

Local development (localhost:5001) is still available for testing and development.

**Q25: What is port 8080 and can I change it?**

A: Port 8080 is the standard port where the application listens inside the Docker container:
- **Internal port**: Always 8080 (Dockerfile EXPOSE 8080)
- **External port**: Configurable in docker-compose.yml (default: 8080)
- **Accessing**: `http://your-ip:8080` (default) or `http://your-ip:YOUR_PORT` (custom)

To change the external port, edit docker-compose.yml:
```yaml
ports:
  - "9000:8080"  # Access via port 9000 instead
```

**Q26: What is CasaOS and how do I deploy to it?**

A: CasaOS is a home server operating system that simplifies Docker app deployment:
- **One-click install**: Use the CasaOS app store (if available)
- **Manual installation**: Import docker-compose.yml via CasaOS UI
- **Configuration**: Edit environment variables and ports in UI
- **Labeled for CasaOS**: Application includes CasaOS metadata labels

The docker-compose.yml file includes CasaOS-specific labels for proper integration (app name, icon, category, etc.).

**Q27: How do I configure for Raspberry Pi 5 (4GB vs 8GB)?**

A: The default configuration is optimized for the 4GB model. For 8GB:

Edit `docker-compose.yml`:
```yaml
environment:
  - GUNICORN_WORKERS=2  # Change from 1
mem_limit: 2560m  # Change from 1792m
mem_reservation: 768m  # Change from 512m
cpus: 3.0  # Change from 2.5
tmpfs:
  - /tmp:size=512M  # Change from 384M
  - /app/.cache:size=256M  # Change from 192M
```

See [RASPBERRY_PI_QUICKSTART.md](RASPBERRY_PI_QUICKSTART.md) for detailed instructions.

**Q28: What does entrypoint.sh do?**

A: The entrypoint script (entrypoint.sh) performs comprehensive safety checks before starting the application:
- **Architecture verification**: Confirms ARM64 platform (Raspberry Pi 5)
- **Memory validation**: Checks available memory (warns if <1500MB)
- **Disk space check**: Ensures sufficient disk space (warns if <1000MB)
- **CPU temperature**: Monitors temperature on Raspberry Pi (warns if >70°C)
- **Port validation**: Verifies PORT is numeric and in valid range
- **Worker count validation**: Checks GUNICORN_WORKERS configuration
- **Permission fixes**: Automatically fixes mounted volume permissions
- **Application verification**: Confirms all required files exist

The script logs all checks and switches to non-root user (appuser) before starting the application.

---

### About & License

**Q29: What Python libraries are used?**

A: Key dependencies:
- **Flask**: Web framework
- **Flask-SocketIO**: Real-time WebSocket communication
- **PyMuPDF (fitz)**: PDF processing and annotation
- **openpyxl**: Excel file manipulation
- **pandas**: Data processing
- **ReportLab**: PDF watermark generation
- **PyPDF2**: PDF merging
- **Gunicorn**: Production WSGI server
- **eventlet**: Async worker for WebSocket support

See [requirements.txt](requirements.txt) for complete list with versions.

**Q30: Who created this application?**

A: PID Annotator was created by **Rudi S. Kærgaard** (rudikdk@gmail.com).

- **Desktop version**: Original standalone application
- **Web version**: Flask-based web application with Docker support
- **Optimization**: Raspberry Pi 5 specific performance tuning
- **License**: See project repository for license information

**Q31: How do I replay the interactive tutorial?**

A: To replay the tutorial:
1. Click the "FAQ" button in the top-right corner
2. Scroll to the bottom of the FAQ modal
3. Click the "Start Tutorial" button
4. The tutorial will restart from step 1

This is useful for training new team members or refreshing your memory about features.

---

**Additional Help**: For more detailed information, see:
- [RASPBERRY_PI_QUICKSTART.md](RASPBERRY_PI_QUICKSTART.md) - Quick start for Raspberry Pi 5
- [CLAUDE.md](CLAUDE.md) - Developer documentation
- [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) - Performance tuning guide
- [Troubleshooting Section](#troubleshooting) - Common issues and solutions

---

## Known Limitations

### File Processing

1. **Password-Protected PDFs**
   - Not currently supported
   - Remove password protection before uploading

2. **Scanned PDFs**
   - OCR quality affects tag recognition
   - Text-based PDFs work best
   - Poor scans may result in missed tags

3. **Tag Format Requirements**
   - Must be 3-5 part hierarchical (e.g., A-B-C or A-B-C-D-E)
   - Fewer than 3 or more than 5 parts won't match
   - Delimiters must be consistent (hyphens or periods)

### Performance

4. **Very Large Files (>200MB)**
   - May require 10+ minutes processing
   - Monitor server resources during processing
   - Consider splitting into smaller PDFs if possible

5. **Concurrent Users**
   - Resource limits apply per Docker container
   - Multiple heavy jobs may slow performance
   - Consider resource limit adjustments for high usage

### Browser Compatibility

6. **Modern Browsers Required**
   - React 18 and modern JavaScript features
   - IE11 not supported
   - Chrome, Firefox, Safari, Edge recommended

### Session Management

7. **Browser-Based Sessions**
   - Each browser tab = separate session
   - Closing tab loses session data
   - Files persist for 24 hours regardless

8. **No Cross-Device Resume**
   - Sessions tied to single browser/device
   - Cannot resume processing from different device
   - Download files before switching devices

### File Cleanup

9. **24-Hour Retention**
   - Files automatically deleted after 24 hours
   - No option to extend retention
   - Download important files immediately

10. **Manual Cleanup Required**
    - Use "Clear All" to free space sooner
    - Server admin may need to manually clean if disk full

---

## Support

For issues or questions:
- Check the FAQ in the web interface
- Review the troubleshooting section above
- Check Docker logs for error messages: `docker-compose logs pid-annotator`
- Review [CLAUDE.md](CLAUDE.md) for development guidance
- Review [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) for performance tuning
- See [RASPBERRY_PI_QUICKSTART.md](RASPBERRY_PI_QUICKSTART.md) for Raspberry Pi 5 specific help

## Credits

**Created by:** Rudi S. Kærgaard
**Email:** rudikdk@gmail.com
**Local Server:** Flask development server (localhost:5001)
**Docker Deployment:** Optimized for Raspberry Pi 5 + CasaOS

## License

See project repository for license information.

## Recent Updates

### Latest Enhancements (v2.2)

- **HTML Report Generation**
  - Interactive processing reports with visual dashboard
  - Search, sort, and filter capabilities across all tables
  - Found/Not Found/Duplicate tags analysis
  - Bookmark integration showing PDF section references
  - Export filtered data to Excel with formatting
  - Print-ready layout for documentation
  - Validation warnings and duplicate detection
  - Collapsible sections for focused viewing
  - Self-contained HTML file (200-500 KB)

### Previous Updates (v2.1)

- **Enhanced Interactive Tutorial**
  - Dynamic tooltip positioning with arrow pointers
  - Animated spotlight effects on target elements
  - Keyboard navigation (arrow keys, ESC)
  - Smooth transitions and fade-in animations
  - Visual progress indicators

- **Comprehensive FAQ System**
  - 30+ questions across 5 categories
  - Real-time search functionality
  - Category-based navigation with icons
  - Expandable answers with detailed explanations
  - Direct tutorial launch from FAQ

- **Improved Documentation**
  - Common workflows section with 5 scenarios
  - Step-by-step usage examples
  - Known limitations documented
  - Enhanced troubleshooting guide
  - Table of contents for easy navigation
  - Port configuration clarification (8080)
  - Raspberry Pi 5 specific deployment guide

### Earlier Updates (v2.0)

- **Configuration Profiles**: Save/load configuration presets with 5 built-in templates
- **Interactive Tutorial**: Automatic step-by-step onboarding for new users
- **Enhanced UX**: Profile management with export/import functionality
- **Performance Optimization**: Added parallel indexing, streaming mode, and adaptive processing
- **Python 3.13 Support**: Compatibility fix script included
- **Multi-File Support**: Process multiple PDFs with single Excel file
- **Excel Annotation**: Automatic highlighting of found tags in Excel
- **Session Management**: UUID-based session isolation
- **Auto-Cleanup**: 24-hour file retention policy
- **React 18 Frontend**: Modern UI with TailwindCSS and dark mode
- **Docker Optimization**: Multi-stage builds, BuildKit caching, ARM64 support
- **Entrypoint Safety Checks**: Comprehensive startup validation and permission fixes
- **Memory Optimization**: MALLOC_ARENA_MAX=2, tmpfs mounts, garbage collection
