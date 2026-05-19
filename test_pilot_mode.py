import os
from pathlib import Path

import pilot_mode
from pilot_mode import generate_daily_summary, generate_pilot_report, is_pilot_mode, log_pilot_event, load_pilot_log


def test_pilot_mode_environment_toggle(monkeypatch):
    monkeypatch.setenv("KULIMA_PILOT_MODE", "1")
    assert is_pilot_mode() is True

    monkeypatch.setenv("KULIMA_PILOT_MODE", "0")
    assert is_pilot_mode() is False


def test_log_pilot_event_and_summary(monkeypatch, tmp_path):
    monkeypatch.setenv("KULIMA_PILOT_MODE", "1")
    monkeypatch.setattr(pilot_mode, "LOG_FILE", tmp_path / "pilot_log.json")

    event = {
        "event_type": "incoming_signal",
        "zone": "MZUZU",
        "activity_type": "irrigation",
        "validated": True,
        "confidence_class": "high",
        "coordination_confidence": 0.92,
        "decision_note": "planning_ready",
    }
    log_pilot_event(event)

    entries = load_pilot_log()
    assert len(entries) == 1
    assert entries[0]["zone"] == "MZUZU"
    assert entries[0]["activity_type"] == "irrigation"
    assert entries[0]["validated"] is True
    assert "logged_at" in entries[0]

    summary = generate_daily_summary()
    assert summary["entry_count"] == 1
    assert summary["validated_entries"] == 1
    assert summary["trust_distribution"]["high"] == 1

    report = generate_pilot_report()
    assert report["pilot_mode"] is True
    assert report["daily_summary"]["entry_count"] == 1
