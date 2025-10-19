"""
Database Models

These classes define the structure of database tables.
SQLAlchemy will create the actual PostgreSQL tables based on these definitions.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Statement(Base):
    """
    Represents a bank statement uploaded by the user.

    Database table: 'statements'

    Stores the extracted text from the PDF, not the PDF file itself.
    One statement can have multiple analyses.
    """

    __tablename__ = "statements"

    # Primary key - auto-incrementing integer
    id = Column(Integer, primary_key=True, index=True)

    # Original filename of the uploaded PDF
    filename = Column(String(255), nullable=False)

    # Extracted text from the PDF (can be very long)
    # Text type allows unlimited length (vs String which has a max)
    extracted_text = Column(Text, nullable=False)

    # Timestamp when the statement was uploaded
    # default=datetime.utcnow means it auto-fills with current time
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship: One statement has many analyses
    # back_populates creates a two-way relationship
    # cascade="all, delete-orphan" means deleting a statement deletes its analyses
    analyses = relationship("Analysis", back_populates="statement", cascade="all, delete-orphan")

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
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key linking to the statements table
    # ForeignKey creates the relationship at the database level
    statement_id = Column(Integer, ForeignKey("statements.id"), nullable=False)

    # The prompt/question sent to Claude AI
    prompt = Column(Text, nullable=False)

    # Claude's analysis response (can be very long)
    response = Column(Text, nullable=False)

    # When this analysis was created
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship: Each analysis belongs to one statement
    # back_populates links to Statement.analyses
    statement = relationship("Statement", back_populates="analyses")

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<Analysis(id={self.id}, statement_id={self.statement_id})>"
