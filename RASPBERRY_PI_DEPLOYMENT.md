# PID Annotator - Raspberry Pi 5 Deployment Guide

Complete guide for deploying PID Annotator on Raspberry Pi 5 (64-bit) with CasaOS.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start with CasaOS](#quick-start-with-casaos)
- [Manual Docker Installation](#manual-docker-installation)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

---

## Prerequisites

### Hardware Requirements
- **Raspberry Pi 5** (4GB or 8GB RAM model)
- **Storage**: Minimum 8GB free space (16GB+ recommended for large PDFs)
- **SD Card**: Class 10 or better (UHS-I/UHS-II recommended)
- **Power**: Official 27W USB-C power supply
- **Network**: Ethernet or WiFi connection

### Software Requirements
- **OS**: Raspberry Pi OS (64-bit) - Bookworm or later
- **Docker**: Version 20.10 or later
- **CasaOS**: Version 0.4.0 or later (optional but recommended)

### Check Your System
```bash
# Verify 64-bit OS
uname -m
# Should output: aarch64

# Check available memory
free -h

# Check Docker version
docker --version

# Check disk space
df -h
```

---

## Quick Start with CasaOS

### Method 1: Import via CasaOS UI

1. **Access CasaOS Dashboard**
   ```
   http://your-pi-ip:80
   ```

2. **Navigate to App Store** → **Custom Install**

3. **Import Docker Compose**
   - Upload `docker-compose.casaos.yml` from this repository
   - CasaOS will automatically detect all labels and configuration

4. **Configure Settings**
   - **Port**: 8080 (or change to preferred port)
   - **Memory Limit**:
     - 4GB Pi: Set to 1536 MB
     - 8GB Pi: Set to 2560 MB (recommended)
   - **Timezone**: Adjust `TZ` environment variable to your timezone

5. **Install and Start**
   - Click "Install"
   - Wait for build to complete (5-10 minutes first time)
   - Access at `http://your-pi-ip:8080`

### Method 2: Command Line Installation with CasaOS

1. **Clone or copy files to your Pi**
   ```bash
   cd /home/$USER/apps
   mkdir pid-annotator
   cd pid-annotator

   # Copy all files from this repository here
   ```

2. **Create persistent directories**
   ```bash
   mkdir -p persistent_uploads persistent_output
   chmod 755 persistent_uploads persistent_output
   ```

3. **Start with CasaOS compose file**
   ```bash
   docker-compose -f docker-compose.casaos.yml up -d --build
   ```

4. **Monitor logs**
   ```bash
   docker-compose -f docker-compose.casaos.yml logs -f pid-annotator
   ```

5. **Verify in CasaOS**
   - App should appear in CasaOS dashboard automatically
   - Health status will show green when ready

---

## Manual Docker Installation

For users not using CasaOS:

### Step 1: Install Docker (if not already installed)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
```

### Step 2: Prepare Application

```bash
# Create application directory
mkdir -p ~/pid-annotator
cd ~/pid-annotator

# Copy all application files here

# Create data directories
mkdir -p persistent_uploads persistent_output
chmod 755 persistent_uploads persistent_output
```

### Step 3: Configure for Your Pi Model

Edit `docker-compose.yml` and adjust resource limits:

**For Raspberry Pi 5 (4GB RAM):**
```yaml
mem_limit: 1536m
mem_reservation: 512m
cpus: 2.5
```

**For Raspberry Pi 5 (8GB RAM) - Recommended:**
```yaml
mem_limit: 2560m
mem_reservation: 768m
cpus: 3.0
```

### Step 4: Build and Start

```bash
# Build the image (takes 5-10 minutes first time)
docker-compose build

# Start the container
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Step 5: Verify Deployment

```bash
# Check container status
docker ps

# Test health endpoint
curl http://localhost:8080/

# View startup logs
docker logs pid-annotator-web
```

Access the application at: `http://your-pi-ip:8080`

---

## Performance Tuning

### For Optimal Performance

1. **Use Ethernet Connection**
   - Faster than WiFi for large file uploads
   - More stable for long processing tasks

2. **SD Card Optimization**
   ```bash
   # The docker-compose already uses tmpfs for /tmp
   # This reduces SD card wear during processing

   # Optional: Move Docker data to USB SSD
   sudo systemctl stop docker
   sudo mv /var/lib/docker /mnt/ssd/docker
   sudo ln -s /mnt/ssd/docker /var/lib/docker
   sudo systemctl start docker
   ```

3. **Enable zswap for Better Memory Management**
   ```bash
   # Add to /boot/firmware/cmdline.txt
   sudo nano /boot/firmware/cmdline.txt

   # Add: zswap.enabled=1 zswap.compressor=lz4
   # Then reboot
   sudo reboot
   ```

4. **Adjust Processing Parameters**

   Edit `pid_annotator_core.py` for your specific needs:
   ```python
   # For faster processing on small files (reduce overhead)
   PARALLEL_INDEXING_ENABLED = True
   MAX_WORKERS = 3  # Match CPU cores allocated

   # For large files (reduce memory usage)
   STREAMING_THRESHOLD_MB = 50  # Lower if running out of memory
   MEMORY_CLEANUP_BATCH_SIZE = 50  # More frequent cleanup
   ```

### Resource Monitoring

```bash
# Real-time resource usage
docker stats pid-annotator-web

# System resources
htop

# Disk I/O
sudo iotop

# Temperature monitoring (important for Pi!)
watch -n 1 vcgencmd measure_temp
```

### Raspberry Pi 5 Specific Optimizations

1. **Enable PCIe Gen 3** (if using NVMe SSD via HAT)
   ```bash
   sudo nano /boot/firmware/config.txt
   # Add: dtparam=pciex1_gen=3
   sudo reboot
   ```

2. **Active Cooling Recommendation**
   - Use official active cooler or case with fan
   - Prevents thermal throttling during heavy processing
   - Target: Keep under 70°C during processing

3. **Overclock (Optional, Advanced Users)**
   ```bash
   sudo nano /boot/firmware/config.txt
   # Add:
   over_voltage=6
   arm_freq=2600

   # Monitor stability carefully!
   ```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker logs pid-annotator-web

# Common issues:
# 1. Port already in use
sudo netstat -tulpn | grep 8080

# 2. Insufficient memory
free -h

# 3. Permissions issues
ls -la persistent_uploads persistent_output
sudo chown -R $USER:$USER persistent_*
```

### Out of Memory Errors

```bash
# Check container memory limit
docker inspect pid-annotator-web | grep -A 5 Memory

# Reduce memory limit or upgrade to 8GB Pi
# Edit docker-compose.yml:
mem_limit: 1024m  # For 4GB Pi with other services
```

### Slow Performance

1. **Check CPU throttling**
   ```bash
   # Check for throttling
   vcgencmd get_throttled

   # 0x0 = no throttling (good)
   # Other values indicate thermal or voltage throttling
   ```

2. **Verify SD card speed**
   ```bash
   # Test write speed
   dd if=/dev/zero of=test.img bs=1M count=1024 oflag=direct

   # Should be >30 MB/s for Class 10
   ```

3. **Check Docker storage driver**
   ```bash
   docker info | grep "Storage Driver"

   # Should be: overlay2 (best for Pi)
   ```

### Cannot Access Web Interface

```bash
# Check if container is running
docker ps | grep pid-annotator

# Check port binding
docker port pid-annotator-web

# Check firewall (if enabled)
sudo ufw status
sudo ufw allow 8080/tcp

# Test from Pi itself
curl http://localhost:8080/
```

### File Upload Fails

```bash
# Check disk space
df -h

# Check upload directory permissions
docker exec pid-annotator-web ls -la /app/uploads

# Check container logs during upload
docker logs -f pid-annotator-web
```

---

## Maintenance

### Regular Tasks

1. **Update Application**
   ```bash
   cd ~/pid-annotator

   # Pull latest code
   git pull  # If using git

   # Rebuild container
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Clean Up Old Files**
   ```bash
   # Application auto-cleans files after 24 hours
   # Manual cleanup if needed:
   docker exec pid-annotator-web find /app/uploads -mtime +1 -delete
   docker exec pid-annotator-web find /app/output -mtime +1 -delete
   ```

3. **View Logs**
   ```bash
   # Live logs
   docker-compose logs -f

   # Last 100 lines
   docker-compose logs --tail=100

   # Logs from specific time
   docker-compose logs --since 1h
   ```

4. **Backup Configuration**
   ```bash
   # Backup docker-compose and configs
   tar -czf pid-annotator-backup.tar.gz \
       docker-compose*.yml \
       Dockerfile \
       requirements.txt \
       persistent_uploads \
       persistent_output
   ```

### Health Monitoring

1. **Check Health Status**
   ```bash
   docker inspect pid-annotator-web | grep -A 10 Health
   ```

2. **Set Up Monitoring with CasaOS**
   - CasaOS automatically monitors health via labels
   - Check dashboard for status indicators

3. **Email Alerts (Optional)**
   ```bash
   # Install monitoring tool
   docker run -d --name watchtower \
     -v /var/run/docker.sock:/var/run/docker.sock \
     containrrr/watchtower --monitor-only \
     --notification-email-to your@email.com
   ```

### Performance Benchmarks

Expected processing times on Raspberry Pi 5 (8GB):

| PDF Size | Pages | Processing Time | Memory Used |
|----------|-------|-----------------|-------------|
| Small    | 10    | ~7 seconds      | ~300 MB     |
| Medium   | 100   | ~18 seconds     | ~600 MB     |
| Large    | 500   | ~2.5 minutes    | ~1.2 GB     |
| Very Large | 1000 | ~6 minutes     | ~1.8 GB     |

*Times include indexing, annotation, and watermark generation*

---

## Advanced Configuration

### Custom Port Configuration

```bash
# Change external port without modifying docker-compose.yml
docker run -d \
  -p 9090:8080 \
  --name pid-annotator-custom \
  pid-annotator-web:latest
```

### Reverse Proxy with Nginx

```nginx
# /etc/nginx/sites-available/pid-annotator
server {
    listen 80;
    server_name pid-annotator.local;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeouts for large file processing
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
```

### SSL/TLS with Let's Encrypt (via CasaOS)

CasaOS can automatically provision SSL certificates:
1. Go to Settings → SSL
2. Enable automatic SSL
3. Enter your domain name
4. CasaOS handles certificate renewal

---

## Support

### Resources
- **Documentation**: See [CLAUDE.md](CLAUDE.md) for architecture details
- **Performance Guide**: See [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)
- **Issues**: Report issues to the repository maintainer
- **Email**: rudikdk@gmail.com

### Before Reporting Issues

Please collect this information:

```bash
# System information
uname -a
cat /proc/cpuinfo | grep Model
free -h
df -h

# Docker information
docker --version
docker-compose --version
docker ps -a
docker logs pid-annotator-web --tail=50

# Application logs
docker exec pid-annotator-web python --version
docker exec pid-annotator-web ls -la /app
```

---

## License

See main README.md for license information.

**Author:** Rudi S. Kærgaard (rudikdk@gmail.com)

**Last Updated:** 2025-01-23
