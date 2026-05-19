"""
KULIMA OS Pilot - LUNDAI Settlement & Infrastructure Gap Engine
================================================================

LUNDAI (Pilot Scope) performs deterministic settlement context and infrastructure
gap analysis using zone-level metadata, without external GIS or satellite data.

INVARIANT ENFORCEMENT:
- Zero-PII: Operates only on zone-level aggregates (no individual locations)
- Coordination > Identity: Reasons over settlement patterns, not people
- Deterministic: No external APIs, real-time data, or personal identifiers
- Semantic Guard: No surveillance, tracking, or individual profiling

LUNDAI combines with LUMOZA's temporal coordination intelligence to strengthen
Critical Load Protection by providing settlement and infrastructure context.
"""

from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from typing import List, Dict
import statistics
import math

from zone_metadata import get_zone_metadata, get_all_zones
from policy import compute_planning_reserve, RESERVE_RATIO


def _parse_iso_timestamp(timestamp: str):
    """Parse an ISO timestamp string into a timezone-aware datetime."""
    if not timestamp:
        return None

    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _extract_group_key(signal: Dict):
    activity = signal.get('activity_type') or signal.get('activity')
    zone = signal.get('zone') or signal.get('zone_id')
    return activity, zone


def _calculate_integrity_score(
    unique_days: int,
    unique_senders: int,
    span_days: float,
    average_spacing_days: float,
    signal_count: int,
    telemetry_count: int,
    human_count: int,
) -> float:
    """Calculate a normalized integrity score for a signal group.

    New scoring balances three core axes:
    - user_diversity: many distinct senders increase trust
    - time_spread: signals distributed across days and spacing
    - recurrence: pattern repeating across cycles

    Additional penalties:
    - burstiness: many signals concentrated in a short period (suspicious)
    - anomaly_severity: sudden spikes relative to baseline

    Returns a float in [0, 1].
    """
    # Core factors
    recurrence_factor = min(unique_days / 4.0, 1.0)
    # user_diversity: fraction of unique senders relative to signal count
    user_diversity = min(float(unique_senders) / max(1.0, float(signal_count)), 1.0)

    # time spread factors
    span_factor = min(span_days / 4.0, 1.0)
    spacing_factor = min(average_spacing_days / 1.5, 1.0)

    density_factor = min(signal_count / 5.0, 1.0)

    # Compose base score from weighted components
    base_score = (
        0.35 * recurrence_factor
        + 0.25 * user_diversity
        + 0.15 * span_factor
        + 0.15 * density_factor
        + 0.10 * spacing_factor
    )

    # Apply penalties if caller provided burst/anomaly hints via global heuristics
    # (evaluate_signal_integrity will compute burst_ratio and anomaly_severity and attach to context)
    # We try to be conservative: big bursts reduce score up to 50%, anomalies subtract up to 20%.
    # If caller didn't compute burst/anomaly, expect those values embedded in span_days negative sentinel (not used here).
    # To avoid changing signature further, we return base_score and let caller adjust externally when needed.

    return round(min(max(base_score, 0.0), 1.0), 3)


def _classify_integrity(score: float) -> str:
    if score < 0.4:
        return 'low'
    if score < 0.7:
        return 'medium'
    return 'high'


