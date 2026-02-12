"""
Session management for PID Annotator web application.
Handles session initialization, file discovery, and session clearing.
"""

import uuid
from pathlib import Path
from flask import session
from typing import Optional


def get_or_create_session_id() -> str:
    """Get existing session ID or create a new one.

    Returns:
        str: Session ID (UUID)
    """
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


def clear_session_data() -> str:
    """Clear all session data and generate new session ID.

    Returns:
        str: Old session ID (for cleanup purposes)
    """
    old_session_id = session.get('session_id', 'default')
    session.clear()
    session['session_id'] = str(uuid.uuid4())
    session['tag_filters'] = []
    session['filter_logic'] = 'AND'
    return old_session_id


def try_attach_existing_files_to_session(upload_folder: str, reload_excel_columns_func):
    """Attempt to auto-populate session with existing files in uploads if session is empty.

    Args:
        upload_folder: Path to uploads directory
        reload_excel_columns_func: Function to reload Excel columns (from core)
    """
    try:
        uploads_dir = Path(upload_folder)
        session_id = session.get('session_id', 'default')

        # Excel: pick the most recent .xlsx/.xls for current session only
        if not session.get('excel_file'):
            excel_candidates = list(uploads_dir.glob(f'{session_id}_*.xlsx')) + \
                             list(uploads_dir.glob(f'{session_id}_*.xls'))
            if excel_candidates:
                # Select most recently modified
                excel_path = max(excel_candidates, key=lambda p: p.stat().st_mtime)
                session['excel_file'] = excel_path.name
                # Also try to load columns to keep UX consistent
                try:
                    result = reload_excel_columns_func(str(excel_path), 6)
                    if result.get('success'):
                        session['excel_columns'] = result['columns']
                        session['default_tag_column'] = result['default_tag_column']
                        session['header_row'] = 6
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


def delete_session_files(session_id: str, upload_folder: str, output_folder: str) -> tuple[int, int]:
    """Delete all files associated with a session.

    Args:
        session_id: Session ID to clean up
        upload_folder: Path to uploads directory
        output_folder: Path to output directory

    Returns:
        tuple: (deleted_uploads_count, deleted_outputs_count)
    """
    deleted_uploads = 0
    deleted_outputs = 0

    # Delete session-specific files from uploads directory
    uploads_dir = Path(upload_folder)
    for file_path in uploads_dir.glob(f'{session_id}_*'):
        if file_path.is_file():
            file_path.unlink()
            deleted_uploads += 1

    # Delete session-specific files from output directory
    output_dir = Path(output_folder)
    for file_path in output_dir.glob(f'{session_id}_*'):
        if file_path.is_file():
            file_path.unlink()
            deleted_outputs += 1

    return deleted_uploads, deleted_outputs
