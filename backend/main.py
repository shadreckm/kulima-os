"""
Kulima OS Backend API - Main Application
FastAPI application for coordination intelligence API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.config import settings
from backend.api import signals, summaries, prospectus, health, twilio, system, visualization, recent_signals, zones, reports
from backend.middleware.logging import setup_logging, RequestIDMiddleware, StructuredLoggingMiddleware
from backend.middleware.rate_limiter import rate_limit_middleware
from backend.middleware.error_handler import setup_error_handlers
from backend.database.connection import init_db
from backend.services.cache import cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    setup_logging()
    logging.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize database
    try:
        init_db()
    except Exception as e:
        logging.critical(f"Lifespan database initialization critical failure: {e}")
    
    # Store settings in app state
    app.state.settings = settings
    app.state.cache = cache
    
    logging.info("Application startup complete")
    yield
    # Shutdown
    logging.info("Application shutdown")


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

# Add custom middleware (order matters!)
app.middleware("http")(RequestIDMiddleware())
app.middleware("http")(StructuredLoggingMiddleware())
app.middleware("http")(rate_limit_middleware)

# Setup error handlers
setup_error_handlers(app)

# Include routers
app.include_router(health.router, prefix=settings.API_PREFIX, tags=["Health"])
app.include_router(signals.router, prefix=settings.API_PREFIX, tags=["Signals"])
app.include_router(recent_signals.router, prefix=settings.API_PREFIX, tags=["Signals"])
app.include_router(reports.router, prefix=settings.API_PREFIX, tags=["Reports"])
app.include_router(summaries.router, prefix=settings.API_PREFIX, tags=["Summaries"])
app.include_router(zones.router, prefix=settings.API_PREFIX, tags=["Zones"])
app.include_router(prospectus.router, prefix=settings.API_PREFIX, tags=["Prospectus"])
app.include_router(twilio.router, prefix=settings.API_PREFIX, tags=["Twilio"])
app.include_router(system.router, prefix=settings.API_PREFIX, tags=["System"])
app.include_router(visualization.router, prefix=settings.API_PREFIX, tags=["Visualization"])


@app.get("/health")
async def root_health():
    """Simple health check endpoint returning OK or DB_CONNECTED"""
    from backend.database import connection
    from sqlalchemy import text
    
    db_status = "unhealthy"
    try:
        with connection.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "DB_CONNECTED"
    except Exception as e:
        logging.error(f"Root health check database connection failed: {e}")
        db_status = f"error: {str(e)}"
        
    status = "OK" if db_status == "DB_CONNECTED" else "DEGRADED"
    return {
        "status": status,
        "database": db_status
    }


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
