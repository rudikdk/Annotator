# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PID Annotator Web Application** - A Flask-based web application that automatically annotates P&ID (Piping & Instrumentation Diagram) PDF documents with metadata from Excel component lists. Optimized for Raspberry Pi 5 deployment with Docker/CasaOS.

**Author:** Rudi S. Kærgaard (rudikdk@gmail.com)

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (port 5001)
python app.py

# Install dev dependencies
pip install -e ".[dev]"
```

### Testing & Code Quality
```bash
# Run tests
pytest

# Code formatting
black .

# Import sorting
isort .

# Linting
flake8 .

# Type checking
mypy .

# Coverage report
pytest --cov=pid_annotator_web --cov-report=html
```

### Docker Operations
```bash
# Build and run with Docker Compose (production)
docker-compose up -d --build

# View logs
docker-compose logs pid-annotator

# Stop container
docker-compose down

# Build for ARM64 (Raspberry Pi 5)
docker buildx build --platform linux/arm64 -t pid-annotator-web .

# Build for AMD64
docker buildx build --platform linux/amd64 -t pid-annotator-web .
```

## Architecture

### Application Structure

The application follows a **session-based client-server architecture** with real-time WebSocket communication:

1. **Flask Backend** ([app.py](app.py))
   - Session management with unique UUID per client
   - File upload handling with `secure_filename()` validation
   - Background task processing with threading
   - Real-time progress via Flask-SocketIO
   - Automatic file cleanup (24-hour retention)

2. **Core Processing Engine** ([pid_annotator_core.py](pid_annotator_core.py))
   - Three processing modes (auto-selected based on file size):
     - **Standard mode** (< 50MB): Fast, memory-loaded processing
     - **Streaming mode** (≥ 50MB): Chunk-based processing for large files
     - **Parallel indexing** (> 20 pages): Multi-threaded page processing
   - Tag extraction with regex pattern matching
   - PDF annotation via PyMuPDF
   - Optional watermark overlay (ReportLab + PyPDF2)
   - Optional Excel annotation with openpyxl

3. **Frontend** ([templates/index.html](templates/index.html))
   - React 18 single-page application
   - TailwindCSS for responsive styling
   - Socket.IO client for real-time updates
   - Drag-and-drop file upload
   - Dark mode with localStorage persistence

### Processing Pipeline

```
Upload PDF + Excel
    ↓
Session-namespaced storage
    ↓
Build Tag Index (parallel if >20 pages)
    ├─ Extract text with regex
    ├─ Find coordinates with page.search_for()
    └─ Cache in defaultdict
    ↓
Process Annotations (from Excel)
    ├─ Iterate Excel rows
    ├─ Lookup tags in index
    ├─ Apply highlights + notes
    └─ Collect watermark positions
    ↓
Save pre-watermark PDF
    ↓
Apply Watermarks (if enabled)
    ├─ Generate ReportLab overlay
    ├─ Merge with PyPDF2
    └─ Handle rotations
    ↓
Annotate Excel (if enabled)
    └─ Highlight found tags with green fill
    ↓
Download annotated files
```

### Performance Optimization

The core engine uses **adaptive processing modes** (see [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)):

**Configuration parameters** ([pid_annotator_core.py](pid_annotator_core.py)):
```python
PARALLEL_INDEXING_ENABLED = True       # Multi-core processing
MAX_WORKERS = os.cpu_count() - 1       # CPU cores to use
STREAMING_THRESHOLD_MB = 50            # File size for streaming mode
MEMORY_CLEANUP_BATCH_SIZE = 100        # Pages between gc.collect()
PROGRESS_UPDATE_INTERVAL = 2           # Progress update frequency (%)
```

**Benchmarks:**
- Small (10 pages, 5MB): ~7 seconds
- Medium (100 pages, 25MB): ~18 seconds (2.5x faster with parallel)
- Large (500 pages, 80MB): ~2:30 (streaming mode)
- Very large (1000 pages, 200MB): ~6 minutes (previously failed)

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

4. **Tag Format Support**
   - Accepts both `-` and `.` delimiters (A.B.C or A-B-C)
   - 3-5 part hierarchical tags
   - Case-insensitive normalization
   - Multiple variant lookup

## File Organization

- **[app.py](app.py)** - Flask routes, session management, WebSocket handlers
- **[pid_annotator_core.py](pid_annotator_core.py)** - PDF/Excel processing engine
- **[report_template.py](report_template.py)** - HTML report generation
- **[templates/index.html](templates/index.html)** - React SPA interface
- **[requirements.txt](requirements.txt)** - Python dependencies
- **[Dockerfile](Dockerfile)** - Multi-stage container build
- **[docker-compose.yml](docker-compose.yml)** - Container orchestration
- **[entrypoint.sh](entrypoint.sh)** - Container startup script
- **[pyproject.toml](pyproject.toml)** - Project metadata, tool configs
- **[OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)** - Performance optimization documentation
- **uploads/** - Temporary uploaded files (auto-cleaned)
- **output/** - Generated annotated PDFs (auto-cleaned)

## Important Technical Details

### Session Management

When modifying session logic, note:
- Session data stored in Flask session: `pdf_files`, `excel_file`, `session_id`, `columns`, `header_row`
- File cleanup runs on every request via `@app.before_request`
- Session clearing removes both session data AND physical files

### WebSocket Events

Real-time communication ([app.py](app.py)):
```python
# Server emits:
socketio.emit('progress_update', data, room=session_id)

