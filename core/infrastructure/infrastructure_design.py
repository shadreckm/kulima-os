"""
KULIMA OS Pilot - Infrastructure Design Layer
============================================

Infrastructure Design Layer for phased rollout planning and capacity estimation.

INVARIANT ENFORCEMENT:
- Zero-PII: Operates only on aggregated patterns (never raw signals)
- Coordination > Identity: Plans based on collective patterns, not individual needs
- Semantic Guard: Designed for infrastructure planning, not surveillance or profiling

The Infrastructure Design Layer uses priority rankings and capacity models to design
phased rollout plans for infrastructure deployment.
"""

from typing import List, Dict, Optional
from collections import defaultdict


class InfrastructureDesignLayer:
    """
    Infrastructure Design Layer for phased rollout planning.
    
    Uses priority rankings and capacity models to design infrastructure deployment plans.
    """
    
    # Activity to infrastructure type mapping
    ACTIVITY_INFRASTRUCTURE_MAP = {
        'irrigation': {
            'type': 'pumping_systems_3phase',
            'base_capacity_kw': 20,
            'description': 'Water pumping systems requiring three-phase power'
        },
        'milling': {
            'type': 'processing_energy_3phase',
            'base_capacity_kw': 15,
            'description': 'Processing energy for milling operations'
        },
        'cold storage': {
            'type': 'refrigeration_load',
            'base_capacity_kw': 10,
            'description': 'Refrigeration load for cold storage'
        },
        'welding': {
            'type': 'industrial_load',
            'base_capacity_kw': 5,
            'description': 'Industrial load for welding operations'
        },
        'trading': {
            'type': 'commercial_load',
            'base_capacity_kw': 2,
            'description': 'Commercial load for trading activities'
        }
    }
    
    def __init__(self):
        """Initialize Infrastructure Design Layer."""
        pass
    
    def rank_zones_by_priority(self, zone_scores: Dict[str, Dict]) -> List[Dict]:
        """
        Rank zones by priority based on persistence, stability, and coordination strength.
        
        Args:
            zone_scores: Dictionary mapping zones to their scorecard metrics
            
        Returns:
            List of zones ranked by priority (highest first)
        """
        ranked_zones = []
        
        for zone, scores in zone_scores.items():
            # Calculate composite priority score
            persistence = scores.get('persistence_score', 0)
            stability = scores.get('stability_score', 0)
            coordination_strength = scores.get('coordination_strength', 0)
            
            # Weighted priority score
            priority_score = (0.4 * persistence) + (0.3 * stability) + (0.3 * coordination_strength)
            
            ranked_zones.append({
                'zone': zone,
                'priority_score': round(priority_score, 2),
                'persistence': persistence,
                'stability': stability,
                'coordination_strength': coordination_strength,
                'overall_rating': scores.get('overall_rating', 0)
            })
        
        # Sort by priority score (descending)
        ranked_zones.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return ranked_zones
    
    def determine_infrastructure_type(self, activity_type: str) -> Dict:
        """
        Determine infrastructure type based on activity.
        
        Args:
            activity_type: Activity type (irrigation, milling, etc.)
            
        Returns:
            Infrastructure type mapping
        """
        return self.ACTIVITY_INFRASTRUCTURE_MAP.get(activity_type, {
            'type': 'general_load',
            'base_capacity_kw': 5,
            'description': 'General electrical load'
        })
    
    def design_phased_rollout(self, ranked_zones: List[Dict], infrastructure_needs: List[Dict]) -> Dict:
        """
        Design phased rollout plan based on priority zones and infrastructure needs.
        
        Args:
            ranked_zones: Zones ranked by priority
            infrastructure_needs: Infrastructure recommendations for each zone
            
        Returns:
            Phased rollout plan with 3 phases
        """
        # Phase 1: Highest persistence + highest confidence zones
        phase_1_zones = []
        phase_2_zones = []
        phase_3_zones = []
        
        # Distribute zones across phases based on priority
        total_zones = len(ranked_zones)
        
        for i, zone_data in enumerate(ranked_zones):
            zone = zone_data['zone']
            priority_score = zone_data['priority_score']
            
            # Find infrastructure needs for this zone
            zone_infra = [infra for infra in infrastructure_needs if infra.get('zone') == zone]
            
            if priority_score >= 0.7:
                phase_1_zones.append({
                    'zone': zone,
                    'priority_score': priority_score,
                    'infrastructure': zone_infra,
                    'capacity_kw': sum(infra.get('recommended_capacity_kw', 0) for infra in zone_infra)
                })
            elif priority_score >= 0.5:
                phase_2_zones.append({
                    'zone': zone,
                    'priority_score': priority_score,
                    'infrastructure': zone_infra,
                    'capacity_kw': sum(infra.get('recommended_capacity_kw', 0) for infra in zone_infra)
                })
            else:
                phase_3_zones.append({
                    'zone': zone,
                    'priority_score': priority_score,
                    'infrastructure': zone_infra,
                    'capacity_kw': sum(infra.get('recommended_capacity_kw', 0) for infra in zone_infra)
                })
        
        # Calculate phase timelines
        phase_1_timeline = self._calculate_phase_timeline(phase_1_zones, 1)
        phase_2_timeline = self._calculate_phase_timeline(phase_2_zones, 2)
        phase_3_timeline = self._calculate_phase_timeline(phase_3_zones, 3)
        
        return {
            'phase_1': {
                'zones': phase_1_zones,
                'total_capacity_kw': round(sum(z['capacity_kw'] for z in phase_1_zones), 1),
                'timeline_months': phase_1_timeline,
                'description': 'Highest persistence + highest confidence zones'
            },
            'phase_2': {
                'zones': phase_2_zones,
                'total_capacity_kw': round(sum(z['capacity_kw'] for z in phase_2_zones), 1),
                'timeline_months': phase_2_timeline,
                'description': 'Adjacent or growing coordination zones'
            },
            'phase_3': {
                'zones': phase_3_zones,
                'total_capacity_kw': round(sum(z['capacity_kw'] for z in phase_3_zones), 1),
                'timeline_months': phase_3_timeline,
                'description': 'Full value chain integration (flow-connected activities)'
            },
            'total_capacity_kw': round(
                sum(z['capacity_kw'] for z in phase_1_zones + phase_2_zones + phase_3_zones), 1
            ),
            'total_timeline_months': phase_1_timeline + phase_2_timeline + phase_3_timeline
        }
    
    def calculate_capacity_with_growth(self, base_capacity: float, persistence_trend: str) -> float:
        """
        Calculate capacity with growth factor based on persistence trend.
        
        Args:
            base_capacity: Base capacity in kW
            persistence_trend: Trend (increasing, stable, declining)
            
        Returns:
            Capacity with growth factor applied
        """
        growth_factor = 1.0
        
        if persistence_trend == 'increasing':
            growth_factor = 1.3  # 30% growth buffer
        elif persistence_trend == 'stable':
            growth_factor = 1.15  # 15% growth buffer
        elif persistence_trend == 'declining':
            growth_factor = 1.0  # No growth buffer
        
        return round(base_capacity * growth_factor, 1)
    
    def estimate_load_distribution(self, zones: List[str], infrastructure_types: List[str]) -> Dict:
        """
        Estimate load distribution across zones.
        
        Args:
            zones: List of zones
            infrastructure_types: List of infrastructure types
            
        Returns:
            Load distribution by zone
        """
        load_distribution = {}
        
        for zone in zones:
            # Calculate base load based on infrastructure types
            base_load = 0
            for infra_type in infrastructure_types:
                # Find base capacity for this infrastructure type
                for activity, infra_map in self.ACTIVITY_INFRASTRUCTURE_MAP.items():
                    if infra_map['type'] == infra_type:
                        base_load += infra_map['base_capacity_kw']
            
            # Add some variation based on zone (simplified)
            zone_factor = 1.0
            if zone == 'MZUZU':
                zone_factor = 1.2
            elif zone == 'LILONGWE':
                zone_factor = 1.1
            elif zone == 'BLANTYRE':
                zone_factor = 1.0
            elif zone == 'ZOMBA':
                zone_factor = 0.9
            
            load_distribution[zone] = round(base_load * zone_factor, 1)
        
        return load_distribution
    
    def _calculate_phase_timeline(self, phase_zones: List[Dict], phase_number: int) -> int:
        """
        Calculate timeline for a phase based on number of zones.
        
        Args:
            phase_zones: Zones in this phase
            phase_number: Phase number (1, 2, or 3)
            
        Returns:
            Timeline in months
        """
        if not phase_zones:
            return 0
        
        # Base timeline: 6 months for Phase 1, 4 months for Phase 2, 6 months for Phase 3
        base_timeline = {1: 6, 2: 4, 3: 6}
        
        # Add 2 months per additional zone beyond the first
        additional_months = (len(phase_zones) - 1) * 2
        
        return base_timeline.get(phase_number, 6) + additional_months


