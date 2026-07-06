"""
Adaptive NLP pipeline for Kulima OS signal ingestion.
Text + voice transcripts → structured coordination signals (Zero-PII).
"""
import re
from typing import Dict, List, Tuple

FILLER_WORDS = frozenset({
    "um", "uh", "er", "ah", "like", "you know", "i mean", "basically",
    "actually", "so", "well", "okay", "ok", "please", "thanks", "thank you",
})

SPELL_CORRECTIONS = {
    # English typo corrections
    "irrigaton": "irrigation",
    "irrigatng": "irrigation",
    "irigation": "irrigation",
    "irrigatin": "irrigation",
    "wtering": "watering",
    "farmng": "farming",
    "miling": "milling",
    "trding": "trading",
    "storag": "storage",
    "mzuz": "mzuzu",
    "lilongw": "lilongwe",
    "blantyr": "blantyre",
    "maize": "maize",
    "tomatoe": "tomato",
    "ekwendni": "ekwendeni",
    "mhuj": "mhuju",
    "bweng": "bwengu",
    "rumphe": "rumphi",
    "euthni": "euthini",
    # Chichewa / Tumbuka phonetic variants
    "kuthirira": "irrigation",   # Chichewa: to irrigate
    "kuyeretsa": "irrigation",   # Chichewa: to water/clean (plants)
    "chigayo": "milling",        # Chichewa: grinding mill
    "mgayo": "milling",          # Chichewa: milling/grinding
    "kugaya": "milling",         # Chichewa: to grind/mill
    "msika": "trading",          # Chichewa: market
    "msitulo": "trading",        # Chichewa: shop/trading
    "kugulitsa": "trading",      # Chichewa: to sell
    "kugula": "trading",         # Chichewa: to buy
    "dimba": "irrigation",       # Chichewa: winter garden (dimba irrigation)
    "madimba": "irrigation",     # Chichewa: plural of dimba (winter gardens)
    "nkhokwe": "storage",        # Chichewa: granary/storage hut
    "kusunga": "storage",        # Chichewa: to store/keep
    "mpunga": "farming",         # Chichewa: rice farming
    "ulimi": "farming",          # Chichewa: farming/agriculture
    "kulima": "farming",         # Chichewa: to farm (root of Kulima OS name)
    "mbewu": "farming",          # Chichewa: seed (seed request = farming context)
    "fetelaiza": "farming",      # Chichewa phonetic: fertilizer
}

INTENT_PATTERNS: List[Tuple[str, List[str], float]] = [
    ("irrigation", [
        # English terms
        "irrigation", "irrigat", "watering", "water crops", "watering crops",
        "pump water", "sprinkler", "drip", "irrigate", "need water", "water shortage",
        # Chichewa / local terms
        "kuthirira", "kuyeretsa", "dimba", "madimba", "water pump", "pump broken",
        "water dry", "river dry", "borehole dry", "bwino madzi",
    ], 0.85),
    ("farming", [
        # English terms
        "farming", "farm", "planting", "plant crops", "growing", "harvest",
        "cultivate", "agriculture", "field work", "grow maize",
        # Chichewa / local terms
        "kulima", "ulimi", "mpunga", "mbewu", "seed", "fertilizer", "fetelaiza",
        "no seed", "no maize seed", "seed shortage", "input shortage",
        "npk", "urea", "lime", "pesticide",
    ], 0.8),
    ("trading", [
        # English terms
        "trading", "selling", "sell maize", "selling maize", "market", "buying",
        "shop", "vendor", "trade", "sold", "market day",
        # Chichewa / local terms
        "msika", "msitulo", "kugulitsa", "kugula", "stock out", "stockout",
        "no stock", "out of stock", "supply", "depot",
    ], 0.85),
    ("milling", [
        # English terms
        "milling", "mill", "grinding", "grind maize", "processing grain", "grain mill",
        "posho mill", "hammer mill", "queue", "long queue",
        # Chichewa / local terms
        "chigayo", "mgayo", "kugaya", "chigayo chathu", "chigayo chawonongeka",
    ], 0.85),
    ("storage", [
        # English terms
        "storage", "warehouse", "cold storage", "cold chain", "store crops",
        "store maize", "silo", "post harvest", "post-harvest",
        # Chichewa / local terms
        "nkhokwe", "kusunga", "granary", "storage hut",
    ], 0.85),
    ("welding", [
        "welding", "weld", "metalwork", "forge", "fabrication", "repair",
        "broken pump", "chigayo chawonongeka",
    ], 0.8),
    ("energy", [
        "energy", "power", "electricity", "solar", "grid", "blackout",
        "load shedding", "generator", "no power", "power cut", "outage",
    ], 0.75),
]

RESOURCE_KEYWORDS = {
    "water": ["water", "pump", "borehole", "river", "irrigation"],
    "energy": ["power", "energy", "electricity", "solar", "grid"],
    "storage": ["storage", "warehouse", "cold chain"],
}

