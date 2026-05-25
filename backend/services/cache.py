"""
In-memory caching service
Simple cache with TTL-based expiration (no Redis required)
"""
import time
import logging
from typing import Any, Optional, Dict
from backend.config import settings

logger = logging.getLogger(__name__)


class SimpleCache:
    """
    Simple in-memory cache with TTL-based expiration.
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if exists and not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if time.time() > entry['expires_at']:
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        logger.debug(f"Cache hit for key: {key}")
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 300)
        """
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        logger.debug(f"Cache set for key: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted for key: {key}")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared ({count} entries)")
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "summary:*")
            
        Returns:
            Number of keys invalidated
        """
        to_delete = []
        for key in self._cache.keys():
            if pattern in key:
                to_delete.append(key)
        
        for key in to_delete:
            del self._cache[key]
        
        logger.info(f"Invalidated {len(to_delete)} keys matching pattern: {pattern}")
        return len(to_delete)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            'size': len(self._cache),
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total
        }
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        now = time.time()
        to_delete = []
        
        for key, entry in self._cache.items():
            if now > entry['expires_at']:
                to_delete.append(key)
        
        for key in to_delete:
            del self._cache[key]
        
        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} expired cache entries")
        
        return len(to_delete)


# Global cache instance
cache = SimpleCache()


def get_cached_summary(zone: str) -> Optional[Dict]:
    """
    Get cached summary for a zone.
    
    Args:
        zone: Zone identifier
        
    Returns:
        Cached summary or None
    """
    key = f"summary:{zone.upper()}"
    return cache.get(key)


def set_cached_summary(zone: str, summary: Dict) -> None:
    """
    Cache summary for a zone.
    
    Args:
        zone: Zone identifier
        summary: Summary data to cache
    """
    key = f"summary:{zone.upper()}"
    cache.set(key, summary, ttl=settings.CACHE_TTL_SUMMARY)


def invalidate_summary(zone: str) -> None:
    """
    Invalidate cached summary for a zone.
    
    Args:
        zone: Zone identifier
    """
    key = f"summary:{zone.upper()}"
    cache.delete(key)


def get_cached_patterns(zone: str) -> Optional[Dict]:
    """
    Get cached patterns for a zone.
    
    Args:
        zone: Zone identifier
        
    Returns:
        Cached patterns or None
    """
    key = f"patterns:{zone.upper()}"
    return cache.get(key)


def set_cached_patterns(zone: str, patterns: Dict) -> None:
    """
    Cache patterns for a zone.
    
    Args:
        zone: Zone identifier
        patterns: Pattern data to cache
    """
    key = f"patterns:{zone.upper()}"
    cache.set(key, patterns, ttl=settings.CACHE_TTL_PATTERNS)


def invalidate_patterns(zone: str) -> None:
    """
    Invalidate cached patterns for a zone.
    
    Args:
        zone: Zone identifier
    """
    key = f"patterns:{zone.upper()}"
    cache.delete(key)


def invalidate_zone(zone: str) -> None:
    """
    Invalidate all cache entries for a zone.
    
    Args:
        zone: Zone identifier
    """
    zone_upper = zone.upper()
    cache.invalidate_pattern(f"summary:{zone_upper}")
    cache.invalidate_pattern(f"patterns:{zone_upper}")
    logger.info(f"Invalidated all cache entries for zone: {zone_upper}")
