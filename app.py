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
    async_mode=os.environ.get('SOCKETIO_ASYNC_MODE', 'threading'),
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
    'excel': {'xlsx', 'xls', 'csv'}
}

# Combined allowed extensions for unified upload
ALL_ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'csv'}

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

@app.route('/select_excel', methods=['POST'])
def select_excel():
    """Select an Excel file and load its columns"""
    data = request.get_json()
    excel_file = data.get('excel_file')
    header_row = data.get('header_row', 6)

    if not excel_file:
        return jsonify({'success': False, 'message': 'No Excel file specified'})

    # Validate file exists
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_file)
    if not os.path.exists(excel_path):
        return jsonify({'success': False, 'message': f'Excel file not found: {excel_file}'})

    # Update session with selected Excel file
    session['excel_file'] = excel_file

    # Load columns
    result = reload_excel_columns(excel_path, header_row)

    if result['success']:
        session['excel_columns'] = result['columns']
        session['default_tag_column'] = result['default_tag_column']
        print(f"[SESSION] Selected Excel file updated: {excel_file}")

    return jsonify(result)

@app.route('/process', methods=['POST'])
def process_files():
    """Process the PDF annotation"""
    try:
        # Get form data
        data = request.get_json()

        # Get selected PDFs and Excel from request
        selected_pdfs = data.get('selected_pdfs', [])
        selected_excel = data.get('selected_excel', None)

        # Validate Excel file - use selected_excel from frontend if provided
        if selected_excel:
            excel_file = selected_excel
            print(f"[APP DEBUG] Using selected Excel file: {excel_file}")
        else:
            # Fallback to session for backward compatibility
            excel_file = session.get('excel_file')
            if not excel_file:
                try_attach_existing_files_to_session()
                excel_file = session.get('excel_file')
            print(f"[APP DEBUG] Using Excel file from session: {excel_file}")

        if not excel_file:
            return jsonify({'success': False, 'message': 'Please select an Excel/CSV file'})

        # Validate that selected Excel file exists on disk
        uploads_dir = Path(app.config['UPLOAD_FOLDER'])
        excel_path_obj = uploads_dir / excel_file
        if not excel_path_obj.exists():
            return jsonify({'success': False, 'message': f'Selected Excel file not found: {excel_file}'})

        # Convert to string for compatibility with processing functions
        excel_path = str(excel_path_obj)

        # Use selected PDFs directly from request (they come from workspace which lists actual files)
        if selected_pdfs:
            pdf_files = selected_pdfs
            print(f"[APP DEBUG] Processing {len(pdf_files)} selected PDF(s)")

            # Validate that selected files actually exist on disk
            uploads_dir = Path(app.config['UPLOAD_FOLDER'])
            valid_pdf_files = []
            for pdf_file in pdf_files:
                pdf_path = uploads_dir / pdf_file
                if pdf_path.exists():
                    valid_pdf_files.append(pdf_file)
                else:
                    print(f"[APP WARNING] Selected PDF not found: {pdf_file}")

            if not valid_pdf_files:
                return jsonify({'success': False, 'message': 'None of the selected PDF files exist on disk'})

            pdf_files = valid_pdf_files
            print(f"[APP DEBUG] Validated {len(pdf_files)} PDF file(s) exist on disk")
        else:
            # Fallback: use PDFs from session (backward compatibility)
            pdf_files = session.get('pdf_files', [])
            if not pdf_files:
                try_attach_existing_files_to_session()
                pdf_files = session.get('pdf_files', [])
            if not pdf_files:
                return jsonify({'success': False, 'message': 'No PDF files selected'})
            print(f"[APP DEBUG] No PDF selection provided, using all {len(pdf_files)} PDF(s) from session")

        # Get file paths (excel_path already set during validation above)
        pdf_paths = [os.path.join(app.config['UPLOAD_FOLDER'], pdf_file) for pdf_file in pdf_files]

        # Get original PDF names for clean output naming (matching the selected PDFs)
        all_original_names = session.get('original_pdf_names', [])
        all_session_pdfs = session.get('pdf_files', [])
        original_pdf_names = []
        for pdf_file in pdf_files:
            try:
                idx = all_session_pdfs.index(pdf_file)
                if idx < len(all_original_names):
                    original_pdf_names.append(all_original_names[idx])
                else:
                    # Fallback: use filename without session ID
                    session_id = session.get('session_id', 'default')
                    original_pdf_names.append(pdf_file[len(f"{session_id}_"):] if pdf_file.startswith(f"{session_id}_") else pdf_file)
            except ValueError:
                # Fallback
                session_id = session.get('session_id', 'default')
                original_pdf_names.append(pdf_file[len(f"{session_id}_"):] if pdf_file.startswith(f"{session_id}_") else pdf_file)

        # Get processing parameters
        header_row = data.get('header_row', 6)
        tag_column = data.get('tag_column', session.get('default_tag_column'))
        selected_comment_columns = data.get('comment_columns', None)
        max_tags = data.get('max_tags', None)  # For test runs
        is_test = data.get('is_test', False)  # Flag to indicate test run
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
                          watermark_text_color, annotate_excel, is_test):
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

                    # Add TEST prefix for test runs
                    if is_test:
                        clean_filename = f"{original_basename}_TEST_annotated_{current_date}.pdf"
                    else:
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

                    # Add TEST prefix for test runs
                    if is_test:
                        excel_clean_filename = f"{excel_basename}_TEST_annotated_{current_date}.xlsx"
                    else:
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
                    'annotate_excel': annotate_excel,
                    'is_test': is_test
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
                          watermark_text_color, annotate_excel, is_test)

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

    # Return JSON with file info for download
    # Note: Files might be in output folder OR uploads folder (if already moved to workspace)
    file_urls = []
    for filename in output_files:
        # Check if file exists in either location
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        uploads_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if os.path.exists(output_path) or os.path.exists(uploads_path):
            file_urls.append(f'/download_file/{filename}')
        else:
            print(f"[APP WARNING] File not found in output or uploads: {filename}")

    if not file_urls:
        print(f"[APP ERROR] No output files found")
        return jsonify({'success': False, 'message': 'Output files not found'})

    # Single file download
    if len(file_urls) == 1:
        print(f"[APP DEBUG] Single file download mode")
        response_data = {
            'success': True,
            'multiple_files': False,
            'file_count': 1,
            'files': file_urls,
            'output_files': output_files,  # Include original filenames for workspace management
            'message': '1 file ready for download'
        }
        print(f"[APP DEBUG] Returning JSON response for single file: {response_data}")
        return jsonify(response_data)

    # Multiple files - return JSON with file list for sequential download
    else:
        print(f"[APP DEBUG] Multiple files download mode")
        response_data = {
            'success': True,
            'multiple_files': True,
            'file_count': len(file_urls),
            'files': file_urls,
            'output_files': output_files,  # Include original filenames for workspace management
            'message': f'{len(file_urls)} files ready for download'
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

    # Check both output and uploads folders (files might have been moved to workspace)
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    uploads_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    file_path = None
    if os.path.exists(output_path):
        file_path = output_path
        print(f"[DOWNLOAD] Found file in output folder: {filename}")
    elif os.path.exists(uploads_path):
        file_path = uploads_path
        print(f"[DOWNLOAD] Found file in uploads folder (workspace): {filename}")

    if not file_path:
        print(f"[DOWNLOAD ERROR] File not found in either folder: {filename}")
        return jsonify({'success': False, 'message': 'File not found'})

    # Use clean filename for download
    clean_name = get_clean_filename(filename)
    return send_file(file_path, as_attachment=True, download_name=clean_name)

@app.route('/progress/<task_id>')
def get_progress(task_id):
    """Get progress for a specific task"""
    if task_id in progress_data:
        return jsonify(progress_data[task_id])
    return jsonify({'progress': 0, 'status': 'Task not found'})

@app.route('/cleanup_test_output', methods=['POST'])
def cleanup_test_output():
    """Delete only test output files, preserve uploads for full run"""
    try:
        session_id = session.get('session_id', 'default')
        current_task = session.get('current_task')

        print(f"[TEST CLEANUP] Starting test output cleanup for session {session_id}")

        # Delete only TEST output files from output directory
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        deleted_outputs = 0
        for file_path in output_dir.glob(f'{session_id}_*_TEST_*'):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    deleted_outputs += 1
                    print(f"[TEST CLEANUP] Deleted test output file: {file_path.name}")
                except Exception as e:
                    print(f"[TEST CLEANUP ERROR] Failed to delete test output file {file_path.name}: {e}")

        # Clean up output_files_data for this task
        if current_task and current_task in output_files_data:
            del output_files_data[current_task]
            print(f"[TEST CLEANUP] Cleared output_files_data for task {current_task}")

        # Clean up progress_data for this task
        if current_task and current_task in progress_data:
            del progress_data[current_task]
            print(f"[TEST CLEANUP] Cleared progress_data for task {current_task}")

        print(f"[TEST CLEANUP] Test cleanup complete. Deleted {deleted_outputs} test output file(s). Uploads preserved for full run.")

        return jsonify({
            'success': True,
            'message': f'Test files cleaned up successfully. Upload data preserved.',
            'deleted_outputs': deleted_outputs,
            'uploads_preserved': True
        })

    except Exception as e:
        print(f"[TEST CLEANUP ERROR] {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error during test cleanup: {str(e)}'
        })

