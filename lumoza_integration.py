"""
LUMOZA Integration Layer

Bridges WhatsApp signals with LUMOZA 7-cycle processing.
Patterns come from repetition across time windows, not single messages.
"""

from typing import List, Dict, Optional
from datetime import datetime

from signal_storage import get_unprocessed_signals, default_storage
from coordination_accumulation import (
    compute_coordination_patterns,
    get_zone_window_signals,
)
from zone_utils import normalize_zone


class LumozaIntegration:
    """Integrates time-accumulated WhatsApp signals with LUMOZA."""

    def convert_to_lumoza_patterns(
        self, zone: Optional[str] = None, mark_processed: bool = False
    ) -> List[Dict]:
        if not zone:
            return []

        zone_key = normalize_zone(zone)
        patterns = compute_coordination_patterns(zone_key)
        enriched = [self._enrich_pattern(p) for p in patterns]

        if mark_processed:
            for signal in get_unprocessed_signals(zone=zone_key):
                default_storage.mark_processed(signal.signal_id)

        return enriched

    def _enrich_pattern(self, pattern: Dict) -> Dict:
        score = pattern.get("stability_score", 0.0)
        return {
            "activity_type": pattern["activity_type"],
            "zone": pattern["zone"],
            "demand_rhythm": {
                "time_window": pattern["time_window"],
                "frequency": pattern["demand_rhythm"]["frequency"],
                "stability_class": pattern["demand_rhythm"]["stability_class"],
                "cycles_present": pattern["demand_rhythm"].get("cycles_present", []),
            },
            "coordination_confidence": score,
            "confidence_class": self._classify_confidence(score),
            "validation_strength": pattern.get("validation_strength", "human_only"),
            "validation_details": pattern.get("validation_details", ""),
            "bankability_note": (
                "Pattern derived from repeated signals across a 7-cycle window. "
                "Not inferred from a single message."
            ),
        }

    def _classify_confidence(self, confidence_score: float) -> str:
        if confidence_score >= 0.7:
            return "high"
        if confidence_score >= 0.4:
            return "moderate"
        return "low"

    def process_signals_for_lumoza(
        self, zone: Optional[str] = None, mark_processed: bool = False
    ) -> Dict:
        zone_key = normalize_zone(zone) if zone else None
        patterns = self.convert_to_lumoza_patterns(zone=zone_key, mark_processed=mark_processed)
        window_signals = get_zone_window_signals(zone_key) if zone_key else []

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "zone": zone_key or "none",
            "window_days": 7,
            "signals_in_window": len(window_signals),
            "patterns_processed": len(patterns),
            "patterns": patterns,
            "status": "ready_for_lumoza",
        }


def integrate_whatsapp_to_lumoza(
    zone: Optional[str] = None, mark_processed: bool = False
) -> Dict:
    integrator = LumozaIntegration()
    return integrator.process_signals_for_lumoza(zone=zone, mark_processed=mark_processed)
