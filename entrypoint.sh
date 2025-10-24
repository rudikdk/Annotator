#!/bin/sh
set -e

# Entrypoint script for PID Annotator - Raspberry Pi 5 optimized
# This script runs as root to fix permissions, then switches to appuser
# Ensures Docker volume mounts have correct permissions

echo "================================================"
echo "PID Annotator - Starting on Raspberry Pi 5"
echo "================================================"

# Function to check and fix directory permissions
fix_directory_permissions() {
    local dir="$1"
    if [ -d "$dir" ]; then
        if ! chmod 755 "$dir" 2>/dev/null; then
            echo "WARNING: Could not change permissions for $dir"
            return 1
        fi
        if ! chown -R appuser:appuser "$dir" 2>/dev/null; then
            echo "WARNING: Could not change ownership for $dir"
            return 1
        fi
        echo "✓ Fixed permissions for $dir"
        return 0
    else
        echo "⚠ Directory $dir does not exist, creating..."
        mkdir -p "$dir" && chown appuser:appuser "$dir" && chmod 755 "$dir"
        echo "✓ Created $dir"
        return 0
    fi
}

# Fix permissions for all required directories
echo "Fixing directory permissions..."
fix_directory_permissions "/app/uploads"
fix_directory_permissions "/app/output"
fix_directory_permissions "/app/.cache"

# Verify Python installation
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not found!"
    exit 1
fi

# Display system information (useful for debugging on Pi)
echo ""
echo "System Information:"
echo "  Python version: $(python --version)"
echo "  Architecture: $(uname -m)"
echo "  Memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  Disk space: $(df -h /app | awk 'NR==2 {print $4 " available"}')"
echo ""

# Check if required files exist
if [ ! -f "/app/app.py" ]; then
    echo "ERROR: app.py not found!"
    exit 1
fi

if [ ! -f "/app/pid_annotator_core.py" ]; then
    echo "ERROR: pid_annotator_core.py not found!"
    exit 1
fi

echo "✓ All application files present"
echo ""

# Switch to appuser and execute the application
echo "Switching to appuser (non-root) and starting application..."
echo "Port: ${PORT:-8080}"
echo "================================================"
echo ""

# Use exec to replace shell process with application
exec gosu appuser "$@"