def evaluate_signal_integrity(signals: List[Dict], integrity_threshold: float = 0.4) -> List[Dict]:
    """Evaluate raw signals and score each activity-zone group for integrity.

    Args:
        signals: List of raw activity signal dictionaries.
        integrity_threshold: Minimum score required for a signal group to be valid.

    Returns:
        A list of activity-zone integrity records.
    """
    grouped = defaultdict(list)
    for signal in signals:
        activity, zone = _extract_group_key(signal)
        if not activity or not zone:
            continue
        grouped[(activity, zone)].append(signal)

    integrity_results = []
    for (activity, zone), group in grouped.items():
        timestamps = []
        sender_ids = set()
        telemetry_count = 0
        human_count = 0

        for signal in group:
            source = signal.get('signal_source')
            if source == 'telemetry':
                telemetry_count += 1
            if source == 'human':
                human_count += 1

            sender = signal.get('user_phone') or signal.get('sender') or signal.get('source_id')
            if sender:
                sender_ids.add(sender)

            ts = _parse_iso_timestamp(signal.get('timestamp', ''))
            if ts is None and signal.get('cycle_index') is not None:
                try:
                    cycle_index = int(signal['cycle_index'])
                    ts = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(days=cycle_index - 1)
                except (TypeError, ValueError):
                    ts = None

            if ts is not None:
                timestamps.append(ts)

        unique_days = len({ts.date() for ts in timestamps}) if timestamps else 0
        signal_count = len(timestamps)
        unique_senders = len(sender_ids)

        span_days = 0.0
        average_spacing_days = 0.0
        # Daily counts to detect bursts and spikes
        daily_counts = []
        anomaly_flag = False
        anomaly_severity = 0.0
        burst_ratio = 1.0
        if len(timestamps) > 1:
            timestamps.sort()
            span_days = float((timestamps[-1].date() - timestamps[0].date()).days)
            gaps = [
                (timestamps[i] - timestamps[i - 1]).total_seconds() / 86400.0
                for i in range(1, len(timestamps))
            ]
            if gaps:
                average_spacing_days = sum(gaps) / len(gaps)

            # Build per-day counts for burst detection
            day_counts = Counter(ts.date() for ts in timestamps)
            daily_counts = sorted(day_counts.values(), reverse=True)
            median_daily = statistics.median(day_counts.values()) if day_counts else 0
            max_daily = max(day_counts.values()) if day_counts else 0

            # Burst ratio: how concentrated is activity in the peak day vs median
            if median_daily > 0:
                burst_ratio = max_daily / float(median_daily)
            else:
                burst_ratio = float(max_daily) if max_daily > 0 else 1.0

            # Simple anomaly scoring: if max_daily significantly exceeds median, mark anomaly
            if median_daily > 0 and burst_ratio >= 3.0:
                anomaly_flag = True
                anomaly_severity = min((burst_ratio - 2.0) / burst_ratio, 1.0)
            elif max_daily > 10 and signal_count >= 10 and burst_ratio >= 2.5:
                # Large absolute spike even if median small
                anomaly_flag = True
                anomaly_severity = min((burst_ratio - 1.5) / burst_ratio, 0.9)

        else:
            # For single timestamp, treat as high burstiness and low spread
            if signal_count == 1:
                burst_ratio = 1.0
                anomaly_flag = False

        score = _calculate_integrity_score(
            unique_days=unique_days,
            unique_senders=unique_senders,
            span_days=span_days,
            average_spacing_days=average_spacing_days,
            signal_count=signal_count,
            telemetry_count=telemetry_count,
            human_count=human_count,
        )

        # Post-adjust score with burst and anomaly penalties to discourage gaming
        # user_repeat_ratio: fraction of signals coming from repeated same senders
        user_repeat_ratio = 0.0
        if signal_count > 0:
            user_repeat_ratio = max(0.0, 1.0 - (unique_senders / float(signal_count)))

        # Derive a burst penalty [0..0.5] — strong concentration reduces score
        burst_penalty = 0.0
        if burst_ratio >= 3.0:
            burst_penalty = min(0.5, (burst_ratio - 2.0) / (burst_ratio + 1.0))
        elif burst_ratio >= 2.0:
            burst_penalty = min(0.25, (burst_ratio - 1.5) / (burst_ratio + 1.0))

        # User repetition penalty: repeated posts by same user reduce score modestly
        user_repeat_penalty = min(user_repeat_ratio * 0.35, 0.35)

        # Anomaly severity penalty up to 0.2
        anomaly_penalty = anomaly_severity * 0.2

        adjusted_score = score * (1.0 - burst_penalty - user_repeat_penalty) - anomaly_penalty
        # Ensure bounds
        score = round(min(max(adjusted_score, 0.0), 1.0), 3)

        classification = _classify_integrity(score)
        valid = score >= integrity_threshold

        integrity_results.append({
            "activity": activity,
            "zone": zone,
            "integrity_score": round(score, 3),
            "valid": valid,
            "classification": classification,
            "signal_count": signal_count,
            "unique_days": unique_days,
            "unique_senders": unique_senders,
            "user_repeat_ratio": round(user_repeat_ratio, 3),
            "burst_ratio": round(burst_ratio, 3),
            "anomaly_flag": anomaly_flag,
            "anomaly_severity": round(anomaly_severity, 3),
            "span_days": round(span_days, 2),
            "average_spacing_days": round(average_spacing_days, 3),
            "telemetry_count": telemetry_count,
            "human_count": human_count,
        })

    return sorted(integrity_results, key=lambda item: (item['zone'], item['activity']))


