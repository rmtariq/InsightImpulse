#!/usr/bin/env python3
"""
Convert InsightPulse Brochure from Markdown to PDF
Using markdown2 and reportlab
"""

import os
import re
from pathlib import Path

# Install required packages if not available
try:
    import markdown2
except ImportError:
    print("Installing markdown2...")
    os.system("pip install markdown2")
    import markdown2

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.lib.colors import HexColor, blue, black, white
    from reportlab.pdfgen import canvas
except ImportError:
    print("ReportLab is already installed")

def clean_markdown_for_html(md_text):
    """Clean markdown text for better HTML conversion"""
    # Remove shield.io badges (they won't render in PDF)
    md_text = re.sub(r'\[\!\[.*?\]\(.*?\)\]\(\)', '', md_text)
    
    # Convert div tags to simple text
    md_text = re.sub(r'<div.*?>', '', md_text)
    md_text = re.sub(r'</div>', '', md_text)
    
    return md_text

def markdown_to_html(md_file):
    """Convert Markdown file to HTML"""
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()
    
    # Clean markdown
    md_text = clean_markdown_for_html(md_text)
    
    # Convert to HTML
    html = markdown2.markdown(md_text, extras=[
        'tables',
        'fenced-code-blocks',
        'header-ids',
        'strike',
        'task_list'
    ])
    
    return html

def html_to_pdf_simple(html_content, output_pdf):
    """Convert HTML to PDF using simple HTML rendering"""
    try:
        # Try using weasyprint if available
        import weasyprint
        weasyprint.HTML(string=html_content).write_pdf(output_pdf)
        return True
    except ImportError:
        return False

def main():
    print("🔄 Converting INSIGHTPULSE_BROCHURE.md to PDF...")
    
    md_file = "INSIGHTPULSE_BROCHURE.md"
    output_pdf = "INSIGHTPULSE_BROCHURE.pdf"
    
    if not Path(md_file).exists():
        print(f"❌ Error: {md_file} not found!")
        return
    
    # Convert Markdown to HTML
    print("📝 Converting Markdown to HTML...")
    html_content = markdown_to_html(md_file)
    
    # Add CSS styling
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #333;
            }}
            h1 {{
                color: #1e40af;
                font-size: 24pt;
                border-bottom: 3px solid #1e40af;
                padding-bottom: 10px;
                page-break-after: avoid;
            }}
            h2 {{
                color: #1e40af;
                font-size: 18pt;
                margin-top: 20px;
                page-break-after: avoid;
            }}
            h3 {{
                color: #3b82f6;
                font-size: 14pt;
                margin-top: 15px;
                page-break-after: avoid;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #1e40af;
                color: white;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 5px;
                border-radius: 3px;
            }}
            blockquote {{
                border-left: 4px solid #1e40af;
                padding-left: 15px;
                margin-left: 0;
                font-style: italic;
                color: #666;
            }}
            a {{
                color: #1e40af;
                text-decoration: none;
            }}
            hr {{
                border: none;
                border-top: 2px solid #e5e7eb;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Try weasyprint first
    print("📄 Generating PDF...")
    if html_to_pdf_simple(styled_html, output_pdf):
        print(f"✅ PDF created successfully: {output_pdf}")
    else:
        print("⚠️  WeasyPrint not available. Installing...")
        os.system("pip install weasyprint")
        try:
            import weasyprint
            weasyprint.HTML(string=styled_html).write_pdf(output_pdf)
            print(f"✅ PDF created successfully: {output_pdf}")
        except Exception as e:
            print(f"❌ Error creating PDF: {e}")
            print("\n💡 Alternative: Save HTML version for manual conversion")
            html_file = "INSIGHTPULSE_BROCHURE.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(styled_html)
            print(f"✅ HTML version saved: {html_file}")
            print("   You can open this in a browser and use 'Print to PDF'")

if __name__ == "__main__":
    main()
