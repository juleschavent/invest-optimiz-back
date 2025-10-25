from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.exceptions import CSVProcessingError
from app.logger import get_logger
from app.models import Analysis, Statement
from app.services.csv_parser import parse_csv

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["statements"])


@router.post("/statements")
async def upload_statement(
    file: UploadFile, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Upload a CSV bank statement and parse its transactions.

    This endpoint:
    - Accepts a CSV file upload
    - Validates the file type
    - Parses transactions and metadata
    - Saves the statement to the database
    - Returns the created statement details

    Args:
        file: The CSV file to upload
        db: Database session (injected)

    Returns:
        Created statement with id, filename, transaction count, and sample data

    Raises:
        HTTPException 400: If file is not a CSV
        HTTPException 422: If CSV processing fails
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only CSV files are allowed.",
        )

    # Also check content type if provided
    if file.content_type and file.content_type not in ["text/csv", "application/csv"]:
        logger.warning(
            f"File {file.filename} has content_type {file.content_type}, expected text/csv"
        )

    logger.info(f"Processing uploaded file: {file.filename}")

    try:
        # Read file bytes
        file_bytes = await file.read()
        file_size = len(file_bytes)

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        logger.info(f"Read {file_size} bytes from {file.filename}")

        # Parse CSV file
        parsed_data = await parse_csv(file_bytes)

        # Extract metadata
        metadata = parsed_data["metadata"]

        # Create statement in database
        statement = Statement(
            filename=file.filename,
            file_type="csv",
            raw_data=parsed_data["raw_csv"],
            transactions=parsed_data["transactions"],
            account_holder=metadata.get("account_holder"),
            account_number=metadata.get("account_number"),
            balance=metadata.get("balance"),
            balance_date=metadata.get("balance_date"),
            period_start=metadata.get("period_start"),
            period_end=metadata.get("period_end"),
        )

        db.add(statement)
        await db.flush()
        await db.refresh(statement)

        logger.info(
            f"Successfully created statement {statement.id} from {file.filename} "
            f"with {len(parsed_data['transactions'])} transactions"
        )

        return {
            "message": "Statement uploaded successfully",
            "id": statement.id,
            "filename": statement.filename,
            "uploaded_at": statement.uploaded_at.isoformat(),
            "transaction_count": len(parsed_data["transactions"]),
            "metadata": parsed_data["metadata"],
            "transactions_preview": parsed_data["transactions"][:5],  # First 5
        }

    except CSVProcessingError as e:
        logger.error(f"CSV processing failed for {file.filename}: {e.message}")
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
    # Create a new Statement instance with test CSV data
    statement = Statement(
        filename="test_statement.csv",
        file_type="csv",
        raw_data="Date;Description;Debit;Credit\n01/01/2024;Test transaction;10.00;",
        transactions=[
            {
                "date": "01/01/2024",
                "description": "Test transaction",
                "debit": 10.0,
                "credit": None,
            }
        ],
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
                "file_type": s.file_type,
                "uploaded_at": s.uploaded_at.isoformat(),
                "transaction_count": len(s.transactions),
                "account_holder": s.account_holder,
                "account_number": s.account_number,
                "balance": s.balance,
                "balance_date": s.balance_date,
                "period_start": s.period_start,
                "period_end": s.period_end,
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
    # Query for statement with eager loading of analyses
    query = (
        select(Statement)
        .where(Statement.id == statement_id)
        .options(selectinload(Statement.analyses))
    )
    result = await db.execute(query)
    statement = result.scalar_one_or_none()

    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")

    return {
        "id": statement.id,
        "filename": statement.filename,
        "file_type": statement.file_type,
        "uploaded_at": statement.uploaded_at.isoformat(),
        "transaction_count": len(statement.transactions),
        "transactions": statement.transactions,
        "account_holder": statement.account_holder,
        "account_number": statement.account_number,
        "balance": statement.balance,
        "balance_date": statement.balance_date,
        "period_start": statement.period_start,
        "period_end": statement.period_end,
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
    # Query with eager loading to avoid lazy load issues
    query = (
        select(Statement)
        .where(Statement.id == statement_id)
        .options(selectinload(Statement.analyses))
    )
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
