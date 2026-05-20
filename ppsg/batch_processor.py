"""
Batch Processor Module
Reference: PPSG_SPECIFICATION.md Lines 452-520

Handles ephemeral buffer, deduplication, batch handoff, and guaranteed deletion.
Implements Temporal Moat and guaranteed raw signal deletion.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

from .anti_gaming import (
    apply_volume_dampening,
    calculate_entropy,
    detect_suspicious_pattern,
    calculate_cross_source_confidence,
    DAMPENING_FACTOR
)


# Configuration (PPSG_SPECIFICATION.md Lines 272-280)
BUFFER_TTL_HOURS = 2
BATCH_WINDOW_HOURS = 6


class EphemeralBuffer:
    """
    Ephemeral intake buffer with TTL and guaranteed deletion.
    Reference: PPSG_SPECIFICATION.md Lines 272-338
    """
    
    def __init__(self):
        # Buffer stores: [(signal_dict, timestamp, ttl), ...]
        self.buffer: List[Tuple[Dict[str, str], datetime, datetime]] = []
        self.last_batch_handoff: datetime = datetime.utcnow()
    
    def add_signal(self, signal: Dict[str, str]):
        """
        Add signal to buffer with TTL.
        Reference: PPSG_SPECIFICATION.md Lines 282-290
        """
        now = datetime.utcnow()
        ttl = now + timedelta(hours=BUFFER_TTL_HOURS)
        self.buffer.append((signal, now, ttl))
    
    def cleanup_expired(self):
        """
        Remove signals that have exceeded TTL.
        Reference: PPSG_SPECIFICATION.md Lines 292-296
        """
        now = datetime.utcnow()
        self.buffer = [
            (sig, ts, ttl) for sig, ts, ttl in self.buffer
            if ttl > now
        ]
    
    def get_buffer_size(self) -> int:
        """Get current buffer size."""
        return len(self.buffer)
    
    def should_process_batch(self) -> bool:
        """
        Check if batch window has closed.
        Reference: PPSG_SPECIFICATION.md Lines 298-302
        """
        now = datetime.utcnow()
        elapsed = (now - self.last_batch_handoff).total_seconds() / 3600
        return elapsed >= BATCH_WINDOW_HOURS
    
    def process_batch(self) -> Dict:
        """
        Process batch: deduplicate, dampen, calculate entropy, handoff, delete.
        Reference: PPSG_SPECIFICATION.md Lines 304-338
        
        Returns:
            Batch processing results
        """
        # Step 1: Cleanup expired signals
        self.cleanup_expired()
        
        if not self.buffer:
            return {
                "batch_size": 0,
                "aggregated_signals": [],
                "entropy_metrics": {},
                "suspicious": False
            }
        
        # Step 2: Extract raw signals
        raw_signals = [sig for sig, _, _ in self.buffer]
        
        # Step 3: Deduplicate and count
        # Key: (activity_type, time_window, zone_id, signal_source_type)
        signal_counts: Dict[Tuple, Dict] = {}
        
        for sig in raw_signals:
            key = (
                sig["activity_type"],
                sig["time_window"],
                sig["zone_id"],
                sig["signal_source_type"]
            )
            if key not in signal_counts:
                signal_counts[key] = {"count": 0, "sources": defaultdict(int)}
            
            signal_counts[key]["count"] += 1
            signal_counts[key]["sources"][sig["signal_source_type"]] += 1
        
        # Step 4: Apply volume dampening
        dampened_signals = []
        for key, data in signal_counts.items():
            weight = apply_volume_dampening(data["count"])
            
            # Calculate cross-source confidence
            human_count = data["sources"].get("human", 0)
            device_count = data["sources"].get("device", 0)
            proxy_count = data["sources"].get("proxy", 0)
            confidence = calculate_cross_source_confidence(
                human_count, device_count, proxy_count
            )
            
            dampened_signals.append({
                "activity_type": key[0],
                "time_window": key[1],
                "zone_id": key[2],
                "signal_source_type": key[3],
                "weight": weight,
                "raw_count": data["count"],
                "cross_source_confidence": confidence,
                "source_breakdown": dict(data["sources"])
            })
        
        # Step 5: Calculate entropy
        entropy_metrics = calculate_entropy(raw_signals)
        
        # Step 6: Detect suspicious patterns
        suspicious = detect_suspicious_pattern(entropy_metrics)
        
        # Step 7: Down-weight if suspicious
        if suspicious:
            for sig in dampened_signals:
                sig["weight"] *= DAMPENING_FACTOR
                sig["flagged"] = "low_entropy"
        
        # Step 8: Handoff to LUMOZA (stub)
        self._handoff_to_lumoza(dampened_signals, entropy_metrics)
        
        # Step 9: DELETE raw signals (guaranteed, irreversible)
        batch_size = len(self.buffer)
        self.buffer = []  # Irreversible deletion
        self.last_batch_handoff = datetime.utcnow()
        
        return {
            "batch_size": batch_size,
            "aggregated_signals": dampened_signals,
            "entropy_metrics": entropy_metrics,
            "suspicious": suspicious
        }
    
    def _handoff_to_lumoza(self, signals: List[Dict], entropy_metrics: Dict):
        """
        Handoff aggregated signals to LUMOZA pipeline (stub).
        Reference: PPSG_SPECIFICATION.md Lines 320-330
        
        In production, this would write to a queue or call LUMOZA API.
        For reference implementation, we just log the handoff.
        """
        print(f"[BATCH HANDOFF] {len(signals)} aggregated signals → LUMOZA")
        print(f"[ENTROPY] {entropy_metrics}")
        
        # In production, this would be:
        # - Write to message queue (RabbitMQ, Kafka)
        # - Call LUMOZA HTTP API
        # - Write to shared file system
        # For now, we just demonstrate the interface
    
    def get_stats(self) -> Dict:
        """Get buffer statistics (no sensitive data)."""
        return {
            "buffer_size": len(self.buffer),
            "last_batch_handoff": self.last_batch_handoff.isoformat() + "Z"
        }

