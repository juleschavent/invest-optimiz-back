"""
Database Models

These classes define the structure of database tables.
SQLAlchemy will create the actual PostgreSQL tables based on these definitions.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Statement(Base):
    """
    Represents a bank statement uploaded by the user.

    Database table: 'statements'

    Stores both the raw CSV content and parsed transaction data.
    One statement can have multiple analyses.
    """

    __tablename__ = "statements"

    # Primary key - auto-incrementing integer
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Original filename of the uploaded file
    filename: Mapped[str] = mapped_column(String(255))

    # File type (currently only 'csv')
    file_type: Mapped[str] = mapped_column(String(10), default="csv")

    # Raw CSV content (can be very long)
    # Text type allows unlimited length (vs String which has a max)
    raw_data: Mapped[str] = mapped_column(Text)

    # Parsed transactions as JSON array
    # JSONB type in PostgreSQL allows efficient querying and indexing
    # Stores list of dicts: [{date, description, debit, credit}, ...]
    transactions: Mapped[list[dict[str, Any]]] = mapped_column(JSON)

    # Timestamp when the statement was uploaded
    # server_default uses database function for timezone-aware timestamps
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship: One statement has many analyses
    # back_populates creates a two-way relationship
    # cascade="all, delete-orphan" means deleting a statement deletes its analyses
    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="statement", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<Statement(id={self.id}, filename='{self.filename}')>"


class Analysis(Base):
    """
    Represents an AI analysis of a bank statement.

    Database table: 'analyses'

    Stores the prompt sent to Claude and the response received.
    Multiple analyses can be created for the same statement.
    """

    __tablename__ = "analyses"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key linking to the statements table
    # ForeignKey creates the relationship at the database level
    statement_id: Mapped[int] = mapped_column(ForeignKey("statements.id"))

    # The prompt/question sent to Claude AI
    prompt: Mapped[str] = mapped_column(Text)

    # Claude's analysis response (can be very long)
    response: Mapped[str] = mapped_column(Text)

    # When this analysis was created
    # server_default uses database function for timezone-aware timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship: Each analysis belongs to one statement
    # back_populates links to Statement.analyses
    statement: Mapped["Statement"] = relationship(back_populates="analyses")

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<Analysis(id={self.id}, statement_id={self.statement_id})>"
