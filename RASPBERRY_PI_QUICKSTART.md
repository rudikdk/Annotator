# Raspberry Pi 5 Quick Start Guide

**PID Annotator Web Application** - Fast deployment guide for Raspberry Pi 5

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Raspberry Pi 5** (4GB or 8GB RAM model)
- [ ] **64-bit Raspberry Pi OS** (Bookworm recommended)
- [ ] **Docker and Docker Compose** installed
- [ ] **10GB free disk space** minimum
- [ ] **Active internet connection** for initial setup
- [ ] **Cooling solution** (heatsink or fan recommended)
- [ ] **Class 10 SD card** or faster (UHS-I recommended, SSD even better)

---

## Quick 3-Step Deployment

### Step 1: Get the Application Files

Clone the repository or download the docker-compose.yml:

```bash
# Option A: Clone the repository (if available)
git clone https://github.com/your-repo/pid-annotator.git
cd pid-annotator

# Option B: Download docker-compose.yml manually
mkdir pid-annotator
cd pid-annotator
wget https://your-url/docker-compose.yml
```

### Step 2: Configure for Your Pi Model

**For Raspberry Pi 5 4GB (Default Configuration)**

No changes needed! The default docker-compose.yml is optimized for 4GB:

```yaml
environment:
  - GUNICORN_WORKERS=1
mem_limit: 1792m
mem_reservation: 512m
cpus: 2.5
tmpfs:
  - /tmp:size=384M
  - /app/.cache:size=192M
```

**For Raspberry Pi 5 8GB (Recommended Changes)**

Edit `docker-compose.yml` and update these values:

```yaml
environment:
  - GUNICORN_WORKERS=2  # Change from 1 to 2
mem_limit: 2560m  # Change from 1792m
mem_reservation: 768m  # Change from 512m
cpus: 3.0  # Change from 2.5
tmpfs:
  - /tmp:size=512M  # Change from 384M
  - /app/.cache:size=256M  # Change from 192M
```

### Step 3: Deploy with Docker Compose

```bash
# Build and start the container
docker-compose up -d --build

# Check status
docker-compose ps

# View startup logs
docker-compose logs -f pid-annotator
```

**Expected startup time**: 60-90 seconds (first build may take 5-10 minutes)

### Access the Application

Open your web browser and navigate to:

```
http://your-pi-ip:8080
```

To find your Pi's IP address:
```bash
hostname -I | awk '{print $1}'
```

Example: `http://192.168.1.100:8080`

---

## First-Time Usage

1. **Interactive Tutorial**: An automatic tutorial will guide you through all features
2. **Upload Files**: Drag and drop your PDF and Excel files
3. **Configure**: Set header row and select tag column
4. **Process**: Click "Start" or "Test Run" (100 tags)
5. **Download**: Get your annotated PDFs, Excel, and HTML report

---

## Performance Expectations

### 4GB Model

| File Size | Pages | Expected Time | Notes |
|-----------|-------|---------------|-------|
| 5MB       | 10    | ~7 seconds    | Standard mode |
| 25MB      | 100   | ~18 seconds   | Parallel mode |
| 80MB      | 500   | ~2:30 minutes | Streaming mode |
| 200MB     | 1000  | ~6 minutes    | Streaming + caution |

**Recommended limits**: 1-2 PDFs at a time, up to 500 pages each

### 8GB Model

| File Size | Pages | Expected Time | Notes |
|-----------|-------|---------------|-------|
| 5MB       | 10    | ~5 seconds    | Faster with 2 workers |
| 25MB      | 100   | ~12 seconds   | Parallel mode |
| 80MB      | 500   | ~2 minutes    | Streaming mode |
| 200MB     | 1000  | ~5 minutes    | Streaming + better |

**Recommended limits**: 2-3 PDFs at a time, up to 1000 pages each

---

## Common Issues & Solutions

### Issue 1: Port Already in Use

**Symptom**: Container fails to start with "port 8080 is already allocated"

**Solution**:

```bash
# Check what's using port 8080
sudo netstat -tulpn | grep 8080

# Option A: Stop the conflicting service
sudo systemctl stop <service-name>

# Option B: Change the external port
# Edit docker-compose.yml:
ports:
  - "8081:8080"  # Use 8081 instead

# Restart container
docker-compose down
docker-compose up -d
```

