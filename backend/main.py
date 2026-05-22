"""
Kulima OS Backend API - Main Application
FastAPI application for coordination intelligence API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.config import settings
from backend.api import signals, summaries, prospectus, health, twilio, system


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    yield
    # Shutdown


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for Kulima OS coordination intelligence system",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.API_PREFIX, tags=["Health"])
app.include_router(signals.router, prefix=settings.API_PREFIX, tags=["Signals"])
app.include_router(summaries.router, prefix=settings.API_PREFIX, tags=["Summaries"])
app.include_router(prospectus.router, prefix=settings.API_PREFIX, tags=["Prospectus"])
app.include_router(twilio.router, prefix=settings.API_PREFIX, tags=["Twilio"])
app.include_router(system.router, prefix=settings.API_PREFIX, tags=["System"])


@app.get("/")
async def root():
    """Root endpoint with system identity"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "type": "coordination-first infrastructure planning system",
        "description": "A coordination-first infrastructure planning system that transforms real-world activity into decision-grade intelligence without relying on identity or assumptions.",
        "docs": "/docs",
        "api_prefix": settings.API_PREFIX,
        "system_info": "/api/system/info"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
