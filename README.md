# PID Annotator - CasaOS / Raspberry Pi Docker Deployment

Web app that annotates P&ID PDF documents with metadata from Excel component lists. This branch contains only the files needed to build and run the Docker image on a Raspberry Pi (ARM64) with CasaOS.

## Requirements

- Raspberry Pi 5 (4GB or 8GB RAM) running 64-bit OS
- CasaOS installed ([install guide](https://casaos.io))
- Docker (included with CasaOS)

## Quick Start

### Option 1: CasaOS Custom Install

1. In CasaOS, go to **App Store** > **Custom Install**
2. Paste the contents of `docker-compose.yml`
3. Click **Install**

### Option 2: Command Line

```bash
# Clone this branch
git clone -b claude/docker-raspberrypi-casaos-H7s0a https://github.com/rudikdk/Annotator.git
cd Annotator

# Create storage directories
mkdir -p uploads output

# Build and start
docker-compose up -d --build
```

Access the web interface at **http://your-pi-ip:5001**

## Configuration

### 4GB Raspberry Pi 5 (default)

The default settings are tuned for the 4GB model:
- 1 Gunicorn worker
- 1.75GB memory limit
- 2.5 CPU cores

### 8GB Raspberry Pi 5

Edit `docker-compose.yml` to use these values:

```yaml
environment:
  GUNICORN_WORKERS: "2"
mem_limit: 2560m
mem_reservation: 768m
cpus: 3.0
```

### Timezone

Change `TZ` in the environment section (default: `Europe/Copenhagen`).

## Usage

1. Open **http://your-pi-ip:5001** in a browser
2. Upload one or more P&ID PDF files
3. Upload the corresponding Excel component list
4. Configure column mappings and settings
5. Click **Annotate** to process
6. Download annotated PDFs and reports

## Monitoring

```bash
# View logs
docker-compose logs -f pid-annotator

# Check health
docker inspect --format='{{.State.Health.Status}}' pid-annotator-web

# Resource usage
docker stats pid-annotator-web
```

## File Structure

```
Dockerfile              # Multi-stage ARM64 build
docker-compose.yml      # CasaOS-optimized compose with labels
entrypoint.sh           # Startup script with safety checks
app.py                  # Flask web server
pid_annotator_core.py   # PDF/Excel processing engine
report_template.py      # Report generation
templates/index.html    # Web UI (React 18 + TailwindCSS)
requirements.txt        # Python dependencies
```

## Author

Rudi S. Kaergaard (rudikdk@gmail.com)
