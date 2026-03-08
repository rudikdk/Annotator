#!/usr/bin/env python3
"""
Tag parts analysis module

Analyzes Excel files to extract and count the most common values for each tag part position.
Used to populate tag part filter dropdowns in the UI.
"""

import pandas as pd
from collections import defaultdict


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

    # If no delimiter found, return the whole tag as a single part
    return [tag.strip()] if tag.strip() else []


def analyze_tag_parts(excel_path, tag_column, header_row=6, top_n=20, sheet_name=None, start_column='A'):
    """
    Analyze an Excel file and extract the most common values for each tag part.

    Args:
        excel_path: Path to the Excel file
        tag_column: Column name containing the tags
        header_row: Row number containing headers (1-based)
        top_n: Number of top values to return per part
        sheet_name: Sheet name to read (None = first sheet)
        start_column: Excel column letter to start from, e.g. 'A', 'C' (default 'A')

    Returns:
        dict: Contains 'success', 'parts' (dict with part statistics), and 'message'
    """
    try:
        from .excel_helpers import _get_engine, _apply_start_column
        engine = _get_engine(excel_path)
        xl = pd.ExcelFile(excel_path, engine=engine)
        resolved_sheet = sheet_name if sheet_name in xl.sheet_names else xl.sheet_names[0]

        df = xl.parse(sheet_name=resolved_sheet, header=header_row - 1)
        df = _apply_start_column(df, start_column)
        df = df.dropna(axis=1, how="all")

        # Strip whitespace from column names for consistent matching
        df.columns = [str(col).strip() for col in df.columns]

        # Validate tag column
        if tag_column not in df.columns:
            return {
                'success': False,
                'parts': {},
                'message': f"Tag column '{tag_column}' not found in Excel file"
            }

        # Extract all tags
        tags = df[tag_column].dropna().astype(str).str.strip()

        # Track values for each part position
        part_values = defaultdict(lambda: defaultdict(int))  # {part_num: {value: count}}
        max_parts = 0

        for tag in tags:
            if tag and tag.lower() != 'nan':
                parts = parse_tag_parts(tag)
                max_parts = max(max_parts, len(parts))

                for i, part in enumerate(parts):
                    part_num = i + 1  # 1-based
                    part_values[part_num][part.upper()] += 1

        # Build result with top N values for each part
        result_parts = {}
        for part_num in range(1, max_parts + 1):
            if part_num in part_values:
                # Sort by count (descending) and get top N
                sorted_values = sorted(
                    part_values[part_num].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:top_n]

                result_parts[f"part{part_num}"] = [
                    {"value": value, "count": count}
                    for value, count in sorted_values
                ]
            else:
                result_parts[f"part{part_num}"] = []

        return {
            'success': True,
            'parts': result_parts,
            'message': f"Analyzed {len(tags)} tags with up to {max_parts} parts"
        }

    except Exception as e:
        return {
            'success': False,
            'parts': {},
            'message': f"Error analyzing tag parts: {str(e)}"
        }
