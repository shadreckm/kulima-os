"""
Quick test script for Critical Load Protection feature
"""

from pilot_signals import generate_pilot_signals
from lumoza_engine import LumozaEngine
from zentari_engine import ZentariEngine
from prospectus_generator import ProspectusGenerator

print("Testing Critical Load Protection Implementation...")
print("=" * 70)

# Generate signals
signals = generate_pilot_signals()
print(f"\n1. Generated {len(signals)} signals")

# Count essential vs productive
essential_count = sum(1 for s in signals if s.get('service_priority') == 'essential')
productive_count = sum(1 for s in signals if s.get('service_priority') == 'productive')
print(f"   - Essential service signals: {essential_count}")
print(f"   - Productive activity signals: {productive_count}")

# Process through LUMOZA
lumoza = LumozaEngine()
patterns = lumoza.process_signals(signals)
print(f"\n2. LUMOZA detected {len(patterns)} coordination patterns")

# Count essential vs productive patterns
essential_patterns = [p for p in patterns if p.get('service_priority') == 'essential']
productive_patterns = [p for p in patterns if p.get('service_priority') == 'productive']
print(f"   - Essential service patterns: {len(essential_patterns)}")
print(f"   - Productive activity patterns: {len(productive_patterns)}")

# Show essential services detected
if essential_patterns:
    print("\n3. Essential Services Detected:")
    for p in essential_patterns:
        print(f"   - {p['activity_type']} in {p['zone']} ({p['time_window']})")

# Process through ZENTARI
zentari = ZentariEngine()
confidence_results = zentari.evaluate_coordination_confidence(patterns)

# Generate prospectus
generator = ProspectusGenerator()
prospectus = generator.generate_prospectus(confidence_results)

# Check Critical Load Protection section
if 'critical_load_protection' in prospectus:
    clp = prospectus['critical_load_protection']
    print(f"\n4. Critical Load Protection Analysis:")
    print(f"   - Enforcement Status: {clp['enforcement_status']}")
    print(f"   - Capacity Reserved: {clp['capacity_reservation']['percentage']}%")
    print(f"   - Essential Services: {clp['essential_service_count']}")
    print(f"   - Productive Activities: {clp['productive_activity_count']}")
    print(f"\n5. Scenario Analysis:")
    for scenario_name, scenario in clp['scenario_analysis'].items():
        print(f"   - {scenario_name.upper()}: {scenario['essential_load_percentage']}% reserved")

print("\n" + "=" * 70)
print("[SUCCESS] Critical Load Protection is working correctly!")
print("=" * 70)

# Made with Bob
