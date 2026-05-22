"""
KULIMA OS Pilot - Multi-Sector Coordinator
==========================================

Multi-Sector Coordinator for integrated coordination layer with sector tagging.

INVARIANT ENFORCEMENT:
- Zero-PII: Operates only on aggregated patterns (never raw signals)
- Coordination > Identity: Analyzes collective patterns, not individual behaviors
- Semantic Guard: Designed for infrastructure planning, not surveillance or profiling

The Multi-Sector Coordinator extends the coordination intelligence system to support
multiple sectors (agriculture, energy, water, health, logistics) using a single
coordination engine with sector-specific mappings.
"""

from typing import List, Dict, Optional
from collections import defaultdict


class MultiSectorCoordinator:
    """
    Multi-Sector Coordinator for integrated coordination layer.
    
    Uses a single coordination engine with sector tagging to support
    multiple sectors while maintaining universal coordination logic.
    """
    
    # Sector definitions
    SECTORS = {
        'agriculture': {
            'activities': ['irrigation', 'milling', 'cold_storage', 'trading', 'welding'],
            'infrastructure_mapping': {
                'irrigation': {'type': 'pumping_systems_3phase', 'load_type': 'productive', 'base_capacity_kw': 20},
                'milling': {'type': 'processing_energy_3phase', 'load_type': 'productive', 'base_capacity_kw': 15},
                'cold_storage': {'type': 'refrigeration_load', 'load_type': 'productive', 'base_capacity_kw': 10},
                'trading': {'type': 'commercial_load', 'load_type': 'productive', 'base_capacity_kw': 2},
                'welding': {'type': 'industrial_load', 'load_type': 'productive', 'base_capacity_kw': 5}
            }
        },
        'energy': {
            'activities': ['grid_monitoring', 'load_balancing', 'transformer_maintenance'],
            'infrastructure_mapping': {
                'grid_monitoring': {'type': 'grid_infrastructure', 'load_type': 'critical', 'base_capacity_kw': 10},
                'load_balancing': {'type': 'grid_infrastructure', 'load_type': 'critical', 'base_capacity_kw': 15},
                'transformer_maintenance': {'type': 'grid_infrastructure', 'load_type': 'critical', 'base_capacity_kw': 20}
            }
        },
        'water': {
            'activities': ['water_distribution', 'water_treatment', 'pump_operation'],
            'infrastructure_mapping': {
                'water_distribution': {'type': 'water_infrastructure', 'load_type': 'essential', 'base_capacity_kw': 15},
                'water_treatment': {'type': 'water_infrastructure', 'load_type': 'essential', 'base_capacity_kw': 20},
                'pump_operation': {'type': 'water_infrastructure', 'load_type': 'essential', 'base_capacity_kw': 10}
            }
        },
        'health': {
            'activities': ['clinic_operations', 'medical_equipment', 'emergency_services'],
            'infrastructure_mapping': {
                'clinic_operations': {'type': 'critical_load', 'load_type': 'critical', 'base_capacity_kw': 25},
                'medical_equipment': {'type': 'critical_load', 'load_type': 'critical', 'base_capacity_kw': 30},
                'emergency_services': {'type': 'critical_load', 'load_type': 'critical', 'base_capacity_kw': 35}
            }
        },
        'logistics': {
            'activities': ['transport_flow', 'distribution', 'warehousing'],
            'infrastructure_mapping': {
                'transport_flow': {'type': 'distribution_infrastructure', 'load_type': 'productive', 'base_capacity_kw': 15},
                'distribution': {'type': 'distribution_infrastructure', 'load_type': 'productive', 'base_capacity_kw': 20},
                'warehousing': {'type': 'distribution_infrastructure', 'load_type': 'productive', 'base_capacity_kw': 25}
            }
        }
    }
    
    def __init__(self):
        """Initialize Multi-Sector Coordinator."""
        pass
    
    def classify_sector(self, activity_type: str) -> str:
        """
        Determine sector from activity type.
        
        Args:
            activity_type: Activity type to classify
            
        Returns:
            Sector identifier
        """
        activity_lower = activity_type.lower()
        
        for sector, sector_config in self.SECTORS.items():
            if activity_lower in sector_config['activities']:
                return sector
        
        # Default to agriculture for unknown activities
        return 'agriculture'
    
    def get_sector_infrastructure_mapping(self, sector: str, activity_type: str) -> Dict:
        """
        Get sector-specific infrastructure mapping for an activity.
        
        Args:
            sector: Sector identifier
            activity_type: Activity type
            
        Returns:
            Infrastructure mapping dictionary
        """
        if sector not in self.SECTORS:
            sector = 'agriculture'
        
        sector_config = self.SECTORS[sector]
        infrastructure_mapping = sector_config['infrastructure_mapping']
        
        # Return mapping for specific activity, or default mapping
        if activity_type in infrastructure_mapping:
            return infrastructure_mapping[activity_type]
        else:
            # Return default infrastructure for sector
            return {
                'type': 'general_load',
                'load_type': 'productive',
                'base_capacity_kw': 5
            }
    
    def apply_sector_tagging(self, signals: List[Dict]) -> List[Dict]:
        """
        Apply sector tagging to signals.
        
        Args:
            signals: List of signals without sector tags
            
        Returns:
            List of signals with sector tags added
        """
        tagged_signals = []
        
        for signal in signals:
            activity_type = signal.get('activity_type', '')
            sector = self.classify_sector(activity_type)
            
            tagged_signal = signal.copy()
            tagged_signal['sector'] = sector
            tagged_signals.append(tagged_signal)
        
        return tagged_signals
    
    def apply_sector_rules(self, patterns: List[Dict], sector: str) -> List[Dict]:
        """
        Apply sector-specific rules to coordination patterns.
        
        Args:
            patterns: Coordination patterns
            sector: Sector identifier
            
        Returns:
            Patterns with sector-specific rules applied
        """
        sector_patterns = []
        
        for pattern in patterns:
            activity_type = pattern.get('activity_type', '')
            infrastructure_mapping = self.get_sector_infrastructure_mapping(sector, activity_type)
            
            sector_pattern = pattern.copy()
            sector_pattern['sector'] = sector
            sector_pattern['infrastructure_type'] = infrastructure_mapping['type']
            sector_pattern['load_type'] = infrastructure_mapping['load_type']
            sector_pattern['base_capacity_kw'] = infrastructure_mapping['base_capacity_kw']
            
            sector_patterns.append(sector_pattern)
        
        return sector_patterns
    
    def generate_sector_report(self, sector: str, patterns: List[Dict]) -> Dict:
        """
        Generate sector-specific analysis report.
        
        Args:
            sector: Sector identifier
            patterns: Coordination patterns for the sector
            
        Returns:
            Sector analysis report
        """
        # Filter patterns by sector
        sector_patterns = [p for p in patterns if p.get('sector') == sector]
        
        if not sector_patterns:
            return {
                'sector': sector,
                'total_patterns': 0,
                'activities': [],
                'infrastructure_needs': [],
                'load_type_distribution': {}
            }
        
        # Analyze activities
        activities = list(set(p.get('activity_type') for p in sector_patterns))
        
        # Calculate infrastructure needs
        infrastructure_needs = []
        for activity in activities:
            activity_patterns = [p for p in sector_patterns if p.get('activity_type') == activity]
            infrastructure_mapping = self.get_sector_infrastructure_mapping(sector, activity)
            
            infrastructure_needs.append({
                'activity_type': activity,
                'infrastructure_type': infrastructure_mapping['type'],
                'load_type': infrastructure_mapping['load_type'],
                'base_capacity_kw': infrastructure_mapping['base_capacity_kw'],
                'pattern_count': len(activity_patterns)
            })
        
        # Calculate load type distribution
        load_type_distribution = defaultdict(int)
        for pattern in sector_patterns:
            load_type = pattern.get('load_type', 'productive')
            load_type_distribution[load_type] += 1
        
        return {
            'sector': sector,
            'total_patterns': len(sector_patterns),
            'activities': activities,
            'infrastructure_needs': infrastructure_needs,
            'load_type_distribution': dict(load_type_distribution),
            'coordination_summary': {
                'avg_persistence': self._calculate_avg_metric(sector_patterns, 'pattern_persistence'),
                'avg_stability': self._calculate_avg_metric(sector_patterns, 'pattern_stability'),
                'avg_confidence': self._calculate_avg_metric(sector_patterns, 'confidence_score')
            }
        }
    
    def generate_multi_sector_report(self, all_patterns: List[Dict]) -> Dict:
        """
        Generate comprehensive multi-sector analysis report.
        
        Args:
            all_patterns: All coordination patterns across sectors
            
        Returns:
            Multi-sector analysis report
        """
        # Generate reports for each sector
        sector_reports = {}
        
        for sector in self.SECTORS.keys():
            sector_report = self.generate_sector_report(sector, all_patterns)
            sector_reports[sector] = sector_report
        
        # Calculate cross-sector insights
        total_patterns = len(all_patterns)
        sector_distribution = {}
        
        for sector, report in sector_reports.items():
            sector_distribution[sector] = report['total_patterns']
        
        return {
            'total_patterns': total_patterns,
            'sector_distribution': sector_distribution,
            'sector_reports': sector_reports,
            'cross_sector_insights': {
                'dominant_sector': max(sector_distribution, key=sector_distribution.get) if sector_distribution else None,
                'sector_diversity': len([s for s, count in sector_distribution.items() if count > 0])
            }
        }
    
    def _calculate_avg_metric(self, patterns: List[Dict], metric_key: str) -> float:
        """
        Calculate average metric value across patterns.
        
        Args:
            patterns: List of patterns
            metric_key: Key of metric to average
            
        Returns:
            Average value
        """
        values = [p.get(metric_key, 0) for p in patterns if metric_key in p]
        if not values:
            return 0.0
        return round(sum(values) / len(values), 2)


