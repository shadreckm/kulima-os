"""
Signal validation: quality checks, duplicate detection, structure requirements.
"""
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from backend.utils.nlp_pipeline import parse_signal_text, normalize_text

MIN_SIGNAL_LENGTH = 8
MEANINGLESS_PATTERNS = frozenset({"test", "hello", "hi", "asdf", "xxx", "none", "na", "n/a", "..."})


def _signal_fingerprint(activity: str, zone: str, time_window: str, normalized_text: str) -> str:
    payload = f"{zone}|{activity}|{time_window}|{normalized_text}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def is_meaningful_text(text: str) -> bool:
    normalized = normalize_text(text)
    if len(normalized) < MIN_SIGNAL_LENGTH:
        return False
    if normalized in MEANINGLESS_PATTERNS:
        return False
    if re.fullmatch(r"[\W\d_]+", normalized):
        return False
    alpha_count = sum(1 for c in normalized if c.isalpha())
    return alpha_count >= 4


def validate_signal_input(
    raw_text: str,
    zone: str = "MZUZU",
    is_voice: bool = False,
) -> Tuple[bool, Dict, str]:
    """
    Validate and parse a signal.
    Returns (accepted, parsed_dict, rejection_reason).
    """
    if not raw_text or not isinstance(raw_text, str):
        return False, {}, "empty_input"

    parsed = parse_signal_text(raw_text, default_zone=zone, is_voice=is_voice)

    if not is_meaningful_text(parsed.get("normalized_text") or raw_text):
        return False, parsed, "low_quality"

    if not parsed.get("valid") and parsed.get("intent_confidence", 0) < 0.3:
        return False, parsed, "unrecognized_intent"

    activity = parsed.get("activity_type", "unknown")
    if activity == "unknown":
        return False, parsed, "missing_activity"

    return True, parsed, "ok"


def is_duplicate_signal(
    db_session,
    zone: str,
    activity: str,
    time_window: str,
    normalized_text: str,
    window_hours: int = 4,
) -> bool:
    """Check DB for semantically duplicate signals within aggregation window."""
    from backend.database.models import Signal

    if not normalized_text:
        return False

    recent_window = datetime.utcnow() - timedelta(hours=window_hours)
    fingerprint = _signal_fingerprint(activity, zone, time_window, normalized_text)

    recent = (
        db_session.query(Signal)
        .filter(Signal.zone == zone.upper(), Signal.timestamp >= recent_window)
        .all()
    )

    for signal in recent:
        existing_norm = normalize_text(signal.original_text or "")
        existing_fp = _signal_fingerprint(
            signal.activity_type or "",
            signal.zone or "",
            signal.time_window or "",
            existing_norm,
        )
        if existing_fp == fingerprint:
            return True
        if existing_norm == normalized_text:
            return True

    return False
