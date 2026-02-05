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

### Core Files

| File | Purpose |
|------|---------|
| `app.py` | Flask routes, session management, WebSocket handlers |
| `pid_annotator_core.py` | PDF/Excel processing engine, tag extraction |
| `report_template.py` | HTML report generation |
| `templates/index.html` | React 18 SPA with TailwindCSS |
| `entrypoint.sh` | Docker startup with safety checks |

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

Pattern in `pid_annotator_core.py:160`:
```python
r'\b[A-Za-z0-9]{1,5}[-\.][A-Za-z0-9]{1,5}[-\.][A-Za-z0-9]{1,5}(?:[-\.][A-Za-z0-9]{1,5}){0,2}\b'
```
Matches 3-5 part tags: `TAG-001-A`, `SYS.SUB.COMP`, `A.B.C.D.E`

### Watermark Implementation

Two-library approach:
1. **ReportLab** - Generate overlay PDF
2. **PyPDF2** - Merge overlay onto pages (handles rotations)

## Configuration

**Processing parameters** (`pid_annotator_core.py`):
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
```python
@app.route('/new_route', methods=['POST'])
def new_route():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session'}), 400
    # ...
    return jsonify({'success': True})
```

### Modifying Core Processing
- Always call `progress_callback()` with percentage 0-100
- Use `fitz.TOOLS.store_shrink(100)` after heavy operations
- Set `page = None` explicitly after processing
- Test with both small (<50MB) and large (>50MB) files

### Session Data
Stored in Flask session: `pdf_files`, `excel_file`, `session_id`, `columns`, `header_row`

File cleanup runs on every request via `@app.before_request` (24-hour retention).

## Docker/Deployment

- **Base image:** `python:3.11-slim-bookworm` (ARM64 compatible)
- **Ports:** 5001 (local dev), 8080 (Docker production)
- **Memory optimization:** `MALLOC_ARENA_MAX=2` reduces fragmentation on Raspberry Pi
- **Gunicorn:** eventlet worker, max-requests 1000 for worker recycling

See `RASPBERRY_PI_QUICKSTART.md` for Pi 5 deployment.
