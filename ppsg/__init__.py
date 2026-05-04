"""
Privacy-Preserving Signal Gateway (PPSG) for KULIMA OS
Reference Implementation

This package implements a production-faithful reference implementation
of the PPSG specification (PPSG_SPECIFICATION.md).

Components:
- gateway.py: Main FastAPI gateway with three endpoints
- pii_filter.py: PII detection and granularity validation
- anti_gaming.py: Anti-gaming and manipulation resistance
- batch_processor.py: Ephemeral buffer and batch processing

Invariants Enforced:
- Zero-PII: No personal identifiers accepted or stored
- Temporal Moat: 6-hour batch windows, no real-time processing
- Strict Schema: Only four fields allowed, no extras
- Rate Limiting: Zone-level and source-type limits (no individual tracking)
- Guaranteed Deletion: Raw signals deleted after batch handoff
"""

__version__ = "1.0.0"
__author__ = "KULIMA OS Team"

from .gateway import app, run_gateway
from .pii_filter import detect_pii
from .anti_gaming import RateLimiter, apply_volume_dampening
from .batch_processor import EphemeralBuffer

__all__ = [
    "app",
    "run_gateway",
    "detect_pii",
    "RateLimiter",
    "apply_volume_dampening",
    "EphemeralBuffer"
]

# Made with Bob
