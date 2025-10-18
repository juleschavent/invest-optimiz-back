# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack
- **Framework**: FastAPI (Python 3.13+)
- **Server**: uvicorn with hot-reload
- **Database**: PostgreSQL with SQLAlchemy ORM (planned)
- **PDF Processing**: pdfplumber (planned)
- **AI Integration**: Anthropic Python SDK (planned)

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
├── main.py              # FastAPI app with CORS for frontend (ports 5173-5175)
├── routes/              # API endpoint routers
│   └── test.py         # Example: /tests/test endpoint
└── services/            # Business logic layer
    └── test_service.py # Example service
```

### Planned Structure (from project spec)
```
app/
├── main.py
├── database.py          # SQLAlchemy setup & session management
├── models.py            # Database models (Statement, Analysis tables)
├── schemas.py           # Pydantic request/response models
├── routes/
│   ├── statements.py    # Statement upload & retrieval endpoints
│   └── analyses.py      # Analysis creation & retrieval endpoints
└── services/
    ├── pdf_parser.py    # Extract text from PDFs using pdfplumber
    └── claude_service.py # Call Claude API with statement data
```

### Design Patterns

**Service Layer Pattern**: All business logic lives in `services/`, while `routes/` handle only HTTP concerns (validation, status codes, etc.)

**Async-first**: All route handlers and service methods use `async`/`await` for non-blocking I/O operations.

**Type Safety**: Heavy use of type hints throughout. Pydantic schemas validate all request/response data.

### CORS Configuration
The API is configured to accept requests from:
- `http://localhost:5173` (Vite default)
- `http://localhost:5174`
- `http://localhost:5175` (current frontend port)

When adding new origins, update `app/main.py:15-19`.

## Database (Planned)

### Models
- **Statement**: Stores filename, extracted text (not PDF itself), upload timestamp
- **Analysis**: Stores Claude prompt, response, and creation timestamp with foreign key to Statement

### Migrations
Will use Alembic for schema migrations once database is added.

## Environment Variables

Create a `.env` file (not in version control):
```
DATABASE_URL=postgresql://user:password@localhost/bankstatements
ANTHROPIC_API_KEY=your_api_key_here
```

Load with `python-dotenv` in `app/main.py`.

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

## Project Context

This is a **learning project** focused on:
- Full-stack development fundamentals
- AI API integration
- Building a personal finance tool

**Not** production-ready - runs locally only, no authentication, no deployment planned initially.
