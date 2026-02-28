"""FastAPI application initialization and configuration."""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .middleware.error_handler import ErrorHandlerMiddleware
from .middleware.rate_limiter import RateLimitMiddleware

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FarmOps Location-Based Insights Engine",
    description="AI-powered agricultural insights for Tamil Nadu farmers",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
)

# Register API routes
app.include_router(api_router)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "service": "FarmOps Location-Based Insights Engine",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT", "development") == "development",
    )
