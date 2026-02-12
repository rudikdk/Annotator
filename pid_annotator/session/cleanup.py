"""
File cleanup utilities for PID Annotator.
Handles periodic cleanup of old uploaded and output files.
"""

import os
import time
from datetime import datetime
from pathlib import Path


# Periodic cleanup state - avoids running cleanup on every single request
_last_periodic_cleanup = time.time()
_PERIODIC_CLEANUP_INTERVAL = 300  # Run at most every 5 minutes


def cleanup_old_files(upload_folder: str, output_folder: str, retention_hours: int = 1):
    """Clean up old files to prevent accumulation while preserving active sessions.

    Args:
        upload_folder: Path to uploads directory
        output_folder: Path to output directory
        retention_hours: Number of hours to retain files (default: 1)
    """
    try:
        cutoff_time = datetime.now().timestamp() - (retention_hours * 60 * 60)
        cleaned_count = 0

        # Clean uploads directory
        uploads_dir = Path(upload_folder)
        for file_path in uploads_dir.glob('*'):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                cleaned_count += 1
                print(f"[APP CLEANUP] Removed old upload file: {file_path.name}")

        # Clean output directory
        output_dir = Path(output_folder)
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


def periodic_file_cleanup(upload_folder: str, output_folder: str, retention_hours: int = 1) -> bool:
    """Periodically clean up stale files from abandoned sessions.

    Runs at most once every 5 minutes to avoid performance impact.

    Args:
        upload_folder: Path to uploads directory
        output_folder: Path to output directory
        retention_hours: Number of hours to retain files (default: 1)

    Returns:
        bool: True if cleanup ran, False if skipped due to interval
    """
    global _last_periodic_cleanup
    now = time.time()

    if now - _last_periodic_cleanup < _PERIODIC_CLEANUP_INTERVAL:
        return False

    _last_periodic_cleanup = now

    try:
        cutoff_time = now - (retention_hours * 60 * 60)
        cleaned = 0

        for folder in [upload_folder, output_folder]:
            for file_path in Path(folder).glob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned += 1

        if cleaned > 0:
            print(f"[PERIODIC CLEANUP] Removed {cleaned} stale file(s) older than {retention_hours} hour(s)")

        return True

    except Exception as e:
        print(f"[PERIODIC CLEANUP ERROR] {e}")
        return False
