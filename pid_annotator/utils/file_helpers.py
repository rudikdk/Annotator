"""
File handling utilities for PID Annotator.
Provides file validation and naming helpers.
"""

from datetime import datetime
from werkzeug.utils import secure_filename as werkzeug_secure_filename


# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'pdf': {'pdf'},
    'excel': {'xlsx', 'xls', 'csv'}
}

# Combined allowed extensions for unified upload
ALL_ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'csv'}


def allowed_file(filename: str, file_type: str) -> bool:
    """Check if file has an allowed extension for the given type.

    Args:
        filename: Name of the file to check
        file_type: Type of file ('pdf' or 'excel')

    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS[file_type]


def secure_filename(filename: str) -> str:
    """Secure a filename by removing dangerous characters.

    This is a wrapper around werkzeug.utils.secure_filename.

    Args:
        filename: Filename to secure

    Returns:
        str: Secured filename
    """
    return werkzeug_secure_filename(filename)


def format_date_ddmmmyyyy(dt: datetime) -> str:
    """Format date as DDMMMYYYY (e.g., 01JAN2025).

    Args:
        dt: Datetime object to format

    Returns:
        str: Formatted date string in DDMMMYYYY format
    """
    return dt.strftime('%d%b%Y').upper()
