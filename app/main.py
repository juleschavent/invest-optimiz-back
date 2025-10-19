from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.routes import statements, test

# Load environment variables from .env file
# This must happen BEFORE importing database.py (which reads DATABASE_URL)
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI app.

    Runs on startup and shutdown to manage resources.
    This is the modern way (replaces @app.on_event decorators).
    """
    # Startup: Initialize database
    print("🚀 Starting up...")

    # Import database module (not the engine directly)
    import app.database as db

    # Initialize database (this creates the engine)
    db.init_db()

    # Test database connection
    try:
        async with db.engine.begin() as conn:
            print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise

    yield  # Application runs here

    # Shutdown: Close database connections
    print("👋 Shutting down...")
    if db.engine:
        await db.engine.dispose()
        print("✅ Database connections closed")


app = FastAPI(
    title="Bank Statement Analyzer API",
    description="API for analyzing bank statements using Claude AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default port
        "http://localhost:5174",
        "http://localhost:5175",  # Our frontend is running on this
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


app.include_router(test.router)
app.include_router(statements.router)

# Import db_test AFTER load_dotenv() has been called
from app.routes import db_test
app.include_router(db_test.router)
