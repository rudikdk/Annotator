"""Flask application configuration for PID Annotator."""

import os
from pathlib import Path


class AppConfig:
    """Flask application configuration."""

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

    # File paths (will be set at runtime)
    APP_ROOT = None
    UPLOAD_FOLDER = None
    OUTPUT_FOLDER = None

    # File upload limits
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size

    # Session cookie behavior (important when running behind Docker/proxies)
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '0').lower() in ('1', 'true', 'yes')
    SESSION_COOKIE_PATH = '/'

    # SocketIO configuration
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    SOCKETIO_ASYNC_MODE = os.environ.get('SOCKETIO_ASYNC_MODE', 'threading')
    SOCKETIO_PING_INTERVAL = 25
    SOCKETIO_PING_TIMEOUT = 60

    # Cleanup configuration
    FILE_CLEANUP_INTERVAL_SECONDS = 300  # Run at most every 5 minutes
    FILE_RETENTION_HOURS = 1  # Keep files for 1 hour

    @classmethod
    def init_paths(cls, app_root: Path):
        """Initialize path-based configuration."""
        cls.APP_ROOT = str(app_root)
        cls.UPLOAD_FOLDER = str(app_root / 'uploads')
        cls.OUTPUT_FOLDER = str(app_root / 'output')

    @classmethod
    def to_dict(cls):
        """Convert config to dictionary for Flask app.config.from_object()."""
        return {
            key: value
            for key, value in cls.__dict__.items()
            if not key.startswith('_') and key.isupper() and not callable(value)
        }
