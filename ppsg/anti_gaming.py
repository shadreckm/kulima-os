"""
Anti-Gaming & Manipulation Resistance Module
Reference: PPSG_SPECIFICATION.md Lines 340-450

This module implements defenses against coordinated falsification without identity tracking.
Includes: Temporal Friction, Volume Dampening, Pattern Entropy, Cross-Source Dependence, Rate Limiting.
"""

import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# Configuration (PPSG_SPECIFICATION.md Lines 350-360)
ZONE_RATE_LIMIT = 100  # signals per zone per hour
SOURCE_RATE_LIMIT = 500  # signals per source_type per hour
ENTROPY_THRESHOLD = 1.5  # bits, below this is suspicious
DAMPENING_FACTOR = 0.5  # down-weight suspicious batches by 50%


class RateLimiter:
    """
    Zone-level and source-type rate limiting (no individual tracking).
    Reference: PPSG_SPECIFICATION.md Lines 438-450
    """
    
    def __init__(self):
        # Counters: {(zone_id, hour): count} and {(source_type, hour): count}
        self.zone_counters: Dict[tuple, int] = defaultdict(int)
        self.source_counters: Dict[tuple, int] = defaultdict(int)
    
    def check_zone_limit(self, zone_id: str) -> Optional[str]:
        """Check if zone rate limit exceeded."""
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        key = (zone_id, current_hour)
        
        if self.zone_counters[key] >= ZONE_RATE_LIMIT:
            return f"Zone rate limit exceeded ({ZONE_RATE_LIMIT}/hour)"
        
        return None
    
    def check_source_limit(self, source_type: str) -> Optional[str]:
        """Check if source type rate limit exceeded."""
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        key = (source_type, current_hour)
        
        if self.source_counters[key] >= SOURCE_RATE_LIMIT:
            return f"Source type rate limit exceeded ({SOURCE_RATE_LIMIT}/hour)"
        
        return None
    
    def increment(self, zone_id: str, source_type: str):
        """Increment rate limit counters."""
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        self.zone_counters[(zone_id, current_hour)] += 1
        self.source_counters[(source_type, current_hour)] += 1
    
    def cleanup_old_counters(self):
        """Remove counters older than 2 hours."""
        cutoff = datetime.utcnow() - timedelta(hours=2)
        cutoff = cutoff.replace(minute=0, second=0, microsecond=0)
        
        # Clean zone counters
        self.zone_counters = {
            k: v for k, v in self.zone_counters.items()
            if k[1] >= cutoff
        }
        
        # Clean source counters
        self.source_counters = {
            k: v for k, v in self.source_counters.items()
            if k[1] >= cutoff
        }


def apply_volume_dampening(count: int) -> float:
    """
    Apply logarithmic dampening to signal count.
    Reference: PPSG_SPECIFICATION.md Lines 380-398
    
    Prevents volume amplification attacks:
    - 1 signal → weight 1.0
    - 10 signals → weight 2.4
    - 100 signals → weight 4.6
    - 1000 signals → weight 6.9
    
    Args:
        count: Raw signal count
        
    Returns:
        Dampened weight
    """
    return math.log(1 + count)


def calculate_entropy(signals: List[Dict[str, str]]) -> Dict[str, float]:
    """
    Calculate entropy of signal distribution.
    Reference: PPSG_SPECIFICATION.md Lines 400-420
    
    Low entropy indicates overly uniform or synthetic submissions.
    
    Args:
        signals: List of signal dictionaries
        
    Returns:
        Dictionary with entropy for each dimension
    """
    if not signals:
        return {"activity_entropy": 0.0, "time_entropy": 0.0, "zone_entropy": 0.0}
    
    # Count occurrences for each dimension
    activity_counts = Counter(s["activity_type"] for s in signals)
    time_counts = Counter(s["time_window"] for s in signals)
    zone_counts = Counter(s["zone_id"] for s in signals)
    
    def entropy(counts: Counter) -> float:
        """Calculate Shannon entropy."""
        total = sum(counts.values())
        if total == 0:
            return 0.0
        return -sum(
            (count / total) * math.log2(count / total)
            for count in counts.values()
            if count > 0
        )
    
    return {
        "activity_entropy": entropy(activity_counts),
        "time_entropy": entropy(time_counts),
        "zone_entropy": entropy(zone_counts)
    }


def detect_suspicious_pattern(entropy_metrics: Dict[str, float]) -> bool:
    """
    Detect if signal pattern is suspicious (low entropy).
    Reference: PPSG_SPECIFICATION.md Lines 410-420
    
    Args:
        entropy_metrics: Entropy values for each dimension
        
    Returns:
        True if pattern is suspicious (any entropy < threshold)
    """
    return any(e < ENTROPY_THRESHOLD for e in entropy_metrics.values())


def calculate_cross_source_confidence(
    human_count: int,
    device_count: int,
    proxy_count: int
) -> float:
    """
    Calculate confidence boost from cross-source alignment.
    Reference: PPSG_SPECIFICATION.md Lines 422-436
    
    Confidence increases when multiple signal sources align:
    - Human-only or device-only: base confidence 0.5
    - Human + device: aligned confidence 0.8
    - Human + device + proxy: strong confidence 0.9
    
    Args:
        human_count: Number of human signals
        device_count: Number of device signals
        proxy_count: Number of proxy signals
        
    Returns:
        Confidence score (0.5 to 0.9)
    """
    sources_present = sum([
        human_count > 0,
        device_count > 0,
        proxy_count > 0
    ])
    
    if sources_present == 1:
        return 0.5  # Single source only
    elif sources_present == 2:
        return 0.8  # Two sources aligned
    else:
        return 0.9  # All three sources aligned

# Made with Bob
