#!/bin/sh
set -e

# Entrypoint script for PID Annotator - Raspberry Pi 5 optimized
# This script runs as root to fix permissions, then switches to appuser
# Ensures Docker volume mounts have correct permissions with comprehensive safety checks

# Enable debug mode if requested
if [ "${DEBUG:-0}" = "1" ]; then
    set -x
    echo "DEBUG MODE ENABLED"
fi

echo "================================================"
echo "PID Annotator - Raspberry Pi 5 Deployment"
echo "================================================"
echo ""

# ============================================
# Architecture Verification
# ============================================
ARCH=$(uname -m)
echo "Verifying architecture..."
if [ "$ARCH" != "aarch64" ] && [ "$ARCH" != "arm64" ]; then
    echo "ERROR: Expected ARM64 architecture, got: $ARCH"
    echo "This container is optimized for Raspberry Pi 5 (ARM64)"
    exit 1
fi
echo "✓ Architecture: $ARCH (ARM64 compatible)"
echo ""

# ============================================
# Memory Validation
# ============================================
echo "Checking memory availability..."
if [ -f /proc/meminfo ]; then
    AVAILABLE_MEM=$(grep MemAvailable /proc/meminfo | awk '{print $2}' | xargs -I {} expr {} / 1024)
    TOTAL_MEM=$(grep MemTotal /proc/meminfo | awk '{print $2}' | xargs -I {} expr {} / 1024)

    echo "  Total Memory: ${TOTAL_MEM}MB"
    echo "  Available Memory: ${AVAILABLE_MEM}MB"

    if [ "$AVAILABLE_MEM" -lt 1500 ]; then
        echo "  WARNING: Available memory ${AVAILABLE_MEM}MB is below 1500MB recommended"
        echo "  Application may experience performance issues or OOM errors"
    else
        echo "✓ Memory check passed"
    fi
else
    echo "  WARNING: Cannot read /proc/meminfo - skipping memory check"
fi
echo ""

# ============================================
# Disk Space Check
# ============================================
echo "Checking disk space..."
if command -v df >/dev/null 2>&1; then
    DISK_AVAILABLE=$(df /app | awk 'NR==2 {print $4}' | xargs -I {} expr {} / 1024)
    echo "  Available Disk: ${DISK_AVAILABLE}MB"

    if [ "$DISK_AVAILABLE" -lt 1000 ]; then
        echo "  WARNING: Available disk space ${DISK_AVAILABLE}MB is below 1000MB"
        echo "  Application may fail to process large files"
    else
        echo "✓ Disk space check passed"
    fi
else
    echo "  WARNING: df command not available - skipping disk check"
fi
echo ""

