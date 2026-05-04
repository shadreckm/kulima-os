"""
PII & Granularity Filter Module
Reference: PPSG_SPECIFICATION.md Lines 182-230

This module detects and rejects signals containing PII or overly precise data.
Implements Zero-PII enforcement as specified in PPSG_SPECIFICATION.md.
"""

import re
from typing import Dict, Optional


# PII Detection Patterns (PPSG_SPECIFICATION.md Lines 195-210)
PHONE_PATTERN = re.compile(r'^\+?[0-9]{7,15}$')
GPS_PATTERN = re.compile(r'^-?\d+\.\d+,-?\d+\.\d+$')
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
MAC_PATTERN = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
IMEI_PATTERN = re.compile(r'^\d{15}$')


def detect_pii(signal: Dict[str, str]) -> Optional[str]:
    """
    Detect PII patterns in signal fields.
    
    Reference: PPSG_SPECIFICATION.md Lines 195-210
    
    Args:
        signal: Signal dictionary to check
        
    Returns:
        Error message if PII detected, None otherwise
    """
    for key, value in signal.items():
        if not isinstance(value, str):
            continue
            
        # Phone number detection
        if PHONE_PATTERN.match(value):
            return f"Field '{key}' contains phone number pattern"
        
        # GPS coordinates detection
        if GPS_PATTERN.match(value):
            return f"Field '{key}' contains GPS coordinates"
        
        # UUID detection
        if UUID_PATTERN.match(value):
            return f"Field '{key}' contains UUID pattern"
        
        # MAC address detection
        if MAC_PATTERN.match(value):
            return f"Field '{key}' contains MAC address pattern"
        
        # IMEI detection
        if IMEI_PATTERN.match(value):
            return f"Field '{key}' contains IMEI pattern"
        
        # Long alphabetic strings (potential names)
        if len(value) > 20 and value.replace(' ', '').isalpha():
            return f"Field '{key}' contains potential name or identifier (>20 chars)"
    
    return None


def validate_temporal_coarseness(time_window: str) -> Optional[str]:
    """
    Validate that time_window is coarse (morning/afternoon/evening), not precise.
    
    Reference: PPSG_SPECIFICATION.md Lines 212-214
    
    Args:
        time_window: Time window value to validate
        
    Returns:
        Error message if too precise, None otherwise
    """
    # Check if it looks like a timestamp (contains colons or T separator)
    if ':' in time_window or 'T' in time_window:
        return "time_window must be coarse (morning/afternoon/evening), not precise timestamp"
    
    # Check if it's a number (hour precision)
    if time_window.isdigit():
        return "time_window must be coarse (morning/afternoon/evening), not hour number"
    
    return None


def validate_zone_precision(zone_id: str) -> Optional[str]:
    """
    Validate that zone_id is coarse, not precise location.
    
    Reference: PPSG_SPECIFICATION.md Lines 232-270
    
    Args:
        zone_id: Zone ID to validate
        
    Returns:
        Error message if too precise, None otherwise
    """
    # Check if it looks like GPS coordinates
    if GPS_PATTERN.match(zone_id):
        return "zone_id must be coarse zone identifier, not GPS coordinates"
    
    # Check if it contains suspicious precision indicators
    if any(indicator in zone_id.lower() for indicator in ['lat', 'lon', 'gps', 'coord']):
        return "zone_id must be coarse zone identifier, not location coordinates"
    
    return None

# Made with Bob
