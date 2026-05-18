"""Pilot zone identifiers and phone-to-cluster mapping (Malawi pilot)."""

import os
from typing import Optional

ZONE_ALIASES = {
    "B": "B",
    "ZONE_B": "B",
    "ZONE B": "B",
    "MZUZU": "MZUZU",
    "ZONE_MZUZU": "MZUZU",
    "EKWENDENI": "EKWENDENI",
    "ZONE_EKWENDENI": "EKWENDENI",
    "KARONGA": "KARONGA",
    "ZONE_KARONGA": "KARONGA",
}

DEFAULT_ZONE = os.getenv("PILOT_DEFAULT_ZONE", "MZUZU")


def normalize_phone(phone: str) -> str:
    """Normalize Twilio/WhatsApp numbers for ZONE_MAP lookup."""
    normalized = phone.strip().lower().replace("whatsapp:", "").replace(" ", "")
    if normalized and not normalized.startswith("+"):
        normalized = f"+{normalized}"
    return normalized


_RAW_PILOT_PHONES = {
    os.getenv("PILOT_PHONE_MZUZU", "+265883766348"): "MZUZU",
    os.getenv("PILOT_PHONE_EKWENDENI", "+265XXXXXXXXX"): "EKWENDENI",
    os.getenv("PILOT_PHONE_KARONGA", "+265YYYYYYYYY"): "KARONGA",
}
ZONE_MAP = {normalize_phone(k): v for k, v in _RAW_PILOT_PHONES.items()}


def normalize_zone(zone: str) -> str:
    """Canonical zone id for aggregation (per-cluster isolation)."""
    if not zone:
        return DEFAULT_ZONE
    cleaned = zone.strip().upper().replace(" ", "_")
    if cleaned.startswith("ZONE_"):
        cleaned = cleaned[5:]
    if cleaned == "ZONE":
        return DEFAULT_ZONE
    return ZONE_ALIASES.get(cleaned, cleaned)


def zone_from_phone(sender_phone: Optional[str]) -> Optional[str]:
    """Resolve pilot cluster from phone; None if phone missing."""
    if not sender_phone:
        return None
    return ZONE_MAP.get(normalize_phone(sender_phone))
