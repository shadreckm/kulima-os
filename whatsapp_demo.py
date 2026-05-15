"""
LUMOZA WhatsApp Demo - Local Testing Interface

Run this script to test LUMOZA WhatsApp integration locally without Twilio.
Simulates real WhatsApp user interactions.

Usage:
    python whatsapp_demo.py
"""

from whatsapp_handler import process_message
from signal_storage import get_unprocessed_signals, default_storage
import json


def demo_session():
    """Interactive demo of WhatsApp interface."""
    
    print("=" * 70)
    print("LUMOZA WhatsApp Interface - Local Demo")
    print("=" * 70)
    print("\nThis demo simulates WhatsApp user interactions with LUMOZA.")
    print("Type 'exit' to quit, 'signals' to view stored signals, 'clear' to reset.\n")
    
    demo_count = 0
    
    while True:
        try:
            user_input = input("\n📱 [WhatsApp Message]: ").strip()
            
            if user_input.lower() == "exit":
                print("\n👋 Demo ended.")
                break
            
            if user_input.lower() == "signals":
                signals = get_unprocessed_signals()
                print(f"\n📊 Stored Signals ({len(signals)} total):")
                if signals:
                    for sig in signals:
                        print(f"  • {sig.activity_type} in {sig.zone} ({sig.frequency})" + 
                              (f" - {sig.actors} actors" if sig.actors else ""))
                else:
                    print("  (no signals yet)")
                continue
            
            if user_input.lower() == "clear":
                # Reset storage
                default_storage._ensure_file()
                print("✅ Storage cleared")
                demo_count = 0
                continue
            
            if not user_input:
                continue
            
            # Simulate WhatsApp user with phone number
            demo_count += 1
            phone = f"+256703200{demo_count:03d}"
            
            print(f"\n→ Processing message from {phone}...")
            
            # Process message
            success, response = process_message(user_input, phone)
            
            print("\n🤖 LUMOZA Response:")
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Demo ended.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def run_demo_script():
    """Run predefined demo sequence."""
    
    print("=" * 70)
    print("LUMOZA WhatsApp Interface - Automated Demo")
    print("=" * 70)
    
    demo_messages = [
        ("Milling activity in Zone A, 3 times this week", "Automated Demo 1"),
        ("5 farmers doing irrigation in Zone B", "Automated Demo 2"),
        ("Traders selling maize daily in Zone C", "Automated Demo 3"),
        ("Cold storage Zone D, 10 actors, weekly", "Automated Demo 4"),
        ("GENERATE REPORT Zone A", "Report Request"),
    ]
    
    for message, description in demo_messages:
        print(f"\n{'='*70}")
        print(f"📱 {description}")
        print(f"Message: {message}")
        print("-" * 70)
        
        success, response = process_message(message, f"+256{len(message):03d}")
        print(response)
    
    print(f"\n{'='*70}")
    print("📊 Final Signal Summary:")
    print("=" * 70)
    
    signals = get_unprocessed_signals()
    print(f"\nTotal signals stored: {len(signals)}\n")
    
    # Group by zone
    by_zone = {}
    for sig in signals:
        if sig.zone not in by_zone:
            by_zone[sig.zone] = []
        by_zone[sig.zone].append(sig)
    
    for zone, zone_signals in sorted(by_zone.items()):
        print(f"\n📍 {zone}:")
        for sig in zone_signals:
            print(f"  • {sig.activity_type.upper()} ({sig.frequency})" + 
                  (f" - {sig.actors} actors" if sig.actors else ""))
    
    # Save to JSON for inspection
    print(f"\n{'='*70}")
    print("💾 Signals saved to: lumoza_signals.json")
    print("=" * 70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        run_demo_script()
    else:
        demo_session()
