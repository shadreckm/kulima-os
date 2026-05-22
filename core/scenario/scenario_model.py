"""
KULIMA OS Pilot - Scenario Model
=================================

Scenario Model for infrastructure simulation.

INVARIANT ENFORCEMENT:
- Zero-PII: Operates only on aggregated patterns (never raw signals)
- Coordination > Identity: Simulations based on collective patterns, not individual needs
- Semantic Guard: Designed for infrastructure planning, not surveillance or profiling

The Scenario Model simulates the impact of infrastructure additions on coordination patterns
and economic activity.
"""

from typing import List, Dict, Optional
from collections import defaultdict


class ScenarioModel:
    """
    Scenario Model for infrastructure simulation.
    
    Simulates "what happens if infrastructure is added" to a zone.
    """
    
    # Infrastructure impact factors (estimated impact on coordination strength)
    INFRASTRUCTURE_IMPACT_FACTORS = {
        'three_phase_power': {
            'coordination_boost': 0.15,  # 15% increase in coordination strength
            'persistence_boost': 0.10,   # 10% increase in persistence
            'new_activities': ['cold storage', 'welding'],  # Activities that become possible
            'description': 'Three-phase power enables heavy equipment and continuous operations'
        },
        'single_phase_power': {
            'coordination_boost': 0.08,  # 8% increase in coordination strength
            'persistence_boost': 0.05,   # 5% increase in persistence
            'new_activities': ['trading'],  # Activities that become possible
            'description': 'Single-phase power supports basic commercial activities'
        },
        'transformer_upgrade': {
            'coordination_boost': 0.12,  # 12% increase in coordination strength
            'persistence_boost': 0.08,   # 8% increase in persistence
            'new_activities': [],
            'description': 'Transformer upgrade improves reliability and capacity'
        }
    }
    
    def __init__(self):
        """Initialize Scenario Model."""
        pass
    
    def simulate_infrastructure_addition(
        self,
        patterns: List[Dict],
        flow_graph: Dict,
        confidence_results: List[Dict],
        infrastructure_type: str,
        zone: str
    ) -> Dict:
        """
        Simulate the impact of adding infrastructure to a zone.
        
        Args:
            patterns: Current coordination patterns
            flow_graph: Current flow graph
            confidence_results: Current confidence results
            infrastructure_type: Type of infrastructure to add
            zone: Zone to simulate infrastructure addition for
            
        Returns:
            Simulation results with projected changes in coordination metrics
        """
        
        if infrastructure_type not in self.INFRASTRUCTURE_IMPACT_FACTORS:
            return {
                'status': 'error',
                'message': f'Unknown infrastructure type: {infrastructure_type}'
            }
        
        # Get current zone score
        from core.decision.decision_engine import DecisionEngine
        decision_engine = DecisionEngine()
        
        zone_patterns = [p for p in patterns if p['zone'] == zone]
        current_zone_score = decision_engine._calculate_zone_score(zone_patterns, confidence_results, flow_graph)
        
        # Get impact factors
        impact_factors = self.INFRASTRUCTURE_IMPACT_FACTORS[infrastructure_type]
        
        # Calculate projected metrics
        projected_persistence = min(
            current_zone_score['persistence_score'] + impact_factors['persistence_boost'],
            1.0
        )
        projected_stability = current_zone_score['stability_score']  # Stability less affected by infrastructure
        projected_coordination_strength = min(
            current_zone_score['coordination_strength'] + impact_factors['coordination_boost'],
            1.0
        )
        
        # Calculate projected overall rating
        projected_overall = (0.4 * projected_persistence) + (0.3 * projected_stability) + (0.3 * projected_coordination_strength)
        
        # Determine projected rating category
        if projected_overall >= 0.7:
            projected_category = 'high'
        elif projected_overall >= 0.5:
            projected_category = 'moderate'
        else:
            projected_category = 'low'
        
        # Calculate changes
        persistence_change = projected_persistence - current_zone_score['persistence_score']
        coordination_change = projected_coordination_strength - current_zone_score['coordination_strength']
        overall_change = projected_overall - current_zone_score['overall_rating']
        
        # Identify potential new activities
        current_activities = set(p['activity_type'] for p in zone_patterns)
        potential_new_activities = [
            activity for activity in impact_factors['new_activities']
            if activity not in current_activities
        ]
        
        # Generate impact narrative
        impact_narrative = self._generate_impact_narrative(
            infrastructure_type,
            current_zone_score,
            projected_overall,
            persistence_change,
            coordination_change,
            potential_new_activities
        )
        
        return {
            'status': 'success',
            'zone': zone,
            'infrastructure_type': infrastructure_type,
            'infrastructure_description': impact_factors['description'],
            'current_metrics': current_zone_score,
            'projected_metrics': {
                'persistence_score': round(projected_persistence, 2),
                'stability_score': round(projected_stability, 2),
                'coordination_strength': round(projected_coordination_strength, 2),
                'overall_rating': round(projected_overall, 2),
                'rating_category': projected_category
            },
            'changes': {
                'persistence_change': round(persistence_change, 2),
                'coordination_strength_change': round(coordination_change, 2),
                'overall_rating_change': round(overall_change, 2)
            },
            'potential_new_activities': potential_new_activities,
            'impact_narrative': impact_narrative,
            'recommendation': self._generate_recommendation(projected_overall, current_zone_score['overall_rating'])
        }
    
    def simulate_capacity_upgrade(
        self,
        patterns: List[Dict],
        confidence_results: List[Dict],
        current_capacity_kw: float,
        new_capacity_kw: float,
        zone: str
    ) -> Dict:
        """
        Simulate the impact of upgrading capacity.
        
        Args:
            patterns: Current coordination patterns
            confidence_results: Current confidence results
            current_capacity_kw: Current capacity in kW
            new_capacity_kw: New capacity in kW
            zone: Zone to simulate capacity upgrade for
            
        Returns:
            Simulation results with projected changes
        """
        
        capacity_increase = new_capacity_kw - current_capacity_kw
        capacity_increase_ratio = capacity_increase / current_capacity_kw if current_capacity_kw > 0 else 0
        
        # Capacity increase improves coordination strength (more capacity = more activities possible)
        coordination_boost = min(capacity_increase_ratio * 0.20, 0.25)  # Max 25% boost
        
        # Get current zone score
        from core.decision.decision_engine import DecisionEngine
        decision_engine = DecisionEngine()
        
        zone_patterns = [p for p in patterns if p['zone'] == zone]
        flow_graph = {'nodes': [], 'edges': []}  # Simplified for capacity simulation
        current_zone_score = decision_engine._calculate_zone_score(zone_patterns, confidence_results, flow_graph)
        
        # Calculate projected metrics
        projected_coordination_strength = min(
            current_zone_score['coordination_strength'] + coordination_boost,
            1.0
        )
        projected_overall = (0.4 * current_zone_score['persistence_score']) + \
                           (0.3 * current_zone_score['stability_score']) + \
                           (0.3 * projected_coordination_strength)
        
        # Determine projected rating category
        if projected_overall >= 0.7:
            projected_category = 'high'
        elif projected_overall >= 0.5:
            projected_category = 'moderate'
        else:
            projected_category = 'low'
        
        # Calculate changes
        coordination_change = projected_coordination_strength - current_zone_score['coordination_strength']
        overall_change = projected_overall - current_zone_score['overall_rating']
        
        # Generate impact narrative
        impact_narrative = (
            f"Upgrading capacity from {current_capacity_kw} kW to {new_capacity_kw} kW "
            f"(increase of {capacity_increase} kW, {capacity_increase_ratio:.0%}) "
            f"is projected to increase coordination strength by {coordination_change:.2f}. "
            f"This could enable additional productive activities and improve overall coordination "
            f"from {current_zone_score['overall_rating']:.2f} to {projected_overall:.2f}."
        )
        
        return {
            'status': 'success',
            'zone': zone,
            'current_capacity_kw': current_capacity_kw,
            'new_capacity_kw': new_capacity_kw,
            'capacity_increase_kw': capacity_increase,
            'capacity_increase_ratio': round(capacity_increase_ratio, 2),
            'current_metrics': current_zone_score,
            'projected_metrics': {
                'coordination_strength': round(projected_coordination_strength, 2),
                'overall_rating': round(projected_overall, 2),
                'rating_category': projected_category
            },
            'changes': {
                'coordination_strength_change': round(coordination_change, 2),
                'overall_rating_change': round(overall_change, 2)
            },
            'impact_narrative': impact_narrative,
            'recommendation': self._generate_recommendation(projected_overall, current_zone_score['overall_rating'])
        }
    
    def _generate_impact_narrative(
        self,
        infrastructure_type: str,
        current_score: Dict,
        projected_overall: float,
        persistence_change: float,
        coordination_change: float,
        potential_new_activities: List[str]
    ) -> str:
        """
        Generate narrative description of infrastructure impact.
        
        Args:
            infrastructure_type: Type of infrastructure being added
            current_score: Current zone score
            projected_overall: Projected overall rating
            persistence_change: Change in persistence
            coordination_change: Change in coordination strength
            potential_new_activities: Activities that could emerge
            
        Returns:
            Impact narrative text
        """
        
        narrative_parts = [
            f"Adding {infrastructure_type} infrastructure is projected to "
        ]
        
        if persistence_change > 0.05:
            narrative_parts.append(
                f"increase persistence by {persistence_change:.2f} "
            )
        
        if coordination_change > 0.05:
            narrative_parts.append(
                f"and improve coordination strength by {coordination_change:.2f}. "
            )
        
        narrative_parts.append(
            f"The overall rating is expected to improve from {current_score['overall_rating']:.2f} "
            f"to {projected_overall:.2f}. "
        )
        
        if potential_new_activities:
            narrative_parts.append(
                f"This infrastructure could enable new activities: {', '.join(potential_new_activities)}. "
            )
        
        return ''.join(narrative_parts)
    
    def _generate_recommendation(self, projected_overall: float, current_overall: float) -> str:
        """
        Generate recommendation based on projected improvement.
        
        Args:
            projected_overall: Projected overall rating
            current_overall: Current overall rating
            
        Returns:
            Recommendation text
        """
        
        improvement = projected_overall - current_overall
        
        if improvement >= 0.15:
            return "Strongly recommended: Significant improvement in coordination expected."
        elif improvement >= 0.08:
            return "Recommended: Moderate improvement in coordination expected."
        elif improvement >= 0.03:
            return "Consider: Slight improvement in coordination expected."
        else:
            return "Low priority: Minimal improvement in coordination expected."
    
    def regional_simulation(self, patterns: List[Dict], confidence_results: List[Dict], infrastructure_additions: List[Dict]) -> Dict:
        """
        Simulate infrastructure impact across multiple zones.
        
        This method extends the Scenario Model to support regional infrastructure
        planning by simulating the impact of infrastructure additions across zones.
        
        Args:
            patterns: Current coordination patterns
            confidence_results: Current confidence results
            infrastructure_additions: List of infrastructure additions by zone
            
        Returns:
            Regional simulation results with zone-by-zone impact analysis
        """
        regional_impact = {}
        
        # Group patterns by zone
        patterns_by_zone = {}
        for pattern in patterns:
            zone = pattern['zone']
            if zone not in patterns_by_zone:
                patterns_by_zone[zone] = []
            patterns_by_zone[zone].append(pattern)
        
        # Simulate impact for each zone with infrastructure addition
        for addition in infrastructure_additions:
            zone = addition.get('zone')
            infrastructure_type = addition.get('infrastructure_type', 'three_phase_power')
            
            if zone not in patterns_by_zone:
                continue
            
            zone_patterns = patterns_by_zone[zone]
            flow_graph = {'nodes': [], 'edges': []}  # Simplified for regional simulation
            
            simulation = self.simulate_infrastructure_addition(
                zone_patterns, flow_graph, confidence_results, infrastructure_type, zone
            )
            
            regional_impact[zone] = simulation
        
        # Calculate regional aggregate metrics
        total_capacity_increase = sum(
            addition.get('capacity_kw', 0) for addition in infrastructure_additions
        )
        
        avg_coordination_boost = 0
        if regional_impact:
            coordination_boosts = [
                impact['projected_metrics']['coordination_strength'] - impact['current_metrics']['coordination_strength']
                for impact in regional_impact.values()
            ]
            avg_coordination_boost = statistics.mean(coordination_boosts) if coordination_boosts else 0
        
        return {
            'zone_impacts': regional_impact,
            'regional_aggregates': {
                'total_zones_affected': len(regional_impact),
                'total_capacity_increase_kw': total_capacity_increase,
                'average_coordination_boost': round(avg_coordination_boost, 2)
            },
            'infrastructure_additions': infrastructure_additions
        }


