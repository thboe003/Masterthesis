"""
FastAPI Backend for AI-Powered Pole Sport Training Plan Generator
Master's Thesis Project - Applied Artificial Intelligence
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info("Starting up FastAPI application...")
    
    # Initialize database
    from app.core.database import init_db
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application...")


# Initialize FastAPI app
app = FastAPI(
    title="Pole Sport AI Training Generator",
    description="AI-powered training plan generator for pole sport",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
from app.api import training_plans, exercises, video_analysis
app.include_router(training_plans.router)
app.include_router(exercises.router)
app.include_router(video_analysis.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Pole Sport AI Training Plan Generator",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