@app.route('/cleanup_after_download', methods=['POST'])
def cleanup_after_download():
    """Delete Excel output files after download (PDFs stay in workspace)"""
    try:
        session_id = session.get('session_id', 'default')
        current_task = session.get('current_task')

        # Check if this was a test run
        is_test_run = False
        if current_task and current_task in output_files_data:
            is_test_run = output_files_data[current_task].get('is_test', False)

        if is_test_run:
            # For test runs, only delete test output files
            print(f"[CLEANUP] Test run detected - preserving uploads")
            return cleanup_test_output()

        # For full runs, only delete Excel output files (PDFs are already in workspace)
        print(f"[CLEANUP] Starting post-download cleanup for session {session_id}")

        # Delete only Excel files from output directory (PDFs already moved to workspace)
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        deleted_outputs = 0
        for file_path in output_dir.glob(f'{session_id}_*.xlsx'):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    deleted_outputs += 1
                    print(f"[CLEANUP] Deleted Excel output file: {file_path.name}")
                except Exception as e:
                    print(f"[CLEANUP ERROR] Failed to delete output file {file_path.name}: {e}")

        # Don't clear session data - files remain in workspace for reprocessing
        # Only clear task-specific data
        if current_task and current_task in output_files_data:
            del output_files_data[current_task]
            print(f"[CLEANUP] Cleared output_files_data for task {current_task}")

        if current_task and current_task in progress_data:
            del progress_data[current_task]
            print(f"[CLEANUP] Cleared progress_data for task {current_task}")

        print(f"[CLEANUP] Cleanup complete. Deleted {deleted_outputs} Excel output file(s). PDFs remain in workspace.")

        return jsonify({
            'success': True,
            'message': f'Excel outputs cleaned up. PDFs remain in workspace.',
            'deleted_outputs': deleted_outputs
        })

    except Exception as e:
        print(f"[CLEANUP ERROR] {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error during cleanup: {str(e)}'
        })

