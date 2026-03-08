"""
PDF preview generation routes
"""
import os
import base64
from datetime import datetime
from pathlib import Path
import fitz
from flask import Blueprint, request, jsonify, send_file, session, current_app

from pid_annotator.core.preview_generator import annotate_pdf_page_for_preview
from pid_annotator.core.pdf_annotator import annotate_pdf_with_progress
from pid_annotator.config import AnnotationConfig, WatermarkConfig, TagMatchingConfig

# Create blueprint
preview_bp = Blueprint('preview', __name__)


def format_date_ddmmmyyyy(dt):
    """Format date as DDMMMYYYY (e.g., 01JAN2025)"""
    return dt.strftime('%d%b%Y').upper()


@preview_bp.route('/preview_color_rules', methods=['POST'])
def preview_color_rules():
    """
    Generate a preview of a PDF page with FULL annotation pipeline.
    This now uses the same code path as actual processing for accurate preview.
    """
    try:
        data = request.get_json()
        pdf_file = data.get('pdf_file')
        excel_file = data.get('excel_file')
        tag_column = data.get('tag_column')
        header_row = data.get('header_row', 6)

        # Get ALL settings (same as /process endpoint)
        color_rules = data.get('color_rules', [])
        default_highlight_color = data.get('default_highlight_color', '#FFFF00')
        enable_default_color = data.get('enable_default_color', True)
        excel_constraint_mode = data.get('excel_constraint_mode', False)
        excel_constraint_logic = data.get('excel_constraint_logic', 'AND')
        tag_filters = data.get('tag_filters', [])
        filter_logic = data.get('filter_logic', 'AND')
        tag_matching_config = data.get('tag_matching_config', None)
        page_number = data.get('page_number', None)

        # NEW: Get comment and watermark settings for full preview
        selected_comment_columns = data.get('comment_columns', None)
        watermark_enabled = data.get('watermark_enabled', False)
        watermark_attributes = data.get('watermark_attributes', [])
        watermark_text_color = data.get('watermark_text_color', '#000000')
        watermark_font_size = data.get('watermark_font_size', 9)
        watermark_background_enabled = data.get('watermark_background_enabled', False)
        annotation_type = data.get('annotation_type', 'highlight_only')

        if not pdf_file:
            return jsonify({'success': False, 'message': 'No PDF file specified'})

        if not excel_file:
            return jsonify({'success': False, 'message': 'No Excel file specified'})

        # Get file paths
        pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], pdf_file)
        excel_path = os.path.join(current_app.config['UPLOAD_FOLDER'], excel_file)

        if not os.path.exists(pdf_path):
            return jsonify({'success': False, 'message': f'PDF file not found: {pdf_file}'})

        if not os.path.exists(excel_path):
            return jsonify({'success': False, 'message': f'Excel file not found: {excel_file}'})

        # Determine page number with smart defaults
        doc_temp = fitz.open(pdf_path)
        total_pages = len(doc_temp)
        doc_temp.close()

        if page_number is not None:
            page_num = max(0, min(page_number - 1, total_pages - 1))  # Convert to 0-indexed and clamp
        else:
            # Default selection logic: page 5 if available, else last page
            if total_pages >= 5:
                page_num = 4  # Page 5 (0-indexed)
            else:
                page_num = total_pages - 1  # Last page

        print(f"[PREVIEW] Generating preview for page {page_num + 1} of {total_pages}")

        # Call the single-page preview function with ALL settings
        result = annotate_pdf_page_for_preview(
            pdf_path=pdf_path,
            excel_path=excel_path,
            page_num=page_num,
            tag_column=tag_column,
            header_row=header_row,
            selected_comment_columns=selected_comment_columns,
            color_rules=color_rules,
            default_highlight_color=default_highlight_color,
            enable_default_color=enable_default_color,
            excel_constraint_mode=excel_constraint_mode,
            excel_constraint_logic=excel_constraint_logic,
            watermark_enabled=watermark_enabled,
            watermark_attributes=watermark_attributes,
            watermark_text_color=watermark_text_color,
            watermark_font_size=watermark_font_size,
            watermark_background_enabled=watermark_background_enabled,
            tag_matching_config=tag_matching_config,
            tag_filters=tag_filters,
            filter_logic=filter_logic,
            annotation_type=annotation_type
        )

        if not result['success']:
            return jsonify(result)

        # Render the annotated page as image
        page = result['page']
        doc = result['doc']

        # Render page as image (2x zoom for better quality)
        # annots=True ensures all annotations (highlights, comments) are rendered
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat, annots=True)

        # Convert to PNG bytes
        img_bytes = pix.tobytes("png")

        # Encode as base64 for JSON response
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        # Close document
        doc.close()

        # Return preview with complete stats
        return jsonify({
            'success': True,
            'page_number': page_num + 1,  # 1-indexed for display
            'total_pages': total_pages,
            'stats': result['stats'],
            'image': f'data:image/png;base64,{img_base64}',
            'message': result['message']
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error generating preview: {str(e)}'
        })


