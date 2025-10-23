#!/usr/bin/env python3
"""
Core PID annotation functionality without GUI dependencies
- Replaced "stamp" feature with "watermark" implemented via ReportLab + PyPDF2
- Removed background options for the former stamp feature
- Optimized with parallel indexing, memory management, and streaming for large files
"""

import os
import fitz  # PyMuPDF
import pandas as pd
import re
import time
import gc
from collections import defaultdict
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Watermark overlay libs
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter

# Configuration for optimization features
PARALLEL_INDEXING_ENABLED = True
MAX_WORKERS = max(1, (os.cpu_count() or 2) - 1)  # Leave one core free
STREAMING_THRESHOLD_MB = 50  # Enable streaming for files larger than this
MEMORY_CLEANUP_BATCH_SIZE = 100  # Clean memory after processing this many pages
PROGRESS_UPDATE_INTERVAL = 2  # Minimum percent change to trigger progress update


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


def is_valid_tag(tag):
    """Check if a tag has the correct format with delimiters."""
    if tag.lower() == "nan" or tag == "":
        return False
    
    # Use the new parse_tag_format function
    tag_info = parse_tag_format(tag)
    
    # Accept tags with 3 to 5 parts (removed option for 2-part tags)
    return tag_info['valid'] and 3 <= tag_info['count'] <= 5


def _index_page_range(doc_path, page_start, page_end, tag_pattern):
    """
    Index a range of pages from a PDF document (worker function for parallel processing).
    
    Args:
        doc_path: Path to the PDF file
        page_start: Starting page number (inclusive)
        page_end: Ending page number (exclusive)
        tag_pattern: Compiled regex pattern for tag matching
        
    Returns:
        dict: Partial tag index for this page range
    """
    local_index = defaultdict(list)
    
    # Open document in worker thread
    doc = fitz.open(doc_path)
    
    try:
        for page_num in range(page_start, page_end):
            if page_num >= len(doc):
                break
                
            page = doc[page_num]
            text = page.get_text()
            
            # Find all potential tags on this page
            matches = tag_pattern.finditer(text)
            
            for match in matches:
                original_tag = match.group()
                
                # Skip if not a valid tag format
                if not is_valid_tag(original_tag):
                    continue
                
                # Get exact coordinates for this tag occurrence
                rects = page.search_for(original_tag, flags=1)
                
                if rects:  # Only add if we can find the coordinates
                    # Normalize tag for lookup
                    normalized_tag = original_tag.upper()
                    
                    # Store both original format and converted formats
                    tag_variants = [
                        normalized_tag,
                        convert_tag_format(normalized_tag, from_delimiter="-", to_delimiter="."),
                        convert_tag_format(normalized_tag, from_delimiter=".", to_delimiter="-")
                    ]
                    
                    # Add all variants to index
                    for variant in set(tag_variants):
                        local_index[variant].append((page_num, rects, original_tag))
            
            # Memory cleanup after each page
            page = None
        
    finally:
        doc.close()
        # Force garbage collection
        gc.collect()
    
    return dict(local_index)


def build_tag_index(doc, update_progress=None, use_parallel=None, pdf_path=None):
    """
    Build a comprehensive index of all potential tags found in the PDF.
    Supports both sequential and parallel processing modes.
    
    Args:
        doc: PyMuPDF document object
        update_progress: Optional progress callback function
        use_parallel: Override parallel processing (True/False/None=auto)
        pdf_path: Path to PDF file (required for parallel processing)
        
    Returns:
        dict: Index mapping normalized tag strings to their locations
              Format: {tag_normalized: [(page_num, rects, original_tag), ...]}
    """
    print("Building comprehensive tag index...")
    start_time = time.time()
    
    total_pages = len(doc)
    
    # Determine if we should use parallel processing
    if use_parallel is None:
        use_parallel = PARALLEL_INDEXING_ENABLED and total_pages > 20
    
    # Define tag pattern - matches sequences with delimiters
    tag_pattern = re.compile(r'\b[A-Z0-9]+[-\.][A-Z0-9]+(?:[-\.][A-Z0-9]+)*\b', re.IGNORECASE)
    
    if use_parallel and pdf_path and total_pages > 20:
        print(f"Using parallel indexing with {MAX_WORKERS} workers for {total_pages} pages")
        return _build_tag_index_parallel(pdf_path, total_pages, tag_pattern, update_progress)
    else:
        print(f"Using sequential indexing for {total_pages} pages")
        return _build_tag_index_sequential(doc, total_pages, tag_pattern, update_progress)