@app.route('/delete_file', methods=['POST'])
def delete_file():
    """Delete a single file from the workspace"""
    try:
        data = request.get_json()
        filename = data.get('filename')

        if not filename:
            return jsonify({'success': False, 'message': 'No filename provided'})

        session_id = session.get('session_id', 'default')

        # Security: ensure filename belongs to current session
        if not filename.startswith(f"{session_id}_"):
            return jsonify({'success': False, 'message': 'Invalid file access'})

        # Try to find and delete file from uploads or output folder
        deleted = False
        file_path = None

        uploads_path = Path(app.config['UPLOAD_FOLDER']) / filename
        output_path = Path(app.config['OUTPUT_FOLDER']) / filename

        if uploads_path.exists():
            uploads_path.unlink()
            file_path = uploads_path
            deleted = True
            print(f"[FILE DELETE] Deleted from uploads: {filename}")
        elif output_path.exists():
            output_path.unlink()
            file_path = output_path
            deleted = True
            print(f"[FILE DELETE] Deleted from output: {filename}")

        if not deleted:
            return jsonify({'success': False, 'message': 'File not found'})

        # Remove from session data
        if 'pdf_files' in session and filename in session['pdf_files']:
            pdf_index = session['pdf_files'].index(filename)
            session['pdf_files'].pop(pdf_index)
            if 'original_pdf_names' in session and pdf_index < len(session['original_pdf_names']):
                session['original_pdf_names'].pop(pdf_index)
            print(f"[FILE DELETE] Removed from pdf_files session")

        if session.get('excel_file') == filename:
            session.pop('excel_file', None)
            session.pop('excel_columns', None)
            session.pop('default_tag_column', None)
            print(f"[FILE DELETE] Removed excel_file from session")

        # Also remove from output_files_data if present
        current_task = session.get('current_task')
        if current_task and current_task in output_files_data:
            task_data = output_files_data[current_task]
            if 'output_files' in task_data and filename in task_data['output_files']:
                task_data['output_files'].remove(filename)
                print(f"[FILE DELETE] Removed from output_files_data")

        return jsonify({
            'success': True,
            'message': f'File deleted successfully: {filename}'
        })

    except Exception as e:
        print(f"[FILE DELETE ERROR] {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error deleting file: {str(e)}'
        })

