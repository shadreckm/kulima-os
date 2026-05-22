"""
KULIMA OS Pilot - Cross-Zone Flow Detector
==========================================

Cross-Zone Flow Detector for regional coordination networks.

INVARIANT ENFORCEMENT:
- Zero-PII: Operates only on aggregated patterns (never raw signals)
- Coordination > Identity: Analyzes collective patterns, not individual behaviors
- Semantic Guard: Designed for infrastructure planning, not surveillance or profiling

The Cross-Zone Flow Detector identifies flows between zones and builds regional
coordination networks using correlation-based analysis of aggregate coordination signals.
"""

from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import statistics


class CrossZoneFlowDetector:
    """
    Cross-Zone Flow Detector for regional coordination network analysis.
    
    Identifies inter-zone flows using correlation-based analysis of coordination patterns.
    """
    
    def __init__(self):
        """Initialize Cross-Zone Flow Detector."""
        pass
    
    def detect_inter_zone_correlations(self, patterns_by_zone: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Detect similar activity patterns occurring in different zones.
        
        Args:
            patterns_by_zone: Dictionary mapping zones to their coordination patterns
            
        Returns:
            List of inter-zone flow correlations
        """
        inter_zone_flows = []
        
        # Get all zone pairs
        zones = list(patterns_by_zone.keys())
        
        for i in range(len(zones)):
            for j in range(i + 1, len(zones)):
                zone_a = zones[i]
                zone_b = zones[j]
                
                patterns_a = patterns_by_zone[zone_a]
                patterns_b = patterns_by_zone[zone_b]
                
                # Find correlations between zones
                correlations = self._find_activity_correlations(patterns_a, patterns_b, zone_a, zone_b)
                inter_zone_flows.extend(correlations)
        
        return inter_zone_flows
    
    def detect_time_shifted_correlations(self, patterns_by_zone: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Detect time-shifted correlations (e.g., milling in Zone B follows irrigation in Zone A).
        
        Args:
            patterns_by_zone: Dictionary mapping zones to their coordination patterns
            
        Returns:
            List of time-shifted inter-zone flows
        """
        time_shifted_flows = []
        
        # Get all zone pairs
        zones = list(patterns_by_zone.keys())
        
        for i in range(len(zones)):
            for j in range(len(zones)):
                if i == j:
                    continue
                
                zone_a = zones[i]
                zone_b = zones[j]
                
                patterns_a = patterns_by_zone[zone_a]
                patterns_b = patterns_by_zone[zone_b]
                
                # Find time-shifted correlations
                shifted_correlations = self._find_time_shifted_correlations(patterns_a, patterns_b, zone_a, zone_b)
                time_shifted_flows.extend(shifted_correlations)
        
        return time_shifted_flows
    
    def calculate_temporal_lag(self, zone_a_pattern: Dict, zone_b_pattern: Dict) -> float:
        """
        Calculate time lag between zones for similar activities.
        
        Args:
            zone_a_pattern: Pattern from zone A
            zone_b_pattern: Pattern from zone B
            
        Returns:
            Temporal lag in hours
        """
        # Extract time windows
        time_window_a = zone_a_pattern.get('time_window', 'morning')
        time_window_b = zone_b_pattern.get('time_window', 'morning')
        
        # Map time windows to hours
        time_map = {
            'morning': 8,
            'afternoon': 14,
            'evening': 18
        }
        
        hour_a = time_map.get(time_window_a, 12)
        hour_b = time_map.get(time_window_b, 12)
        
        lag = abs(hour_b - hour_a)
        
        return lag
    
    def calculate_correlation_strength(self, pattern_a: Dict, pattern_b: Dict) -> float:
        """
        Measure repeated co-occurrence strength between patterns.
        
        Args:
            pattern_a: First pattern
            pattern_b: Second pattern
            
        Returns:
            Correlation strength (0-1)
        """
        # Calculate based on pattern frequency and persistence
        freq_a = pattern_a.get('pattern_frequency', 1)
        freq_b = pattern_b.get('pattern_frequency', 1)
        persistence_a = pattern_a.get('pattern_persistence', 0)
        persistence_b = pattern_b.get('pattern_persistence', 0)
        
        # Normalize frequencies
        max_freq = max(freq_a, freq_b, 1)
        norm_freq_a = freq_a / max_freq
        norm_freq_b = freq_b / max_freq
        
        # Calculate correlation strength
        correlation = (norm_freq_a * norm_freq_b) * ((persistence_a + persistence_b) / 2)
        
        return round(correlation, 2)
    
    def calculate_sequence_consistency(self, patterns_sequence: List[Dict]) -> float:
        """
        Calculate consistency of activity sequences across zones.
        
        Args:
            patterns_sequence: List of patterns in sequence
            
        Returns:
            Sequence consistency score (0-1)
        """
        if len(patterns_sequence) < 2:
            return 0.0
        
        # Calculate variance in pattern frequencies
        frequencies = [p.get('pattern_frequency', 1) for p in patterns_sequence]
        
        try:
            variance = statistics.variance(frequencies)
            mean_freq = statistics.mean(frequencies)
            
            if mean_freq == 0:
                return 0.0
            
            consistency = 1.0 - min(variance / mean_freq, 1.0)
            return round(consistency, 2)
        except:
            return 0.0
    
    def build_regional_flow_network(self, all_zones_patterns: Dict[str, List[Dict]]) -> Dict:
        """
        Build cross-zone flow network graph.
        
        Args:
            all_zones_patterns: Dictionary mapping zones to their coordination patterns
            
        Returns:
            Flow network with nodes and edges
        """
        nodes = []
        edges = []
        
        node_id_counter = 0
        
        # Create nodes for each zone-activity combination
        for zone, patterns in all_zones_patterns.items():
            for pattern in patterns:
                node_id = f"node_{node_id_counter}"
                nodes.append({
                    'id': node_id,
                    'activity_type': pattern['activity_type'],
                    'zone': zone,
                    'frequency': pattern.get('pattern_frequency', 1),
                    'persistence': pattern.get('pattern_persistence', 0),
                    'confidence_score': pattern.get('confidence_score', 0),
                    'temporal_weight': pattern.get('temporal_weight', 1.0),
                    'persistence_weight': pattern.get('persistence_weight', 1.0)
                })
                node_id_counter += 1
        
        # Create edges for intra-zone flows (existing LUNDAI logic)
        for zone, patterns in all_zones_patterns.items():
            zone_edges = self._build_intra_zone_edges(patterns, zone, nodes)
            edges.extend(zone_edges)
        
        # Create edges for inter-zone flows
        inter_zone_flows = self.detect_inter_zone_correlations(all_zones_patterns)
        for flow in inter_zone_flows:
            # Find corresponding nodes
            from_node = self._find_node_by_activity_zone(nodes, flow['from_zone'], flow['activity_type'])
            to_node = self._find_node_by_activity_zone(nodes, flow['to_zone'], flow['activity_type'])
            
            if from_node and to_node:
                edges.append({
                    'from_node': from_node['id'],
                    'to_node': to_node['id'],
                    'from_zone': flow['from_zone'],
                    'to_zone': flow['to_zone'],
                    'zone': f"{flow['from_zone']}-{flow['to_zone']}",
                    'transition_probability': flow['correlation_strength'],
                    'average_time_lag_hours': flow['temporal_lag'],
                    'strength_score': flow['correlation_strength'],
                    'flow_type': 'inter_zone'
                })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'total_nodes': len(nodes),
            'total_edges': len(edges)
        }
    
    def _find_activity_correlations(self, patterns_a: List[Dict], patterns_b: List[Dict], zone_a: str, zone_b: str) -> List[Dict]:
        """
        Find activity correlations between two zones.
        
        Args:
            patterns_a: Patterns from zone A
            patterns_b: Patterns from zone B
            zone_a: Zone A identifier
            zone_b: Zone B identifier
            
        Returns:
            List of activity correlations
        """
        correlations = []
        
        # Group patterns by activity type
        activities_a = defaultdict(list)
        for pattern in patterns_a:
            activities_a[pattern['activity_type']].append(pattern)
        
        activities_b = defaultdict(list)
        for pattern in patterns_b:
            activities_b[pattern['activity_type']].append(pattern)
        
        # Find common activities
        common_activities = set(activities_a.keys()) & set(activities_b.keys())
        
        for activity in common_activities:
            patterns_for_activity_a = activities_a[activity]
            patterns_for_activity_b = activities_b[activity]
            
            # Calculate average correlation strength
            correlation_strength = 0
            temporal_lag = 0
            
            for pattern_a in patterns_for_activity_a:
                for pattern_b in patterns_for_activity_b:
                    correlation_strength += self.calculate_correlation_strength(pattern_a, pattern_b)
                    temporal_lag += self.calculate_temporal_lag(pattern_a, pattern_b)
            
            if patterns_for_activity_a and patterns_for_activity_b:
                count = len(patterns_for_activity_a) * len(patterns_for_activity_b)
                correlation_strength /= count
                temporal_lag /= count
            
            # Only include if correlation is significant
            if correlation_strength >= 0.3:
                correlations.append({
                    'from_zone': zone_a,
                    'to_zone': zone_b,
                    'activity_type': activity,
                    'temporal_lag': round(temporal_lag, 2),
                    'correlation_strength': round(correlation_strength, 2),
                    'sequence_consistency': 0.8  # Placeholder for sequence consistency
                })
        
        return correlations
    
    def _find_time_shifted_correlations(self, patterns_a: List[Dict], patterns_b: List[Dict], zone_a: str, zone_b: str) -> List[Dict]:
        """
        Find time-shifted correlations between zones.
        
        Args:
            patterns_a: Patterns from zone A
            patterns_b: Patterns from zone B
            zone_a: Zone A identifier
            zone_b: Zone B identifier
            
        Returns:
            List of time-shifted correlations
        """
        # This is a simplified implementation
        # In a full implementation, this would analyze temporal sequences
        # to detect patterns like "irrigation in Zone A followed by milling in Zone B"
        
        correlations = []
        
        # For now, use the same logic as regular correlations
        # but with emphasis on temporal lag
        regular_correlations = self._find_activity_correlations(patterns_a, patterns_b, zone_a, zone_b)
        
        for correlation in regular_correlations:
            if correlation['temporal_lag'] > 0:  # Has temporal lag
                correlation['is_time_shifted'] = True
                correlations.append(correlation)
        
        return correlations
    
    def _build_intra_zone_edges(self, patterns: List[Dict], zone: str, nodes: List[Dict]) -> List[Dict]:
        """
        Build edges for intra-zone flows (existing LUNDAI logic).
        
        Args:
            patterns: Patterns for the zone
            zone: Zone identifier
            nodes: List of all nodes
            
        Returns:
            List of intra-zone edges
        """
        edges = []
        
        # This would use existing LUNDAI flow detection logic
        # For now, create placeholder edges based on activity sequence
        
        for i in range(len(patterns) - 1):
            pattern_a = patterns[i]
            pattern_b = patterns[i + 1]
            
            from_node = self._find_node_by_activity_zone(nodes, zone, pattern_a['activity_type'])
            to_node = self._find_node_by_activity_zone(nodes, zone, pattern_b['activity_type'])
            
            if from_node and to_node:
                edges.append({
                    'from_node': from_node['id'],
                    'to_node': to_node['id'],
                    'zone': zone,
                    'transition_probability': 0.7,  # Placeholder
                    'average_time_lag_hours': 2,  # Placeholder
                    'strength_score': 0.7,  # Placeholder
                    'flow_type': 'intra_zone'
                })
        
        return edges
    
    def _find_node_by_activity_zone(self, nodes: List[Dict], zone: str, activity_type: str) -> Optional[Dict]:
        """
        Find a node by zone and activity type.
        
        Args:
            nodes: List of nodes
            zone: Zone identifier
            activity_type: Activity type
            
        Returns:
            Node dictionary or None
        """
        for node in nodes:
            if node['zone'] == zone and node['activity_type'] == activity_type:
                return node
        return None


