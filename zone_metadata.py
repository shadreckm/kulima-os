"""
KULIMA OS Pilot - Zone Metadata Configuration
==============================================

Zone-level metadata for settlement context and infrastructure gap inference.

INVARIANT COMPLIANCE:
- Zero-PII: No individual locations, addresses, or personal identifiers
- Coordination > Identity: Metadata describes zones, not people
- Deterministic: No external GIS, satellite data, or real-time APIs

This metadata enables LUNDAI to infer settlement context and infrastructure
gaps without requiring external data sources or violating privacy invariants.
"""

from typing import Dict, Literal

SettlementType = Literal["rural_agricultural", "peri_urban", "informal_settlement", "grid_edge"]
InfrastructureStatus = Literal["critical_gap", "underserved", "partial_coverage", "adequate"]

# Zone metadata for pilot demonstration
ZONE_METADATA: Dict[str, Dict] = {
    "zone_a": {
        "settlement_type": "rural_agricultural",
        "infrastructure_status": "underserved",
        "grid_connection": "partial",
        "distance_to_substation_km": 15,
        "transformer_capacity_kva": 50,
        "service_reliability": "intermittent",
        "essential_services_present": ["clinic", "school"],
        "productive_activities": ["irrigation", "milling"],
        "population_density_category": "low",  # Not precise count, just category
        "grid_edge_exposure": True,
        "description": "Rural agricultural zone with partial grid access, frequent outages, essential services present but vulnerable"
    },
    "zone_b": {
        "settlement_type": "peri_urban",
        "infrastructure_status": "partial_coverage",
        "grid_connection": "connected",
        "distance_to_substation_km": 5,
        "transformer_capacity_kva": 100,
        "service_reliability": "moderate",
        "essential_services_present": ["water_system", "emergency_services"],
        "productive_activities": ["cold_storage", "welding"],
        "population_density_category": "medium",
        "grid_edge_exposure": False,
        "description": "Peri-urban zone with grid connection but insufficient capacity for productive use expansion"
    },
    "zone_c": {
        "settlement_type": "informal_settlement",
        "infrastructure_status": "critical_gap",
        "grid_connection": "none",
        "distance_to_substation_km": 25,
        "transformer_capacity_kva": 0,
        "service_reliability": "none",
        "essential_services_present": ["water_system"],
        "productive_activities": ["milling", "irrigation"],
        "population_density_category": "medium",
        "grid_edge_exposure": True,
        "description": "Informal settlement with no grid access, critical infrastructure gap, essential services at risk"
    },
    # Pilot zone: Mzuzu, Northern Malawi — peri-urban city with partial grid coverage
    "mzuzu": {
        "settlement_type": "peri_urban",
        "infrastructure_status": "underserved",
        "grid_connection": "partial",
        "distance_to_substation_km": 8,
        "transformer_capacity_kva": 75,
        "service_reliability": "intermittent",
        "essential_services_present": ["clinic", "school", "water_system"],
        "productive_activities": ["irrigation", "milling", "cold_storage"],
        "population_density_category": "medium",
        "grid_edge_exposure": True,
        "description": "Peri-urban zone in northern Malawi with partial grid access and growing productive demand"
    },
    "MZUZU": {
        "settlement_type": "peri_urban",
        "infrastructure_status": "underserved",
        "grid_connection": "partial",
        "distance_to_substation_km": 8,
        "transformer_capacity_kva": 75,
        "service_reliability": "intermittent",
        "essential_services_present": ["clinic", "school", "water_system"],
        "productive_activities": ["irrigation", "milling", "cold_storage"],
        "population_density_category": "medium",
        "grid_edge_exposure": True,
        "description": "Peri-urban zone in northern Malawi with partial grid access and growing productive demand"
    },
}


def get_zone_metadata(zone: str) -> Dict:
    """
    Retrieve metadata for a zone.
    
    ZERO-PII ENFORCEMENT:
    - Returns only zone-level aggregates
    - No individual locations or identifiers
    
    Args:
        zone: Zone identifier (e.g., 'zone_a')
        
    Returns:
        Zone metadata dictionary
    """
    # Normalize zone key: try as-is first, then uppercase, then lowercase
    zone_key = zone
    if zone_key not in ZONE_METADATA:
        zone_key = zone.upper()
    if zone_key not in ZONE_METADATA:
        zone_key = zone.lower()
    return ZONE_METADATA.get(zone_key, {
        "settlement_type": "unknown",
        "infrastructure_status": "unknown",
        "grid_connection": "unknown",
        "distance_to_substation_km": 0,
        "transformer_capacity_kva": 0,
        "service_reliability": "unknown",
        "essential_services_present": [],
        "productive_activities": [],
        "population_density_category": "unknown",
        "grid_edge_exposure": False,
        "description": "No metadata available for this zone"
    })


def get_all_zones() -> list:
    """Return list of all zones with metadata."""
    return list(ZONE_METADATA.keys())


if __name__ == "__main__":
    import logging
    logger = logging.getLogger(__name__)
    logger.info("" + "=" * 60)
    logger.info("KULIMA OS PILOT - ZONE METADATA")
    logger.info("" + "=" * 60)

    for zone_id in get_all_zones():
        metadata = get_zone_metadata(zone_id)
        logger.info(f"\n{zone_id.upper()}:")
        logger.info(f"  Settlement Type: {metadata['settlement_type']}")
        logger.info(f"  Infrastructure Status: {metadata['infrastructure_status']}")
        logger.info(f"  Grid Connection: {metadata['grid_connection']}")
        logger.info(f"  Essential Services: {', '.join(metadata['essential_services_present'])}")
        logger.info(f"  Grid Edge Exposure: {metadata['grid_edge_exposure']}")

    logger.info("\n" + "=" * 60)
    logger.info("[OK] Zero-PII: No individual identifiers in metadata")
    logger.info("[OK] Coordination > Identity: Zone-level aggregates only")
    logger.info("" + "=" * 60)

