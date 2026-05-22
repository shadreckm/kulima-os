"""
Signal normalization utility for converting text input to structured signals
"""
from typing import Dict, Optional
import re

class SignalNormalizer:
    """
    Normalizes natural language text input into structured signal format.
    
    Maps common Malawian farming and trading terms to standardized activity types.
    """
    
    # Activity type mappings with comprehensive synonym support
    ACTIVITY_MAPPINGS = {
        # Irrigation-related terms
        'watering': 'irrigation',
        'watering crops': 'irrigation',
        'irrigating': 'irrigation',
        'pumping water': 'irrigation',
        'water pump': 'irrigation',
        'pumping': 'irrigation',
        'pump': 'irrigation',
        'watering my crops': 'irrigation',
        'irrigation': 'irrigation',
        'watering the garden': 'irrigation',
        'watering farm': 'irrigation',
        'using water pump': 'irrigation',
        
        # Milling-related terms
        'milling': 'milling',
        'grinding': 'milling',
        'grinding maize': 'milling',
        'milling maize': 'milling',
        'processing': 'milling',
        'processing maize': 'milling',
        'mill': 'milling',
        'grind': 'milling',
        'grinding corn': 'milling',
        'milling corn': 'milling',
        'maize mill': 'milling',
        'grinding my maize': 'milling',
        'milling my maize': 'milling',
        'going to mill': 'milling',
        'going to grind': 'milling',
        
        # Cold storage-related terms
        'cold storage': 'cold storage',
        'refrigeration': 'cold storage',
        'storing': 'cold storage',
        'keeping cold': 'cold storage',
        'cold room': 'cold storage',
        'refrigerator': 'cold storage',
        'fridge': 'cold storage',
        'cooling': 'cold storage',
        'keeping produce cold': 'cold storage',
        'storing vegetables': 'cold storage',
        'cold storage room': 'cold storage',
        
        # Welding-related terms
        'welding': 'welding',
        'metal work': 'welding',
        'fabrication': 'welding',
        'weld': 'welding',
        'metalworking': 'welding',
        'fabricating': 'welding',
        'metal fabrication': 'welding',
        'welding metal': 'welding',
        
        # Trading-related terms
        'selling': 'trading',
        'trading': 'trading',
        'selling crops': 'trading',
        'market': 'trading',
        'selling produce': 'trading',
        'selling goods': 'trading',
        'selling at market': 'trading',
        'going to market': 'trading',
        'selling my crops': 'trading',
        'selling my produce': 'trading',
        'trade': 'trading',
        'trading goods': 'trading',
    }
    
    # Time window mappings
    TIME_WINDOW_MAPPINGS = {
        'morning': 'morning',
        'am': 'morning',
        'early': 'morning',
        'before noon': 'morning',
        
        'afternoon': 'afternoon',
        'pm': 'afternoon',
        'midday': 'afternoon',
        'after noon': 'afternoon',
        
        'evening': 'evening',
        'night': 'evening',
        'late': 'evening',
    }
    
    # Zone mappings (case-insensitive)
    ZONE_MAPPINGS = {
        'mzuzu': 'MZUZU',
        'lilongwe': 'LILONGWE',
        'blantyre': 'BLANTYRE',
        'zomba': 'ZOMBA',
    }
    
    def normalize_text(self, text: str) -> Dict:
        """
        Normalize natural language text into structured signal.
        
        Args:
            text: Natural language input (e.g., "watering crops in Mzuzu this morning")
            
        Returns:
            Structured signal dictionary with activity_type, zone, time_window
        """
        text_lower = text.lower()
        
        # Extract activity type
        activity_type = self._extract_activity_type(text_lower)
        
        # Extract zone
        zone = self._extract_zone(text_lower)
        
        # Extract time window
        time_window = self._extract_time_window(text_lower)
        
        return {
            'activity_type': activity_type,
            'zone': zone,
            'time_window': time_window,
            'original_text': text
        }
    
    def _extract_activity_type(self, text: str) -> str:
        """Extract activity type from text using keyword matching."""
        for keyword, activity in self.ACTIVITY_MAPPINGS.items():
            if keyword in text:
                return activity
        return 'unknown'
    
    def _extract_zone(self, text: str) -> str:
        """Extract zone from text using keyword matching."""
        for keyword, zone in self.ZONE_MAPPINGS.items():
            if keyword in text:
                return zone
        return 'UNKNOWN'
    
    def _extract_time_window(self, text: str) -> str:
        """Extract time window from text using keyword matching."""
        for keyword, window in self.TIME_WINDOW_MAPPINGS.items():
            if keyword in text:
                return window
        return 'unknown'
    
    def normalize_structured(self, data: Dict) -> Dict:
        """
        Normalize structured input (e.g., from frontend form) to standard format.
        
        Args:
            data: Dictionary with activity_type, zone, time_window fields
            
        Returns:
            Normalized signal dictionary
        """
        activity_type = data.get('activity_type', '').lower()
        zone = data.get('zone', '').upper()
        time_window = data.get('time_window', '').lower()
        
        # Map activity type if it's a natural language term
        if activity_type in self.ACTIVITY_MAPPINGS:
            activity_type = self.ACTIVITY_MAPPINGS[activity_type]
        
        # Normalize zone
        if zone in self.ZONE_MAPPINGS:
            zone = self.ZONE_MAPPINGS[zone]
        
        # Normalize time window
        if time_window in self.TIME_WINDOW_MAPPINGS:
            time_window = self.TIME_WINDOW_MAPPINGS[time_window]
        
        return {
            'activity_type': activity_type,
            'zone': zone,
            'time_window': time_window
        }


# Singleton instance
normalizer = SignalNormalizer()

def normalize_signal_text(text: str) -> Dict:
    """Convenience function to normalize text input."""
    return normalizer.normalize_text(text)

def normalize_signal_data(data: Dict) -> Dict:
    """Convenience function to normalize structured data."""
    return normalizer.normalize_structured(data)