def _extract_signal_group(signal: Dict):
    return _extract_group_key(signal)


def filter_signals_by_integrity(
    signals: List[Dict], integrity_threshold: float = 0.4
) -> List[Dict]:
    """Return only signals whose activity-zone groups pass integrity filtering."""
    valid_groups = {
        (r['activity'], r['zone'])
        for r in evaluate_signal_integrity(signals, integrity_threshold)
        if r['valid']
    }
    return [
        signal for signal in signals
        if _extract_signal_group(signal) in valid_groups
    ]


def apply_planning_reserve(total_signals: float) -> Dict:
    """Apply the ethical planning reserve to total signals.

    This helper returns the usable signal capacity and explicit reserve buffer.
    It delegates the reserve ratio enforcement to the central policy module.
    """
    return compute_planning_reserve(total_signals)


def assess_settlement_alignment(validated_signals: List[Dict]) -> Dict:
    """Assess whether validated signals reflect real settlement alignment."""
    if not validated_signals:
        return {
            "alignment_level": "low",
            "cluster_strength": 0.0,
            "spatial_consistency": 0.0,
        }

    activity_groups = defaultdict(list)
    zones = set()
    for signal in validated_signals:
        activity = signal.get('activity_type') or signal.get('activity')
        zone = signal.get('zone') or signal.get('zone_id')
        time_window = signal.get('time_window') or signal.get('time_window_label')
        if not activity or not zone or not time_window:
            continue
        activity_groups[activity].append((zone, time_window))
        zones.add(zone)

    total_signals = sum(len(values) for values in activity_groups.values())
    if total_signals == 0:
        return {
            "alignment_level": "low",
            "cluster_strength": 0.0,
            "spatial_consistency": 0.0,
        }

    cluster_strength_sum = 0.0
    spatial_consistency_sum = 0.0

    max_zone_count = max(len(zones), 1)
    for activity, events in activity_groups.items():
        activity_count = len(events)
        group_counts = defaultdict(int)
        zone_set = set()
        window_set = set()

        for zone, time_window in events:
            group_counts[(zone, time_window)] += 1
            zone_set.add(zone)
            window_set.add(time_window)

        cluster_strength_activity = max(group_counts.values()) / activity_count

        zone_concentration = 1.0 - ((len(zone_set) - 1) / max_zone_count)
        window_diversity = 1.0 - ((len(window_set) - 1) / 3.0)
        zone_concentration = max(0.0, min(zone_concentration, 1.0))
        window_diversity = max(0.0, min(window_diversity, 1.0))

        spatial_consistency_activity = 0.6 * zone_concentration + 0.4 * window_diversity

        cluster_strength_sum += cluster_strength_activity * activity_count
        spatial_consistency_sum += spatial_consistency_activity * activity_count

    cluster_strength = round(cluster_strength_sum / total_signals, 3)
    spatial_consistency = round(spatial_consistency_sum / total_signals, 3)
    alignment_score = (cluster_strength + spatial_consistency) / 2.0

    if alignment_score >= 0.7:
        alignment_level = "high"
    elif alignment_score >= 0.45:
        alignment_level = "medium"
    else:
        alignment_level = "low"

    return {
        "alignment_level": alignment_level,
        "cluster_strength": cluster_strength,
        "spatial_consistency": spatial_consistency,
    }


