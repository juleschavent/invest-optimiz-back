from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import test

app = FastAPI(
    title="Bank Statement Analyzer API",
    description="API for analyzing bank statements using Claude AI",
    version="1.0.0",
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
