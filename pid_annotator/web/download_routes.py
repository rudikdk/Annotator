"""
File download and workspace management routes
"""
import os
import shutil
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, session, current_app

# Import from processing_routes to share state
from pid_annotator.web.processing_routes import output_files_data, progress_data

# Create blueprint
download_bp = Blueprint('download', __name__)


def get_clean_filename(stored_filename):
    """Extract clean filename from stored filename by removing session ID prefix"""
    session_id = session.get('session_id', 'default')
    if stored_filename.startswith(f"{session_id}_"):
        return stored_filename[len(f"{session_id}_"):]
    return stored_filename


@download_bp.route('/download')
def download_file():
    """Download the processed files - supports filtering by file type"""
    current_task = session.get('current_task')
    file_type = request.args.get('type', 'all')  # 'all', 'pdf', 'excel', 'report'

    # Check if we have a completed task with output files
    if not current_task or current_task not in output_files_data:
        return jsonify({'success': False, 'message': 'No output files available'})

    task_data = output_files_data[current_task]
    if not task_data.get('completed'):
        return jsonify({'success': False, 'message': 'Processing not complete'})

    output_files = task_data['output_files']

    if not output_files:
        return jsonify({'success': False, 'message': 'No output files available'})

    # Filter files by type
    filtered_files = []
    for filename in output_files:
        if file_type == 'pdf' and filename.endswith('.pdf'):
            filtered_files.append(filename)
        elif file_type == 'excel' and filename.endswith('.xlsx'):
            filtered_files.append(filename)
        elif file_type == 'report' and filename.endswith('.html'):
            filtered_files.append(filename)
        elif file_type == 'all':
            filtered_files.append(filename)

    if not filtered_files:
        return jsonify({'success': False, 'message': f'No {file_type} files available'})

    # Return JSON with file info for download
    # Note: Files might be in output folder OR uploads folder (if already moved to workspace)
    file_urls = []
    for filename in filtered_files:
        # Check if file exists in either location
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)
        uploads_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        if os.path.exists(output_path) or os.path.exists(uploads_path):
            file_urls.append(f'/download_file/{filename}')
        else:
            print(f"[APP WARNING] File not found in output or uploads: {filename}")

    if not file_urls:
        print(f"[APP ERROR] No output files found")
        return jsonify({'success': False, 'message': 'Output files not found'})

    # Single file download
    if len(file_urls) == 1:
        response_data = {
            'success': True,
            'multiple_files': False,
            'file_count': 1,
            'files': file_urls,
            'output_files': filtered_files,  # Include original filenames for workspace management
            'message': '1 file ready for download'
        }
        return jsonify(response_data)

    # Multiple files - return JSON with file list for sequential download
    else:
        response_data = {
            'success': True,
            'multiple_files': True,
            'file_count': len(file_urls),
            'files': file_urls,
            'output_files': filtered_files,  # Include original filenames for workspace management
            'message': f'{len(file_urls)} files ready for download'
        }
        return jsonify(response_data)



@download_bp.route('/download_file/<filename>')
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
    output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)
    uploads_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

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


@download_bp.route('/progress/<task_id>')
def get_progress(task_id):
    """Get progress for a specific task"""
    if task_id in progress_data:
        return jsonify(progress_data[task_id])
    return jsonify({'progress': 0, 'status': 'Task not found'})


@download_bp.route('/cleanup_test_output', methods=['POST'])
def cleanup_test_output():
    """Delete only test output files, preserve uploads for full run"""
    try:
        session_id = session.get('session_id', 'default')
        current_task = session.get('current_task')

        print(f"[TEST CLEANUP] Starting test output cleanup for session {session_id}")

        # Delete only TEST output files from output directory
        output_dir = Path(current_app.config['OUTPUT_FOLDER'])
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


