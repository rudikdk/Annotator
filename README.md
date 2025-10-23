# PID Annotator Web Application

A web-based application for annotating P&ID (Piping & Instrumentation Diagram) PDF documents with metadata from Excel component lists. Can run as a local server (localhost:5001) or in Docker containers, specifically optimized for Raspberry Pi 5 with CasaOS.

**Author:** Rudi S. Kærgaard (rudikdk@gmail.com)

## Features

- **Flexible Deployment**: Run locally on localhost:5001 or deploy in Docker containers
- **Modern Web Interface**: React 18 with TailwindCSS, responsive design with dark mode
- **Real-time Progress**: Live progress updates via WebSockets (Socket.IO)
- **File Upload**: Drag & drop support for PDF and Excel files
- **Multi-File Processing**: Support for multiple PDFs with single Excel file
- **Excel Annotation**: Automatically highlights found tags in Excel file
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

1. **Upload Files:**
   - Drag & drop or click to upload your PID PDF file(s) - supports multiple PDFs
   - Drag & drop or click to upload your Excel component list (one Excel file)

2. **Configure Settings:**
   - Set the header row (default: 6)
   - Select the tag column
   - Choose comment columns to include
   - Configure highlighting colors
   - Enable/disable watermark feature
   - Enable/disable Excel annotation (highlights found tags)

3. **Process:**
   - Click "Start" for full processing
   - Click "Test Run" to process only 100 tags for testing

4. **Download:**
   - Download the annotated PDF(s) when processing completes
   - Download the annotated Excel file if Excel annotation is enabled
   - Files are automatically cleaned up after 24 hours

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
- **Backend**: Flask with Flask-SocketIO for real-time updates
- **Frontend**: React 18 with TailwindCSS
- **PDF Processing**: PyMuPDF (fitz) with memory optimization
- **Excel Processing**: pandas + openpyxl with annotation support
- **Watermarking**: ReportLab + PyPDF2 two-library approach
- **Containerization**: Docker with multi-stage build (optional)
- **Local Server**: Flask development server (localhost:5001)
- **Production Server**: Gunicorn with eventlet workers (Docker)
- **Real-time Communication**: Socket.IO (WebSocket)

### Processing Pipeline

```
Upload PDF(s) + Excel
    ↓
Session-namespaced storage (UUID)
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
    ↓
Auto-cleanup after 24 hours
```

### File Structure
```
Annotator/
├── app.py                      # Main Flask application with routes
├── pid_annotator_core.py       # Core processing engine
├── templates/
│   └── index.html              # React 18 SPA with TailwindCSS
├── static/                     # Static assets (auto-created)
├── uploads/                    # Temporary file uploads
├── output/                     # Generated PDF files
├── persistent_uploads/         # Docker volume mount
├── persistent_output/          # Docker volume mount
├── data/                       # Application data
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata and tool configs
├── Dockerfile                  # Multi-stage container build
├── docker-compose.yml          # Container orchestration
├── entrypoint.sh               # Container startup script
├── CLAUDE.md                   # Project instructions for Claude Code
├── OPTIMIZATION_GUIDE.md       # Performance optimization guide
├── README.md                   # This file
└── fix python 3.13.bat         # Python 3.13 compatibility fix
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
| Easy Deployment | ✅ (pip install) | ✅ (Docker Compose) |

## Development

### Local Server Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run local server (localhost:5001)
python app.py

# Install dev dependencies (for testing and code quality tools)
pip install -e ".[dev]"
```

The local server runs on `http://localhost:5001` by default. This is perfect for:
- Personal use on your local machine
- Development and testing
- Quick access without Docker setup
- Single-user scenarios

For production or multi-user deployment, use Docker (see Deployment section above).

### Testing & Code Quality

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=pid_annotator_web --cov-report=html

# Code formatting
black .

# Import sorting
isort .

# Linting
flake8 .

# Type checking
mypy .
```

### Code Style Configuration

Per [pyproject.toml](pyproject.toml):
- **Line length:** 120 characters
- **Formatter:** black with Python 3.8+ target
- **Import sorting:** isort with black profile
- **Type checking:** mypy (lenient, ignore missing imports)

### Building for Different Architectures

```bash
# For ARM64 (Raspberry Pi 5)
docker buildx build --platform linux/arm64 -t pid-annotator-web .

# For AMD64 (x86_64)
docker buildx build --platform linux/amd64 -t pid-annotator-web .

# Multi-platform build
docker buildx build --platform linux/arm64,linux/amd64 -t pid-annotator-web .
```

### Docker Operations

```bash
# Build and run with Docker Compose (production)
docker-compose up -d --build

# View logs
docker-compose logs -f pid-annotator

# Stop container
docker-compose down

# Restart container
docker-compose restart pid-annotator

# Check container status
docker ps
```

## Python Version Compatibility

- **Recommended:** Python 3.11 (used in Docker image)
- **Supported:** Python 3.8+
- **Python 3.13:** Compatible with fix script
  - If you encounter errors with Python 3.13, run: `fix python 3.13.bat`
  - This resolves compatibility issues with newer Python versions

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

- **Performance Optimization:** Added parallel indexing, streaming mode, and adaptive processing
- **Python 3.13 Support:** Compatibility fix script included
- **Multi-File Support:** Process multiple PDFs with single Excel file
- **Excel Annotation:** Automatic highlighting of found tags in Excel
- **Session Management:** UUID-based session isolation
- **Auto-Cleanup:** 24-hour file retention policy
- **React 18 Frontend:** Modern UI with TailwindCSS and dark mode