def _build_tag_index_sequential(doc, total_pages, tag_pattern, update_progress=None):
    """Sequential tag indexing (original implementation)."""
    tag_index = defaultdict(list)
    last_reported_progress = -1
    
    for page_num in range(total_pages):
        # Update progress with throttling
        if update_progress:
            progress = int((page_num / total_pages) * 100) if total_pages else 100
            if progress - last_reported_progress >= PROGRESS_UPDATE_INTERVAL:
                update_progress(progress, f"Indexing page {page_num + 1}/{total_pages}...")
                last_reported_progress = progress
        
        page = doc[page_num]
        text = page.get_text()
        
        # Find all potential tags on this page
        matches = tag_pattern.finditer(text)
        
        for match in matches:
            original_tag = match.group()
            
            if not is_valid_tag(original_tag):
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
                    tag_index[variant].append((page_num, rects, original_tag))
        
        # Memory cleanup every MEMORY_CLEANUP_BATCH_SIZE pages
        if (page_num + 1) % MEMORY_CLEANUP_BATCH_SIZE == 0:
            page = None
            gc.collect()
            if hasattr(fitz, 'TOOLS'):
                try:
                    fitz.TOOLS.store_shrink(100)
                except:
                    pass
    
    total_tags = sum(len(locations) for locations in tag_index.values())
    print(f"Sequential indexing complete. Found {total_tags} tag instances across {len(tag_index)} unique tags.")
    return dict(tag_index)


