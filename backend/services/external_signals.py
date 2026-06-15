"""
External activity signal helpers for Kulima OS.

This service provides synthetic external signal generation and source
normalization for pipeline augmentation. It is intentionally lightweight
and preserves coordination-first invariants.
"""

from datetime import datetime
from typing import Dict, List

# Source categories used throughout the backend pipeline
KNOWN_SOURCES = {
    'web',
    'whatsapp',
    'manual',
    'social',
    'news',
    'system',
    'telemetry',
    'sensor',
    'infrastructure',
    'external',
    'user',
}

HUMAN_REPORTED_SOURCES = {
    'web',
    'whatsapp',
    'manual',
    'social',
    'news',
    'system',
    'external',
    'user',
}

TELEMETRY_SOURCES = {
    'telemetry',
    'sensor',
    'infrastructure',
}

DEFAULT_EXTERNAL_SIGNALS = {
    'MZUZU': [
        {
            'activity_type': 'irrigation',
            'zone': 'MZUZU',
            'time_window': 'morning',
            'location': 'community observation',
            'signal_source': 'social',
            'source': 'social',
            'service_priority': 'productive',
            'original_text': 'Social media reports indicate morning irrigation activity in Mzuzu.',
        },
        {
            'activity_type': 'milling',
            'zone': 'MZUZU',
            'time_window': 'afternoon',
            'location': 'market district',
            'signal_source': 'news',
            'source': 'news',
            'service_priority': 'productive',
            'original_text': 'News reports mention increased milling demand in the zone.',
        }
    ],
    'LILONGWE': [
        {
            'activity_type': 'water_system',
            'zone': 'LILONGWE',
            'time_window': 'morning',
            'location': 'urban supply node',
            'signal_source': 'system',
            'source': 'system',
            'service_priority': 'essential',
            'original_text': 'System-derived water system usage suggests active morning pumping.',
        },
        {
            'activity_type': 'trading',
            'zone': 'LILONGWE',
            'time_window': 'afternoon',
            'location': 'central market',
            'signal_source': 'social',
            'source': 'social',
            'service_priority': 'productive',
            'original_text': 'Community chatter points to afternoon trading and market activity.',
        }
    ],
    'BLANTYRE': [
        {
            'activity_type': 'cold_storage',
            'zone': 'BLANTYRE',
            'time_window': 'evening',
            'location': 'cold chain facility',
            'signal_source': 'system',
            'source': 'system',
            'service_priority': 'productive',
            'original_text': 'System logs indicate active cold storage draw in Blantyre.',
        },
        {
            'activity_type': 'milling',
            'zone': 'BLANTYRE',
            'time_window': 'afternoon',
            'location': 'processing hub',
            'signal_source': 'news',
            'source': 'news',
            'service_priority': 'productive',
            'original_text': 'Market reports show milling demand in the afternoon.',
        }
    ],
    'ZOMBA': [
        {
            'activity_type': 'irrigation',
            'zone': 'ZOMBA',
            'time_window': 'morning',
            'location': 'river pump station',
            'signal_source': 'system',
            'source': 'system',
            'service_priority': 'productive',
            'original_text': 'System sensors and reports indicate irrigation activity near Zomba.',
        },
        {
            'activity_type': 'trading',
            'zone': 'ZOMBA',
            'time_window': 'evening',
            'location': 'town market',
            'signal_source': 'social',
            'source': 'social',
            'service_priority': 'productive',
            'original_text': 'Local news mentions evening trading clusters in Zomba.',
        }
    ],
}


def normalize_signal_source(source: str) -> str:
    """Normalize signal sources into known provenance categories."""
    if not source or not isinstance(source, str):
        return 'web'

    normalized = source.strip().lower()
    if normalized in KNOWN_SOURCES:
        return normalized

    if normalized.startswith('whatsapp'):
        return 'whatsapp'
    if normalized.startswith('web'):
        return 'web'
    if any(token in normalized for token in ['social', 'media', 'survey', 'report']):
        return 'social'
    if any(token in normalized for token in ['news', 'bulletin', 'press']):
        return 'news'
    if any(token in normalized for token in ['telemetry', 'sensor', 'infrastructure', 'device']):
        return 'telemetry'
    if any(token in normalized for token in ['system', 'external']):
        return 'external'

    return 'external'


def source_category(source: str) -> str:
    """Classify a normalized source into a broader category."""
    normalized = normalize_signal_source(source)
    if normalized in TELEMETRY_SOURCES:
        return 'telemetry'
    if normalized in HUMAN_REPORTED_SOURCES:
        return 'human'
    return 'unknown'


