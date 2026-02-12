"""
Upload route handlers for PDF and Excel files
"""
import os
from pathlib import Path
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename

from pid_annotator.analysis import reload_excel_columns

# Create blueprint
upload_bp = Blueprint('upload', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'pdf': {'pdf'},
    'excel': {'xlsx', 'xls', 'csv'}
}

def allowed_file(filename, file_type):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS[file_type]


@upload_bp.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    """Handle PDF file upload"""
    if 'pdf_file' not in request.files:
        return jsonify({'success': False, 'message': 'No PDF file provided'})

    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    if file and allowed_file(file.filename, 'pdf'):
        original_filename = secure_filename(file.filename)
        # Add session ID to filename to avoid conflicts
        session_id = session.get('session_id', 'default')
        stored_filename = f"{session_id}_{original_filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_filename)
        file.save(filepath)

        # Store multiple PDFs in session with both original and stored names
        if 'pdf_files' not in session:
            session['pdf_files'] = []
        if 'original_pdf_names' not in session:
            session['original_pdf_names'] = []

        if stored_filename not in session['pdf_files']:
            session['pdf_files'].append(stored_filename)
            session['original_pdf_names'].append(original_filename)

        # For backward compatibility, also set single pdf_file
        session['pdf_file'] = stored_filename
        session['original_pdf_name'] = original_filename

        return jsonify({
            'success': True,
            'message': 'PDF uploaded successfully',
            'filename': file.filename,
            'filepath': stored_filename
        })

    return jsonify({'success': False, 'message': 'Invalid PDF file'})


@upload_bp.route('/upload_excel', methods=['POST'])
def upload_excel():
    """Handle Excel file upload"""
    if 'excel_file' not in request.files:
        return jsonify({'success': False, 'message': 'No Excel file provided'})

    file = request.files['excel_file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    if file and allowed_file(file.filename, 'excel'):
        filename = secure_filename(file.filename)
        # Add session ID to filename to avoid conflicts
        session_id = session.get('session_id', 'default')
        filename = f"{session_id}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        session['excel_file'] = filename

        # Load Excel columns
        result = reload_excel_columns(filepath, 6)

        if result['success']:
            session['excel_columns'] = result['columns']
            session['default_tag_column'] = result['default_tag_column']
            session['header_row'] = 6

            return jsonify({
                'success': True,
                'message': 'Excel uploaded successfully',
                'filename': file.filename,
                'filepath': filename,
                'columns': result['columns'],
                'default_tag_column': result['default_tag_column']
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Error reading Excel file: {result["message"]}'
            })

    return jsonify({'success': False, 'message': 'Invalid Excel file'})
