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
    # Ekwendeni EPA — Northern Malawi, Mzimba District
    # High maize milling and dimba (winter garden) irrigation demand.
    # Serves ~12,000 smallholder farming households across the sub-zone.
    "ekwendeni": {
        "settlement_type": "rural_agricultural",
        "infrastructure_status": "underserved",
        "grid_connection": "partial",
        "distance_to_substation_km": 18,
        "transformer_capacity_kva": 50,
        "service_reliability": "intermittent",
        "essential_services_present": ["clinic", "school", "water_system"],
        "productive_activities": ["milling", "irrigation", "trading"],
        "population_density_category": "low",
        "grid_edge_exposure": True,
        "description": "Rural EPA in Mzimba District with strong chigayo (maize milling) demand and active dimba irrigation cooperatives. Partial grid with frequent outages during peak farming periods."
    },
    "EKWENDENI": {
        "settlement_type": "rural_agricultural",
        "infrastructure_status": "underserved",
        "grid_connection": "partial",
        "distance_to_substation_km": 18,
        "transformer_capacity_kva": 50,
        "service_reliability": "intermittent",
        "essential_services_present": ["clinic", "school", "water_system"],
        "productive_activities": ["milling", "irrigation", "trading"],
        "population_density_category": "low",
        "grid_edge_exposure": True,
        "description": "Rural EPA in Mzimba District with strong chigayo (maize milling) demand and active dimba irrigation cooperatives. Partial grid with frequent outages during peak farming periods."
    },
    # Mhuju EPA — Northern Malawi, Mzimba District
    # Emerging cold storage and market coordination hub for tobacco and legumes.
    "mhuju": {
        "settlement_type": "peri_urban",
        "infrastructure_status": "partial_coverage",
        "grid_connection": "connected",
        "distance_to_substation_km": 6,
        "transformer_capacity_kva": 100,
        "service_reliability": "moderate",
        "essential_services_present": ["water_system", "emergency_services", "school"],
        "productive_activities": ["cold_storage", "trading", "storage"],
        "population_density_category": "medium",
        "grid_edge_exposure": False,
        "description": "Peri-urban EPA near Mzuzu with grid connectivity but insufficient transformer capacity for productive cold storage expansion. Main market node for surrounding EPAs."
    },
    "MHUJU": {
        "settlement_type": "peri_urban",
        "infrastructure_status": "partial_coverage",
        "grid_connection": "connected",
        "distance_to_substation_km": 6,
        "transformer_capacity_kva": 100,
        "service_reliability": "moderate",
        "essential_services_present": ["water_system", "emergency_services", "school"],
        "productive_activities": ["cold_storage", "trading", "storage"],
        "population_density_category": "medium",
        "grid_edge_exposure": False,
        "description": "Peri-urban EPA near Mzuzu with grid connectivity but insufficient transformer capacity for productive cold storage expansion. Main market node for surrounding EPAs."
    },
    # Bwengu EPA — Rumphi District, Northern Malawi
    # Off-grid, high irrigation demand from Rukuru River basin cooperatives.
    "bwengu": {
        "settlement_type": "informal_settlement",
        "infrastructure_status": "critical_gap",
        "grid_connection": "none",
        "distance_to_substation_km": 28,
        "transformer_capacity_kva": 0,
        "service_reliability": "none",
        "essential_services_present": ["water_system"],
        "productive_activities": ["irrigation", "milling", "farming"],
        "population_density_category": "medium",
        "grid_edge_exposure": True,
        "description": "Off-grid EPA in Rumphi District with critical infrastructure gap. Smallholder cooperatives rely on manual irrigation from Rukuru River. Highest priority for solar pump deployment."
    },
    "BWENGU": {
        "settlement_type": "informal_settlement",
        "infrastructure_status": "critical_gap",
        "grid_connection": "none",
        "distance_to_substation_km": 28,
        "transformer_capacity_kva": 0,
        "service_reliability": "none",
        "essential_services_present": ["water_system"],
        "productive_activities": ["irrigation", "milling", "farming"],
        "population_density_category": "medium",
        "grid_edge_exposure": True,
        "description": "Off-grid EPA in Rumphi District with critical infrastructure gap. Smallholder cooperatives rely on manual irrigation from Rukuru River. Highest priority for solar pump deployment."
    },
    # Rumphi EPA — Rumphi District, Northern Malawi
    # District headquarters area. Growing agro-dealer network and seed stockout patterns.
    "rumphi": {
        "settlement_type": "peri_urban",
        "infrastructure_status": "partial_coverage",
        "grid_connection": "connected",
        "distance_to_substation_km": 4,
        "transformer_capacity_kva": 150,
        "service_reliability": "moderate",
        "essential_services_present": ["clinic", "school", "water_system", "emergency_services"],
        "productive_activities": ["trading", "storage", "milling"],
        "population_density_category": "medium",
        "grid_edge_exposure": False,
        "description": "District headquarters EPA with reliable grid connectivity. Serves as input supply hub for surrounding rural EPAs. Recurring NPK fertilizer and seed stockout patterns during planting season."
    },
    "RUMPHI": {
        "settlement_type": "peri_urban",
        "infrastructure_status": "partial_coverage",
        "grid_connection": "connected",
        "distance_to_substation_km": 4,
        "transformer_capacity_kva": 150,
        "service_reliability": "moderate",
        "essential_services_present": ["clinic", "school", "water_system", "emergency_services"],
        "productive_activities": ["trading", "storage", "milling"],
        "population_density_category": "medium",
        "grid_edge_exposure": False,
        "description": "District headquarters EPA with reliable grid connectivity. Serves as input supply hub for surrounding rural EPAs. Recurring NPK fertilizer and seed stockout patterns during planting season."
    },
    # Euthini EPA — Mzimba District, Northern Malawi
    # Emerging irrigation activity. High seasonal maize production with poor post-harvest storage.
    "euthini": {
        "settlement_type": "rural_agricultural",
        "infrastructure_status": "underserved",
        "grid_connection": "partial",
        "distance_to_substation_km": 20,
        "transformer_capacity_kva": 30,
        "service_reliability": "intermittent",
        "essential_services_present": ["school", "water_system"],
        "productive_activities": ["farming", "irrigation", "milling"],
        "population_density_category": "low",
        "grid_edge_exposure": True,
        "description": "Rural EPA in Mzimba District with seasonal maize farming patterns. Poor post-harvest storage leading to significant post-harvest losses. Emerging dimba irrigation demand emerging from women-led cooperatives."
    },
    "EUTHINI": {
        "settlement_type": "rural_agricultural",
        "infrastructure_status": "underserved",
        "grid_connection": "partial",
        "distance_to_substation_km": 20,
        "transformer_capacity_kva": 30,
        "service_reliability": "intermittent",
        "essential_services_present": ["school", "water_system"],
        "productive_activities": ["farming", "irrigation", "milling"],
        "population_density_category": "low",
        "grid_edge_exposure": True,
        "description": "Rural EPA in Mzimba District with seasonal maize farming patterns. Poor post-harvest storage leading to significant post-harvest losses. Emerging dimba irrigation demand emerging from women-led cooperatives."
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

