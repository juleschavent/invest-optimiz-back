# Backend Development Guide

## Tech Stack
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **PDF Processing**: pdfplumber
- **AI Integration**: Anthropic Python SDK (Claude API)

## Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # Database connection & session
│   ├── models.py            # SQLAlchemy models (database tables)
│   ├── schemas.py           # Pydantic schemas (request/response validation)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── statements.py    # Statement endpoints
│   │   └── analyses.py      # Analysis endpoints
│   └── services/
│       ├── __init__.py
│       ├── pdf_parser.py    # PDF extraction logic
│       └── claude_service.py # Claude API integration
├── alembic/                 # Database migrations
├── requirements.txt
└── .env                     # Environment variables
```

## Code Guidelines

### Always use modern Python and FastAPI best practices
- Use async/await for all routes and database operations
- Leverage Python type hints throughout
- Follow FastAPI's dependency injection patterns
- Use Pydantic for data validation

### API Design
Build clear, RESTful endpoints with proper status codes and error handling.

## Core Services

### Claude Service
- Format statement data into prompt
- Call Anthropic API
- Return Claude's analysis

## Environment Variables (.env)

```
DATABASE_URL=postgresql://user:password@localhost/bankstatements
ANTHROPIC_API_KEY=your_api_key_here
```