@preview_bp.route('/generate_full_preview', methods=['POST'])
def generate_full_preview():
    """
    Generate a complete annotated single-page PDF preview with ALL settings applied.
    This creates an actual PDF file that can be viewed and downloaded.
    Processes a single page (default: total_pages / 3) as a test run.
    """
    try:
        data = request.get_json()

        # Get file selections
        selected_pdfs = data.get('selected_pdfs', [])
        selected_excel = data.get('selected_excel', None)

        if not selected_pdfs or len(selected_pdfs) == 0:
            return jsonify({'success': False, 'message': 'No PDF file selected'})

        if not selected_excel:
            return jsonify({'success': False, 'message': 'No Excel file selected'})

        # Use first selected PDF
        pdf_file = selected_pdfs[0]
        excel_file = selected_excel

        # Get file paths
        pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], pdf_file)
        excel_path = os.path.join(current_app.config['UPLOAD_FOLDER'], excel_file)

        if not os.path.exists(pdf_path):
            return jsonify({'success': False, 'message': f'PDF file not found: {pdf_file}'})

        if not os.path.exists(excel_path):
            return jsonify({'success': False, 'message': f'Excel file not found: {excel_file}'})

        # Get processing parameters
        header_row = data.get('header_row', 6)
        tag_column = data.get('tag_column')
        selected_comment_columns = data.get('comment_columns', None)

        # Color settings
        color_rules = data.get('color_rules', [])
        default_highlight_color = data.get('default_highlight_color', '#FFFF00')
        enable_default_color = data.get('enable_default_color', True)
        excel_constraint_mode = data.get('excel_constraint_mode', False)
        excel_constraint_logic = data.get('excel_constraint_logic', 'AND')

        # Watermark settings
        watermark_enabled = data.get('watermark_enabled', False)
        watermark_attributes = data.get('watermark_attributes', [])
        watermark_text_color = data.get('watermark_text_color', '#000000')
        watermark_font_size = data.get('watermark_font_size', 9)
        watermark_background_enabled = data.get('watermark_background_enabled', False)

        # Tag matching and filtering
        tag_matching_config = data.get('tag_matching_config', None)
        tag_filters = data.get('tag_filters', [])
        filter_logic = data.get('filter_logic', 'AND')

        # Page selection
        requested_page = data.get('page_number', None)

        # Determine which page to preview
        doc_source = fitz.open(pdf_path)
        total_pages = len(doc_source)

        if requested_page is not None:
            # User selected a specific page
            preview_page = max(1, min(requested_page, total_pages))
        else:
            # Smart default: page at total_pages / 3 position
            preview_page = max(1, total_pages // 3)

        print(f"[FULL PREVIEW] Processing page {preview_page} of {total_pages} from {pdf_file}")

        # Extract single page to temporary PDF
        session_id = session.get('session_id', 'default')
        temp_single_page_pdf = os.path.join(current_app.config['OUTPUT_FOLDER'], f"{session_id}_temp_page_{preview_page}.pdf")

        # Create single-page PDF
        doc_single = fitz.open()  # New empty PDF
        doc_single.insert_pdf(doc_source, from_page=preview_page-1, to_page=preview_page-1)
        doc_single.save(temp_single_page_pdf)
        doc_single.close()
        doc_source.close()

        # Create output filename
        original_name = pdf_file[len(f"{session_id}_"):] if pdf_file.startswith(f"{session_id}_") else pdf_file
        original_basename = os.path.splitext(original_name)[0]
        current_date = format_date_ddmmmyyyy(datetime.now())

        preview_clean_filename = f"{original_basename}_PREVIEW_page{preview_page}_{current_date}.pdf"
        preview_output_filename = f"{session_id}_{preview_clean_filename}"
        preview_output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], preview_output_filename)

        # Create watermark configuration if enabled
        watermark_config = None
        if watermark_enabled:
            attrs = watermark_attributes if isinstance(watermark_attributes, list) else ([watermark_attributes] if watermark_attributes else [])
            watermark_config = WatermarkConfig(
                enabled=True,
                attributes=attrs,
                text_color=watermark_text_color,
                font_size=watermark_font_size,
                background_enabled=watermark_background_enabled
            )

        # Convert tag_matching_config from dict to object if needed
        tag_matching_obj = None
        if tag_matching_config:
            if isinstance(tag_matching_config, dict):
                tag_matching_obj = TagMatchingConfig.from_dict(tag_matching_config)
            else:
                tag_matching_obj = tag_matching_config

        # Create annotation configuration
        config = AnnotationConfig(
            pdf_paths=[temp_single_page_pdf],
            excel_path=excel_path,
            output_path=preview_output_path,
            tag_column=tag_column,
            header_row=header_row,
            comment_columns=selected_comment_columns,
            highlight_color=default_highlight_color,
            annotation_type="highlight_only",
            watermark=watermark_config,
            tag_matching=tag_matching_obj,
            filters=tag_filters,
            filter_logic=filter_logic,
            color_rules=color_rules,
            column_color_pairs=[],
            max_tags=None,
            enable_default_color=enable_default_color,
            excel_constraint_mode=excel_constraint_mode,
            excel_constraint_logic=excel_constraint_logic,
            task_id='preview',
            progress_callback=lambda tid, prog, status: None
        )

        # Process the single-page PDF with full annotation pipeline
        found_tags, report_data = annotate_pdf_with_progress(config)

        # Clean up temp file
        try:
            os.remove(temp_single_page_pdf)
        except:
            pass

        # Prepare stats - for the single preview page
        # report_data['page_stats'][1] = statistics for page 1 (the single preview page)
        # page_stats contains:
        #   - total_count: ALL tag occurrences found on this page
        #   - colored_count: How many of those occurrences were actually colored

        # Debug: Print report_data structure
        print(f"\n[PREVIEW DEBUG] Original page selected: {preview_page} (out of {total_pages} pages)")
        print(f"[PREVIEW DEBUG] Temp single-page PDF: {temp_single_page_pdf}")
        print(f"[PREVIEW DEBUG] report_data keys: {report_data.keys() if report_data else 'None'}")
        if report_data and 'page_stats' in report_data:
            print(f"[PREVIEW DEBUG] page_stats keys: {report_data['page_stats'].keys()}")
            for page_num, page_data in report_data['page_stats'].items():
                # Don't print full tag_details to avoid clutter
                summary = {k: v for k, v in page_data.items() if k != 'tag_details'}
                print(f"[PREVIEW DEBUG] Page {page_num} stats: {summary}")

        # Get page stats for the preview page
        # The single-page PDF has only 1 page at index 0 (PyMuPDF uses 0-based indexing)
        # This contains stats for the original page (preview_page) that was extracted
        page_stats = report_data.get('page_stats', {}).get(0, {}) if report_data else {}

        stats = {
            'total_tags': page_stats.get('total_count', 0),  # All tag occurrences found on this page
            'colored_tags': page_stats.get('colored_count', 0),  # How many were actually colored
            'conflict_count': len(report_data.get('color_conflicts', [])) if report_data else 0
        }

        print(f"[PREVIEW] Preview generated successfully: {preview_clean_filename}")
        print(f"[PREVIEW] Stats for original page {preview_page}: {stats['colored_tags']} colored / {stats['total_tags']} total tags")
        print(f"[PREVIEW] Conflict count: {stats['conflict_count']}\n")

        # Return PDF URL instead of base64 image - frontend will use PDF.js to render
        return jsonify({
            'success': True,
            'page_number': preview_page,
            'total_pages': total_pages,
            'stats': stats,
            'pdf_url': f'/view_preview/{preview_output_filename}',
            'preview_filename': preview_output_filename,
            'preview_clean_name': preview_clean_filename,
            'download_url': f'/download_preview/{preview_output_filename}',
            'message': f'Preview generated for page {preview_page} of {total_pages}'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error generating preview: {str(e)}'
        })


