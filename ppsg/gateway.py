"""
Privacy-Preserving Signal Gateway (PPSG) - Main Gateway
Reference: PPSG_SPECIFICATION.md

This is the main API gateway implementing three endpoints:
- POST /signal/submit
- GET /health
- GET /zones

Implements Zero-PII enforcement, strict schema validation, and anti-gaming defenses.
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import Literal, Dict
from datetime import datetime
import uvicorn

from .pii_filter import detect_pii, validate_temporal_coarseness, validate_zone_precision
from .anti_gaming import RateLimiter
from .batch_processor import EphemeralBuffer


# Configuration (PPSG_SPECIFICATION.md Lines 140-180)
ALLOWED_ACTIVITY_TYPES = [
    "irrigation", "milling", "cold_storage", "welding",
    "clinic", "school", "water_system", "emergency_services"
]
ALLOWED_TIME_WINDOWS = ["morning", "afternoon", "evening"]
ALLOWED_SOURCE_TYPES = ["human", "device", "proxy"]
ZONE_WHITELIST = ["zone_a", "zone_b", "zone_c"]


# Pydantic model for strict schema validation (PPSG_SPECIFICATION.md Lines 272-290)
class SignalSubmission(BaseModel):
    """
    Strict signal schema - ONLY these four fields allowed.
    Reference: PPSG_SPECIFICATION.md Lines 140-180
    """
    activity_type: Literal[
        "irrigation", "milling", "cold_storage", "welding",
        "clinic", "school", "water_system", "emergency_services"
    ]
    time_window: Literal["morning", "afternoon", "evening"]
    zone_id: str
    signal_source_type: Literal["human", "device", "proxy"]
    
    class Config:
        # Forbid extra fields (PPSG_SPECIFICATION.md Line 175)
        extra = "forbid"
    
    @validator('zone_id')
    def validate_zone(cls, v):
        """Validate zone_id against whitelist."""
        if v not in ZONE_WHITELIST:
            raise ValueError(f"zone_id '{v}' not in approved whitelist")
        return v


# Initialize FastAPI app
app = FastAPI(
    title="PPSG - Privacy-Preserving Signal Gateway",
    description="Reference implementation of KULIMA OS signal ingestion gateway",
    version="1.0.0"
)

# Initialize global state (in-memory only)
rate_limiter = RateLimiter()
ephemeral_buffer = EphemeralBuffer()


@app.post("/signal/submit", status_code=status.HTTP_202_ACCEPTED)
async def submit_signal(signal: SignalSubmission):
    """
    Submit coordination signal.
    Reference: PPSG_SPECIFICATION.md Lines 522-570
    
    Accepts ONLY the four required fields. Rejects any extra fields.
    Enforces Zero-PII, validates schema, applies rate limiting.
    
    Returns:
        202 Accepted on success
        400 Bad Request on PII/schema/zone violation
        429 Too Many Requests on rate limit exceeded
    """
    # Convert to dict for processing
    signal_dict = signal.dict()
    
    # Step 1: PII Detection (PPSG_SPECIFICATION.md Lines 182-230)
    pii_error = detect_pii(signal_dict)
    if pii_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PII_DETECTED",
                "message": "Signal contains prohibited personal identifiers",
                "detail": pii_error
            }
        )
    
    # Step 2: Temporal Coarseness Validation
    temporal_error = validate_temporal_coarseness(signal_dict["time_window"])
    if temporal_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "SCHEMA_VIOLATION",
                "message": "Signal contains invalid or additional fields",
                "detail": temporal_error
            }
        )
    
    # Step 3: Zone Precision Validation
    zone_error = validate_zone_precision(signal_dict["zone_id"])
    if zone_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_ZONE",
                "message": "Zone ID validation failed",
                "detail": zone_error
            }
        )
    
    # Step 4: Rate Limiting (PPSG_SPECIFICATION.md Lines 438-450)
    zone_limit_error = rate_limiter.check_zone_limit(signal_dict["zone_id"])
    if zone_limit_error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": zone_limit_error,
                "retry_after": 3600
            }
        )
    
    source_limit_error = rate_limiter.check_source_limit(signal_dict["signal_source_type"])
    if source_limit_error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": source_limit_error,
                "retry_after": 3600
            }
        )
    
    # Step 5: Add to ephemeral buffer (PPSG_SPECIFICATION.md Lines 272-290)
    ephemeral_buffer.add_signal(signal_dict)
    
    # Step 6: Increment rate limit counters
    rate_limiter.increment(signal_dict["zone_id"], signal_dict["signal_source_type"])
    
    # Step 7: Cleanup old rate limit counters
    rate_limiter.cleanup_old_counters()
    
    # Step 8: Check if batch should be processed
    if ephemeral_buffer.should_process_batch():
        batch_result = ephemeral_buffer.process_batch()
        print(f"[BATCH PROCESSED] {batch_result['batch_size']} signals aggregated")
    
    # Step 9: Return success (no unique submission ID)
    batch_window = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    batch_window = batch_window.replace(
        hour=(batch_window.hour // 6) * 6
    )
    
    return {
        "status": "queued",
        "batch_window": batch_window.isoformat() + "Z"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Reference: PPSG_SPECIFICATION.md Lines 572-584
    
    Returns operational metrics only (no sensitive data).
    """
    stats = ephemeral_buffer.get_stats()
    
    return {
        "status": "healthy",
        "buffer_size": stats["buffer_size"],
        "last_batch_handoff": stats["last_batch_handoff"]
    }


@app.get("/zones")
async def get_zones():
    """
    Get approved zone whitelist.
    Reference: PPSG_SPECIFICATION.md Lines 586-600
    
    Returns public zone information (no privacy concerns).
    """
    return {
        "zones": [
            {"id": "zone_a", "type": "rural_agricultural"},
            {"id": "zone_b", "type": "peri_urban"},
            {"id": "zone_c", "type": "informal_settlement"}
        ]
    }


@app.on_event("startup")
async def startup_event():
    """Initialize gateway on startup."""
    print("[PPSG] Privacy-Preserving Signal Gateway started")
    print("[PPSG] Zero-PII enforcement active")
    print("[PPSG] Temporal Moat: 6-hour batch windows")
    print("[PPSG] Rate limiting: 100/hour per zone, 500/hour per source_type")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("[PPSG] Gateway shutting down")
    print("[PPSG] Ephemeral buffer will be cleared (no persistence)")


def run_gateway(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the PPSG gateway.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_gateway()

