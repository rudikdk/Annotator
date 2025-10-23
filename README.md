# PID Annotator Web Application

A web-based version of the PID Annotator tool that runs in Docker containers, specifically optimized for Raspberry Pi 5 with CasaOS.

## Features

- **Same Functionality**: Identical features to the desktop version
- **Web Interface**: Modern, responsive web UI with dark theme
- **Real-time Progress**: Live progress updates via WebSockets
- **File Upload**: Drag & drop support for PDF and Excel files
- **Docker Ready**: Optimized for ARM64 architecture (Raspberry Pi 5)
- **CasaOS Compatible**: Easy deployment on CasaOS systems

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Raspberry Pi 5 with 64-bit OS (recommended)
- At least 2GB RAM available

### Deployment

1. **Clone or copy the application files to your Raspberry Pi**

2. **Build and run with Docker Compose:**
   ```bash
   cd pid-web-app
   docker-compose up -d --build
   ```

3. **Access the application:**
   - Open your browser and go to: `http://your-pi-ip:18080`
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
   - Drag & drop or click to upload your PID PDF file
   - Drag & drop or click to upload your Excel component list

2. **Configure Settings:**
   - Set the header row (default: 6)
   - Select the tag column
   - Choose comment columns to include
   - Configure highlighting and watermark feature

3. **Process:**
   - Click "Start" for full processing
   - Click "Test Run" to process only 100 tags for testing

4. **Download:**
   - Download the annotated PDF when processing completes

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

## Features Comparison

| Feature | Desktop App | Web App |
|---------|-------------|---------|
| PDF Annotation | ✅ | ✅ |
| Excel Integration | ✅ | ✅ |
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
```

### Port Already in Use
```bash
# Check what's using port 18080
sudo netstat -tulpn | grep 18080

# Or change the port in docker-compose.yml
ports:
  - "19080:8080"  # Use different external port
```

### Memory Issues
```bash
# Check system memory
free -h

# Reduce memory limits in docker-compose.yml if needed
deploy:
  resources:
    limits:
      memory: 1G  # Reduce from 2G
```

### File Upload Issues
- Check that upload directories exist and have proper permissions
- Ensure sufficient disk space is available
- Check file size limits (default: 100MB)

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
```

### Building for Different Architectures
```bash
# For ARM64 (Raspberry Pi 5)
docker buildx build --platform linux/arm64 -t pid-annotator-web .

# For AMD64 (x86_64)
docker buildx build --platform linux/amd64 -t pid-annotator-web .
```

## Security Notes

- The application runs as a non-root user inside the container
- File uploads are validated and secured
- Session-based file isolation prevents user conflicts
- Resource limits prevent resource exhaustion

## Support

For issues or questions:
- Check the FAQ in the web interface
- Review the troubleshooting section above
- Check Docker logs for error messages

## Credits

**Created by:** Rudi S. Kærgaard  
**Email:** rudikdk@gmail.com  
**Original Desktop Version:** PID Annotator GUI  
**Web Version:** Optimized for Raspberry Pi 5 + CasaOS
