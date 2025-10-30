"""
Test script to demonstrate the refactored Not Found tags section in the report template.
This script generates a sample HTML report showing both old-style (no row_data) and
new-style (with row_data) Not Found tags.
"""

from report_template import generate_html_report

# Sample report data with both old and new format for not_found tags
report_data = {
    'found': [
        {
            'tag': 'TAG-001-A',
            'pages': [0, 5, 10],
            'bookmarks': ['System A', 'System B'],
            'occurrence_count': 15,
            'excel_row': 2
        },
        {
            'tag': 'TAG-002-B',
            'pages': [3, 7],
            'bookmarks': ['Subsystem C'],
            'occurrence_count': 8,
            'excel_row': 3
        }
    ],
    'not_found': [
        # OLD FORMAT: Simple not_found item without row_data (toggle button will NOT appear)
        {
            'tag': 'TAG-003-C',
            'excel_row': 4,
            'reason': 'not_in_pdf'
        },
        # NEW FORMAT: Not_found item WITH row_data (toggle button WILL appear, table will be shown)
        {
            'tag': 'TAG-004-D',
            'excel_row': 5,
            'reason': 'not_in_pdf',
            'row_data': {
                'excel_row': 5,
                'Tag': 'TAG-004-D',
                'Description': 'Pressure Transmitter',
                'Location': 'Area 51',
                'Type': 'PT',
                'Vendor': 'Rosemount',
                'Model': '3051CD'
            }
        },
        # Another NEW FORMAT example with different columns
        {
            'tag': 'TAG-005-E',
            'excel_row': 6,
            'reason': 'missing_in_drawing',
            'row_data': {
                'excel_row': 6,
                'Tag': 'TAG-005-E',
                'Description': 'Flow Indicator',
                'Service': 'Cooling Water',
                'Size': '2 inch',
                'Material': 'SS316'
            }
        }
    ],
    'duplicates': {
        'TAG-006-F': {
            'excel_rows': [7, 12, 18],
            'row_data': [
                {
                    'excel_row': 7,
                    'Tag': 'TAG-006-F',
                    'Description': 'Level Switch - First Instance',
                    'Location': 'Tank A'
                },
                {
                    'excel_row': 12,
                    'Tag': 'TAG-006-F',
                    'Description': 'Level Switch - Second Instance',
                    'Location': 'Tank B'
                },
                {
                    'excel_row': 18,
                    'Tag': 'TAG-006-F',
                    'Description': 'Level Switch - Third Instance',
                    'Location': 'Tank C'
                }
            ]
        }
    },
    'validation_warnings': [
        {
            'tag': 'TAG-007-G',
            'excel_row': 8,
            'warning': 'Missing description'
        }
    ],
    'page_stats': {}
}

# Generate HTML report
html_content = generate_html_report(
    report_data=report_data,
    pdf_filenames=['sample_drawing.pdf'],
    excel_filename='component_list.xlsx',
    settings={
        'tag_column': 'A',
        'header_row': 6,
        'watermark_enabled': True,
        'annotate_excel': True
    }
)

# Save to file
output_path = 'test_report_output.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Test report generated successfully!")
print(f"Output saved to: {output_path}")
print("\nWhat to look for in the report:")
print("1. TAG-003-C (old format): NO toggle button - shows as simple row")
print("2. TAG-004-D (new format): HAS toggle button - click to see Excel data table")
print("3. TAG-005-E (new format): HAS toggle button - click to see Excel data table with different columns")
print("\nThe detail panel now displays Excel row data in a formatted table,")
print("just like the Duplicates section does!")
