"""
Main FastAPI application entry point for Shopify AI Analytics Service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers import auth, analytics
from utils.logger import setup_logger
from models.database import Base, engine

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger()

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Shopify AI Analytics Service",
    description="AI-powered analytics service for Shopify stores using GPT-4o-mini",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(analytics.router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Shopify AI Analytics",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "shopify-ai-analytics"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
