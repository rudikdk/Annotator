"""Processing configuration constants for PID Annotator."""

import os

# Configuration for optimization features
PARALLEL_INDEXING_ENABLED = True
MAX_WORKERS = max(1, (os.cpu_count() or 2) - 1)  # Leave one core free
STREAMING_THRESHOLD_MB = 50  # Enable streaming for files larger than this
MEMORY_CLEANUP_BATCH_SIZE = 100  # Clean memory after processing this many pages
PROGRESS_UPDATE_INTERVAL = 2  # Minimum percent change to trigger progress update