def print_infrastructure_design_results(ranked_zones: List[Dict], phased_rollout: Dict, load_distribution: Dict) -> None:
    """Log infrastructure design results in a readable format."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("\n" + "=" * 60)
    logger.info("INFRASTRUCTURE DESIGN LAYER OUTPUT")
    logger.info("=" * 60)

    logger.info("\nRanked Zones by Priority:")
    for i, zone_data in enumerate(ranked_zones, 1):
        logger.info("  %s. %s:", i, zone_data['zone'])
        logger.info("     Priority Score: %s", zone_data['priority_score'])
        logger.info("     Persistence: %s", zone_data['persistence'])
        logger.info("     Stability: %s", zone_data['stability'])
        logger.info("     Coordination Strength: %s", zone_data['coordination_strength'])

    logger.info("\nPhased Rollout Plan:")
    logger.info("\nPhase 1: %s", phased_rollout['phase_1']['description'])
    logger.info("  Timeline: %s months", phased_rollout['phase_1']['timeline_months'])
    logger.info("  Total Capacity: %s kW", phased_rollout['phase_1']['total_capacity_kw'])
    for zone_data in phased_rollout['phase_1']['zones']:
        logger.info("    - %s: %s kW", zone_data['zone'], zone_data['capacity_kw'])

    logger.info("\nPhase 2: %s", phased_rollout['phase_2']['description'])
    logger.info("  Timeline: %s months", phased_rollout['phase_2']['timeline_months'])
    logger.info("  Total Capacity: %s kW", phased_rollout['phase_2']['total_capacity_kw'])
    for zone_data in phased_rollout['phase_2']['zones']:
        logger.info("    - %s: %s kW", zone_data['zone'], zone_data['capacity_kw'])

    logger.info("\nPhase 3: %s", phased_rollout['phase_3']['description'])
    logger.info("  Timeline: %s months", phased_rollout['phase_3']['timeline_months'])
    logger.info("  Total Capacity: %s kW", phased_rollout['phase_3']['total_capacity_kw'])
    for zone_data in phased_rollout['phase_3']['zones']:
        logger.info("    - %s: %s kW", zone_data['zone'], zone_data['capacity_kw'])

    logger.info("\nTotal Capacity: %s kW", phased_rollout['total_capacity_kw'])
    logger.info("Total Timeline: %s months", phased_rollout['total_timeline_months'])

    logger.info("\nLoad Distribution:")
    for zone, load in load_distribution.items():
        logger.info("  %s: %s kW", zone, load)

    logger.info("\n" + "=" * 60)
    logger.info("INVARIANT COMPLIANCE:")
    logger.info("✓ Zero-PII: Planning based on aggregated patterns only")
    logger.info("✓ Coordination > Identity: Infrastructure for collective benefit")
    logger.info("✓ Semantic Guard: Designed for planning, not surveillance")
    logger.info("=" * 60)


if __name__ == "__main__":
    # Test with sample data
    import logging
    logging.getLogger(__name__).info("Testing Infrastructure Design Layer...")
    
    design_layer = InfrastructureDesignLayer()
    
    # Sample zone scores
    zone_scores = {
        'MZUZU': {
            'persistence_score': 0.8,
            'stability_score': 0.75,
            'coordination_strength': 0.82,
            'overall_rating': 0.79
        },
        'LILONGWE': {
            'persistence_score': 0.65,
            'stability_score': 0.6,
            'coordination_strength': 0.7,
            'overall_rating': 0.65
        },
        'BLANTYRE': {
            'persistence_score': 0.5,
            'stability_score': 0.55,
            'coordination_strength': 0.6,
            'overall_rating': 0.55
        }
    }
    
    # Rank zones by priority
    ranked_zones = design_layer.rank_zones_by_priority(zone_scores)
    
    # Sample infrastructure needs
    infrastructure_needs = [
        {'zone': 'MZUZU', 'activity_type': 'irrigation', 'recommended_capacity_kw': 50},
        {'zone': 'MZUZU', 'activity_type': 'milling', 'recommended_capacity_kw': 40},
        {'zone': 'LILONGWE', 'activity_type': 'irrigation', 'recommended_capacity_kw': 30},
        {'zone': 'BLANTYRE', 'activity_type': 'irrigation', 'recommended_capacity_kw': 20}
    ]
    
    # Design phased rollout
    phased_rollout = design_layer.design_phased_rollout(ranked_zones, infrastructure_needs)
    
    # Estimate load distribution
    zones = ['MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA']
    infrastructure_types = ['pumping_systems_3phase', 'processing_energy_3phase']
    load_distribution = design_layer.estimate_load_distribution(zones, infrastructure_types)
    
    print_infrastructure_design_results(ranked_zones, phased_rollout, load_distribution)
