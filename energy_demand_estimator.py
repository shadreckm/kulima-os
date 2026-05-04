"""
KULIMA OS - Energy Demand Estimator
====================================

Translates coordination patterns into conservative energy demand estimates.

DESIGN PRINCIPLES:
- Conservative by default: Use lower bounds of typical ranges
- Transparent assumptions: Every estimate has documented justification
- Activity-focused: Estimates based on activity types, not individuals
- Bankable outputs: Suitable for DFI and infrastructure planning review

INVARIANT COMPLIANCE:
- Zero-PII: No individual-level estimation, only aggregate patterns
- Coordination > Identity: Estimates derived from collective activity patterns
- Semantic Guard: For infrastructure planning only, not profiling

This module provides the technical foundation for translating informal economic
activity into bankable energy demand signals for infrastructure investment.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class LoadProfile:
    """Energy load profile for an activity type."""
    activity_type: str
    typical_power_kw_range: Tuple[float, float]  # (min, max) in kW
    hours_per_event_range: Tuple[float, float]   # (min, max) hours
    load_factor: float                            # 0.0 to 1.0
    diversity_factor: float                       # 0.0 to 1.0
    notes: str
    source: str


# Conservative load profiles based on rural electrification literature
# Sources: World Bank Rural Electrification Toolkit, ESMAP Technical Papers,
# IFC Productive Use of Energy studies
ACTIVITY_LOAD_PROFILES = {
    'irrigation': LoadProfile(
        activity_type='irrigation',
        typical_power_kw_range=(3.0, 7.5),
        hours_per_event_range=(2.0, 4.0),
        load_factor=0.85,
        diversity_factor=0.70,
        notes='Three-phase motor for water pumping. Sustained load during operation.',
        source='World Bank Rural Electrification Toolkit (2008), ESMAP Technical Paper 121'
    ),
    
    'milling': LoadProfile(
        activity_type='milling',
        typical_power_kw_range=(5.0, 15.0),
        hours_per_event_range=(3.0, 6.0),
        load_factor=0.75,
        diversity_factor=0.65,
        notes='Grain mill motor. High starting current, sustained load. Peak during harvest.',
        source='IFC Productive Use of Energy Study (2018), ESMAP Technical Paper 145'
    ),
    
    'cold_storage': LoadProfile(
        activity_type='cold_storage',
        typical_power_kw_range=(2.0, 8.0),
        hours_per_event_range=(8.0, 24.0),
        load_factor=0.60,
        diversity_factor=0.80,
        notes='Cold room compressor. Intermittent cycling, continuous operation. Critical for food security.',
        source='World Bank Cold Chain Development Study (2019), ESMAP Technical Paper 156'
    ),
    
    'welding': LoadProfile(
        activity_type='welding',
        typical_power_kw_range=(4.0, 10.0),
        hours_per_event_range=(2.0, 5.0),
        load_factor=0.50,
        diversity_factor=0.60,
        notes='Arc welding equipment. High instantaneous load, intermittent use. Industrial profile.',
        source='IFC Productive Use of Energy Study (2018)'
    ),
    
    # Essential services (for Critical Load Protection)
    'clinic': LoadProfile(
        activity_type='clinic',
        typical_power_kw_range=(1.5, 5.0),
        hours_per_event_range=(8.0, 24.0),
        load_factor=0.40,
        diversity_factor=0.90,
        notes='Medical equipment, lighting, refrigeration for vaccines. Non-negotiable load.',
        source='WHO Health Facility Electrification Guidelines (2020)'
    ),
    
    'school': LoadProfile(
        activity_type='school',
        typical_power_kw_range=(2.0, 6.0),
        hours_per_event_range=(6.0, 10.0),
        load_factor=0.50,
        diversity_factor=0.85,
        notes='Lighting, computers, fans. Daytime load. Essential for education access.',
        source='World Bank Education Infrastructure Study (2019)'
    ),
    
    'water_system': LoadProfile(
        activity_type='water_system',
        typical_power_kw_range=(3.0, 10.0),
        hours_per_event_range=(4.0, 12.0),
        load_factor=0.70,
        diversity_factor=0.85,
        notes='Community water pumping and treatment. Non-negotiable for public health.',
        source='World Bank Water Supply Electrification Study (2017)'
    ),
    
    'emergency_services': LoadProfile(
        activity_type='emergency_services',
        typical_power_kw_range=(2.0, 8.0),
        hours_per_event_range=(24.0, 24.0),
        load_factor=0.30,
        diversity_factor=0.95,
        notes='Emergency lighting, communications, backup systems. Must be always available.',
        source='UNDP Disaster Risk Reduction Guidelines (2018)'
    )
}


class EnergyDemandEstimator:
    """
    Estimates conservative energy demand from coordination patterns.
    
    Uses activity-level load profiles to translate coordination signals into
    bankable energy demand estimates (kW peak, kWh consumption).
    """
    
    def __init__(self):
        """Initialize energy demand estimator."""
        self.load_profiles = ACTIVITY_LOAD_PROFILES
    
    def estimate_pattern_demand(self, pattern: Dict) -> Dict:
        """
        Estimate energy demand for a single coordination pattern.
        
        Args:
            pattern: Coordination pattern from ZENTARI (includes activity_type, 
                    zone, time_window, frequency, confidence)
        
        Returns:
            Energy demand estimate with conservative bounds
        """
        activity_type = pattern['activity_type']
        
        # Handle both ZENTARI output format and direct pattern format
        if 'demand_rhythm' in pattern:
            frequency = pattern['demand_rhythm']['frequency']
            time_window = pattern['demand_rhythm'].get('time_window', pattern.get('time_window', 'unknown'))
        else:
            frequency = pattern.get('frequency', '0 of 7 cycles')
            time_window = pattern.get('time_window', 'unknown')
        
        if activity_type not in self.load_profiles:
            return self._unknown_activity_estimate(pattern)
        
        profile = self.load_profiles[activity_type]
        
        # Parse frequency (e.g., "6 of 7 cycles" -> 6)
        occurrences = int(frequency.split()[0])
        
        # Conservative estimation: use lower bounds
        power_kw_conservative = profile.typical_power_kw_range[0]
        hours_conservative = profile.hours_per_event_range[0]
        
        # Apply load factor (accounts for intermittent operation)
        effective_power_kw = power_kw_conservative * profile.load_factor
        
        # Energy per event
        energy_per_event_kwh = effective_power_kw * hours_conservative
        
        # Weekly energy (based on frequency)
        weekly_energy_kwh = energy_per_event_kwh * occurrences
        
        # Daily average
        daily_energy_kwh = weekly_energy_kwh / 7.0
        
        return {
            'activity_type': activity_type,
            'zone': pattern['zone'],
            'time_window': time_window,
            'frequency': frequency,
            'load_profile': {
                'power_range_kw': profile.typical_power_kw_range,
                'conservative_power_kw': power_kw_conservative,
                'effective_power_kw': round(effective_power_kw, 2),
                'hours_per_event_range': profile.hours_per_event_range,
                'conservative_hours': hours_conservative,
                'load_factor': profile.load_factor,
                'diversity_factor': profile.diversity_factor
            },
            'energy_estimate': {
                'per_event_kwh': round(energy_per_event_kwh, 2),
                'weekly_kwh': round(weekly_energy_kwh, 2),
                'daily_average_kwh': round(daily_energy_kwh, 2)
            },
            'notes': profile.notes,
            'source': profile.source,
            'estimation_method': 'Conservative lower-bound estimation using activity-level load profiles'
        }
    
    def estimate_zone_demand(self, patterns: List[Dict]) -> Dict:
        """
        Aggregate energy demand estimates for a zone.
        
        Args:
            patterns: List of coordination patterns for a single zone
        
        Returns:
            Aggregated zone-level demand estimate
        """
        zone = patterns[0]['zone'] if patterns else 'unknown'
        
        pattern_estimates = [self.estimate_pattern_demand(p) for p in patterns]
        
        # Aggregate peak demand (apply diversity factor)
        total_effective_power = sum(e['load_profile']['effective_power_kw'] for e in pattern_estimates)
        
        # Use weighted average diversity factor
        avg_diversity = sum(
            self.load_profiles[e['activity_type']].diversity_factor 
            for e in pattern_estimates if e['activity_type'] in self.load_profiles
        ) / len(pattern_estimates) if pattern_estimates else 0.7
        
        diversified_peak_kw = total_effective_power * avg_diversity
        
        # Aggregate daily energy
        total_daily_kwh = sum(e['energy_estimate']['daily_average_kwh'] for e in pattern_estimates)
        
        return {
            'zone': zone,
            'pattern_count': len(patterns),
            'activities': [e['activity_type'] for e in pattern_estimates],
            'peak_demand': {
                'undiversified_kw': round(total_effective_power, 2),
                'diversity_factor': round(avg_diversity, 2),
                'diversified_kw': round(diversified_peak_kw, 2),
                'notes': 'Diversified peak accounts for non-simultaneous operation'
            },
            'daily_energy': {
                'total_kwh': round(total_daily_kwh, 2),
                'per_pattern_kwh': [round(e['energy_estimate']['daily_average_kwh'], 2) for e in pattern_estimates]
            },
            'pattern_estimates': pattern_estimates
        }
    
    def estimate_total_demand(self, confidence_results: List[Dict]) -> Dict:
        """
        Estimate total energy demand across all zones and patterns.
        
        Args:
            confidence_results: All coordination patterns from ZENTARI
        
        Returns:
            System-wide demand estimate with productive/essential breakdown
        """
        # Group patterns by zone
        zones = {}
        for pattern in confidence_results:
            zone = pattern['zone']
            if zone not in zones:
                zones[zone] = []
            zones[zone].append(pattern)
        
        # Estimate demand for each zone
        zone_estimates = {zone: self.estimate_zone_demand(patterns) for zone, patterns in zones.items()}
        
        # Separate essential vs productive activities
        essential_activities = {'clinic', 'school', 'water_system', 'emergency_services'}
        productive_activities = {'irrigation', 'milling', 'cold_storage', 'welding'}
        
        essential_patterns = [p for p in confidence_results if p['activity_type'] in essential_activities]
        productive_patterns = [p for p in confidence_results if p['activity_type'] in productive_activities]
        
        # Aggregate totals
        total_peak_kw = sum(z['peak_demand']['diversified_kw'] for z in zone_estimates.values())
        total_daily_kwh = sum(z['daily_energy']['total_kwh'] for z in zone_estimates.values())
        
        # Essential vs productive breakdown
        essential_estimates = [self.estimate_pattern_demand(p) for p in essential_patterns]
        productive_estimates = [self.estimate_pattern_demand(p) for p in productive_patterns]
        
        essential_peak_kw = sum(e['load_profile']['effective_power_kw'] for e in essential_estimates) * 0.85
        productive_peak_kw = sum(e['load_profile']['effective_power_kw'] for e in productive_estimates) * 0.70
        
        essential_daily_kwh = sum(e['energy_estimate']['daily_average_kwh'] for e in essential_estimates)
        productive_daily_kwh = sum(e['energy_estimate']['daily_average_kwh'] for e in productive_estimates)
        
        return {
            'total_demand': {
                'peak_kw': round(total_peak_kw, 2),
                'daily_kwh': round(total_daily_kwh, 2),
                'monthly_kwh': round(total_daily_kwh * 30, 2),
                'annual_kwh': round(total_daily_kwh * 365, 2)
            },
            'essential_demand': {
                'peak_kw': round(essential_peak_kw, 2),
                'daily_kwh': round(essential_daily_kwh, 2),
                'percentage_of_total': round((essential_peak_kw / total_peak_kw * 100) if total_peak_kw > 0 else 0, 1)
            },
            'productive_demand': {
                'peak_kw': round(productive_peak_kw, 2),
                'daily_kwh': round(productive_daily_kwh, 2),
                'percentage_of_total': round((productive_peak_kw / total_peak_kw * 100) if total_peak_kw > 0 else 0, 1)
            },
            'zone_breakdown': zone_estimates,
            'estimation_metadata': {
                'method': 'Conservative lower-bound estimation',
                'diversity_applied': True,
                'load_factors_applied': True,
                'confidence_note': 'Estimates use lower bounds of typical ranges for bankability'
            }
        }
    
    def _unknown_activity_estimate(self, pattern: Dict) -> Dict:
        """Fallback estimate for unknown activity types."""
        # Handle both ZENTARI output format and direct pattern format
        if 'demand_rhythm' in pattern:
            frequency = pattern['demand_rhythm']['frequency']
            time_window = pattern['demand_rhythm'].get('time_window', pattern.get('time_window', 'unknown'))
        else:
            frequency = pattern.get('frequency', '0 of 7 cycles')
            time_window = pattern.get('time_window', 'unknown')
            
        return {
            'activity_type': pattern['activity_type'],
            'zone': pattern['zone'],
            'time_window': time_window,
            'frequency': frequency,
            'load_profile': {
                'power_range_kw': (2.0, 5.0),
                'conservative_power_kw': 2.0,
                'effective_power_kw': 1.5,
                'hours_per_event_range': (2.0, 4.0),
                'conservative_hours': 2.0,
                'load_factor': 0.75,
                'diversity_factor': 0.70
            },
            'energy_estimate': {
                'per_event_kwh': 3.0,
                'weekly_kwh': 15.0,
                'daily_average_kwh': 2.1
            },
            'notes': 'Unknown activity type - using generic productive use profile',
            'source': 'Generic estimate',
            'estimation_method': 'Fallback estimation for unknown activity'
        }


if __name__ == "__main__":
    # Test energy demand estimation
    from pilot_signals import generate_pilot_signals
    from lumoza_engine import LumozaEngine
    from zentari_engine import ZentariEngine
    
    print("Testing Energy Demand Estimator...")
    
    # Process signals
    signals = generate_pilot_signals()
    lumoza = LumozaEngine()
    patterns = lumoza.process_signals(signals)
    
    zentari = ZentariEngine()
    confidence_results = zentari.evaluate_coordination_confidence(patterns)
    
    # Estimate demand
    estimator = EnergyDemandEstimator()
    demand_estimate = estimator.estimate_total_demand(confidence_results)
    
    print("\n=== TOTAL DEMAND ESTIMATE ===")
    print(f"Peak Demand: {demand_estimate['total_demand']['peak_kw']} kW")
    print(f"Daily Energy: {demand_estimate['total_demand']['daily_kwh']} kWh")
    print(f"Monthly Energy: {demand_estimate['total_demand']['monthly_kwh']} kWh")
    print(f"\nEssential: {demand_estimate['essential_demand']['peak_kw']} kW ({demand_estimate['essential_demand']['percentage_of_total']}%)")
    print(f"Productive: {demand_estimate['productive_demand']['peak_kw']} kW ({demand_estimate['productive_demand']['percentage_of_total']}%)")
    
    print("\n✓ Energy demand estimation complete")

# Made with Bob
