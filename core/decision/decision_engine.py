"""
KULIMA OS Pilot - Decision Engine
==================================

Decision Engine for infrastructure recommendations based on coordination patterns.

INVARIANT ENFORCEMENT:
- Zero-PII: Operates only on aggregated patterns (never raw signals)
- Coordination > Identity: Recommendations based on collective patterns, not individual needs
- Semantic Guard: Designed for infrastructure planning, not surveillance or profiling

The Decision Engine translates coordination intelligence into actionable infrastructure
recommendations for utilities and development finance institutions.
"""

from typing import List, Dict, Optional
from collections import defaultdict


class DecisionEngine:
    """
    Decision Engine for infrastructure recommendations.
    
    Translates coordination patterns, flow graphs, and confidence results
    into actionable infrastructure decisions.
    """
    
    # Infrastructure type mappings based on activity types
    ACTIVITY_INFRASTRUCTURE_MAP = {
        'irrigation': {
            'type': 'three_phase_power',
            'min_capacity_kw': 20,
            'recommended_capacity_kw': 50,
            'priority': 'high',
            'justification': 'Water pumps require reliable three-phase power for agricultural productivity'
        },
        'milling': {
            'type': 'three_phase_power',
            'min_capacity_kw': 15,
            'recommended_capacity_kw': 40,
            'priority': 'high',
            'justification': 'Maize mills require consistent power for community food processing'
        },
        'cold storage': {
            'type': 'three_phase_power',
            'min_capacity_kw': 10,
            'recommended_capacity_kw': 30,
            'priority': 'medium',
            'justification': 'Cold storage requires continuous power for perishable goods preservation'
        },
        'welding': {
            'type': 'single_phase_power',
            'min_capacity_kw': 5,
            'recommended_capacity_kw': 15,
            'priority': 'medium',
            'justification': 'Welding operations require stable power for metal fabrication'
        },
        'trading': {
            'type': 'single_phase_power',
            'min_capacity_kw': 2,
            'recommended_capacity_kw': 10,
            'priority': 'low',
            'justification': 'Trading activities require basic power for lighting and equipment'
        }
    }
    
    def __init__(self):
        """Initialize Decision Engine."""
        pass
    
    def recommend_infrastructure(
        self,
        patterns: List[Dict],
        flow_graph: Dict,
        confidence_results: List[Dict]
    ) -> Dict:
        """
        Generate infrastructure recommendations based on coordination intelligence.
        
        Args:
            patterns: Coordination patterns from LUMOZA
            flow_graph: Flow graph from LUNDAI
            confidence_results: Confidence results from ZENTARI
            
        Returns:
            Infrastructure recommendations with priority zone, capacity, and justification
        """
        
        # Aggregate patterns by zone
        zone_patterns = defaultdict(list)
        for pattern in patterns:
            zone_patterns[pattern['zone']].append(pattern)
        
        # Calculate zone scores
        zone_scores = {}
        for zone, zone_pattern_list in zone_patterns.items():
            zone_scores[zone] = self._calculate_zone_score(zone_pattern_list, confidence_results, flow_graph)
        
        # Identify priority zone (highest overall score)
        priority_zone = max(zone_scores.keys(), key=lambda z: zone_scores[z]['overall_rating']) if zone_scores else None
        
        if not priority_zone:
            return {
                'recommended_infrastructure': None,
                'priority_zone': None,
                'required_capacity': None,
                'justification': 'Insufficient coordination patterns to recommend infrastructure'
            }
        
        # Determine required infrastructure for priority zone
        priority_patterns = zone_patterns[priority_zone]
        infrastructure_recommendations = self._determine_infrastructure_needs(priority_patterns, confidence_results)
        
        # Calculate total required capacity
        total_capacity = sum(rec['recommended_capacity_kw'] for rec in infrastructure_recommendations)
        
        # Generate justification
        justification = self._generate_justification(priority_zone, zone_scores[priority_zone], infrastructure_recommendations)
        
        return {
            'recommended_infrastructure': infrastructure_recommendations,
            'priority_zone': priority_zone,
            'required_capacity': {
                'total_kw': total_capacity,
                'by_type': self._aggregate_capacity_by_type(infrastructure_recommendations)
            },
            'justification': justification,
            'zone_scores': zone_scores
        }
    
    def _calculate_zone_score(
        self,
        patterns: List[Dict],
        confidence_results: List[Dict],
        flow_graph: Dict
    ) -> Dict:
        """
        Calculate zone scorecard with persistence, stability, and coordination strength.
        
        Args:
            patterns: Patterns for this zone
            confidence_results: Confidence results from ZENTARI
            flow_graph: Flow graph from LUNDAI
            
        Returns:
            Zone scorecard with persistence_score, stability_score, coordination_strength, overall_rating
        """
        
        # Get confidence results for this zone's patterns
        zone_confidence = [
            r for r in confidence_results
            if any(p['activity_type'] == r['activity_type'] and p['zone'] == r['zone'] for p in patterns)
        ]
        
        # Calculate persistence score (average across patterns)
        persistence_values = [r.get('persistence', 0) for r in zone_confidence]
        persistence_score = sum(persistence_values) / len(persistence_values) if persistence_values else 0
        
        # Calculate stability score (average across patterns)
        stability_values = [r.get('stability_score', 0) for r in zone_confidence]
        stability_score = sum(stability_values) / len(stability_values) if stability_values else 0
        
        # Calculate coordination strength (based on flow graph)
        coordination_strength = self._calculate_coordination_strength(patterns, flow_graph)
        
        # Calculate overall rating (weighted composite)
        overall_rating = (0.4 * persistence_score) + (0.3 * stability_score) + (0.3 * coordination_strength)
        
        # Determine rating category
        if overall_rating >= 0.7:
            rating_category = 'high'
        elif overall_rating >= 0.5:
            rating_category = 'moderate'
        else:
            rating_category = 'low'
        
        return {
            'persistence_score': round(persistence_score, 2),
            'stability_score': round(stability_score, 2),
            'coordination_strength': round(coordination_strength, 2),
            'overall_rating': round(overall_rating, 2),
            'rating_category': rating_category
        }
    
    def _calculate_coordination_strength(self, patterns: List[Dict], flow_graph: Dict) -> float:
        """
        Calculate coordination strength based on flow graph connections.
        
        Args:
            patterns: Patterns for this zone
            flow_graph: Flow graph from LUNDAI
            
        Returns:
            Coordination strength score (0-1)
        """
        
        edges = flow_graph.get('edges', [])
        
        # Filter edges for this zone's activities
        zone_activities = set(p['activity_type'] for p in patterns)
        zone_edges = [
            e for e in edges
            if e.get('from_activity') in zone_activities or e.get('to_activity') in zone_activities
        ]
        
        if not zone_edges:
            return 0.0
        
        # Calculate average strength of connections
        strength_values = [e.get('strength_score', 0) for e in zone_edges]
        avg_strength = sum(strength_values) / len(strength_values) if strength_values else 0
        
        # Adjust by number of connections (more connections = stronger coordination)
        connection_factor = min(len(zone_edges) / 5.0, 1.0)  # Normalize to 0-1
        
        return round(avg_strength * connection_factor, 2)
    
    def _determine_infrastructure_needs(
        self,
        patterns: List[Dict],
        confidence_results: List[Dict]
    ) -> List[Dict]:
        """
        Determine infrastructure needs based on patterns and confidence.
        
        Args:
            patterns: Patterns for the zone
            confidence_results: Confidence results from ZENTARI
            
        Returns:
            List of infrastructure recommendations
        """
        
        infrastructure_recommendations = []
        
        # Group patterns by activity type
        activity_patterns = defaultdict(list)
        for pattern in patterns:
            activity_patterns[pattern['activity_type']].append(pattern)
        
        # For each activity type, determine infrastructure need
        for activity_type, activity_pattern_list in activity_patterns.items():
            if activity_type not in self.ACTIVITY_INFRASTRUCTURE_MAP:
                continue
            
            # Get average confidence for this activity
            activity_confidence = [
                r for r in confidence_results
                if r['activity_type'] == activity_type
            ]
            
            if not activity_confidence:
                continue
            
            avg_confidence = sum(r.get('confidence_score', 0) for r in activity_confidence) / len(activity_confidence)
            
            # Only recommend infrastructure if confidence is moderate or higher
            if avg_confidence >= 50:  # 0-100 scale
                base_infra = self.ACTIVITY_INFRASTRUCTURE_MAP[activity_type]
                
                # Adjust capacity based on pattern frequency
                pattern_frequency = sum(p.get('pattern_frequency', 1) for p in activity_pattern_list)
                capacity_multiplier = min(pattern_frequency / 3.0, 1.5)  # Cap at 1.5x
                
                infrastructure_recommendations.append({
                    'activity_type': activity_type,
                    'infrastructure_type': base_infra['type'],
                    'min_capacity_kw': round(base_infra['min_capacity_kw'] * capacity_multiplier, 1),
                    'recommended_capacity_kw': round(base_infra['recommended_capacity_kw'] * capacity_multiplier, 1),
                    'priority': base_infra['priority'],
                    'confidence_score': round(avg_confidence, 0),
                    'justification': base_infra['justification']
                })
        
        # Sort by priority (high > medium > low)
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        infrastructure_recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return infrastructure_recommendations
    
    def _aggregate_capacity_by_type(self, recommendations: List[Dict]) -> Dict:
        """
        Aggregate capacity requirements by infrastructure type.
        
        Args:
            recommendations: Infrastructure recommendations
            
        Returns:
            Capacity aggregated by type
        """
        
        capacity_by_type = defaultdict(float)
        
        for rec in recommendations:
            infra_type = rec['infrastructure_type']
            capacity_by_type[infra_type] += rec['recommended_capacity_kw']
        
        return {
            type_: round(capacity, 1)
            for type_, capacity in capacity_by_type.items()
        }
    
    def _generate_justification(
        self,
        zone: str,
        zone_score: Dict,
        recommendations: List[Dict]
    ) -> str:
        """
        Generate justification for infrastructure recommendation.
        
        Args:
            zone: Priority zone
            zone_score: Zone scorecard
            recommendations: Infrastructure recommendations
            
        Returns:
            Justification text
        """
        
        rating_category = zone_score['rating_category']
        
        justification_parts = [
            f"Zone {zone} selected as priority based on {rating_category} coordination strength "
            f"(overall rating: {zone_score['overall_rating']:.2f}). "
        ]
        
        if zone_score['persistence_score'] >= 0.6:
            justification_parts.append(
                f"High persistence ({zone_score['persistence_score']:.2f}) indicates consistent demand patterns. "
            )
        
        if zone_score['stability_score'] >= 0.6:
            justification_parts.append(
                f"High stability ({zone_score['stability_score']:.2f}) indicates reliable coordination. "
            )
        
        if zone_score['coordination_strength'] >= 0.6:
            justification_parts.append(
                f"Strong coordination ({zone_score['coordination_strength']:.2f}) indicates integrated economic activity. "
            )
        
        # Add infrastructure details
        if recommendations:
            high_priority = [r for r in recommendations if r['priority'] == 'high']
            if high_priority:
                activities = ', '.join(r['activity_type'] for r in high_priority)
                justification_parts.append(
                    f"High-priority infrastructure recommended for: {activities}. "
                )
        
        return ''.join(justification_parts)
    
    def regional_priority_ranking(self, zone_scores: Dict[str, Dict]) -> List[Dict]:
        """
        Rank zones by priority for regional infrastructure planning.
        
        This method extends the Decision Engine to support multi-zone
        infrastructure planning by ranking zones based on composite scores.
        
        Args:
            zone_scores: Dictionary mapping zones to their scorecard metrics
            
        Returns:
            List of zones ranked by regional priority
        """
        return self.rank_zones_by_priority(zone_scores)
    
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


