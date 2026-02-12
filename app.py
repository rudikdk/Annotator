#!/usr/bin/env python3
import eventlet
eventlet.monkey_patch()
"""
PID Annotator Web Application
A web-based version of the PID Annotator tool

Minimal entry point - all routes are in blueprints, all logic is in modules.
"""

import os
import sys
from pathlib import Path

from flask import Flask, render_template
from flask_socketio import SocketIO



# Import configuration
from pid_annotator.config import AppConfig

# Import blueprint and handler registration
from pid_annotator.web import register_blueprints, register_socketio_handlers

# Import cleanup utilities
from pid_annotator.session.cleanup import cleanup_old_files, periodic_file_cleanup


# Initialize Flask app
print("DEBUG: Initializing Flask app...")
app = Flask(__name__)
print("DEBUG: Flask app initialized.")

# Prevent Jinja from conflicting with React's {{ }} by changing variable delimiters
app.jinja_env.variable_start_string = '[['
app.jinja_env.variable_end_string = ']]'

# Initialize paths and configure app
print("DEBUG: Initializing AppConfig paths...")
APP_ROOT = Path(__file__).resolve().parent
AppConfig.init_paths(APP_ROOT)
app.config.from_object(AppConfig)
print("DEBUG: AppConfig initialized.")

# Initialize SocketIO for real-time updates
print("DEBUG: Initializing SocketIO...")
socketio = SocketIO(
    app,
    cors_allowed_origins=AppConfig.SOCKETIO_CORS_ALLOWED_ORIGINS,
    async_mode=AppConfig.SOCKETIO_ASYNC_MODE,
    ping_interval=AppConfig.SOCKETIO_PING_INTERVAL,
    ping_timeout=AppConfig.SOCKETIO_PING_TIMEOUT
)
print("DEBUG: SocketIO initialized.")

# Ensure directories exist
print("DEBUG: Creating directories...")
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
print("DEBUG: Directories created.")

# Register all Flask blueprints
print("DEBUG: Registering blueprints...")
register_blueprints(app)
print("DEBUG: Blueprints registered.")

# Register WebSocket handlers
print("DEBUG: Registering SocketIO handlers...")
register_socketio_handlers(socketio)
print("DEBUG: SocketIO handlers registered.")
print("DEBUG: app.py top-level execution complete.")


@app.before_request
def before_request():
    """Run periodic cleanup before each request (throttled to every 5 minutes)"""
    periodic_file_cleanup(
        app.config['UPLOAD_FOLDER'],
        app.config['OUTPUT_FOLDER'],
        retention_hours=1
    )


@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')


if __name__ == '__main__':
    # Clean up old files on startup
    cleanup_old_files(
        app.config['UPLOAD_FOLDER'],
        app.config['OUTPUT_FOLDER'],
        retention_hours=1
    )

    # Run the application
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        allow_unsafe_werkzeug=True
    )
