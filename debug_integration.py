"""Debug script for LUMOZA signal integration."""

from signal_storage import get_unprocessed_signals, default_storage
from lumoza_integration import integrate_whatsapp_to_lumoza
import json

print("=" * 70)
print("LUMOZA Integration Debug")
print("=" * 70)

# Check stored signals
print("\n1. Signals in storage:")
with open('lumoza_signals.json') as f:
    all_sigs = json.load(f)
    for sig in all_sigs[:5]:
        print(f"  Zone='{sig['zone']}' (len={len(sig['zone'])}), Activity={sig['activity_type']}, Processed={sig['processed']}")

# Test zone filtering
print("\n2. Testing zone filter:")
zone_tests = ['Zone_A', 'ZONE_A', 'A', 'Zone A']
for zone in zone_tests:
    sigs = get_unprocessed_signals(zone=zone)
    print(f"  zone='{zone}': {len(sigs)} signals")

# Test unfiltered
print("\n3. All unprocessed signals:")
all_unprocessed = get_unprocessed_signals()
print(f"  Total: {len(all_unprocessed)}")

# Test LUMOZA integration
print("\n4. LUMOZA Integration (no zone filter):")
summary = integrate_whatsapp_to_lumoza()
print(f"  Patterns: {summary['patterns_processed']}")

print("\n5. LUMOZA Integration (Zone_A):")
summary_a = integrate_whatsapp_to_lumoza(zone='Zone_A')
print(f"  Patterns: {summary_a['patterns_processed']}")
if summary_a['patterns']:
    for p in summary_a['patterns']:
        print(f"    - {p['activity_type']} in {p['zone']}")
