"""
Main PDF processing route handler
"""
import os
import uuid
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, session, current_app
from flask_socketio import SocketIO
import pandas as pd

from pid_annotator.analysis import reload_excel_columns
from pid_annotator.core.pdf_annotator import annotate_pdf_with_progress
from pid_annotator.core.excel_processor import annotate_excel_with_found_tags
from pid_annotator.tag_engine.filters import apply_tag_filters
from pid_annotator.config import AnnotationConfig, WatermarkConfig, TagMatchingConfig
from pid_annotator.session.manager import try_attach_existing_files_to_session as _try_attach

# Create blueprint
processing_bp = Blueprint('processing', __name__)

# Progress tracking
progress_data = {}
# Thread-safe storage for output files
output_files_data = {}


def make_progress_callback(socketio_instance):
    """
    Factory function to create a progress callback with socketio instance.
    This avoids Flask context issues in background threads.
    """
    def progress_callback(task_id, progress, status):
        """Callback function for progress updates"""
        progress_data[task_id] = {
            'progress': progress,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }

        # Emit progress update via SocketIO
        try:
            if socketio_instance:
                socketio_instance.emit('progress_update', {
                    'task_id': task_id,
                    'progress': progress,
                    'status': status
                }, namespace='/')
                # Yield to the Socket.IO server so progress updates flush promptly under eventlet/gevent
                try:
                    socketio_instance.sleep(0)
                except Exception:
                    pass
        except Exception as e:
            print(f"[APP ERROR] Failed to emit progress update: {e}")

        # Also flush stdout to ensure console output appears immediately
        import sys
        sys.stdout.flush()

    return progress_callback


def format_date_ddmmmyyyy(dt):
    """Format date as DDMMMYYYY (e.g., 01JAN2025)"""
    return dt.strftime('%d%b%Y').upper()