def _build_tag_index_parallel(pdf_path, total_pages, tag_pattern, update_progress=None):
    """Parallel tag indexing using ThreadPoolExecutor."""
    tag_index = defaultdict(list)
    index_lock = Lock()
    completed_pages = [0]
    last_reported_progress = [-1]
    
    # Calculate chunk size (distribute pages across workers)
    chunk_size = max(10, total_pages // (MAX_WORKERS * 2))
    chunks = [(i, min(i + chunk_size, total_pages)) for i in range(0, total_pages, chunk_size)]
    
    def process_chunk(chunk_info):
        """Process a chunk and update progress."""
        start_page, end_page = chunk_info
        local_result = _index_page_range(pdf_path, start_page, end_page, tag_pattern)
        
        # Update global progress
        with index_lock:
            completed_pages[0] += (end_page - start_page)
            if update_progress:
                progress = int((completed_pages[0] / total_pages) * 100)
                if progress - last_reported_progress[0] >= PROGRESS_UPDATE_INTERVAL:
                    update_progress(progress, f"Indexed {completed_pages[0]}/{total_pages} pages (parallel)...")
                    last_reported_progress[0] = progress
        
        return local_result
    
    # Execute parallel processing
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
        
        for future in as_completed(futures):
            try:
                local_index = future.result()
                
                # Merge local results into global index
                with index_lock:
                    for tag_variant, locations in local_index.items():
                        tag_index[tag_variant].extend(locations)
                        
            except Exception as e:
                print(f"Error in parallel indexing chunk: {e}")
    
    total_tags = sum(len(locations) for locations in tag_index.values())
    print(f"Parallel indexing complete. Found {total_tags} tag instances across {len(tag_index)} unique tags.")
    return dict(tag_index)


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
    default_highlight_color="#FFFF00"
):
    """
    Process annotations using the pre-built tag index for optimal performance.
    
    Args:
        doc: PyMuPDF document object
        df: DataFrame with Excel data
        tag_index: Pre-built tag index from build_tag_index()
        tag_col: Column name containing tags
        column_color_pairs: list of (column, color)
        selected_comment_columns: which columns to include in notes
        annotation_type: "highlight_only" or "note_only"
        watermark_enabled: enable watermark placement
        watermark_attribute: Excel column to render as watermark text
        watermark_text_color: color for watermark text (hex)
        max_tags: optional limit
        update_progress: progress callback
        watermark_items_by_page: dict(page_num -> [ {text,x,y,font_size} ])
        default_highlight_color: hex color used when highlighting due to comments (no column rule)
        
    Returns:
        tuple: (found_tags, skipped_tags, processed_tags_set)
    """
    print("Processing annotations using tag index...")
    start_time = time.time()
    
    if watermark_items_by_page is None:
        watermark_items_by_page = defaultdict(list)
    
    found_tags = 0
    skipped_tags = 0
    processed_tags = set()
    
    # Limit processing if max_tags specified
    total_to_process = min(max_tags, len(df)) if max_tags and max_tags > 0 else len(df)
    
    for i, (_, row) in enumerate(df.iterrows()):
        if max_tags and i >= max_tags:
            print(f"Reached maximum number of tags ({max_tags}). Stopping processing.")
            break
            
        if update_progress:
            progress = int((i / total_to_process) * 100) if total_to_process else 100
            update_progress(progress, f"Processing tag {i+1}/{total_to_process}...")
        
        tag = str(row[tag_col]).strip()
        
        # Skip empty or invalid tags
        if not tag or not is_valid_tag(tag):
            if tag:  # Only log if tag exists but is invalid
                print(f"Skipping invalid tag: {tag}")
                skipped_tags += 1
            continue
            
        # Skip already processed tags
        if tag in processed_tags:
            print(f"Skipping duplicate tag: {tag}")
            skipped_tags += 1
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
        
        if not tag_locations:
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
                # Check if we should add highlighting based on color rules
                has_color_rule_match = False
                if column_color_pairs:
                    for column, color in column_color_pairs:
                        if column and column in df.columns:
                            if pd.notna(row[column]) and str(row[column]).strip() != "":
                                has_color_rule_match = True
                                break

                # Add highlight annotation if color rule matches or comments are selected
                should_add_highlight = has_color_rule_match or note_text
                if should_add_highlight:
                    hl = page.add_highlight_annot(rects)

                    # Set highlight color
                    if has_color_rule_match:
                        if column_color_pairs:
                            for column, color in column_color_pairs:
                                if column and column in df.columns:
                                    if pd.notna(row[column]) and str(row[column]).strip() != "":
                                        if color and color.startswith('#'):
                                            try:
                                                color_hex = color.lstrip('#')
                                                r = int(color_hex[0:2], 16) / 255.0
                                                g = int(color_hex[2:4], 16) / 255.0
                                                b = int(color_hex[4:6], 16) / 255.0
                                                hl.set_colors(stroke=(r, g, b))
                                            except:
                                                hl.set_colors(stroke=(1, 1, 0))  # Fallback to yellow
                                        else:
                                            # Handle predefined colors
                                            color_map = {
                                                "blue": (0, 0, 1), "green": (0, 1, 0), "red": (1, 0, 0),
                                                "purple": (0.5, 0, 0.5), "orange": (1, 0.65, 0)
                                            }
                                            hl.set_colors(stroke=color_map.get(color, (1, 1, 0)))
                                        break
                    else:
                        try:
                            r, g, b = _hex_to_rgb01(default_highlight_color or "#FFFF00")
                            hl.set_colors(stroke=(r, g, b))
                        except Exception:
                            hl.set_colors(stroke=(1, 1, 0))  # Fallback to yellow

                    # Add comment to highlight
                    if annotation_type == "highlight_only" and note_text:
                        hl.set_info(content=note_text)

                    hl.update()
                
                # Add sticky note if using note_only mode
                if annotation_type == "note_only":
                    r0 = rects[0]
                    note_pos = fitz.Point(r0.x0, r0.y0 - 20)
                    ta = page.add_text_annot(note_pos, note_text, icon="Note")
                    ta.update()
                
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
                            
                            # Group attributes in sets of 3, join with " / ", then join groups with "\n"
                            # Example: [Val1, Val2, Val3, Val4, Val5] → "Val1 / Val2 / Val3\nVal4 / Val5"
                            grouped_lines = []
                            for i in range(0, len(watermark_parts), 3):
                                group = watermark_parts[i:i+3]
                                grouped_lines.append(" / ".join(group))
                            wm_text = "\n".join(grouped_lines)
                            
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
                        except Exception as e:
                            print(f"Error collecting watermark for tag '{tag}': {e}")
                            continue
                            
            except Exception as e:
                print(f"Error processing tag '{tag}' on page {page_num}: {e}")
                continue
        
        if tag_locations:
            found_tags += 1
            processed_tags.add(tag)
            print(f"Found and processed tag: {tag} ({len(tag_locations)} occurrences)")
    
    elapsed_time = time.time() - start_time
    print(f"Annotation processing completed in {elapsed_time:.2f}s")
    
    return found_tags, skipped_tags, processed_tags


