#!/usr/bin/env python3
"""
Column analysis module

Analyzes Excel columns to extract unique values and their frequencies.
Used to populate filter and color rule dropdowns for header-based matching.
"""

import pandas as pd


def analyze_header_unique_values(excel_path, column_name, header_row=6, top_n=100, sheet_name=None, start_column='A'):
    """
    Analyze an Excel file and extract unique values from a specific column.
    This function is used to populate filter and color rule dropdowns for header-based matching.

    Args:
        excel_path: Path to the Excel file
        column_name: Name of the column to analyze
        header_row: Row number containing headers (1-based, default: 6)
        top_n: Maximum number of unique values to return (default: 100)
        sheet_name: Sheet name to read (None = first sheet)
        start_column: Excel column letter to start from, e.g. 'A', 'C' (default 'A')

    Returns:
        list: List of dictionaries with 'value' and 'count' keys, sorted by count descending
              Example: [{"value": "Valve", "count": 45}, {"value": "Pump", "count": 23}]
              Returns empty list on error
    """
    try:
        from .excel_helpers import _get_engine, _apply_start_column
        engine = _get_engine(excel_path)
        xl = pd.ExcelFile(excel_path, engine=engine)
        resolved_sheet = sheet_name if sheet_name in xl.sheet_names else xl.sheet_names[0]

        df = xl.parse(sheet_name=resolved_sheet, header=header_row - 1)
        df = _apply_start_column(df, start_column)

        # Remove completely empty columns
        df = df.dropna(axis=1, how="all")

        # Strip whitespace from column names for consistent matching
        df.columns = [str(col).strip() for col in df.columns]

        # Validate column exists
        if column_name not in df.columns:
            print(f"[WARNING] Column '{column_name}' not found in Excel file")
            return []

        # Extract column values, remove NaN/empty values
        column_values = df[column_name].dropna().astype(str).str.strip()

        # Filter out empty strings and 'nan' strings
        column_values = column_values[
            (column_values != '') &
            (column_values.str.lower() != 'nan')
        ]

        # Count occurrences of each unique value
        value_counts = column_values.value_counts()

        # Build result list with top N values
        result = [
            {"value": str(value), "count": int(count)}
            for value, count in value_counts.head(top_n).items()
        ]

        return result

    except Exception as e:
        print(f"[ERROR] Error analyzing header column '{column_name}': {str(e)}")
        return []
