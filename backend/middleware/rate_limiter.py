"""
Rate limiting middleware for API endpoints
Uses in-memory storage for simplicity (no Redis required)
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta
import time
import logging
from backend.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.
    
    Tracks request counts per IP address within a time window.
    """
    
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        # Store request timestamps per IP: {ip: [timestamp1, timestamp2, ...]}
        self.requests = defaultdict(list)
        # Whitelist for local development
        self.whitelist = {"127.0.0.1", "localhost", "::1"}
    
    def is_allowed(self, ip: str) -> bool:
        """
        Check if request from IP is allowed based on rate limit.
        
        Args:
            ip: Client IP address
            
        Returns:
            True if allowed, False otherwise
        """
        # Skip rate limiting for whitelisted IPs
        if ip in self.whitelist or settings.DEBUG:
            return True
        
        now = time.time()
        window_start = now - 60  # 1 minute window
        
        # Remove old requests outside the window
        self.requests[ip] = [
            timestamp for timestamp in self.requests[ip]
            if timestamp > window_start
        ]
        
        # Check if under limit
        if len(self.requests[ip]) < self.requests_per_minute:
            self.requests[ip].append(now)
            return True
        
        return False
    
    def get_remaining_requests(self, ip: str) -> int:
        """
        Get remaining requests for IP within current window.
        
        Args:
            ip: Client IP address
            
        Returns:
            Number of remaining requests
        """
        if ip in self.whitelist or settings.DEBUG:
            return self.requests_per_minute
        
        now = time.time()
        window_start = now - 60
        self.requests[ip] = [
            timestamp for timestamp in self.requests[ip]
            if timestamp > window_start
        ]
        
        return max(0, self.requests_per_minute - len(self.requests[ip]))


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)


async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware for rate limiting.
    
    Args:
        request: Incoming request
        call_next: Next middleware/route handler
        
    Returns:
        Response or rate limit error
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit
    if not rate_limiter.is_allowed(client_ip):
        remaining = rate_limiter.get_remaining_requests(client_ip)
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        
        return JSONResponse(
            status_code=429,
            content={
                "status": "error",
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "details": {
                    "limit": settings.RATE_LIMIT_PER_MINUTE,
                    "remaining": remaining,
                    "window": "1 minute"
                }
            }
        )
    
    # Add rate limit headers to response
    response = await call_next(request)
    remaining = rate_limiter.get_remaining_requests(client_ip)
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Window"] = "1 minute"
    
    return response