@download_bp.route('/cleanup_after_download', methods=['POST'])
def cleanup_after_download():
    """Delete generated output files after download, but preserve uploaded files for reuse"""
    try:
        session_id = session.get('session_id', 'default')
        current_task = session.get('current_task')

        # Check if this was a test run
        is_test_run = False
        if current_task and current_task in output_files_data:
            is_test_run = output_files_data[current_task].get('is_test', False)

        if is_test_run:
            # For test runs, only delete test output files
            print(f"[CLEANUP] Test run detected - preserving uploads and cleaning test outputs")
            return cleanup_test_output()

        print(f"[CLEANUP] Starting post-download cleanup for session {session_id}")

        # Delete session files from output directory, but PRESERVE HTML reports
        output_dir = Path(current_app.config['OUTPUT_FOLDER'])
        deleted_outputs = 0
        for file_path in output_dir.glob(f'{session_id}_*'):
            if file_path.is_file():
                # Skip HTML report files so users can view them after downloading PDFs
                if file_path.suffix.lower() == '.html':
                    print(f"[CLEANUP] Preserving report file: {file_path.name}")
                    continue

                try:
                    file_path.unlink()
                    deleted_outputs += 1
                    print(f"[CLEANUP] Deleted output file: {file_path.name}")
                except Exception as e:
                    print(f"[CLEANUP ERROR] Failed to delete output file {file_path.name}: {e}")

        # PRESERVE uploaded files - do NOT delete from uploads directory
        # Users can process the same files multiple times without re-uploading
        print(f"[CLEANUP] Preserving uploaded files for reuse")

        # Clear task-specific data from memory
        if current_task and current_task in output_files_data:
            del output_files_data[current_task]
            print(f"[CLEANUP] Cleared output_files_data for task {current_task}")

        if current_task and current_task in progress_data:
            del progress_data[current_task]
            print(f"[CLEANUP] Cleared progress_data for task {current_task}")

        print(f"[CLEANUP] Cleanup complete. Deleted {deleted_outputs} output file(s). Uploaded files preserved for reuse.")

        return jsonify({
            'success': True,
            'message': f'Output files cleaned up. Uploaded files preserved for reuse.',
            'deleted_outputs': deleted_outputs,
            'deleted_uploads': 0  # No longer deleting uploads
        })

    except Exception as e:
        print(f"[CLEANUP ERROR] {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error during cleanup: {str(e)}'
        })


@download_bp.route('/delete_file', methods=['POST'])
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

        uploads_path = Path(current_app.config['UPLOAD_FOLDER']) / filename
        output_path = Path(current_app.config['OUTPUT_FOLDER']) / filename

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


@download_bp.route('/add_outputs_to_workspace', methods=['POST'])
def add_outputs_to_workspace():
    """Move output PDFs from output folder to workspace (uploads folder) after processing"""
    try:
        data = request.get_json()
        output_files = data.get('output_files', [])

        session_id = session.get('session_id', 'default')
        uploads_dir = Path(current_app.config['UPLOAD_FOLDER'])
        output_dir = Path(current_app.config['OUTPUT_FOLDER'])

        moved_pdfs = []

        for filename in output_files:
            # Only move PDF files (not Excel outputs)
            if not filename.endswith('.pdf'):
                continue

            output_path = output_dir / filename
            upload_path = uploads_dir / filename

            # Move file from output to uploads folder
            if output_path.exists():
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


@download_bp.route('/list_workspace_files', methods=['GET'])
def list_workspace_files():
    """Get list of original uploaded files in the workspace (uploads folder only, excludes generated outputs)"""
    try:
        session_id = session.get('session_id', 'default')
        uploads_dir = Path(current_app.config['UPLOAD_FOLDER'])

        files_data = {
            'excel': [],
            'pdfs': []
        }

        # Scan uploads folder ONLY - do not include files from output folder
        for file_path in uploads_dir.glob(f'{session_id}_*'):
            if file_path.is_file():
                original_name = file_path.name[len(f"{session_id}_"):]
                file_ext = file_path.suffix.lower()
                file_size = file_path.stat().st_size

                # Skip generated/annotated files - only show original uploads
                if '_annotated_' in original_name or '_TEST_' in original_name:
                    continue

                if file_ext in ['.xlsx', '.xls', '.xlsm', '.csv']:
                    files_data['excel'].append({
                        'name': original_name,
                        'filename': file_path.name,
                        'size': file_size,
                        'uploadedAt': file_path.stat().st_mtime,
                        'type': file_ext[1:],  # Remove dot
                        'supportsAnnotation': file_ext in ('.xlsx', '.xlsm')
                    })
                elif file_ext == '.pdf':
                    files_data['pdfs'].append({
                        'name': original_name,
                        'filename': file_path.name,
                        'size': file_size,
                        'uploadedAt': file_path.stat().st_mtime,
                        'isAnnotated': False,
                        'isTest': False
                    })

        # Sort files by upload time (most recent first)
        files_data['pdfs'].sort(key=lambda x: x['uploadedAt'], reverse=True)
        files_data['excel'].sort(key=lambda x: x['uploadedAt'], reverse=True)

        print(f"[WORKSPACE LIST] Found {len(files_data['excel'])} Excel/CSV files and {len(files_data['pdfs'])} PDFs (original uploads only)")

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


@download_bp.route('/clear_session', methods=['POST'])
def clear_session_route():
    """Clear all session data and delete uploaded/output files"""
    import uuid
    try:
        session_id = session.get('session_id', 'default')

        # Delete session-specific files from uploads directory
        uploads_dir = Path(current_app.config['UPLOAD_FOLDER'])
        deleted_uploads = 0
        for file_path in uploads_dir.glob(f'{session_id}_*'):
            if file_path.is_file():
                file_path.unlink()
                deleted_uploads += 1

        # Delete session-specific files from output directory
        output_dir = Path(current_app.config['OUTPUT_FOLDER'])
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
