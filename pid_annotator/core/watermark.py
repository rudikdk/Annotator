#!/usr/bin/env python3
"""
Watermark Module

Handles watermark overlay generation and application using ReportLab + PyPDF2.
Two-library approach: ReportLab generates overlay PDFs, PyPDF2 merges them onto pages.
"""

from io import BytesIO
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter

from pid_annotator.tag_engine import _hex_to_rgb01


def create_overlay_page(width, height, items, color_hex, page_rotation=0, background_enabled=False):
    """
    Create a single-page PDF overlay with watermark items at specified positions.
    Applies per-item rotation and compensates for the page's /Rotate value so text
    appears in the intended orientation after viewer rotation.

    Args:
        width: Page width in points
        height: Page height in points
        items: List of watermark items with text, position, rotation
               Each item: {'text': str, 'x': float, 'y': float, 'font_size': int, 'rotation': int}
        color_hex: Text color in hex format (e.g., "#000000")
        page_rotation: Page rotation value (0, 90, 180, 270)
        background_enabled: If True, draw white rectangle behind text

    Returns:
        bytes: PDF overlay as bytes
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


def apply_watermarks(input_pdf_path, output_pdf_path, watermark_items_by_page, watermark_text_color="#000000", watermark_background_enabled=False):
    """
    Apply watermark overlays to a PDF document.

    Args:
        input_pdf_path: Path to input PDF file
        output_pdf_path: Path to output PDF file
        watermark_items_by_page: dict mapping page numbers to lists of watermark items
                                 Format: {page_num: [{'text': str, 'x': float, 'y': float, 'font_size': int, 'rotation': int}, ...]}
        watermark_text_color: Text color in hex format (default: "#000000")
        watermark_background_enabled: If True, draw white rectangle behind text (default: False)

    Returns:
        bool: True if watermarks were applied, False if no watermarks to apply
    """
    # Check if there are any watermarks to apply
    if not watermark_items_by_page or not any(len(v) > 0 for v in watermark_items_by_page.values()):
        print("No watermark overlays to apply.")
        return False

    print("Applying watermark overlays using ReportLab + PyPDF2...")
    reader = PdfReader(input_pdf_path)
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
            overlay_bytes = create_overlay_page(width, height, items, watermark_text_color, page_rotation, watermark_background_enabled)
            overlay_reader = PdfReader(BytesIO(overlay_bytes))
            overlay_page = overlay_reader.pages[0]
            # Merge overlay at (0,0)
            base_page.merge_page(overlay_page)

        writer.add_page(base_page)

    with open(output_pdf_path, "wb") as f_out:
        writer.write(f_out)

    print("Watermark overlay applied and final PDF written.")
    return True
