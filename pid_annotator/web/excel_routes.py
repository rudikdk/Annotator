"""
Excel analysis and column management routes
"""
import os
import fitz
import pandas as pd
from flask import Blueprint, request, jsonify, session, current_app

from pid_annotator.analysis import (
    analyze_tag_parts,
    analyze_header_unique_values,
    reload_excel_columns
)
from pid_annotator.tag_engine.filters import apply_tag_filters
from pid_annotator.config.tag_matching_config import TagMatchingConfig
from pid_annotator.tag_engine.parser import generate_regex_pattern

# Create blueprint
excel_bp = Blueprint('excel', __name__)


@excel_bp.route('/reload_columns', methods=['POST'])
def reload_columns():
    """Reload Excel columns with new header row"""
    data = request.get_json()
    header_row = data.get('header_row', 6)

    if 'excel_file' not in session:
        return jsonify({'success': False, 'message': 'No Excel file uploaded'})

    excel_path = os.path.join(current_app.config['UPLOAD_FOLDER'], session['excel_file'])
    result = reload_excel_columns(excel_path, header_row)

    if result['success']:
        session['excel_columns'] = result['columns']
        session['default_tag_column'] = result['default_tag_column']
        # Update stored header row in session
        session['header_row'] = header_row

    return jsonify(result)


@excel_bp.route('/get_tag_parts', methods=['POST'])
def get_tag_parts():
    """Analyze Excel file and return available values for each tag part"""
    data = request.get_json()
    header_row = data.get('header_row', 6)
    tag_column = data.get('tag_column')

    # Use selected_excel from request if provided, otherwise fall back to session
    selected_excel = data.get('selected_excel')
    if selected_excel:
        excel_file = selected_excel
    else:
        excel_file = session.get('excel_file')

    if not excel_file:
        return jsonify({'success': False, 'message': 'No Excel file selected'})

    if not tag_column:
        tag_column = session.get('default_tag_column')
        if not tag_column:
            return jsonify({'success': False, 'message': 'No tag column specified'})

    excel_path = os.path.join(current_app.config['UPLOAD_FOLDER'], excel_file)

    if not os.path.exists(excel_path):
        return jsonify({'success': False, 'message': f'Excel file not found: {excel_file}'})

    result = analyze_tag_parts(excel_path, tag_column, header_row, top_n=20)

    return jsonify(result)


@excel_bp.route('/get_header_unique_values', methods=['POST'])
def get_header_unique_values():
    """
    Analyze Excel file and return unique values for a specified header column.
    This is used for header-based filtering and color rules.
    """
    data = request.get_json()
    header_row = data.get('header_row', 6)
    column_name = data.get('column_name')

    # Use selected_excel from request if provided, otherwise fall back to session
    selected_excel = data.get('selected_excel')
    if selected_excel:
        excel_file = selected_excel
    else:
        excel_file = session.get('excel_file')

    if not excel_file:
        return jsonify({'values': [], 'error': 'No Excel file selected'})

    if not column_name:
        return jsonify({'values': [], 'error': 'No column name specified'})

    excel_path = os.path.join(current_app.config['UPLOAD_FOLDER'], excel_file)

    if not os.path.exists(excel_path):
        return jsonify({'values': [], 'error': f'Excel file not found: {excel_file}'})

    # Get unique values for the specified column
    values = analyze_header_unique_values(excel_path, column_name, header_row, top_n=100)

    return jsonify({'values': values, 'error': None})


