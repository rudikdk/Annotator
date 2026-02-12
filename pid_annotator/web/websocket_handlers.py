"""
WebSocket event handlers
"""
from flask import request
from flask_socketio import emit


def register_socketio_handlers(socketio):
    """Register all WebSocket event handlers"""

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print(f'Client connected: {request.sid}')
        emit('connected', {'message': 'Connected to PID Annotator'})

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print(f'Client disconnected: {request.sid}')