Access via: `http://your-pi-ip:8081`

### Issue 2: Insufficient Memory

**Symptoms**:
- Container crashes during processing
- "Out of memory" errors in logs
- System becomes unresponsive

**Solutions**:

```bash
# Check available memory
free -h

# Reduce worker count (edit docker-compose.yml)
environment:
  - GUNICORN_WORKERS=1  # Set to 1 if higher

# Lower memory limit
mem_limit: 1536m  # Reduce from 1792m

# Close unnecessary applications
sudo systemctl stop cups  # Example: disable printing service

# Restart container
docker-compose down
docker-compose up -d
```

### Issue 3: Temperature Throttling

**Symptoms**:
- Processing becomes very slow
- System feels sluggish
- Warning messages in logs

**Check temperature**:

```bash
vcgencmd measure_temp
```

**Temperature thresholds**:
- **Normal**: < 65°C (green)
- **Warning**: 65-75°C (yellow)
- **Throttling**: > 75°C (red)

**Solutions**:

1. **Improve cooling**:
   - Add heatsink (recommended minimum)
   - Add active cooling fan
   - Improve case ventilation

2. **Reduce load temporarily**:
   ```bash
   # Lower CPU limit (edit docker-compose.yml)
   cpus: 2.0  # Reduce from 2.5

   # Restart container
   docker-compose down
   docker-compose up -d
   ```

3. **Monitor during processing**:
   ```bash
   watch -n 2 vcgencmd measure_temp
   ```

### Issue 4: Disk Space Warning

**Symptoms**:
- Processing fails with disk errors
- entrypoint.sh shows "disk space below 1000MB" warning

**Check disk space**:

```bash
df -h
```

**Solutions**:

```bash
# Clean Docker system
docker system prune -a -f

# Remove old images
docker images
docker rmi <image-id>

# Clean application files (manual)
cd /path/to/pid-annotator
rm -rf persistent_uploads/* persistent_output/*

# Check space again
df -h
```

### Issue 5: SD Card Performance

**Symptoms**:
- Very slow processing
- High disk I/O wait times
- Container startup takes > 2 minutes

**Solutions**:

1. **Upgrade to faster SD card**:
   - Use UHS-I (U1 or U3)
   - Minimum Class 10
   - A1 or A2 application class preferred

2. **Use SSD via USB 3.0** (best performance):
   ```bash
   # Move application to SSD
   sudo mkdir /media/ssd/pid-annotator
   sudo rsync -av /home/pi/pid-annotator/ /media/ssd/pid-annotator/
   cd /media/ssd/pid-annotator
   docker-compose up -d --build
   ```

3. **Monitor I/O performance**:
   ```bash
   iostat -x 2
   ```

### Issue 6: Container Won't Start

**Check logs**:

```bash
docker-compose logs pid-annotator
```

**Common causes**:

1. **Architecture mismatch**:
   - entrypoint.sh verifies ARM64
   - Solution: Rebuild with correct platform
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Missing files**:
   - Check app.py, pid_annotator_core.py exist
   - Re-download or re-clone repository

3. **Permission issues**:
   - entrypoint.sh should auto-fix
   - Manual fix:
   ```bash
   sudo chown -R 1000:1000 persistent_uploads persistent_output
   ```

### Issue 7: WebSocket Connection Failed

**Symptoms**:
- No real-time progress updates
- Console shows "WebSocket connection failed"

**Solutions**:

1. **Check firewall**:
   ```bash
   sudo ufw allow 8080/tcp
   ```

2. **Verify container is running**:
   ```bash
   docker ps | grep pid-annotator
   ```

3. **Restart container**:
   ```bash
   docker-compose restart pid-annotator
   ```

4. **Check browser compatibility**:
   - Use Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
   - Avoid IE11

---

## Monitoring & Maintenance

### View Live Logs

```bash
# Follow logs in real-time
docker-compose logs -f pid-annotator

# View last 100 lines
docker-compose logs --tail 100 pid-annotator

# Filter for errors only
docker-compose logs pid-annotator | grep ERROR
```

### Resource Usage