@excel_bp.route('/get_color_rule_examples', methods=['POST'])
def get_color_rule_examples():
    """
    Return up to 3 matching and 2 non-matching rows from Excel for a color rule being built.
    Used to give the user live feedback in the rule builder.
    """
    data = request.get_json()
    header_row = data.get('header_row', 6)
    column_name = data.get('column_name')
    match_type = data.get('match_type', 'exact')
    value = data.get('value', '')
    tag_column = data.get('tag_column')
    selected_excel = data.get('selected_excel') or session.get('excel_file')

    if not selected_excel or not column_name:
        return jsonify({'matches': [], 'non_matches': []})

    excel_path = os.path.join(current_app.config['UPLOAD_FOLDER'], selected_excel)
    if not os.path.exists(excel_path):
        return jsonify({'matches': [], 'non_matches': []})

    try:
        is_xls = excel_path.lower().endswith('.xls') and not excel_path.lower().endswith('.xlsx')
        engine = 'xlrd' if is_xls else 'openpyxl'
        df = pd.read_excel(excel_path, header=header_row - 1, engine=engine)
        df = df.dropna(axis=1, how='all')
        df.columns = [str(col).strip() for col in df.columns]

        if column_name not in df.columns:
            return jsonify({'matches': [], 'non_matches': []})

        if not tag_column or tag_column not in df.columns:
            tag_column = df.columns[0]

        matches = []
        non_matches = []

        for _, row in df.iterrows():
            tag = str(row[tag_column]).strip()
            if not tag or tag.lower() == 'nan':
                continue

            col_val = row[column_name]
            col_str = str(col_val).strip() if pd.notna(col_val) else ''
            is_empty = col_str == '' or col_str.lower() == 'nan'

            matched = False
            if match_type == 'has_value':
                matched = not is_empty
            elif not is_empty:
                col_upper = col_str.upper()
                val_upper = value.strip().upper()
                if match_type == 'exact':
                    matched = (col_upper == val_upper)
                elif match_type == 'contains':
                    matched = (val_upper in col_upper)
                elif match_type == 'greater_than':
                    try:
                        matched = float(col_str) > float(value)
                    except (ValueError, TypeError):
                        matched = col_upper > val_upper
                elif match_type == 'less_than':
                    try:
                        matched = float(col_str) < float(value)
                    except (ValueError, TypeError):
                        matched = col_upper < val_upper

            entry = {'tag': tag, 'column_value': col_str if not is_empty else '(empty)'}

            if matched and len(matches) < 3:
                matches.append(entry)
            elif not matched and len(non_matches) < 2:
                non_matches.append(entry)

            if len(matches) >= 3 and len(non_matches) >= 2:
                break

        return jsonify({'matches': matches, 'non_matches': non_matches})

    except Exception as e:
        return jsonify({'matches': [], 'non_matches': [], 'error': str(e)})


@excel_bp.route('/preview_filtered_tags', methods=['POST'])
def preview_filtered_tags():
    """Preview which tags match the current filter criteria"""
    data = request.get_json()
    header_row = data.get('header_row', 6)
    tag_column = data.get('tag_column')
    tag_filters = data.get('tag_filters', [])
    filter_logic = data.get('filter_logic', 'AND')

    # Use selected_excel from request if provided, otherwise fall back to session
    selected_excel = data.get('selected_excel')
    if selected_excel:
        excel_file = selected_excel
    else:
        excel_file = session.get('excel_file')

    if not excel_file:
        return jsonify({'success': False, 'message': 'No Excel file selected'})

    if not tag_column:
        tag_column = session.get('default_tag_column')
        if not tag_column:
            return jsonify({'success': False, 'message': 'No tag column specified'})

    excel_path = os.path.join(current_app.config['UPLOAD_FOLDER'], excel_file)

    if not os.path.exists(excel_path):
        return jsonify({'success': False, 'message': f'Excel file not found: {excel_file}'})

    try:
        # Load Excel data
        is_xls = excel_path.lower().endswith('.xls') and not excel_path.lower().endswith('.xlsx')
        if is_xls:
            df = pd.read_excel(excel_path, header=header_row-1, engine='xlrd')
        else:
            df = pd.read_excel(excel_path, header=header_row-1, engine='openpyxl')

        df = df.dropna(axis=1, how="all")

        # Strip whitespace from column names for consistent matching
        df.columns = [str(col).strip() for col in df.columns]

        # Validate tag column exists
        if tag_column not in df.columns:
            return jsonify({'success': False, 'message': f'Tag column "{tag_column}" not found in Excel file'})

        # Extract all tags
        tags = df[tag_column].dropna().astype(str).str.strip()

        # Filter tags
        if tag_filters:
            matching_tags = []
            for tag in tags:
                if tag and tag.lower() != 'nan' and apply_tag_filters(tag, tag_filters, filter_logic):
                    matching_tags.append(tag)
        else:
            # No filters, all tags match
            matching_tags = [tag for tag in tags if tag and tag.lower() != 'nan']

        return jsonify({
            'success': True,
            'matching_tags': matching_tags,
            'total_tags': len([tag for tag in tags if tag and tag.lower() != 'nan']),
            'message': f'{len(matching_tags)} tags match the filter criteria'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error previewing filtered tags: {str(e)}'
        })


