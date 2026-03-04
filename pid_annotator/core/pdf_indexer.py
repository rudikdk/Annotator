#!/usr/bin/env python3
"""
PDF Tag Indexing Module

Builds comprehensive indexes of tags found in PDF documents.
Supports both sequential and parallel processing modes for optimal performance.
"""

import fitz  # PyMuPDF
import gc
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from pid_annotator.config import (
    TagMatchingConfig,
    PARALLEL_INDEXING_ENABLED,
    MAX_WORKERS,
    MEMORY_CLEANUP_BATCH_SIZE,
    PROGRESS_UPDATE_INTERVAL
)
from pid_annotator.tag_engine import (
    generate_regex_pattern,
    convert_tag_format,
    is_valid_tag
)


def build_tag_index(doc, update_progress=None, use_parallel=None, pdf_path=None, config=None):
    """
    Build a comprehensive index of all potential tags found in the PDF.
    Supports both sequential and parallel processing modes.

    Args:
        doc: PyMuPDF document object
        update_progress: Optional progress callback function
        use_parallel: Override parallel processing (True/False/None=auto)
        pdf_path: Path to PDF file (required for parallel processing)
        config: TagMatchingConfig instance (uses default if not provided)

    Returns:
        dict: Index mapping normalized tag strings to their locations
              Format: {tag_normalized: [(page_num, rects, original_tag), ...]}
    """
    start_time = time.time()

    # Use default config if not provided
    if config is None:
        config = TagMatchingConfig.get_default_preset()

    total_pages = len(doc)

    # Determine if we should use parallel processing
    if use_parallel is None:
        use_parallel = PARALLEL_INDEXING_ENABLED and total_pages > 20

    # Generate tag pattern from config
    tag_pattern = generate_regex_pattern(config)

    if use_parallel and pdf_path and total_pages > 20:
        return _build_tag_index_parallel(pdf_path, total_pages, tag_pattern, update_progress, config)
    else:
        return _build_tag_index_sequential(doc, total_pages, tag_pattern, update_progress, config)


def _build_tag_index_sequential(doc, total_pages, tag_pattern, update_progress=None, config=None):
    """Sequential tag indexing (original implementation)."""
    tag_index = defaultdict(list)
    last_reported_progress = -1

    # Use default config if not provided
    if config is None:
        config = TagMatchingConfig.get_default_preset()

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


