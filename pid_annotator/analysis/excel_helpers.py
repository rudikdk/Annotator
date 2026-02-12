#!/usr/bin/env python3
"""
Excel helpers module

Utility functions for working with Excel files, particularly for reloading columns
with different header row configurations.
"""

import pandas as pd


def reload_excel_columns(excel_path, header_row):
    """
    Reload Excel columns with a new header row

    Args:
        excel_path: Path to the Excel file
        header_row: Row number containing headers (1-based)

    Returns:
        dict: Contains 'success', 'columns', 'message', 'default_tag_column'
    """
    try:
        if header_row < 1:
            return {
                'success': False,
                'columns': [],
                'message': 'Header row must be 1 or greater',
                'default_tag_column': None
            }

        # Support both .xlsx and .xls files
        # .xls files can be read for processing but cannot be annotated (Excel annotation disabled for .xls)
        is_xls = excel_path.lower().endswith('.xls') and not excel_path.lower().endswith('.xlsx')

        if is_xls:
            # Use xlrd engine for .xls files
            df = pd.read_excel(excel_path, header=header_row-1, engine='xlrd')
        else:
            # Use openpyxl engine for .xlsx files
            df = pd.read_excel(excel_path, header=header_row-1, engine='openpyxl')

        df = df.dropna(axis=1, how="all")  # Remove empty columns

        # Strip whitespace from column names to prevent matching issues
        columns = [str(col).strip() for col in df.columns]

        # Default tag column to None - user must select manually
        default_tag_column = None

        # Build message
        message = f"Successfully loaded {len(columns)} columns from header row {header_row}"

        return {
            'success': True,
            'columns': columns,
            'message': message,
            'default_tag_column': default_tag_column
        }

    except Exception as e:
        return {
            'success': False,
            'columns': [],
            'message': f'Error loading Excel columns: {str(e)}',
            'default_tag_column': None
        }
