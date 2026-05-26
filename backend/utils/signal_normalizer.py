"""
Simple signal normalizer that extracts a small set of activities, zones, and time windows.
This file intentionally implements a minimal, robust parser used by webhooks and quick inputs.
"""
from typing import Dict

# Allowed activities, zones and time windows
_ACTIVITIES = ['irrigation', 'milling', 'trading', 'welding']
_ZONES = {
    'mzuzu': 'MZUZU',
    'lilongwe': 'LILONGWE',
    'blantyre': 'BLANTYRE',
    'zomba': 'ZOMBA'
}

# Expanded Malawi districts to reduce UNKNOWN fallbacks
# Keywords are substrings matched against the lowercased message
_ZONES.update({
    'karonga': 'KARONGA',
    'mzimba': 'MZIMBA',
    'nkhata': 'NKHATA_BAY',
    'nkhatabay': 'NKHATA_BAY',
    'rumphi': 'RUMPHI',
    'kasungu': 'KASUNGU',
    'dedza': 'DEDZA',
    'salima': 'SALIMA',
    'mangochi': 'MANGOCHI',
    'nsanje': 'NSANJE',
    'chikwawa': 'CHIKWAWA',
    'mulanje': 'MULANJE'
})
_TIME_KEYWORDS = {
    'morning': ['morning', 'am', 'early'],
    'afternoon': ['afternoon', 'pm', 'midday'],
    'evening': ['evening', 'night', 'late']
}


_DEFAULT_ZONE = 'MZUZU'


def normalize_signal_text(text: str) -> Dict:
    """
    Normalize a free-text message into a minimal structured signal dictionary.

    Returns keys: activity_type, zone, time_window, original_text
    Always returns original_text and uses robust contains checks on lowercase input.
    """
    if not isinstance(text, str):
        text = '' if text is None else str(text)
    lowered = text.lower()

    # Detect activity
    activity = 'unknown'
    for a in _ACTIVITIES:
        if a in lowered:
            activity = a
            break
    # some heuristics for common synonyms
    if activity == 'unknown':
        if 'mill' in lowered or 'grind' in lowered:
            activity = 'milling'
        elif 'sell' in lowered or 'market' in lowered:
            activity = 'trading'
        elif 'pump' in lowered or 'water' in lowered or 'irrigat' in lowered:
            activity = 'irrigation'
        elif 'weld' in lowered or 'metal' in lowered:
            activity = 'welding'

    # Detect zone
    zone = None
    for k, v in _ZONES.items():
        if k in lowered:
            zone = v
            break

    if not zone:
        zone = _DEFAULT_ZONE

    # Detect time window
    time_window = 'unknown'
    for window, keywords in _TIME_KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                time_window = window
                break
        if time_window != 'unknown':
            break

    return {
        'activity_type': activity,
        'zone': zone,
        'time_window': time_window,
        'original_text': text
    }


def normalize_signal_data(data: Dict) -> Dict:
    """Normalize already-structured data (compat helper)."""
    if not isinstance(data, dict):
        return {
            'activity_type': 'unknown',
            'zone': 'UNKNOWN',
            'time_window': 'unknown',
            'original_text': str(data)
        }
    return {
        'activity_type': data.get('activity_type', 'unknown') or 'unknown',
        'zone': (data.get('zone') or _DEFAULT_ZONE).upper(),
        'time_window': data.get('time_window', 'unknown') or 'unknown',
        'original_text': data.get('original_text') or data.get('raw_text') or ''
    }
