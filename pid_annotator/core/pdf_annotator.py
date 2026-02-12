"""
PDF annotation engine - main processing logic.

This module contains the core annotation functions that process PDF files with
metadata from Excel files, applying highlights, comments, and watermarks.
"""

import os
import gc
import time
import fitz  # PyMuPDF
import pandas as pd
from collections import defaultdict
from io import BytesIO

# Watermark overlay libs
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter

# Configuration
from pid_annotator.config import (
    AnnotationConfig,
    TagMatchingConfig,
    STREAMING_THRESHOLD_MB,
)

# Tag engine functions
from pid_annotator.tag_engine import (
    convert_tag_format,
    parse_tag_format,
    apply_tag_filters,
    apply_color_rules,
    _hex_to_rgb01,
    is_valid_tag,
)

# Core processing functions
from pid_annotator.core.pdf_indexer import (
    build_tag_index,
    build_page_statistics,
    build_page_bookmark_map,
)


def _get_file_size_mb(filepath):
    """Get file size in megabytes."""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except:
        return 0


def apply_color_rules_to_all_text(doc, tag_index, color_rules, default_highlight_color="#FFFF00",
                                  enable_default_color=True, excel_tags_set=None,
                                  excel_constraint_mode=False, excel_constraint_logic="AND",
                                  tag_filters=None, filter_logic="AND",
                                  progress_callback=None, page_bookmark_map=None, df=None, tag_col=None, header_row=6):
    """
    Apply color rules to ALL text in the PDF that matches tag patterns, with optional Excel constraints.

    Args:
        doc: PyMuPDF document object
        tag_index: Pre-built tag index from build_tag_index()
        color_rules: List of color rule dictionaries
        default_highlight_color: Default color for tags that don't match any rule
        enable_default_color: Whether to use default color for unmatched tags
        excel_tags_set: Set of tags from Excel (after filtering)
        excel_constraint_mode: Whether to constrain coloring to Excel tags
        excel_constraint_logic: "AND" or "OR" logic for Excel constraint
        tag_filters: List of tag filter dictionaries (for filtering PDF tags)
        filter_logic: "AND" or "OR" logic for tag filters
        progress_callback: Optional progress callback function
        page_bookmark_map: dict mapping page numbers to bookmark titles (optional)

    Returns:
        dict: Statistics about colored tags including page-level breakdown
    """
    # If no color rules AND default color is disabled, nothing to do
    if not color_rules and not enable_default_color:
        return {'total_tags': 0, 'colored_tags': 0, 'page_stats': {}}

    colored_count = 0
    total_count = 0
    page_stats = {}  # {page_num: {'colored_count': X, 'total_count': Y, 'bookmark': 'Title', 'tag_details': []}}
    detail_lookup = {}
    seen_occurrences = set()
    colored_occurrences = set()

    def _make_occurrence_key(page_num, rects, original_tag):
        if rects:
            coords = tuple(
                (
                    round(rect.x0, 3),
                    round(rect.y0, 3),
                    round(rect.x1, 3),
                    round(rect.y1, 3),
                )
                for rect in rects
            )
        else:
            coords = tuple()
        return (page_num, original_tag.upper(), coords)

    # Initialize excel_tags_set if not provided
    if excel_tags_set is None:
        excel_tags_set = set()

    # Build mapping from tag to Excel row data if df is provided
    tag_to_row_data = {}
    if df is not None and tag_col is not None:
        for idx, row in df.iterrows():
            tag = str(row[tag_col]).strip()
            if not tag or tag.lower() == 'nan':
                continue

            # Normalize tag for matching
            normalized_tag = tag.upper()

            # Build row data dict with all Excel columns
            excel_row_num = header_row + 1 + idx
            row_dict = {'excel_row': excel_row_num}
            for col in df.columns:
                row_dict[col] = row[col] if pd.notna(row[col]) else ''

            # Store with ALL variants of the tag as keys to handle both dash and dot delimiters
            tag_variants = set()
            tag_variants.add(normalized_tag)  # Original format

            # Generate dash and dot variants
            if '-' in normalized_tag:
                tag_variants.add(convert_tag_format(normalized_tag, from_delimiter="-", to_delimiter="."))
            elif '.' in normalized_tag:
                tag_variants.add(convert_tag_format(normalized_tag, from_delimiter=".", to_delimiter="-"))

            # Store row data for each variant
            for variant in tag_variants:
                tag_to_row_data[variant] = row_dict

    # Process all tags found in the PDF
    for tag_text, locations in tag_index.items():
        # Check if tag is in Excel list
        in_excel = tag_text in excel_tags_set

        # Check if tag passes tag filters (for PDF tags)
        passes_filters = True
        if tag_filters:
            passes_filters = apply_tag_filters(tag_text, tag_filters, filter_logic)

        # Determine color for this tag
        # Pass None as default_color so unmatched tags don't automatically get a color;
        # the enable_default_color logic below decides if a default color should be applied
        if color_rules:
            highlight_color, matched_rule_id, conflicts = apply_color_rules(
                tag_text, None, color_rules, None
            )
        else:
            # No color rules defined - use default color if enabled
            highlight_color = default_highlight_color if enable_default_color else None
            matched_rule_id = None
            conflicts = []

        # Determine if this tag should be colored based on constraint mode
        should_color = False
        coloring_reason = "Not colored"

        if not excel_constraint_mode:
            # No constraint - color all tags (or filtered tags if filters are enabled)
            if passes_filters:
                # Tag passes filters (or no filters set)
                if highlight_color is not None:
                    # Has a color rule match
                    should_color = True
                    if matched_rule_id:
                        coloring_reason = f"Color rule matched (Rule ID: {matched_rule_id})"
                    else:
                        coloring_reason = "Color rule matched"
                elif enable_default_color:
                    # No rule match but default color enabled
                    should_color = True
                    highlight_color = default_highlight_color
                    coloring_reason = "Default color (no specific rule matched)"
            else:
                coloring_reason = "Excluded by tag filters"
        elif excel_constraint_logic == 'AND':
            # AND logic: Tag must be in Excel AND (match a color rule OR use default color)
            if in_excel:
                if matched_rule_id is not None:
                    should_color = True
                    coloring_reason = f"Excel tag with color rule (Rule ID: {matched_rule_id})"
                elif enable_default_color:
                    # Use default color for Excel tags that don't match any specific rule
                    should_color = True
                    if not highlight_color:
                        highlight_color = default_highlight_color
                    coloring_reason = "Excel tag with default color"
                else:
                    coloring_reason = "In Excel but no color rule matched"
            else:
                coloring_reason = "Not in Excel (AND constraint active)"
        elif excel_constraint_logic == 'OR':
            # OR logic: Color if (tag passes filters AND matches rules) OR tag is in Excel
            if passes_filters and highlight_color is not None:
                # Tag matches filters and has a color rule
                should_color = True
                if matched_rule_id:
                    coloring_reason = f"Color rule matched (Rule ID: {matched_rule_id})"
                else:
                    coloring_reason = "Color rule matched"
            elif in_excel:
                # Tag is in Excel - use matched color or default
                should_color = True
                if not highlight_color and enable_default_color:
                    highlight_color = default_highlight_color
                if matched_rule_id:
                    coloring_reason = f"Excel tag with color rule (Rule ID: {matched_rule_id})"
                else:
                    coloring_reason = "Excel tag with default color"
            elif passes_filters and enable_default_color:
                # Tag passes filters but has no specific rule - use default color
                should_color = True
                highlight_color = default_highlight_color
                coloring_reason = "Passed filters with default color"
            else:
                if not passes_filters:
                    coloring_reason = "Excluded by tag filters"
                elif not in_excel:
                    coloring_reason = "Not in Excel (OR constraint active)"
                else:
                    coloring_reason = "No color rules matched"

        # Track page-level statistics for all tags
        for page_num, rects, original_tag in locations:
            occurrence_key = _make_occurrence_key(page_num, rects, original_tag)

            # Initialize page stats if not exists
            if page_num not in page_stats:
                # Get bookmark title for this page
                bookmark_title = page_bookmark_map.get(page_num, 'N/A') if page_bookmark_map else 'N/A'
                page_stats[page_num] = {
                    'colored_count': 0,
                    'total_count': 0,
                    'bookmark': bookmark_title,
                    'tag_details': []
                }

            # Skip duplicate occurrences that arise from variant tag keys
            if occurrence_key in seen_occurrences:
                continue

            seen_occurrences.add(occurrence_key)
            total_count += 1

            # Increment total count for this page
            page_stats[page_num]['total_count'] += 1

            detail_entry = {
                'tag': tag_text,
                'found_text': original_tag,
                'in_excel': bool(in_excel),
                'colored': False,
                'coloring_reason': coloring_reason
            }

            # Add row_data if tag is in Excel and we have the data
            if in_excel and tag_text in tag_to_row_data:
                detail_entry['row_data'] = tag_to_row_data[tag_text]

            page_stats[page_num]['tag_details'].append(detail_entry)
            detail_lookup[occurrence_key] = detail_entry

        if not should_color or not highlight_color:
            continue

        # Apply color to all occurrences of this tag
        for page_num, rects, original_tag in locations:
            occurrence_key = _make_occurrence_key(page_num, rects, original_tag)
            if occurrence_key in colored_occurrences:
                continue

            try:
                page = doc[page_num]

                # Add highlight annotation
                hl = page.add_highlight_annot(rects)

                # Convert hex color to RGB
                try:
                    r, g, b = _hex_to_rgb01(highlight_color)
                    hl.set_colors(stroke=(r, g, b))
                except Exception:
                    hl.set_colors(stroke=(1, 1, 0))  # Fallback to yellow

                hl.update()
                colored_count += 1

                colored_occurrences.add(occurrence_key)

                # Increment colored count for this page
                page_stats[page_num]['colored_count'] += 1

                detail_entry = detail_lookup.get(occurrence_key)
                if detail_entry:
                    detail_entry['colored'] = True
                    # Update coloring reason to reflect that it was actually colored
                    if 'Not colored' in detail_entry.get('coloring_reason', ''):
                        detail_entry['coloring_reason'] = coloring_reason

            except Exception as e:
                print(f"Error coloring tag {tag_text} on page {page_num}: {e}")
                continue

    return {
        'total_tags': total_count,
        'colored_tags': colored_count,
        'page_stats': page_stats
    }


def process_annotations_from_index(
    doc,
    df,
    tag_index,
    tag_col,
    column_color_pairs=None,
    selected_comment_columns=None,
    annotation_type="highlight_only",
    watermark_enabled=False,
    watermark_attribute="",
    watermark_text_color="#000000",
    max_tags=None,
    update_progress=None,
    watermark_items_by_page=None,
    default_highlight_color="#FFFF00",
    header_row=6,
    config=None,
    tag_filters=None,
    filter_logic="AND",
    page_bookmark_map=None,
    color_rules=None,
    enable_default_color=True
):
    """
    Process annotations using the pre-built tag index for optimal performance.

    Args:
        doc: PyMuPDF document object
        df: DataFrame with Excel data
        tag_index: Pre-built tag index from build_tag_index()
        tag_col: Column name containing tags
        column_color_pairs: list of (column, color) - DEPRECATED, use color_rules instead
        selected_comment_columns: which columns to include in notes
        annotation_type: "highlight_only" or "note_only"
        watermark_enabled: enable watermark placement
        watermark_attribute: Excel column to render as watermark text
        watermark_text_color: color for watermark text (hex)
        max_tags: optional limit
        update_progress: progress callback
        watermark_items_by_page: dict(page_num -> [ {text,x,y,font_size} ])
        default_highlight_color: hex color used when no color rules match but attribute has value
        header_row: Excel header row number (1-based) for row number tracking
        config: TagMatchingConfig instance (uses default if not provided)
        tag_filters: List of filter rules to apply to tags (optional)
        filter_logic: "AND" or "OR" for combining multiple filters (default: "AND")
        page_bookmark_map: dict mapping page numbers to bookmark titles (optional)
        color_rules: List of color rule dicts (part, value, match_type, color, attribute_column, id)

    Returns:
        tuple: (found_tags, skipped_tags, processed_tags_set, report_data)
    """
    print("Processing annotations using tag index...")
    start_time = time.time()

    # Use default config if not provided
    if config is None:
        config = TagMatchingConfig.get_default_preset()

    if watermark_items_by_page is None:
        watermark_items_by_page = defaultdict(list)

    found_tags = 0
    skipped_tags = 0
    processed_tags = set()

    # Initialize report data structure
    report_data = {
        'found': [],  # List of {tag, pages, occurrence_count, excel_row}
        'not_found': [],  # List of {tag, excel_row, reason}
        'duplicates': {},  # Dict of {tag: [excel_rows]}
        'validation_warnings': [],  # List of {tag, excel_row, warning}
        'color_conflicts': []  # List of {tag, excel_row, matched_rule_id, conflict_rule_ids}
    }

    # Track which tags appear multiple times in Excel (duplicates)
    tag_excel_rows = defaultdict(list)  # {tag: [row_numbers]}
    tag_excel_row_data = defaultdict(list)  # {tag: [full_row_data_dicts]}

    # Track annotations per page: {page_num: set of (tag, rect_key) tuples}
    # This tracks ALL tags that received ANY annotation (highlight, comment, or watermark)
    annotated_tags_by_page = defaultdict(set)

    # Limit processing if max_tags specified
    total_to_process = min(max_tags, len(df)) if max_tags and max_tags > 0 else len(df)

    for i, (df_index, row) in enumerate(df.iterrows()):
        # Calculate Excel row number (df index is 0-based, Excel row is header_row + 1 + df_index)
        excel_row = header_row + 1 + df_index

        if max_tags and i >= max_tags:
            print(f"Reached maximum number of tags ({max_tags}). Stopping processing.")
            break

        if update_progress:
            progress = int((i / total_to_process) * 100) if total_to_process else 100
            update_progress(progress, f"Processing tag {i+1}/{total_to_process}...")

        tag = str(row[tag_col]).strip()

        # Track all tags and their Excel rows (for duplicate detection)
        if tag and tag.lower() != 'nan':
            tag_excel_rows[tag].append(excel_row)
            # Store full row data for duplicates report
            row_dict = {'excel_row': excel_row}
            for col in df.columns:
                row_dict[col] = row[col] if pd.notna(row[col]) else ''
            tag_excel_row_data[tag].append(row_dict)

        # Skip empty or invalid tags
        if not tag or not is_valid_tag(tag, config):
            if tag:  # Only log if tag exists but is invalid
                print(f"Skipping invalid tag: {tag}")
                skipped_tags += 1
                # Add validation warning to report
                tag_info = parse_tag_format(tag, config.separators)
                if not tag_info['valid']:
                    report_data['validation_warnings'].append({
                        'tag': tag,
                        'excel_row': excel_row,
                        'warning': f"Invalid tag format - has {tag_info['count']} parts, needs {config.min_parts}-{config.max_parts}"
                    })
            continue

        # Apply tag filters if provided
        if tag_filters:
            if not apply_tag_filters(tag, tag_filters, filter_logic, row_data=row):
                print(f"Skipping tag due to filter: {tag}")
                skipped_tags += 1
                # Skip filtered tags entirely - do NOT add to report
                # Filtered tags should not appear in the report at all
                continue

        # Skip already processed tags (duplicate in Excel)
        if tag in processed_tags:
            print(f"Skipping duplicate tag: {tag}")
            skipped_tags += 1
            # Duplicate will be tracked in tag_excel_rows and processed at the end
            continue

        # Normalize tag for index lookup
        normalized_tag = tag.upper()

        # Try to find tag in index (check multiple variants)
        tag_variants = [
            normalized_tag,
            convert_tag_format(normalized_tag, from_delimiter="-", to_delimiter="."),
            convert_tag_format(normalized_tag, from_delimiter=".", to_delimiter="-")
        ]

        tag_locations = []
        for variant in tag_variants:
            if variant in tag_index:
                tag_locations = tag_index[variant]
                break

        # If partial matching is enabled and no exact match found, try partial matching
        if not tag_locations and config.allow_partial_match:
            for index_tag, locations in tag_index.items():
                # Check if the index tag starts with any of our tag variants
                if any(index_tag.startswith(variant) for variant in tag_variants):
                    tag_locations.extend(locations)
            # Remove duplicates if multiple partial matches found
            if tag_locations:
                seen = set()
                unique_locations = []
                for loc in tag_locations:
                    loc_key = (loc[0], tuple(loc[1]))  # (page_num, tuple of rects)
                    if loc_key not in seen:
                        seen.add(loc_key)
                        unique_locations.append(loc)
                tag_locations = unique_locations
                print(f"Found tag via partial matching: {tag} ({len(tag_locations)} occurrences)")

        if not tag_locations:
            # Tag not found in PDF - add to report
            # Build row_data dict with all Excel columns
            row_dict = {'excel_row': excel_row}
            for col in df.columns:
                row_dict[col] = row[col] if pd.notna(row[col]) else ''

            report_data['not_found'].append({
                'tag': tag,
                'excel_row': excel_row,
                'reason': 'not_in_pdf',
                'row_data': row_dict
            })
            continue  # Tag not found in PDF

        # Create note text
        if selected_comment_columns is not None:
            columns_to_include = [col for col in selected_comment_columns if col in df.columns and col != tag_col]
            if columns_to_include:
                note_text = f"TAG: {tag}\n" + "\n".join(
                    f"{col}: {row[col]}" for col in columns_to_include if pd.notna(row[col])
                )
            else:
                note_text = ""
        else:
            note_text = ""

        # Process all occurrences of this tag
        for page_num, rects, original_tag in tag_locations:
            page = doc[page_num]

            try:
                # Determine highlight color using new color rules system
                highlight_color = None
                matched_rule_id = None
                conflicts = []

                # Use new color_rules system if provided
                if color_rules:
                    highlight_color, matched_rule_id, conflicts = apply_color_rules(
                        tag, row, color_rules, default_highlight_color if enable_default_color else None
                    )

                    # Track conflicts for reporting
                    if conflicts:
                        report_data['color_conflicts'].append({
                            'tag': tag,
                            'excel_row': excel_row,
                            'matched_rule_id': matched_rule_id,
                            'conflict_rule_ids': conflicts
                        })
                # Fall back to legacy column_color_pairs system for backward compatibility
                elif column_color_pairs:
                    for column, color in column_color_pairs:
                        if column and column in df.columns:
                            if pd.notna(row[column]) and str(row[column]).strip() != "":
                                highlight_color = color
                                break

                # Track if ANY annotation is added to this tag occurrence
                has_annotation = False

                # Add highlight annotation if color determined or comments are selected
                should_add_highlight = (highlight_color is not None) or note_text
                if should_add_highlight:
                    hl = page.add_highlight_annot(rects)

                    # Set highlight color
                    if highlight_color:
                        # Convert hex color to RGB
                        try:
                            r, g, b = _hex_to_rgb01(highlight_color)
                            hl.set_colors(stroke=(r, g, b))
                        except Exception:
                            hl.set_colors(stroke=(1, 1, 0))  # Fallback to yellow
                    elif note_text and enable_default_color:
                        # No color rule matched, but we have comments and default color is enabled
                        try:
                            r, g, b = _hex_to_rgb01(default_highlight_color or "#FFFF00")
                            hl.set_colors(stroke=(r, g, b))
                        except Exception:
                            hl.set_colors(stroke=(1, 1, 0))  # Fallback to yellow
                    elif note_text:
                        # Comments exist but default color disabled - make highlight transparent
                        hl.set_colors(stroke=(1, 1, 1))  # White/invisible highlight
                        hl.set_opacity(0.0)

                    # Add comment to highlight
                    if annotation_type == "highlight_only" and note_text:
                        hl.set_info(content=note_text)

                    hl.update()
                    has_annotation = True

                # Add sticky note if using note_only mode
                if annotation_type == "note_only":
                    r0 = rects[0]
                    note_pos = fitz.Point(r0.x0, r0.y0 - 20)
                    ta = page.add_text_annot(note_pos, note_text, icon="Note")
                    ta.update()
                    has_annotation = True

                # Collect watermark placements if enabled
                if watermark_enabled and watermark_attribute:
                    # Handle multiple attributes (passed as list or single string)
                    attributes = watermark_attribute if isinstance(watermark_attribute, list) else [watermark_attribute]

                    # Build watermark text from multiple attributes (values only, no attribute names)
                    watermark_parts = []
                    for attr in attributes:
                        if attr and attr in df.columns:
                            attr_value = str(row[attr]).strip()
                            if attr_value and attr_value.lower() != "nan" and attr_value != "":
                                watermark_parts.append(attr_value)  # Only the value, not "attr: value"

                    if watermark_parts:
                        try:
                            r0 = rects[0]

                            # Join all attributes with " / " on a single line
                            # Example: [Val1, Val2, Val3, Val4, Val5] → "Val1 / Val2 / Val3 / Val4 / Val5"
                            wm_text = " / ".join(watermark_parts)

                            # Orientation-aware placement relative to the tag box.
                            # Also record desired text rotation (0 = horizontal, 90 = vertical).
                            font_size = 9
                            char_width = font_size * 0.6
                            text_length = len(wm_text) * char_width  # approximate text width in points
                            margin = 6
                            text_height = font_size

                            r = r0  # first rectangle for the tag
                            is_horizontal = (r.width >= r.height)
                            tag_center = fitz.Point((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)

                            if is_horizontal:
                                # dette er vertical tag  i virkeligheden!
                                wm_width = text_length + (margin * 2)
                                wm_x = tag_center.x - (wm_width / 2)
                                wm_y = r.y1 + 3  # slightly below
                                desired_rotation = 270
                            else:
                                # Place to the right of a vertical tag; draw text vertically (bottom-to-top).
                                wm_x = r.x1 - (margin * 3) # a bit to the right
                                # Anchor at the lower end so, after 90° rotation, the text centers on the tag
                                wm_y = tag_center.y - (text_length / 2)
                                desired_rotation = 180

                            watermark_items_by_page[page_num].append({
                                'text': wm_text,
                                'x': wm_x,
                                'y': wm_y,
                                'font_size': font_size,
                                'rotation': desired_rotation
                            })
                            has_annotation = True
                        except Exception as e:
                            print(f"Error collecting watermark for tag '{tag}': {e}")
                            continue

                # Track this tag occurrence as annotated if any annotation was added
                if has_annotation:
                    # Create a unique key for this tag occurrence based on position
                    rect_key = tuple(
                        (round(r.x0, 3), round(r.y0, 3), round(r.x1, 3), round(r.y1, 3))
                        for r in rects
                    )
                    annotated_tags_by_page[page_num].add((tag.upper(), rect_key))

            except Exception as e:
                print(f"Error processing tag '{tag}' on page {page_num}: {e}")
                continue

        if tag_locations:
            found_tags += 1
            processed_tags.add(tag)
            print(f"Found and processed tag: {tag} ({len(tag_locations)} occurrences)")

            # Add to found tags in report
            # Extract unique pages where this tag was found
            pages = sorted(set(page_num for page_num, _, _ in tag_locations))

            # Extract bookmark titles for each page
            bookmarks = []
            if page_bookmark_map:
                for page_num in pages:
                    bookmark = page_bookmark_map.get(page_num, "N/A")
                    bookmarks.append(bookmark)
            else:
                bookmarks = ["N/A"] * len(pages)

            # Build row_data dict with all Excel columns
            row_dict = {'excel_row': excel_row}
            for col in df.columns:
                row_dict[col] = row[col] if pd.notna(row[col]) else ''

            report_data['found'].append({
                'tag': tag,
                'pages': pages,
                'bookmarks': bookmarks,
                'occurrence_count': len(tag_locations),
                'excel_row': excel_row,
                'row_data': row_dict
            })

    # Process duplicate detection
    for tag, excel_rows in tag_excel_rows.items():
        if len(excel_rows) > 1:
            report_data['duplicates'][tag] = {
                'excel_rows': excel_rows,
                'row_data': tag_excel_row_data[tag]
            }

    elapsed_time = time.time() - start_time
    print(f"Annotation processing completed in {elapsed_time:.2f}s")
    print(f"Report: {len(report_data['found'])} found, {len(report_data['not_found'])} not found, {len(report_data['duplicates'])} duplicates, {len(report_data['validation_warnings'])} warnings")

    # Add annotation statistics to report_data
    # This tracks which tag occurrences received annotations (highlights, comments, watermarks)
    report_data['annotated_tags_by_page'] = {
        page_num: len(tags_set) for page_num, tags_set in annotated_tags_by_page.items()
    }

    # Debug: Log annotation counts per page
    for page_num, count in report_data['annotated_tags_by_page'].items():
        print(f"[ANNOTATION STATS] Page {page_num}: {count} tags received annotations (highlights/comments/watermarks)")

    # Compute unmatched PDF tags (tags in PDF but not in Excel)
    # Build set of all normalized Excel tags with delimiter variants
    excel_tags_normalized = set()
    for excel_tag in df[tag_col].dropna().astype(str).str.strip():
        if excel_tag and excel_tag.lower() != 'nan':
            normalized = excel_tag.upper()
            excel_tags_normalized.add(normalized)
            # Add delimiter variants
            if '-' in normalized:
                excel_tags_normalized.add(convert_tag_format(normalized, from_delimiter="-", to_delimiter="."))
            if '.' in normalized:
                excel_tags_normalized.add(convert_tag_format(normalized, from_delimiter=".", to_delimiter="-"))

    # Find tags in tag_index that are NOT in Excel
    unmatched_pdf_tags = []
    seen_tags = set()  # To avoid duplicate entries from tag variants

    for tag_text, locations in tag_index.items():
        # Skip if already processed (variant handling)
        if tag_text in seen_tags:
            continue

        # Check if tag is NOT in Excel
        if tag_text not in excel_tags_normalized:
            # Mark all variants as seen to avoid duplicates
            seen_tags.add(tag_text)
            dash_variant = convert_tag_format(tag_text, from_delimiter=".", to_delimiter="-")
            dot_variant = convert_tag_format(tag_text, from_delimiter="-", to_delimiter=".")
            seen_tags.add(dash_variant)
            seen_tags.add(dot_variant)

            # Also check if variants are in Excel (if so, skip - it was matched)
            if dash_variant in excel_tags_normalized or dot_variant in excel_tags_normalized:
                continue

            # Extract page numbers (0-indexed in locations)
            pages = sorted(set(page_num for page_num, _, _ in locations))
            occurrence_count = len(locations)

            # Get original tag format from first location
            original_tag = locations[0][2] if locations else tag_text

            unmatched_pdf_tags.append({
                'tag': original_tag,
                'pages': pages,  # 0-indexed, will be displayed as 1-indexed in report
                'occurrence_count': occurrence_count
            })

    # Sort by tag name for consistent display
    unmatched_pdf_tags.sort(key=lambda x: x['tag'].upper())

    # Add to report_data
    report_data['unmatched_pdf_tags'] = unmatched_pdf_tags

    print(f"Report: {len(report_data['unmatched_pdf_tags'])} unmatched PDF tags (in PDF but not in Excel)")

    return found_tags, skipped_tags, processed_tags, report_data


def annotate_pdf_with_progress(config: AnnotationConfig) -> tuple:
    """
    Annotate PDF with tags from Excel file with progress tracking.
    Automatically uses streaming mode for large files (>50MB by default).

    Args:
        config: AnnotationConfig instance containing all annotation parameters

    Returns:
        tuple: (processed_tags_set, report_data)
    """
    # Validate that we have at least one PDF path
    if not config.pdf_paths or not config.pdf_paths[0]:
        raise ValueError("No PDF path provided in configuration")

    # For now, use the first PDF path (multi-PDF support can be added later)
    pdf_path = config.pdf_paths[0]

    # Determine if we should use streaming mode
    use_streaming = config.use_streaming
    if use_streaming is None:
        file_size_mb = _get_file_size_mb(pdf_path)
        use_streaming = file_size_mb > STREAMING_THRESHOLD_MB
        if use_streaming:
            print(f"[OPTIMIZATION] Large file detected ({file_size_mb:.1f}MB). Using streaming mode.")

    if use_streaming:
        return _annotate_pdf_streaming(config)
    else:
        return _annotate_pdf_standard(config)


def _annotate_pdf_standard(config: AnnotationConfig) -> tuple:
    """Standard annotation mode - loads entire PDF into memory."""
    # Extract values from config
    pdf_path = config.pdf_paths[0]
    excel_path = config.excel_path
    out_path = config.output_path
    tag_column = config.tag_column
    header_row = config.header_row
    selected_comment_columns = config.comment_columns
    annotation_type = config.annotation_type
    default_highlight_color = config.highlight_color

    # Watermark configuration
    watermark_enabled = config.watermark and config.watermark.enabled
    watermark_attribute = config.watermark.attributes if config.watermark else ""
    watermark_text_color = config.watermark.text_color if config.watermark else "#000000"
    watermark_background_enabled = False  # Not yet in WatermarkConfig

    # Tag matching and filtering
    tag_matching_config = config.tag_matching or TagMatchingConfig.get_default_preset()
    tag_filters = config.filters
    filter_logic = config.filter_logic
    color_rules = config.color_rules
    enable_default_color = config.enable_default_color
    excel_constraint_mode = config.excel_constraint_mode
    excel_constraint_logic = config.excel_constraint_logic

    # Progress tracking
    task_id = config.task_id
    progress_callback = config.progress_callback
    max_tags = config.max_tags
    column_color_pairs = config.column_color_pairs

    def update_progress(progress, status):
        print(f"[CORE DEBUG] update_progress called: progress={progress}%, status='{status}'")
        if progress_callback:
            try:
                progress_callback(task_id, progress, status)
                print(f"[CORE DEBUG] progress_callback executed successfully for task {task_id}")
            except Exception as e:
                print(f"[CORE ERROR] progress_callback failed: {e}")
        else:
            print(f"[CORE WARNING] No progress_callback provided")

    print(f"\n--- Starting annotation process ---")
    print(f"PDF: {pdf_path}")
    print(f"Excel: {excel_path}")
    print(f"Output: {out_path}")
    print(f"Watermark enabled: {watermark_enabled}")
    if watermark_enabled:
        print(f"Watermark attribute: {watermark_attribute}")
        print(f"Watermark text color: {watermark_text_color}")

    # Read Excel with configurable header row
    update_progress(2, "Starting Excel file validation...")
    print(f"Loading Excel file...")
    print(f"Using header row: {header_row}")

    # Support both .xlsx and .xls files for reading
    is_xls = excel_path.lower().endswith('.xls') and not excel_path.lower().endswith('.xlsx')

    update_progress(5, "Reading Excel file...")
    if is_xls:
        # Use xlrd engine for .xls files
        df = pd.read_excel(excel_path, header=header_row-1, engine='xlrd')
    else:
        # Use openpyxl engine for .xlsx files
        df = pd.read_excel(excel_path, header=header_row-1, engine='openpyxl')

    update_progress(8, "Processing Excel data...")
    df = df.dropna(axis=1, how="all")  # Remove empty columns
    # Strip whitespace from column names for consistent matching
    df.columns = [str(col).strip() for col in df.columns]
    print(f"Excel loaded successfully. Found {len(df)} rows.")

    update_progress(10, "Excel file loaded successfully")

    # Use selected tag column or default to column G (index 6)
    if tag_column and tag_column in df.columns:
        tag_col = tag_column
    else:
        tag_col = df.columns[6]  # Default to column G

    tags = df[tag_col].dropna().astype(str).str.strip()
    print(f"Found {len(tags)} tags in column '{tag_col}'.")

    update_progress(12, "Validating PDF file...")
    print(f"Opening PDF file...")

    update_progress(15, "Loading PDF document...")
    doc = fitz.open(pdf_path)

    update_progress(18, "Analyzing PDF structure...")
    print(f"PDF opened successfully. Contains {len(doc)} pages.")

    update_progress(20, "PDF file ready for processing")

    update_progress(22, "Preparing annotation parameters...")
    print(f"Found {len(tags)} tags in column '{tag_col}'.")

    update_progress(25, "Initializing processing pipeline...")

    update_progress(28, "Setting up annotation engine...")

    # PHASE 1: Build comprehensive tag index (30-60% progress)
    def index_progress_callback(progress, status):
        # Map index progress (0-100%) to overall progress (30-60%)
        overall_progress = 30 + int(progress * 0.3)
        update_progress(overall_progress, status)

    update_progress(30, "Building comprehensive tag index...")
    tag_index = build_tag_index(doc, index_progress_callback, pdf_path=pdf_path, config=tag_matching_config)

    # Build page-to-bookmark mapping for report
    update_progress(60, "Extracting PDF bookmarks...")
    page_bookmark_map = build_page_bookmark_map(doc)

    # Build Excel tags set for color rule filtering
    excel_tags_set = set()
    if tag_filters:
        update_progress(61, "Applying tag filters to Excel data...")
        # Iterate over dataframe rows to access full row data for header_column filters
        for idx, row in df.iterrows():
            tag = str(row[tag_col]).strip()
            if not tag or tag.lower() == 'nan':
                continue
            if apply_tag_filters(tag, tag_filters, filter_logic, row_data=row):
                # Add all variants of the tag (normalized and with different delimiters)
                normalized = tag.upper()
                excel_tags_set.add(normalized)
                if '-' in normalized:
                    excel_tags_set.add(convert_tag_format(normalized, from_delimiter="-", to_delimiter="."))
                elif '.' in normalized:
                    excel_tags_set.add(convert_tag_format(normalized, from_delimiter=".", to_delimiter="-"))
    else:
        # Add all variants of all tags
        for tag in tags:
            normalized = tag.upper()
            excel_tags_set.add(normalized)
            if '-' in normalized:
                excel_tags_set.add(convert_tag_format(normalized, from_delimiter="-", to_delimiter="."))
            elif '.' in normalized:
                excel_tags_set.add(convert_tag_format(normalized, from_delimiter=".", to_delimiter="-"))

    # PHASE 1.5: Apply color rules to ALL matching text in PDF (if color rules provided OR default color enabled)
    color_stats = None
    if color_rules or enable_default_color:
        update_progress(62, "Applying color rules to all matching text...")
        color_stats = apply_color_rules_to_all_text(
            doc, tag_index, color_rules, default_highlight_color,
            enable_default_color=enable_default_color,
            excel_tags_set=excel_tags_set,
            excel_constraint_mode=excel_constraint_mode,
            excel_constraint_logic=excel_constraint_logic,
            tag_filters=tag_filters,
            filter_logic=filter_logic,
            page_bookmark_map=page_bookmark_map,
            df=df,
            tag_col=tag_col,
            header_row=header_row
        )
        print(f"Colored {color_stats['colored_tags']} out of {color_stats['total_tags']} tag occurrences based on color rules.")

    # PHASE 2: Process annotations using index (65-90% progress)
    def annotation_progress_callback(progress, status):
        # Map annotation progress (0-100%) to overall progress (65-90%)
        overall_progress = 65 + int(progress * 0.25)
        update_progress(overall_progress, status)

    # Collect watermark placements per page during processing
    watermark_items_by_page = defaultdict(list)

    update_progress(65, "Processing Excel annotations and comments...")
    found_tags, skipped_tags, processed_tags, report_data = process_annotations_from_index(
        doc=doc,
        df=df,
        tag_index=tag_index,
        tag_col=tag_col,
        column_color_pairs=column_color_pairs,
        selected_comment_columns=selected_comment_columns,
        annotation_type=annotation_type,
        watermark_enabled=watermark_enabled,
        watermark_attribute=watermark_attribute,
        watermark_text_color=watermark_text_color,
        max_tags=max_tags,
        update_progress=annotation_progress_callback,
        watermark_items_by_page=watermark_items_by_page,
        default_highlight_color=default_highlight_color,
        header_row=header_row,
        config=tag_matching_config,
        tag_filters=tag_filters,
        filter_logic=filter_logic,
        page_bookmark_map=page_bookmark_map,
        color_rules=color_rules,
        enable_default_color=enable_default_color
    )

    # Add page statistics to report data
    # If color rules were applied, use those stats (includes coloring info)
    # Otherwise, build stats from tag_index (shows all tags found per page)
    if color_stats and 'page_stats' in color_stats:
        report_data['page_stats'] = color_stats['page_stats']
    else:
        # Build page statistics even without color rules
        update_progress(90, "Building page statistics...")
        report_data['page_stats'] = build_page_statistics(
            tag_index,
            page_bookmark_map=page_bookmark_map,
            excel_tags_set=excel_tags_set,
            df=df,
            tag_col=tag_col,
            header_row=header_row
        )

    # Merge annotation statistics from process_annotations_from_index
    # The 'annotated_tags_by_page' contains tags that got highlights, comments, or watermarks from Excel processing
    # We want 'colored_count' to reflect ALL tags with ANY visual marking (color from rules, highlight, comment, or watermark)
    # Note: Some tags may have both color rule highlights AND Excel annotations, so we use max() to avoid double-counting
    if 'annotated_tags_by_page' in report_data and report_data['page_stats']:
        print("[STATS MERGE] Merging annotation statistics into page_stats...")
        annotated_by_page = report_data['annotated_tags_by_page']
        for page_num, annotated_count in annotated_by_page.items():
            if page_num in report_data['page_stats']:
                # Take the maximum because:
                # - color_stats counts tags colored by rules (can include tags NOT in Excel)
                # - annotated_tags_by_page counts tags from Excel with annotations
                # - Some overlap is possible, so max() gives us a better approximation
                # In most cases, annotated_count from Excel processing is the correct value
                # because it tracks actual annotations added
                current_colored = report_data['page_stats'][page_num].get('colored_count', 0)
                new_colored = max(current_colored, annotated_count)
                print(f"[STATS MERGE] Page {page_num}: colored_count {current_colored} -> {new_colored} (annotated: {annotated_count})")
                report_data['page_stats'][page_num]['colored_count'] = new_colored
        # Clean up temporary key
        del report_data['annotated_tags_by_page']

    # Save intermediate annotated PDF (highlights/notes only)
    update_progress(95, "Saving annotated PDF (pre-watermark)...")
    print(f"Annotation (highlights/notes) complete.")
    print(f"Found {found_tags} tags out of {len(tags)} valid tags.")
    print(f"Skipped {skipped_tags} invalid or duplicate tags.")
    tmp_out_path = f"{out_path}.prewatermark.pdf"
    print(f"Saving pre-watermark PDF to {tmp_out_path}...")
    doc.save(tmp_out_path, incremental=False, deflate=True)
    doc.close()
    print(f"Pre-watermark PDF saved successfully.")

    # Apply watermark overlay via ReportLab + PyPDF2 if enabled
    def _create_overlay_page(width, height, items, color_hex, page_rotation=0, background_enabled=False):
        """Create a single-page PDF overlay with watermark items at specified positions.
        Applies per-item rotation and compensates for the page's /Rotate value so text
        appears in the intended orientation after viewer rotation.

        Args:
            width: Page width in points
            height: Page height in points
            items: List of watermark items with text, position, rotation
            color_hex: Text color in hex format
            page_rotation: Page rotation value (0, 90, 180, 270)
            background_enabled: If True, draw white rectangle behind text
        """
        r, g, b = _hex_to_rgb01(color_hex or "#000000")
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(width, height))
        c.setFillColorRGB(r, g, b)

        # Normalize rotation to [0,360)
        try:
            page_rotation = int(page_rotation) % 360
        except Exception:
            page_rotation = 0

        for it in items:
            text = it.get('text', '')
            x = float(it.get('x', 0))
            y_fitz = float(it.get('y', 0))
            font_size = int(it.get('font_size', 9)) or 9
            desired_rotation = int(it.get('rotation', 0)) % 360

            # Convert PyMuPDF (origin top-left) to ReportLab (origin bottom-left)
            # Adjust baseline by font size for better visual alignment
            y_rl = float(height) - (y_fitz + font_size)

            # Compensate for page rotation so final appearance matches intent
            final_rotation = (desired_rotation - page_rotation) % 360

            c.saveState()
            c.setFont("Helvetica", font_size)

            # Draw white background rectangle if enabled
            if background_enabled:
                # Estimate text dimensions
                text_width = c.stringWidth(text, "Helvetica", font_size)
                padding = .5  # padding in points

                # Draw white filled rectangle before text
                c.setFillColorRGB(1, 1, 1)  # white
                c.translate(x, y_rl)
                if final_rotation:
                    c.rotate(final_rotation)
                # Draw rectangle at origin with padding
                c.rect(-padding, -padding,
                       text_width + 2*padding,
                       font_size + 2*padding,
                       fill=1, stroke=0)
                # Restore color for text
                c.setFillColorRGB(r, g, b)
            else:
                # No background, just translate and rotate
                c.translate(x, y_rl)
                if final_rotation:
                    c.rotate(final_rotation)

            # Draw text at local origin after transform
            c.drawString(0, 0, text)
            c.restoreState()

        c.showPage()
        c.save()
        packet.seek(0)
        return packet.getvalue()

    if watermark_enabled and any(len(v) > 0 for v in watermark_items_by_page.values()):
        update_progress(97, "Applying watermark overlays...")
        print("Applying watermark overlays using ReportLab + PyPDF2...")
        reader = PdfReader(tmp_out_path)
        writer = PdfWriter()

        num_pages = len(reader.pages)
        for p in range(num_pages):
            base_page = reader.pages[p]
            # Compute page size (points)
            try:
                width = float(base_page.mediabox.right) - float(base_page.mediabox.left)
                height = float(base_page.mediabox.top) - float(base_page.mediabox.bottom)
            except Exception:
                # Fallback in case of unexpected mediabox values
                width = 595.0  # A4 width in points
                height = 842.0  # A4 height in points

            items = watermark_items_by_page.get(p, [])
            if items:
                # Respect page rotation so overlay text appears correctly oriented
                try:
                    page_rotation = int(base_page.get('/Rotate', 0)) % 360
                except Exception:
                    page_rotation = 0
                overlay_bytes = _create_overlay_page(width, height, items, watermark_text_color, page_rotation, watermark_background_enabled)
                overlay_reader = PdfReader(BytesIO(overlay_bytes))
                overlay_page = overlay_reader.pages[0]
                # Merge overlay at (0,0)
                base_page.merge_page(overlay_page)

            writer.add_page(base_page)

        with open(out_path, "wb") as f_out:
            writer.write(f_out)

        print("Watermark overlay applied and final PDF written.")
        try:
            os.remove(tmp_out_path)
        except Exception:
            pass
    else:
        # No watermarks: move prewatermark PDF to final output
        print("No watermark overlays to apply; finalizing output.")
        try:
            # Prefer atomic replace when possible
            os.replace(tmp_out_path, out_path)
        except Exception:
            # Fallback to copy-then-remove
            import shutil
            shutil.copyfile(tmp_out_path, out_path)
            try:
                os.remove(tmp_out_path)
            except Exception:
                pass

    print(f"PDF saved successfully to {out_path}.")

    # Return the set of found tags for Excel annotation and report data
    return processed_tags, report_data


