"""
LUMOZA Integration Layer

Bridges WhatsApp signals with LUMOZA 7-cycle processing, LUNDAI settlement context,
and ZENTARI coordination confidence evaluation.

This pipeline ensures:
- Raw signals are filtered for integrity before decision support
- LUMOZA operates on validated, identity-free coordination entries
- LUNDAI adds settlement and infrastructure context
- ZENTARI evaluates the trustworthiness of coordination patterns
"""

from typing import List, Dict, Optional
from datetime import datetime

from signal_storage import get_unprocessed_signals, default_storage
from coordination_accumulation import (
    get_zone_window_signals,
    infer_time_window,
    cycle_index_from_timestamp,
    window_start,
)
from lumoza_engine import LumozaEngine
from lundai_engine import (
    filter_signals_by_integrity,
    apply_planning_reserve,
    evaluate_signal_integrity,
    assess_settlement_alignment,
    detect_infrastructure_mismatch,
    LundaiEngine,
)
from pilot_mode import is_pilot_mode, log_pilot_event
from zentari_engine import ZentariEngine
from zone_utils import normalize_zone


class LumozaIntegration:
    """Integrates time-accumulated WhatsApp signals through the full KULIMA OS pipeline."""

    def convert_to_lumoza_patterns(
        self,
        zone: Optional[str] = None,
        mark_processed: bool = False,
        pilot_mode: bool = False,
    ) -> Dict:
        """Process raw zone signals through LUMOZA, then LUNDAI and ZENTARI."""
        if not zone:
            return self._empty_summary()

        pilot_mode = pilot_mode or is_pilot_mode()
        zone_key = normalize_zone(zone)
        window_signals = get_zone_window_signals(zone_key)
        raw_signal_count = len(window_signals)
        raw_signal_dicts = [signal.to_dict() for signal in window_signals]

        validated_signal_dicts = filter_signals_by_integrity(raw_signal_dicts)
        validated_signal_count = len(validated_signal_dicts)
        planning_reserve = apply_planning_reserve(validated_signal_count)

        # LUNDAI integrity evaluation for explainability / traceability
        integrity_records = evaluate_signal_integrity(raw_signal_dicts)
        integrity_map = { (r['activity'], r['zone']): r for r in integrity_records }
        rejected_signal_count = raw_signal_count - validated_signal_count

        win_start = window_start()
        lumoza_entries = self._dicts_to_lumoza_entries(validated_signal_dicts, win_start)
        lumoza_patterns = LumozaEngine().process_signals(lumoza_entries)

        if mark_processed:
            for signal in get_unprocessed_signals(zone=zone_key):
                default_storage.mark_processed(signal.signal_id)

        # LUNDAI context analysis uses validated coordination patterns
        settlement_alignment = assess_settlement_alignment(validated_signal_dicts)
        lundai_analysis = LundaiEngine().analyze_settlement_context(lumoza_patterns) if lumoza_patterns else {}
        infrastructure_mismatch = detect_infrastructure_mismatch(lundai_analysis)

        # ZENTARI evaluates confidence after LUNDAI context has been established
        # Attach explainability / traceability to each LUMOZA pattern before ZENTARI
        for p in lumoza_patterns:
            key = (p.get('activity_type'), p.get('zone'))
            rec = integrity_map.get(key, None)
            # trace fields
            p['signal_count'] = rec['signal_count'] if rec else 0
            p['validated_signals'] = validated_signal_count if rec else 0
            p['rejected_signals'] = rejected_signal_count if rec else 0
            p['integrity_score'] = rec['integrity_score'] if rec else round(p.get('stability_score', 0.0),3)
            p['alignment_level'] = settlement_alignment.get('alignment_level', 'low')
            # human-readable explanation
            if rec:
                p['explanation'] = (
                    f"This signal group has {rec['signal_count']} signals from {rec['unique_senders']} unique senders over {rec['unique_days']} day(s). "
                    f"Integrity score {rec['integrity_score']} ({rec['classification']}). "
                    f"Burst ratio {rec.get('burst_ratio', 1.0)}; anomaly_flag={rec.get('anomaly_flag', False)}."
                )
            else:
                p['explanation'] = (
                    f"Derived from LUMOZA pattern with stability {p.get('stability_score', 0.0)}; no raw integrity record available."
                )

        confidence_patterns = ZentariEngine().evaluate_coordination_confidence(
            lumoza_patterns,
            planning_reserve=planning_reserve,
        )

        if pilot_mode:
            for pattern in confidence_patterns:
                log_pilot_event(
                    {
                        "event_type": "coordination_pattern",
                        "zone": zone_key,
                        "activity_type": pattern.get("activity_type"),
                        "time_window": pattern.get("demand_rhythm", {}).get("time_window"),
                        "validated": bool(pattern.get("confidence_class") in {"high", "moderate"}),
                        "confidence_class": pattern.get("confidence_class"),
                        "coordination_confidence": pattern.get("coordination_confidence"),
                        "alignment_level": pattern.get("alignment_level"),
                        "integrity_score": pattern.get("integrity_score"),
                        "decision_note": pattern.get("bankability_note", ""),
                        "explanation": pattern.get("explanation"),
                        "planning_reserve": planning_reserve,
                        "signal_count": pattern.get("signal_count"),
                        "validated_signals": pattern.get("validated_signals"),
                        "rejected_signals": pattern.get("rejected_signals"),
                    }
                )

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "zone": zone_key,
            "window_days": 7,
            "raw_signal_count": raw_signal_count,
            "validated_signal_count": validated_signal_count,
            "planning_reserve": planning_reserve,
            "signals_in_window": raw_signal_count,
            "coordination_trend": self._derive_coordination_trend(confidence_patterns, raw_signal_count),
            "patterns_processed": len(confidence_patterns),
            "patterns": confidence_patterns,
            "lundai_analysis": lundai_analysis,
            "settlement_alignment": settlement_alignment,
            "infrastructure_mismatch": infrastructure_mismatch,
            "pilot_mode": pilot_mode,
            "status": "ready_for_prospectus" if confidence_patterns else "insufficient_data",
        }

    def _dicts_to_lumoza_entries(self, signals: List[Dict], win_start: datetime) -> List[Dict]:
        """Convert validated raw signal dictionaries into LUMOZA inputs."""
        entries = []
        for signal in signals:
            activity_type = signal.get('activity_type') or signal.get('activity')
            zone = normalize_zone(signal.get('zone') or signal.get('zone_id') or "")
            timestamp = signal.get('timestamp', "")
            if not activity_type or not zone:
                continue

            entries.append({
                "activity_type": activity_type,
                "zone": zone,
                "time_window": infer_time_window(timestamp),
                "cycle_index": cycle_index_from_timestamp(timestamp, win_start),
                "signal_source": signal.get('signal_source', 'human'),
                "service_priority": signal.get('service_priority', 'productive'),
            })
        return entries

    def _derive_coordination_trend(self, patterns: List[Dict], raw_signal_count: int) -> str:
        """Derive a dashboard-friendly coordination trend from ZENTARI outputs."""
        if patterns:
            high_confidence = any(
                p.get('confidence_class') == 'high' or p.get('coordination_confidence', 0) >= 0.8
                for p in patterns
            )
            return "Strong" if high_confidence else "Growing"
        if raw_signal_count < 2:
            return "Emerging"
        return "Growing"

    def _empty_summary(self) -> Dict:
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "zone": "none",
            "window_days": 7,
            "raw_signal_count": 0,
            "validated_signal_count": 0,
            "planning_reserve": apply_planning_reserve(0),
            "signals_in_window": 0,
            "coordination_trend": "Emerging",
            "patterns_processed": 0,
            "patterns": [],
            "lundai_analysis": {},
            "settlement_alignment": {},
            "infrastructure_mismatch": [],
            "status": "insufficient_data",
        }


def integrate_whatsapp_to_lumoza(
    zone: Optional[str] = None, mark_processed: bool = False
) -> Dict:
    integrator = LumozaIntegration()
    return integrator.convert_to_lumoza_patterns(zone=zone, mark_processed=mark_processed)
