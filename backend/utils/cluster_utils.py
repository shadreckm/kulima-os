"""
Cluster utilities for grouping activity signals into geographic clusters.
"""
import re
from typing import List, Dict, Any

KNOWN_LOCATIONS = [
    'luwinga', 'mchesi', 'chengani', 'chatinkha', 'chibanja', 'katoto',
    'area 25', 'area 26', 'area 27', 'area 16', 'area 17', 'area 18',
    'area 19', 'area 20', 'kampanja', 'bingu', 'boma', 'tengani', 'nkhoma',
    'limbe', 'chirimba', 'zomba', 'blantyre', 'lilongwe', 'mzuzu',
    'karonga', 'kasungu', 'dowa'
]

CROP_KEYWORDS = {
    'maize', 'rice', 'tomatoes', 'tomato', 'beans', 'groundnut', 'cassava',
    'potato', 'onion', 'sugarcane', 'vegetables', 'cashew', 'tea', 'tobacco',
    'bananas', 'banana', 'sorghum', 'millet', 'pepper', 'chilies'
}

ACTIVITY_SYNONYMS = {
    'irrigation': ['irrigation', 'pump', 'water', 'watering', 'sprinkler'],
    'trading': ['trade', 'trading', 'sell', 'sold', 'buy', 'buying', 'market', 'marketday', 'market day', 'shop'],
    'milling': ['milling', 'mill', 'grind', 'grinding'],
    'welding': ['welding', 'weld', 'metalwork', 'forge'],
    'storage': ['storage', 'store', 'warehouse', 'cold storage', 'coldchain', 'cold chain'],
    'farming': ['farm', 'farming', 'grow', 'growing', 'plant', 'planting', 'harvest', 'harvesting']
}

TIME_WINDOW_KEYWORDS = {
    'morning': ['morning', 'am', 'early'],
    'afternoon': ['afternoon', 'pm', 'midday', 'noon'],
    'evening': ['evening', 'night', 'late', 'tonight']
}

LOCATION_PATTERNS = [
    r"\bin\s+(area\s*\d+)\b",
    r"\bin\s+(block\s*\d+)\b",
    r"\bin\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})\b",
    r"\bat\s+(area\s*\d+)\b",
    r"\bat\s+(block\s*\d+)\b",
    r"\bat\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})\b",
    r"\bnear\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})\b"
]

DEFAULT_LOCATION = 'Local area'
DEFAULT_ZONE = 'MZUZU'


def _normalize_location_name(location: str) -> str:
    if not location or not isinstance(location, str):
        return DEFAULT_LOCATION
    location = location.strip().lower()
    if not location:
        return DEFAULT_LOCATION

    location = re.sub(r"[^a-z0-9 ]+", " ", location)
    location = re.sub(r"\s+", " ", location).strip()

    # Preserve area labels
    if re.match(r"^(area|block|ward)\s*\d+$", location):
        return location.title()

    # Normalize common place names
    for known in KNOWN_LOCATIONS:
        if known in location:
            return known.title()

    return location.title()


def _extract_text_location(text: str, zone: str = DEFAULT_ZONE) -> str:
    if not isinstance(text, str):
        return DEFAULT_LOCATION
    lowered = text.lower()

    # explicit area/block matches
    for pattern in LOCATION_PATTERNS:
        match = re.search(pattern, lowered)
        if match:
            candidate = match.group(1)
            normalized = _normalize_location_name(candidate)
            if normalized and normalized != DEFAULT_LOCATION:
                return normalized

    # location by known place names
    for known in KNOWN_LOCATIONS:
        if known in lowered:
            return known.title()

    return DEFAULT_LOCATION


def _extract_crop(text: str) -> str:
    if not isinstance(text, str):
        return ''
    lowered = text.lower()
    crops = [crop for crop in CROP_KEYWORDS if crop in lowered]
    if crops:
        return crops[0]
    return ''


def _extract_activity_type(text: str) -> str:
    if not isinstance(text, str):
        return 'unknown'
    lowered = text.lower()
    for activity, synonyms in ACTIVITY_SYNONYMS.items():
        for synonym in synonyms:
            if synonym in lowered:
                return activity
    return 'unknown'


def _extract_time_window(text: str) -> str:
    if not isinstance(text, str):
        return 'unknown'
    lowered = text.lower()
    for window, keywords in TIME_WINDOW_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                return window
    return 'unknown'


def normalize_cluster_signal_text(text: str, default_zone: str = DEFAULT_ZONE) -> Dict[str, str]:
    if not isinstance(text, str):
        text = '' if text is None else str(text)

    zone = default_zone
    lowered = text.lower()
    for key in KNOWN_LOCATIONS:
        if key in lowered and key.upper() in {'MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA'}:
            zone = key.upper()
            break
    # fallback if a full zone name is present
    for member in ['mzuzu', 'lilongwe', 'blantyre', 'zomba']:
        if member in lowered:
            zone = member.upper()
            break

    location = _extract_text_location(text, zone)
    activity_type = _extract_activity_type(text)
    time_window = _extract_time_window(text)
    crop = _extract_crop(text)

    cluster_id = f"{zone}-{location.replace(' ', '_')}" if location else f"{zone}-local"

    return {
        'activity_type': activity_type,
        'location': location,
        'zone': zone,
        'time_window': time_window,
        'crop': crop,
        'cluster_id': cluster_id,
        'original_text': text
    }


def _infer_demand_pattern(time_windows, signal_count: int) -> str:
    if isinstance(time_windows, set):
        windows_set = time_windows
    else:
        windows_set = set(time_windows or [])
    windows = sorted(windows_set - {'unknown'})
    window_label = ', '.join(windows) if windows else 'mixed windows'
    cycles = min(signal_count, 7)
    return f"{window_label.title()} peaks, {cycles} of 7 cycles"


def _compute_cluster_confidence(signal_count: int, activity_counts: Dict[str, int]) -> float:
  """Estimate cluster confidence from signal density and activity concentration."""
  if signal_count <= 0:
      return 0.0
  top_count = max(activity_counts.values()) if activity_counts else 0
  density = min(signal_count / 7.0, 1.0)
  concentration = top_count / max(signal_count, 1)
  return round(min(0.95, 0.35 + (0.4 * density) + (0.25 * concentration)), 2)


def build_cluster_summary(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    clusters: Dict[str, Dict[str, Any]] = {}

    for signal in signals:
        if not signal or not isinstance(signal, dict):
            continue

        zone = (signal.get('zone') or DEFAULT_ZONE).upper()
        location = signal.get('location') or signal.get('sub_zone') or DEFAULT_LOCATION
        sub_zone = signal.get('sub_zone') or (location if location != DEFAULT_LOCATION else 'General')
        cluster_id = signal.get('cluster_id') or f"{zone}-{sub_zone.replace(' ', '_')}"
        activity = (signal.get('activity_type') or signal.get('activity') or 'unknown').lower()
        crop = signal.get('crop') or ''
        time_window = signal.get('time_window') or 'unknown'

        key = cluster_id
        if key not in clusters:
            clusters[key] = {
                'cluster_id': key,
                'cluster_name': f"{sub_zone} Cluster" if sub_zone and sub_zone != 'General' else f"{zone} Local Cluster",
                'zone': zone,
                'sub_zone': sub_zone,
                'location': location,
                'activities': {},
                'crops': set(),
                'time_windows': set(),
                'signals': [],
                'signal_count': 0,
                'summary': '',
                'infrastructure_gaps': [],
                'recommended_projects': []
            }

        cluster = clusters[key]
        cluster['signal_count'] += 1
        cluster['activities'][activity] = cluster['activities'].get(activity, 0) + 1
        if crop:
            cluster['crops'].add(crop)
        if time_window:
            cluster['time_windows'].add(time_window)
        cluster['signals'].append(signal)

    for cluster in clusters.values():
        activity_counts = cluster['activities']
        crop_list = sorted(cluster['crops'])
        top_activities = sorted(activity_counts.items(), key=lambda item: item[1], reverse=True)

        infrastructure_gaps = []
        recommended_projects = []

        irrigation_count = activity_counts.get('irrigation', 0)
        farming_count = activity_counts.get('farming', 0)
        milling_count = activity_counts.get('milling', 0)
        trading_count = activity_counts.get('trading', 0)
        storage_count = activity_counts.get('storage', 0)
        welding_count = activity_counts.get('welding', 0)

        if irrigation_count >= 2 or farming_count >= 2:
            infrastructure_gaps.append('No reliable irrigation system')
            recommended_projects.append('Community irrigation scheme')

        if storage_count >= 1 or trading_count >= 2 or crop_list:
            infrastructure_gaps.append('No storage facility or cold chain')
            recommended_projects.append('Community storage center')

        if milling_count >= 1:
            infrastructure_gaps.append('No local milling or processing facility')
            recommended_projects.append('Local grain milling facility')

        if trading_count >= 2:
            infrastructure_gaps.append('No organized market access for traders')
            recommended_projects.append('Market access hub for local trade')

        if welding_count >= 1:
            infrastructure_gaps.append('No reliable workshop or power supply for metalwork')
            recommended_projects.append('Community workshop with reliable power')

        if not infrastructure_gaps:
            infrastructure_gaps.append('No dedicated local infrastructure identified yet')
            recommended_projects.append('Reliable power access for cluster activities')

        cluster_summary = []
        if top_activities:
            cluster_summary.append(
                f"Top activities: {', '.join([f'{act.title()} ({count})' for act, count in top_activities])}."
            )
        if crop_list:
            cluster_summary.append(f"Crops mentioned: {', '.join(crop_list)}.")
        cluster_summary.append(f"Matched {cluster['signal_count']} activity signals in this cluster.")

        cluster['crops'] = crop_list
        cluster['top_activities'] = [act for act, _ in top_activities]
        cluster['infrastructure_gaps'] = infrastructure_gaps
        cluster['recommended_projects'] = sorted(set(recommended_projects), key=lambda x: x)
        cluster['summary'] = ' '.join(cluster_summary)

        dominant_activity = top_activities[0][0] if top_activities else 'unknown'
        cluster['dominant_activity'] = dominant_activity
        cluster['demand_pattern'] = _infer_demand_pattern(cluster['time_windows'], cluster['signal_count'])
        cluster['key_gap'] = infrastructure_gaps[0] if infrastructure_gaps else 'No dedicated local infrastructure identified yet'
        cluster['recommended_project'] = cluster['recommended_projects'][0] if cluster['recommended_projects'] else 'Reliable power access for cluster activities'
        cluster['confidence_score'] = _compute_cluster_confidence(cluster['signal_count'], activity_counts)
        cluster['time_windows'] = sorted(cluster['time_windows'])

    sorted_clusters = sorted(clusters.values(), key=lambda c: c['signal_count'], reverse=True)
    return sorted_clusters
