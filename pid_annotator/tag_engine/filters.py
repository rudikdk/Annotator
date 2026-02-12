"""
Tag filtering logic for PID Annotator.

This module handles:
- Tag-part based filtering (include/exclude by tag part position and value)
- Header-column based filtering (include/exclude by Excel column values)
- AND/OR filter logic combination
"""

from .parser import parse_tag_parts


def apply_tag_filters(tag, filters, filter_logic="AND", row_data=None):
    """
    Check if a tag matches the filter criteria.
    Now supports both tag-part based filtering and header-column based filtering.

    Args:
        tag: Tag string to check
        filters: List of filter rules, each containing:
            For tag_part filters:
                - filter_type: "tag_part" (default if not specified)
                - part: Part number (1-based index, e.g., 2 for second part)
                - value: Value to match
                - match_type: "exact" or "contains"
                - action: "include" or "exclude"
            For header_column filters:
                - filter_type: "header_column"
                - column_name: Name of the Excel column to check
                - value: Value to match against column data
                - match_type: "exact" or "contains"
                - action: "include" or "exclude"
        filter_logic: "AND" or "OR" - how to combine multiple filters
        row_data: Pandas Series containing the Excel row data (required for header_column filters)

    Returns:
        bool: True if tag should be processed, False if it should be filtered out
    """
    if not filters:
        return True  # No filters means all tags pass

    if not tag or tag.lower() == "nan":
        return False

    # Parse tag into parts (needed for tag_part filters)
    tag_parts = parse_tag_parts(tag)

    if not tag_parts:
        return False

    # Separate include and exclude filters
    include_filters = [f for f in filters if f.get('action') == 'include']
    exclude_filters = [f for f in filters if f.get('action') == 'exclude']

    # Check exclude filters first (if any exclude filter matches, tag is excluded)
    for filter_rule in exclude_filters:
        filter_type = filter_rule.get('filter_type', 'tag_part')  # Default to tag_part for backward compatibility
        value = filter_rule.get('value', '').strip()
        match_type = filter_rule.get('match_type', 'exact')

        if filter_type == 'header_column':
            # Header column filtering - requires row_data
            if row_data is None:
                continue  # Skip if no row data provided

            column_name = filter_rule.get('column_name', '')
            if not column_name or column_name not in row_data.index:
                continue  # Skip if column doesn't exist

            # Get the column value from row data
            column_value = str(row_data[column_name]).strip()
            if column_value.lower() == 'nan' or column_value == '':
                continue  # Skip empty values

            # Compare column value with filter value (case-insensitive)
            column_value_upper = column_value.upper()
            value_upper = value.upper()

            # Check if filter matches
            if match_type == 'exact':
                if column_value_upper == value_upper:
                    return False  # Excluded
            elif match_type == 'contains':
                if value_upper in column_value_upper:
                    return False  # Excluded

        else:  # tag_part filtering (original logic)
            part_index = filter_rule.get('part', 1) - 1  # Convert to 0-based

            # Skip if tag doesn't have this part
            if part_index < 0 or part_index >= len(tag_parts):
                continue

            tag_part = tag_parts[part_index].upper()
            value_upper = value.upper()

            # Check if filter matches
            if match_type == 'exact':
                if tag_part == value_upper:
                    return False  # Excluded
            elif match_type == 'contains':
                if value_upper in tag_part:
                    return False  # Excluded

    # If no include filters, tag passes (wasn't excluded)
    if not include_filters:
        return True

    # Check include filters based on logic
    matches = []
    for filter_rule in include_filters:
        filter_type = filter_rule.get('filter_type', 'tag_part')  # Default to tag_part for backward compatibility
        value = filter_rule.get('value', '').strip()
        match_type = filter_rule.get('match_type', 'exact')

        if filter_type == 'header_column':
            # Header column filtering - requires row_data
            if row_data is None:
                matches.append(False)
                continue

            column_name = filter_rule.get('column_name', '')
            if not column_name or column_name not in row_data.index:
                matches.append(False)
                continue

            # Get the column value from row data
            column_value = str(row_data[column_name]).strip()
            if column_value.lower() == 'nan' or column_value == '':
                matches.append(False)
                continue

            # Compare column value with filter value (case-insensitive)
            column_value_upper = column_value.upper()
            value_upper = value.upper()

            # Check if filter matches
            if match_type == 'exact':
                matches.append(column_value_upper == value_upper)
            elif match_type == 'contains':
                matches.append(value_upper in column_value_upper)
            else:
                matches.append(False)

        else:  # tag_part filtering (original logic)
            part_index = filter_rule.get('part', 1) - 1  # Convert to 0-based

            # If tag doesn't have this part, it doesn't match this filter
            if part_index < 0 or part_index >= len(tag_parts):
                matches.append(False)
                continue

            tag_part = tag_parts[part_index].upper()
            value_upper = value.upper()

            # Check if filter matches
            if match_type == 'exact':
                matches.append(tag_part == value_upper)
            elif match_type == 'contains':
                matches.append(value_upper in tag_part)
            else:
                matches.append(False)

    # Apply logic
    if filter_logic == "AND":
        return all(matches) if matches else False
    else:  # OR
        return any(matches) if matches else False


def is_valid_tag(tag, config=None):
    """
    Validate a tag string against configuration rules.

    Args:
        tag: Tag string to validate
        config: TagMatchingConfig instance (optional)

    Returns:
        bool: True if tag is valid, False otherwise
    """
    from pid_annotator.config import TagMatchingConfig

    if config is None:
        config = TagMatchingConfig.get_default_preset()

    # Basic validation - tags should not be empty or contain only whitespace
    if not tag or not tag.strip():
        return False

    # Calculate reasonable length bounds from part configuration
    # min_length = min_parts * min_part_length + (min_parts - 1) separators
    # max_length = max_parts * max_part_length + (max_parts - 1) separators
    min_tag_length = config.min_parts * config.min_part_length + max(0, config.min_parts - 1)
    max_tag_length = config.max_parts * config.max_part_length + max(0, config.max_parts - 1)

    # Apply minimum length check
    if len(tag) < min_tag_length:
        return False

    # Apply maximum length check
    if len(tag) > max_tag_length:
        return False

    return True