def print_decision_recommendations(recommendations: Dict) -> None:
    """Print decision recommendations in a readable format."""
    print("\n" + "=" * 60)
    print("DECISION ENGINE OUTPUT - INFRASTRUCTURE RECOMMENDATIONS")
    print("=" * 60)
    
    if not recommendations.get('priority_zone'):
        print("\nNo infrastructure recommendations at this time.")
        print(recommendations.get('justification', ''))
        return
    
    print(f"\nPriority Zone: {recommendations['priority_zone']}")
    print(f"Total Required Capacity: {recommendations['required_capacity']['total_kw']} kW")
    
    print("\nInfrastructure Recommendations:")
    for rec in recommendations['recommended_infrastructure']:
        print(f"  - {rec['activity_type'].capitalize()}:")
        print(f"    Type: {rec['infrastructure_type']}")
        print(f"    Capacity: {rec['recommended_capacity_kw']} kW")
        print(f"    Priority: {rec['priority']}")
        print(f"    Confidence: {rec['confidence_score']}%")
        print(f"    Justification: {rec['justification']}")
    
    print(f"\nJustification: {recommendations['justification']}")
    
    print("\nZone Scores:")
    for zone, score in recommendations['zone_scores'].items():
        print(f"  {zone}:")
        print(f"    Persistence: {score['persistence_score']}")
        print(f"    Stability: {score['stability_score']}")
        print(f"    Coordination Strength: {score['coordination_strength']}")
        print(f"    Overall Rating: {score['overall_rating']} ({score['rating_category']})")
    
    print("\n" + "=" * 60)
    print("INVARIANT COMPLIANCE:")
    print("✓ Zero-PII: Recommendations based on aggregated patterns only")
    print("✓ Coordination > Identity: Decisions for collective infrastructure")
    print("✓ Semantic Guard: Designed for planning, not surveillance")
    print("=" * 60)


if __name__ == "__main__":
    # Test with sample data
    print("Testing Decision Engine...")
    
    decision_engine = DecisionEngine()
    
    # Sample patterns
    patterns = [
        {'activity_type': 'irrigation', 'zone': 'MZUZU', 'pattern_frequency': 5},
        {'activity_type': 'milling', 'zone': 'MZUZU', 'pattern_frequency': 4},
        {'activity_type': 'irrigation', 'zone': 'LILONGWE', 'pattern_frequency': 3},
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
        {'activity_type': 'irrigation', 'zone': 'MZUZU', 'persistence': 0.8, 'stability_score': 0.7, 'confidence_score': 75},
        {'activity_type': 'milling', 'zone': 'MZUZU', 'persistence': 0.7, 'stability_score': 0.6, 'confidence_score': 65},
        {'activity_type': 'irrigation', 'zone': 'LILONGWE', 'persistence': 0.5, 'stability_score': 0.5, 'confidence_score': 50},
    ]
    
    recommendations = decision_engine.recommend_infrastructure(patterns, flow_graph, confidence_results)
    print_decision_recommendations(recommendations)
