# Multi-stage build for ARM64 (Raspberry Pi 5) optimization
FROM python:3.11-slim-bullseye as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=8080

# Install runtime dependencies including gosu for privilege switching
RUN apt-get update && apt-get install -y \
    libffi7 \
    libssl1.1 \
    gosu \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

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
RUN mkdir -p uploads output && \
    chmod +x entrypoint.sh && \
    chown -R appuser:appuser /app && \
    chmod -R 755 uploads output

# Note: We don't switch to appuser here because entrypoint.sh needs root privileges
# to fix mounted volume permissions, then it will switch to appuser using gosu

# Expose port
EXPOSE 8080

# Health check (stdlib urllib to avoid extra deps)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/', timeout=5).status == 200 else 1)"

# Set entrypoint and start command using gunicorn for production
ENTRYPOINT ["./entrypoint.sh"]
CMD ["sh", "-c", "gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:${PORT:-8080} --timeout 300 --keep-alive 2 app:app"]
