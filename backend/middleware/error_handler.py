"""
Centralized error handling middleware
Provides consistent error responses across all endpoints
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
import uuid

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Centralized error handler for consistent error responses.
    """
    
    @staticmethod
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Handle HTTP exceptions.
        """
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger.error(
            f"HTTP exception: {exc.status_code} - {exc.detail}",
            extra={"request_id": request_id, "path": request.url.path}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error": "http_error",
                "message": exc.detail,
                "request_id": request_id
            }
        )
    
    @staticmethod
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Handle request validation errors.
        """
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger.warning(
            f"Validation error: {exc.errors()}",
            extra={"request_id": request_id, "path": request.url.path}
        )
        
        # Extract first error for user-friendly message
        error_details = exc.errors()
        first_error = error_details[0] if error_details else {}
        
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "error": "validation_error",
                "message": f"Invalid input: {first_error.get('msg', 'Unknown validation error')}",
                "details": error_details,
                "request_id": request_id
            }
        )
    
    @staticmethod
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        """
        Handle database errors.
        """
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger.error(
            f"Database error: {str(exc)}",
            extra={"request_id": request_id, "path": request.url.path},
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "database_error",
                "message": "A database error occurred. Please try again later.",
                "request_id": request_id
            }
        )
    
    @staticmethod
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Handle all other exceptions.
        """
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger.error(
            f"Unhandled exception: {str(exc)}",
            extra={"request_id": request_id, "path": request.url.path},
            exc_info=True
        )
        
        # Don't expose stack traces in production
        message = "An unexpected error occurred. Please try again later."
        if request.app.state.settings.DEBUG:
            message = f"Unexpected error: {str(exc)}"
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "internal_error",
                "message": message,
                "request_id": request_id
            }
        )


def setup_error_handlers(app):
    """
    Register all error handlers with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(HTTPException, ErrorHandler.http_exception_handler)
    app.add_exception_handler(RequestValidationError, ErrorHandler.validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, ErrorHandler.database_exception_handler)
    app.add_exception_handler(Exception, ErrorHandler.general_exception_handler)