def infer_settlement_context(metadata: Dict) -> Dict:
    """Infer settlement context and a simple infrastructure presence estimate.

    settlement_type: 'rural' | 'peri-urban' | 'market-node'
    inferred_infrastructure_presence: 'low' | 'medium' | 'high'
    """
    settlement_type = metadata.get('settlement_type', 'rural')

    # Heuristics for inferred infrastructure presence
    presence_score = 0
    if metadata.get('grid_connection') == 'none':
        presence_score -= 2
    elif metadata.get('grid_connection') == 'partial':
        presence_score -= 1
    else:
        presence_score += 1

    distance = metadata.get('distance_to_substation_km', 0) or 0
    if distance > 20:
        presence_score -= 1
    elif distance > 10:
        presence_score -= 0
    else:
        presence_score += 1

    capacity = metadata.get('transformer_capacity_kva', 0) or 0
    if capacity >= 100:
        presence_score += 1
    elif capacity >= 50:
        presence_score += 0
    else:
        presence_score -= 1

    # Map to low/medium/high
    if presence_score <= -1:
        inferred = 'low'
    elif presence_score == 0:
        inferred = 'medium'
    else:
        inferred = 'high'

    return {
        'settlement_type': settlement_type,
        'inferred_infrastructure_presence': inferred,
        'presence_score': presence_score
    }


def _validate_lundai_explanation(explanation: Dict) -> None:
    """Ensure that LUNDAI explanation fields are present and complete."""
    if not isinstance(explanation, dict):
        raise ValueError("LUNDAI explanation must be a dictionary.")

    required_keys = [
        'why_accepted',
        'why_rejected',
        'reserve_explanation',
        'action_recommendation',
        'human_readable'
    ]

    missing = [key for key in required_keys if not explanation.get(key)]
    if missing:
        raise ValueError(f"LUNDAI explanation missing required keys: {', '.join(missing)}")


def evaluate_infrastructure_gap(validated_patterns: List[Dict], inferred_presence: str = None) -> Dict:
    """Evaluate whether validated coordination indicates an infrastructure gap.

    Logic (per task):
    - If integrity_score is high (>=0.7)
    - AND alignment_level is high
    - AND inferred_infrastructure_presence is low
    => classify as infrastructure gap

    Returns an audit-friendly dict with gap_detected, gap_type, severity, explanation.
    """
    # Aggregate indicators across validated patterns
    high_trust_count = 0
    total = 0
    alignment_levels = []

    for p in validated_patterns or []:
        total += 1
        integrity = float(p.get('integrity_score', 0) or 0)
        if integrity >= 0.7:
            high_trust_count += 1
        alignment_levels.append(p.get('alignment_level'))

    # Decide alignment majority
    high_alignment = alignment_levels.count('high') >= max(1, math.floor(len(alignment_levels) / 2))

    inferred = inferred_presence or 'unknown'

    gap_detected = False
    gap_type = None
    severity = 'low'
    explanation = 'No infrastructure gap detected based on provided signals and context.'

    if total > 0 and high_trust_count > 0 and high_alignment and inferred == 'low':
        gap_detected = True
        # Determine gap type heuristically from patterns / presence
        # If grid_connection is none -> off-grid, else grid-edge or under-capacity
        # Caller should override if metadata available; here we infer from patterns
        # Use count proportions to estimate severity
        proportion = high_trust_count / float(total)
        if proportion >= 0.75:
            severity = 'high'
        elif proportion >= 0.4:
            severity = 'medium'
        else:
            severity = 'low'

        # Guess gap type
        # If inferred_presence explicitly 'low' and patterns show many essential loads -> under-capacity
        essential_count = sum(1 for p in validated_patterns if p.get('service_priority') == 'essential')
        if inferred == 'low' and essential_count > 0:
            gap_type = 'under-capacity'
        else:
            gap_type = 'grid-edge'

        explanation = (
            f"High-confidence coordination ({high_trust_count}/{total}) with strong alignment detected, "
            f"but inferred infrastructure presence is '{inferred}'. This suggests an infrastructure gap requiring inspection."
        )

    reserve_explanation = (
        f"A {int(RESERVE_RATIO * 100)}% planning reserve is enforced for critical communal loads. "
        "This infrastructure gap evaluation is derived from validated patterns before reserve allocation."
    )

    explanation_payload = {
        'why_accepted': (
            f"Accepted {high_trust_count} high-integrity patterns out of {total} total validated patterns. "
            "Patterns were accepted based on integrity and alignment thresholds."
        ),
        'why_rejected': (
            f"Patterns below high-integrity or alignment thresholds were excluded from gap analysis. "
            "This avoids over-asserting infrastructure needs from noisy or sparse signals."
        ),
        'reserve_explanation': reserve_explanation,
        'action_recommendation': (
            "Recommend detailed infrastructure inspection and reserve-aware capacity planning."
            if gap_detected else
            "No immediate infrastructure upgrade recommended; continue monitoring and protect reserve capacity."
        ),
        'human_readable': explanation
    }

    _validate_lundai_explanation(explanation_payload)

    return {
        'gap_detected': gap_detected,
        'gap_type': gap_type,
        'severity': severity,
        'explanation': explanation_payload,
        'total_patterns': total,
        'high_trust_patterns': high_trust_count,
        'inferred_infrastructure_presence': inferred,
    }