def is_telemetry_source(source: str) -> bool:
    return normalize_signal_source(source) in TELEMETRY_SOURCES


def is_human_reported_source(source: str) -> bool:
    return normalize_signal_source(source) in HUMAN_REPORTED_SOURCES


def generate_external_signals(zone: str) -> List[Dict]:
    """Generate synthetic external activity signals for a zone.

    These are added to the pipeline as corroborating external provenance.
    """
    zone_key = (zone or '').strip().upper()
    base_signals = DEFAULT_EXTERNAL_SIGNALS.get(zone_key, [])
    result = []
    now_iso = datetime.utcnow().isoformat() + 'Z'

    for signal in base_signals:
        entry = {
            'zone': signal['zone'],
            'activity_type': signal['activity_type'],
            'time_window': signal['time_window'],
            'location': signal['location'],
            'timestamp': now_iso,
            'signal_source': normalize_signal_source(signal['signal_source']),
            'source': normalize_signal_source(signal.get('source', signal['signal_source'])),
            'user_phone': None,
            'service_priority': signal.get('service_priority', 'productive'),
            'original_text': signal.get('original_text', ''),
        }
        result.append(entry)

    return result


def augment_signals_with_external_sources(signals: List[Dict], zone: str) -> List[Dict]:
    """Return signal list augmented with external provenance signals for the same zone."""
    if not signals or not zone:
        return signals

    external_signals = generate_external_signals(zone)
    if not external_signals:
        return signals

    # Avoid duplicate exact signals in the merged list
    existing_set = {
        (s.get('activity_type'), s.get('zone'), s.get('time_window'), s.get('signal_source'), s.get('original_text'))
        for s in signals
    }
    augmented = list(signals)
    for external in external_signals:
        key = (
            external.get('activity_type'),
            external.get('zone'),
            external.get('time_window'),
            external.get('signal_source'),
            external.get('original_text'),
        )
        if key not in existing_set:
            augmented.append(external)
    return augmented


def count_signal_sources(signals: List[Dict]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for signal in signals:
        source = normalize_signal_source(signal.get('source') or signal.get('signal_source') or '')
        counts[source] = counts.get(source, 0) + 1
    return counts


def compute_provenance_confidence(source_counts: Dict[str, int]) -> Dict[str, any]:
    """Compute provenance-derived confidence with multi-source validation rules."""
    if not source_counts:
        return {
            "community_count": 0,
            "external_count": 0,
            "system_count": 0,
            "unique_sources": 0,
            "label": "LOW",
            "boost": -0.15,
        }

    community_keys = ['web', 'whatsapp', 'manual', 'user', 'social']
    external_keys = ['news', 'external']
    system_keys = ['telemetry', 'sensor', 'infrastructure', 'system']

    community_count = sum(source_counts.get(k, 0) for k in community_keys)
    external_count = sum(source_counts.get(k, 0) for k in external_keys)
    system_count = sum(source_counts.get(k, 0) for k in system_keys)

    unique_sources = sum(1 for count in [community_count, external_count, system_count] if count > 0)

    # Minimum source rule: fewer than 2 categories reduces trust
    if unique_sources < 2:
        return {
            "community_count": int(community_count),
            "external_count": int(external_count),
            "system_count": int(system_count),
            "unique_sources": unique_sources,
            "label": "LOW",
            "boost": -0.15,
        }

    category_present = 0
    if community_count >= 1:
        category_present += 1
    if external_count >= 1:
        category_present += 1
    if system_count >= 1:
        category_present += 1

    if category_present >= 3:
        label = 'HIGH'
        boost = 0.12
    elif category_present == 2:
        label = 'MEDIUM'
        boost = 0.06
    else:
        label = 'LOW'
        boost = -0.05

    return {
        "community_count": int(community_count),
        "external_count": int(external_count),
        "system_count": int(system_count),
        "unique_sources": unique_sources,
        "label": label,
        "boost": boost,
    }


def deduplicate_signals(signals: List[Dict]) -> List[Dict]:
    """Remove duplicate signals based on activity, zone, time window, source, and text."""
    seen = set()
    unique: List[Dict] = []
    for signal in signals:
        key = (
            signal.get('activity_type'),
            signal.get('zone'),
            signal.get('time_window'),
            normalize_signal_source(signal.get('source') or signal.get('signal_source') or ''),
            (signal.get('original_text') or '').strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(signal)
    return unique
