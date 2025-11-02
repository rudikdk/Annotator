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

# Build for ARM64 (Raspberry Pi 5) - multi-platform with BuildKit
docker buildx create --use
docker buildx build --platform linux/arm64 -t pid-annotator-web:arm64 .

# Build for AMD64
docker buildx build --platform linux/amd64 -t pid-annotator-web:amd64 .

# Multi-platform build (both ARM64 and AMD64)
docker buildx build --platform linux/arm64,linux/amd64 -t pid-annotator-web:latest .

# Manual single-platform build (no BuildKit)
docker build --platform linux/arm64 -t pid-annotator-web .
```

### CasaOS Deployment

```bash
# Deploy via CasaOS UI
# 1. Open CasaOS web interface
# 2. Go to App Store → Custom Install
# 3. Upload docker-compose.yml
# 4. Configure settings and install

# Or manually import compose file
casaos-cli app install docker-compose.yml
```

### Raspberry Pi Specific Commands

```bash
# Check architecture
uname -m  # Should show aarch64 or arm64

# Monitor temperature
watch -n 2 vcgencmd measure_temp

# Check memory usage
free -h

# Monitor Docker container resources
docker stats pid-annotator-web

# Check disk space
df -h

# View entrypoint startup logs
docker-compose logs pid-annotator | grep "STARTUP SUMMARY" -A 10
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
   - **MALLOC_ARENA_MAX=2**: Reduces memory fragmentation on Raspberry Pi

4. **Tag Format Support**
   - Accepts both `-` and `.` delimiters (A.B.C or A-B-C)
   - 3-5 part hierarchical tags
   - Case-insensitive normalization
   - Multiple variant lookup

5. **Entrypoint Safety System** ([entrypoint.sh](entrypoint.sh))
   - Architecture verification (ARM64 check)
   - Memory availability validation (warns if <1500MB)
   - Disk space monitoring (warns if <1000MB)
   - CPU temperature checks (Raspberry Pi specific)
   - Port and worker count validation
   - Automatic permission fixes for mounted volumes
   - Comprehensive startup logging
   - Switches to non-root user (appuser) after setup

## File Organization