def print_scenario_results(results: Dict) -> None:
    """Print scenario simulation results in a readable format."""
    print("\n" + "=" * 60)
    print("SCENARIO MODEL OUTPUT - INFRASTRUCTURE SIMULATION")
    print("=" * 60)
    
    if results.get('status') == 'error':
        print(f"\nError: {results.get('message', 'Unknown error')}")
        return
    
    print(f"\nZone: {results['zone']}")
    print(f"Infrastructure: {results['infrastructure_type']}")
    print(f"Description: {results.get('infrastructure_description', 'N/A')}")
    
    print("\nCurrent Metrics:")
    current = results['current_metrics']
    print(f"  Persistence: {current['persistence_score']}")
    print(f"  Stability: {current['stability_score']}")
    print(f"  Coordination Strength: {current['coordination_strength']}")
    print(f"  Overall Rating: {current['overall_rating']} ({current['rating_category']})")
    
    print("\nProjected Metrics:")
    projected = results['projected_metrics']
    print(f"  Persistence: {projected['persistence_score']}")
    print(f"  Stability: {projected['stability_score']}")
    print(f"  Coordination Strength: {projected['coordination_strength']}")
    print(f"  Overall Rating: {projected['overall_rating']} ({projected['rating_category']})")
    
    print("\nChanges:")
    changes = results['changes']
    print(f"  Persistence Change: {changes['persistence_change']:+.2f}")
    print(f"  Coordination Strength Change: {changes['coordination_strength_change']:+.2f}")
    print(f"  Overall Rating Change: {changes['overall_rating_change']:+.2f}")
    
    if results.get('potential_new_activities'):
        print(f"\nPotential New Activities: {', '.join(results['potential_new_activities'])}")
    
    print(f"\nImpact Narrative: {results['impact_narrative']}")
    print(f"Recommendation: {results['recommendation']}")
    
    print("\n" + "=" * 60)
    print("INVARIANT COMPLIANCE:")
    print("✓ Zero-PII: Simulations based on aggregated patterns only")
    print("✓ Coordination > Identity: Infrastructure for collective benefit")
    print("✓ Semantic Guard: Designed for planning, not surveillance")
    print("=" * 60)


