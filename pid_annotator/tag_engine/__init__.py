"""
Tag engine module for PID Annotator.

This module provides:
- Regex pattern generation from TagMatchingConfig
- Tag parsing and format conversion
- Tag filtering (include/exclude by part or column)
- Color rule application
"""

from .parser import (
    generate_regex_pattern,
    convert_tag_format,
    parse_tag_format,
    parse_tag_parts,
)
from .filters import apply_tag_filters, is_valid_tag
from .color_rules import apply_color_rules, _hex_to_rgb01

__all__ = [
    # Parser functions
    'generate_regex_pattern',
    'convert_tag_format',
    'parse_tag_format',
    'parse_tag_parts',
    # Filter functions
    'apply_tag_filters',
    'is_valid_tag',
    # Color rule functions
    'apply_color_rules',
    '_hex_to_rgb01',
]
