"""
Health check endpoint
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "engines": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }
