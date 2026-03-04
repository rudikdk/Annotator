"""
PDF preview generation functionality.

This module handles single-page PDF preview generation with full annotation pipeline
including color rules, watermarks, and comment annotations.
"""

import fitz  # PyMuPDF
import pandas as pd
from collections import defaultdict
from io import BytesIO

from pid_annotator.config import TagMatchingConfig
from pid_annotator.tag_engine import (
    generate_regex_pattern,
    convert_tag_format,
    apply_tag_filters,
    apply_color_rules,
    is_valid_tag,
    _hex_to_rgb01,
)


def annotate_pdf_page_for_preview(
    pdf_path,
    excel_path,
    page_num,
    tag_column=None,
    header_row=6,
    selected_comment_columns=None,
    color_rules=None,
    default_highlight_color="#FFFF00",
    enable_default_color=True,
    excel_constraint_mode=False,
    excel_constraint_logic="AND",
    watermark_enabled=False,
    watermark_attributes=None,
    watermark_text_color="#000000",
    watermark_background_enabled=False,
    tag_matching_config=None,
    tag_filters=None,
    filter_logic="AND",
    annotation_type="highlight_only"
):
    """
    Process ONLY the specified page with full annotation pipeline for preview.
    This function replicates the exact same processing logic as annotate_pdf_with_progress
    but optimized for single-page preview.

    Args:
        pdf_path: Path to the PDF file
        excel_path: Path to the Excel file
        page_num: 0-indexed page number to process
        tag_column: Column name containing the tags
        header_row: Row number containing headers (1-based)
        selected_comment_columns: List of column names to include in comments
        color_rules: List of color rule dictionaries
        default_highlight_color: Default color for unmatched tags
        enable_default_color: Whether to use default color
        excel_constraint_mode: Whether to constrain coloring to Excel tags
        excel_constraint_logic: "AND" or "OR" logic
        watermark_enabled: Whether to enable watermarks
        watermark_attributes: List of column names for watermark text
        watermark_text_color: Hex color for watermark text
        watermark_background_enabled: Whether to add white background to watermarks
        tag_matching_config: TagMatchingConfig instance or dict
        tag_filters: List of filter rules
        filter_logic: "AND" or "OR" for combining filters
        annotation_type: "highlight_only" or "note_only"

    Returns:
        dict: {
            'success': bool,
            'page': PyMuPDF page object with annotations,
            'stats': {
                'total_tags': int,
                'colored_tags': int,
                'comments_added': int,
                'watermarks_added': int
            },
            'message': str
        }
    """
    try:
        # Use default config if not provided
        if tag_matching_config is None:
            config = TagMatchingConfig.get_default_preset()
        else:
            config = TagMatchingConfig.from_dict(tag_matching_config) if isinstance(tag_matching_config, dict) else tag_matching_config

        # Generate tag pattern
        tag_pattern = generate_regex_pattern(config)

        # Load Excel data
        is_xls = excel_path.lower().endswith('.xls') and not excel_path.lower().endswith('.xlsx')
        if is_xls:
            df = pd.read_excel(excel_path, header=header_row-1, engine='xlrd')
        else:
            df = pd.read_excel(excel_path, header=header_row-1, engine='openpyxl')

        df = df.dropna(axis=1, how="all")
        # Strip whitespace from column names for consistent matching
        df.columns = [str(col).strip() for col in df.columns]

        # Use selected tag column or default
        if tag_column and tag_column in df.columns:
            tag_col = tag_column
        else:
            tag_col = df.columns[6] if len(df.columns) > 6 else df.columns[0]

        tags = df[tag_col].dropna().astype(str).str.strip()

        # Build Excel tags set with filters
        excel_tags_set = set()
        if tag_filters:
            for tag in tags:
                if apply_tag_filters(tag, tag_filters, filter_logic):
                    excel_tags_set.add(tag)
        else:
            excel_tags_set = set(tags)

        # Open PDF
        doc = fitz.open(pdf_path)

        # Validate page number
        if page_num < 0 or page_num >= len(doc):
            doc.close()
            return {
                'success': False,
                'message': f'Invalid page number: {page_num + 1}. PDF has {len(doc)} pages.'
            }

        page = doc[page_num]

        # Build tag index for ONLY this page
        page_tag_index = defaultdict(list)

        text = page.get_text()
        matches = tag_pattern.finditer(text)

        for match in matches:
            original_tag = match.group()

            if not is_valid_tag(original_tag, config):
                continue

            rects = page.search_for(original_tag, flags=1)

            if rects:
                normalized_tag = original_tag.upper()
                tag_variants = [
                    normalized_tag,
                    convert_tag_format(normalized_tag, from_delimiter="-", to_delimiter="."),
                    convert_tag_format(normalized_tag, from_delimiter=".", to_delimiter="-")
                ]

                for variant in set(tag_variants):
                    page_tag_index[variant].append((page_num, rects, original_tag))

        tag_index = dict(page_tag_index)

        # Calculate total tag occurrences across all unique tags
        # This represents ALL text strings on the page that match the custom tag matching rules
        total_tag_occurrences = sum(len(locations) for locations in tag_index.values())

        # PHASE 1: Apply color rules to ALL matching text on this page
        color_stats = {'total_tags': total_tag_occurrences, 'colored_tags': 0}
        if color_rules or enable_default_color:
            for tag_text, locations in tag_index.items():

                # Check if tag is in Excel list
                in_excel = tag_text in excel_tags_set

                # Determine color for this tag
                if color_rules:
                    highlight_color, matched_rule_id, conflicts = apply_color_rules(
                        tag_text, None, color_rules, None
                    )
                else:
                    highlight_color = default_highlight_color if enable_default_color else None
                    matched_rule_id = None

                # Determine if this tag should be colored based on constraint mode
                should_color = False
                if not excel_constraint_mode:
                    if highlight_color is not None:
                        should_color = True
                    elif enable_default_color:
                        should_color = True
                        highlight_color = default_highlight_color
                elif excel_constraint_logic == 'AND':
                    if in_excel:
                        if matched_rule_id is not None:
                            should_color = True
                        elif enable_default_color:
                            should_color = True
                            if not highlight_color:
                                highlight_color = default_highlight_color
                elif excel_constraint_logic == 'OR':
                    if highlight_color is not None:
                        should_color = True
                    elif in_excel:
                        should_color = True
                        if not highlight_color and enable_default_color:
                            highlight_color = default_highlight_color
                    elif enable_default_color:
                        should_color = True
                        highlight_color = default_highlight_color

                if not should_color or not highlight_color:
                    continue

                # Apply color to all occurrences
                for pg_num, rects, original_tag in locations:
                    try:
                        hl = page.add_highlight_annot(rects)
                        r, g, b = _hex_to_rgb01(highlight_color)
                        hl.set_colors(stroke=(r, g, b))
                        hl.update()
                        color_stats['colored_tags'] += 1
                    except Exception as e:
                        print(f"[PREVIEW] Error coloring tag {tag_text}: {e}")

        # PHASE 2: Add comment annotations for Excel tags
        comments_added = 0
        watermarks_added = 0
        watermark_items = []

        if selected_comment_columns or watermark_enabled:
            for idx, row in df.iterrows():
                tag = str(row[tag_col]).strip()
                if not tag or tag.lower() == 'nan':
                    continue

                # Check filters
                if tag_filters and not apply_tag_filters(tag, tag_filters, filter_logic, row_data=row):
                    continue

                # Find this tag in the index
                tag_normalized = tag.upper()
                tag_variants = [
                    tag_normalized,
                    convert_tag_format(tag_normalized, from_delimiter="-", to_delimiter="."),
                    convert_tag_format(tag_normalized, from_delimiter=".", to_delimiter="-")
                ]

                locations_for_tag = []
                for variant in tag_variants:
                    if variant in tag_index:
                        locations_for_tag.extend(tag_index[variant])

                if not locations_for_tag:
                    continue

                # Process each location
                for pg_num, rects, original_tag in locations_for_tag:
                    if pg_num != page_num:
                        continue

                    # Add comment annotation
                    if selected_comment_columns and annotation_type != "note_only":
                        comment_parts = [f"Tag: {tag}"]
                        for col in selected_comment_columns:
                            if col in df.columns:
                                val = row[col]
                                if pd.notna(val):
                                    comment_parts.append(f"{col}: {val}")

                        comment_text = "\n".join(comment_parts)

                        try:
                            annot = page.add_text_annot(
                                rects[0].tl,
                                comment_text,
                                icon="Note"
                            )
                            comments_added += 1
                        except Exception as e:
                            print(f"[PREVIEW] Error adding comment for {tag}: {e}")

                    # Collect watermark data
                    if watermark_enabled and watermark_attributes:
                        watermark_parts = []
                        for attr in watermark_attributes:
                            if attr in df.columns:
                                val = row[attr]
                                if pd.notna(val):
                                    watermark_parts.append(str(val))

                        if watermark_parts:
                            watermark_text = " | ".join(watermark_parts)
                            first_rect = rects[0]
                            watermark_items.append({
                                'text': watermark_text,
                                'x': first_rect.x0,
                                'y': first_rect.y0 - 15,
                                'font_size': 8
                            })

        # PHASE 3: Apply watermarks if enabled
        if watermark_enabled and watermark_items:
            try:
                for item in watermark_items:
                    # Add white background if enabled
                    if watermark_background_enabled:
                        text_width = len(item['text']) * item['font_size'] * 0.6
                        bg_rect = fitz.Rect(
                            item['x'], item['y'] - item['font_size'],
                            item['x'] + text_width, item['y'] + 2
                        )
                        page.draw_rect(bg_rect, color=(1, 1, 1), fill=(1, 1, 1))

                    # Add text
                    r, g, b = _hex_to_rgb01(watermark_text_color)
                    page.insert_text(
                        (item['x'], item['y']),
                        item['text'],
                        fontsize=item['font_size'],
                        color=(r, g, b)
                    )
                    watermarks_added += 1
            except Exception as e:
                print(f"[PREVIEW] Error applying watermarks: {e}")

        print(f"[PREVIEW] Preview complete: {color_stats['colored_tags']} colored, {comments_added} comments, {watermarks_added} watermarks")

        # Commit all changes by saving and reloading the page
        # This ensures watermarks (added with insert_text) are visible in the rendered image
        try:
            import io
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            # Store page number before closing
            target_page = page_num
            doc.close()

            # Reopen from buffer
            doc = fitz.open(stream=buffer, filetype="pdf")
            page = doc[target_page]

        except Exception as e:
            print(f"[PREVIEW] Warning: Failed to reload page, watermarks may not be visible: {e}")
            # Continue anyway with original page

        return {
            'success': True,
            'page': page,
            'doc': doc,  # Return doc so caller can close it
            'stats': {
                'total_tags': color_stats['total_tags'],
                'colored_tags': color_stats['colored_tags'],
                'comments_added': comments_added,
                'watermarks_added': watermarks_added
            },
            'message': 'Preview generated successfully'
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f'Error generating preview: {str(e)}'
        }
