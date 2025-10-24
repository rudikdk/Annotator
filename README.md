# PID Annotator Web Application

A powerful web-based tool for automatically annotating P&ID (Piping & Instrumentation Diagram) PDF documents with metadata from Excel component lists. Optimized for Raspberry Pi 5 deployment with Docker/CasaOS, but works on any system with Docker support.

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
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
   - Open your browser and go to: `http://your-ip:18080`
   - The application will be available on port 18080 as specified

### Manual Docker Build

If you prefer to build manually:

```bash
# Build the image
docker build -t pid-annotator-web .

# Run the container
docker run -d \
  --name pid-annotator-web \
  -p 18080:8080 \
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
   - Files are automatically cleaned up after 24 hours

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

### Port Mapping
- External port: 18080 (as requested)
- Internal port: 8080
- Access via: `http://localhost:18080` or `http://your-ip:18080`

### Resource Limits
The application is configured with resource limits suitable for Raspberry Pi 5:
- Memory limit: 2GB
- CPU limit: 2 cores
- Memory reservation: 512MB
- CPU reservation: 0.5 cores

### Persistent Storage
The following directories are mounted for persistent data:
- `./persistent_uploads` → `/app/uploads` (uploaded files)
- `./persistent_output` → `/app/output` (generated PDFs)
- `./data` → `/app/data` (application data)

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

## Interactive Tutorial

### First-Time Experience

New users automatically see an interactive tutorial:
- Appears 1 second after page load
- Highlights each feature with overlay
- 10 steps covering all functionality
- Can be skipped at any time

### Tutorial Steps

1. **Welcome & File Upload** - Upload area introduction
2. **Header Row Configuration** - Excel structure setup
3. **Tag Column Selection** - Identifying tag column
4. **Configuration Profiles** - Templates and saved profiles
5. **Comment Columns** - Selecting annotation content
6. **Conditional Highlighting** - Attribute-based colors
7. **Excel Annotation** - Excel highlighting feature
8. **Watermark Feature** - PDF overlay labels
9. **Start Processing** - Running full or test jobs
10. **FAQ & Help** - Support resources

### Tutorial Controls

- **Next/Previous**: Navigate between steps
- **Skip Tutorial**: Dismiss (tracked in localStorage)
- **Progress Dots**: Visual step indicator
- **Replay**: Available anytime from FAQ → "Start Tutorial" button

### Persistence

Tutorial state stored in browser localStorage:
- `tutorial_completed`: Whether user finished tutorial
- `tutorial_dismissed_count`: Times skipped (max 3 auto-shows)
- `tutorial_started`: Initial trigger tracking

Auto-start only for:
- First-time visitors (no completion flag)
- Users who dismissed < 3 times

## Deployment Comparison

| Feature | Local Server (localhost:5001) | Docker/Web Deployment |
|---------|-------------------------------|----------------------|
| PDF Annotation | ✅ | ✅ |
| Excel Integration | ✅ | ✅ |
| Excel Annotation | ✅ | ✅ |
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
# Check what's using port 18080 (Linux)
sudo netstat -tulpn | grep 18080

# Check on Windows
netstat -ano | findstr :18080

# Or change the port in docker-compose.yml
ports:
  - "19080:8080"  # Use different external port
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
      memory: 1G  # Reduce from 2G
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

## Security Notes

- The application runs as a non-root user (`appuser`) inside the container
- File uploads are validated with `werkzeug.utils.secure_filename()`
- Session-based file isolation prevents user conflicts
- Resource limits prevent resource exhaustion
- Filenames are namespaced with session IDs
- Automatic file cleanup after 24 hours

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

The web application includes a **comprehensive FAQ modal** with categorized help topics:

### FAQ Categories

1. **Getting Started** (3 questions)
   - How to start using PID Annotator
   - Excel header row configuration
   - Tag column selection

2. **Features & Configuration** (6 questions)
   - Configuration profiles explained
   - Start vs Test Run differences
   - Excel annotation details
   - Watermark feature guide
   - Conditional highlighting
   - Multi-PDF processing

3. **Troubleshooting** (5 questions)
   - Tags not found in PDF
   - Slow processing for large files
   - File size limits
   - File storage duration
   - Different Excel structures

4. **Technical Details** (5 questions)
   - Supported tag formats
   - PDF annotation content
   - Output file locations
   - Parallel processing explanation
   - Streaming mode details

5. **About & Licenses** (2 questions)
   - Python library licenses
   - Application creator info

### FAQ Features

- **Searchable**: Real-time search across all questions and answers
- **Categorized**: Organized by topic with icon badges
- **Interactive**: Click categories to browse specific topics
- **Tutorial Link**: Launch interactive tutorial directly from FAQ
- **Question Count**: See number of questions per category

### Accessing the FAQ

- Click the "FAQ" button in the top-right corner of the application
- Press during tutorial to learn about help resources
- Searchable interface helps find answers quickly

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

## Credits

**Created by:** Rudi S. Kærgaard
**Email:** rudikdk@gmail.com
**Local Server:** Flask development server (localhost:5001)
**Docker Deployment:** Optimized for Raspberry Pi 5 + CasaOS

## License

See project repository for license information.

## Recent Updates

### Latest Enhancements (v2.1)

- **Enhanced Interactive Tutorial**
  - Dynamic tooltip positioning with arrow pointers
  - Animated spotlight effects on target elements
  - Keyboard navigation (arrow keys, ESC)
  - Smooth transitions and fade-in animations
  - Visual progress indicators

- **Comprehensive FAQ System**
  - 21+ questions across 5 categories
  - Real-time search functionality
  - Category-based navigation with icons
  - Expandable answers with detailed explanations
  - Direct tutorial launch from FAQ

- **Improved Documentation**
  - Common workflows section with 4 scenarios
  - Step-by-step usage examples
  - Known limitations documented
  - Enhanced troubleshooting guide
  - Table of contents for easy navigation

### Previous Updates (v2.0)

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