TIME_KEYWORDS = {
    "morning": [
        "morning", "am", "early", "dawn", "6am", "7am", "8am",
        # Chichewa: m'mawa = morning
        "m'mawa", "mmawa", "sunrise", "cockcrow",
    ],
    "afternoon": [
        "afternoon", "pm", "midday", "noon", "lunch",
        # Chichewa: masana = afternoon/midday
        "masana", "midday",
    ],
    "evening": [
        "evening", "night", "late", "tonight", "dusk",
        # Chichewa: madzulo = evening
        "madzulo", "sunset", "after work",
    ],
}

ZONE_KEYWORDS = {
    # Northern Malawi pilot zones (primary)
    "ekwendeni": "EKWENDENI",
    "mhuju": "MHUJU",
    "bwengu": "BWENGU",
    "rumphi": "RUMPHI",
    "euthini": "EUTHINI",
    "mzuzu": "MZUZU",
    "mzimba": "MZIMBA",
    # Broader Malawi zones (secondary)
    "lilongwe": "LILONGWE",
    "blantyre": "BLANTYRE",
    "zomba": "ZOMBA",
    "kasungu": "KASUNGU",
    "karonga": "KARONGA",
}

MIN_TEXT_LENGTH = 8
MIN_VOICE_LENGTH = 4
INTENT_CONFIDENCE_THRESHOLD = 0.45


def _safe_str(value) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        return str(value)
    return value


def normalize_text(text: str) -> str:
    """Lowercase, strip noise, basic spell correction, tokenize-ready string."""
    text = _safe_str(text).strip()
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s'-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = []
    for token in text.split():
        tokens.append(SPELL_CORRECTIONS.get(token, token))
    return " ".join(tokens)


def clean_voice_transcript(transcript: str) -> str:
    """Remove filler words and normalize voice capture."""
    text = normalize_text(transcript)
    if not text:
        return ""
    tokens = []
    for token in text.split():
        if token in FILLER_WORDS:
            continue
        tokens.append(token)
    return " ".join(tokens).strip()


def extract_intent(text: str) -> Tuple[str, float]:
    """Detect activity intent with confidence score."""
    normalized = normalize_text(text)
    if not normalized:
        return "unknown", 0.0

    best_activity = "unknown"
    best_score = 0.0

    for activity, patterns, base_confidence in INTENT_PATTERNS:
        for pattern in patterns:
            if pattern in normalized:
                score = base_confidence + min(0.1, len(pattern) / 100)
                if score > best_score:
                    best_score = score
                    best_activity = activity

    if best_score < INTENT_CONFIDENCE_THRESHOLD:
        return "unknown", best_score
    return best_activity, round(min(best_score, 1.0), 2)


def extract_time_window(text: str) -> str:
    normalized = normalize_text(text)
    for window, keywords in TIME_KEYWORDS.items():
        for kw in keywords:
            if kw in normalized:
                return window
    return "unknown"


def extract_zone(text: str, default_zone: str = "MZUZU") -> str:
    normalized = normalize_text(text)
    for key, value in ZONE_KEYWORDS.items():
        if key in normalized:
            return value
    return default_zone.upper()


def extract_crop(text: str) -> str:
    crops = ["maize", "rice", "tomato", "tomatoes", "beans", "groundnut", "cassava", "sorghum"]
    normalized = normalize_text(text)
    for crop in crops:
        if crop in normalized:
            return crop.rstrip("s") if crop == "tomatoes" else crop
    return ""


def parse_signal_text(text: str, default_zone: str = "MZUZU", is_voice: bool = False) -> Dict:
    """
    Full NLP parse pipeline.
    Returns structured dict with confidence metadata.
    """
    raw = _safe_str(text)
    cleaned = clean_voice_transcript(raw) if is_voice else normalize_text(raw)

    min_len = MIN_VOICE_LENGTH if is_voice else MIN_TEXT_LENGTH
    if len(cleaned) < min_len:
        return {
            "valid": False,
            "reason": "too_short",
            "activity_type": "unknown",
            "zone": default_zone.upper(),
            "time_window": "unknown",
            "location": "",
            "sub_zone": None,
            "crop": "",
            "intent_confidence": 0.0,
            "original_text": raw,
            "normalized_text": cleaned,
        }

    zone = extract_zone(cleaned, default_zone)
    activity, confidence = extract_intent(cleaned)

    from backend.utils.zone_whitelist import extract_sub_zone_from_text, validate_sub_zone

    sub_zone = extract_sub_zone_from_text(zone, cleaned)
    location = sub_zone or ""

    if not sub_zone:
        loc_match = re.search(r"\b(?:in|at|near)\s+([a-z0-9 ]{2,30})", cleaned)
        if loc_match:
            candidate = loc_match.group(1).strip()
            validated = validate_sub_zone(zone, candidate)
            if validated:
                sub_zone = validated
                location = validated

    return {
        "valid": activity != "unknown" or confidence >= INTENT_CONFIDENCE_THRESHOLD,
        "reason": "ok" if activity != "unknown" else "low_confidence",
        "activity_type": activity if activity != "unknown" else "farming",
        "zone": zone,
        "time_window": extract_time_window(cleaned),
        "location": location,
        "sub_zone": sub_zone,
        "crop": extract_crop(cleaned),
        "intent_confidence": confidence,
        "original_text": raw,
        "normalized_text": cleaned,
        "cluster_id": f"{zone}-{sub_zone.replace(' ', '_')}" if sub_zone else None,
    }