def _annotate_pdf_streaming(config: AnnotationConfig) -> tuple:
    """Streaming annotation mode - for large PDFs, processes in chunks with memory management."""
    # Extract values from config
    pdf_path = config.pdf_paths[0]
    excel_path = config.excel_path
    out_path = config.output_path
    tag_column = config.tag_column
    header_row = config.header_row
    selected_comment_columns = config.comment_columns
    annotation_type = config.annotation_type
    default_highlight_color = config.highlight_color

    # Watermark configuration
    watermark_enabled = config.watermark and config.watermark.enabled
    watermark_attribute = config.watermark.attributes if config.watermark else ""
    watermark_text_color = config.watermark.text_color if config.watermark else "#000000"
    watermark_background_enabled = False  # Not yet in WatermarkConfig

    # Tag matching and filtering
    tag_matching_config = config.tag_matching or TagMatchingConfig.get_default_preset()
    tag_filters = config.filters
    filter_logic = config.filter_logic
    color_rules = config.color_rules
    enable_default_color = config.enable_default_color
    excel_constraint_mode = config.excel_constraint_mode
    excel_constraint_logic = config.excel_constraint_logic

    # Progress tracking
    task_id = config.task_id
    progress_callback = config.progress_callback
    max_tags = config.max_tags
    column_color_pairs = config.column_color_pairs

    def update_progress(progress, status):
        print(f"[CORE DEBUG STREAMING] update_progress called: progress={progress}%, status='{status}'")
        if progress_callback:
            try:
                progress_callback(task_id, progress, status)
            except Exception as e:
                print(f"[CORE ERROR] progress_callback failed: {e}")

    print(f"\n--- Starting STREAMING annotation process ---")
    print(f"PDF: {pdf_path}")
    print(f"Using streaming mode for large file optimization")

    # Read Excel data
    update_progress(2, "Loading Excel file...")
    # Support both .xlsx and .xls files for reading
    is_xls = excel_path.lower().endswith('.xls') and not excel_path.lower().endswith('.xlsx')

    if is_xls:
        # Use xlrd engine for .xls files
        df = pd.read_excel(excel_path, header=header_row-1, engine='xlrd')
    else:
        # Use openpyxl engine for .xlsx files
        df = pd.read_excel(excel_path, header=header_row-1, engine='openpyxl')

    df = df.dropna(axis=1, how="all")
    # Strip whitespace from column names for consistent matching
    df.columns = [str(col).strip() for col in df.columns]

    if tag_column and tag_column in df.columns:
        tag_col = tag_column
    else:
        tag_col = df.columns[6]

    update_progress(10, "Excel loaded. Building tag index with streaming...")

    # Build tag index using parallel processing (efficient for large files)
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    def index_progress_callback(progress, status):
        overall_progress = 10 + int(progress * 0.4)
        update_progress(overall_progress, f"Streaming index: {status}")

    tag_index = build_tag_index(doc, index_progress_callback, pdf_path=pdf_path, config=tag_matching_config)

    # Build page-to-bookmark mapping for report
    update_progress(50, "Extracting PDF bookmarks...")
    page_bookmark_map = build_page_bookmark_map(doc)

    # Close and reopen document to clear memory
    doc.close()
    gc.collect()
    if hasattr(fitz, 'TOOLS'):
        try:
            fitz.TOOLS.store_shrink(100)
        except:
            pass

    update_progress(52, "Processing annotations in streaming mode...")

    # Reopen for annotation
    doc = fitz.open(pdf_path)
    watermark_items_by_page = defaultdict(list)

    def annotation_progress_callback(progress, status):
        overall_progress = 52 + int(progress * 0.33)
        update_progress(overall_progress, f"Streaming annotations: {status}")

    found_tags, skipped_tags, processed_tags, report_data = process_annotations_from_index(
        doc=doc,
        df=df,
        tag_index=tag_index,
        tag_col=tag_col,
        column_color_pairs=column_color_pairs,
        selected_comment_columns=selected_comment_columns,
        annotation_type=annotation_type,
        watermark_enabled=watermark_enabled,
        watermark_attribute=watermark_attribute,
        watermark_text_color=watermark_text_color,
        max_tags=max_tags,
        update_progress=annotation_progress_callback,
        watermark_items_by_page=watermark_items_by_page,
        default_highlight_color=default_highlight_color,
        header_row=header_row,
        config=tag_matching_config,
        tag_filters=tag_filters,
        filter_logic=filter_logic,
        page_bookmark_map=page_bookmark_map,
        color_rules=color_rules,
        enable_default_color=enable_default_color
    )

    update_progress(85, "Saving annotated PDF (streaming mode)...")

    # Save with compression
    tmp_out_path = f"{out_path}.prewatermark.pdf"
    doc.save(tmp_out_path, incremental=False, deflate=True, garbage=4, clean=True)
    doc.close()

    # Clear memory before watermark phase
    gc.collect()
    if hasattr(fitz, 'TOOLS'):
        try:
            fitz.TOOLS.store_shrink(100)
        except:
            pass

    # Apply watermarks if needed (same as standard mode)
    def _create_overlay_page(width, height, items, color_hex, page_rotation=0, background_enabled=False):
        """Create overlay page with optional background (streaming mode version)."""
        r, g, b = _hex_to_rgb01(color_hex or "#000000")
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(width, height))
        c.setFillColorRGB(r, g, b)

        try:
            page_rotation = int(page_rotation) % 360
        except Exception:
            page_rotation = 0

        for it in items:
            text = it.get('text', '')
            x = float(it.get('x', 0))
            y_fitz = float(it.get('y', 0))
            font_size = int(it.get('font_size', 9)) or 9
            desired_rotation = int(it.get('rotation', 0)) % 360
            y_rl = float(height) - (y_fitz + font_size)
            final_rotation = (desired_rotation - page_rotation) % 360

            c.saveState()
            c.setFont("Helvetica", font_size)

            # Draw white background rectangle if enabled
            if background_enabled:
                # Estimate text dimensions
                text_width = c.stringWidth(text, "Helvetica", font_size)
                padding = 3  # padding in points

                # Draw white filled rectangle before text
                c.setFillColorRGB(1, 1, 1)  # white
                c.translate(x, y_rl)
                if final_rotation:
                    c.rotate(final_rotation)
                # Draw rectangle at origin with padding
                c.rect(-padding, -padding,
                       text_width + 2*padding,
                       font_size + 2*padding,
                       fill=1, stroke=0)
                # Restore color for text
                c.setFillColorRGB(r, g, b)
            else:
                # No background, just translate and rotate
                c.translate(x, y_rl)
                if final_rotation:
                    c.rotate(final_rotation)

            # Draw text at local origin after transform
            c.drawString(0, 0, text)
            c.restoreState()

        c.showPage()
        c.save()
        packet.seek(0)
        return packet.getvalue()

    if watermark_enabled and any(len(v) > 0 for v in watermark_items_by_page.values()):
        update_progress(90, "Applying watermarks (streaming mode)...")
        reader = PdfReader(tmp_out_path)
        writer = PdfWriter()

        num_pages = len(reader.pages)
        for p in range(num_pages):
            base_page = reader.pages[p]

            try:
                width = float(base_page.mediabox.right) - float(base_page.mediabox.left)
                height = float(base_page.mediabox.top) - float(base_page.mediabox.bottom)
            except Exception:
                width = 595.0
                height = 842.0

            items = watermark_items_by_page.get(p, [])
            if items:
                try:
                    page_rotation = int(base_page.get('/Rotate', 0)) % 360
                except Exception:
                    page_rotation = 0

                overlay_bytes = _create_overlay_page(width, height, items, watermark_text_color, page_rotation, watermark_background_enabled)
                overlay_reader = PdfReader(BytesIO(overlay_bytes))
                overlay_page = overlay_reader.pages[0]
                base_page.merge_page(overlay_page)

            writer.add_page(base_page)

            # Memory cleanup every 50 pages in streaming mode
            if (p + 1) % 50 == 0:
                gc.collect()

        with open(out_path, "wb") as f_out:
            writer.write(f_out)

        try:
            os.remove(tmp_out_path)
        except Exception:
            pass
    else:
        try:
            os.replace(tmp_out_path, out_path)
        except Exception:
            import shutil
            shutil.copyfile(tmp_out_path, out_path)
            try:
                os.remove(tmp_out_path)
            except Exception:
                pass

    # Build page statistics if not already included in report_data
    if 'page_stats' not in report_data or not report_data['page_stats']:
        update_progress(96, "Building page statistics...")
        # Build excel_tags_set from filtered tags with all variants
        tags = df[tag_col].dropna().unique().tolist()
        excel_tags_set = set()
        if tag_filters:
            for tag in tags:
                tag_str = str(tag).strip()
                normalized_tag = tag_str.upper()
                if apply_tag_filters(tag_str, tag_filters, filter_logic):
                    # Add all variants of the tag (normalized and with different delimiters)
                    excel_tags_set.add(normalized_tag)
                    if '-' in normalized_tag:
                        excel_tags_set.add(convert_tag_format(normalized_tag, from_delimiter="-", to_delimiter="."))
                    elif '.' in normalized_tag:
                        excel_tags_set.add(convert_tag_format(normalized_tag, from_delimiter=".", to_delimiter="-"))
        else:
            for tag in tags:
                tag_str = str(tag).strip()
                normalized_tag = tag_str.upper()
                # Add all variants of the tag
                excel_tags_set.add(normalized_tag)
                if '-' in normalized_tag:
                    excel_tags_set.add(convert_tag_format(normalized_tag, from_delimiter="-", to_delimiter="."))
                elif '.' in normalized_tag:
                    excel_tags_set.add(convert_tag_format(normalized_tag, from_delimiter=".", to_delimiter="-"))

        report_data['page_stats'] = build_page_statistics(
            tag_index,
            page_bookmark_map=page_bookmark_map,
            excel_tags_set=excel_tags_set,
            df=df,
            tag_col=tag_col,
            header_row=header_row
        )

    # Merge annotation statistics from process_annotations_from_index (same as standard mode)
    if 'annotated_tags_by_page' in report_data and report_data['page_stats']:
        annotated_by_page = report_data['annotated_tags_by_page']
        for page_num, annotated_count in annotated_by_page.items():
            if page_num in report_data['page_stats']:
                current_colored = report_data['page_stats'][page_num].get('colored_count', 0)
                report_data['page_stats'][page_num]['colored_count'] = max(current_colored, annotated_count)
        del report_data['annotated_tags_by_page']

    update_progress(98, "Streaming annotation complete")
    print(f"Streaming mode: PDF saved successfully to {out_path}.")
    print(f"Found {found_tags} tags, skipped {skipped_tags}")

    return processed_tags, report_data
