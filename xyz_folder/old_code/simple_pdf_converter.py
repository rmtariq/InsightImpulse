#!/usr/bin/env python3
"""
Simple PDF converter using markdown-pdf package
"""

import os
import subprocess

def convert_with_markdown_pdf():
    """Try using markdown-pdf npm package"""
    try:
        # Check if npm is available
        result = subprocess.run(['which', 'npm'], capture_output=True)
        if result.returncode != 0:
            print("❌ npm not found")
            return False
        
        # Check if markdown-pdf is installed
        result = subprocess.run(['npm', 'list', '-g', 'markdown-pdf'], capture_output=True)
        if 'markdown-pdf' not in result.stdout.decode():
            print("📦 Installing markdown-pdf...")
            subprocess.run(['npm', 'install', '-g', 'markdown-pdf'])
        
        # Convert
        print("🔄 Converting with markdown-pdf...")
        result = subprocess.run([
            'markdown-pdf',
            'INSIGHTPULSE_BROCHURE.md',
            '-o', 'INSIGHTPULSE_BROCHURE.pdf'
        ], capture_output=True)
        
        if result.returncode == 0:
            print("✅ PDF created successfully!")
            return True
        else:
            print(f"❌ Error: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def open_html_in_browser():
    """Open HTML in browser for manual PDF conversion"""
    print("\n📖 Opening HTML in browser for manual conversion...")
    print("\nTo convert to PDF:")
    print("1. The HTML file will open in your browser")
    print("2. Press Cmd+P (or File > Print)")
    print("3. Select 'Save as PDF' as the destination")
    print("4. Save as 'INSIGHTPULSE_BROCHURE.pdf'")
    print("\nOpening browser now...")
    
    html_path = os.path.abspath('INSIGHTPULSE_BROCHURE.html')
    subprocess.run(['open', html_path])
    
    return True

def main():
    print("=" * 60)
    print("InsightPulse Brochure - PDF Conversion Tool")
    print("=" * 60)
    
    # Try markdown-pdf first
    if convert_with_markdown_pdf():
        print("\n✅ Success! PDF file created: INSIGHTPULSE_BROCHURE.pdf")
        return
    
    # Fallback to manual browser conversion
    print("\n💡 Automatic conversion failed. Using manual method...")
    if open_html_in_browser():
        print("\n✅ HTML file opened in browser for manual conversion")
    else:
        print("\n❌ Could not open HTML file")
        print("Please manually open: INSIGHTPULSE_BROCHURE.html")

if __name__ == "__main__":
    main()