def detect_infrastructure_mismatch(lundai_data: Dict) -> List[Dict]:
    """Detect inventory gaps where activity suggests missing or insufficient infrastructure."""
    patterns = []
    zone_map = {}

    if isinstance(lundai_data, dict):
        zone_map = lundai_data.get('zone_analyses', {})
        patterns = lundai_data.get('coordination_patterns') or lundai_data.get('patterns') or []
    elif isinstance(lundai_data, list):
        patterns = lundai_data

    results = []
    for pattern in patterns:
        zone = pattern.get('zone')
        activity = pattern.get('activity_type') or pattern.get('activity')
        if not zone or not activity:
            continue

        zone_analysis = zone_map.get(zone, {})
        gap_severity = zone_analysis.get('gap_severity', 'minimal')
        adequacy_score = zone_analysis.get('infrastructure_adequacy_score', 100)

        stability_score = float(pattern.get('stability_score', 0))
        validation_strength = pattern.get('validation_strength', '')
        alignment_level = pattern.get('alignment_level', '')

        strong_integrity = stability_score >= 0.7 or pattern.get('integrity_score', 0) >= 0.7
        strong_alignment = alignment_level == 'high' or validation_strength == 'strong'

        cycle_count = 0
        demand_rhythm = pattern.get('demand_rhythm', {})
        if isinstance(demand_rhythm, dict):
            cycle_count = int(demand_rhythm.get('frequency', '0').split(' of ')[0]) if 'frequency' in demand_rhythm else 0
        repeated = cycle_count >= 5 or stability_score >= 0.7

        infrastructure_gap = gap_severity in ['critical', 'severe'] or adequacy_score < 70

        mismatch = bool(strong_integrity and strong_alignment and repeated and infrastructure_gap)

        if mismatch:
            if gap_severity == 'critical' or adequacy_score < 50:
                severity = 'high'
            elif gap_severity == 'severe' or adequacy_score < 70:
                severity = 'medium'
            else:
                severity = 'low'
        else:
            severity = 'low'

        results.append({
            "zone": zone,
            "activity": activity,
            "mismatch": mismatch,
            "severity": severity,
        })

    return results


