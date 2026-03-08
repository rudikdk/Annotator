"""Annotation configuration for PID Annotator."""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Callable, Any, Dict
from .tag_matching_config import TagMatchingConfig


@dataclass
class WatermarkConfig:
    """Configuration for watermark overlay on PDF pages."""
    enabled: bool = False
    text: str = ""
    attributes: List[str] = field(default_factory=list)  # Ordered list of column names
    text_color: str = "#000000"
    font_size: int = 9
    background_enabled: bool = False
    opacity: float = 0.3
    angle: int = 45
    position_x: float = 0.5  # Relative position (0.0 to 1.0)
    position_y: float = 0.5  # Relative position (0.0 to 1.0)


@dataclass
class AnnotationConfig:
    """
    Consolidated configuration for PDF annotation.

    This dataclass consolidates all 25+ parameters from annotate_pdf_with_progress
    into logical field groups for cleaner code organization.
    """

    # File paths
    pdf_paths: List[str] = field(default_factory=list)
    excel_path: str = ""
    output_path: str = ""

    # Excel settings
    tag_column: Optional[str] = None
    header_row: int = 6
    sheet_name: Optional[str] = None
    start_column: str = 'A'
    comment_columns: Optional[List[str]] = None

    # Highlighting
    highlight_color: str = "#FFFF00"
    annotate_excel: bool = False
    annotation_type: str = "highlight_only"

    # Watermark
    watermark: Optional[WatermarkConfig] = None

    # Tag matching
    tag_matching: Optional[TagMatchingConfig] = None
    filters: Optional[Dict[str, Any]] = None
    filter_logic: str = "AND"
    color_rules: Optional[List[Dict[str, Any]]] = None

    # Advanced options
    column_color_pairs: Optional[List[Tuple[str, str]]] = None
    max_tags: Optional[int] = None
    use_streaming: Optional[bool] = None
    enable_default_color: bool = True
    excel_constraint_mode: bool = False
    excel_constraint_logic: str = "AND"

    # Session
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    progress_callback: Optional[Callable] = None

    @classmethod
    def from_request(cls, request_data: Dict[str, Any], session_data: Dict[str, Any]) -> 'AnnotationConfig':
        """
        Factory method to create AnnotationConfig from Flask request data and session.

        Args:
            request_data: Dictionary from request.get_json() or request.form
            session_data: Dictionary from Flask session

        Returns:
            AnnotationConfig instance
        """
        # Extract watermark configuration
        # Normalize watermark_attributes: support list, string, and legacy single-attribute key
        watermark = None
        if request_data.get('watermark_enabled', False):
            watermark_attributes = request_data.get('watermark_attributes', [])
            if not watermark_attributes and request_data.get('watermark_attribute'):
                watermark_attributes = [request_data.get('watermark_attribute')]
            if isinstance(watermark_attributes, str):
                watermark_attributes = [watermark_attributes] if watermark_attributes else []

            watermark = WatermarkConfig(
                enabled=True,
                attributes=watermark_attributes,
                text_color=request_data.get('watermark_text_color', '#000000'),
                font_size=request_data.get('watermark_font_size', 9),
                background_enabled=request_data.get('watermark_background_enabled', False),
                opacity=request_data.get('watermark_opacity', 0.3),
                angle=request_data.get('watermark_angle', 45),
                position_x=request_data.get('watermark_position_x', 0.5),
                position_y=request_data.get('watermark_position_y', 0.5)
            )

        # Extract tag matching configuration
        tag_matching = None
        tag_matching_data = request_data.get('tag_matching_config')
        if tag_matching_data:
            tag_matching = TagMatchingConfig.from_dict(tag_matching_data)

        # Resolve column_color_pairs: new color_rules take precedence; legacy fallback uses highlight_column/highlight_color
        color_rules = request_data.get('color_rules', [])
        if color_rules:
            column_color_pairs = []
        else:
            highlight_column = request_data.get('highlight_column', '')
            highlight_color = request_data.get('highlight_color', '#FFFF00')
            column_color_pairs = [(highlight_column, highlight_color)] if highlight_column else []

        # Resolve tag_column: request data takes precedence, fall back to session default
        tag_column = request_data.get('tag_column') or session_data.get('default_tag_column')

        # Build configuration
        return cls(
            pdf_paths=request_data.get('selected_pdfs', []),
            excel_path=request_data.get('selected_excel', ''),
            output_path=request_data.get('output_path', ''),
            tag_column=tag_column,
            header_row=request_data.get('header_row', 6),
            sheet_name=request_data.get('sheet_name') or session_data.get('sheet_name'),
            start_column=request_data.get('start_column') or session_data.get('start_column', 'A'),
            comment_columns=request_data.get('comment_columns'),
            highlight_color=request_data.get('default_highlight_color', '#FFFF00'),
            annotate_excel=request_data.get('annotate_excel', False),
            annotation_type=request_data.get('annotation_type', 'highlight_only'),
            watermark=watermark,
            tag_matching=tag_matching,
            filters=request_data.get('tag_filters'),
            filter_logic=request_data.get('filter_logic', 'AND'),
            color_rules=color_rules if color_rules else None,
            column_color_pairs=column_color_pairs if column_color_pairs else None,
            max_tags=request_data.get('max_tags'),
            use_streaming=request_data.get('use_streaming'),
            enable_default_color=request_data.get('enable_default_color', True),
            excel_constraint_mode=request_data.get('excel_constraint_mode', False),
            excel_constraint_logic=request_data.get('excel_constraint_logic', 'AND'),
            session_id=session_data.get('session_id'),
            task_id=request_data.get('task_id')
        )
