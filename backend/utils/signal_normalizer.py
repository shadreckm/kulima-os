"""
Signal normalizer — delegates to adaptive NLP pipeline with zone whitelist.
"""
from typing import Dict

from backend.utils.nlp_pipeline import parse_signal_text, normalize_text
from backend.utils.zone_whitelist import resolve_sub_zone, PILOT_ZONES

_DEFAULT_ZONE = 'MZUZU'
_DEFAULT_LOCATION = ''


def normalize_signal_text(text: str, default_zone: str = _DEFAULT_ZONE, is_voice: bool = False) -> Dict:
    """
    Normalize free-text into a structured signal dictionary.
    Returns: activity_type, zone, time_window, location, sub_zone, crop, cluster_id, original_text
    """
    parsed = parse_signal_text(text, default_zone=default_zone, is_voice=is_voice)
    zone = parsed.get('zone', default_zone).upper()
    sub_zone = parsed.get('sub_zone')
    location = sub_zone or parsed.get('location') or ''

    if not sub_zone and location:
        resolved, valid = resolve_sub_zone(zone, location, text)
        if valid:
            sub_zone = resolved
            location = resolved

    cluster_id = f"{zone}-{sub_zone.replace(' ', '_')}" if sub_zone else None

    return {
        'activity_type': parsed.get('activity_type', 'unknown'),
        'zone': zone if zone in PILOT_ZONES else _DEFAULT_ZONE,
        'time_window': parsed.get('time_window', 'unknown'),
        'location': location,
        'sub_zone': sub_zone,
        'crop': parsed.get('crop', ''),
        'cluster_id': cluster_id,
        'intent_confidence': parsed.get('intent_confidence', 0.0),
        'normalized_text': parsed.get('normalized_text', ''),
        'original_text': parsed.get('original_text', text),
        'valid': parsed.get('valid', False),
    }


def normalize_signal_data(data: Dict) -> Dict:
    if not isinstance(data, dict):
        return normalize_signal_text(str(data))
    raw = data.get('original_text') or data.get('raw_text') or ''
    if raw:
        return normalize_signal_text(raw, default_zone=data.get('zone', _DEFAULT_ZONE))
    return {
        'activity_type': data.get('activity_type', 'unknown') or 'unknown',
        'zone': (data.get('zone') or _DEFAULT_ZONE).upper(),
        'time_window': data.get('time_window', 'unknown') or 'unknown',
        'location': data.get('location') or data.get('sub_zone') or '',
        'sub_zone': data.get('sub_zone'),
        'crop': data.get('crop', '') or '',
        'cluster_id': data.get('cluster_id'),
        'original_text': raw,
        'valid': True,
    }
