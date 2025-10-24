# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack
- **Framework**: FastAPI (Python 3.13+)
- **Server**: uvicorn with hot-reload
- **Database**: PostgreSQL with SQLAlchemy 2.0+ (async support)
- **Configuration**: pydantic-settings for type-safe environment variables
- **PDF Processing**: pdfplumber
- **AI Integration**: Anthropic Python SDK (to be integrated)
- **Code Quality**: Ruff (formatter/linter), mypy (type checking), autopep8 (indentation)

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Run development server with hot-reload
uvicorn app.main:app --reload

# Run on specific port
uvicorn app.main:app --reload --port 8000

# Run with host binding (for network access)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with automatic API docs at `/docs`.

### Code Quality Tools
```bash
# Format code (auto-fix style issues)
ruff format app/

# Fix indentation issues (for valid but poorly indented code)
autopep8 --in-place --aggressive --aggressive app/

# Lint code (check for errors, unused imports, etc.)
ruff check app/

# Auto-fix linting issues
ruff check app/ --fix

# Type check (enforce type hints)
mypy app/
```

Configuration is in `pyproject.toml`. All functions must have type hints (enforced by mypy).

**Formatter behavior:**
- **Ruff** (primary formatter): Fast, handles valid Python code
- **autopep8**: Fixes indentation issues in valid code (e.g., 5 spaces → 4 spaces)
- Both run automatically on save in VS Code
- **Important**: Neither can fix syntax errors (invalid indentation that breaks Python parsing)

## Architecture

### Current Structure
```
app/
├── main.py                 # FastAPI app entry point with lifespan management
├── config.py               # Centralized configuration with pydantic-settings
├── logger.py               # Structured logging setup
├── database.py             # SQLAlchemy 2.0 async engine & session management
├── models.py               # Database models (Statement, Analysis) with Mapped[] types
├── schemas.py              # Pydantic request/response models with validation
├── exceptions.py           # Custom exception classes
├── exception_handlers.py   # FastAPI exception handlers
├── routes/
│   └── statements.py       # Statement CRUD endpoints
└── services/
    └── pdf_parser.py       # PDF text extraction with error handling
```

### Planned Additions
- `services/claude_service.py` - Claude API integration for analysis
- `routes/analyses.py` - Analysis-specific endpoints (if needed)

### Design Patterns

**Service Layer Pattern**: All business logic lives in `services/`, while `routes/` handle only HTTP concerns (validation, status codes, etc.)

**Async-first**: All route handlers and service methods use `async`/`await` for non-blocking I/O operations.

**Type Safety**: Heavy use of type hints throughout. Pydantic schemas validate all request/response data.

### CORS Configuration
The API is configured to accept requests from frontend ports defined in `app/config.py`:
- `http://localhost:5173` (Vite default)
- `http://localhost:5174`
- `http://localhost:5175` (current frontend port)

Update CORS origins in `app/config.py` Settings class, not directly in main.py.

## Configuration Management

All configuration is centralized in `app/config.py` using pydantic-settings:

```python
from app.config import get_settings

settings = get_settings()
print(settings.database_url)
```

**Key Features:**
- Type-safe environment variable loading
- Automatic .env file parsing
- Validation and defaults
- Cached with `@lru_cache` for performance

**Settings Available:**
- `database_url` - PostgreSQL connection string (required)
- `database_echo` - Log SQL queries (default: True)
- `api_title`, `api_description`, `api_version` - API metadata
- `cors_origins` - List of allowed frontend URLs
- `anthropic_api_key` - Claude API key (optional, for future use)
- `log_level` - Logging level (default: INFO)

See `.env.example` for all available options.

## Logging

Structured logging is configured in `app/logger.py`:

```python
from app.logger import get_logger

logger = get_logger(__name__)
logger.info("Something happened")
logger.error("Error occurred", exc_info=True)
```

**Features:**
- Consistent format: timestamp, module, level, message
- Configurable log level via settings
- Separate loggers per module
- Proper exception logging with `exc_info=True`

**Do NOT use `print()` statements** - use the logger instead.

## Error Handling

Custom exception hierarchy in `app/exceptions.py`:

```python
from app.exceptions import NotFoundError, ValidationError, PDFProcessingError

# Raise specific exceptions
raise NotFoundError("Statement not found", details={"id": statement_id})
```

**Available Exceptions:**
- `DatabaseError` - Database operation failures
- `ValidationError` - Input validation failures (→ 400)
- `NotFoundError` - Resource not found (→ 404)
- `PDFProcessingError` - PDF parsing issues (→ 422)
- `AIServiceError` - Claude API failures (→ 503)

Exception handlers automatically convert to proper HTTP responses with consistent JSON format:
```json
{
  "error": "NotFoundError",
  "message": "Statement not found",
  "details": {"id": 123}
}
```

## Database

### SQLAlchemy 2.0 Async Setup

The database uses SQLAlchemy 2.0+ with async support (`asyncpg` driver):

**Connection String Format:**
```
postgresql+asyncpg://user:password@host:port/database
```

**Key Components:**

