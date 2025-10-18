"""
Pydantic Schemas

These models define the structure of data going in/out of our API.
They provide automatic validation and documentation.
"""

from pydantic import BaseModel


class StatementUploadResponse(BaseModel):
    """
    Response returned after uploading a bank statement PDF.

    Why use Pydantic schemas?
    - Automatic validation: Ensures data matches expected types
    - Auto-generated API docs: FastAPI uses these to build /docs
    - Type safety: Your editor knows what fields exist
    - Serialization: Converts Python objects to JSON automatically
    """

    filename: str  # Original name of the uploaded file
    extracted_text: str  # Text content extracted from the PDF
    page_count: int  # Number of pages in the PDF
    character_count: int  # Total characters extracted (useful for debugging)

    class Config:
        """
        Pydantic configuration.

        json_schema_extra provides example data shown in /docs.
        This helps you (and future API consumers) understand the response format.
        """

        json_schema_extra = {
            "example": {
                "filename": "bank_statement_january.pdf",
                "extracted_text": "BANK STATEMENT\nAccount: 1234567890\nDate: 01/01/2024\n...",
                "page_count": 3,
                "character_count": 1542,
            }
        }
