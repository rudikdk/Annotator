"""Core annotation processing modules."""

from pid_annotator.core.pdf_indexer import (
    build_tag_index,
    build_page_statistics,
    build_page_bookmark_map
)
from pid_annotator.core.watermark import (
    create_overlay_page,
    apply_watermarks
)
from pid_annotator.core.excel_processor import (
    annotate_excel_with_found_tags,
    convert_xls_to_xlsx_preserving_format
)
from pid_annotator.core.preview_generator import (
    annotate_pdf_page_for_preview
)
from pid_annotator.core.pdf_annotator import (
    annotate_pdf_with_progress
)

__all__ = [
    'build_tag_index',
    'build_page_statistics',
    'build_page_bookmark_map',
    'create_overlay_page',
    'apply_watermarks',
    'annotate_excel_with_found_tags',
    'convert_xls_to_xlsx_preserving_format',
    'annotate_pdf_page_for_preview',
    'annotate_pdf_with_progress'
]
