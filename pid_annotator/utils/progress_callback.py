"""
Progress reporting utilities for PID Annotator.
Provides abstract and concrete implementations for progress tracking.
"""

import sys
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class ProgressReporter(ABC):
    """Abstract base class for progress reporting."""

    @abstractmethod
    def report(self, task_id: str, percent: int, message: str):
        """Report progress for a task.

        Args:
            task_id: Unique identifier for the task
            percent: Progress percentage (0-100)
            message: Status message describing current progress
        """
        pass


class ConsoleProgressReporter(ProgressReporter):
    """Progress reporter that prints to console."""

    def report(self, task_id: str, percent: int, message: str):
        """Report progress to console.

        Args:
            task_id: Unique identifier for the task
            percent: Progress percentage (0-100)
            message: Status message describing current progress
        """
        timestamp = datetime.now().isoformat()
        print(f"[PROGRESS {timestamp}] Task {task_id}: {percent}% - {message}")
        sys.stdout.flush()


class SocketIOProgressReporter(ProgressReporter):
    """Progress reporter that uses Flask-SocketIO for real-time updates."""

    def __init__(self, socketio_instance, namespace: str = '/'):
        """Initialize the SocketIO progress reporter.

        Args:
            socketio_instance: Flask-SocketIO instance
            namespace: SocketIO namespace (default: '/')
        """
        self.socketio = socketio_instance
        self.namespace = namespace
        self.progress_data = {}

    def report(self, task_id: str, percent: int, message: str):
        """Report progress via SocketIO and console.

        Args:
            task_id: Unique identifier for the task
            percent: Progress percentage (0-100)
            message: Status message describing current progress
        """
        # Store progress data
        self.progress_data[task_id] = {
            'progress': percent,
            'status': message,
            'timestamp': datetime.now().isoformat()
        }

        print(f"[APP DEBUG] Progress callback called: task_id={task_id}, progress={percent}, status='{message}'")

        # Emit progress update via SocketIO
        try:
            self.socketio.emit('progress_update', {
                'task_id': task_id,
                'progress': percent,
                'status': message
            }, namespace=self.namespace)

            # Yield to the Socket.IO server so progress updates flush promptly
            try:
                self.socketio.sleep(0)
            except Exception:
                pass

            print(f"[APP DEBUG] SocketIO emit successful for task {task_id}")
        except Exception as e:
            print(f"[APP ERROR] Failed to emit progress update: {e}")

        # Flush stdout to ensure console output appears immediately
        sys.stdout.flush()

    def get_progress(self, task_id: str) -> Optional[dict]:
        """Get stored progress data for a task.

        Args:
            task_id: Task identifier

        Returns:
            dict: Progress data or None if not found
        """
        return self.progress_data.get(task_id)
