# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PID Annotator** - Flask web app that annotates P&ID PDF documents with metadata from Excel component lists. Finds tags in PDFs, highlights them, and adds popup notes from Excel data.

**Author:** Rudi S. Kærgaard (rudikdk@gmail.com)

## Development Commands

```bash
# Install and run locally (port 5001)
pip install -r requirements.txt
python app.py

# Run tests
pytest
pytest tests/test_core.py              # Single test file
pytest --cov=pid_annotator_web         # With coverage

# Code quality
black . && isort . && flake8 . && mypy .

# Docker
docker-compose up -d --build           # Build and run
docker-compose logs pid-annotator      # View logs
docker-compose down                    # Stop

# ARM64/Raspberry Pi build
docker buildx build --platform linux/arm64 -t pid-annotator-web:arm64 .
```

## Architecture

### Entry Point

| File | Purpose |
|------|---------|
| `app.py` | Minimal Flask entry point (91 lines) - blueprint registration only |
| `templates/index.html` | React 18 SPA with TailwindCSS |
| `entrypoint.sh` | Docker startup with safety checks |

### Module Structure

The application is organized into focused modules under `pid_annotator/`:

**Core Processing**
- `core/pdf_annotator.py` - PDF annotation engine with highlight and note creation
- `core/pdf_indexer.py` - Tag extraction and indexing (parallel/streaming modes)
- `core/excel_processor.py` - Excel file reading and data extraction
- `core/watermark.py` - Watermark generation and overlay
- `core/preview_generator.py` - PDF preview image generation

**Configuration**
- `config/annotation_config.py` - **AnnotationConfig dataclass** (centralized settings)
- `config/processing_config.py` - Processing thresholds and performance tuning
- `config/app_config.py` - Flask app configuration
- `config/tag_matching_config.py` - Tag pattern matching rules

**Tag Processing**
- `tag_engine/parser.py` - Tag pattern extraction and validation
- `tag_engine/filters.py` - Tag filtering and deduplication
- `tag_engine/color_rules.py` - Color assignment based on rules

**Analysis**
- `analysis/column_analysis.py` - Excel column type detection
- `analysis/excel_helpers.py` - Excel data validation and helpers
- `analysis/tag_parts.py` - Tag component parsing and analysis

**Reporting**
- `reports/html_generator.py` - HTML report generation
- `reports/excel_exporter.py` - Excel annotation and export

**Web Layer**
- `web/upload_routes.py` - File upload endpoints
- `web/process_routes.py` - PDF processing endpoints
- `web/download_routes.py` - File download endpoints
- `web/excel_routes.py` - Excel analysis endpoints
- `web/socketio_handlers.py` - WebSocket event handlers

**Session Management**
- `session/manager.py` - Session state and file tracking
- `session/cleanup.py` - Automatic file cleanup (24h retention)

**Utilities**
- `utils/file_helpers.py` - File operations and validation
- `utils/progress_callback.py` - Progress tracking helpers

### Processing Flow

```
Upload PDF + Excel → Session storage → Build tag index (parallel if >20 pages)
    → Match tags from Excel → Highlight in PDF + add notes
    → Optional: watermarks, Excel annotation → Download
```

### Key Patterns

1. **Session Isolation** - Each client gets UUID, files namespaced as `{session_id}_{filename}`

2. **Adaptive Processing** (auto-selected by file size):
   - Standard mode (< 50MB): Memory-loaded
   - Streaming mode (≥ 50MB): Chunk-based
   - Parallel indexing (> 20 pages): Multi-threaded

3. **Real-time Progress** - WebSocket via Flask-SocketIO:
   ```python
   socketio.emit('progress_update', {'progress': 50, 'message': '...'}, room=session_id)
   ```

4. **Memory Management** - Garbage collection every 100 pages, PyMuPDF cache shrinking

### Tag Extraction

Pattern in `pid_annotator/tag_engine/parser.py`:
```python
r'\b[A-Za-z0-9]{1,5}[-\.][A-Za-z0-9]{1,5}[-\.][A-Za-z0-9]{1,5}(?:[-\.][A-Za-z0-9]{1,5}){0,2}\b'
```
Matches 3-5 part tags: `TAG-001-A`, `SYS.SUB.COMP`, `A.B.C.D.E`

### Watermark Implementation

Two-library approach:
1. **ReportLab** - Generate overlay PDF
2. **PyPDF2** - Merge overlay onto pages (handles rotations)

## Configuration

### AnnotationConfig Pattern

The application uses a centralized `AnnotationConfig` dataclass for all processing settings:

```python
from pid_annotator.config.annotation_config import AnnotationConfig

# Create configuration with sensible defaults
config = AnnotationConfig(
    tag_column="Tag ID",
    comment_columns=["Description", "Notes"],
    highlight_color=(1, 1, 0),  # RGB yellow
    header_row=6
)

# Pass to processing functions
annotate_pdf_with_progress(pdf_path, output_path, config, progress_callback)
```

**Processing parameters** (`pid_annotator/config/processing_config.py`):
```python
PARALLEL_INDEXING_ENABLED = True
MAX_WORKERS = os.cpu_count() - 1
STREAMING_THRESHOLD_MB = 50
MEMORY_CLEANUP_BATCH_SIZE = 100
```

**Code style** (`pyproject.toml`):
- Line length: 120
- Formatter: black
- Imports: isort (black profile)

## Key Implementation Notes

### Adding a Route

Create a new blueprint in `pid_annotator/web/`:

```python
# pid_annotator/web/new_routes.py
from flask import Blueprint, jsonify, session

bp = Blueprint('new_routes', __name__)

@bp.route('/new_route', methods=['POST'])
def new_route():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session'}), 400
    # ...
    return jsonify({'success': True})
```

Register in `pid_annotator/web/__init__.py`:

```python
from .new_routes import bp as new_bp
app.register_blueprint(new_bp)
```

### Working with AnnotationConfig

```python
from pid_annotator.config.annotation_config import AnnotationConfig
from pid_annotator.core.pdf_annotator import annotate_pdf_with_progress

# Create configuration
config = AnnotationConfig(
    tag_column="Tag ID",
    comment_columns=["Description", "Location"],
    highlight_color=(1, 0.8, 0),  # Orange
    header_row=1,
    watermark_text="REVIEWED"
)

# Use in processing
annotate_pdf_with_progress(
    pdf_path="/path/to/input.pdf",
    output_path="/path/to/output.pdf",
    config=config,
    progress_callback=lambda p, m: print(f"{p}% - {m}")
)
```

### Modifying Core Processing

- Always call `progress_callback()` with percentage 0-100
- Use `fitz.TOOLS.store_shrink(100)` after heavy operations
- Set `page = None` explicitly after processing
- Test with both small (<50MB) and large (>50MB) files
- Processing logic is now in focused modules (see Module Structure above)

### Session Data

Stored in Flask session: `pdf_files`, `excel_file`, `session_id`, `columns`, `header_row`

File cleanup runs on every request via `@app.before_request` (1-hour retention, throttled to every 5 minutes).

## Docker/Deployment

- **Base image:** `python:3.11-slim-bookworm` (ARM64 compatible)
- **Ports:** 5001 (local dev), 8080 (Docker production)
- **Memory optimization:** `MALLOC_ARENA_MAX=2` reduces fragmentation on Raspberry Pi
- **Gunicorn:** eventlet worker, max-requests 1000 for worker recycling

See `RASPBERRY_PI_QUICKSTART.md` for Pi 5 deployment.
