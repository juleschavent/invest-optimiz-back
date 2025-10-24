from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.exception_handlers import app_exception_handler, generic_exception_handler
from app.exceptions import AppException
from app.logger import get_logger, setup_logging
from app.routes import statements

# Get settings (this will load from .env automatically via pydantic-settings)
settings = get_settings()

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan event handler for FastAPI app.

    Runs on startup and shutdown to manage resources.
    This is the modern way (replaces @app.on_event decorators).
    """
    # Startup: Initialize database
    logger.info("Starting up application...")

    # Import database module (not the engine directly)
    import app.database as db

    # Initialize database (this creates the engine)
    db.init_db()
    logger.info("Database engine initialized")

    # Test database connection
    try:
        if db.engine is None:
            raise RuntimeError("Database engine not initialized")
        async with db.engine.begin() as conn:
            # Execute a simple query to verify the connection works
            result = await conn.execute(text("SELECT 1"))
            result.close()
            logger.info("Database connection test successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        raise

    yield  # Application runs here

    # Shutdown: Close database connections
    logger.info("Shutting down application...")
    if db.engine:
        await db.engine.dispose()
        logger.info("Database connections closed")


app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
)

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Configure CORS to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


app.include_router(statements.router)
