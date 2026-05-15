"""
LUMOZA Integration Layer

Bridges WhatsApp input signals with LUMOZA processing pipeline.
Converts stored WhatsApp signals into LUMOZA coordination patterns.
"""

from typing import List, Dict, Optional
from signal_storage import get_unprocessed_signals, Signal, default_storage
from datetime import datetime


class LumozaIntegration:
    """
    Integrates WhatsApp signals with LUMOZA pipeline.
    
    Takes stored signals from WhatsApp and converts them into
    LUMOZA coordination patterns for processing.
    """
    
    def __init__(self):
        self.frequency_to_cycles = {
            "daily": 7,
            "weekly": 1,
            "monthly": 0.25,
            "seasonal": 0.05,
            "unknown": 0.5
        }
    
    def convert_to_lumoza_patterns(self, zone: Optional[str] = None, mark_processed: bool = False) -> List[Dict]:
        """
        Convert WhatsApp signals into LUMOZA coordination patterns.
        
        Args:
            zone: Optional zone filter
            mark_processed: Whether to mark signals as processed after conversion
            
        Returns:
            List of LUMOZA-compatible coordination patterns
        """
        # Get unprocessed signals
        signals = get_unprocessed_signals(zone=zone)
        
        if not signals:
            return []
        
        patterns = []
        
        for signal in signals:
            # Convert to LUMOZA pattern format
            pattern = self._signal_to_pattern(signal)
            patterns.append(pattern)
            
            # Mark as processed if requested
            if mark_processed:
                default_storage.mark_processed(signal.signal_id)
        
        return patterns
    
    def _signal_to_pattern(self, signal: Signal) -> Dict:
        """Convert a WhatsApp signal to LUMOZA coordination pattern."""
        
        # Estimate cycles based on frequency
        cycles_per_window = self.frequency_to_cycles.get(signal.frequency, 0.5)
        occurrences_in_7cycles = max(1, int(cycles_per_window * 7))
        
        pattern = {
            "source": "whatsapp",
            "signal_id": signal.signal_id,
            "activity_type": signal.activity_type,
            "zone": signal.zone,
            "timestamp": signal.timestamp,
            "user_phone": signal.user_phone,
            
            # LUMOZA-compatible fields
            "demand_rhythm": {
                "frequency": f"{occurrences_in_7cycles} of 7 cycles",  # Format for energy estimator
                "occurrences_in_7cycles": occurrences_in_7cycles,
                "stability_class": self._estimate_stability(occurrences_in_7cycles),
                "time_window": self._infer_time_window(signal.frequency)
            },
            
            "coordination_confidence": signal.confidence,
            "confidence_class": self._classify_confidence(signal.confidence),
            
            "cluster_info": {
                "estimated_actors": signal.actors if signal.actors else 1,
                "raw_report": signal.raw_message
            },
            
            "validation_strength": "reported",
            "validation_details": f"WhatsApp signal from {signal.user_phone} at {signal.timestamp}",
            "bankability_note": "Community-reported signal. Awaiting infrastructure telemetry corroboration."
        }
        
        return pattern
    
    def _estimate_stability(self, occurrences: int) -> str:
        """Estimate stability class based on occurrence frequency."""
        if occurrences >= 5:
            return "stable"
        elif occurrences >= 3:
            return "moderate"
        else:
            return "emerging"
    
    def _classify_confidence(self, confidence_score: float) -> str:
        """Classify confidence level."""
        if confidence_score >= 0.7:
            return "high"
        elif confidence_score >= 0.4:
            return "moderate"
        else:
            return "low"
    
    def _infer_time_window(self, frequency: str) -> str:
        """Infer time window from frequency."""
        window_map = {
            "daily": "morning/afternoon/evening",
            "weekly": "weekly_cycle",
            "monthly": "monthly_cycle",
            "seasonal": "seasonal",
            "unknown": "unspecified"
        }
        return window_map.get(frequency, "unspecified")
    
    def process_signals_for_lumoza(self, zone: Optional[str] = None, mark_processed: bool = False) -> Dict:
        """
        Process all unprocessed WhatsApp signals for LUMOZA.
        
        Args:
            zone: Optional zone filter
            mark_processed: Whether to mark signals as processed after conversion
            
        Returns:
            Dictionary with processing summary
        """
        patterns = self.convert_to_lumoza_patterns(zone=zone, mark_processed=mark_processed)
        
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "zone": zone if zone else "all",
            "patterns_processed": len(patterns),
            "patterns": patterns,
            "status": "ready_for_lumoza"
        }
        
        return summary


def integrate_whatsapp_to_lumoza(zone: Optional[str] = None, mark_processed: bool = False) -> Dict:
    """
    Convenience function to integrate WhatsApp signals with LUMOZA.
    
    Args:
        zone: Optional zone filter
        mark_processed: Whether to mark signals as processed
        
    Returns:
        Processing summary ready for LUMOZA pipeline
    """
    integrator = LumozaIntegration()
    return integrator.process_signals_for_lumoza(zone=zone, mark_processed=mark_processed)
