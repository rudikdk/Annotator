"""
Report viewing routes
"""
import os
from flask import Blueprint, send_file, jsonify, session, current_app

# Create blueprint
report_bp = Blueprint('report', __name__)


@report_bp.route('/view_report/<filename>')
def view_report(filename):
    """View HTML processing report in browser"""
    session_id = session.get('session_id', 'default')

    # Security check - ensure filename starts with session ID
    if not filename.startswith(f"{session_id}_report_"):
        print(f"[VIEW_REPORT ERROR] Invalid report access attempt: {filename}")
        return jsonify({'error': 'Invalid report access'}), 403

    # Check if file exists in output folder
    report_path = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)

    if not os.path.exists(report_path):
        print(f"[VIEW_REPORT ERROR] Report not found: {filename}")
        return jsonify({'error': 'Report not found'}), 404

    # Serve the HTML report
    print(f"[VIEW_REPORT] Serving report: {filename}")
    return send_file(report_path, mimetype='text/html')
