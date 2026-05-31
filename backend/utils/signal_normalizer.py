"""
Simple signal normalizer that extracts a set of activities, zones, time windows, location, and crop context.
This parser is designed for natural-language input from WhatsApp and manual entry forms.
"""
import re
from typing import Dict

# Allowed activities, zones and time windows
_ACTIVITIES = ['irrigation', 'milling', 'trading', 'welding', 'storage', 'farming']
_ZONES = {
    'mzuzu': 'MZUZU',
    'lilongwe': 'LILONGWE',
    'blantyre': 'BLANTYRE',
    'zomba': 'ZOMBA'
}

# Expanded Malawi districts to reduce UNKNOWN fallbacks
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
    'afternoon': ['afternoon', 'pm', 'midday', 'noon'],
    'evening': ['evening', 'night', 'late', 'tonight']
}
_CROP_KEYWORDS = ['maize', 'rice', 'tomato', 'tomatoes', 'beans', 'groundnut', 'cassava', 'potato', 'onion', 'sugarcane', 'pepper', 'banana', 'bananas', 'sorghum', 'millet']
_LOCATION_TERMS = ['area', 'block', 'ward', 'zone', 'market', 'village', 'town', 'estate']
_DEFAULT_ZONE = 'MZUZU'
_DEFAULT_LOCATION = 'Local area'


def _extract_location(text: str) -> str:
    lowered = text.lower()
    parts = re.split(r'\b(?:in|at|near)\b', lowered)
    if len(parts) > 1:
        candidate = parts[1].strip().split()[:3]
        candidate_text = ' '.join(candidate)
        if candidate_text:
            normalized = re.sub(r'[^a-z0-9 ]', ' ', candidate_text).strip()
            if normalized:
                return normalized.title()

    for term in _LOCATION_TERMS:
        pattern = rf"\b{term}\s*(\d+|[a-zA-Z]+(?:\s+[a-zA-Z]+)?)\b"
        match = re.search(pattern, lowered)
        if match:
            return match.group(0).title()

    return _DEFAULT_LOCATION


def _extract_crop(text: str) -> str:
    lowered = text.lower()
    for crop in _CROP_KEYWORDS:
        if crop in lowered:
            return crop
    return ''


def _detect_activity(text: str) -> str:
    lowered = text.lower()
    for activity in _ACTIVITIES:
        if activity in lowered:
            return activity
    if 'mill' in lowered or 'grind' in lowered:
        return 'milling'
    if 'sell' in lowered or 'market' in lowered or 'shop' in lowered:
        return 'trading'
    if 'pump' in lowered or 'water' in lowered or 'irrigat' in lowered or 'field' in lowered:
        return 'irrigation'
    if 'weld' in lowered or 'metal' in lowered or 'forge' in lowered:
        return 'welding'
    if 'store' in lowered or 'cold' in lowered or 'warehouse' in lowered:
        return 'storage'
    if 'farm' in lowered or 'plant' in lowered or 'harvest' in lowered or 'growing' in lowered:
        return 'farming'
    return 'unknown'


def _detect_zone(text: str) -> str:
    lowered = text.lower()
    for key, value in _ZONES.items():
        if key in lowered:
            return value
    return _DEFAULT_ZONE


def _detect_time_window(text: str) -> str:
    lowered = text.lower()
    for window, keywords in _TIME_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                return window
    return 'unknown'


def normalize_signal_text(text: str) -> Dict:
    """
    Normalize a free-text message into a structured signal dictionary.

    Returns keys: activity_type, zone, time_window, location, crop, cluster_id, original_text
    """
    if not isinstance(text, str):
        text = '' if text is None else str(text)
    zone = _detect_zone(text)
    location = _extract_location(text)
    activity_type = _detect_activity(text)
    time_window = _detect_time_window(text)
    crop = _extract_crop(text)

    cluster_id = f"{zone}-{location.replace(' ', '_')}" if location else f"{zone}-Local"

    return {
        'activity_type': activity_type,
        'zone': zone,
        'time_window': time_window,
        'location': location,
        'crop': crop,
        'cluster_id': cluster_id,
        'original_text': text
    }


def normalize_signal_data(data: Dict) -> Dict:
    """Normalize already-structured data (compat helper)."""
    if not isinstance(data, dict):
        return {
            'activity_type': 'unknown',
            'zone': 'UNKNOWN',
            'time_window': 'unknown',
            'location': _DEFAULT_LOCATION,
            'crop': '',
            'cluster_id': 'UNKNOWN-Local',
            'original_text': str(data)
        }
    return {
        'activity_type': data.get('activity_type', 'unknown') or 'unknown',
        'zone': (data.get('zone') or _DEFAULT_ZONE).upper(),
        'time_window': data.get('time_window', 'unknown') or 'unknown',
        'location': data.get('location') or _DEFAULT_LOCATION,
        'crop': data.get('crop', '') or '',
        'cluster_id': data.get('cluster_id') or f"{data.get('zone', _DEFAULT_ZONE)}-Local",
        'original_text': data.get('original_text') or data.get('raw_text') or ''
    }
