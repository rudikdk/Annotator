#!/usr/bin/env python3
"""
Excel helpers module

Utility functions for working with Excel files, particularly for reloading columns
with different header row configurations.
"""

import pandas as pd


def _get_engine(excel_path: str) -> str:
    """Return the correct pandas engine for the given Excel file."""
    lower = excel_path.lower()
    if lower.endswith('.xls') and not lower.endswith('.xlsx'):
        return 'xlrd'
    return 'openpyxl'


def _apply_start_column(df, start_column: str):
    """Drop all columns to the left of start_column (Excel letter, e.g. 'C')."""
    start_column = (start_column or 'A').upper()
    if start_column == 'A':
        return df
    try:
        from openpyxl.utils import column_index_from_string
        start_idx = column_index_from_string(start_column) - 1
        if 0 < start_idx < len(df.columns):
            return df.iloc[:, start_idx:]
    except Exception:
        pass
    return df


def get_excel_sheets(excel_path: str) -> list:
    """Return list of sheet names for an Excel file. Returns [] on error."""
    try:
        xl = pd.ExcelFile(excel_path, engine=_get_engine(excel_path))
        return xl.sheet_names
    except Exception:
        return []


def reload_excel_columns(excel_path, header_row, sheet_name=None, start_column='A'):
    """
    Reload Excel columns with a new header row, optional sheet, and optional start column.

    Args:
        excel_path: Path to the Excel file
        header_row: Row number containing headers (1-based)
        sheet_name: Sheet name to read (None = first sheet)
        start_column: Excel column letter to start reading from, e.g. 'A', 'C' (default 'A')

    Returns:
        dict: Contains 'success', 'columns', 'message', 'default_tag_column',
              'sheet_names', 'active_sheet'
    """
    try:
        if header_row < 1:
            return {
                'success': False,
                'columns': [],
                'message': 'Header row must be 1 or greater',
                'default_tag_column': None,
                'sheet_names': [],
                'active_sheet': None,
            }

        engine = _get_engine(excel_path)

        # Get sheet names
        xl = pd.ExcelFile(excel_path, engine=engine)
        sheet_names = xl.sheet_names

        # Resolve sheet
        if sheet_name not in sheet_names:
            sheet_name = sheet_names[0] if sheet_names else 0

        df = xl.parse(sheet_name=sheet_name, header=header_row - 1)

        # Apply start column filter (drop columns to the left of start_column)
        start_column = (start_column or 'A').upper()
        if start_column != 'A':
            try:
                from openpyxl.utils import column_index_from_string
                start_idx = column_index_from_string(start_column) - 1
                if 0 < start_idx < len(df.columns):
                    df = df.iloc[:, start_idx:]
            except Exception:
                pass  # Invalid column letter — ignore, use full dataframe

        df = df.dropna(axis=1, how="all")  # Remove empty columns
        columns = [str(col).strip() for col in df.columns]

        return {
            'success': True,
            'columns': columns,
            'message': f"Successfully loaded {len(columns)} columns from header row {header_row}",
            'default_tag_column': None,
            'sheet_names': sheet_names,
            'active_sheet': sheet_name,
        }

    except Exception as e:
        return {
            'success': False,
            'columns': [],
            'message': f'Error loading Excel columns: {str(e)}',
            'default_tag_column': None,
            'sheet_names': [],
            'active_sheet': None,
        }
