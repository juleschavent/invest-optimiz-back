"""
Database Configuration

This module sets up SQLAlchemy for async PostgreSQL operations.
It provides the database engine and session management for the application.
"""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment variable
# Note: load_dotenv() must be called before importing this module
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Create async engine
# Will fail with clear error if DATABASE_URL is empty
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
)

# Create async session factory
# expire_on_commit=False prevents objects from being expired after commit
# This is important for async sessions to avoid extra queries
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for all database models
# All your models (Statement, Analysis) will inherit from this
Base = declarative_base()


# Dependency for FastAPI routes
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a database session to FastAPI route handlers.

    Usage in routes:
        @router.get("/statements")
        async def get_statements(db: AsyncSession = Depends(get_db)):
            # use db here

    The session is automatically closed after the request completes.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Auto-commit if no errors
        except Exception:
            await session.rollback()  # Rollback on errors
            raise
        finally:
            await session.close()
