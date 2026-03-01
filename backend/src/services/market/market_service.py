"""Market price service with caching."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from .agmarknet_client import AGMARKNETClient

logger = logging.getLogger(__name__)


class PriceCache(ABC):
    """Abstract base class for price caching backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl_minutes: int = 60) -> None:
        """Set cached value with TTL."""
        pass


class InMemoryPriceCache(PriceCache):
    """Simple in-memory cache for prices."""

    def __init__(self):
        """Initialize in-memory cache."""
        self.cache: Dict[str, tuple[Any, datetime]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self.cache:
            value, expiry = self.cache[key]
            if datetime.now() < expiry:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl_minutes: int = 60) -> None:
        """Set cached value with TTL."""
        expiry = datetime.now() + timedelta(minutes=ttl_minutes)
        self.cache[key] = (value, expiry)


class MarketService:
    """Service for market price data with caching."""

    def __init__(
        self,
        agmarknet_client: Optional[AGMARKNETClient] = None,
        cache: Optional[PriceCache] = None,
        cache_ttl_minutes: int = 60,
    ):
        """
        Initialize market service.
        
        Args:
            agmarknet_client: AGMARKNET client
            cache: Price cache backend
            cache_ttl_minutes: Cache TTL in minutes
        """
        self.agmarknet_client = agmarknet_client or AGMARKNETClient()
        self.cache = cache or InMemoryPriceCache()
        self.cache_ttl_minutes = cache_ttl_minutes
        logger.info("Market service initialized with caching")

    def get_price(
        self,
        market_id: int,
        commodity: str,
        use_cache: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Get current price for a commodity in a mandi.
        
        Args:
            market_id: AGMARKNET market ID
            commodity: Commodity name
            use_cache: Whether to use cache
            
        Returns:
            Price data with source and age metadata
        """
        cache_key = f"price:{market_id}:{commodity}"

        # Try cache first
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {cache_key}")
                return cached

        # Fetch from AGMARKNET
        try:
            price = self.agmarknet_client.get_price_for_commodity(market_id, commodity)
            
            if price:
                price["fetched_at"] = datetime.now().isoformat()
                price["source"] = "AGMARKNET"
                
                # Cache the result
                self.cache.set(cache_key, price, self.cache_ttl_minutes)
                logger.info(f"Fetched and cached price for {commodity} in market {market_id}")
                
                return price

            return None

        except Exception as e:
            logger.error(f"Error fetching price: {e}")
            return None

    def get_prices_for_commodity(
        self,
        commodity: str,
        market_ids: List[int],
    ) -> List[Dict[str, Any]]:
        """
        Get prices for a commodity across multiple mandis.
        
        Args:
            commodity: Commodity name
            market_ids: List of market IDs
            
        Returns:
            List of prices from different markets
        """
        prices = []
        
        for market_id in market_ids:
            price = self.get_price(market_id, commodity)
            if price:
                prices.append(price)

        logger.info(f"Fetched prices for {commodity} from {len(prices)} mandis")
        return prices

    def get_price_trend(
        self,
        market_id: int,
        commodity: str,
        days: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """
        Get price trend for a commodity.
        
        Args:
            market_id: AGMARKNET market ID
            commodity: Commodity name
            days: Number of days of history
            
        Returns:
            Price trend analysis
        """
        try:
            history = self.agmarknet_client.get_price_history(market_id, commodity, days)
            
            if not history:
                return None

            # Calculate trend stats
            prices = [h["modal_price_per_quintal"] for h in history]
            current = prices[-1] if prices else 0
            average = sum(prices) / len(prices) if prices else 0

            trend = "increasing" if current > average else "decreasing"

            return {
                "market_id": market_id,
                "commodity": commodity,
                "current_price": current,
                "average_price": average,
                "trend": trend,
                "days": len(history),
                "price_change_pct": ((current - average) / average * 100) if average > 0 else 0,
            }

        except Exception as e:
            logger.error(f"Error calculating price trend: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear all cached prices."""
        self.cache.cache.clear()
        logger.info("Price cache cleared")