def reload_excel_columns(excel_path, header_row):
    """
    Reload Excel columns with a new header row
    
    Args:
        excel_path: Path to the Excel file
        header_row: Row number containing headers (1-based)
        
    Returns:
        dict: Contains 'success', 'columns', 'message', and 'default_tag_column'
    """
    try:
        if header_row < 1:
            return {
                'success': False,
                'columns': [],
                'message': 'Header row must be 1 or greater',
                'default_tag_column': None
            }
        
        # Determine engine based on file extension
        engine = 'openpyxl' if excel_path.lower().endswith('.xlsx') else 'xlrd'
        
        # Load Excel file with new header row
        df = pd.read_excel(excel_path, header=header_row-1, engine=engine)  # Convert to 0-based indexing
        df = df.dropna(axis=1, how="all")  # Remove empty columns
        
        columns = list(df.columns)
        
        # Set default tag column to column G (index 6) if it exists, otherwise first column
        default_tag_column = None
        if len(columns) > 6:
            default_tag_column = columns[6]  # Column G
        elif columns:
            default_tag_column = columns[0]  # First available column
        
        message = f"Successfully loaded {len(columns)} columns from header row {header_row}"
        if header_row != 6:
            message += f" (changed from default row 6)"
        
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


def _get_file_size_mb(filepath):
    """Get file size in megabytes."""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except:
        return 0


def annotate_pdf_with_progress(
    pdf_path,
    excel_path,
    out_path,
    column_color_pairs=None,
    max_tags=None,
    tag_column=None,
    header_row=6,
    selected_comment_columns=None,
    task_id=None,
    progress_callback=None,
    annotation_type="highlight_only",
    watermark_enabled=False,
    watermark_attribute="",
    watermark_text_color="#000000",
    default_highlight_color="#FFFF00",
    use_streaming=None
):
    """
    Annotate PDF with tags from Excel file with progress tracking.
    Automatically uses streaming mode for large files (>50MB by default).

    Args:
        pdf_path: Path to the PDF file
        excel_path: Path to the Excel file
        out_path: Path for the output annotated PDF
        column_color_pairs: List of (column, color) tuples for conditional highlighting
        max_tags: Maximum number of tags to process (for testing)
        tag_column: Column name containing the tags
        header_row: Row number containing headers (1-based, default is 6)
        selected_comment_columns: List of column names to include in comments (None = all columns)
        task_id: Task ID for progress tracking
        progress_callback: Function to call for progress updates
        annotation_type: Type of annotation to use ("highlight_only" or "note_only")
        watermark_enabled: Whether to enable watermark feature
        watermark_attribute: Column name to use for watermark text
        watermark_text_color: Text color for watermark (hex format)
        use_streaming: Override streaming mode (True/False/None=auto)
    """
    # Determine if we should use streaming mode
    if use_streaming is None:
        file_size_mb = _get_file_size_mb(pdf_path)
        use_streaming = file_size_mb > STREAMING_THRESHOLD_MB
        if use_streaming:
            print(f"[OPTIMIZATION] Large file detected ({file_size_mb:.1f}MB). Using streaming mode.")
    
    if use_streaming:
        return _annotate_pdf_streaming(
            pdf_path, excel_path, out_path, column_color_pairs, max_tags,
            tag_column, header_row, selected_comment_columns, task_id,
            progress_callback, annotation_type, watermark_enabled,
            watermark_attribute, watermark_text_color, default_highlight_color
        )
    else:
        return _annotate_pdf_standard(
            pdf_path, excel_path, out_path, column_color_pairs, max_tags,
            tag_column, header_row, selected_comment_columns, task_id,
            progress_callback, annotation_type, watermark_enabled,
            watermark_attribute, watermark_text_color, default_highlight_color
        )


