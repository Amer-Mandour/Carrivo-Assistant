"""
Carrivo Assistant 🚀 - FastAPI Application
Multilingual Educational Chatbot
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from .config import settings
from .database import get_supabase
from .routes.chat import router as chat_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("🚀 Starting Carrivo Assistant...")
    
    # Check database connection
    try:
        supabase = get_supabase()
        supabase.table("faq").select("count", count="exact").limit(1).execute()
        logger.info("✅ Database connected successfully")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
    
    yield
    
    logger.info("🛑 Shutting down application...")

# Create application
app = FastAPI(
    title="Carrivo Assistant - Your Personal Learning Guide",
    description="Multilingual Educational Chatbot",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(chat_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Carrivo Assistant 🚀",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/v1/chat",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """System health check"""
    try:
        supabase = get_supabase()
        # Check Supabase connection
        response = supabase.table("faq").select("count", count="exact").limit(1).execute()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )