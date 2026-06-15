"""
Aggregation refresh metadata for Kulima OS coordination pipeline.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional

AGGREGATION_CYCLE_HOURS = 4
DEEP_RECALC_HOURS = 24


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00").replace("+00:00", ""))
    except ValueError:
        return None


def get_refresh_metadata(
    last_signal_at: Optional[datetime] = None,
    last_aggregation_at: Optional[datetime] = None,
) -> Dict:
    """Compute refresh timestamps exposed in API responses."""
    now = datetime.utcnow()

    if last_signal_at is None:
        last_signal_at = now
    if last_aggregation_at is None:
        last_aggregation_at = now

    next_aggregation = last_aggregation_at + timedelta(hours=AGGREGATION_CYCLE_HOURS)
    next_deep = last_aggregation_at + timedelta(hours=DEEP_RECALC_HOURS)

    hours_since_update = max(0, int((now - last_aggregation_at).total_seconds() // 3600))

    return {
        "last_updated": last_aggregation_at.isoformat() + "Z",
        "last_revalidated": now.isoformat() + "Z",
        "last_signal_at": last_signal_at.isoformat() + "Z",
        "next_aggregation_at": next_aggregation.isoformat() + "Z",
        "next_deep_recalc_at": next_deep.isoformat() + "Z",
        "aggregation_cycle_hours": AGGREGATION_CYCLE_HOURS,
        "deep_recalc_hours": DEEP_RECALC_HOURS,
        "hours_since_update": hours_since_update,
        "freshness_label": _freshness_label(hours_since_update),
    }


def _freshness_label(hours: int) -> str:
    if hours < 1:
        return "just now"
    if hours == 1:
        return "1 hour ago"
    if hours < 24:
        return f"{hours} hours ago"
    days = hours // 24
    return f"{days} day{'s' if days > 1 else ''} ago"


def get_zone_signal_timestamps(db_session, zone: str):
    """Fetch latest signal timestamp for a zone."""
    from backend.database.models import Signal
    from sqlalchemy import func

    result = (
        db_session.query(func.max(Signal.timestamp))
        .filter(Signal.zone == zone.upper())
        .scalar()
    )
    return result
