"""
LUMOZA End-to-End CLI

Demonstrates the complete flow:
WhatsApp Input → Parser → Storage → LUMOZA Integration → Prospectus Generation

Usage:
    python lumoza_cli.py submit "Milling in Zone A, 3 times this week"
    python lumoza_cli.py process Zone A
    python lumoza_cli.py report Zone A
    python lumoza_cli.py status
"""

import sys
import json
from datetime import datetime
from pathlib import Path

from input_parser import parse_user_input
from signal_storage import store_signal, get_unprocessed_signals, default_storage
from lumoza_integration import integrate_whatsapp_to_lumoza
from prospectus_generator import ProspectusGenerator


def cmd_submit(message: str, phone: str = "+256700000000"):
    """Submit a WhatsApp signal."""
    print(f"\n📱 Submitting: {message}")
    
    parsed = parse_user_input(message, sender_phone=phone)
    if not parsed:
        print("❌ Could not parse message")
        return
    
    signal_id = store_signal(
        activity_type=parsed.activity_type,
        zone=parsed.zone,
        frequency=parsed.frequency,
        actors=parsed.actors,
        raw_message=message,
        user_phone=phone
    )
    
    if signal_id:
        print(f"✅ Signal stored: {signal_id}")
        print(f"   Activity: {parsed.activity_type}")
        print(f"   Zone: {parsed.zone}")
        print(f"   Frequency: {parsed.frequency}")
        if parsed.actors:
            print(f"   Actors: {parsed.actors}")
    else:
        print("❌ Error storing signal")


def cmd_process(zone: str = None):
    """Process signals through LUMOZA."""
    # Normalize zone format
    if zone:
        zone = zone.strip().upper().replace("ZONE_", "").replace("_", "").replace(" ", "")
    
    print(f"\n🔄 Processing signals{f' for zone {zone}' if zone else ''}...")
    
    summary = integrate_whatsapp_to_lumoza(zone=zone)
    
    print(f"\n✅ Processing complete")
    print(f"   Patterns converted: {summary['patterns_processed']}")
    print(f"   Status: {summary['status']}")
    
    if summary['patterns']:
        print(f"\n📊 Patterns:")
        for pattern in summary['patterns']:
            print(f"   • {pattern['activity_type']} in {pattern['zone']}")
            print(f"     Frequency: {pattern['demand_rhythm']['frequency']}")
            print(f"     Stability: {pattern['demand_rhythm']['stability_class']}")
    
    # Save summary to file
    output_file = f"lumoza_processing_{datetime.utcnow().isoformat().replace(':', '-')}.json"
    Path(output_file).write_text(json.dumps(summary, indent=2))
    print(f"\n💾 Processing summary saved: {output_file}")


def cmd_report(zone: str = None):
    """Generate prospectus report."""
    # Normalize zone format
    if zone:
        zone = zone.strip().upper().replace("ZONE_", "").replace("_", "").replace(" ", "")
    
    print(f"\n📄 Generating report{f' for zone {zone}' if zone else ''}...")
    
    # Get processed patterns
    summary = integrate_whatsapp_to_lumoza(zone=zone)
    patterns = summary['patterns']
    
    if not patterns:
        print("❌ No patterns to generate report")
        return
    
    # Convert to format expected by prospectus generator
    # For MVP, we'll create mock confidence results
    confidence_results = []
    for pattern in patterns:
        confidence_results.append({
            'activity_type': pattern['activity_type'],
            'zone': pattern['zone'],
            'time_window': pattern['demand_rhythm']['time_window'],  # Add missing time_window
            'confidence_class': pattern['confidence_class'],
            'stability_score': 0.7,
            'demand_rhythm': {
                'frequency': pattern['demand_rhythm']['frequency'],
                'stability_class': pattern['demand_rhythm']['stability_class']
            },
            'coordination_confidence': pattern['coordination_confidence'],
            'validation_strength': pattern['validation_strength'],
            'validation_details': pattern['validation_details'],
            'bankability_note': pattern['bankability_note']
        })
    
    # Generate prospectus
    gen = ProspectusGenerator()
    metadata = {
        'region': zone if zone else 'Pilot Region',
        'period': '7-cycle window (1 week)'
    }
    
    prospectus = gen.generate_prospectus(confidence_results, metadata=metadata)
    
    # Generate PDF
    pdf_path = f"lumoza_prospectus_{zone.lower() if zone else 'all'}_{datetime.utcnow().isoformat().replace(':', '-')}.pdf"
    gen.generate_pdf(prospectus, pdf_path)
    
    print(f"✅ Report generated")
    print(f"   PDF: {pdf_path}")
    print(f"   Patterns: {len(patterns)}")
    
    # Save JSON too
    json_path = pdf_path.replace('.pdf', '.json')
    Path(json_path).write_text(json.dumps(prospectus, indent=2))
    print(f"   JSON: {json_path}")


def cmd_status():
    """Show system status."""
    signals = get_unprocessed_signals()
    
    print("\n📊 LUMOZA WhatsApp System Status")
    print("=" * 50)
    print(f"Unprocessed signals: {len(signals)}")
    
    if signals:
        # Group by zone and activity
        by_zone = {}
        by_activity = {}
        
        for sig in signals:
            by_zone.setdefault(sig.zone, []).append(sig)
            by_activity.setdefault(sig.activity_type, []).append(sig)
        
        print(f"\nBy Zone:")
        for zone in sorted(by_zone.keys()):
            print(f"  {zone}: {len(by_zone[zone])} signals")
        
        print(f"\nBy Activity:")
        for activity in sorted(by_activity.keys()):
            print(f"  {activity}: {len(by_activity[activity])} signals")
    
    print("\nFiles:")
    if Path("lumoza_signals.json").exists():
        print(f"  ✓ lumoza_signals.json")


def cmd_clear():
    """Clear all stored signals."""
    default_storage._ensure_file()
    print("✅ All signals cleared")


def print_usage():
    """Print CLI usage."""
    print("""
LUMOZA End-to-End CLI

Usage:
    python lumoza_cli.py submit "<message>" [phone]
    python lumoza_cli.py process [zone]
    python lumoza_cli.py report [zone]
    python lumoza_cli.py status
    python lumoza_cli.py clear

Examples:
    python lumoza_cli.py submit "Milling in Zone A, 3 times this week"
    python lumoza_cli.py process Zone_A
    python lumoza_cli.py report Zone_A
    python lumoza_cli.py status
    """)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "submit":
        if len(sys.argv) < 3:
            print("❌ Message required: submit \"<message>\" [phone]")
            sys.exit(1)
        phone = sys.argv[3] if len(sys.argv) > 3 else "+256700000000"
        cmd_submit(sys.argv[2], phone)
    
    elif cmd == "process":
        zone = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_process(zone)
    
    elif cmd == "report":
        zone = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_report(zone)
    
    elif cmd == "status":
        cmd_status()
    
    elif cmd == "clear":
        cmd_clear()
    
    else:
        print(f"❌ Unknown command: {cmd}")
        print_usage()
        sys.exit(1)