@excel_bp.route('/preview_tag_matching', methods=['POST'])
def preview_tag_matching():
    """Preview which tags from PDF would match the current tag matching configuration"""
    data = request.get_json()

    # Get tag matching configuration
    tag_matching_config = data.get('tag_matching_config', {})

    # Get selected PDF (use first selected PDF if multiple)
    selected_pdfs = data.get('selected_pdfs', [])
    if not selected_pdfs or len(selected_pdfs) == 0:
        return jsonify({'success': False, 'message': 'No PDF file selected'})

    pdf_file = selected_pdfs[0]
    pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], pdf_file)

    if not os.path.exists(pdf_path):
        return jsonify({'success': False, 'message': f'PDF file not found: {pdf_file}'})

    try:
        # Create TagMatchingConfig from request data
        config = TagMatchingConfig.from_dict(tag_matching_config)

        # Generate regex pattern from config
        tag_pattern = generate_regex_pattern(config)

        # Open PDF
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        # Sample pages to extract tags from (max 3 pages to keep preview fast)
        sample_size = min(3, total_pages)
        if total_pages <= 3:
            sample_pages = list(range(total_pages))
        else:
            # Sample from beginning, middle, and end
            sample_pages = [
                0,  # First page
                total_pages // 2,  # Middle page
                total_pages - 1  # Last page
            ]

        # Extract matching tags from sample pages
        matched_tags = set()

        for page_num in sample_pages:
            page = doc[page_num]
            text = page.get_text()

            # Find all matches
            matches = tag_pattern.finditer(text)
            for match in matches:
                matched_tags.add(match.group())

        doc.close()

        # Convert to sorted list
        matched_tags_list = sorted(list(matched_tags))

        return jsonify({
            'success': True,
            'matched_tags': matched_tags_list,
            'total_matched': len(matched_tags_list),
            'sample_pages': sample_size,
            'total_pages': total_pages,
            'message': f'Found {len(matched_tags_list)} unique tags from {sample_size} sample pages'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error previewing tag matching: {str(e)}'
        })


@excel_bp.route('/select_excel', methods=['POST'])
def select_excel():
    """Select an Excel file and load its columns"""
    data = request.get_json()
    excel_file = data.get('excel_file')
    header_row = data.get('header_row', 6)

    if not excel_file:
        return jsonify({'success': False, 'message': 'No Excel file specified'})

    # Validate file exists
    excel_path = os.path.join(current_app.config['UPLOAD_FOLDER'], excel_file)
    if not os.path.exists(excel_path):
        return jsonify({'success': False, 'message': f'Excel file not found: {excel_file}'})

    # Update session with selected Excel file
    session['excel_file'] = excel_file

    # Load columns
    result = reload_excel_columns(excel_path, header_row)

    if result['success']:
        session['excel_columns'] = result['columns']
        session['default_tag_column'] = result['default_tag_column']
        session['header_row'] = header_row
        print(f"[SESSION] Selected Excel file updated: {excel_file}")

    return jsonify(result)