@processing_bp.route('/process', methods=['POST'])
def process_files():
    """Process the PDF annotation"""
    try:
        # Get form data
        data = request.get_json()

        # Get selected PDFs and Excel from request
        selected_pdfs = data.get('selected_pdfs', [])
        selected_excel = data.get('selected_excel', None)

        # Validate Excel file - use selected_excel from frontend if provided
        if selected_excel:
            excel_file = selected_excel
        else:
            # Fallback to session for backward compatibility
            excel_file = session.get('excel_file')
            if not excel_file:
                _try_attach(current_app.config['UPLOAD_FOLDER'], reload_excel_columns)
                excel_file = session.get('excel_file')

        if not excel_file:
            return jsonify({'success': False, 'message': 'Please select an Excel/CSV file'})

        # Validate that selected Excel file exists on disk
        uploads_dir = Path(current_app.config['UPLOAD_FOLDER'])
        excel_path_obj = uploads_dir / excel_file
        if not excel_path_obj.exists():
            return jsonify({'success': False, 'message': f'Selected Excel file not found: {excel_file}'})

        # Convert to string for compatibility with processing functions
        excel_path = str(excel_path_obj)

        # Use selected PDFs directly from request (they come from workspace which lists actual files)
        if selected_pdfs:
            pdf_files = selected_pdfs

            # Validate that selected files actually exist on disk
            uploads_dir = Path(current_app.config['UPLOAD_FOLDER'])
            valid_pdf_files = []
            for pdf_file in pdf_files:
                pdf_path = uploads_dir / pdf_file
                if pdf_path.exists():
                    valid_pdf_files.append(pdf_file)
                else:
                    print(f"[APP WARNING] Selected PDF not found: {pdf_file}")

            if not valid_pdf_files:
                return jsonify({'success': False, 'message': 'None of the selected PDF files exist on disk'})

            pdf_files = valid_pdf_files
        else:
            # Fallback: use PDFs from session (backward compatibility)
            pdf_files = session.get('pdf_files', [])
            if not pdf_files:
                _try_attach(current_app.config['UPLOAD_FOLDER'], reload_excel_columns)
                pdf_files = session.get('pdf_files', [])
            if not pdf_files:
                return jsonify({'success': False, 'message': 'No PDF files selected'})

        # Get file paths (excel_path already set during validation above)
        pdf_paths = [os.path.join(current_app.config['UPLOAD_FOLDER'], pdf_file) for pdf_file in pdf_files]

        # Get original PDF names for clean output naming (matching the selected PDFs)
        all_original_names = session.get('original_pdf_names', [])
        all_session_pdfs = session.get('pdf_files', [])
        original_pdf_names = []
        for pdf_file in pdf_files:
            try:
                idx = all_session_pdfs.index(pdf_file)
                if idx < len(all_original_names):
                    original_pdf_names.append(all_original_names[idx])
                else:
                    # Fallback: use filename without session ID
                    session_id = session.get('session_id', 'default')
                    original_pdf_names.append(pdf_file[len(f"{session_id}_"):] if pdf_file.startswith(f"{session_id}_") else pdf_file)
            except ValueError:
                # Fallback
                session_id = session.get('session_id', 'default')
                original_pdf_names.append(pdf_file[len(f"{session_id}_"):] if pdf_file.startswith(f"{session_id}_") else pdf_file)

        # Get processing parameters
        header_row = data.get('header_row', 6)
        tag_column = data.get('tag_column', session.get('default_tag_column'))
        selected_comment_columns = data.get('comment_columns', None)
        max_tags = data.get('max_tags', None)  # For test runs
        is_test = data.get('is_test', False)  # Flag to indicate test run
        annotate_excel = data.get('annotate_excel', False)  # New parameter for Excel annotation

        # Disable Excel annotation for .xls files (read-only support for .xls)
        is_xls_file = excel_path.lower().endswith('.xls') and not excel_path.lower().endswith('.xlsx')
        if annotate_excel and is_xls_file:
            # Automatically disable Excel annotation for .xls files
            print(f"[APP INFO] Excel annotation disabled for .xls file: {excel_path}")
            annotate_excel = False

        # Highlight settings - support both new color_rules and legacy column_color_pairs
        color_rules = data.get('color_rules', [])
        default_highlight_color = data.get('default_highlight_color', '#FFFF00')
        enable_default_color = data.get('enable_default_color', True)
        excel_constraint_mode = data.get('excel_constraint_mode', False)
        excel_constraint_logic = data.get('excel_constraint_logic', 'AND')

        # Legacy support for old single-color system
        if not color_rules:
            highlight_column = data.get('highlight_column', '')
            highlight_color = data.get('highlight_color', '#FFFF00')
            column_color_pairs = [(highlight_column, highlight_color)] if highlight_column else []
        else:
            column_color_pairs = []  # Not used when color_rules provided

        # Watermark settings
        watermark_enabled = data.get('watermark_enabled', False)
        watermark_attributes = data.get('watermark_attributes', [])
        # Support both old single attribute format and new array format
        if not watermark_attributes and data.get('watermark_attribute'):
            watermark_attributes = [data.get('watermark_attribute')]
        watermark_text_color = data.get('watermark_text_color', '#000000')
        watermark_background_enabled = data.get('watermark_background_enabled', False)

        # Tag matching settings
        tag_matching_config = data.get('tag_matching_config', None)

        # Tag filtering settings
        tag_filters = data.get('tag_filters', [])
        filter_logic = data.get('filter_logic', 'AND')

        # Validate filters and count matching tags
        if tag_filters:
            # Load Excel to count matching tags
            is_xls = excel_path.lower().endswith('.xls') and not excel_path.lower().endswith('.xlsx')
            if is_xls:
                df = pd.read_excel(excel_path, header=header_row-1, engine='xlrd')
            else:
                df = pd.read_excel(excel_path, header=header_row-1, engine='openpyxl')

            df = df.dropna(axis=1, how="all")

            # Strip whitespace from column names for consistent matching
            df.columns = [str(col).strip() for col in df.columns]

            # Count tags that pass the filters
            tags = df[tag_column].dropna().astype(str).str.strip()
            matching_tags = sum(1 for tag in tags if tag and tag.lower() != 'nan' and apply_tag_filters(tag, tag_filters, filter_logic))

            if matching_tags == 0:
                return jsonify({
                    'success': False,
                    'message': f'No tags match the selected filters. Please adjust your filter criteria.'
                })


        # Store filters in session for reuse
        session['tag_filters'] = tag_filters
        session['filter_logic'] = filter_logic

        # Create task ID for progress tracking
        task_id = str(uuid.uuid4())
        session['current_task'] = task_id

        # Capture session data and config values for thread (avoid Flask context issues)
        session_id = session.get('session_id', 'default')
        session_data = dict(session)
        current_task_id = task_id
        output_folder = current_app.config['OUTPUT_FOLDER']
        upload_folder = current_app.config['UPLOAD_FOLDER']

        # Get socketio instance and create progress callback
        socketio_instance = current_app.extensions.get('socketio')
        progress_cb = make_progress_callback(socketio_instance)

        # Start processing in a separate thread
        def process_thread(session_id, task_id, original_pdf_names, pdf_paths, excel_path,
                          column_color_pairs, max_tags, tag_column, header_row,
                          selected_comment_columns, watermark_enabled, watermark_attributes,
                          watermark_text_color, watermark_background_enabled, annotate_excel, is_test,
                          tag_matching_config, tag_filters, filter_logic, color_rules, default_highlight_color,
                          enable_default_color, excel_constraint_mode, excel_constraint_logic,
                          output_folder, upload_folder, progress_callback,
                          data, session_data):
            try:
                output_files = []
                output_display_names = []  # Clean names for user display/download
                all_found_tags = set()  # Collect all found tags from all PDFs

                # Aggregate report data from all PDFs
                aggregated_report = {
                    'found': [],
                    'not_found': [],
                    'duplicates': {},
                    'validation_warnings': [],
                    'color_conflicts': [],
                    'page_stats': {},
                    'unmatched_pdf_tags': []
                }

                # Process each PDF file
                for i, pdf_path in enumerate(pdf_paths):
                    # Update progress for current file (allocate 90% across files)
                    total_files = len(pdf_paths)
                    file_share = 90 / total_files if total_files else 90
                    file_base = int(i * file_share)
                    file_end = int((i + 1) * file_share)

                    # Get original filename for progress display (remove session ID prefix)
                    original_name = original_pdf_names[i] if i < len(original_pdf_names) else os.path.basename(pdf_path)

                    # Per-file progress mapper: map core 0..100 into [file_base .. file_end)
                    def per_file_progress_cb(_tid, prog, status):
                        try:
                            mapped = file_base + int((float(prog) / 100.0) * file_share)
                            # Keep within this file's range; leave final step to file_end update
                            if mapped >= file_end:
                                mapped = max(file_end - 1, file_base)
                        except Exception:
                            mapped = file_base
                        progress_callback(task_id, mapped, f"Processing file {i+1}/{total_files}: {original_name} — {status}")

                    # Initial update at start of file segment
                    progress_callback(task_id, file_base, f"Processing file {i+1}/{total_files}: {original_name} — starting...")

                    # Generate clean output filename (no UUID, clean date format)
                    if i < len(original_pdf_names):
                        original_basename = os.path.splitext(original_pdf_names[i])[0]
                    else:
                        # Fallback: extract from stored filename by removing session ID prefix
                        stored_basename = os.path.splitext(os.path.basename(pdf_path))[0]
                        if stored_basename.startswith(f"{session_id}_"):
                            original_basename = stored_basename[len(f"{session_id}_"):]
                        else:
                            original_basename = stored_basename

                    # Format date as DDMMMYYYY (e.g., 01JAN2025)
                    current_date = format_date_ddmmmyyyy(datetime.now())

                    # Add TEST prefix for test runs
                    if is_test:
                        clean_filename = f"{original_basename}_TEST_annotated_{current_date}.pdf"
                    else:
                        clean_filename = f"{original_basename}_annotated_{current_date}.pdf"

                    # Use session ID in actual stored filename to avoid conflicts
                    output_filename = f"{session_id}_{clean_filename}"
                    output_path = os.path.join(output_folder, output_filename)

                    # Create watermark configuration if enabled
                    watermark_config = None
                    if watermark_enabled:
                        # Handle watermark_attributes - convert list to string if needed
                        watermark_attr_str = ""
                        if isinstance(watermark_attributes, list) and watermark_attributes:
                            watermark_attr_str = watermark_attributes[0] if watermark_attributes else ""
                        elif isinstance(watermark_attributes, str):
                            watermark_attr_str = watermark_attributes

                        watermark_config = WatermarkConfig(
                            enabled=True,
                            attributes=watermark_attr_str,
                            text_color=watermark_text_color
                        )

                    # Convert tag_matching_config from dict to object if needed
                    tag_matching_obj = None
                    if tag_matching_config:
                        if isinstance(tag_matching_config, dict):
                            tag_matching_obj = TagMatchingConfig.from_dict(tag_matching_config)
                        else:
                            tag_matching_obj = tag_matching_config

                    # Create annotation configuration from request data, then override computed fields
                    config = AnnotationConfig.from_request(data, dict(session_data))
                    config.pdf_paths = [pdf_path]
                    config.excel_path = excel_path
                    config.output_path = output_path
                    config.max_tags = max_tags
                    config.task_id = task_id
                    config.progress_callback = per_file_progress_cb
                    # Override with resolved values that required pre-processing
                    config.tag_column = tag_column
                    config.watermark = watermark_config
                    config.tag_matching = tag_matching_obj

                    # Process this PDF and get found tags and report data
                    found_tags, report_data = annotate_pdf_with_progress(config)

                    # Collect all found tags from all PDFs
                    if found_tags:
                        all_found_tags.update(found_tags)

                    # Aggregate report data
                    if report_data:
                        aggregated_report['found'].extend(report_data.get('found', []))
                        aggregated_report['not_found'].extend(report_data.get('not_found', []))
                        # Merge duplicates (dict)
                        for tag, dup_data in report_data.get('duplicates', {}).items():
                            # Handle both old format (list) and new format (dict with excel_rows and row_data)
                            if isinstance(dup_data, dict):
                                excel_rows = dup_data.get('excel_rows', [])
                                row_data = dup_data.get('row_data', [])
                            else:
                                # Legacy format - just a list of row numbers
                                excel_rows = dup_data
                                row_data = []

                            if tag in aggregated_report['duplicates']:
                                # Merge with existing entry
                                existing = aggregated_report['duplicates'][tag]
                                if isinstance(existing, dict):
                                    existing['excel_rows'].extend(excel_rows)
                                    existing['row_data'].extend(row_data)
                                else:
                                    # Upgrade legacy format to new format
                                    aggregated_report['duplicates'][tag] = {
                                        'excel_rows': existing + excel_rows,
                                        'row_data': row_data
                                    }
                            else:
                                aggregated_report['duplicates'][tag] = {
                                    'excel_rows': excel_rows,
                                    'row_data': row_data
                                }
                        aggregated_report['validation_warnings'].extend(report_data.get('validation_warnings', []))
                        aggregated_report['color_conflicts'].extend(report_data.get('color_conflicts', []))

                        # Aggregate unmatched PDF tags (merge from multiple PDFs)
                        for unmatched_tag in report_data.get('unmatched_pdf_tags', []):
                            # Check if tag already exists in aggregated list
                            existing = next(
                                (t for t in aggregated_report['unmatched_pdf_tags']
                                 if t['tag'].upper() == unmatched_tag['tag'].upper()),
                                None
                            )
                            if existing:
                                # Merge pages and update count
                                existing['pages'] = sorted(set(existing['pages'] + unmatched_tag['pages']))
                                existing['occurrence_count'] += unmatched_tag['occurrence_count']
                            else:
                                aggregated_report['unmatched_pdf_tags'].append(unmatched_tag.copy())

                        # Capture per-PDF page statistics for reporting
                        page_stats = report_data.get('page_stats') or {}
                        if page_stats:
                            # Use the original filename for clarity in the report output
                            pdf_label = original_name
                            aggregated_report['page_stats'][pdf_label] = {
                                page: dict(stats) if isinstance(stats, dict) else stats
                                for page, stats in page_stats.items()
                            }

                    # Ensure progress reaches the end of this file's segment
                    progress_callback(task_id, file_end, f"Finished file {i+1}/{total_files}: {original_name}")
                    output_files.append(output_filename)
                    output_display_names.append(clean_filename)

                # After processing all PDFs, generate Excel annotation if requested
                if annotate_excel:
                    print(f"\n{'='*80}")
                    print(f"[APP] Starting Excel annotation process...")
                    print(f"{'='*80}")
                    print(f"[APP] Excel file path: {excel_path}")
                    print(f"[APP] Excel file exists: {os.path.exists(excel_path)}")
                    if os.path.exists(excel_path):
                        print(f"[APP] Excel file size: {os.path.getsize(excel_path)} bytes")
                    print(f"[APP] Found tags count: {len(all_found_tags)}")
                    print(f"[APP] Tag column: {tag_column}")
                    print(f"[APP] Header row: {header_row}")
                    print(f"[APP] Report data - Found: {len(aggregated_report.get('found', []))}, Not Found: {len(aggregated_report.get('not_found', []))}, Duplicates: {len(aggregated_report.get('duplicates', {}))}")

                    # Validate prerequisites
                    if not os.path.exists(excel_path):
                        print(f"[APP ERROR] Cannot annotate Excel - file does not exist: {excel_path}")
                        progress_callback(task_id, 95, "Excel annotation skipped - file not found")
                    elif len(all_found_tags) == 0 and len(aggregated_report.get('not_found', [])) == 0:
                        print(f"[APP WARNING] No tags to colorize (no found tags and no not-found tags)")
                        progress_callback(task_id, 95, "Excel annotation skipped - no tags to colorize")
                    else:
                        progress_callback(task_id, 95, "Annotating Excel file...")

                        # Generate clean Excel output filename
                        excel_basename = os.path.splitext(os.path.basename(excel_path))[0]
                        if excel_basename.startswith(f"{session_id}_"):
                            excel_basename = excel_basename[len(f"{session_id}_"):]

                        current_date = format_date_ddmmmyyyy(datetime.now())

                        # Add TEST prefix for test runs
                        if is_test:
                            excel_clean_filename = f"{excel_basename}_TEST_annotated_{current_date}.xlsx"
                        else:
                            excel_clean_filename = f"{excel_basename}_annotated_{current_date}.xlsx"

                        # Use session ID in actual stored filename to avoid conflicts
                        excel_output_filename = f"{session_id}_{excel_clean_filename}"
                        excel_output_path = os.path.join(output_folder, excel_output_filename)

                        print(f"[APP] Output filename: {excel_output_filename}")
                        print(f"[APP] Full output path: {excel_output_path}")
                        print(f"[APP] Output folder exists: {os.path.exists(output_folder)}")

                        # Annotate Excel file with all found tags and report data for color coding
                        try:
                            success = annotate_excel_with_found_tags(
                                excel_path=excel_path,
                                out_path=excel_output_path,
                                found_tags_set=all_found_tags,
                                tag_column=tag_column,
                                header_row=header_row,
                                report_data=aggregated_report
                            )
                        except Exception as e:
                            print(f"[APP ERROR] Exception during Excel annotation: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            success = False

                        if success:
                            # Double-check file exists before adding to output list
                            if os.path.exists(excel_output_path):
                                file_size = os.path.getsize(excel_output_path)
                                output_files.append(excel_output_filename)
                                output_display_names.append(excel_clean_filename)
                                print(f"[APP SUCCESS] Excel file created and verified:")
                                print(f"[APP SUCCESS]   - Path: {excel_output_path}")
                                print(f"[APP SUCCESS]   - Size: {file_size} bytes")
                                print(f"[APP SUCCESS]   - Added to output files list")
                                progress_callback(task_id, 96, "Excel annotation complete")
                            else:
                                print(f"[APP ERROR] annotate_excel_with_found_tags returned True but file does not exist!")
                                print(f"[APP ERROR] Expected path: {excel_output_path}")
                                progress_callback(task_id, 96, "Excel annotation failed - file not created")
                        else:
                            print(f"[APP ERROR] Excel annotation function returned False")
                            progress_callback(task_id, 96, "Excel annotation failed")

                    print(f"{'='*80}\n")

                # Generate HTML processing report
                progress_callback(task_id, 97, "Generating processing report...")
                try:
                    from pid_annotator.reports import generate_html_report

                    # Prepare report settings
                    report_settings = {
                        'tag_column': tag_column,
                        'header_row': header_row,
                        'watermark_enabled': watermark_enabled,
                        'annotate_excel': annotate_excel
                    }

                    # Generate HTML report
                    report_html = generate_html_report(
                        report_data=aggregated_report,
                        pdf_filenames=original_pdf_names,
                        excel_filename=os.path.basename(excel_path),
                        settings=report_settings
                    )

                    # Save report to output folder
                    current_date = format_date_ddmmmyyyy(datetime.now())
                    if is_test:
                        report_clean_filename = f"report_TEST_{current_date}.html"
                    else:
                        report_clean_filename = f"report_{current_date}.html"

                    report_filename = f"{session_id}_{report_clean_filename}"
                    report_path = os.path.join(output_folder, report_filename)

                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write(report_html)

                    output_files.append(report_filename)
                    output_display_names.append(report_clean_filename)

                    progress_callback(task_id, 98, "Report generated successfully")

                except Exception as e:
                    print(f"[APP ERROR] Report generation failed: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    progress_callback(task_id, 98, "Report generation failed (processing continued)")

                # Store output files info in thread-safe global dictionary
                output_files_data[task_id] = {
                    'output_files': output_files,
                    'completed': True,
                    'timestamp': datetime.now().isoformat(),
                    'annotate_excel': annotate_excel,
                    'is_test': is_test
                }

                # Final progress update
                pdf_count = len([f for f in output_files if f.endswith('.pdf')])
                excel_count = len([f for f in output_files if f.endswith('.xlsx')])
                file_description = []
                if pdf_count > 0:
                    file_description.append(f"{pdf_count} PDF(s)")
                if excel_count > 0:
                    file_description.append(f"{excel_count} Excel file(s)")
                file_desc = " and ".join(file_description)

                progress_callback(task_id, 100, f"Processing complete! {file_desc} processed successfully")

            except Exception as e:
                progress_callback(task_id, -1, f"Error: {str(e)}")

        # Start the background task with the progress callback
        if socketio_instance:
            socketio_instance.start_background_task(process_thread, session_id, current_task_id, original_pdf_names, pdf_paths, excel_path,
                              column_color_pairs, max_tags, tag_column, header_row,
                              selected_comment_columns, watermark_enabled, watermark_attributes,
                              watermark_text_color, watermark_background_enabled, annotate_excel, is_test,
                              tag_matching_config, tag_filters, filter_logic, color_rules, default_highlight_color,
                              enable_default_color, excel_constraint_mode, excel_constraint_logic,
                              output_folder, upload_folder, progress_cb,
                              data, session_data)

        return jsonify({
            'success': True,
            'message': f'Processing started',
            'task_id': task_id,
            'file_count': len(pdf_files)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