@app.route('/add_outputs_to_workspace', methods=['POST'])
def add_outputs_to_workspace():
    """Move output PDFs from output folder to workspace (uploads folder) after processing"""
    try:
        data = request.get_json()
        output_files = data.get('output_files', [])

        session_id = session.get('session_id', 'default')
        uploads_dir = Path(app.config['UPLOAD_FOLDER'])
        output_dir = Path(app.config['OUTPUT_FOLDER'])

        moved_pdfs = []

        for filename in output_files:
            # Only move PDF files (not Excel outputs)
            if not filename.endswith('.pdf'):
                continue

            output_path = output_dir / filename
            upload_path = uploads_dir / filename

            # Move file from output to uploads folder
            if output_path.exists():
                import shutil
                shutil.move(str(output_path), str(upload_path))
                print(f"[WORKSPACE] Moved {filename} to workspace")

                # Extract original name for session tracking
                original_name = filename[len(f"{session_id}_"):]

                # Add to session pdf_files
                if 'pdf_files' not in session:
                    session['pdf_files'] = []
                if 'original_pdf_names' not in session:
                    session['original_pdf_names'] = []

                if filename not in session['pdf_files']:
                    session['pdf_files'].append(filename)
                    session['original_pdf_names'].append(original_name)

                moved_pdfs.append(filename)

        # Mark session as modified to ensure Flask persists the changes
        if moved_pdfs:
            session.modified = True

        print(f"[WORKSPACE] Added {len(moved_pdfs)} PDFs to workspace")

        return jsonify({
            'success': True,
            'message': f'{len(moved_pdfs)} PDFs added to workspace',
            'moved_files': moved_pdfs
        })

    except Exception as e:
        print(f"[WORKSPACE ERROR] {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error adding outputs to workspace: {str(e)}'
        })