1. **Engine Creation** (`database.py`):
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(
    database_url,
    echo=True,  # Log SQL queries
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

**Important**: Use `async_sessionmaker` (not `sessionmaker`) for async engines.

2. **Dependency Injection** (`database.py`):
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

3. **Usage in Routes**:
```python
@router.get("/statements")
async def get_statements(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Statement))
    statements = result.scalars().all()
    return statements
```

### Models (SQLAlchemy 2.0 Style)

**Use `Mapped[type]` annotations** (not `Column` directly):

```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, func

class Statement(Base):
    __tablename__ = "statements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    extracted_text: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships with type hints
    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="statement",
        cascade="all, delete-orphan"
    )
```

**Key Patterns:**
- `Mapped[int]` for required integer fields
- `Mapped[str]` for required string fields
- `Mapped[datetime]` for timestamp fields
- `Mapped[list["Analysis"]]` for one-to-many relationships
- `server_default=func.now()` for database-level timestamps (preferred over Python-level)

**Current Models:**
- **Statement**: Bank statement with filename, extracted text, upload timestamp
- **Analysis**: AI analysis with prompt, response, creation timestamp, foreign key to Statement

### Migrations

Using Alembic for schema migrations:

```bash
# Create migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Environment Variables

Create a `.env` file in the project root (not in version control).

**Use `.env.example` as a template:**
```bash
cp .env.example .env
# Then edit .env with your actual values
```

**Required Variables:**
- `DATABASE_URL` - PostgreSQL connection string (format: `postgresql+asyncpg://user:password@host:port/database`)

**Optional Variables (have defaults):**
- `DATABASE_ECHO` - Log SQL queries (default: true)
- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `ANTHROPIC_API_KEY` - Claude API key (for future use)
- `API_TITLE`, `API_DESCRIPTION`, `API_VERSION` - API metadata
- `CORS_ORIGINS` - Comma-separated list of allowed frontend URLs

**Loading:**
Environment variables are automatically loaded by `pydantic-settings` when you call `get_settings()`. No need to manually load `.env` with `python-dotenv`.

## VS Code Setup

**Required Extensions:**
- **Ruff** (charliermarsh.ruff) - Primary formatter and linter
- **Python** (ms-python.python) - Python language support
- **autopep8** (ms-python.autopep8) - Indentation fixes

With these installed and the workspace settings in `.vscode/settings.json`, you get:
- Auto-format on save (Ruff)
- Auto-organize imports on save
- Auto-fix linting issues on save
- Auto-fix indentation in valid code (autopep8 with --aggressive)
- Type checking in the editor

**What auto-fixes on save:**
- ✅ Import sorting and organization
- ✅ Spacing, quotes, line length
- ✅ Unused imports removal
- ✅ Wrong indentation in valid code (5 spaces → 4 spaces)
- ❌ Syntax errors (you must fix these manually first)

## Best Practices

### Code Quality Standards

1. **Type Hints Required**
   - All functions MUST have complete type hints (enforced by mypy)
   - Use `Mapped[type]` for SQLAlchemy models
   - Use `-> dict[str, Any]` or specific return types for routes

2. **Async-First**
   - All route handlers use `async def`
   - Database operations use `await`
   - Use `AsyncSession` for database access

3. **Error Handling**
   - Use custom exception classes from `app.exceptions`
   - Never raise generic `Exception` - use specific types
   - Include helpful error messages and details dict

4. **Logging**
   - Use `get_logger(__name__)` in every module
   - Never use `print()` statements
   - Use appropriate levels: `.debug()`, `.info()`, `.warning()`, `.error()`
   - Include `exc_info=True` when logging exceptions

5. **Configuration**
   - All settings in `app/config.py`
   - Never hardcode values in code
   - Use `get_settings()` to access configuration

6. **Validation**
   - Use Pydantic schemas for all API inputs/outputs
   - Use `Field()` for validation (gt, ge, min_length, etc.)
   - Document fields with descriptions

7. **Database Patterns**
   - Use `Mapped[type]` annotations (SQLAlchemy 2.0)
   - Use `async_sessionmaker` (not `sessionmaker`)
   - Prefer `server_default=func.now()` over Python defaults
   - Always use `select()` queries (not legacy query API)

### Code Organization

- **Routes** (`routes/`) - HTTP layer only (parsing, validation, status codes)
- **Services** (`services/`) - Business logic, external API calls, complex operations
- **Models** (`models.py`) - Database schema definitions
- **Schemas** (`schemas.py`) - API request/response structures
- **Exceptions** (`exceptions.py`) - Custom error types

### Testing Checklist

Before committing:
1. Run `ruff format app/` - auto-format code
2. Run `ruff check app/ --fix` - fix linting issues
3. Run `mypy app/` - verify type hints
4. Check VSCode for any remaining diagnostics
5. Test endpoints manually via `/docs`

## Project Context

This is a **learning project** focused on:
- Full-stack development fundamentals
- Python/FastAPI best practices
- SQLAlchemy 2.0 async patterns
- AI API integration
- Building a personal finance tool

**Status:** In development - runs locally, no authentication, no deployment planned initially.

**What We've Learned:**
- Modern async Python with FastAPI
- SQLAlchemy 2.0 type-safe patterns
- Structured logging and error handling
- Configuration management with pydantic-settings
- Type-driven development with mypy
