import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PILOT_MODE_ENV = "KULIMA_PILOT_MODE"
LOG_FILE = Path(__file__).resolve().parent / "pilot_log.json"


def is_pilot_mode() -> bool:
    """Return whether the system is running in pilot evidence collection mode."""
    return os.getenv(PILOT_MODE_ENV, "false").strip().lower() in {"1", "true", "yes", "on"}


def set_pilot_mode(enabled: bool) -> None:
    """Set pilot mode for the current process."""
    os.environ[PILOT_MODE_ENV] = "1" if enabled else "0"


def load_pilot_log(log_file: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load the structured pilot evidence log from disk."""
    file_path = log_file or LOG_FILE
    if not file_path.is_file():
        return []

    try:
        content = file_path.read_text(encoding="utf-8")
        data = json.loads(content)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def save_pilot_log(entries: List[Dict[str, Any]], log_file: Optional[Path] = None) -> None:
    """Persist structured pilot evidence entries."""
    file_path = log_file or LOG_FILE
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def log_pilot_event(event: Dict[str, Any], force: bool = False, log_file: Optional[Path] = None) -> None:
    """Append a structured evidence log entry when pilot mode is enabled."""
    if not force and not is_pilot_mode():
        return

    result = dict(event)
    result["logged_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    result.setdefault("event_type", "pilot_evidence")

    entries = load_pilot_log(log_file=log_file)
    entries.append(result)
    save_pilot_log(entries, log_file=log_file)


def generate_daily_summary(log_file: Optional[Path] = None) -> Dict[str, Any]:
    """Create a daily summary from the pilot evidence log."""
    entries = load_pilot_log(log_file=log_file)
    today = datetime.now(timezone.utc).date()
    daily = []
    for entry in entries:
        logged_at = entry.get("logged_at")
        if not logged_at:
            continue
        try:
            timestamp = datetime.fromisoformat(logged_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        if timestamp.date() == today:
            daily.append(entry)

    activity_counts: Dict[str, int] = {}
    trust_counts: Dict[str, int] = {}
    rejected = 0
    validated = 0
    zones: Dict[str, int] = {}
    infrastructure_flags: Dict[str, int] = {}
    for entry in daily:
        activity = str(entry.get("activity_type", "unknown"))
        activity_counts[activity] = activity_counts.get(activity, 0) + 1

        zone = str(entry.get("zone", "unknown"))
        zones[zone] = zones.get(zone, 0) + 1

        if entry.get("validated") is True:
            validated += 1
        elif entry.get("validated") is False:
            rejected += 1

        trust_label = str(entry.get("confidence_class", "unknown"))
        trust_counts[trust_label] = trust_counts.get(trust_label, 0) + 1

        if entry.get("decision_note"):
            infrastructure_flags[entry["decision_note"]] = infrastructure_flags.get(entry["decision_note"], 0) + 1

    total = len(daily)
    coordination_strength = "Emerging"
    if trust_counts.get("high", 0) >= max(1, total // 2):
        coordination_strength = "Strong"
    elif trust_counts.get("moderate", 0) >= max(1, total // 3):
        coordination_strength = "Growing"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "entry_count": total,
        "validated_entries": validated,
        "rejected_entries": rejected,
        "zones": zones,
        "activity_counts": activity_counts,
        "trust_distribution": trust_counts,
        "coordination_strength": coordination_strength,
        "top_infrastructure_notes": sorted(
            infrastructure_flags.items(), key=lambda item: item[1], reverse=True
        )[:5],
        "latest_entries": daily[-5:],
    }


def generate_pilot_report(log_file: Optional[Path] = None) -> Dict[str, Any]:
    """Generate a structured pilot report for dashboard and stakeholder review."""
    today_summary = generate_daily_summary(log_file=log_file)
    entries = load_pilot_log(log_file=log_file)
    latest_entries = entries[-10:]

    return {
        "report_generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "pilot_mode": is_pilot_mode(),
        "daily_summary": today_summary,
        "recent_log_entries": latest_entries,
        "recommendations": [
            "Continue collecting real coordination signals to strengthen planning-grade patterns.",
            "Review high-confidence patterns for infrastructure sizing and reserve validation.",
            "Use the pilot evidence log to demonstrate traceability for stakeholder governance."
        ],
    }