def _annotate_pdf_standard(
    pdf_path, excel_path, out_path, column_color_pairs, max_tags,
    tag_column, header_row, selected_comment_columns, task_id,
    progress_callback, annotation_type, watermark_enabled,
    watermark_attribute, watermark_text_color, default_highlight_color
):
    """Standard annotation mode - loads entire PDF into memory."""
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

    # Determine engine based on file extension
    engine = 'openpyxl' if excel_path.lower().endswith('.xlsx') else 'xlrd'

    update_progress(5, "Reading Excel file...")
    df = pd.read_excel(excel_path, header=header_row-1, engine=engine)  # Convert to 0-based indexing

    update_progress(8, "Processing Excel data...")
    df = df.dropna(axis=1, how="all")  # Remove empty columns
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
    tag_index = build_tag_index(doc, index_progress_callback, pdf_path=pdf_path)
    
    # PHASE 2: Process annotations using index (60-90% progress)
    def annotation_progress_callback(progress, status):
        # Map annotation progress (0-100%) to overall progress (60-90%)
        overall_progress = 60 + int(progress * 0.3)
        update_progress(overall_progress, status)
    
    # Collect watermark placements per page during processing
    watermark_items_by_page = defaultdict(list)

    update_progress(60, "Processing annotations using optimized index...")
    found_tags, skipped_tags, processed_tags = process_annotations_from_index(
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
        default_highlight_color=default_highlight_color
    )

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
    def _create_overlay_page(width, height, items, color_hex, page_rotation=0):
        """Create a single-page PDF overlay with watermark items at specified positions.
        Applies per-item rotation and compensates for the page's /Rotate value so text
        appears in the intended orientation after viewer rotation."""
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
            c.translate(x, y_rl)
            if final_rotation:
                c.rotate(final_rotation)
            # Draw at local origin after transform
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
                overlay_bytes = _create_overlay_page(width, height, items, watermark_text_color, page_rotation)
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

    # Return the set of found tags for Excel annotation
    return processed_tags