```bash
# Real-time resource monitoring
docker stats pid-annotator-web

# Check memory usage
docker exec pid-annotator-web free -h

# Check disk usage
docker exec pid-annotator-web df -h
```

### Health Check

```bash
# Manual health check
curl http://localhost:8080/

# Expected response: HTTP 200 OK with HTML content
```

### System Monitoring

```bash
# CPU and memory overview
htop

# Temperature monitoring
watch -n 2 vcgencmd measure_temp

# Disk I/O monitoring
iostat -x 2

# Network monitoring
iftop
```

---

## Updating the Application

### Pull Latest Changes

```bash
cd /path/to/pid-annotator

# Pull latest code (if using git)
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Manual Update

```bash
# Stop container
docker-compose down

# Download new docker-compose.yml
wget -O docker-compose.yml https://your-url/docker-compose.yml

# Download new application files (if changed)
# app.py, pid_annotator_core.py, templates/, etc.

# Rebuild
docker-compose up -d --build
```

### Verify Update

```bash
# Check container status
docker-compose ps

# View startup logs
docker-compose logs --tail 50 pid-annotator

# Test application
curl http://localhost:8080/
```

---

## Backup & Restore

### Backup Configuration Profiles

Configuration profiles are stored in `./data/profiles/`:

```bash
# Backup profiles
tar -czf pid-annotator-profiles-backup.tar.gz data/profiles/

# Copy to safe location
cp pid-annotator-profiles-backup.tar.gz ~/backups/
```

### Restore Profiles

```bash
# Stop container
docker-compose down

# Restore profiles
tar -xzf pid-annotator-profiles-backup.tar.gz -C .

# Start container
docker-compose up -d
```

### Backup Entire Application

```bash
# Stop container
docker-compose down

# Backup everything
cd ..
tar -czf pid-annotator-backup-$(date +%Y%m%d).tar.gz pid-annotator/

# Restore (if needed)
tar -xzf pid-annotator-backup-20250102.tar.gz
cd pid-annotator
docker-compose up -d
```

---

## Advanced Configuration

### Change External Port

Edit `docker-compose.yml`:

```yaml
ports:
  - "9000:8080"  # Change 8080 to your preferred port
```

Restart:
```bash
docker-compose down
docker-compose up -d
```

Access via: `http://your-pi-ip:9000`

### Increase Workers (8GB Model Only)

Edit `docker-compose.yml`:

```yaml
environment:
  - GUNICORN_WORKERS=2  # Max 2 for 8GB, max 1 for 4GB
```

**Warning**: Do not set GUNICORN_WORKERS > 2 on Raspberry Pi 5

### Enable Debug Logging

Edit `docker-compose.yml`:

```yaml
environment:
  - DEBUG=1  # Enable debug mode
  - PYTHONUNBUFFERED=1
```

Restart and view logs:
```bash
docker-compose restart pid-annotator
docker-compose logs -f pid-annotator
```

### Configure Timezone

Edit `docker-compose.yml`:

```yaml
environment:
  - TZ=America/New_York  # Change to your timezone
```

Common timezones:
- Europe/Copenhagen
- America/New_York
- America/Los_Angeles
- Asia/Tokyo
- UTC (default)

### Persistent Volume Location

Change where files are stored on host:

```yaml
volumes:
  pid_uploads:
    driver_opts:
      device: /media/ssd/pid-uploads  # Change path

  pid_output:
    driver_opts:
      device: /media/ssd/pid-output  # Change path
```

---

## Optimizing for SSD

If you're running from an SSD (recommended for best performance):

1. **Move tmpfs to RAM** (already configured in docker-compose.yml):
   ```yaml
   tmpfs:
     - /tmp:size=384M,mode=1777
     - /app/.cache:size=192M,mode=755
   ```

2. **Disable SD card swap** (if using SSD as root):
   ```bash
   sudo dmesg | grep swap  # Check if swap is on SD card
   sudo swapoff -a  # Disable swap (if on SD card)
   ```

3. **Enable SSD TRIM**:
   ```bash
   sudo fstrim -v /  # Manual TRIM

   # Enable automatic TRIM
   sudo systemctl enable fstrim.timer
   ```

---

## CasaOS Deployment

### One-Click Installation (if available)