@app.route('/list_workspace_files', methods=['GET'])
def list_workspace_files():
    """Get list of all files in the workspace (uploads + outputs)"""
    try:
        session_id = session.get('session_id', 'default')
        uploads_dir = Path(app.config['UPLOAD_FOLDER'])
        output_dir = Path(app.config['OUTPUT_FOLDER'])

        files_data = {
            'excel': [],
            'pdfs': []
        }

        # Scan uploads folder
        for file_path in uploads_dir.glob(f'{session_id}_*'):
            if file_path.is_file():
                original_name = file_path.name[len(f"{session_id}_"):]
                file_ext = file_path.suffix.lower()
                file_size = file_path.stat().st_size

                if file_ext in ['.xlsx', '.xls', '.csv']:
                    files_data['excel'].append({
                        'name': original_name,
                        'filename': file_path.name,
                        'size': file_size,
                        'uploadedAt': file_path.stat().st_mtime,
                        'type': file_ext[1:]  # Remove dot
                    })
                elif file_ext == '.pdf':
                    is_annotated = '_annotated_' in original_name
                    is_test = '_TEST_' in original_name
                    files_data['pdfs'].append({
                        'name': original_name,
                        'filename': file_path.name,
                        'size': file_size,
                        'uploadedAt': file_path.stat().st_mtime,
                        'isAnnotated': is_annotated,
                        'isTest': is_test
                    })

        # Scan output folder for PDFs (outputs that haven't been moved to uploads yet)
        for file_path in output_dir.glob(f'{session_id}_*.pdf'):
            if file_path.is_file():
                original_name = file_path.name[len(f"{session_id}_"):]
                file_size = file_path.stat().st_size
                is_annotated = '_annotated_' in original_name
                is_test = '_TEST_' in original_name

                # Check if already in pdfs list (avoid duplicates)
                if not any(f['filename'] == file_path.name for f in files_data['pdfs']):
                    files_data['pdfs'].append({
                        'name': original_name,
                        'filename': file_path.name,
                        'size': file_size,
                        'uploadedAt': file_path.stat().st_mtime,
                        'isAnnotated': is_annotated,
                        'isTest': is_test,
                        'inOutput': True  # Mark as being in output folder
                    })

        # Sort files by upload time (most recent first)
        files_data['pdfs'].sort(key=lambda x: x['uploadedAt'], reverse=True)
        files_data['excel'].sort(key=lambda x: x['uploadedAt'], reverse=True)

        print(f"[WORKSPACE LIST] Found {len(files_data['excel'])} Excel/CSV files and {len(files_data['pdfs'])} PDFs")

        return jsonify({
            'success': True,
            'files': files_data,
            'total': len(files_data['excel']) + len(files_data['pdfs'])
        })

    except Exception as e:
        print(f"[WORKSPACE LIST ERROR] {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error listing files: {str(e)}',
            'files': {'excel': [], 'pdfs': []}
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

# Configuration Profile Management
PROFILES_FOLDER = str(APP_ROOT / 'data' / 'profiles')
os.makedirs(PROFILES_FOLDER, exist_ok=True)

def get_builtin_templates():
    """Return built-in configuration templates"""
    return [
        {
            "name": "Minimal Setup",
            "description": "Only tag highlighting, no comments or watermarks",
            "version": "1.0",
            "builtin": True,
            "settings": {
                "header_row": 6,
                "tag_column": None,
                "comment_columns": [],
                "highlight_column": "",
                "highlight_color": "#FFFF00",
                "annotate_excel": False,
                "watermark_enabled": False,
                "watermark_attributes": [],
                "watermark_text_color": "#000000"
            }
        },
        {
            "name": "Standard Documentation",
            "description": "Tag highlighting with basic comments",
            "version": "1.0",
            "builtin": True,
            "settings": {
                "header_row": 6,
                "tag_column": None,
                "comment_columns": [],
                "highlight_column": "",
                "highlight_color": "#FFFF00",
                "annotate_excel": False,
                "watermark_enabled": False,
                "watermark_attributes": [],
                "watermark_text_color": "#000000"
            }
        },
        {
            "name": "Production Ready",
            "description": "All features enabled - comprehensive annotations",
            "version": "1.0",
            "builtin": True,
            "settings": {
                "header_row": 6,
                "tag_column": None,
                "comment_columns": [],
                "highlight_column": "",
                "highlight_color": "#FF0000",
                "annotate_excel": True,
                "watermark_enabled": True,
                "watermark_attributes": [],
                "watermark_text_color": "#000000"
            }
        },
        {
            "name": "Quick Review",
            "description": "Optimized for test runs and quick validation",
            "version": "1.0",
            "builtin": True,
            "settings": {
                "header_row": 6,
                "tag_column": None,
                "comment_columns": [],
                "highlight_column": "",
                "highlight_color": "#00FF00",
                "annotate_excel": False,
                "watermark_enabled": False,
                "watermark_attributes": [],
                "watermark_text_color": "#000000"
            }
        },
        {
            "name": "Excel Focus",
            "description": "Prioritizes Excel annotation with highlighting",
            "version": "1.0",
            "builtin": True,
            "settings": {
                "header_row": 6,
                "tag_column": None,
                "comment_columns": [],
                "highlight_column": "",
                "highlight_color": "#90EE90",
                "annotate_excel": True,
                "watermark_enabled": False,
                "watermark_attributes": [],
                "watermark_text_color": "#000000"
            }
        }
    ]

def validate_profile_data(data):
    """Validate profile data structure"""
    required_fields = ['name', 'settings']
    settings_fields = [
        'header_row', 'tag_column', 'comment_columns',
        'highlight_column', 'highlight_color', 'annotate_excel',
        'watermark_enabled', 'watermark_attributes', 'watermark_text_color'
    ]

    # Check required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Check settings fields
    settings = data.get('settings', {})
    for field in settings_fields:
        if field not in settings:
            return False, f"Missing settings field: {field}"

    # Validate data types
    if not isinstance(settings['header_row'], int) or settings['header_row'] < 1:
        return False, "header_row must be a positive integer"

    if not isinstance(settings['comment_columns'], list):
        return False, "comment_columns must be a list"

    if not isinstance(settings['annotate_excel'], bool):
        return False, "annotate_excel must be a boolean"

    if not isinstance(settings['watermark_enabled'], bool):
        return False, "watermark_enabled must be a boolean"

    if not isinstance(settings['watermark_attributes'], list):
        return False, "watermark_attributes must be a list"

    return True, "Valid"

@app.route('/get_builtin_templates', methods=['GET'])
def get_templates():
    """Get built-in configuration templates"""
    try:
        templates = get_builtin_templates()
        return jsonify({
            'success': True,
            'templates': templates
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading templates: {str(e)}'
        })

@app.route('/save_profile', methods=['POST'])
def save_profile():
    """Save current configuration as a named profile"""
    try:
        data = request.get_json()

        # Validate profile data
        is_valid, message = validate_profile_data(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': f'Invalid profile data: {message}'
            })

        # Create profile object
        profile = {
            'name': data['name'],
            'description': data.get('description', ''),
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'settings': data['settings']
        }

        # Sanitize filename
        filename = secure_filename(data['name']) + '.json'
        filepath = os.path.join(PROFILES_FOLDER, filename)

        # Save to file
        with open(filepath, 'w') as f:
            json.dump(profile, f, indent=2)

        print(f"[PROFILE] Saved profile: {data['name']}")

        return jsonify({
            'success': True,
            'message': f'Profile "{data["name"]}" saved successfully',
            'filename': filename
        })

    except Exception as e:
        print(f"[PROFILE ERROR] Failed to save profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error saving profile: {str(e)}'
        })