# Client listens:
socket.on('progress_update', handleProgressUpdate)
```

### Tag Extraction Regex

Core pattern ([pid_annotator_core.py](pid_annotator_core.py:160)):
```python
r'\b[A-Za-z0-9]{1,5}[-\.][A-Za-z0-9]{1,5}[-\.][A-Za-z0-9]{1,5}(?:[-\.][A-Za-z0-9]{1,5}){0,2}\b'
```
Matches: `TAG-001-A`, `SYS.SUB.COMP`, `A.B.C.D.E` (3-5 parts)

**Note:** The application now includes a `TagMatchingConfig` class for customizable tag matching behavior with presets and custom regex support.

### Watermark Implementation

Watermarks use **two-library approach** ([pid_annotator_core.py](pid_annotator_core.py:26-27)):
1. **ReportLab** (`reportlab.pdfgen.canvas`) - Generate overlay PDF with text/graphics
2. **PyPDF2** (`PdfReader`, `PdfWriter`) - Merge overlay onto base PDF pages

Handles page rotations by drawing on unrotated canvas.

### Security Considerations

- Filenames sanitized with `werkzeug.utils.secure_filename()`
- 100MB file upload limit
- Session-based file isolation
- Container runs as non-root user `appuser`
- Resource limits: 2GB memory, 2 CPU cores

## Common Development Patterns

### Adding a New Route

```python
@app.route('/new_route', methods=['POST'])
def new_route():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session'}), 400

    # Your logic here

    return jsonify({'success': True})
```

### Emitting Progress Updates

```python
def long_running_task(session_id):
    socketio.emit('progress_update', {
        'status': 'processing',
        'progress': 50,
        'message': 'Processing...'
    }, room=session_id)
```

### Modifying Core Processing

When changing [pid_annotator_core.py](pid_annotator_core.py):
- Always call `progress_callback()` with percentage (0-100)
- Use `fitz.TOOLS.store_shrink(100)` after heavy operations
- Set `page = None` explicitly after processing
- Test with both small (<50MB) and large (>50MB) files

### Testing Parallel Processing

```python
# Disable parallel for debugging
import pid_annotator_core
pid_annotator_core.PARALLEL_INDEXING_ENABLED = False
```

## Deployment Notes

### Docker Configuration

- **Base image:** `python:3.11-slim-bookworm` (ARM64 compatible, updated from bullseye)
- **Production server:** Gunicorn with eventlet worker
- **Ports:** 8080 (internal), 18080 (external default)
- **Volumes:**
  - `./persistent_uploads:/app/uploads`
  - `./persistent_output:/app/output`
  - `./data:/app/data`

### Resource Limits (Raspberry Pi 5)

```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2'
    reservations:
      memory: 512M
      cpus: '0.5'
```

### Health Checks

Container includes health check on port 8080:
```bash
curl -f http://localhost:8080/ || exit 1
```

## Code Style

Per [pyproject.toml](pyproject.toml):
- **Line length:** 120 characters
- **Formatter:** black with Python 3.8+ target
- **Import sorting:** isort with black profile
- **Type checking:** mypy (lenient, ignore missing imports)

## Tag Format Notes

The application expects Excel files with:
- **Header row** (default: row 6, configurable)
- **Tag column** containing component identifiers
- **Comment columns** (optional) with additional metadata

Tag formats accepted: `A-B-C`, `A.B.C`, `TAG-001-A`, `SYS.PUMP.01`

## Multi-File Support

The application supports:
- **Multiple PDFs** - All PDFs processed with same Excel file
- **Single Excel** - One Excel file per session
- **Batch processing** - Sequential processing with aggregated progress

When working with multi-file logic, see `process_files()` in [app.py](app.py:436).
