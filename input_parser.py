"""
Natural Language Input Parser for LUMOZA WhatsApp Interface

Converts user messages into structured coordination signals.
Designed for fast, lightweight parsing without heavy NLP dependencies.
Forgiving of spelling, incomplete sentences, and informal community language.
"""

import re
import difflib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from zone_utils import DEFAULT_ZONE, normalize_zone, zone_from_phone

UNKNOWN_PRODUCTIVE_ACTIVITY = "unknown_productive_activity"
FUZZY_MATCH_THRESHOLD = 0.72


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
    Always returns a signal for non-empty input; uses best-effort classification.
    """
    
    # (pattern, activity, priority) — highest priority wins; one activity per message
    ACTIVITY_PATTERNS: List[Tuple[str, str, int]] = [
        (r'cold\s+storage', 'storage', 100),
        (r'keep(?:ing)?\s+cool', 'storage', 95),
        (r'busy.*mill', 'milling', 90),
        (r'at\s+(?:the\s+)?mill', 'milling', 88),
        (r'hama\s*mill', 'milling', 85),
        (r'water\s+crops', 'irrigation', 85),
        (r'watering\s+crops', 'irrigation', 85),
        (r'watering', 'irrigation', 70),
        (r'water\s+the\s+', 'irrigation', 70),
        (r'pump(?:ing)?', 'irrigation', 65),
        (r'irrigat(?:e|ing|ion)', 'irrigation', 80),
        (r'irrigat', 'irrigation', 75),
        (r'irrig', 'irrigation', 60),
        (r'mill(?:ing)?', 'milling', 55),
        (r'\bmill\b', 'milling', 50),
        (r'grind(?:ing)?', 'milling', 55),
        (r'sell(?:ing)?', 'trading', 70),
        (r'sold', 'trading', 65),
        (r'maize', 'trading', 40),
        (r'market(?:ing)?', 'trading', 60),
        (r'trade(?:ing|rs)?', 'trading', 65),
        (r'trading', 'trading', 60),
        (r'storage', 'storage', 50),
        (r'store(?:d|age|s)?', 'storage', 45),
        (r'weld(?:ing)?', 'welding', 70),
        (r'clinic', 'clinic', 80),
        (r'health', 'clinic', 50),
        (r'school', 'school', 80),
        (r'education', 'school', 50),
        (r'crop', 'irrigation', 35),
    ]

    # Root tokens for substring and fuzzy matching (longer roots first)
    ACTIVITY_ROOTS = [
        ('irrigat', 'irrigation'),
        ('irrig', 'irrigation'),
        ('watering', 'irrigation'),
        ('water', 'irrigation'),
        ('milling', 'milling'),
        ('mill', 'milling'),
        ('grind', 'milling'),
        ('selling', 'trading'),
        ('sell', 'trading'),
        ('market', 'trading'),
        ('maize', 'trading'),
        ('storage', 'storage'),
        ('storag', 'storage'),
        ('store', 'storage'),
        ('welding', 'welding'),
        ('weld', 'welding'),
        ('clinic', 'clinic'),
        ('school', 'school'),
    ]
    
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
        r'\bbusy\b': 'weekly',
    }
    
    NUMBER_PATTERNS = [
        r'(\d+)\s+(?:farmers|traders|people|actors|users|participants)',
        r'(\d+)\s+(?:farmers|traders|people)',
    ]
    
    def parse(self, message: str, sender_phone: Optional[str] = None) -> Optional[ParsedSignal]:
        """
        Parse a user message into a structured signal.
        Returns None only for completely meaningless input (empty / no letters).
        """
        if self._is_meaningless(message):
            return None
        
        message_normalized = message.strip().lower()
        collapsed = self._collapse_doubled_letters(message_normalized)
        
        activity_type, confidence = self._extract_activity_type(message_normalized, collapsed)
        
        zone = zone_from_phone(sender_phone)
        if not zone:
            zone = DEFAULT_ZONE
        zone = normalize_zone(zone)
        
        frequency = self._extract_frequency(message_normalized) or "unknown"
        
        actors = self._extract_actors(message_normalized)
        if actors is None:
            actors = 1
        
        return ParsedSignal(
            activity_type=activity_type,
            zone=zone,
            frequency=frequency,
            actors=actors,
            raw_message=message_normalized,
            confidence=confidence,
        )
    
    def _is_meaningless(self, message: str) -> bool:
        """True when there is nothing to interpret (empty or no word characters)."""
        if not message or not message.strip():
            return True
        return not re.search(r'[a-zA-Z0-9]', message)
    
    def _collapse_doubled_letters(self, text: str) -> str:
        """Collapse repeated letters to tolerate typos like irringating -> irigating."""
        return re.sub(r'(.)\1+', r'\1', text)
    
    def _extract_activity_type(self, message: str, collapsed: str) -> tuple[str, float]:
        """One activity per message — highest-priority match only."""
        best_activity = None
        best_priority = -1

        for pattern, activity_type, priority in self.ACTIVITY_PATTERNS:
            if re.search(pattern, message) or re.search(pattern, collapsed):
                if priority > best_priority:
                    best_activity = activity_type
                    best_priority = priority

        if best_activity:
            confidence = min(0.9, 0.7 + best_priority / 500)
            return best_activity, confidence

        best_root = None
        best_root_len = 0
        for root, activity_type in self.ACTIVITY_ROOTS:
            if root in message or root in collapsed:
                if len(root) > best_root_len:
                    best_root = activity_type
                    best_root_len = len(root)
        if best_root:
            return best_root, 0.75

        fuzzy = self._fuzzy_root_match(message) or self._fuzzy_root_match(collapsed)
        if fuzzy:
            return fuzzy, 0.65

        return UNKNOWN_PRODUCTIVE_ACTIVITY, 0.45
    
    def _fuzzy_root_match(self, text: str) -> Optional[str]:
        """Match message words to activity roots using fuzzy string similarity."""
        words = re.findall(r'[a-z]{3,}', text)
        roots = [root for root, _ in self.ACTIVITY_ROOTS]
        for word in words:
            matches = difflib.get_close_matches(
                word, roots, n=1, cutoff=FUZZY_MATCH_THRESHOLD
            )
            if matches:
                matched_root = matches[0]
                for root, activity_type in self.ACTIVITY_ROOTS:
                    if root == matched_root:
                        return activity_type
        return None
    
    def _extract_frequency(self, message: str) -> Optional[str]:
        """Extract frequency from message."""
        for pattern, frequency in self.FREQUENCY_PATTERNS.items():
            if re.search(pattern, message, re.IGNORECASE):
                return frequency
        return None
    
    def _extract_actors(self, message: str) -> Optional[int]:
        """Extract number of actors from message."""
        if re.search(r'\bwe\b', message):
            return 2
        for pattern in self.NUMBER_PATTERNS:
            match = re.search(pattern, message)
            if match:
                return int(match.group(1))
        return None


def parse_user_input(message_text: str, sender_phone: Optional[str] = None) -> Optional[ParsedSignal]:
    """
    Parse user input into a coordination signal.
    Returns None only for completely meaningless messages.
    """
    parser = InputParser()
    return parser.parse(message_text, sender_phone=sender_phone)
