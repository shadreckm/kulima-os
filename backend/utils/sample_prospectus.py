"""
Sample prospectus fallback for zones with insufficient coordination signals.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.services.refresh_service import get_refresh_metadata

_SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_prospectus.json"
_CACHE: Optional[Dict[str, Any]] = None


def _load_sample_data() -> Dict[str, Any]:
    global _CACHE
    if _CACHE is None:
        with open(_SAMPLE_PATH, encoding="utf-8") as f:
            _CACHE = json.load(f)
    return _CACHE


def build_simulated_summary(zone: str, mode: str = "investor", signal_count: int = 0) -> Dict[str, Any]:
    """Return a high-quality simulated prospectus payload for low-data zones."""
    sample = _load_sample_data()
    zone_key = (zone or "MZUZU").upper()
    zone_clusters: List[Dict[str, Any]] = sample.get("zone_clusters", {}).get(
        zone_key, sample.get("clusters", [])
    )

    mode_data = sample.get("mode_outputs", {}).get(mode, {})
    key_finding = mode_data.get("key_finding", sample.get("key_finding", ""))

    cluster_summaries = [
        {
            "cluster_id": c.get("cluster_id"),
            "cluster_name": f"{c.get('sub_zone', 'Local')} Cluster",
            "sub_zone": c.get("sub_zone"),
            "summary": {
                "signal_count": 6,
                "top_activities": [c.get("dominant_activity", "irrigation")],
                "dominant_activity": c.get("dominant_activity"),
                "key_gap": c.get("key_gap"),
                "recommended_project": c.get("recommended_project"),
            },
        }
        for c in zone_clusters
    ]

    result: Dict[str, Any] = {
        "zone": zone_key,
        "signal_count": max(signal_count, 14),
        "total_patterns": sample.get("total_patterns", 4),
        "high_confidence_patterns": sample.get("high_confidence_patterns", 3),
        "moderate_confidence_patterns": sample.get("moderate_confidence_patterns", 1),
        "zones_with_coordinated_demand": [zone_key],
        "productive_activities_detected": sample.get("productive_activities_detected", []),
        "key_finding": key_finding,
        "trust_score": sample.get("trust_score", 0.74),
        "confidence_breakdown": sample.get("confidence_breakdown", {}),
        "infrastructure_gaps": sample.get("infrastructure_gaps", []),
        "recommended_projects": sample.get("recommended_projects", []),
        "is_simulated": True,
        "clusters": zone_clusters,
        "cluster_summaries": cluster_summaries,
    }

    if mode == "investor":
        result["opportunity_ranking"] = mode_data.get("opportunity_ranking", [])
    elif mode == "government":
        result["service_coverage"] = mode_data.get("service_coverage", [])
    elif mode == "ngo":
        result["access_gaps"] = mode_data.get("access_gaps", [])

    result.update(get_refresh_metadata())
    return result
