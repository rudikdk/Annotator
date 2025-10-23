#!/usr/bin/env python3
"""
PID Annotator Web Application
A web-based version of the PID Annotator tool
"""

import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
import threading
import time
import zipfile
from io import BytesIO

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import pandas as pd

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our core functionality (we'll copy this from the original)
from pid_annotator_core import annotate_pdf_with_progress, reload_excel_columns, annotate_excel_with_found_tags

app = Flask(__name__)
# Prevent Jinja from conflicting with React's {{ }} by changing variable delimiters
app.jinja_env.variable_start_string = '[['
app.jinja_env.variable_end_string = ']]'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Use absolute paths inside container for robustness
APP_ROOT = Path(__file__).resolve().parent
app.config['UPLOAD_FOLDER'] = str(APP_ROOT / 'uploads')
app.config['OUTPUT_FOLDER'] = str(APP_ROOT / 'output')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Session cookie behavior (important when running behind Docker/proxies)
session_cookie_secure_env = os.environ.get('SESSION_COOKIE_SECURE', '0').lower() in ('1', 'true', 'yes')
app.config['SESSION_COOKIE_SAMESITE'] = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['SESSION_COOKIE_SECURE'] = session_cookie_secure_env
app.config['SESSION_COOKIE_PATH'] = '/'

# Initialize SocketIO for real-time updates
# Explicitly set async_mode for stability on Raspberry Pi (eventlet worker) and tune ping settings
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode=os.environ.get('SOCKETIO_ASYNC_MODE', 'eventlet'),
    ping_interval=25,
    ping_timeout=60
)

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def cleanup_old_files():
    """Clean up old files (24+ hours) to prevent disk accumulation while preserving active sessions."""
    try:
        cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)  # 24 hours ago
        cleaned_count = 0

        # Clean uploads directory
        uploads_dir = Path(app.config['UPLOAD_FOLDER'])
        for file_path in uploads_dir.glob('*'):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                cleaned_count += 1
                print(f"[APP CLEANUP] Removed old upload file: {file_path.name}")

        # Clean output directory
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        for file_path in output_dir.glob('*'):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                cleaned_count += 1
                print(f"[APP CLEANUP] Removed old output file: {file_path.name}")

        if cleaned_count > 0:
            print(f"[APP CLEANUP] Cleanup complete: removed {cleaned_count} old files")
        else:
            print("[APP CLEANUP] No old files to clean up")

    except Exception as e:
        print(f"[APP ERROR] Cleanup failed: {e}")

# Run cleanup on startup
cleanup_old_files()

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'pdf': {'pdf'},
    'excel': {'xlsx', 'xls'}
}

# Combined allowed extensions for unified upload
ALL_ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}

def allowed_file(filename, file_type):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS[file_type]

def try_attach_existing_files_to_session():
    """Attempt to auto-populate session with existing files in uploads if session is empty."""
    try:
        uploads_dir = Path(app.config['UPLOAD_FOLDER'])
        session_id = session.get('session_id', 'default')

        # Excel: pick the most recent .xlsx/.xls for current session only
        if not session.get('excel_file'):
            excel_candidates = list(uploads_dir.glob(f'{session_id}_*.xlsx')) + list(uploads_dir.glob(f'{session_id}_*.xls'))
            if excel_candidates:
                # Select most recently modified
                excel_path = max(excel_candidates, key=lambda p: p.stat().st_mtime)
                session['excel_file'] = excel_path.name
                # Also try to load columns to keep UX consistent
                try:
                    result = reload_excel_columns(str(excel_path), 6)
                    if result.get('success'):
                        session['excel_columns'] = result['columns']
                        session['default_tag_column'] = result['default_tag_column']
                except Exception as e:
                    print(f"[APP WARN] Failed to load columns from discovered Excel: {e}")
        # PDFs: add all .pdf for current session only
        if not session.get('pdf_files'):
            pdf_candidates = list(uploads_dir.glob(f'{session_id}_*.pdf'))
            if pdf_candidates:
                stored_names = [p.name for p in pdf_candidates]
                # Derive original names removing session prefix
                original_names = [name[len(f"{session_id}_"):] for name in stored_names]
                session['pdf_files'] = stored_names
                session['original_pdf_names'] = original_names
    except Exception as e:
        print(f"[APP WARN] Auto-discovery of uploads failed: {e}")

# Progress tracking
progress_data = {}
# Thread-safe storage for output files
output_files_data = {}