@app.route('/load_profiles', methods=['GET'])
def load_profiles():
    """Get list of all saved profiles"""
    try:
        profiles = []

        # Load all JSON files from profiles folder
        for filename in os.listdir(PROFILES_FOLDER):
            if filename.endswith('.json'):
                filepath = os.path.join(PROFILES_FOLDER, filename)
                try:
                    with open(filepath, 'r') as f:
                        profile = json.load(f)
                        # Add metadata
                        profile['filename'] = filename
                        profile['builtin'] = False
                        profiles.append(profile)
                except Exception as e:
                    print(f"[PROFILE WARNING] Failed to load profile {filename}: {str(e)}")
                    continue

        return jsonify({
            'success': True,
            'profiles': profiles,
            'count': len(profiles)
        })

    except Exception as e:
        print(f"[PROFILE ERROR] Failed to load profiles: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error loading profiles: {str(e)}',
            'profiles': []
        })

@app.route('/load_profile/<filename>', methods=['GET'])
def load_profile(filename):
    """Load a specific profile by filename"""
    try:
        # Sanitize filename
        filename = secure_filename(filename)
        if not filename.endswith('.json'):
            filename += '.json'

        filepath = os.path.join(PROFILES_FOLDER, filename)

        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'message': f'Profile not found: {filename}'
            })

        with open(filepath, 'r') as f:
            profile = json.load(f)

        print(f"[PROFILE] Loaded profile: {profile.get('name', filename)}")

        return jsonify({
            'success': True,
            'profile': profile
        })

    except Exception as e:
        print(f"[PROFILE ERROR] Failed to load profile {filename}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error loading profile: {str(e)}'
        })

