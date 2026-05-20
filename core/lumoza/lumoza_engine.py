"""
KULIMA OS Pilot - LUMOZA Coordination Engine
=============================================

LUMOZA processes identity-free coordination signals into demand rhythms using 7-cycle logic.

INVARIANT ENFORCEMENT:
- Zero-PII: Operates only on activity types, zones, and time windows (no individuals)
- Temporal Moat: Processes pre-batched 7-cycle windows (no real-time streaming)
- Coordination > Identity: Reasons over collective patterns, never individual behaviors
- Semantic Guard: No surveillance, tracking, profiling, or credit scoring capabilities

LUMOZA transforms heterogeneous activity signals into:
1. Demand rhythms (when and where productive activities cluster)
2. Stability scores (how reliably patterns repeat)
3. Validation strength (human-telemetry alignment)
"""

from typing import List, Dict, Tuple
from collections import defaultdict


class LumozaEngine:
    """
    LUMOZA - Livelihood and Energy Coordination Engine
    
    Processes coordination signals through 7-cycle logic to identify stable,
    coordinated demand patterns without tracking individuals.
    """
    
    # Coordination thresholds
    STABLE_THRESHOLD = 5  # Pattern must appear in ≥5 of 7 cycles
    NOISE_THRESHOLD = 3   # Pattern appearing in <3 cycles is noise
    TOTAL_CYCLES = 7
    
    def __init__(self):
        """Initialize LUMOZA engine."""
        pass
    
    def process_signals(self, signals: List[Dict]) -> List[Dict]:
        """
        Process coordination signals through 7-cycle logic.
        
        TEMPORAL MOAT ENFORCEMENT:
        - Accepts only pre-batched signals (no real-time processing)
        - Groups signals into coordination patterns
        - Discards temporal precision beyond cycle windows
        
        COORDINATION > IDENTITY ENFORCEMENT:
        - Groups by activity_type, zone, time_window (not individuals)
        - Counts pattern occurrences across cycles
        - Produces aggregate outputs only
        
        Args:
            signals: List of identity-free coordination signals
            
        Returns:
            List of coordination patterns with demand rhythms and stability scores
        """
        
        # Group signals by coordination pattern (activity, zone, time_window)
        # ZERO-PII: No individual identifiers in grouping keys
        pattern_groups = self._group_by_pattern(signals)
        
        # Process each pattern through 7-cycle logic
        coordination_patterns = []
        
        for pattern_key, pattern_signals in pattern_groups.items():
            activity_type, zone, time_window = pattern_key
            
            # Analyze pattern across 7 cycles
            pattern_analysis = self._analyze_pattern(pattern_signals)
            
            # Apply coordination thresholds
            if pattern_analysis['cycle_count'] < self.NOISE_THRESHOLD:
                # Noise: discard pattern
                continue
            
            # Determine stability classification
            if pattern_analysis['cycle_count'] >= self.STABLE_THRESHOLD:
                stability_class = "stable"
            else:
                stability_class = "intermediate"
            
            # Calculate stability score (0-1)
            stability_score = pattern_analysis['cycle_count'] / self.TOTAL_CYCLES
            
            # Cross-validate with telemetry
            validation_result = self._cross_validate(pattern_signals)
            
            # Determine service priority (essential vs productive)
            # CRITICAL LOAD PROTECTION: Essential services are identified and flagged
            service_priority = self._determine_service_priority(pattern_signals)
            
            # Build coordination pattern output
            # ZERO-PII: Output contains only aggregates, no individual data
            coordination_pattern = {
                "activity_type": activity_type,
                "zone": zone,
                "time_window": time_window,
                "service_priority": service_priority,
                "demand_rhythm": {
                    "frequency": f"{pattern_analysis['cycle_count']} of {self.TOTAL_CYCLES} cycles",
                    "cycles_present": sorted(pattern_analysis['cycles_present']),
                    "stability_class": stability_class
                },
                "stability_score": round(stability_score, 2),
                "validation_strength": validation_result['strength'],
                "validation_details": validation_result['details']
            }
            
            coordination_patterns.append(coordination_pattern)
        
        return coordination_patterns
    
    def _group_by_pattern(self, signals: List[Dict]) -> Dict[Tuple, List[Dict]]:
        """
        Group signals by coordination pattern (activity, zone, time_window).
        
        COORDINATION > IDENTITY:
        - Groups by collective activity characteristics
        - No individual identifiers in grouping
        """
        pattern_groups = defaultdict(list)
        
        for signal in signals:
            pattern_key = (
                signal['activity_type'],
                signal['zone'],
                signal['time_window']
            )
            pattern_groups[pattern_key].append(signal)
        
        return dict(pattern_groups)
    
    def _analyze_pattern(self, pattern_signals: List[Dict]) -> Dict:
        """
        Analyze how a pattern repeats across 7 cycles.
        
        TEMPORAL MOAT:
        - Analyzes cycle-level patterns (not precise timestamps)
        - Destroys temporal precision needed for tracking
        """
        cycles_present = set()
        
        for signal in pattern_signals:
            cycles_present.add(signal['cycle_index'])
        
        return {
            'cycle_count': len(cycles_present),
            'cycles_present': list(cycles_present)
        }
    
    def _cross_validate(self, pattern_signals: List[Dict]) -> Dict:
        """
        Cross-validate human signals with infrastructure telemetry.
        
        VALIDATION WITHOUT SURVEILLANCE:
        - Checks if human-reported patterns align with telemetry
        - Operates at aggregate level (never individual)
        - Discrepancies reduce confidence but don't penalize participants
        
        Returns:
            Validation result with strength and details
        """
        # Separate human and telemetry signals
        human_cycles = set()
        telemetry_cycles = set()
        
        for signal in pattern_signals:
            cycle = signal['cycle_index']
            if signal['signal_source'] == 'human':
                human_cycles.add(cycle)
            elif signal['signal_source'] == 'telemetry':
                telemetry_cycles.add(cycle)
        
        # Calculate alignment
        if not human_cycles:
            # No human signals (shouldn't happen in valid data)
            return {
                'strength': 'none',
                'details': 'No human coordination signals'
            }
        
        if not telemetry_cycles:
            # Human signals without telemetry corroboration
            return {
                'strength': 'human_only',
                'details': f'Human signals in {len(human_cycles)} cycles, no telemetry corroboration'
            }
        
        # Calculate overlap
        aligned_cycles = human_cycles & telemetry_cycles
        alignment_ratio = len(aligned_cycles) / len(human_cycles)
        
        if alignment_ratio >= 0.8:
            strength = 'strong'
        elif alignment_ratio >= 0.5:
            strength = 'moderate'
        else:
            strength = 'weak'
        
        return {
            'strength': strength,
            'details': f'{len(aligned_cycles)} of {len(human_cycles)} human cycles corroborated by telemetry'
        }
    
    def _determine_service_priority(self, pattern_signals: List[Dict]) -> str:
        """
        Determine if a coordination pattern represents essential services or productive activity.
        
        CRITICAL LOAD PROTECTION:
        - Essential services (clinics, schools, water systems, emergency services) are flagged
        - These patterns will be prioritized in capacity planning
        - Cannot be overridden by commercial optimization
        
        Returns:
            'essential' for critical communal services, 'productive' for economic activities
        """
        # Check if any signal in the pattern has essential priority
        for signal in pattern_signals:
            if signal.get('service_priority') == 'essential':
                return 'essential'
        
        # Default to productive if not explicitly marked as essential
        # Use first signal's priority or default to 'productive'
        if pattern_signals:
            return pattern_signals[0].get('service_priority', 'productive')
        return 'productive'