@preview_bp.route('/view_preview/<filename>')
def view_preview(filename):
    """View a preview PDF file in the browser (for PDF.js rendering)"""
    try:
        session_id = session.get('session_id', 'default')

        # Security check - ensure filename belongs to current session
        if not filename.startswith(f"{session_id}_"):
            return jsonify({'success': False, 'message': 'Invalid file access'}), 403

        # Check if file exists in output folder
        file_path = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)

        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'Preview file not found'}), 404

        print(f"[PREVIEW VIEW] Serving preview for viewing: {filename}")
        return send_file(file_path, mimetype='application/pdf')

    except Exception as e:
        print(f"[PREVIEW VIEW ERROR] {str(e)}")
        return jsonify({'success': False, 'message': f'Error viewing preview: {str(e)}'}), 500


@preview_bp.route('/download_preview/<filename>')
def download_preview(filename):
    """Download a preview PDF file"""
    try:
        session_id = session.get('session_id', 'default')

        # Security check - ensure filename belongs to current session
        if not filename.startswith(f"{session_id}_"):
            return jsonify({'success': False, 'message': 'Invalid file access'}), 403

        # Check if file exists in output folder
        file_path = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)

        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'Preview file not found'}), 404

        # Extract clean filename for download
        clean_name = filename[len(f"{session_id}_"):]

        print(f"[PREVIEW DOWNLOAD] Serving preview: {clean_name}")
        return send_file(file_path, as_attachment=True, download_name=clean_name)

    except Exception as e:
        print(f"[PREVIEW DOWNLOAD ERROR] {str(e)}")
        return jsonify({'success': False, 'message': f'Error downloading preview: {str(e)}'}), 500