def _build_tag_index_parallel(pdf_path, total_pages, tag_pattern, update_progress=None, config=None):
    """Parallel tag indexing using ThreadPoolExecutor."""
    tag_index = defaultdict(list)
    index_lock = Lock()
    completed_pages = [0]
    last_reported_progress = [-1]

    # Use default config if not provided
    if config is None:
        config = TagMatchingConfig.get_default_preset()

    # Calculate chunk size (distribute pages across workers)
    chunk_size = max(10, total_pages // (MAX_WORKERS * 2))
    chunks = [(i, min(i + chunk_size, total_pages)) for i in range(0, total_pages, chunk_size)]

    def process_chunk(chunk_info):
        """Process a chunk and update progress."""
        start_page, end_page = chunk_info
        local_result = _index_page_range(pdf_path, start_page, end_page, tag_pattern, config)

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


def _index_page_range(doc_path, page_start, page_end, tag_pattern, config=None):
    """
    Index a range of pages from a PDF document (worker function for parallel processing).

    Args:
        doc_path: Path to the PDF file
        page_start: Starting page number (inclusive)
        page_end: Ending page number (exclusive)
        tag_pattern: Compiled regex pattern for tag matching
        config: TagMatchingConfig instance

    Returns:
        dict: Partial tag index for this page range
    """
    local_index = defaultdict(list)

    # Use default config if not provided
    if config is None:
        config = TagMatchingConfig.get_default_preset()

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
                if not is_valid_tag(original_tag, config):
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


def build_page_statistics(tag_index, page_bookmark_map=None, excel_tags_set=None, df=None, tag_col=None, header_row=6):
    """
    Build page-level statistics for all tags in the tag index.
    This shows how many tags were found per page, regardless of coloring.

    Args:
        tag_index: Pre-built tag index from build_tag_index()
        page_bookmark_map: dict mapping page numbers to bookmark titles (optional)
        excel_tags_set: Set of tags from Excel to mark as "colored" (optional)
        df: DataFrame with Excel data (optional, for including row_data)
        tag_col: Column name containing tags in Excel (optional)
        header_row: Excel header row number (1-based) for row number tracking (default: 6)

    Returns:
        dict: Page statistics {page_num: {'colored_count': X, 'total_count': Y, 'bookmark': 'Title'}}
    """
    page_stats = {}
    seen_occurrences = set()

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

    # Build mapping from tag to Excel row data if df is provided
    tag_to_row_data = {}
    if df is not None and tag_col is not None:
        import pandas as pd
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
        # Check if tag is in Excel list (for "colored" count)
        in_excel = bool(excel_tags_set) and tag_text in excel_tags_set

        # Track page-level statistics for all tags
        for page_num, rects, original_tag in locations:
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

            occurrence_key = _make_occurrence_key(page_num, rects, original_tag)
            if occurrence_key in seen_occurrences:
                continue

            seen_occurrences.add(occurrence_key)

            # Increment total count for this page
            page_stats[page_num]['total_count'] += 1

            # Increment colored count if tag is in Excel
            if in_excel:
                page_stats[page_num]['colored_count'] += 1

            # Determine coloring reason
            if in_excel:
                coloring_reason = "Tag found in Excel list"
            else:
                coloring_reason = "Tag not in Excel list"

            # Create tag detail entry
            tag_detail = {
                'tag': tag_text,
                'found_text': original_tag,
                'in_excel': bool(in_excel),
                'colored': bool(in_excel),
                'coloring_reason': coloring_reason
            }

            # Add row_data if tag is in Excel and we have the data
            if in_excel and tag_text in tag_to_row_data:
                tag_detail['row_data'] = tag_to_row_data[tag_text]

            page_stats[page_num]['tag_details'].append(tag_detail)

    return page_stats


def build_page_bookmark_map(doc):
    """
    Build a mapping of page numbers to their corresponding bookmark titles.

    Args:
        doc: PyMuPDF document object

    Returns:
        dict: Mapping of page numbers (0-based) to bookmark titles
              Format: {page_num: bookmark_title}
    """
    page_bookmark_map = {}

    try:
        # Get table of contents (bookmarks/outline)
        # Returns list of [level, title, page] where page is 1-based
        toc = doc.get_toc()

        if not toc:
            return page_bookmark_map

        # Build map: assign each bookmark to its page and all following pages
        # until the next bookmark of same or higher level
        for i, (level, title, page_1based) in enumerate(toc):
            # Convert to 0-based page number
            page_num = page_1based - 1

            # Find the end page for this bookmark
            # (page before next bookmark of same or higher level)
            end_page = len(doc) - 1  # Default to last page

            for j in range(i + 1, len(toc)):
                next_level, _, next_page_1based = toc[j]
                if next_level <= level:
                    end_page = next_page_1based - 2  # Page before next bookmark (0-based)
                    break

            # Assign this bookmark title to all pages in its range
            # But prefer deeper level bookmarks (child over parent)
            for p in range(page_num, min(end_page + 1, len(doc))):
                # Only update if no bookmark assigned yet, or current is deeper level
                if p not in page_bookmark_map:
                    page_bookmark_map[p] = title
                else:
                    # Keep the most specific (deepest) bookmark
                    # We process in order, so later deeper bookmarks will override
                    current_bookmark_idx = next(
                        (idx for idx, (_, ttl, _) in enumerate(toc)
                         if ttl == page_bookmark_map[p]),
                        -1
                    )
                    if current_bookmark_idx >= 0:
                        current_level = toc[current_bookmark_idx][0]
                        if level > current_level:
                            page_bookmark_map[p] = title

    except Exception as e:
        print(f"[WARNING] Error building page-bookmark map: {e}")

    return page_bookmark_map