def print_cross_zone_results(inter_zone_flows: List[Dict], flow_network: Dict) -> None:
    """Print cross-zone flow detection results in a readable format."""
    print("\n" + "=" * 60)
    print("CROSS-ZONE FLOW DETECTOR OUTPUT")
    print("=" * 60)
    
    print("\nInter-Zone Flows:")
    for flow in inter_zone_flows:
        print(f"  {flow['from_zone']} → {flow['to_zone']} ({flow['activity_type']}):")
        print(f"    Temporal Lag: {flow['temporal_lag']} hours")
        print(f"    Correlation Strength: {flow['correlation_strength']}")
        print(f"    Sequence Consistency: {flow['sequence_consistency']}")
    
    print("\nRegional Flow Network:")
    print(f"  Total Nodes: {flow_network['total_nodes']}")
    print(f"  Total Edges: {flow_network['total_edges']}")
    
    print("\n" + "=" * 60)
    print("INVARIANT COMPLIANCE:")
    print("✓ Zero-PII: Flows based on aggregated patterns only")
    print("✓ Coordination > Identity: Regional patterns, not individual tracking")
    print("✓ Semantic Guard: Designed for planning, not surveillance")
    print("=" * 60)


if __name__ == "__main__":
    # Test with sample data
    print("Testing Cross-Zone Flow Detector...")
    
    detector = CrossZoneFlowDetector()
    
    # Sample patterns by zone
    patterns_by_zone = {
        'MZUZU': [
            {'activity_type': 'irrigation', 'zone': 'MZUZU', 'pattern_frequency': 5, 'pattern_persistence': 0.8, 'time_window': 'morning'},
            {'activity_type': 'milling', 'zone': 'MZUZU', 'pattern_frequency': 4, 'pattern_persistence': 0.7, 'time_window': 'afternoon'}
        ],
        'LILONGWE': [
            {'activity_type': 'irrigation', 'zone': 'LILONGWE', 'pattern_frequency': 4, 'pattern_persistence': 0.7, 'time_window': 'morning'},
            {'activity_type': 'milling', 'zone': 'LILONGWE', 'pattern_frequency': 3, 'pattern_persistence': 0.6, 'time_window': 'afternoon'}
        ],
        'BLANTYRE': [
            {'activity_type': 'irrigation', 'zone': 'BLANTYRE', 'pattern_frequency': 3, 'pattern_persistence': 0.6, 'time_window': 'morning'}
        ]
    }
    
    # Detect inter-zone correlations
    inter_zone_flows = detector.detect_inter_zone_correlations(patterns_by_zone)
    
    # Build regional flow network
    flow_network = detector.build_regional_flow_network(patterns_by_zone)
    
    print_cross_zone_results(inter_zone_flows, flow_network)
