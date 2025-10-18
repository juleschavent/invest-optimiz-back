"""
PDF Parser Service

This service handles extracting text from PDF files using pdfplumber.
"""

from io import BytesIO

import pdfplumber


async def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF file.

    Args:
        file_bytes: The PDF file content as bytes

    Returns:
        Extracted text from all pages concatenated together

    How it works:
    1. BytesIO wraps the bytes in a file-like object (pdfplumber needs this)
    2. pdfplumber.open() reads the PDF structure
    3. We loop through each page and extract text
    4. All page text is joined with newlines
    """
    text_content = []

    # BytesIO creates a file-like object from bytes in memory
    # This avoids writing to disk
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        # pdf.pages is a list of Page objects
        for page in pdf.pages:
            # extract_text() pulls all text from the page
            page_text = page.extract_text()

            # Some pages might be empty or image-only (no text)
            if page_text:
                text_content.append(page_text)

    # Join all pages with double newlines for readability
    return "\n\n".join(text_content)