1. Open CasaOS web interface
2. Go to App Store
3. Search for "PID Annotator"
4. Click "Install"
5. Configure port (default 8080)
6. Start application

### Manual CasaOS Import

1. Open CasaOS
2. Go to App Store → Custom Install
3. Upload `docker-compose.yml`
4. Review configuration
5. Click "Install"
6. Access from CasaOS dashboard

### CasaOS Specific Settings

The docker-compose.yml includes CasaOS labels:

```yaml
labels:
  net.casaos.app.name: "PID Annotator"
  net.casaos.app.version: "1.0"
  net.casaos.app.author: "Rudi S. Kærgaard"
  net.casaos.app.web-port: "8080"
```

These enable:
- CasaOS dashboard integration
- One-click start/stop
- Resource monitoring
- Port management

---

## Troubleshooting Tips Summary

| Problem | Quick Fix |
|---------|-----------|
| Port in use | Change external port in docker-compose.yml |
| Out of memory | Reduce GUNICORN_WORKERS to 1 |
| Slow processing | Check temperature, improve cooling |
| Disk full | Run `docker system prune -a -f` |
| Container won't start | Check logs: `docker-compose logs` |
| No progress updates | Restart container, check firewall |
| High temperature | Add heatsink/fan, reduce CPU limit |
| Slow SD card | Use UHS-I card or switch to SSD |

---

## Performance Tips

1. **Use SSD instead of SD card** for 2-3x faster processing
2. **Add active cooling** to prevent thermal throttling
3. **Close unnecessary services** to free RAM
4. **Use Test Run** first to validate configuration
5. **Process one large file at a time** on 4GB model
6. **Enable parallel processing** (automatic for >20 pages)
7. **Monitor temperature** during heavy processing
8. **Clean up old files** regularly to free disk space

---

## Support & Documentation

For detailed information, see:

- **Main README**: [README.md](README.md) - Complete feature documentation
- **Developer Guide**: [CLAUDE.md](CLAUDE.md) - Technical architecture and development
- **Optimization Guide**: [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) - Performance tuning details

### Getting Help

1. Check the FAQ in the web interface (click FAQ button)
2. Review the troubleshooting section above
3. Check Docker logs: `docker-compose logs pid-annotator`
4. Monitor system resources: `docker stats`
5. Review entrypoint.sh output for startup warnings

### Common Log Messages

**Normal**:
```
✓ Architecture: aarch64 (ARM64 compatible)
✓ Memory check passed
✓ Disk space check passed
Starting application as user 'appuser' (non-root)...
```

**Warning**:
```
WARNING: Available memory 1400MB is below 1500MB recommended
WARNING: CPU temperature is high - consider improving cooling
```

**Error**:
```
ERROR: Expected ARM64 architecture, got: x86_64
ERROR: PORT must be numeric (got: invalid)
```

---

## Quick Reference Commands

```bash
# Start application
docker-compose up -d

# Stop application
docker-compose down

# Restart application
docker-compose restart pid-annotator

# View logs
docker-compose logs -f pid-annotator

# Check status
docker-compose ps

# Check resources
docker stats pid-annotator-web

# Update application
docker-compose down && docker-compose up -d --build

# Clean Docker
docker system prune -a -f

# Check temperature
vcgencmd measure_temp

# Check disk space
df -h

# Check memory
free -h
```

---

## FAQ Quick Links

**Q: What's the minimum RAM needed?**
A: 2GB available RAM (4GB Pi 5 model recommended)

**Q: Can I run this on Raspberry Pi 4?**
A: Yes, but reduce resources in docker-compose.yml

**Q: How do I change the port?**
A: Edit `docker-compose.yml`, change `"8080:8080"` to `"YOUR_PORT:8080"`

**Q: Why is processing slow?**
A: Check temperature, use SSD, ensure cooling, reduce workers if needed

**Q: Can I process multiple large PDFs?**
A: Yes, but process one at a time on 4GB model for best results

**Q: How do I access from other computers?**
A: Use `http://your-pi-ip:8080` from any computer on the same network

---

**Created by**: Rudi S. Kærgaard (rudikdk@gmail.com)
**Last Updated**: 2025-11-02
**Version**: 1.0