def _annotate_pdf_streaming(
    pdf_path, excel_path, out_path, column_color_pairs, max_tags,
    tag_column, header_row, selected_comment_columns, task_id,
    progress_callback, annotation_type, watermark_enabled,
    watermark_attribute, watermark_text_color, default_highlight_color
):
    """Streaming annotation mode - for large PDFs, processes in chunks with memory management."""
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
    engine = 'openpyxl' if excel_path.lower().endswith('.xlsx') else 'xlrd'
    df = pd.read_excel(excel_path, header=header_row-1, engine=engine)
    df = df.dropna(axis=1, how="all")
    
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
    
    tag_index = build_tag_index(doc, index_progress_callback, pdf_path=pdf_path)
    
    # Close and reopen document to clear memory
    doc.close()
    gc.collect()
    if hasattr(fitz, 'TOOLS'):
        try:
            fitz.TOOLS.store_shrink(100)
        except:
            pass
    
    update_progress(50, "Processing annotations in streaming mode...")
    
    # Reopen for annotation
    doc = fitz.open(pdf_path)
    watermark_items_by_page = defaultdict(list)
    
    def annotation_progress_callback(progress, status):
        overall_progress = 50 + int(progress * 0.35)
        update_progress(overall_progress, f"Streaming annotations: {status}")
    
    found_tags, skipped_tags, processed_tags = process_annotations_from_index(
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
        default_highlight_color=default_highlight_color
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
    def _create_overlay_page(width, height, items, color_hex, page_rotation=0):
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
            c.translate(x, y_rl)
            if final_rotation:
                c.rotate(final_rotation)
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
                
                overlay_bytes = _create_overlay_page(width, height, items, watermark_text_color, page_rotation)
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
    
    update_progress(98, "Streaming annotation complete")
    print(f"Streaming mode: PDF saved successfully to {out_path}.")
    print(f"Found {found_tags} tags, skipped {skipped_tags}")
    
    return processed_tags


def annotate_excel_with_found_tags(excel_path, out_path, found_tags_set, tag_column, header_row=6):
    """
    Annotate Excel file by highlighting rows where tags were found in PDF

    Args:
        excel_path: Path to the original Excel file
        out_path: Path for the output annotated Excel file
        found_tags_set: Set of tag strings that were found in the PDF
        tag_column: Column name containing the tags
        header_row: Row number containing headers (1-based, default is 6)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Annotating Excel file: {excel_path}")
        print(f"Found {len(found_tags_set)} tags in PDF")

        # Load Excel file with openpyxl
        workbook = load_workbook(excel_path)
        worksheet = workbook.active

        # Determine engine based on file extension
        engine = 'openpyxl' if excel_path.lower().endswith('.xlsx') else 'xlrd'

        # Load data with pandas to get the tag column index
        df = pd.read_excel(excel_path, header=header_row-1, engine=engine)
        df = df.dropna(axis=1, how="all")  # Remove empty columns

        # Find the tag column index
        tag_col_index = None
        if tag_column in df.columns:
            tag_col_index = df.columns.get_loc(tag_column)
        else:
            # Default to column G (index 6)
            tag_col_index = 6 if len(df.columns) > 6 else 0

        # Define light green fill
        light_green_fill = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")

        # Track how many rows were highlighted
        highlighted_count = 0

        # Iterate through rows and highlight those with found tags
        for row_idx, row in df.iterrows():
            # Convert 0-based index to 1-based Excel row
            excel_row = row_idx + header_row + 1  # +1 for header row, +1 because Excel is 1-based

            tag_value = str(row.iloc[tag_col_index]).strip()

            # Check if this tag was found in the PDF
            if tag_value in found_tags_set:
                # Highlight the entire row
                for col_idx in range(1, len(df.columns) + 1):  # Excel columns are 1-based
                    cell = worksheet.cell(row=excel_row, column=col_idx)
                    cell.fill = light_green_fill

                highlighted_count += 1
                print(f"Highlighted row {excel_row} (tag: {tag_value})")

        # Save the annotated Excel file
        workbook.save(out_path)
        print(f"Excel annotation complete. Highlighted {highlighted_count} rows in {out_path}")

        return True

    except Exception as e:
        print(f"Error annotating Excel file: {str(e)}")
        return False


def annotate_pdf(
    pdf_path,
    excel_path,
    out_path,
    column_color_pairs=None,
    max_tags=None,
    tag_column=None,
    header_row=6,
    selected_comment_columns=None,
    annotation_type="highlight_only",
    watermark_enabled=False,
    watermark_attribute="",
    watermark_text_color="#000000",
    default_highlight_color="#FFFF00"
):
    """
    Annotate PDF with tags from Excel file (original function for backward compatibility)
    """
    return annotate_pdf_with_progress(
        pdf_path,
        excel_path,
        out_path,
        column_color_pairs,
        max_tags,
        tag_column,
        header_row,
        selected_comment_columns,
        None,
        None,
        annotation_type,
        watermark_enabled,
        watermark_attribute,
        watermark_text_color,
        default_highlight_color
    )
