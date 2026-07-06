"""
Validated sub-zone whitelists per pilot zone.
Only whitelisted sub-zones appear in cluster intelligence outputs.
"""
from typing import Dict, List, Optional, Tuple
import re

ZONE_SUBZONES: Dict[str, List[str]] = {
    # Northern Malawi Pilot EPAs
    "EKWENDENI": ["Ekwendeni Mission", "Embangweni", "Eswazini", "Emfeni"],
    "MHUJU":     ["Mhuju Centre", "Mzenga", "Hora Mouth", "Kapita"],
    "BWENGU":    ["Bwengu Centre", "Kazomba", "Mtwalo", "Rufunsa"],
    "RUMPHI":    ["Rumphi Boma", "Katowo", "Hewe", "Ruarwe"],
    "EUTHINI":   ["Euthini Centre", "Elangeni", "Engalaweni", "Etchelo"],
    "MZIMBA":    ["Mzimba Boma", "Mzimba West", "Mzimba North", "Mzimba South"],
    # Primary pilot hub
    "MZUZU":     ["Chibanja", "Katoto", "Luwinga", "Zolozolo", "Jombo"],
    # Secondary zones
    "LILONGWE":  ["Area 25", "Area 18", "Kawale", "Mtandire"],
    "BLANTYRE":  ["Ndirande", "Chilomoni", "Limbe", "Soche"],
    "ZOMBA":     ["Mulunguzi", "Chinamwali", "Domasi"],
}

# Aliases map extracted text → canonical whitelist name
ZONE_ALIASES: Dict[str, Dict[str, str]] = {
    "EKWENDENI": {
        "ekwendeni mission": "Ekwendeni Mission",
        "ekwendeni": "Ekwendeni Mission",
        "embangweni": "Embangweni",
        "eswazini": "Eswazini",
        "emfeni": "Emfeni",
    },
    "MHUJU": {
        "mhuju centre": "Mhuju Centre",
        "mhuju center": "Mhuju Centre",
        "mhuju": "Mhuju Centre",
        "mzenga": "Mzenga",
        "hora mouth": "Hora Mouth",
        "kapita": "Kapita",
    },
    "BWENGU": {
        "bwengu centre": "Bwengu Centre",
        "bwengu center": "Bwengu Centre",
        "bwengu": "Bwengu Centre",
        "kazomba": "Kazomba",
        "mtwalo": "Mtwalo",
        "rufunsa": "Rufunsa",
    },
    "RUMPHI": {
        "rumphi boma": "Rumphi Boma",
        "rumphi": "Rumphi Boma",
        "katowo": "Katowo",
        "hewe": "Hewe",
        "ruarwe": "Ruarwe",
    },
    "EUTHINI": {
        "euthini centre": "Euthini Centre",
        "euthini": "Euthini Centre",
        "elangeni": "Elangeni",
        "engalaweni": "Engalaweni",
        "etchelo": "Etchelo",
    },
    "MZIMBA": {
        "mzimba boma": "Mzimba Boma",
        "mzimba west": "Mzimba West",
        "mzimba north": "Mzimba North",
        "mzimba south": "Mzimba South",
        "mzimba": "Mzimba Boma",
    },
    "MZUZU": {
        "chibanja": "Chibanja",
        "katoto": "Katoto",
        "luwinga": "Luwinga",
        "zolozolo": "Zolozolo",
        "jombo": "Jombo",
    },
    "LILONGWE": {
        "area 25": "Area 25",
        "area25": "Area 25",
        "area 18": "Area 18",
        "area18": "Area 18",
        "kawale": "Kawale",
        "mtandire": "Mtandire",
    },
    "BLANTYRE": {
        "ndirande": "Ndirande",
        "chilomoni": "Chilomoni",
        "limbe": "Limbe",
        "soche": "Soche",
    },
    "ZOMBA": {
        "mulunguzi": "Mulunguzi",
        "chinamwali": "Chinamwali",
        "domasi": "Domasi",
    },
}

PILOT_ZONES = frozenset(ZONE_SUBZONES.keys())


def _normalize_key(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def get_whitelist(zone: str) -> List[str]:
    return ZONE_SUBZONES.get((zone or "").upper(), [])


def validate_sub_zone(zone: str, candidate: str) -> Optional[str]:
    """Return canonical sub-zone name if valid, else None."""
    zone_key = (zone or "").upper()
    aliases = ZONE_ALIASES.get(zone_key, {})
    key = _normalize_key(candidate)

    if not key:
        return None

    if key in aliases:
        return aliases[key]

    for alias, canonical in aliases.items():
        if alias in key or key in alias:
            return canonical

    for canonical in ZONE_SUBZONES.get(zone_key, []):
        if _normalize_key(canonical) == key:
            return canonical

    return None


def extract_sub_zone_from_text(zone: str, text: str) -> Optional[str]:
    """Scan text for a whitelisted sub-zone mention."""
    if not text:
        return None
    lowered = text.lower()
    zone_key = (zone or "").upper()
    for alias, canonical in ZONE_ALIASES.get(zone_key, {}).items():
        if alias in lowered:
            return canonical
    return None


def resolve_sub_zone(zone: str, location: str = "", text: str = "") -> Tuple[Optional[str], bool]:
    """
    Resolve sub-zone from location or original text.
    Returns (canonical_name, is_valid).
    """
    zone_key = (zone or "").upper()
    for candidate in (location, text):
        if not candidate:
            continue
        found = validate_sub_zone(zone_key, candidate)
        if found:
            return found, True
        found = extract_sub_zone_from_text(zone_key, candidate)
        if found:
            return found, True
    return None, False
