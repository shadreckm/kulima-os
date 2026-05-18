"""Tests for 7-cycle accumulation and zone-scoped coordination."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from coordination_accumulation import (
    compute_coordination_patterns,
    compute_coordination_trend,
    cycle_index_from_timestamp,
    get_zone_window_signals,
    signals_to_lumoza_entries,
    window_start,
)
from input_parser import parse_user_input
from signal_storage import JsonSignalStorage, Signal, store_signal
from zone_utils import normalize_zone


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    path = tmp_path / "test_signals.json"
    path.write_text("[]")
    storage = JsonSignalStorage(str(path))
    monkeypatch.setattr("signal_storage.default_storage", storage)
    monkeypatch.setattr("coordination_accumulation.default_storage", storage)
    return storage


def _add(storage, zone, activity, days_ago, phone="+100"):
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    signal = Signal(
        signal_id=f"{zone}_{activity}_{ts}",
        activity_type=activity,
        zone=normalize_zone(zone),
        frequency="unknown",
        timestamp=ts,
        user_phone=phone,
        raw_message=activity,
        processed=False,
    )
    storage.add_signal(signal)


def test_normalize_pilot_zones():
    assert normalize_zone("Zone B") == "B"
    assert normalize_zone("mzuzu") == "MZUZU"
    assert normalize_zone("EKWENDENI") == "EKWENDENI"
    assert normalize_zone("Karonga") == "KARONGA"


def test_zone_isolation(isolated_storage):
    _add(isolated_storage, "B", "irrigation", 1)
    _add(isolated_storage, "MZUZU", "milling", 1)
    assert len(get_zone_window_signals("B")) == 1
    assert len(get_zone_window_signals("MZUZU")) == 1
    b_patterns = compute_coordination_patterns("B")
    mz_patterns = compute_coordination_patterns("MZUZU")
    assert all(p["zone"] == "B" for p in b_patterns)
    assert all(p["zone"] == "MZUZU" for p in mz_patterns) if mz_patterns else True


def test_one_message_one_activity():
    parsed = parse_user_input("sold maize at the mill today")
    assert parsed is not None
    assert parsed.activity_type in ("milling", "trading")
    assert parsed.activity_type == "milling"


def test_patterns_need_repetition_not_single_message(isolated_storage):
    _add(isolated_storage, "B", "irrigation", 0)
    assert compute_coordination_patterns("B") == []
    assert compute_coordination_trend("B") == "Emerging"


def test_strong_trend_after_repeated_cycles(isolated_storage):
    for day in range(7):
        _add(isolated_storage, "B", "irrigation", day)
    patterns = compute_coordination_patterns("B")
    assert len(patterns) >= 1
    assert compute_coordination_trend("B") == "Strong"


def test_growing_with_increasing_reports(isolated_storage):
    _add(isolated_storage, "B", "milling", 6)
    _add(isolated_storage, "B", "milling", 5)
    _add(isolated_storage, "B", "milling", 1)
    _add(isolated_storage, "B", "milling", 0)
    trend = compute_coordination_trend("B")
    assert trend in ("Growing", "Strong")


def test_cycle_index_maps_days_in_window():
    start = window_start()
    ts = (start + timedelta(days=3)).isoformat()
    assert cycle_index_from_timestamp(ts, start) == 4
