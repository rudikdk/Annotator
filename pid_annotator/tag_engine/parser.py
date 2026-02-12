"""
Tag parsing and pattern generation for PID Annotator.

This module handles:
- Regex pattern generation from TagMatchingConfig
- Tag format parsing and conversion
- Tag part extraction
"""

import re


def generate_regex_pattern(config):
    """
    Generate regex pattern from TagMatchingConfig.

    Args:
        config: TagMatchingConfig instance

    Returns:
        compiled regex pattern
    """
    # Import here to avoid circular dependency
    from pid_annotator.config import TagMatchingConfig

    # If custom regex is provided, use it
    if config.custom_regex:
        try:
            return re.compile(config.custom_regex, re.IGNORECASE)
        except re.error as e:
            print(f"Invalid custom regex pattern: {e}. Falling back to default pattern.")
            # Fall back to default pattern
            config = TagMatchingConfig.get_default_preset()

    # Escape separators for regex
    escaped_separators = [re.escape(sep) for sep in config.separators]
    separator_pattern = '|'.join(escaped_separators)

    # Build part pattern
    part_pattern = f'[A-Za-z0-9]{{{config.min_part_length},{config.max_part_length}}}'

    # Build full pattern based on min/max parts
    if config.min_parts == config.max_parts:
        # Exact number of parts
        parts = [part_pattern] * config.min_parts
        pattern = f'\\b{f"(?:{separator_pattern})".join(parts)}\\b'
    else:
        # Variable number of parts
        # Start with minimum parts (required)
        required_parts = [part_pattern] * config.min_parts
        required_pattern = f"(?:{separator_pattern})".join(required_parts)

        # Add optional parts
        optional_count = config.max_parts - config.min_parts
        optional_pattern = f"(?:(?:{separator_pattern}){part_pattern}){{0,{optional_count}}}"

        pattern = f'\\b{required_pattern}{optional_pattern}\\b'

    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        print(f"Error compiling generated regex pattern: {e}. Using default pattern.")
        # Fall back to default pattern
        default_pattern = r'\b[A-Za-z0-9]{1,5}[-\.][A-Za-z0-9]{1,5}[-\.][A-Za-z0-9]{1,5}(?:[-\.][A-Za-z0-9]{1,5}){0,2}\b'
        return re.compile(default_pattern, re.IGNORECASE)


def convert_tag_format(tag, from_delimiter="-", to_delimiter="."):
    """Convert tag from one delimiter format to another."""
    return tag.replace(from_delimiter, to_delimiter)


def parse_tag_format(tag, allowed_delimiters=["-", "."]):
    """
    Parse a tag string and determine its format.

    Args:
        tag: The tag string to parse
        allowed_delimiters: List of allowed delimiter characters

    Returns:
        dict: Contains 'valid' (boolean), 'delimiter' (str), 'parts' (list), and 'count' (int)
    """
    if tag.lower() == "nan" or tag == "":
        return {
            'valid': False,
            'delimiter': None,
            'parts': [],
            'count': 0
        }

    # Determine which delimiter is used
    delimiter = None
    for delim in allowed_delimiters:
        if delim in tag:
            delimiter = delim
            break

    # If no delimiter found, tag is invalid
    if not delimiter:
        return {
            'valid': False,
            'delimiter': None,
            'parts': [tag],
            'count': 1
        }

    # Split the tag into parts
    parts = tag.split(delimiter)

    # Check if all parts are non-empty
    all_parts_valid = all(part.strip() for part in parts)

    return {
        'valid': all_parts_valid and len(parts) >= 2,  # At least 2 parts required
        'delimiter': delimiter,
        'parts': parts,
        'count': len(parts)
    }


def parse_tag_parts(tag, allowed_delimiters=["-", "."]):
    """
    Parse a tag and return its individual parts.
    Supports both '-' and '.' delimiters.

    Args:
        tag: Tag string to parse (e.g., "A-HV-001-A" or "A.HV.001.A")
        allowed_delimiters: List of allowed delimiter characters

    Returns:
        list: List of tag parts (e.g., ["A", "HV", "001", "A"])
    """
    if not tag or tag.lower() == "nan" or tag == "":
        return []

    # Find which delimiter is used
    for delim in allowed_delimiters:
        if delim in tag:
            parts = tag.split(delim)
            # Filter out empty parts
            return [part.strip() for part in parts if part.strip()]

    # No delimiter found, return single-part list
    return [tag.strip()] if tag.strip() else []