- **[app.py](app.py)** - Flask routes, session management, WebSocket handlers
- **[pid_annotator_core.py](pid_annotator_core.py)** - PDF/Excel processing engine
- **[report_template.py](report_template.py)** - HTML report generation
- **[templates/index.html](templates/index.html)** - React SPA interface
- **[requirements.txt](requirements.txt)** - Python dependencies
- **[Dockerfile](Dockerfile)** - Multi-stage container build
- **[docker-compose.yml](docker-compose.yml)** - Container orchestration
- **[entrypoint.sh](entrypoint.sh)** - Container startup script with safety checks
- **[.dockerignore](.dockerignore)** - Docker build exclusions
- **[pyproject.toml](pyproject.toml)** - Project metadata, tool configs
- **[OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)** - Performance optimization documentation
- **[RASPBERRY_PI_QUICKSTART.md](RASPBERRY_PI_QUICKSTART.md)** - Raspberry Pi 5 quick start guide
- **uploads/** - Temporary uploaded files (auto-cleaned)
- **output/** - Generated annotated PDFs (auto-cleaned)
- **data/profiles/** - Configuration profiles (persistent)

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
- 100MB file upload limit (configurable)
- Session-based file isolation
- Container runs as non-root user `appuser`
- Resource limits: 1792MB memory (4GB Pi), 2560MB (8GB Pi), 2.5-3.0 CPU cores
- Entrypoint script validates security before startup

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
- **Ports:** 8080 (internal and external default)
- **Port mapping:** Configurable in docker-compose.yml (e.g., `"9000:8080"` for external port 9000)
- **Volumes:**
  - `./persistent_uploads:/app/uploads`
  - `./persistent_output:/app/output`
  - `./data:/app/data`
- **tmpfs mounts:** `/tmp` and `/app/.cache` for reduced SD card wear
- **Memory optimization:** `MALLOC_ARENA_MAX=2` reduces fragmentation

### Resource Limits (Raspberry Pi 5)

**4GB Model (Default):**

```yaml
deploy:
  resources:
    limits:
      memory: 1792M  # 1.75GB
      cpus: '2.5'
    reservations:
      memory: 512M
      cpus: '0.5'
environment:
  - GUNICORN_WORKERS=1
tmpfs:
  - /tmp:size=384M
  - /app/.cache:size=192M
```

**8GB Model (Recommended):**

```yaml
deploy:
  resources:
    limits:
      memory: 2560M  # 2.5GB
      cpus: '3.0'
    reservations:
      memory: 768M
      cpus: '0.5'
environment:
  - GUNICORN_WORKERS=2
tmpfs:
  - /tmp:size=512M
  - /app/.cache:size=256M
```

### Health Checks

Container includes health check on port 8080:

```bash
curl -f http://localhost:8080/ || exit 1
```

Health check configuration:
- **Interval:** 30s
- **Timeout:** 5s
- **Start period:** 45s (allows slow SD card startup)
- **Retries:** 3

## Raspberry Pi 5 Deployment

### Prerequisites

- Raspberry Pi 5 (4GB or 8GB RAM)
- 64-bit Raspberry Pi OS (Bookworm recommended)
- Docker and Docker Compose installed
- 10GB free disk space minimum
- Active cooling recommended (heatsink or fan)
- Class 10 SD card or faster (SSD preferred)

### Quick Deployment

See [RASPBERRY_PI_QUICKSTART.md](RASPBERRY_PI_QUICKSTART.md) for step-by-step guide.

```bash
# Clone repository
git clone https://github.com/your-repo/pid-annotator.git
cd pid-annotator

# Configure for 4GB or 8GB model (edit docker-compose.yml if needed)

# Deploy
docker-compose up -d --build

# Access
# http://your-pi-ip:8080
```

### Performance Optimization

**MALLOC_ARENA_MAX=2** (Dockerfile line 46):
- Reduces memory fragmentation on Raspberry Pi
- Prevents excessive memory arena allocation
- Improves memory stability for long-running processes

**tmpfs Mounts** (docker-compose.yml):
- Reduces SD card wear for temporary files
- Improves I/O performance
- Automatically managed by Docker

**Health Check Start Period** (45s):
- Accommodates slow SD card startup
- Prevents false health check failures
- Allows entrypoint.sh validation to complete

**Entrypoint Safety Features** (entrypoint.sh):
- Pre-startup validation catches configuration issues
- Automatic permission fixes for mounted volumes
- Temperature monitoring prevents thermal issues
- Memory/disk checks prevent resource exhaustion
- Comprehensive logging aids troubleshooting

### BuildKit Optimization

Docker BuildKit improves build performance:

**Enabled features:**
- Layer caching for faster rebuilds
- Parallel stage execution
- Cache mounts for pip downloads
- Prefer binary wheels (--prefer-binary)

**Dockerfile optimizations:**

```dockerfile
# BuildKit cache mount for pip
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --upgrade pip setuptools wheel && \
    pip install --prefer-binary -r requirements.txt
```

**Benefits:**
- 2-3x faster builds on subsequent runs
- Reduced network usage (cached pip downloads)
- Better ARM64 binary wheel utilization

### CasaOS Integration

The application includes CasaOS-specific labels:

```yaml
labels:
  net.casaos.app.name: "PID Annotator"
  net.casaos.app.version: "1.0"
  net.casaos.app.author: "Rudi S. Kærgård"
  net.casaos.app.description: "Annotate P&ID PDF documents with Excel metadata"
  net.casaos.app.category: "Utilities"
  net.casaos.app.icon: "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/pdf.png"
  net.casaos.app.web-port: "8080"
  net.casaos.app.protocol: "http"
  net.casaos.app.healthcheck: "http://localhost:8080/"
```

**Features:**
- One-click installation from CasaOS app store
- Dashboard integration with icon and metadata
- Port configuration via UI
- Health monitoring integration
- Named volumes for easy management

### Port Configuration

**Standard Port:** 8080

- **Internal port:** Always 8080 (Dockerfile EXPOSE 8080)
- **External port:** Configurable in docker-compose.yml
- **Default mapping:** `"8080:8080"` (direct mapping)
- **Custom mapping:** `"YOUR_PORT:8080"` (e.g., `"9000:8080"`)

**Why port 8080:**
- Standard for web applications in Docker
- Compatible with CasaOS expectations
- Avoids conflict with common services (80, 443, 5000, 5001)
- Consistent with industry conventions

**Changing the port:**

```yaml
# Edit docker-compose.yml
ports:
  - "9000:8080"  # Use external port 9000

# Restart container
docker-compose down
docker-compose up -d
```

Access via: `http://your-pi-ip:9000`

### Temperature Monitoring

Raspberry Pi 5 temperature thresholds:
- **Normal:** < 65°C
- **Warning:** 65-75°C (entrypoint.sh logs warning)
- **Throttling:** > 75°C (performance degradation)

Monitor temperature:

```bash
vcgencmd measure_temp

# Continuous monitoring
watch -n 2 vcgencmd measure_temp
```

Cooling recommendations:
- Minimum: Passive heatsink
- Recommended: Active cooling fan
- Heavy loads: Case with fan and heatsink

### Troubleshooting Raspberry Pi Issues

**Memory Issues:**
- Reduce GUNICORN_WORKERS to 1
- Lower memory limit in docker-compose.yml
- Close unnecessary services
- Monitor with: `docker stats`

**Temperature Throttling:**
- Add heatsink or fan
- Reduce CPU limit in docker-compose.yml
- Monitor with: `vcgencmd measure_temp`

**SD Card Performance:**
- Use Class 10 or UHS-I SD card
- Consider SSD via USB 3.0 for best performance
- Monitor I/O: `iostat -x 2`

**Container Won't Start:**
- Check logs: `docker-compose logs pid-annotator`
- Verify architecture: `uname -m` (should be aarch64)
- Check entrypoint.sh output for validation errors
- Verify disk space: `df -h`

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

## Development Workflow

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/your-repo/pid-annotator.git
cd pid-annotator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py

# Access at http://localhost:5001
```

### Docker Development

```bash
# Build development image
docker build -t pid-annotator-dev .

# Run with live code mounting
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/app.py:/app/app.py \
  -v $(pwd)/pid_annotator_core.py:/app/pid_annotator_core.py \
  -v $(pwd)/templates:/app/templates \
  --name pid-dev \
  pid-annotator-dev

# View logs
docker logs -f pid-dev
```

### Testing Workflow

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_core.py

# Run with coverage
pytest --cov=pid_annotator_web --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Code Quality Checks

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type check
mypy .

# Run all checks
black . && isort . && flake8 . && mypy . && pytest
```

## Production Deployment Checklist

- [ ] Update Dockerfile if dependencies changed
- [ ] Update docker-compose.yml resource limits
- [ ] Test build on target architecture (ARM64 for Pi 5)
- [ ] Verify entrypoint.sh executes successfully
- [ ] Test health check endpoint
- [ ] Verify port configuration (8080)
- [ ] Test with sample PDFs (small, medium, large)
- [ ] Verify WebSocket connectivity
- [ ] Test configuration profiles
- [ ] Verify HTML report generation
- [ ] Check memory usage under load
- [ ] Monitor temperature during processing
- [ ] Verify automatic file cleanup (24 hours)
- [ ] Test session isolation (multiple users)
- [ ] Document any configuration changes

## Common Issues & Solutions

### Issue: ARM64 Build Fails

**Symptom:** `libmupdf-dev` not found

**Solution:** Use Bookworm base image (already in Dockerfile):

```dockerfile
FROM --platform=linux/arm64 python:3.11-slim-bookworm
```

### Issue: Memory Leak on Long-Running Container

**Symptom:** Memory usage grows over time

**Solution:** Enabled in Dockerfile and Gunicorn config:

```dockerfile
ENV MALLOC_ARENA_MAX=2
```

```bash
# Gunicorn max-requests restarts workers
--max-requests 1000 \
--max-requests-jitter 50
```

### Issue: Slow Builds

**Symptom:** Docker build takes 10+ minutes

**Solution:** Enable BuildKit (already configured):

```dockerfile
# Dockerfile uses BuildKit cache mounts
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --prefer-binary -r requirements.txt
```

Build with:

```bash
DOCKER_BUILDKIT=1 docker build -t pid-annotator-web .
```

### Issue: Permission Denied on Mounted Volumes

**Symptom:** Cannot write to uploads/output directories

**Solution:** entrypoint.sh automatically fixes (already implemented):

```bash
# entrypoint.sh runs as root, fixes permissions, then switches to appuser
fix_directory_permissions "/app/uploads"
fix_directory_permissions "/app/output"
fix_directory_permissions "/app/.cache"
```

### Issue: Health Check Fails on Startup

**Symptom:** Container marked unhealthy immediately

**Solution:** Health check has 45s start period (already configured):

```yaml
healthcheck:
  start_period: 45s  # Allows entrypoint.sh validation
  interval: 30s
  timeout: 5s
  retries: 3
```

## Performance Tuning

### For 4GB Raspberry Pi 5

```yaml
environment:
  - GUNICORN_WORKERS=1
  - PORT=8080
  - MALLOC_ARENA_MAX=2
mem_limit: 1792m
mem_reservation: 512m
cpus: 2.5
tmpfs:
  - /tmp:size=384M
  - /app/.cache:size=192M
```

**Expected performance:**
- 10 pages: ~7 seconds
- 100 pages: ~18 seconds
- 500 pages: ~2.5 minutes

### For 8GB Raspberry Pi 5

```yaml
environment:
  - GUNICORN_WORKERS=2
  - PORT=8080
  - MALLOC_ARENA_MAX=2
mem_limit: 2560m
mem_reservation: 768m
cpus: 3.0
tmpfs:
  - /tmp:size=512M
  - /app/.cache:size=256M
```

**Expected performance:**
- 10 pages: ~5 seconds
- 100 pages: ~12 seconds
- 500 pages: ~2 minutes

### For x86_64 Servers

```yaml
environment:
  - GUNICORN_WORKERS=4
  - PORT=8080
mem_limit: 4G
mem_reservation: 1G
cpus: 4.0
```

**Expected performance:**
- 10 pages: ~3 seconds
- 100 pages: ~8 seconds
- 500 pages: ~1 minute

## Documentation Links

- **[README.md](README.md)** - User documentation and features
- **[OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)** - Performance tuning details
- **[RASPBERRY_PI_QUICKSTART.md](RASPBERRY_PI_QUICKSTART.md)** - Raspberry Pi 5 quick start
- **[requirements.txt](requirements.txt)** - Python dependencies
- **[docker-compose.yml](docker-compose.yml)** - Docker configuration
- **[Dockerfile](Dockerfile)** - Container build instructions
- **[entrypoint.sh](entrypoint.sh)** - Startup script with safety checks

## Version History

### v2.2 (Current)
- HTML report generation with interactive features
- Enhanced FAQ system (30+ questions)
- Raspberry Pi Quick Start Guide
- Documentation updates (port standardization, entrypoint.sh)

### v2.1
- Interactive tutorial system
- Configuration profiles
- Enhanced UI/UX

### v2.0
- Multi-file support
- Excel annotation
- Performance optimization (parallel, streaming)
- Docker optimization (BuildKit, tmpfs, MALLOC_ARENA_MAX)
- Entrypoint safety checks

### v1.0
- Initial release
- Basic PDF annotation
- Excel integration
- Docker deployment

## Contact & Support

**Author:** Rudi S. Kærgaard
**Email:** rudikdk@gmail.com

For issues or questions:
- Check [README.md](README.md) FAQ section
- Review [RASPBERRY_PI_QUICKSTART.md](RASPBERRY_PI_QUICKSTART.md) for Pi-specific help
- Check Docker logs: `docker-compose logs pid-annotator`
- Review [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) for performance tuning
