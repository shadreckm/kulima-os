"""
KULIMA OS Pilot - LUNDAI Settlement & Infrastructure Gap Engine
================================================================

LUNDAI (Pilot Scope) performs deterministic settlement context and infrastructure
gap analysis using zone-level metadata, without external GIS or satellite data.

INVARIANT ENFORCEMENT:
- Zero-PII: Operates only on zone-level aggregates (no individual locations)
- Coordination > Identity: Reasons over settlement patterns, not people
- Deterministic: No external APIs, real-time data, or personal identifiers
- Semantic Guard: No surveillance, tracking, or individual profiling

LUNDAI combines with LUMOZA's temporal coordination intelligence to strengthen
Critical Load Protection by providing settlement and infrastructure context.
"""

from typing import List, Dict
from zone_metadata import get_zone_metadata, get_all_zones


class LundaiEngine:
    """
    LUNDAI - Settlement and Infrastructure Mismatch Engine (Pilot Scope)
    
    Analyzes settlement context and infrastructure gaps using zone-level metadata
    to inform capacity planning and Critical Load Protection enforcement.
    """
    
    # Infrastructure gap severity thresholds
    CRITICAL_GAP_INDICATORS = {
        "no_grid": True,
        "distance_threshold_km": 20,
        "capacity_threshold_kva": 25,
        "essential_services_at_risk": True
    }
    
    def __init__(self):
        """Initialize LUNDAI engine."""
        pass
    
    def analyze_settlement_context(self, coordination_patterns: List[Dict]) -> Dict:
        """
        Analyze settlement context and infrastructure gaps for zones with
        coordinated demand patterns.
        
        ZERO-PII ENFORCEMENT:
        - Analyzes zone-level metadata only
        - No individual locations or identifiers
        
        COORDINATION > IDENTITY:
        - Combines coordination patterns (from LUMOZA) with settlement context
        - Identifies infrastructure mismatches at zone level
        
        Args:
            coordination_patterns: List of coordination patterns from LUMOZA
            
        Returns:
            Settlement and infrastructure gap analysis
        """
        
        # Extract zones with coordination patterns
        zones_with_demand = set(p['zone'] for p in coordination_patterns)
        
        # Analyze each zone
        zone_analyses = {}
        for zone in zones_with_demand:
            zone_metadata = get_zone_metadata(zone)
            zone_patterns = [p for p in coordination_patterns if p['zone'] == zone]
            
            zone_analyses[zone] = self._analyze_zone(zone, zone_metadata, zone_patterns)
        
        # Generate overall assessment
        overall_assessment = self._generate_overall_assessment(zone_analyses)
        
        return {
            "zone_analyses": zone_analyses,
            "overall_assessment": overall_assessment
        }
    
    def _analyze_zone(self, zone: str, metadata: Dict, patterns: List[Dict]) -> Dict:
        """
        Analyze a single zone's settlement context and infrastructure gap.
        
        Args:
            zone: Zone identifier
            metadata: Zone metadata
            patterns: Coordination patterns in this zone
            
        Returns:
            Zone analysis
        """
        
        # Classify settlement type
        settlement_type = metadata.get('settlement_type', 'unknown')
        
        # Assess infrastructure gap severity
        gap_severity = self._assess_infrastructure_gap(metadata)
        
        # Identify essential services in this zone
        essential_patterns = [p for p in patterns if p.get('service_priority') == 'essential']
        productive_patterns = [p for p in patterns if p.get('service_priority') == 'productive']
        
        # Determine grid edge exposure
        grid_edge_exposure = metadata.get('grid_edge_exposure', False)
        
        # Calculate infrastructure adequacy score (0-100)
        adequacy_score = self._calculate_infrastructure_adequacy(metadata, patterns)
        
        # Generate infrastructure gap justification
        gap_justification = self._generate_gap_justification(
            metadata, essential_patterns, productive_patterns, gap_severity
        )
        
        return {
            "settlement_type": settlement_type,
            "infrastructure_status": metadata.get('infrastructure_status', 'unknown'),
            "gap_severity": gap_severity,
            "grid_connection": metadata.get('grid_connection', 'unknown'),
            "grid_edge_exposure": grid_edge_exposure,
            "distance_to_substation_km": metadata.get('distance_to_substation_km'),
            "transformer_capacity_kva": metadata.get('transformer_capacity_kva'),
            "service_reliability": metadata.get('service_reliability', 'unknown'),
            "essential_services_count": len(essential_patterns),
            "productive_activities_count": len(productive_patterns),
            "infrastructure_adequacy_score": adequacy_score,
            "gap_justification": gap_justification,
            "priority_classification": self._classify_priority(gap_severity, essential_patterns)
        }
    
    def _assess_infrastructure_gap(self, metadata: Dict) -> str:
        """
        Assess infrastructure gap severity based on metadata.
        
        Returns:
            'critical', 'severe', 'moderate', or 'minimal'
        """
        
        # Critical gap indicators
        if metadata.get('grid_connection') == 'none':
            return 'critical'
        
        if metadata.get('distance_to_substation_km', 0) > self.CRITICAL_GAP_INDICATORS['distance_threshold_km']:
            return 'critical'
        
        if metadata.get('transformer_capacity_kva', 0) < self.CRITICAL_GAP_INDICATORS['capacity_threshold_kva']:
            return 'severe'
        
        if metadata.get('service_reliability') in ['none', 'intermittent']:
            return 'severe'
        
        if metadata.get('infrastructure_status') == 'underserved':
            return 'moderate'
        
        return 'minimal'
    
    def _calculate_infrastructure_adequacy(self, metadata: Dict, patterns: List[Dict]) -> int:
        """
        Calculate infrastructure adequacy score (0-100).
        
        Higher score = better infrastructure adequacy
        """
        
        score = 100
        
        # Penalize for no grid connection
        if metadata.get('grid_connection') == 'none':
            score -= 50
        elif metadata.get('grid_connection') == 'partial':
            score -= 25
        
        # Penalize for distance to substation
        distance = metadata.get('distance_to_substation_km', 0)
        if distance > 20:
            score -= 30
        elif distance > 10:
            score -= 15
        
        # Penalize for low capacity
        capacity = metadata.get('transformer_capacity_kva', 0)
        if capacity == 0:
            score -= 20
        elif capacity < 50:
            score -= 10
        
        # Penalize for poor reliability
        reliability = metadata.get('service_reliability', 'unknown')
        if reliability == 'none':
            score -= 20
        elif reliability == 'intermittent':
            score -= 15
        elif reliability == 'moderate':
            score -= 5
        
        return max(0, score)
    
    def _generate_gap_justification(
        self, metadata: Dict, essential_patterns: List[Dict],
        productive_patterns: List[Dict], gap_severity: str
    ) -> str:
        """Generate human-readable infrastructure gap justification."""
        
        justifications = []
        
        if metadata.get('grid_connection') == 'none':
            justifications.append("No grid connection")
        elif metadata.get('grid_connection') == 'partial':
            justifications.append("Partial grid access with frequent outages")
        
        if metadata.get('distance_to_substation_km', 0) > 15:
            justifications.append(f"Remote location ({metadata['distance_to_substation_km']}km from substation)")
        
        if len(essential_patterns) > 0:
            services = [p['activity_type'] for p in essential_patterns]
            justifications.append(f"Essential services present ({', '.join(services)}) require reliable power")
        
        if metadata.get('grid_edge_exposure'):
            justifications.append("Grid-edge exposure increases vulnerability")
        
        if len(productive_patterns) > 0:
            justifications.append(f"{len(productive_patterns)} productive activities require capacity expansion")
        
        return "; ".join(justifications) if justifications else "Infrastructure adequate for current demand"
    
    def _classify_priority(self, gap_severity: str, essential_patterns: List[Dict]) -> str:
        """
        Classify infrastructure priority based on gap severity and essential services.
        
        Returns:
            'urgent', 'high', 'medium', or 'low'
        """
        
        if gap_severity == 'critical' and len(essential_patterns) > 0:
            return 'urgent'
        elif gap_severity == 'critical':
            return 'high'
        elif gap_severity == 'severe' and len(essential_patterns) > 0:
            return 'high'
        elif gap_severity == 'severe':
            return 'medium'
        elif len(essential_patterns) > 0:
            return 'medium'
        else:
            return 'low'
    
    def _generate_overall_assessment(self, zone_analyses: Dict) -> Dict:
        """Generate overall assessment across all zones."""
        
        total_zones = len(zone_analyses)
        critical_gaps = sum(1 for z in zone_analyses.values() if z['gap_severity'] == 'critical')
        severe_gaps = sum(1 for z in zone_analyses.values() if z['gap_severity'] == 'severe')
        urgent_priority = sum(1 for z in zone_analyses.values() if z['priority_classification'] == 'urgent')
        
        total_essential_services = sum(z['essential_services_count'] for z in zone_analyses.values())
        zones_with_grid_edge_exposure = sum(1 for z in zone_analyses.values() if z['grid_edge_exposure'])
        
        avg_adequacy_score = sum(z['infrastructure_adequacy_score'] for z in zone_analyses.values()) / total_zones if total_zones > 0 else 0
        
        return {
            "total_zones_analyzed": total_zones,
            "critical_infrastructure_gaps": critical_gaps,
            "severe_infrastructure_gaps": severe_gaps,
            "urgent_priority_zones": urgent_priority,
            "total_essential_services_detected": total_essential_services,
            "zones_with_grid_edge_exposure": zones_with_grid_edge_exposure,
            "average_infrastructure_adequacy_score": round(avg_adequacy_score, 1),
            "overall_infrastructure_status": self._classify_overall_status(avg_adequacy_score, critical_gaps, urgent_priority)
        }
    
    def _classify_overall_status(self, avg_score: float, critical_gaps: int, urgent_priority: int) -> str:
        """Classify overall infrastructure status."""
        
        if critical_gaps > 0 or urgent_priority > 0:
            return "Critical infrastructure gaps require urgent intervention"
        elif avg_score < 50:
            return "Severe infrastructure deficits across multiple zones"
        elif avg_score < 70:
            return "Moderate infrastructure gaps, capacity expansion needed"
        else:
            return "Infrastructure generally adequate, targeted improvements recommended"