def progress_callback(task_id, progress, status):
    """Callback function for progress updates"""
    progress_data[task_id] = {
        'progress': progress,
        'status': status,
        'timestamp': datetime.now().isoformat()
    }
    print(f"[APP DEBUG] Progress callback called: task_id={task_id}, progress={progress}, status='{status}'")

    # Emit progress update via SocketIO
    try:
        socketio.emit('progress_update', {
            'task_id': task_id,
            'progress': progress,
            'status': status
        }, namespace='/')
        # Yield to the Socket.IO server so progress updates flush promptly under eventlet/gevent
        try:
            socketio.sleep(0)
        except Exception:
            pass
        print(f"[APP DEBUG] SocketIO emit successful for task {task_id}")
    except Exception as e:
        print(f"[APP ERROR] Failed to emit progress update: {e}")

    # Also flush stdout to ensure console output appears immediately
    import sys
    sys.stdout.flush()


@app.route('/')
def index():
    """Main application page - always start with fresh session"""
    # Get old session ID if it exists (for cleanup)
    old_session_id = session.get('session_id')

    # Clear all session data to start fresh
    session.clear()

    # Generate new session ID
    new_session_id = str(uuid.uuid4())
    session['session_id'] = new_session_id

    print(f"[SESSION] Page loaded. Old session: {old_session_id}, New session: {new_session_id}")

    # Note: Old files will be cleaned up by the 24-hour cleanup routine
    # We don't delete them immediately in case user accidentally refreshed

    return render_template('index.html')

def format_date_ddmmmyyyy(dt):
    """Format date as DDMMMYYYY (e.g., 01JAN2025)"""
    return dt.strftime('%d%b%Y').upper()

@app.route('/upload_pdf', methods=['POST'])
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
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
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

@app.route('/upload_excel', methods=['POST'])
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
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        session['excel_file'] = filename
        
        # Load Excel columns with default header row (6)
        result = reload_excel_columns(filepath, 6)
        
        if result['success']:
            session['excel_columns'] = result['columns']
            session['default_tag_column'] = result['default_tag_column']
            
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

@app.route('/reload_columns', methods=['POST'])
def reload_columns():
    """Reload Excel columns with new header row"""
    data = request.get_json()
    header_row = data.get('header_row', 6)
    
    if 'excel_file' not in session:
        return jsonify({'success': False, 'message': 'No Excel file uploaded'})
    
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], session['excel_file'])
    result = reload_excel_columns(excel_path, header_row)
    
    if result['success']:
        session['excel_columns'] = result['columns']
        session['default_tag_column'] = result['default_tag_column']
    
    return jsonify(result)

