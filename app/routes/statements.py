from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import PDFProcessingError
from app.logger import get_logger
from app.models import Analysis, Statement
from app.services.pdf_parser import extract_text_from_pdf

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["statements"])


@router.post("/statements")
async def upload_statement(
    file: UploadFile, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Upload a PDF bank statement and extract its text.

    This endpoint:
    - Accepts a PDF file upload
    - Validates the file type
    - Extracts text using pdfplumber
    - Saves the statement to the database
    - Returns the created statement details

    Args:
        file: The PDF file to upload
        db: Database session (injected)

    Returns:
        Created statement with id, filename, and upload timestamp

    Raises:
        HTTPException 400: If file is not a PDF
        HTTPException 422: If PDF processing fails
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are allowed.",
        )

    # Also check content type if provided
    if file.content_type and file.content_type != "application/pdf":
        logger.warning(
            f"File {file.filename} has content_type {file.content_type}, expected application/pdf"
        )

    logger.info(f"Processing uploaded file: {file.filename}")

    try:
        # Read file bytes
        file_bytes = await file.read()
        file_size = len(file_bytes)

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        logger.info(f"Read {file_size} bytes from {file.filename}")

        # Extract text from PDF
        extracted_text = await extract_text_from_pdf(file_bytes)

        # Create statement in database
        statement = Statement(
            filename=file.filename,
            extracted_text=extracted_text,
        )

        db.add(statement)
        await db.flush()
        await db.refresh(statement)

        logger.info(
            f"Successfully created statement {statement.id} from {file.filename}"
        )

        return {
            "message": "Statement uploaded successfully",
            "id": statement.id,
            "filename": statement.filename,
            "uploaded_at": statement.uploaded_at.isoformat(),
            "text_length": len(extracted_text),
            "text_preview": extracted_text[:200] + "..."
            if len(extracted_text) > 200
            else extracted_text,
        }

    except PDFProcessingError as e:
        logger.error(f"PDF processing failed for {file.filename}: {e.message}")
        raise HTTPException(status_code=422, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"Unexpected error processing {file.filename}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Internal server error processing file"
        ) from e


@router.post("/create-test-statement")
async def create_test_statement(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Creates a test statement in the database.

    This demonstrates:
    - Creating a model instance
    - Adding it to the session
    - Committing to save to database
    - Returning the created object
    """
    # Create a new Statement instance
    statement = Statement(
        filename="test_statement.pdf",
        extracted_text="This is a test bank statement with sample transactions.",
    )

    # Add to session (stages the insert)
    db.add(statement)

    # Commit happens automatically in get_db()
    # But we need to refresh to get the auto-generated ID
    await db.flush()  # Sends to DB but doesn't commit yet
    await db.refresh(statement)  # Loads the ID back

    return {
        "message": "Test statement created!",
        "id": statement.id,
        "filename": statement.filename,
        "uploaded_at": statement.uploaded_at.isoformat(),
    }


@router.get("/statements")
async def get_all_statements(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Retrieves all statements from the database.

    This demonstrates:
    - Building a SELECT query
    - Executing it asynchronously
    - Processing results
    """
    # Build query using SQLAlchemy 2.0 style
    query = select(Statement).order_by(Statement.uploaded_at.desc())

    # Execute query
    result = await db.execute(query)

    # Get all rows
    statements = result.scalars().all()

    return {
        "count": len(statements),
        "statements": [
            {
                "id": s.id,
                "filename": s.filename,
                "uploaded_at": s.uploaded_at.isoformat(),
                "text_preview": s.extracted_text[:100] + "..."
                if len(s.extracted_text) > 100
                else s.extracted_text,
            }
            for s in statements
        ],
    }


@router.get("/statements/{statement_id}")
async def get_statement(
    statement_id: int, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Get a specific statement by ID with all its analyses.

    This demonstrates:
    - Querying by ID
    - Accessing relationships (statement.analyses)
    - Error handling (404 if not found)
    """
    # Query for statement
    query = select(Statement).where(Statement.id == statement_id)
    result = await db.execute(query)
    statement = result.scalar_one_or_none()

    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")

    return {
        "id": statement.id,
        "filename": statement.filename,
        "extracted_text": statement.extracted_text,
        "uploaded_at": statement.uploaded_at.isoformat(),
        "analyses_count": len(statement.analyses),
        "analyses": [
            {
                "id": a.id,
                "created_at": a.created_at.isoformat(),
                "prompt": a.prompt[:100] + "..." if len(a.prompt) > 100 else a.prompt,
            }
            for a in statement.analyses
        ],
    }


@router.post("/statements/{statement_id}/analyses")
async def create_analysis(
    statement_id: int, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Create a test analysis for a statement.

    This demonstrates:
    - Foreign key relationships
    - Creating related objects
    """
    # Verify statement exists
    query = select(Statement).where(Statement.id == statement_id)
    result = await db.execute(query)
    statement = result.scalar_one_or_none()

    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")

    # Create analysis
    analysis = Analysis(
        statement_id=statement_id,
        prompt="Analyze this test statement",
        response="This is a test analysis. The spending pattern shows normal activity.",
    )

    db.add(analysis)
    await db.flush()
    await db.refresh(analysis)

    return {
        "message": "Analysis created!",
        "id": analysis.id,
        "statement_id": analysis.statement_id,
        "created_at": analysis.created_at.isoformat(),
    }


@router.delete("/statements/{statement_id}")
async def delete_statement(
    statement_id: int, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Delete a statement (and all its analyses via cascade).

    This demonstrates:
    - Delete operations
    - Cascade delete behavior
    """
    query = select(Statement).where(Statement.id == statement_id)
    result = await db.execute(query)
    statement = result.scalar_one_or_none()

    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")

    analyses_count = len(statement.analyses)

    await db.delete(statement)
    # Commit happens automatically

    return {
        "message": "Statement deleted",
        "deleted_analyses": analyses_count,
    }