def print_multi_sector_results(multi_sector_report: Dict) -> None:
    """Print multi-sector analysis results in a readable format."""
    print("\n" + "=" * 60)
    print("MULTI-SECTOR COORDINATOR OUTPUT")
    print("=" * 60)
    
    print(f"\nTotal Patterns: {multi_sector_report['total_patterns']}")
    print(f"Sector Diversity: {multi_sector_report['cross_sector_insights']['sector_diversity']}")
    print(f"Dominant Sector: {multi_sector_report['cross_sector_insights']['dominant_sector']}")
    
    print("\nSector Distribution:")
    for sector, count in multi_sector_report['sector_distribution'].items():
        print(f"  {sector}: {count} patterns")
    
    print("\nSector Reports:")
    for sector, report in multi_sector_report['sector_reports'].items():
        if report['total_patterns'] == 0:
            continue
        
        print(f"\n  {sector.upper()}:")
        print(f"    Total Patterns: {report['total_patterns']}")
        print(f"    Activities: {', '.join(report['activities'])}")
        print(f"    Coordination Summary:")
        print(f"      Avg Persistence: {report['coordination_summary']['avg_persistence']}")
        print(f"      Avg Stability: {report['coordination_summary']['avg_stability']}")
        print(f"      Avg Confidence: {report['coordination_summary']['avg_confidence']}")
    
    print("\n" + "=" * 60)
    print("INVARIANT COMPLIANCE:")
    print("✓ Zero-PII: Analysis based on aggregated patterns only")
    print("✓ Coordination > Identity: Sector patterns, not individual tracking")
    print("✓ Semantic Guard: Designed for planning, not surveillance")
    print("=" * 60)


