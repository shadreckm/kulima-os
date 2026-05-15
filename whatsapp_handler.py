"""
WhatsApp Message Handler for LUMOZA Integration

Processes incoming WhatsApp messages and routes them through the signal pipeline.
Supports Twilio integration for MVP.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
from input_parser import parse_user_input, ParsedSignal
from signal_storage import store_signal, get_unprocessed_signals
from lumoza_integration import integrate_whatsapp_to_lumoza
from prospectus_generator import ProspectusGenerator
import json
from pathlib import Path


class WhatsAppMessageHandler:
    """
    Handles incoming WhatsApp messages and routes them through LUMOZA pipeline.
    """
    
    def __init__(self):
        pass
    
    def handle_incoming_message(self, message_text: str, sender_phone: str) -> Tuple[bool, str]:
        """
        Process incoming WhatsApp message.
        
        Args:
            message_text: User message content
            sender_phone: Sender's phone number
            
        Returns:
            Tuple of (success, response_message)
        """
        message_text = message_text.strip()
        
        # Check for report generation command
        if self._is_report_command(message_text):
            return self._handle_report_command(message_text)
        
        # Parse as activity signal with phone-based zone inference
        parsed_signal = parse_user_input(message_text, sender_phone=sender_phone)
        
        if not parsed_signal:
            return False, self._format_error_message()
        
        # Store signal
        signal_id = store_signal(
            activity_type=parsed_signal.activity_type,
            zone=parsed_signal.zone,
            frequency=parsed_signal.frequency,
            actors=parsed_signal.actors,
            raw_message=message_text,
            user_phone=sender_phone
        )
        
        if signal_id:
            # Count the zone backlog before processing the newly stored signal
            zone_signals = get_unprocessed_signals(zone=parsed_signal.zone)

            # Auto-process signals through the core pipeline and mark them as processed for this zone
            summary = integrate_whatsapp_to_lumoza(zone=parsed_signal.zone, mark_processed=True)
            print(f"🔄 Auto-processed: {len(summary['patterns'])} patterns from {len(summary['patterns'])} signals")
            
            # Optionally generate a light artifact when new signals arrive
            if summary['patterns']:
                self._generate_artifact(parsed_signal.zone, summary['patterns'])
            
            return True, self._format_success_message(parsed_signal, len(zone_signals))
        else:
            return False, "❌ Error storing signal. Please try again."
    
    def _is_report_command(self, message: str) -> bool:
        """Check if message is a report generation command."""
        return message.upper().startswith("REPORT")
    
    def _handle_report_command(self, message: str) -> Tuple[bool, str]:
        """Handle report generation command."""
        # Parse zone from "REPORT <ZONE>"
        zone = self._parse_report_zone(message)
        
        if not zone:
            return False, "❌ Invalid REPORT command. Use: REPORT <ZONE> (e.g., 'REPORT Zone B')"
        
        # Process signals for the zone
        summary = integrate_whatsapp_to_lumoza(zone=zone, mark_processed=True)
        patterns = summary['patterns']
        
        if not patterns:
            return True, f"📊 No coordination patterns found for {zone}. Submit more activity signals first."
        
        # Build confidence results
        confidence_results = []
        for pattern in patterns:
            confidence_results.append({
                'activity_type': pattern['activity_type'],
                'zone': pattern['zone'],
                'time_window': pattern['demand_rhythm']['time_window'],
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
        metadata = {'region': zone, 'period': '7-cycle window (1 week)'}
        prospectus = gen.generate_prospectus(confidence_results, metadata=metadata)
        
        # Create artifacts directory structure
        timestamp = datetime.utcnow().isoformat().replace(':', '-')
        artifacts_dir = Path(f"artifacts/{zone.lower()}/{timestamp}")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate PDF
        pdf_filename = f"demand_prospectus_{zone.lower()}_{timestamp}.pdf"
        pdf_path = artifacts_dir / pdf_filename
        gen.generate_pdf(prospectus, str(pdf_path))
        
        # Save JSON
        json_filename = f"demand_prospectus_{zone.lower()}_{timestamp}.json"
        json_path = artifacts_dir / json_filename
        json_path.write_text(json.dumps(prospectus, indent=2))
        
        response = f"✅ Report generated for {zone}.\n📄 Demand prospectus ready for planners."
        
        return True, response
    
    def _parse_report_zone(self, message: str) -> Optional[str]:
        """Parse zone from REPORT command."""
        parts = message.split()
        if len(parts) >= 2 and parts[0].upper() == "REPORT":
            if len(parts) >= 3 and parts[1].upper() == "ZONE":
                zone = parts[2].upper()
            else:
                zone = parts[1].upper()
            return zone
        return None
    
    def _format_success_message(self, signal: ParsedSignal, zone_signal_count: int) -> str:
        """Format success message for user."""
        # Determine coordination strength using the number of unprocessed signals in zone
        if zone_signal_count >= 5:
            strength = "Strong"
        elif zone_signal_count >= 3:
            strength = "Growing"
        else:
            strength = "Emerging"
        
        message = "✅ Activity Recorded\n\n"
        message += "📊 Coordination in your area:\n"
        message += f"• Status: {strength}\n\n"
        message += "🔌 Your input supports local energy planning"
        
        return message
    
    def _generate_artifact(self, zone: str, patterns: list):
        """Generate a light demand prospectus artifact for the current zone."""
        try:
            confidence_results = []
            for pattern in patterns:
                confidence_results.append({
                    'activity_type': pattern['activity_type'],
                    'zone': pattern['zone'],
                    'time_window': pattern['demand_rhythm']['time_window'],
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

            gen = ProspectusGenerator()
            metadata = {'region': zone, 'period': '7-cycle window (1 week)'}
            prospectus = gen.generate_prospectus(confidence_results, metadata=metadata)

            timestamp = datetime.utcnow().isoformat().replace(':', '-')
            artifacts_dir = Path(f"artifacts/{zone.lower()}/{timestamp}")
            artifacts_dir.mkdir(parents=True, exist_ok=True)

            pdf_filename = f"demand_prospectus_{zone.lower()}_{timestamp}.pdf"
            pdf_path = artifacts_dir / pdf_filename
            gen.generate_pdf(prospectus, str(pdf_path))

            json_filename = f"demand_prospectus_{zone.lower()}_{timestamp}.json"
            json_path = artifacts_dir / json_filename
            json_path.write_text(json.dumps(prospectus, indent=2))

            print(f"📄 Artifact generated: {pdf_path}")
        except Exception as e:
            print(f"Error generating artifact: {e}")

    def _format_error_message(self) -> str:
        """Format error message for malformed input."""
        message = "❌ Could not parse your message.\n\n"
        message += "Please send a simple activity update like:\n\n"
        message += "• 'I am irrigating my crops'\n"
        message += "• 'Our mill is busy this week'\n"
        message += "• 'I sold maize today'\n"
        message += "• 'Cold storage is filling up'\n"
        
        return message


def process_message(message_text: str, sender_phone: str) -> Tuple[bool, str]:
    """
    Convenience function to process a WhatsApp message.
    
    Args:
        message_text: Raw message from user
        sender_phone: Sender's phone number
        
    Returns:
        Tuple of (success, response_message)
    """
    handler = WhatsAppMessageHandler()
    return handler.handle_incoming_message(message_text, sender_phone)