@app.route('/process', methods=['POST'])
def process_files():
    """Process the PDF annotation"""
    try:
        # Get form data
        data = request.get_json()

        # Validate required files (allow auto-discovery from mounted uploads if session is empty)
        pdf_files = session.get('pdf_files', [])
        excel_in_session = session.get('excel_file')
        if not pdf_files or not excel_in_session:
            try_attach_existing_files_to_session()
            pdf_files = session.get('pdf_files', [])
            excel_in_session = session.get('excel_file')
        if not pdf_files or not excel_in_session:
            return jsonify({'success': False, 'message': 'Please upload PDF and Excel files'})

        # Get file paths
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], session['excel_file'])
        pdf_paths = [os.path.join(app.config['UPLOAD_FOLDER'], pdf_file) for pdf_file in pdf_files]

        # Get original PDF names for clean output naming
        original_pdf_names = session.get('original_pdf_names', [])

        # Get processing parameters
        header_row = data.get('header_row', 6)
        tag_column = data.get('tag_column', session.get('default_tag_column'))
        selected_comment_columns = data.get('comment_columns', None)
        max_tags = data.get('max_tags', None)  # For test runs
        annotate_excel = data.get('annotate_excel', False)  # New parameter for Excel annotation

        # Highlight settings
        highlight_column = data.get('highlight_column', '')
        highlight_color = data.get('highlight_color', '#FFFF00')
        column_color_pairs = [(highlight_column, highlight_color)] if highlight_column else []

        # Watermark settings
        watermark_enabled = data.get('watermark_enabled', False)
        watermark_attributes = data.get('watermark_attributes', [])
        # Support both old single attribute format and new array format
        if not watermark_attributes and data.get('watermark_attribute'):
            watermark_attributes = [data.get('watermark_attribute')]
        watermark_text_color = data.get('watermark_text_color', '#000000')

        # Create task ID for progress tracking
        task_id = str(uuid.uuid4())
        session['current_task'] = task_id

        # Capture session data for thread (avoid Flask session context issues)
        session_id = session.get('session_id', 'default')
        current_task_id = task_id

        # Start processing in a separate thread
        def process_thread(session_id, task_id, original_pdf_names, pdf_paths, excel_path,
                          column_color_pairs, max_tags, tag_column, header_row,
                          selected_comment_columns, watermark_enabled, watermark_attributes,
                          watermark_text_color, annotate_excel):
            try:
                output_files = []
                output_display_names = []  # Clean names for user display/download
                all_found_tags = set()  # Collect all found tags from all PDFs

                # Process each PDF file
                for i, pdf_path in enumerate(pdf_paths):
                    # Update progress for current file (allocate 90% across files)
                    total_files = len(pdf_paths)
                    file_share = 90 / total_files if total_files else 90
                    file_base = int(i * file_share)
                    file_end = int((i + 1) * file_share)

                    # Get original filename for progress display (remove session ID prefix)
                    original_name = original_pdf_names[i] if i < len(original_pdf_names) else os.path.basename(pdf_path)

                    # Per-file progress mapper: map core 0..100 into [file_base .. file_end)
                    def per_file_progress_cb(_tid, prog, status):
                        try:
                            mapped = file_base + int((float(prog) / 100.0) * file_share)
                            # Keep within this file's range; leave final step to file_end update
                            if mapped >= file_end:
                                mapped = max(file_end - 1, file_base)
                        except Exception:
                            mapped = file_base
                        progress_callback(task_id, mapped, f"Processing file {i+1}/{total_files}: {original_name} — {status}")

                    # Initial update at start of file segment
                    progress_callback(task_id, file_base, f"Processing file {i+1}/{total_files}: {original_name} — starting...")

                    # Generate clean output filename (no UUID, clean date format)
                    if i < len(original_pdf_names):
                        original_basename = os.path.splitext(original_pdf_names[i])[0]
                    else:
                        # Fallback: extract from stored filename by removing session ID prefix
                        stored_basename = os.path.splitext(os.path.basename(pdf_path))[0]
                        if stored_basename.startswith(f"{session_id}_"):
                            original_basename = stored_basename[len(f"{session_id}_"):]
                        else:
                            original_basename = stored_basename

                    # Format date as DDMMMYYYY (e.g., 01JAN2025)
                    current_date = format_date_ddmmmyyyy(datetime.now())
                    clean_filename = f"{original_basename}_annotated_{current_date}.pdf"

                    # Use session ID in actual stored filename to avoid conflicts
                    output_filename = f"{session_id}_{clean_filename}"
                    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

                    # Process this PDF and get found tags
                    found_tags = annotate_pdf_with_progress(
                        pdf_path=pdf_path,
                        excel_path=excel_path,
                        out_path=output_path,
                        column_color_pairs=column_color_pairs,
                        max_tags=max_tags,
                        tag_column=tag_column,
                        header_row=header_row,
                        selected_comment_columns=selected_comment_columns,
                        task_id=task_id,
                        progress_callback=per_file_progress_cb,
                        annotation_type="highlight_only",
                        watermark_enabled=watermark_enabled,
                        watermark_attribute=watermark_attributes,
                        watermark_text_color=watermark_text_color
                    )

                    # Collect all found tags from all PDFs
                    if found_tags:
                        all_found_tags.update(found_tags)

                    # Ensure progress reaches the end of this file's segment
                    progress_callback(task_id, file_end, f"Finished file {i+1}/{total_files}: {original_name}")
                    output_files.append(output_filename)
                    output_display_names.append(clean_filename)

                # Generate Excel annotation if requested
                if annotate_excel:
                    progress_callback(task_id, 95, "Annotating Excel file...")

                    # Generate clean Excel output filename
                    excel_basename = os.path.splitext(os.path.basename(excel_path))[0]
                    if excel_basename.startswith(f"{session_id}_"):
                        excel_basename = excel_basename[len(f"{session_id}_"):]

                    current_date = format_date_ddmmmyyyy(datetime.now())
                    excel_clean_filename = f"{excel_basename}_annotated_{current_date}.xlsx"

                    # Use session ID in actual stored filename to avoid conflicts
                    excel_output_filename = f"{session_id}_{excel_clean_filename}"
                    excel_output_path = os.path.join(app.config['OUTPUT_FOLDER'], excel_output_filename)

                    # Annotate Excel file with all found tags
                    success = annotate_excel_with_found_tags(
                        excel_path=excel_path,
                        out_path=excel_output_path,
                        found_tags_set=all_found_tags,
                        tag_column=tag_column,
                        header_row=header_row
                    )

                    if success:
                        output_files.append(excel_output_filename)
                        output_display_names.append(excel_clean_filename)
                        print(f"[APP DEBUG] Excel file created successfully: {excel_output_path}")
                        print(f"[APP DEBUG] Excel file exists: {os.path.exists(excel_output_path)}")
                        if os.path.exists(excel_output_path):
                            print(f"[APP DEBUG] Excel file size: {os.path.getsize(excel_output_path)} bytes")
                        progress_callback(task_id, 98, "Excel annotation complete")
                    else:
                        print(f"[APP ERROR] Excel annotation failed!")
                        progress_callback(task_id, 98, "Excel annotation failed")

                # Store output files info in thread-safe global dictionary
                output_files_data[task_id] = {
                    'output_files': output_files,
                    'completed': True,
                    'timestamp': datetime.now().isoformat(),
                    'annotate_excel': annotate_excel
                }

                # Final progress update
                pdf_count = len([f for f in output_files if f.endswith('.pdf')])
                excel_count = len([f for f in output_files if f.endswith('.xlsx')])
                file_description = []
                if pdf_count > 0:
                    file_description.append(f"{pdf_count} PDF(s)")
                if excel_count > 0:
                    file_description.append(f"{excel_count} Excel file(s)")
                file_desc = " and ".join(file_description)

                progress_callback(task_id, 100, f"Processing complete! {file_desc} processed successfully")

            except Exception as e:
                progress_callback(task_id, -1, f"Error: {str(e)}")

        # Instead of running full PDF processing, simulate progress 0→100
        def simulate_thread(task_id):
            try:
                for i in range(101):
                    progress_callback(task_id, i, f"Simulating progress... {i}%")
                    time.sleep(0.05)
                output_files_data[task_id] = {
                    'output_files': [],
                    'completed': True,
                    'timestamp': datetime.now().isoformat()
                }
                progress_callback(task_id, 100, f"Simulation complete! Done.")
            except Exception as e:
                progress_callback(task_id, -1, f"Error during simulation: {str(e)}")

        socketio.start_background_task(process_thread, session_id, current_task_id, original_pdf_names, pdf_paths, excel_path,
                          column_color_pairs, max_tags, tag_column, header_row,
                          selected_comment_columns, watermark_enabled, watermark_attributes,
                          watermark_text_color, annotate_excel)

        return jsonify({
            'success': True,
            'message': f'Processing started',
            'task_id': task_id,
            'file_count': len(pdf_files)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

def get_clean_filename(stored_filename):
    """Extract clean filename from stored filename by removing session ID prefix"""
    session_id = session.get('session_id', 'default')
    if stored_filename.startswith(f"{session_id}_"):
        return stored_filename[len(f"{session_id}_"):]
    return stored_filename

@app.route('/download')
def download_file():
    """Download the processed PDF files"""
    current_task = session.get('current_task')

    print(f"[APP DEBUG] /download route called, current_task: {current_task}")

    # Check if we have a completed task with output files
    if not current_task or current_task not in output_files_data:
        print(f"[APP DEBUG] No task data found for task: {current_task}")
        return jsonify({'success': False, 'message': 'No output files available'})

    task_data = output_files_data[current_task]
    if not task_data.get('completed'):
        print(f"[APP DEBUG] Task not completed: {current_task}")
        return jsonify({'success': False, 'message': 'Processing not complete'})

    output_files = task_data['output_files']
    print(f"[APP DEBUG] Output files: {output_files}")
    print(f"[APP DEBUG] Number of output files: {len(output_files)}")

    if not output_files:
        return jsonify({'success': False, 'message': 'No output files available'})

    # Single file download
    if len(output_files) == 1:
        print(f"[APP DEBUG] Single file download mode")
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_files[0])
        if not os.path.exists(output_path):
            print(f"[APP ERROR] Output file not found: {output_path}")
            return jsonify({'success': False, 'message': 'Output file not found'})

        # Use clean filename for download
        clean_name = get_clean_filename(output_files[0])
        print(f"[APP DEBUG] Sending single file: {clean_name}")
        return send_file(output_path, as_attachment=True, download_name=clean_name)

    # Multiple files - return JSON with file list for sequential download
    else:
        print(f"[APP DEBUG] Multiple files download mode")
        file_urls = []
        for filename in output_files:
            file_url = f'/download_file/{filename}'
            file_urls.append(file_url)
            print(f"[APP DEBUG] Added file URL: {file_url}")

        response_data = {
            'success': True,
            'multiple_files': True,
            'file_count': len(output_files),
            'files': file_urls,
            'message': f'{len(output_files)} files ready for download'
        }
        print(f"[APP DEBUG] Returning JSON response: {response_data}")
        return jsonify(response_data)

@app.route('/download_file/<filename>')
def download_single_file(filename):
    """Download a single file by filename"""
    current_task = session.get('current_task')

    # Security check - ensure filename is in our output files for this task
    if not current_task or current_task not in output_files_data:
        return jsonify({'success': False, 'message': 'File not found'})

    task_data = output_files_data[current_task]
    output_files = task_data.get('output_files', [])

    if filename not in output_files:
        return jsonify({'success': False, 'message': 'File not found'})

    output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if not os.path.exists(output_path):
        return jsonify({'success': False, 'message': 'File not found'})

    # Use clean filename for download
    clean_name = get_clean_filename(filename)
    return send_file(output_path, as_attachment=True, download_name=clean_name)

@app.route('/progress/<task_id>')
def get_progress(task_id):
    """Get progress for a specific task"""
    if task_id in progress_data:
        return jsonify(progress_data[task_id])
    return jsonify({'progress': 0, 'status': 'Task not found'})

@app.route('/cleanup_after_download', methods=['POST'])
def cleanup_after_download():
    """Delete uploaded and output files after successful download"""
    try:
        session_id = session.get('session_id', 'default')
        current_task = session.get('current_task')

        print(f"[CLEANUP] Starting post-download cleanup for session {session_id}")

        # Delete session-specific files from uploads directory
        uploads_dir = Path(app.config['UPLOAD_FOLDER'])
        deleted_uploads = 0
        for file_path in uploads_dir.glob(f'{session_id}_*'):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    deleted_uploads += 1
                    print(f"[CLEANUP] Deleted upload file: {file_path.name}")
                except Exception as e:
                    print(f"[CLEANUP ERROR] Failed to delete upload file {file_path.name}: {e}")

        # Delete session-specific files from output directory
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        deleted_outputs = 0
        for file_path in output_dir.glob(f'{session_id}_*'):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    deleted_outputs += 1
                    print(f"[CLEANUP] Deleted output file: {file_path.name}")
                except Exception as e:
                    print(f"[CLEANUP ERROR] Failed to delete output file {file_path.name}: {e}")

        # Clear session data
        session.pop('pdf_files', None)
        session.pop('original_pdf_names', None)
        session.pop('pdf_file', None)
        session.pop('original_pdf_name', None)
        session.pop('excel_file', None)
        session.pop('excel_columns', None)
        session.pop('default_tag_column', None)
        session.pop('current_task', None)

        # Clean up output_files_data for this task
        if current_task and current_task in output_files_data:
            del output_files_data[current_task]
            print(f"[CLEANUP] Cleared output_files_data for task {current_task}")

        # Clean up progress_data for this task
        if current_task and current_task in progress_data:
            del progress_data[current_task]
            print(f"[CLEANUP] Cleared progress_data for task {current_task}")

        print(f"[CLEANUP] Cleanup complete. Deleted {deleted_uploads} upload file(s) and {deleted_outputs} output file(s)")

        return jsonify({
            'success': True,
            'message': f'Files cleaned up successfully',
            'deleted_uploads': deleted_uploads,
            'deleted_outputs': deleted_outputs
        })

    except Exception as e:
        print(f"[CLEANUP ERROR] {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error during cleanup: {str(e)}'
        })

