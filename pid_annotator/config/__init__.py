"""Configuration module for PID Annotator."""

from .tag_matching_config import TagMatchingConfig
from .processing_config import (
    PARALLEL_INDEXING_ENABLED,
    MAX_WORKERS,
    STREAMING_THRESHOLD_MB,
    MEMORY_CLEANUP_BATCH_SIZE,
    PROGRESS_UPDATE_INTERVAL
)
from .annotation_config import AnnotationConfig, WatermarkConfig
from .app_config import AppConfig

__all__ = [
    # Tag matching
    'TagMatchingConfig',
    # Processing constants
    'PARALLEL_INDEXING_ENABLED',
    'MAX_WORKERS',
    'STREAMING_THRESHOLD_MB',
    'MEMORY_CLEANUP_BATCH_SIZE',
    'PROGRESS_UPDATE_INTERVAL',
    # Annotation
    'AnnotationConfig',
    'WatermarkConfig',
    # App
    'AppConfig',
]
