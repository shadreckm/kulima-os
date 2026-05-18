"""Tests for forgiving WhatsApp input parsing."""

import pytest
from input_parser import parse_user_input, UNKNOWN_PRODUCTIVE_ACTIVITY


@pytest.mark.parametrize(
    "message,expected",
    [
        ("irringating today", "irrigation"),
        ("irigating crops", "irrigation"),
        ("watering crops", "irrigation"),
        ("we busy at mill", "milling"),
        ("busy at the mill this week", "milling"),
        ("sold maize at market", "trading"),
        ("cold storage filling up", "storage"),
    ],
)
def test_parse_community_language(message, expected):
    parsed = parse_user_input(message)
    assert parsed is not None
    assert parsed.activity_type == expected


def test_unknown_productive_activity_still_stored():
    parsed = parse_user_input("went to town for supplies")
    assert parsed is not None
    assert parsed.activity_type == UNKNOWN_PRODUCTIVE_ACTIVITY


def test_meaningless_returns_none():
    assert parse_user_input("") is None
    assert parse_user_input("   ") is None
    assert parse_user_input("!!!") is None


def test_single_activity_per_message():
    """One WhatsApp message yields exactly one activity (highest-priority match)."""
    parsed = parse_user_input("irrigating crops and busy at mill")
    assert parsed is not None
    assert parsed.activity_type == "milling"


def test_zone_assigned_from_phone_only():
    from zone_utils import ZONE_MAP

    for phone, expected_zone in ZONE_MAP.items():
        parsed = parse_user_input("watering crops", phone)
        assert parsed.zone == expected_zone
    parsed = parse_user_input("farming in karonga", "+265883766348")
    assert parsed.zone == "MZUZU"


def test_whatsapp_handler_never_harsh_reject():
    from whatsapp_handler import WhatsAppMessageHandler

    handler = WhatsAppMessageHandler()
    success, msg = handler.handle_incoming_message("watering crops", "+265883766348")
    assert success is True
    assert "best effort interpretation" in msg.lower()
    assert "could not parse" not in msg.lower()
