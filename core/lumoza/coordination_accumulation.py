"""
Time-based signal accumulation for 7-cycle coordination windows.

Groups WhatsApp signals by zone and activity repetition across cycles,
not isolated messages or frequency guesses.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from lumoza_engine import LumozaEngine
from signal_storage import Signal, default_storage
from zone_utils import normalize_zone

CYCLE_WINDOW_DAYS = 7
TOTAL_CYCLES = 7


def _parse_timestamp(ts: str) -> datetime:
    if not ts:
        return datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def cycle_index_from_timestamp(ts: str, window_start: datetime) -> int:
    """
    Map a signal into cycle 1–7 within the rolling window (day offset from window start).
    """
    dt = _parse_timestamp(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if window_start.tzinfo is None:
        window_start = window_start.replace(tzinfo=timezone.utc)
    day_offset = (dt.date() - window_start.date()).days
    if day_offset < 0:
        day_offset = 0
    if day_offset >= TOTAL_CYCLES:
        day_offset = TOTAL_CYCLES - 1
    return day_offset + 1


def infer_time_window(ts: str) -> str:
    """Coarse time window from timestamp (temporal moat — not exact clock for users)."""
    hour = _parse_timestamp(ts).hour
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 22:
        return "evening"
    return "unspecified"


def window_start(reference: Optional[datetime] = None) -> datetime:
    ref = reference or datetime.now(timezone.utc)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)
    return ref - timedelta(days=CYCLE_WINDOW_DAYS - 1)


def get_zone_window_signals(
    zone: str,
    window_days: int = CYCLE_WINDOW_DAYS,
    include_processed: bool = True,
) -> List[Signal]:
    """All signals for one zone within the rolling window."""
    zone_key = normalize_zone(zone)
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    all_signals = default_storage.get_all_signals()
    result = []
    for signal in all_signals:
        if normalize_zone(signal.zone) != zone_key:
            continue
        if not include_processed and signal.processed:
            continue
        if _parse_timestamp(signal.timestamp) < cutoff:
            continue
        result.append(signal)
    result.sort(key=lambda s: _parse_timestamp(s.timestamp))
    return result


def signals_to_lumoza_entries(signals: List[Signal], win_start: datetime) -> List[Dict]:
    """One Lumoza entry per stored message (no per-message cycle inflation)."""
    entries = []
    for signal in signals:
        entries.append({
            "activity_type": signal.activity_type,
            "zone": normalize_zone(signal.zone),
            "time_window": infer_time_window(signal.timestamp),
            "cycle_index": cycle_index_from_timestamp(signal.timestamp, win_start),
            "signal_source": "human",
        })
    return entries


def compute_coordination_patterns(zone: str) -> List[Dict]:
    """Derive patterns from repetition across cycles, not single messages."""
    signals = get_zone_window_signals(zone)
    if not signals:
        return []
    win_start = window_start()
    entries = signals_to_lumoza_entries(signals, win_start)
    return LumozaEngine().process_signals(entries)


def compute_coordination_trend(zone: str) -> str:
    """
    Emerging → few signals / little repetition
    Growing → increasing repetition across the window
    Strong → consistent activity across cycles (stable pattern)
    """
    signals = get_zone_window_signals(zone)
    patterns = compute_coordination_patterns(zone)

    if patterns:
        best_cycles = max(
            int(p["demand_rhythm"]["frequency"].split()[0])
            for p in patterns
        )
        if best_cycles >= LumozaEngine.STABLE_THRESHOLD:
            return "Strong"

    if len(signals) < 2:
        return "Emerging"

    if _repetition_increasing(signals):
        return "Growing"

    if patterns:
        best_cycles = max(
            int(p["demand_rhythm"]["frequency"].split()[0])
            for p in patterns
        )
        if best_cycles >= LumozaEngine.NOISE_THRESHOLD:
            return "Growing"

    if len(signals) >= 3:
        return "Growing"

    return "Emerging"


def _repetition_increasing(signals: List[Signal]) -> bool:
    """True when activity reports cluster more in the recent half of the window."""
    win_start = window_start()
    by_activity: Dict[str, List[int]] = defaultdict(list)
    for signal in signals:
        by_activity[signal.activity_type].append(
            cycle_index_from_timestamp(signal.timestamp, win_start)
        )

    for cycles in by_activity.values():
        if len(cycles) < 2:
            continue
        mid = len(cycles) // 2
        sorted_cycles = sorted(cycles)
        first_distinct = len(set(sorted_cycles[:mid]))
        second_distinct = len(set(sorted_cycles[mid:]))
        if second_distinct > first_distinct:
            return True
    return False


def zone_accumulation_summary(zone: str) -> Dict:
    """Debug/planner summary for a single zone."""
    zone_key = normalize_zone(zone)
    signals = get_zone_window_signals(zone_key)
    patterns = compute_coordination_patterns(zone_key)
    return {
        "zone": zone_key,
        "window_days": CYCLE_WINDOW_DAYS,
        "signal_count": len(signals),
        "pattern_count": len(patterns),
        "coordination_trend": compute_coordination_trend(zone_key),
        "patterns": patterns,
    }