class LundaiEngine:
    """
    LUNDAI - Settlement and Infrastructure Mismatch Engine (Pilot Scope)
    
    Analyzes settlement context and infrastructure gaps using zone-level metadata
    to inform capacity planning and Critical Load Protection enforcement.
    """
    """
    LUNDAI - Settlement and Infrastructure Mismatch Engine (Pilot Scope)
    
    Analyzes settlement context and infrastructure gaps using zone-level metadata
    to inform capacity planning and Critical Load Protection enforcement.
    """
    
    # Infrastructure gap severity thresholds
    CRITICAL_GAP_INDICATORS = {
        "no_grid": True,
        "distance_threshold_km": 20,
        "capacity_threshold_kva": 25,
        "essential_services_at_risk": True
    }
    
    def __init__(self):
        """Initialize LUNDAI engine."""
        pass
    
    def analyze_settlement_context(self, coordination_patterns: List[Dict], planning_reserve: Dict = None) -> Dict:
        """
        Analyze settlement context and infrastructure gaps for zones with
        coordinated demand patterns.
        
        ZERO-PII ENFORCEMENT:
        - Analyzes zone-level metadata only
        - No individual locations or identifiers
        
        COORDINATION > IDENTITY:
        - Combines coordination patterns (from LUMOZA) with settlement context
        - Identifies infrastructure mismatches at zone level
        
        Args:
            coordination_patterns: List of coordination patterns from LUMOZA
            
        Returns:
            Settlement and infrastructure gap analysis
        """
        
        # Extract zones with coordination patterns
        zones_with_demand = set(p['zone'] for p in coordination_patterns)
        
        # Analyze each zone
        zone_analyses = {}
        for zone in zones_with_demand:
            zone_metadata = get_zone_metadata(zone)
            zone_patterns = [p for p in coordination_patterns if p['zone'] == zone]
            
            zone_analyses[zone] = self._analyze_zone(zone, zone_metadata, zone_patterns, planning_reserve)
        
        # Generate overall assessment
        overall_assessment = self._generate_overall_assessment(zone_analyses)
        
        return {
            "zone_analyses": zone_analyses,
            "overall_assessment": overall_assessment
        }
    
    def _analyze_zone(self, zone: str, metadata: Dict, patterns: List[Dict], planning_reserve: Dict = None) -> Dict:
        """
        Analyze a single zone's settlement context and infrastructure gap.
        
        Args:
            zone: Zone identifier
            metadata: Zone metadata
            patterns: Coordination patterns in this zone
            
        Returns:
            Zone analysis
        """
        
        # Classify settlement type
        settlement_type = metadata.get('settlement_type', 'unknown')
        settlement_context = infer_settlement_context(metadata)

        # Assess infrastructure gap severity
        gap_severity = self._assess_infrastructure_gap(metadata)
        
        # Identify essential services in this zone
        essential_patterns = [p for p in patterns if p.get('service_priority') == 'essential']
        productive_patterns = [p for p in patterns if p.get('service_priority') == 'productive']
        
        # Determine grid edge exposure
        grid_edge_exposure = metadata.get('grid_edge_exposure', False)
        
        # Calculate infrastructure adequacy score (0-100)
        adequacy_score = self._calculate_infrastructure_adequacy(metadata, patterns)
        
        # Generate infrastructure gap justification
        gap_justification = self._generate_gap_justification(
            metadata, essential_patterns, productive_patterns, gap_severity
        )

        # Evaluate explicit infrastructure gap from validated patterns
        gap_evaluation = evaluate_infrastructure_gap(
            patterns,
            inferred_presence=settlement_context.get('inferred_infrastructure_presence')
        )

        accepted_patterns = [p for p in patterns if p.get('integrity_score', 0) >= 0.4]
        rejected_patterns = [p for p in patterns if p.get('integrity_score', 0) < 0.4]
        reserve_explanation = (
            f"A {int(RESERVE_RATIO * 100)}% planning reserve is enforced for communal critical loads. "
            "This zone analysis reports validated coordination before reserve allocation."
        )
        zone_explanation = {
            'why_accepted': (
                f"Accepted {len(accepted_patterns)} patterns in zone {zone} based on integrity and alignment metrics."
            ),
            'why_rejected': (
                f"Excluded {len(rejected_patterns)} patterns due to low integrity or insufficient alignment."
            ),
            'reserve_explanation': reserve_explanation,
            'action_recommendation': (
                "Investigate infrastructure upgrades and protect reserved capacity."
                if gap_evaluation['gap_detected'] else
                "Maintain monitoring and preserve planning reserve; no urgent upgrade required."
            ),
            'human_readable': (
                f"Zone {zone} shows {len(accepted_patterns)} accepted patterns and {len(rejected_patterns)} lower-confidence patterns. "
                f"Gap severity is {gap_severity}. {('Upgrade recommended.' if gap_evaluation['gap_detected'] else 'Continue monitoring.')}"
            )
        }
        _validate_lundai_explanation(zone_explanation)

        return {
            "settlement_type": settlement_type,
            "infrastructure_status": metadata.get('infrastructure_status', 'unknown'),
            "gap_severity": gap_severity,
            "settlement_context": settlement_context,
            "infrastructure_gap_evaluation": gap_evaluation,
            "grid_connection": metadata.get('grid_connection', 'unknown'),
            "grid_edge_exposure": grid_edge_exposure,
            "distance_to_substation_km": metadata.get('distance_to_substation_km'),
            "transformer_capacity_kva": metadata.get('transformer_capacity_kva'),
            "service_reliability": metadata.get('service_reliability', 'unknown'),
            "essential_services_count": len(essential_patterns),
            "productive_activities_count": len(productive_patterns),
            "infrastructure_adequacy_score": adequacy_score,
            "gap_justification": gap_justification,
            "priority_classification": self._classify_priority(gap_severity, essential_patterns),
            "explanation": zone_explanation
        }
    
    def _assess_infrastructure_gap(self, metadata: Dict) -> str:
        """
        Assess infrastructure gap severity based on metadata.
        
        Returns:
            'critical', 'severe', 'moderate', or 'minimal'
        """
        
        # Critical gap indicators
        if metadata.get('grid_connection') == 'none':
            return 'critical'
        
        if metadata.get('distance_to_substation_km', 0) > self.CRITICAL_GAP_INDICATORS['distance_threshold_km']:
            return 'critical'
        
        if metadata.get('transformer_capacity_kva', 0) < self.CRITICAL_GAP_INDICATORS['capacity_threshold_kva']:
            return 'severe'
        
        if metadata.get('service_reliability') in ['none', 'intermittent']:
            return 'severe'
        
        if metadata.get('infrastructure_status') == 'underserved':
            return 'moderate'
        
        return 'minimal'
    
    def _calculate_infrastructure_adequacy(self, metadata: Dict, patterns: List[Dict]) -> int:
        """
        Calculate infrastructure adequacy score (0-100).
        
        Higher score = better infrastructure adequacy
        """
        
        score = 100
        
        # Penalize for no grid connection
        if metadata.get('grid_connection') == 'none':
            score -= 50
        elif metadata.get('grid_connection') == 'partial':
            score -= 25
        
        # Penalize for distance to substation
        distance = metadata.get('distance_to_substation_km', 0)
        if distance > 20:
            score -= 30
        elif distance > 10:
            score -= 15
        
        # Penalize for low capacity
        capacity = metadata.get('transformer_capacity_kva', 0)
        if capacity == 0:
            score -= 20
        elif capacity < 50:
            score -= 10
        
        # Penalize for poor reliability
        reliability = metadata.get('service_reliability', 'unknown')
        if reliability == 'none':
            score -= 20
        elif reliability == 'intermittent':
            score -= 15
        elif reliability == 'moderate':
            score -= 5
        
        return max(0, score)
    
    def _generate_gap_justification(
        self, metadata: Dict, essential_patterns: List[Dict],
        productive_patterns: List[Dict], gap_severity: str
    ) -> str:
        """Generate human-readable infrastructure gap justification."""
        
        justifications = []
        
        if metadata.get('grid_connection') == 'none':
            justifications.append("No grid connection")
        elif metadata.get('grid_connection') == 'partial':
            justifications.append("Partial grid access with frequent outages")
        
        if metadata.get('distance_to_substation_km', 0) > 15:
            justifications.append(f"Remote location ({metadata['distance_to_substation_km']}km from substation)")
        
        if len(essential_patterns) > 0:
            services = [p['activity_type'] for p in essential_patterns]
            justifications.append(f"Essential services present ({', '.join(services)}) require reliable power")
        
        if metadata.get('grid_edge_exposure'):
            justifications.append("Grid-edge exposure increases vulnerability")
        
        if len(productive_patterns) > 0:
            justifications.append(f"{len(productive_patterns)} productive activities require capacity expansion")
        
        return "; ".join(justifications) if justifications else "Infrastructure adequate for current demand"
    
    def _classify_priority(self, gap_severity: str, essential_patterns: List[Dict]) -> str:
        """
        Classify infrastructure priority based on gap severity and essential services.
        
        Returns:
            'urgent', 'high', 'medium', or 'low'
        """
        
        if gap_severity == 'critical' and len(essential_patterns) > 0:
            return 'urgent'
        elif gap_severity == 'critical':
            return 'high'
        elif gap_severity == 'severe' and len(essential_patterns) > 0:
            return 'high'
        elif gap_severity == 'severe':
            return 'medium'
        elif len(essential_patterns) > 0:
            return 'medium'
        else:
            return 'low'
    
    def _generate_overall_assessment(self, zone_analyses: Dict) -> Dict:
        """Generate overall assessment across all zones."""
        
        total_zones = len(zone_analyses)
        critical_gaps = sum(1 for z in zone_analyses.values() if z['gap_severity'] == 'critical')
        severe_gaps = sum(1 for z in zone_analyses.values() if z['gap_severity'] == 'severe')
        urgent_priority = sum(1 for z in zone_analyses.values() if z['priority_classification'] == 'urgent')
        
        total_essential_services = sum(z['essential_services_count'] for z in zone_analyses.values())
        zones_with_grid_edge_exposure = sum(1 for z in zone_analyses.values() if z['grid_edge_exposure'])
        
        avg_adequacy_score = sum(z['infrastructure_adequacy_score'] for z in zone_analyses.values()) / total_zones if total_zones > 0 else 0
        
        return {
            "total_zones_analyzed": total_zones,
            "critical_infrastructure_gaps": critical_gaps,
            "severe_infrastructure_gaps": severe_gaps,
            "urgent_priority_zones": urgent_priority,
            "total_essential_services_detected": total_essential_services,
            "zones_with_grid_edge_exposure": zones_with_grid_edge_exposure,
            "average_infrastructure_adequacy_score": round(avg_adequacy_score, 1),
            "overall_infrastructure_status": self._classify_overall_status(avg_adequacy_score, critical_gaps, urgent_priority)
        }
    
    def _classify_overall_status(self, avg_score: float, critical_gaps: int, urgent_priority: int) -> str:
        """Classify overall infrastructure status."""
        
        if critical_gaps > 0 or urgent_priority > 0:
            return "Critical infrastructure gaps require urgent intervention"
        elif avg_score < 50:
            return "Severe infrastructure deficits across multiple zones"
        elif avg_score < 70:
            return "Moderate infrastructure gaps, capacity expansion needed"
        else:
            return "Infrastructure generally adequate, targeted improvements recommended"


