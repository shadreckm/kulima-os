"""
Structured logging middleware with request IDs
"""
import uuid
import time
import logging
from fastapi import Request
from typing import Callable
from backend.config import settings

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """
    Middleware to add unique request IDs to all requests.
    """
    
    async def __call__(self, request: Request, call_next: Callable):
        # Generate or retrieve request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Add request ID to response header
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class StructuredLoggingMiddleware:
    """
    Middleware for structured logging of all requests and responses.
    """
    
    async def __call__(self, request: Request, call_next: Callable):
        # Get request ID
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(
            "Incoming request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2)
                },
                exc_info=True
            )
            
            raise


def setup_logging():
    """
    Configure structured logging for the application.
    """
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set more detailed format for development
    if settings.DEBUG:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
        )
