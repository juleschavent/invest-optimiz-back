from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Bank Statement Analyzer API",
    description="API for analyzing bank statements using Claude AI",
    version="1.0.0"
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


@app.get("/")
def read_root():
    """Root endpoint - API health check"""
    return {
        "message": "Bank Statement Analyzer API is running!",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/test")
def test_endpoint():
    """Test endpoint to verify API is working"""
    return {
        "message": "API is working!",
        "data": {"test": True}
    }
