"""
Web routes package - Flask blueprints for all HTTP routes
"""
from pid_annotator.web.upload_routes import upload_bp
from pid_annotator.web.excel_routes import excel_bp
from pid_annotator.web.processing_routes import processing_bp
from pid_annotator.web.download_routes import download_bp
from pid_annotator.web.profile_routes import profile_bp
from pid_annotator.web.report_routes import report_bp
from pid_annotator.web.preview_routes import preview_bp
from pid_annotator.web.websocket_handlers import register_socketio_handlers


def register_blueprints(app):
    """Register all Flask blueprints with the app"""
    app.register_blueprint(upload_bp)
    app.register_blueprint(excel_bp)
    app.register_blueprint(processing_bp)
    app.register_blueprint(download_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(preview_bp)


__all__ = [
    'register_blueprints',
    'register_socketio_handlers',
    'upload_bp',
    'excel_bp',
    'processing_bp',
    'download_bp',
    'profile_bp',
    'report_bp',
    'preview_bp'
]
