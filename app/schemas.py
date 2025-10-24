"""
Pydantic Schemas

These models define the structure of data going in/out of our API.
They provide automatic validation and documentation.
"""

from pydantic import BaseModel, ConfigDict, Field


class StatementUploadResponse(BaseModel):
    """
    Response returned after uploading a bank statement PDF.

    Why use Pydantic schemas?
    - Automatic validation: Ensures data matches expected types
    - Auto-generated API docs: FastAPI uses these to build /docs
    - Type safety: Your editor knows what fields exist
    - Serialization: Converts Python objects to JSON automatically
    """

    filename: str = Field(..., description="Original name of the uploaded file")
    extracted_text: str = Field(..., description="Text content extracted from the PDF")
    page_count: int = Field(..., gt=0, description="Number of pages in the PDF")
    character_count: int = Field(
        ..., ge=0, description="Total characters extracted (useful for debugging)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "bank_statement_january.pdf",
                "extracted_text": "BANK STATEMENT\nAccount: 1234567890\nDate: 01/01/2024\n...",
                "page_count": 3,
                "character_count": 1542,
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str = Field(..., description="Error type/category")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, str | int | bool] = Field(
        default_factory=dict, description="Additional error details"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "message": "Invalid file format",
                "details": {"allowed_formats": ["pdf"]},
            }
        }
    )


class HealthCheckResponse(BaseModel):
    """Health check endpoint response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "database": "connected",
            }
        }
    )
