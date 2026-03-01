"""Recommendation Cache Service.

Caches crop recommendations to improve response times.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class RecommendationCache:
    """In-memory cache for crop recommendations."""

    def __init__(self, default_ttl_hours: int = 48):
        """
        Initialize cache.
        
        Args:
            default_ttl_hours: Default cache time-to-live in hours
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = timedelta(hours=default_ttl_hours)

    def _make_key(self, farm_id: UUID, season: str) -> str:
        """Generate cache key."""
        return f"recommendations:{farm_id}:{season}"

    def get_cached_recommendation(
        self, farm_id: UUID, season: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached recommendation if fresh.
        
        Args:
            farm_id: Farm UUID
            season: Season name
            
        Returns:
            Cached recommendation or None
        """
        key = self._make_key(farm_id, season)
        cached = self.cache.get(key)
        
        if not cached:
            return None
        
        # Check if expired
        expires_at = cached.get("expires_at")
        if expires_at and datetime.utcnow() > expires_at:
            # Remove expired entry
            del self.cache[key]
            logger.debug(f"Cache expired for {key}")
            return None
        
        logger.info(f"Cache hit for {key}")
        return cached.get("data")

    def cache_recommendation(
        self,
        farm_id: UUID,
        season: str,
        recommendation: Dict[str, Any],
        ttl_hours: Optional[int] = None,
    ) -> None:
        """
        Store recommendation in cache.
        
        Args:
            farm_id: Farm UUID
            season: Season name
            recommendation: Recommendation data
            ttl_hours: Custom TTL (optional)
        """
        key = self._make_key(farm_id, season)
        ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
        expires_at = datetime.utcnow() + ttl
        
        self.cache[key] = {
            "data": recommendation,
            "expires_at": expires_at,
            "cached_at": datetime.utcnow(),
        }
        
        logger.info(f"Cached recommendation for {key}, expires at {expires_at}")

    def invalidate_cache(self, farm_id: UUID, season: Optional[str] = None) -> None:
        """
        Invalidate cache entries.
        
        Args:
            farm_id: Farm UUID
            season: Specific season to invalidate (None = all seasons for farm)
        """
        if season:
             # Invalidate specific season
            key = self._make_key(farm_id, season)
            if key in self.cache:
                del self.cache[key]
                logger.info(f"Invalidated cache for {key}")
        else:
            # Invalidate all seasons for farm
            prefix = f"recommendations:{farm_id}:"
            keys_to_delete = [k for k in self.cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self.cache[key]
            logger.info(f"Invalidated {len(keys_to_delete)} cache entries for farm {farm_id}")

    def is_cache_fresh(self, farm_id: UUID, season: str) -> bool:
        """Check if cached data exists and is fresh."""
        return self.get_cached_recommendation(farm_id, season) is not None

    def clear_all(self) -> None:
        """Clear entire cache."""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared {count} cache entries")
