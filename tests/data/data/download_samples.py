#!/usr/bin/env python
"""
Script to download sample PDF files for testing.

This script downloads various types of PDF files for testing the document processing pipeline:
- Simple text-only PDFs
- Multi-column PDFs
- Scanned PDFs (for OCR testing)
- PDFs with tables
- PDFs with figures
- Complex PDFs with mixed content
- A corrupted PDF for error handling tests
"""

import os
import urllib.request
from pathlib import Path

# Define the sample PDF URLs
# These are public domain or open-licensed PDFs available for testing
SAMPLE_PDFS = {
    # Simple text-only PDF
    "sample1_simple.pdf": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
    
    # Multi-column PDF (academic paper)
    "sample2_multicolumn.pdf": "https://arxiv.org/pdf/2104.08821.pdf",
    
    # Scanned PDF (for OCR testing)
    "sample3_scanned.pdf": "https://arxiv.org/pdf/cond-mat/0610375.pdf",
    
    # PDF with tables
    "sample4_tables.pdf": "https://www.irs.gov/pub/irs-pdf/f1040.pdf",
    
    # PDF with figures
    "sample5_figures.pdf": "https://arxiv.org/pdf/2003.08934.pdf",
    
    # Complex PDF with mixed content
    "sample6_mixed.pdf": "https://www.adobe.com/content/dam/acom/en/devnet/acrobat/pdfs/pdf_open_parameters.pdf"
}

# Path to save the downloaded PDFs
DOWNLOAD_DIR = Path(__file__).parent


def download_file(url, output_path):
    """
    Download a file from a URL.
    
    Args:
        url: URL to download from
        output_path: Path to save the downloaded file
    
    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        print(f"Downloading {url} to {output_path}...")
        urllib.request.urlretrieve(url, output_path)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def create_corrupt_pdf():
    """
    Create a corrupted PDF file for testing error handling.
    
    Returns:
        Path: Path to the created corrupt PDF file
    """
    corrupt_pdf_path = DOWNLOAD_DIR / "corrupt.pdf"
    
    # Create a file that starts with the PDF header but is otherwise corrupted
    with open(corrupt_pdf_path, "wb") as f:
        f.write(b"%PDF-1.7\n")
        f.write(b"This is not a valid PDF file content. It is intentionally corrupted for testing purposes.")
    
    print(f"Created corrupted PDF at {corrupt_pdf_path}")
    return corrupt_pdf_path


def main():
    """
    Main function to download all sample PDFs.
    """
    # Create the download directory if it doesn't exist
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # Download each sample PDF
    for filename, url in SAMPLE_PDFS.items():
        output_path = DOWNLOAD_DIR / filename
        
        # Skip if file already exists
        if output_path.exists():
            print(f"File {filename} already exists. Skipping download.")
            continue
        
        # Download the file
        success = download_file(url, output_path)
        
        if success:
            print(f"Successfully downloaded {filename}")
        else:
            print(f"Failed to download {filename}")
    
    # Create a corrupted PDF for error testing
    create_corrupt_pdf()
    
    print("\nDownload complete. Sample PDFs are available in:", DOWNLOAD_DIR)


if __name__ == "__main__":
    main() 