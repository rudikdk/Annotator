# Multi-stage build optimized for Raspberry Pi 5 (ARM64)
FROM --platform=linux/arm64 python:3.11-slim-bookworm as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create and set working directory
WORKDIR /app

# Create pip cache directory for wheels (speeds up rebuilds)
RUN mkdir -p /root/.cache/pip

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies with wheel caching
# Use --prefer-binary to avoid building from source when possible
RUN pip install --upgrade pip setuptools wheel && \
    pip install --prefer-binary -r requirements.txt

# Production stage - Bookworm for better ARM64 support
FROM --platform=linux/arm64 python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=8080
ENV PYTHONOPTIMIZE=1

# Install runtime dependencies (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi8 \
    libssl3 \
    gosu \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create application directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files
COPY app.py .
COPY pid_annotator_core.py .
COPY templates/ templates/
COPY static/ static/
COPY entrypoint.sh .

# Create directories for uploads and output with proper permissions
RUN mkdir -p uploads output .cache && \
    chmod +x entrypoint.sh && \
    chown -R appuser:appuser /app && \
    chmod -R 755 uploads output .cache

# Note: We don't switch to appuser here because entrypoint.sh needs root privileges
# to fix mounted volume permissions, then it will switch to appuser using gosu

# Expose port
EXPOSE 8080

# Optimized health check using wget (already installed)
HEALTHCHECK --interval=45s --timeout=10s --start-period=60s --retries=3 \
    CMD wget -q --spider http://localhost:8080/ || exit 1

# Set entrypoint and start command
# Using gunicorn with eventlet for WebSocket support
# Optimized for Raspberry Pi 5: 1 worker, reasonable timeouts
ENTRYPOINT ["./entrypoint.sh"]
CMD ["sh", "-c", "gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:${PORT:-8080} --timeout 300 --graceful-timeout 30 --keep-alive 5 --log-level warning app:app"]