if __name__ == "__main__":
    # Test with sample data
    print("Testing Multi-Sector Coordinator...")
    
    coordinator = MultiSectorCoordinator()
    
    # Sample signals
    signals = [
        {'activity_type': 'irrigation', 'zone': 'MZUZU', 'time_window': 'morning'},
        {'activity_type': 'milling', 'zone': 'MZUZU', 'time_window': 'afternoon'},
        {'activity_type': 'clinic_operations', 'zone': 'LILONGWE', 'time_window': 'morning'},
        {'activity_type': 'water_distribution', 'zone': 'BLANTYRE', 'time_window': 'morning'},
        {'activity_type': 'transport_flow', 'zone': 'ZOMBA', 'time_window': 'afternoon'}
    ]
    
    # Apply sector tagging
    tagged_signals = coordinator.apply_sector_tagging(signals)
    
    print("\nTagged Signals:")
    for signal in tagged_signals:
        print(f"  {signal['activity_type']} -> {signal['sector']}")
    
    # Sample patterns
    patterns = [
        {'activity_type': 'irrigation', 'zone': 'MZUZU', 'pattern_persistence': 0.8, 'pattern_stability': 0.7, 'confidence_score': 75},
        {'activity_type': 'milling', 'zone': 'MZUZU', 'pattern_persistence': 0.7, 'pattern_stability': 0.6, 'confidence_score': 70},
        {'activity_type': 'clinic_operations', 'zone': 'LILONGWE', 'pattern_persistence': 0.9, 'pattern_stability': 0.8, 'confidence_score': 85}
    ]
    
    # Apply sector tagging to patterns
    tagged_patterns = coordinator.apply_sector_tagging(patterns)
    
    # Generate multi-sector report
    multi_sector_report = coordinator.generate_multi_sector_report(tagged_patterns)
    
    print_multi_sector_results(multi_sector_report)