@app.route('/clear_session', methods=['POST'])
def clear_session():
    """Clear all session data and delete uploaded/output files"""
    try:
        session_id = session.get('session_id', 'default')

        # Delete session-specific files from uploads directory
        uploads_dir = Path(app.config['UPLOAD_FOLDER'])
        deleted_uploads = 0
        for file_path in uploads_dir.glob(f'{session_id}_*'):
            if file_path.is_file():
                file_path.unlink()
                deleted_uploads += 1

        # Delete session-specific files from output directory
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        deleted_outputs = 0
        for file_path in output_dir.glob(f'{session_id}_*'):
            if file_path.is_file():
                file_path.unlink()
                deleted_outputs += 1

        # Clear all session data
        session.clear()

        # Generate new session ID
        session['session_id'] = str(uuid.uuid4())

        print(f"[SESSION CLEAR] Deleted {deleted_uploads} upload files and {deleted_outputs} output files for session {session_id}")

        return jsonify({
            'success': True,
            'message': f'Session cleared successfully. Deleted {deleted_uploads} upload file(s) and {deleted_outputs} output file(s).',
            'deleted_uploads': deleted_uploads,
            'deleted_outputs': deleted_outputs
        })

    except Exception as e:
        print(f"[SESSION CLEAR ERROR] {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error clearing session: {str(e)}'
        })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    emit('connected', {'message': 'Connected to PID Annotator'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')

if __name__ == '__main__':
    # Run the application
    port = int(os.environ.get('PORT', 5001))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
