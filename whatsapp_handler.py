"""
WhatsApp Message Handler for LUMOZA Integration

Processes incoming WhatsApp messages and routes them through the signal pipeline.
Supports Twilio integration for MVP.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
from input_parser import parse_user_input, ParsedSignal
from signal_storage import store_signal
from lumoza_integration import integrate_whatsapp_to_lumoza
from coordination_accumulation import compute_coordination_trend
from zone_utils import normalize_zone
from prospectus_generator import ProspectusGenerator
from policy import compute_planning_reserve
from pilot_mode import is_pilot_mode, log_pilot_event
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
        
        # Parse as activity signal with phone-based zone inference (best effort)
        parsed_signal = parse_user_input(message_text, sender_phone=sender_phone)
        
        if not parsed_signal:
            return True, self._format_meaningless_message()
        
        print("Parsed activity:", parsed_signal.activity_type)
        
        # Store signal
        signal_id = store_signal(
            activity_type=parsed_signal.activity_type,
            zone=parsed_signal.zone,
            frequency=parsed_signal.frequency,
            actors=parsed_signal.actors,
            raw_message=message_text,
            user_phone=sender_phone,
            confidence=parsed_signal.confidence,
        )
        
        if signal_id:
            zone_key = normalize_zone(parsed_signal.zone)
            if is_pilot_mode():
                log_pilot_event(
                    {
                        "event_type": "incoming_signal",
                        "zone": zone_key,
                        "activity_type": parsed_signal.activity_type,
                        "signal_source": "whatsapp",
                        "confidence": parsed_signal.confidence,
                        "validated": None,
                        "signal_id": signal_id,
                    }
                )

            summary = integrate_whatsapp_to_lumoza(zone=zone_key, mark_processed=False)
            print(
                f"Processing zone {zone_key}: {summary['signals_in_window']} signals in window, "
                f"{summary['patterns_processed']} coordination patterns"
            )

            if summary["patterns"]:
                self._generate_artifact(zone_key, summary["patterns"])

            trend = compute_coordination_trend(zone_key)
            return True, self._format_success_message(trend)
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
            return False, "❌ Invalid REPORT command. Use: REPORT <ZONE> (e.g., 'REPORT B' or 'REPORT MZUZU')"

        zone = normalize_zone(zone)

        # Process only this zone's accumulated signals
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
        prospectus = gen.generate_prospectus(
            confidence_results,
            metadata=metadata,
            planning_reserve=summary['planning_reserve'],
        )
        
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
        """Parse zone from REPORT command (supports cluster names)."""
        parts = message.split()
        if len(parts) < 2 or parts[0].upper() != "REPORT":
            return None
        if len(parts) >= 3 and parts[1].upper() == "ZONE":
            raw = " ".join(parts[2:])
        else:
            raw = " ".join(parts[1:])
        return normalize_zone(raw)
    
    def _format_success_message(self, trend: str) -> str:
        """User-facing confirmation only — coordination trend from accumulated signals."""
        return (
            "✅ Activity recorded (best effort interpretation)\n\n"
            f"📊 Coordination trend: {trend}\n\n"
            "🔌 Thank you — your update supports local energy planning."
        )
    
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
            planning_reserve = compute_planning_reserve(len(confidence_results))
            prospectus = gen.generate_prospectus(
                confidence_results,
                metadata=metadata,
                planning_reserve=planning_reserve,
            )

            timestamp = datetime.utcnow().isoformat().replace(':', '-')
            artifacts_dir = Path(f"artifacts/{zone.lower()}/{timestamp}")
            artifacts_dir.mkdir(parents=True, exist_ok=True)

            pdf_filename = f"demand_prospectus_{zone.lower()}_{timestamp}.pdf"
            pdf_path = artifacts_dir / pdf_filename
            gen.generate_pdf(prospectus, str(pdf_path))

            json_filename = f"demand_prospectus_{zone.lower()}_{timestamp}.json"
            json_path = artifacts_dir / json_filename
            json_path.write_text(json.dumps(prospectus, indent=2))

            print(f"Artifact generated: {pdf_path}")
        except Exception as e:
            print(f"Error generating artifact: {e}")

    def _format_meaningless_message(self) -> str:
        """Friendly response when message has no interpretable content."""
        return (
            "✅ Activity recorded (best effort interpretation)\n\n"
            "📊 Coordination trend: Emerging\n\n"
            "🔌 Send a short note about what you did today when you can."
        )


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
