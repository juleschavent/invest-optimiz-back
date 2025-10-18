"""
Statement Routes

Handles HTTP endpoints for bank statement operations.
"""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import StatementUploadResponse
from app.services.pdf_parser import extract_text_from_pdf

# Create a router - this groups related endpoints together
# prefix="/statements" means all routes here start with /statements
# tags=["statements"] groups them in the /docs interface
router = APIRouter(prefix="/statements", tags=["statements"])


@router.post("/upload", response_model=StatementUploadResponse)
async def upload_statement(
    file: UploadFile = File(...),
) -> StatementUploadResponse:
    """
    Upload a bank statement PDF and extract its text content.

    Args:
        file: The PDF file to upload (FastAPI's UploadFile handles multipart/form-data)

    Returns:
        StatementUploadResponse with extracted text and metadata

    How FastAPI handles file uploads:
    1. UploadFile is a special type that represents an uploaded file
    2. File(...) tells FastAPI this is required (the ... means "no default")
    3. FastAPI automatically parses multipart/form-data requests
    4. We can access file.filename, file.content_type, and file.read()
    """

    # Validate file type - only accept PDFs
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only PDF files are allowed.",
        )

    # Read the file content into memory as bytes
    # await is needed because file.read() is async
    file_bytes = await file.read()

    # Check if file is empty
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        # Extract text using our PDF parser service
        extracted_text = await extract_text_from_pdf(file_bytes)

        # Count pages by splitting on page breaks (simple heuristic)
        # A better approach would be to modify pdf_parser to return page count
        page_count = extracted_text.count("\n\n") + 1

        # Return the response - FastAPI auto-converts to JSON using the schema
        return StatementUploadResponse(
            filename=file.filename or "unknown.pdf",
            extracted_text=extracted_text,
            page_count=page_count,
            character_count=len(extracted_text),
        )

    except Exception as e:
        # Catch any errors during PDF processing
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