if __name__ == "__main__":
    # Test LUNDAI with mock coordination patterns
    from pilot_signals import generate_pilot_signals
    from lumoza_engine import LumozaEngine
    
    print("Testing LUNDAI Engine...")
    print("=" * 70)
    
    # Generate signals and process through LUMOZA
    signals = generate_pilot_signals()
    lumoza = LumozaEngine()
    patterns = lumoza.process_signals(signals)
    
    # Analyze with LUNDAI
    lundai = LundaiEngine()
    analysis = lundai.analyze_settlement_context(patterns)
    
    print("\nLUNDAI SETTLEMENT & INFRASTRUCTURE GAP ANALYSIS")
    print("=" * 70)
    
    for zone, zone_analysis in analysis['zone_analyses'].items():
        print(f"\n{zone.upper()}:")
        print(f"  Settlement Type: {zone_analysis['settlement_type']}")
        print(f"  Infrastructure Status: {zone_analysis['infrastructure_status']}")
        print(f"  Gap Severity: {zone_analysis['gap_severity']}")
        print(f"  Priority: {zone_analysis['priority_classification']}")
        print(f"  Adequacy Score: {zone_analysis['infrastructure_adequacy_score']}/100")
        print(f"  Essential Services: {zone_analysis['essential_services_count']}")
        print(f"  Justification: {zone_analysis['gap_justification']}")
    
    print("\n" + "=" * 70)
    print("OVERALL ASSESSMENT:")
    overall = analysis['overall_assessment']
    print(f"  Zones Analyzed: {overall['total_zones_analyzed']}")
    print(f"  Critical Gaps: {overall['critical_infrastructure_gaps']}")
    print(f"  Urgent Priority: {overall['urgent_priority_zones']}")
    print(f"  Average Adequacy: {overall['average_infrastructure_adequacy_score']}/100")
    print(f"  Status: {overall['overall_infrastructure_status']}")
    print("=" * 70)

# Made with Bob