if __name__ == "__main__":
    # Test LUNDAI with mock coordination patterns
    from pilot_signals import generate_pilot_signals
    from lumoza_engine import LumozaEngine
    
    print("Testing LUNDAI Engine...")
    print("=" * 70)
    
    # Generate signals and process through LUMOZA
    signals = generate_pilot_signals()
    lumoza = LumozaEngine()
    patterns = lumoza.process_signals(signals)
    
    # Analyze with LUNDAI
    lundai = LundaiEngine()
    analysis = lundai.analyze_settlement_context(patterns)
    
    print("\nLUNDAI SETTLEMENT & INFRASTRUCTURE GAP ANALYSIS")
    print("=" * 70)
    
    for zone, zone_analysis in analysis['zone_analyses'].items():
        print(f"\n{zone.upper()}:")
        print(f"  Settlement Type: {zone_analysis['settlement_type']}")
        print(f"  Infrastructure Status: {zone_analysis['infrastructure_status']}")
        print(f"  Gap Severity: {zone_analysis['gap_severity']}")
        print(f"  Priority: {zone_analysis['priority_classification']}")
        print(f"  Adequacy Score: {zone_analysis['infrastructure_adequacy_score']}/100")
        print(f"  Essential Services: {zone_analysis['essential_services_count']}")
        print(f"  Justification: {zone_analysis['gap_justification']}")
    
    print("\n" + "=" * 70)
    print("OVERALL ASSESSMENT:")
    overall = analysis['overall_assessment']
    print(f"  Zones Analyzed: {overall['total_zones_analyzed']}")
    print(f"  Critical Gaps: {overall['critical_infrastructure_gaps']}")
    print(f"  Urgent Priority: {overall['urgent_priority_zones']}")
    print(f"  Average Adequacy: {overall['average_infrastructure_adequacy_score']}/100")
    print(f"  Status: {overall['overall_infrastructure_status']}")
    print("=" * 70)

# Made with Bob
