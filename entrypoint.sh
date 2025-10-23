#!/bin/sh

# This script runs as root to fix permissions, then switches to appuser
# Ensure the uploads and output directories have correct permissions
# This is needed because Docker volume mounts can override container permissions

echo "Fixing directory permissions..."

if [ -d "/app/uploads" ]; then
    chmod 755 /app/uploads
    chown -R appuser:appuser /app/uploads
    echo "Fixed permissions for /app/uploads"
fi

if [ -d "/app/output" ]; then
    chmod 755 /app/output
    chown -R appuser:appuser /app/output
    echo "Fixed permissions for /app/output"
fi

# Switch to appuser and execute the original command
echo "Switching to appuser and starting application..."
exec gosu appuser "$@"