if __name__ == "__main__":
    # Test with sample data
    print("Testing Scenario Model...")
    
    scenario_model = ScenarioModel()
    
    # Sample patterns
    patterns = [
        {'activity_type': 'irrigation', 'zone': 'MZUZU', 'pattern_frequency': 5},
        {'activity_type': 'milling', 'zone': 'MZUZU', 'pattern_frequency': 4},
    ]
    
    # Sample flow graph
    flow_graph = {
        'nodes': [
            {'id': 'node_0', 'activity_type': 'irrigation', 'zone': 'MZUZU'},
            {'id': 'node_1', 'activity_type': 'milling', 'zone': 'MZUZU'},
        ],
        'edges': [
            {'from_activity': 'irrigation', 'to_activity': 'milling', 'zone': 'MZUZU', 'strength_score': 0.8}
        ]
    }
    
    # Sample confidence results
    confidence_results = [
        {'activity_type': 'irrigation', 'zone': 'MZUZU', 'persistence': 0.6, 'stability_score': 0.6, 'confidence_score': 60},
        {'activity_type': 'milling', 'zone': 'MZUZU', 'persistence': 0.5, 'stability_score': 0.5, 'confidence_score': 55},
    ]
    
    # Simulate infrastructure addition
    results = scenario_model.simulate_infrastructure_addition(
        patterns, flow_graph, confidence_results, 'three_phase_power', 'MZUZU'
    )
    print_scenario_results(results)