# ============================================
# CPU Temperature Monitoring (Raspberry Pi specific)
# ============================================
if command -v vcgencmd >/dev/null 2>&1; then
    echo "Checking CPU temperature..."
    TEMP=$(vcgencmd measure_temp 2>/dev/null | cut -d= -f2 | cut -d\' -f1 || echo "N/A")
    if [ "$TEMP" != "N/A" ]; then
        echo "  CPU Temperature: ${TEMP}°C"
        # Warn if temperature is high (>70°C)
        TEMP_INT=$(echo "$TEMP" | cut -d. -f1)
        if [ "$TEMP_INT" -gt 70 ] 2>/dev/null; then
            echo "  WARNING: CPU temperature is high - consider improving cooling"
        fi
    fi
    echo ""
fi

# ============================================
# Port Validation
# ============================================
echo "Validating configuration..."
PORT="${PORT:-8080}"
if ! echo "$PORT" | grep -qE '^[0-9]+$'; then
    echo "ERROR: PORT must be numeric (got: $PORT)"
    exit 1
fi

if [ "$PORT" -lt 1024 ] || [ "$PORT" -gt 65535 ]; then
    echo "WARNING: PORT $PORT is outside recommended range 1024-65535"
fi
echo "✓ Port: $PORT"

# ============================================
# Worker Count Validation
# ============================================
GUNICORN_WORKERS="${GUNICORN_WORKERS:-1}"
if ! echo "$GUNICORN_WORKERS" | grep -qE '^[0-9]+$'; then
    echo "ERROR: GUNICORN_WORKERS must be numeric (got: $GUNICORN_WORKERS)"
    exit 1
fi

if [ "$GUNICORN_WORKERS" -gt 4 ]; then
    echo "WARNING: $GUNICORN_WORKERS workers may be excessive for Raspberry Pi 5"
fi

# Calculate required memory (approximately 1200MB per worker + 500MB base)
REQUIRED_MEM=$((GUNICORN_WORKERS * 1200 + 500))
if [ -n "$AVAILABLE_MEM" ]; then
    if [ "$AVAILABLE_MEM" -lt "$REQUIRED_MEM" ]; then
        echo "WARNING: $GUNICORN_WORKERS workers need ~${REQUIRED_MEM}MB, only ${AVAILABLE_MEM}MB available"
        echo "  Consider reducing GUNICORN_WORKERS or increasing memory limits"
    fi
fi
echo "✓ Workers: $GUNICORN_WORKERS (estimated memory requirement: ${REQUIRED_MEM}MB)"
echo ""

# ============================================
# Python and Application Verification
# ============================================
echo "Verifying Python installation..."
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not found!"
    exit 1
fi
PYTHON_VERSION=$(python --version 2>&1)
echo "✓ Python: $PYTHON_VERSION"

# Check if required application files exist
echo ""
echo "Verifying application files..."
if [ ! -f "/app/app.py" ]; then
    echo "ERROR: app.py not found!"
    exit 1
fi
echo "✓ app.py found"

if [ ! -f "/app/pid_annotator_core.py" ]; then
    echo "ERROR: pid_annotator_core.py not found!"
    exit 1
fi
echo "✓ pid_annotator_core.py found"

if [ ! -d "/app/templates" ]; then
    echo "WARNING: templates/ directory not found"
else
    echo "✓ templates/ directory found"
fi

if [ ! -d "/app/static" ]; then
    echo "WARNING: static/ directory not found"
else
    echo "✓ static/ directory found"
fi
echo ""

# ============================================
# Directory Permissions Setup
# ============================================
echo "Setting up directory permissions..."

# Function to check and fix directory permissions
fix_directory_permissions() {
    local dir="$1"
    if [ -d "$dir" ]; then
        if ! chmod 755 "$dir" 2>/dev/null; then
            echo "  WARNING: Could not change permissions for $dir"
            return 1
        fi
        if ! chown -R appuser:appuser "$dir" 2>/dev/null; then
            echo "  WARNING: Could not change ownership for $dir"
            return 1
        fi
        echo "  ✓ Fixed permissions for $dir"
        return 0
    else
        echo "  ⚠ Directory $dir does not exist, creating..."
        if mkdir -p "$dir" && chown appuser:appuser "$dir" && chmod 755 "$dir"; then
            echo "  ✓ Created $dir"
            return 0
        else
            echo "  ERROR: Failed to create $dir"
            return 1
        fi
    fi
}

# Fix permissions for all required directories
fix_directory_permissions "/app/uploads"
fix_directory_permissions "/app/output"
fix_directory_permissions "/app/.cache"
echo ""

# ============================================
# Startup Summary
# ============================================
echo "================================================"
echo "           STARTUP SUMMARY"
echo "================================================"
echo "Architecture:        $ARCH"
echo "Python:              $PYTHON_VERSION"
echo "Port:                $PORT"
echo "Workers:             $GUNICORN_WORKERS"
echo "Environment:         ${FLASK_ENV:-production}"
if [ -n "$AVAILABLE_MEM" ]; then
    echo "Available Memory:    ${AVAILABLE_MEM}MB"
    echo "Required Memory:     ~${REQUIRED_MEM}MB"
fi
if [ -n "$DISK_AVAILABLE" ]; then
    echo "Available Disk:      ${DISK_AVAILABLE}MB"
fi
echo "Timezone:            ${TZ:-UTC}"
echo "================================================"
echo ""
echo "Starting application as user 'appuser' (non-root)..."
echo ""

# ============================================
# Switch to appuser and execute application
# ============================================
# Use exec to replace shell process with application
# This ensures proper signal handling and PID 1 behavior
exec gosu appuser "$@"
