"""
Natural Language Input Parser for LUMOZA WhatsApp Interface

Converts user messages into structured coordination signals.
Designed for fast, lightweight parsing without heavy NLP dependencies.
"""

import re
from typing import Dict, Optional
from dataclasses import dataclass

ZONE_MAP = {
    "+265883766348": "B"
}
DEFAULT_ZONE = "B"


@dataclass
class ParsedSignal:
    """Structured representation of a user activity signal."""
    activity_type: str
    zone: str
    frequency: str
    actors: int = 1
    raw_message: str = ""
    confidence: float = 0.8
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/processing."""
        return {
            "activity_type": self.activity_type,
            "zone": self.zone,
            "frequency": self.frequency,
            "actors": self.actors,
            "raw_message": self.raw_message,
            "confidence": self.confidence
        }


class InputParser:
    """
    Parse natural language WhatsApp messages into LUMOZA signal format.
    
    Examples:
        "Milling activity in Zone A, 3 times this week"
        "5 farmers doing irrigation in Zone B"
        "Traders selling maize daily in Zone C"
        "Storage activity Zone D frequency 2 per week, 10 actors"
    """
    
    # Activity types the system recognizes
    ACTIVITY_KEYWORDS = {
        r'irrigat': 'irrigation',
        r'water\s+crops': 'irrigation',
        r'watering': 'irrigation',
        r'irrigation': 'irrigation',
        r'mill(?:ing)?': 'milling',
        r'grind(?:ing)?': 'milling',
        r'milling': 'milling',
        r'sell(?:ing)?': 'trading',
        r'sold': 'trading',
        r'market(?:ing)?': 'trading',
        r'trade(?:ing)?': 'trading',
        r'trading': 'trading',
        r'cold\s+storage': 'storage',
        r'storage': 'storage',
        r'store(?:d|age)?': 'storage',
        r'weld(?:ing)?': 'welding',
        r'clinic': 'clinic',
        r'health': 'clinic',
        r'school': 'school',
        r'education': 'school',
        r'water\b': 'irrigation'
    }
    
    # Zone patterns (order matters - most specific first)
    ZONE_PATTERNS = [
        r'in\s+zone\s+([A-Z0-9]+)',
        r'zone\s+([A-Z0-9]+)',
        r'area\s+([A-Z0-9]+)',
        r'in\s+([A-Z][A-Z0-9]*)',
    ]
    
    # Frequency patterns
    FREQUENCY_PATTERNS = {
        r'daily': 'daily',
        r'every\s+day': 'daily',
        r'\btoday\b': 'daily',
        r'\bthis\s+week\b': 'weekly',
        r'(\d+)\s+times?\s+(?:per\s+)?week': 'weekly',
        r'(\d+)\s+times?\s+(?:per\s+)?month': 'monthly',
        r'(\d+)\s+times?\s+this\s+week': 'weekly',
        r'(?:once|1)\s+(?:per\s+)?week': 'weekly',
        r'(?:twice|2)\s+(?:per\s+)?week': 'weekly',
        r'weekly': 'weekly',
        r'monthly': 'monthly',
        r'seasonal': 'seasonal',
    }
    
    # Number extraction patterns
    NUMBER_PATTERNS = [
        r'(\d+)\s+(?:farmers|traders|people|actors|users|participants)',
        r'(\d+)\s+(?:farmers|traders|people)',
    ]
    
    def parse(self, message: str, sender_phone: Optional[str] = None) -> Optional[ParsedSignal]:
        """
        Parse a user message into a structured signal.
        
        Args:
            message: Raw WhatsApp message text
            sender_phone: Optional sender phone number for zone inference
            
        Returns:
            ParsedSignal if parsing successful, None otherwise
        """
        message = message.strip().lower()
        
        # Extract activity type
        activity_type = self._extract_activity_type(message)
        if not activity_type:
            return None
        
        # Extract zone from message or infer from phone
        zone = self._extract_zone(message)
        if not zone:
            zone = self._infer_zone(sender_phone)
        
        # Default zone if not provided or inferred
        if not zone:
            zone = DEFAULT_ZONE
        
        # Extract frequency
        frequency = self._extract_frequency(message)
        if not frequency:
            frequency = "unknown"  # Allow unknown frequency
        
        # Extract number of actors (optional, default 1)
        actors = self._extract_actors(message)
        if actors is None:
            actors = 1
        
        signal = ParsedSignal(
            activity_type=activity_type,
            zone=zone,
            frequency=frequency,
            actors=actors,
            raw_message=message
        )
        
        return signal
    
    def _extract_activity_type(self, message: str) -> Optional[str]:
        """Extract activity type from message."""
        for pattern, activity_type in self.ACTIVITY_KEYWORDS.items():
            if re.search(pattern, message):
                return activity_type
        return None
    
    def _extract_zone(self, message: str) -> Optional[str]:
        """Extract zone identifier from message."""
        for pattern in self.ZONE_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                zone = match.group(1).strip()
                # Clean up zone name
                zone = zone.replace(" ", "_").upper()
                return zone
        return None

    def _infer_zone(self, sender_phone: Optional[str]) -> Optional[str]:
        """Infer zone from sender phone number."""
        if not sender_phone:
            return None
        normalized_phone = sender_phone.strip().lower().replace("whatsapp:", "").replace(" ", "")
        return ZONE_MAP.get(normalized_phone)

    def _extract_frequency(self, message: str) -> Optional[str]:
        """Extract frequency from message."""
        for pattern, frequency in self.FREQUENCY_PATTERNS.items():
            if re.search(pattern, message, re.IGNORECASE):
                return frequency
        return None
    
    def _extract_actors(self, message: str) -> Optional[int]:
        """Extract number of actors from message."""
        for pattern in self.NUMBER_PATTERNS:
            match = re.search(pattern, message)
            if match:
                return int(match.group(1))
        
        return None


def parse_user_input(message_text: str, sender_phone: Optional[str] = None) -> Optional[ParsedSignal]:
    """
    Convenience function to parse user input.
    
    Args:
        message_text: Raw WhatsApp message
        sender_phone: Optional sender phone number for zone inference
        
    Returns:
        ParsedSignal if successful, None otherwise
    """
    parser = InputParser()
    return parser.parse(message_text, sender_phone=sender_phone)