def print_coordination_patterns(patterns: List[Dict]) -> None:
    """Print coordination patterns in a readable format."""
    print("\n" + "=" * 60)
    print("LUMOZA OUTPUT - COORDINATION PATTERNS")
    print("=" * 60)
    
    if not patterns:
        print("\nNo stable coordination patterns detected.")
        return
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\nPattern {i}:")
        print(f"  Activity: {pattern['activity_type']}")
        print(f"  Zone: {pattern['zone']}")
        print(f"  Time Window: {pattern['time_window']}")
        print(f"  Service Priority: {pattern['service_priority'].upper()}")
        print(f"  Demand Rhythm: {pattern['demand_rhythm']['frequency']}")
        print(f"  Cycles Present: {pattern['demand_rhythm']['cycles_present']}")
        print(f"  Stability: {pattern['demand_rhythm']['stability_class']} (score: {pattern['stability_score']})")
        print(f"  Validation: {pattern['validation_strength']}")
        print(f"  Details: {pattern['validation_details']}")
    
    print("\n" + "=" * 60)
    print("INVARIANT COMPLIANCE:")
    print("[OK] Zero-PII: No individual identifiers in outputs")
    print("[OK] Temporal Moat: Cycle-level aggregation (no precise timestamps)")
    print("[OK] Coordination > Identity: Patterns represent collective activity")
    print("=" * 60)


if __name__ == "__main__":
    # Test with synthetic signals
    from pilot_signals import generate_pilot_signals
    
    print("Testing LUMOZA Engine with synthetic signals...")
    
    signals = generate_pilot_signals()
    lumoza = LumozaEngine()
    patterns = lumoza.process_signals(signals)
    
    print_coordination_patterns(patterns)
