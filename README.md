# PID Annotator Web Application

A web-based version of the PID Annotator tool that runs in Docker containers, specifically optimized for Raspberry Pi 5 with CasaOS.

## Features

- **Same Functionality**: Identical features to the desktop version
- **Web Interface**: Modern, responsive web UI with dark theme
- **Real-time Progress**: Live progress updates via WebSockets
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
| Progress Tracking | ✅ | ✅ (Real-time) |
| Dark Theme | ✅ | ✅ |
| File Drag & Drop | ❌ | ✅ |
| Multi-user Support | ❌ | ✅ |
| Remote Access | ❌ | ✅ |

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
**Original Desktop Version:** PID Annotator GUI  
**Web Version:** Optimized for Raspberry Pi 5 + CasaOS
