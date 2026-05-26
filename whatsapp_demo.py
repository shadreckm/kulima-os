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
    import logging
    logger = logging.getLogger(__name__)
    logger.info("=" * 70)
    logger.info("LUMOZA WhatsApp Interface - Local Demo")
    logger.info("=" * 70)
    logger.info("\nThis demo simulates WhatsApp user interactions with LUMOZA.")
    logger.info("Type 'exit' to quit, 'signals' to view stored signals, 'clear' to reset.\n")
    
    demo_count = 0
    
    while True:
        try:
            user_input = input("\n📱 [WhatsApp Message]: ").strip()
            
            if user_input.lower() == "exit":
                logger.info("\n👋 Demo ended.")
                break
            
            if user_input.lower() == "signals":
                signals = get_unprocessed_signals()
                logger.info("\n📊 Stored Signals (%s total):", len(signals))
                if signals:
                    for sig in signals:
                        logger.info("  • %s in %s (%s)%s", sig.activity_type, sig.zone, sig.frequency, (f" - {sig.actors} actors" if sig.actors else ""))
                else:
                    logger.info("  (no signals yet)")
                continue
            
            if user_input.lower() == "clear":
                # Reset storage
                default_storage._ensure_file()
                logger.info("✅ Storage cleared")
                demo_count = 0
                continue
            
            if not user_input:
                continue
            
            # Simulate WhatsApp user with phone number
            demo_count += 1
            phone = f"+256703200{demo_count:03d}"
            
            logger.info("\n→ Processing message from %s...", phone)
            
            # Process message
            success, response = process_message(user_input, phone)
            
            logger.info("\n🤖 LUMOZA Response:")
            logger.info(response)
            
        except KeyboardInterrupt:
            logger.info("\n\n👋 Demo ended.")
            break
        except Exception as e:
            logger.exception("❌ Error: %s", e)


def run_demo_script():
    """Run predefined demo sequence."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("=" * 70)
    logger.info("LUMOZA WhatsApp Interface - Automated Demo")
    logger.info("=" * 70)
    
    demo_messages = [
        ("Milling activity in Zone A, 3 times this week", "Automated Demo 1"),
        ("5 farmers doing irrigation in Zone B", "Automated Demo 2"),
        ("Traders selling maize daily in Zone C", "Automated Demo 3"),
        ("Cold storage Zone D, 10 actors, weekly", "Automated Demo 4"),
        ("GENERATE REPORT Zone A", "Report Request"),
    ]
    
    for message, description in demo_messages:
        logger.info("\n%s", '=' * 70)
        logger.info("📱 %s", description)
        logger.info("Message: %s", message)
        logger.info("-" * 70)

        success, response = process_message(message, f"+256{len(message):03d}")
        logger.info(response)
    
    logger.info("\n%s", '=' * 70)
    logger.info("📊 Final Signal Summary:")
    logger.info("=" * 70)
    
    signals = get_unprocessed_signals()
    logger.info("\nTotal signals stored: %s\n", len(signals))
    
    # Group by zone
    by_zone = {}
    for sig in signals:
        if sig.zone not in by_zone:
            by_zone[sig.zone] = []
        by_zone[sig.zone].append(sig)
    
    for zone, zone_signals in sorted(by_zone.items()):
        logger.info("\n📍 %s:", zone)
        for sig in zone_signals:
            logger.info("  • %s (%s)%s", sig.activity_type.upper(), sig.frequency, (f" - {sig.actors} actors" if sig.actors else ""))
    
    # Save to JSON for inspection
    logger.info("\n%s", '=' * 70)
    logger.info("💾 Signals saved to: lumoza_signals.json")
    logger.info("=" * 70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        run_demo_script()
    else:
        demo_session()
