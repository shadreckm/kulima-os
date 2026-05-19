"""
LUNDAI Signal Integrity Evaluation Tests
========================================
"""

from lundai_engine import evaluate_signal_integrity, filter_signals_by_integrity


def test_evaluate_signal_integrity_low():
    signals = [
        {
            "activity_type": "welding",
            "zone": "zone_x",
            "timestamp": "2026-05-01T08:00:00Z",
            "user_phone": "+10000000001",
            "signal_source": "human",
        }
    ]

    results = evaluate_signal_integrity(signals)
    assert len(results) == 1
    assert results[0]["integrity_score"] < 0.4
    assert results[0]["valid"] is False
    assert results[0]["classification"] == "low"


def test_evaluate_signal_integrity_medium():
    signals = [
        {
            "activity_type": "milling",
            "zone": "zone_x",
            "timestamp": "2026-05-01T08:00:00Z",
            "user_phone": "+10000000001",
            "signal_source": "human",
        },
        {
            "activity_type": "milling",
            "zone": "zone_x",
            "timestamp": "2026-05-01T12:00:00Z",
            "user_phone": "+10000000001",
            "signal_source": "human",
        },
        {
            "activity_type": "milling",
            "zone": "zone_x",
            "timestamp": "2026-05-02T09:00:00Z",
            "user_phone": "+10000000001",
            "signal_source": "human",
        },
    ]

    results = evaluate_signal_integrity(signals)
    assert len(results) == 1
    assert 0.4 <= results[0]["integrity_score"] < 0.7
    assert results[0]["valid"] is True
    assert results[0]["classification"] == "medium"


def test_evaluate_signal_integrity_high_with_telemetry_and_senders():
    signals = [
        {
            "activity_type": "irrigation",
            "zone": "zone_y",
            "timestamp": "2026-05-01T08:00:00Z",
            "user_phone": "+10000000001",
            "signal_source": "human",
        },
        {
            "activity_type": "irrigation",
            "zone": "zone_y",
            "timestamp": "2026-05-02T08:30:00Z",
            "user_phone": "+10000000002",
            "signal_source": "human",
        },
        {
            "activity_type": "irrigation",
            "zone": "zone_y",
            "timestamp": "2026-05-04T09:00:00Z",
            "signal_source": "telemetry",
        },
        {
            "activity_type": "irrigation",
            "zone": "zone_y",
            "timestamp": "2026-05-05T09:15:00Z",
            "signal_source": "telemetry",
        },
        {
            "activity_type": "irrigation",
            "zone": "zone_y",
            "timestamp": "2026-05-06T09:30:00Z",
            "signal_source": "telemetry",
        },
    ]

    results = evaluate_signal_integrity(signals)
    assert len(results) == 1
    assert results[0]["integrity_score"] >= 0.7
    assert results[0]["valid"] is True
    assert results[0]["classification"] == "high"


def test_filter_signals_by_integrity_returns_only_valid_groups():
    signals = [
        {
            "activity_type": "welding",
            "zone": "zone_x",
            "timestamp": "2026-05-01T08:00:00Z",
            "user_phone": "+10000000001",
            "signal_source": "human",
        },
        {
            "activity_type": "irrigation",
            "zone": "zone_y",
            "timestamp": "2026-05-01T08:00:00Z",
            "user_phone": "+10000000001",
            "signal_source": "human",
        },
        {
            "activity_type": "irrigation",
            "zone": "zone_y",
            "timestamp": "2026-05-02T08:00:00Z",
            "user_phone": "+10000000002",
            "signal_source": "human",
        },
        {
            "activity_type": "irrigation",
            "zone": "zone_y",
            "timestamp": "2026-05-04T09:00:00Z",
            "signal_source": "telemetry",
        },
    ]

    filtered = filter_signals_by_integrity(signals)
    assert all(signal["activity_type"] == "irrigation" for signal in filtered)
    assert len(filtered) == 3


def test_apply_planning_reserve():
    from lundai_engine import apply_planning_reserve

    result = apply_planning_reserve(100)
    assert result["usable_signals"] == 75.0
    assert result["reserve_buffer"] == 25.0

    result = apply_planning_reserve(10)
    assert result["usable_signals"] == 7.5
    assert result["reserve_buffer"] == 2.5


def test_detect_infrastructure_mismatch_high():
    from lundai_engine import detect_infrastructure_mismatch

    lundai_data = {
        "zone_analyses": {
            "zone_x": {
                "gap_severity": "critical",
                "infrastructure_adequacy_score": 40,
            }
        },
        "coordination_patterns": [
            {
                "zone": "zone_x",
                "activity_type": "irrigation",
                "stability_score": 0.8,
                "validation_strength": "strong",
                "alignment_level": "high",
                "demand_rhythm": {"frequency": "6 of 7 cycles"},
            }
        ]
    }

    result = detect_infrastructure_mismatch(lundai_data)
    assert len(result) == 1
    assert result[0]["zone"] == "zone_x"
    assert result[0]["activity"] == "irrigation"
    assert result[0]["mismatch"] is True
    assert result[0]["severity"] == "high"


def test_detect_infrastructure_mismatch_false_for_weak_alignment():
    from lundai_engine import detect_infrastructure_mismatch

    lundai_data = {
        "zone_analyses": {
            "zone_y": {
                "gap_severity": "severe",
                "infrastructure_adequacy_score": 65,
            }
        },
        "coordination_patterns": [
            {
                "zone": "zone_y",
                "activity_type": "milling",
                "stability_score": 0.6,
                "validation_strength": "weak",
                "alignment_level": "medium",
                "demand_rhythm": {"frequency": "4 of 7 cycles"},
            }
        ]
    }

    result = detect_infrastructure_mismatch(lundai_data)
    assert len(result) == 1
    assert result[0]["mismatch"] is False
    assert result[0]["severity"] == "low"


def test_assess_settlement_alignment_high():
    validated_signals = [
        {
            "activity_type": "irrigation",
            "zone": "zone_x",
            "time_window": "morning",
            "timestamp": "2026-05-01T08:00:00Z",
        },
        {
            "activity_type": "irrigation",
            "zone": "zone_x",
            "time_window": "morning",
            "timestamp": "2026-05-02T08:00:00Z",
        },
        {
            "activity_type": "irrigation",
            "zone": "zone_x",
            "time_window": "morning",
            "timestamp": "2026-05-03T08:00:00Z",
        },
    ]

    from lundai_engine import assess_settlement_alignment

    result = assess_settlement_alignment(validated_signals)
    assert result["alignment_level"] == "high"
    assert result["cluster_strength"] == 1.0
    assert result["spatial_consistency"] == 1.0


def test_assess_settlement_alignment_low():
    validated_signals = [
        {
            "activity_type": "milling",
            "zone": "zone_a",
            "time_window": "morning",
            "timestamp": "2026-05-01T08:00:00Z",
        },
        {
            "activity_type": "milling",
            "zone": "zone_b",
            "time_window": "afternoon",
            "timestamp": "2026-05-01T13:00:00Z",
        },
        {
            "activity_type": "milling",
            "zone": "zone_c",
            "time_window": "evening",
            "timestamp": "2026-05-01T18:00:00Z",
        },
    ]

    from lundai_engine import assess_settlement_alignment

    result = assess_settlement_alignment(validated_signals)
    assert result["alignment_level"] == "low"
    assert result["cluster_strength"] < 0.5
    assert result["spatial_consistency"] < 0.5
