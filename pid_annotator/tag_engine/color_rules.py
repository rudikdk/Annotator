"""
Color rule application for PID Annotator.

This module handles:
- Tag-part based coloring (color by tag part position and value)
- Header-column based coloring (color by Excel column values)
- Conflict detection when multiple rules match
- Hex color to RGB conversion
"""

from .parser import parse_tag_parts


def apply_color_rules(tag, row_data, color_rules, default_color="#FFFF00"):
    """
    Apply color rules to a tag and return the appropriate highlight color.
    Now supports both tag-part based coloring and header-column based coloring.

    Args:
        tag: Tag string to check (e.g., "A-HV-001-A")
        row_data: Pandas Series containing the Excel row data for this tag (required for header_column rules)
        color_rules: List of color rule dictionaries, each containing:
            For tag_part rules:
                - rule_type: "tag_part" (default if not specified)
                - part: Part number (1-based index, e.g., 2 for second part)
                - value: Value to match
                - match_type: "exact" or "contains"
                - color: Hex color code (e.g., "#0000FF")
                - id: Unique identifier for the rule
            For header_column rules:
                - rule_type: "header_column"
                - column_name: Name of the Excel column to check
                - value: Value to match against column data
                - match_type: "exact" or "contains"
                - color: Hex color code (e.g., "#0000FF")
                - id: Unique identifier for the rule
        default_color: Fallback color if no rules match

    Returns:
        tuple: (color_hex, matched_rule_id, conflicts)
            - color_hex: The color to use (or default_color if no match)
            - matched_rule_id: ID of the matched rule (or None)
            - conflicts: List of rule IDs that also matched (empty if no conflicts)
    """
    if not color_rules:
        return default_color, None, []

    if not tag or tag.lower() == "nan":
        return None, None, []

    # Parse tag into parts (needed for tag_part rules)
    tag_parts = parse_tag_parts(tag)

    if not tag_parts:
        return None, None, []

    # Track all matching rules (last match wins, but we report conflicts)
    matched_color = None
    matched_rule_id = None
    all_matched_rule_ids = []

    # Iterate through rules (last matching rule wins)
    for rule in color_rules:
        rule_type = rule.get('rule_type', 'tag_part')  # Default to tag_part for backward compatibility
        value = rule.get('value', '').strip()
        match_type = rule.get('match_type', 'exact')
        color = rule.get('color', '#FFFF00')
        rule_id = rule.get('id', '')

        # Check if this rule matches
        matches = False

        if rule_type == 'header_column':
            # Header column matching - requires row_data
            if row_data is None:
                continue  # Skip if no row data provided

            column_name = rule.get('column_name', '')
            if not column_name or column_name not in row_data.index:
                continue  # Skip if column doesn't exist

            # Get the column value from row data
            column_value = str(row_data[column_name]).strip()
            if column_value.lower() == 'nan' or column_value == '':
                continue  # Skip empty values

            # Compare column value with rule value (case-insensitive)
            column_value_upper = column_value.upper()
            value_upper = value.upper()

            # Check if rule matches
            if match_type == 'exact':
                matches = (column_value_upper == value_upper)
            elif match_type == 'contains':
                matches = (value_upper in column_value_upper)

        else:  # tag_part matching (original logic)
            part = rule.get('part', 1)
            part_index = part - 1  # Convert to 0-based

            # Skip if tag doesn't have this part
            if part_index < 0 or part_index >= len(tag_parts):
                continue

            tag_part = tag_parts[part_index].upper()
            value_upper = value.upper()

            # Check if rule matches
            if match_type == 'exact':
                matches = (tag_part == value_upper)
            elif match_type == 'contains':
                matches = (value_upper in tag_part)

        if matches:
            # Track this match
            all_matched_rule_ids.append(rule_id)
            # Update matched color (last match wins)
            matched_color = color
            matched_rule_id = rule_id

    # Determine conflicts (if more than one rule matched)
    conflicts = all_matched_rule_ids[:-1] if len(all_matched_rule_ids) > 1 else []

    # If no rules matched, use default color
    if not matched_color:
        return default_color, None, []

    return matched_color, matched_rule_id, conflicts


def _hex_to_rgb01(hex_color):
    """Convert hex like '#RRGGBB' to (r,g,b) floats in 0..1. Returns black on failure."""
    try:
        color_hex = hex_color.lstrip('#')
        if len(color_hex) == 6:
            return (
                int(color_hex[0:2], 16) / 255.0,
                int(color_hex[2:4], 16) / 255.0,
                int(color_hex[4:6], 16) / 255.0
            )
    except Exception:
        pass
    return (0, 0, 0)