@app.route('/delete_profile/<filename>', methods=['DELETE'])
def delete_profile(filename):
    """Delete a profile"""
    try:
        # Sanitize filename
        filename = secure_filename(filename)
        if not filename.endswith('.json'):
            filename += '.json'

        filepath = os.path.join(PROFILES_FOLDER, filename)

        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'message': f'Profile not found: {filename}'
            })

        os.remove(filepath)
        print(f"[PROFILE] Deleted profile: {filename}")

        return jsonify({
            'success': True,
            'message': f'Profile deleted successfully'
        })

    except Exception as e:
        print(f"[PROFILE ERROR] Failed to delete profile {filename}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error deleting profile: {str(e)}'
        })

@app.route('/export_profile', methods=['POST'])
def export_profile():
    """Export a profile as JSON download"""
    try:
        data = request.get_json()
        profile_name = data.get('name')

        if not profile_name:
            return jsonify({
                'success': False,
                'message': 'Profile name is required'
            })

        # Sanitize filename
        filename = secure_filename(profile_name) + '.json'
        filepath = os.path.join(PROFILES_FOLDER, filename)

        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'message': f'Profile not found: {profile_name}'
            })

        # Send file as download
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )

    except Exception as e:
        print(f"[PROFILE ERROR] Failed to export profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error exporting profile: {str(e)}'
        })

@app.route('/import_profile', methods=['POST'])
def import_profile():
    """Import a profile from JSON upload"""
    try:
        if 'profile_file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            })

        file = request.files['profile_file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            })

        if not file.filename.endswith('.json'):
            return jsonify({
                'success': False,
                'message': 'File must be a JSON file'
            })

        # Parse JSON
        try:
            profile_data = json.load(file)
        except json.JSONDecodeError as e:
            return jsonify({
                'success': False,
                'message': f'Invalid JSON format: {str(e)}'
            })

        # Validate profile data
        is_valid, message = validate_profile_data(profile_data)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': f'Invalid profile data: {message}'
            })

        # Save imported profile
        profile_name = profile_data.get('name', 'imported_profile')
        filename = secure_filename(profile_name) + '.json'
        filepath = os.path.join(PROFILES_FOLDER, filename)

        # Update timestamps
        profile_data['imported_at'] = datetime.now().isoformat()

        with open(filepath, 'w') as f:
            json.dump(profile_data, f, indent=2)

        print(f"[PROFILE] Imported profile: {profile_name}")

        return jsonify({
            'success': True,
            'message': f'Profile "{profile_name}" imported successfully',
            'profile': profile_data
        })

    except Exception as e:
        print(f"[PROFILE ERROR] Failed to import profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error importing profile: {str(e)}'
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
