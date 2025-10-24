"""
Database Configuration

This module sets up SQLAlchemy for async PostgreSQL operations.
It provides the database engine and session management for the application.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from app.config import get_settings

engine = None
AsyncSessionLocal = None


def init_db() -> None:
    """
    Initialize database engine and session factory.

    Uses configuration from app.config.get_settings().
    """
    global engine, AsyncSessionLocal

    settings = get_settings()

    engine = create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        future=True,
    )

    # Create async session factory
    # expire_on_commit=False prevents objects from being expired after commit
    # This is important for async sessions to avoid extra queries
    AsyncSessionLocal = async_sessionmaker(
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
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Auto-commit if no errors
        except Exception:
            await session.rollback()  # Rollback on errors
            raise
        finally:
            await session.close()
