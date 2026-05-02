"""
KULIMA OS Pilot - Synthetic Coordination Signals
=================================================

This module generates synthetic, identity-free coordination signals for the pilot demonstration.

INVARIANT COMPLIANCE:
- Zero-PII: No personal identifiers, names, IDs, or individual locations
- Temporal Moat: Signals are pre-batched into 7-cycle windows (no real-time processing)
- Coordination > Identity: Signals represent activity types, not individuals
- Semantic Guard: No surveillance, tracking, or profiling capabilities

Each signal represents a coordination event from either:
1. Human-reported coordination (community members reporting collective activity)
2. Infrastructure telemetry (shared asset usage, aggregated at asset level)
"""

from typing import List, Dict, Literal

# Type definitions for clarity
ActivityType = Literal["irrigation", "milling", "cold_storage", "welding"]
TimeWindow = Literal["morning", "afternoon", "evening"]
SignalSource = Literal["human", "telemetry"]
Zone = Literal["zone_a", "zone_b", "zone_c"]


def generate_pilot_signals() -> List[Dict]:
    """
    Generate synthetic coordination signals for a 7-cycle (weekly) window.
    
    PRIVACY DESIGN:
    - No individual identifiers
    - Coarse spatial granularity (zones, not coordinates)
    - Coarse temporal granularity (time windows, not timestamps)
    - Signals represent activity types, not people
    
    Returns:
        List of identity-free coordination signals
    """
    
    signals = []
    
    # ZONE A: Stable irrigation pattern (appears 6 of 7 cycles)
    # Human signals establish the pattern
    for cycle in [1, 2, 3, 4, 5, 7]:  # Missing cycle 6
        signals.append({
            "activity_type": "irrigation",
            "cycle_index": cycle,
            "time_window": "morning",
            "zone": "zone_a",
            "signal_source": "human"
        })
    
    # Telemetry corroborates the pattern (pump runtime)
    for cycle in [1, 2, 3, 4, 5, 7]:
        signals.append({
            "activity_type": "irrigation",
            "cycle_index": cycle,
            "time_window": "morning",
            "zone": "zone_a",
            "signal_source": "telemetry"
        })
    
    # ZONE A: Stable milling pattern (appears 5 of 7 cycles)
    # Human signals
    for cycle in [2, 3, 4, 6, 7]:
        signals.append({
            "activity_type": "milling",
            "cycle_index": cycle,
            "time_window": "afternoon",
            "zone": "zone_a",
            "signal_source": "human"
        })
    
    # Telemetry corroborates (mill runtime)
    for cycle in [2, 3, 4, 6, 7]:
        signals.append({
            "activity_type": "milling",
            "cycle_index": cycle,
            "time_window": "afternoon",
            "zone": "zone_a",
            "signal_source": "telemetry"
        })
    
    # ZONE B: Stable cold storage pattern (appears 6 of 7 cycles)
    # Human signals
    for cycle in [1, 2, 3, 4, 5, 6]:
        signals.append({
            "activity_type": "cold_storage",
            "cycle_index": cycle,
            "time_window": "evening",
            "zone": "zone_b",
            "signal_source": "human"
        })
    
    # Telemetry corroborates (cold room power draw)
    for cycle in [1, 2, 3, 4, 5, 6]:
        signals.append({
            "activity_type": "cold_storage",
            "cycle_index": cycle,
            "time_window": "evening",
            "zone": "zone_b",
            "signal_source": "telemetry"
        })
    
    # ZONE B: Noise pattern - welding (appears only 2 of 7 cycles, should be filtered)
    for cycle in [3, 5]:
        signals.append({
            "activity_type": "welding",
            "cycle_index": cycle,
            "time_window": "morning",
            "zone": "zone_b",
            "signal_source": "human"
        })
    
    # ZONE C: Intermediate pattern - milling (appears 4 of 7 cycles, borderline)
    for cycle in [1, 3, 5, 7]:
        signals.append({
            "activity_type": "milling",
            "cycle_index": cycle,
            "time_window": "morning",
            "zone": "zone_c",
            "signal_source": "human"
        })
    
    # Partial telemetry corroboration (only 3 cycles)
    for cycle in [1, 3, 5]:
        signals.append({
            "activity_type": "milling",
            "cycle_index": cycle,
            "time_window": "morning",
            "zone": "zone_c",
            "signal_source": "telemetry"
        })
    
    # ZONE C: Discrepancy example - human signals without telemetry
    # (claimed coordination but no infrastructure corroboration)
    for cycle in [2, 4, 6]:
        signals.append({
            "activity_type": "irrigation",
            "cycle_index": cycle,
            "time_window": "afternoon",
            "zone": "zone_c",
            "signal_source": "human"
        })
    # No telemetry signals for this pattern - discrepancy
    
    return signals


def print_signal_summary(signals: List[Dict]) -> None:
    """Print a summary of the synthetic signals for verification."""
    print("=" * 60)
    print("KULIMA OS PILOT - SYNTHETIC COORDINATION SIGNALS")
    print("=" * 60)
    print(f"\nTotal signals generated: {len(signals)}")
    print(f"Signal sources: {set(s['signal_source'] for s in signals)}")
    print(f"Activity types: {set(s['activity_type'] for s in signals)}")
    print(f"Zones: {set(s['zone'] for s in signals)}")
    print(f"Cycle range: {min(s['cycle_index'] for s in signals)} - {max(s['cycle_index'] for s in signals)}")
    print("\nINVARIANT COMPLIANCE:")
    print("✓ Zero-PII: No personal identifiers in signals")
    print("✓ Temporal Moat: Pre-batched into 7-cycle windows")
    print("✓ Coordination > Identity: Signals represent activity types only")
    print("=" * 60)


if __name__ == "__main__":
    signals = generate_pilot_signals()
    print_signal_summary(signals)
    
    # Display first few signals as examples
    print("\nSample signals:")
    for signal in signals[:5]:
        print(f"  {signal}")

# Made with Bob
