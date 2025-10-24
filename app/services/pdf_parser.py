"""
PDF Parser Service

This service handles extracting text from PDF files using pdfplumber.
"""

from io import BytesIO

import pdfplumber

from app.exceptions import PDFProcessingError
from app.logger import get_logger

logger = get_logger(__name__)


async def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF file.

    Args:
        file_bytes: The PDF file content as bytes

    Returns:
        Extracted text from all pages concatenated together

    Raises:
        PDFProcessingError: If the PDF cannot be parsed or contains no text

    How it works:
    1. BytesIO wraps the bytes in a file-like object (pdfplumber needs this)
    2. pdfplumber.open() reads the PDF structure
    3. We loop through each page and extract text
    4. All page text is joined with newlines
    """
    try:
        text_content: list[str] = []

        # BytesIO creates a file-like object from bytes in memory
        # This avoids writing to disk
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            if not pdf.pages:
                raise PDFProcessingError(
                    "PDF has no pages",
                    details={"file_size": len(file_bytes)},
                )

            # pdf.pages is a list of Page objects
            for page_num, page in enumerate(pdf.pages, start=1):
                # extract_text() pulls all text from the page
                page_text = page.extract_text()

                # Some pages might be empty or image-only (no text)
                if page_text:
                    text_content.append(page_text)
                else:
                    logger.warning(f"Page {page_num} contains no extractable text")

        if not text_content:
            raise PDFProcessingError(
                "PDF contains no extractable text",
                details={"pages": len(pdf.pages)},
            )

        # Join all pages with double newlines for readability
        extracted_text = "\n\n".join(text_content)
        logger.info(
            f"Successfully extracted {len(extracted_text)} characters from {len(text_content)} pages"
        )
        return extracted_text

    except (ValueError, OSError) as e:
        # pdfplumber raises ValueError or OSError for invalid PDFs
        raise PDFProcessingError(
            "Invalid PDF format or corrupted file",
            details={"error": str(e)},
        ) from e
    except PDFProcessingError:
        # Re-raise our own exceptions
        raise
    except Exception as e:
        # Catch any other unexpected errors during PDF processing
        raise PDFProcessingError(
            "Failed to process PDF",
            details={"error": str(e), "type": type(e).__name__},
        ) from e
