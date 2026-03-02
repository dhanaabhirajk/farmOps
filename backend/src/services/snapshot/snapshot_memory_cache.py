"""In-memory snapshot cache with TTL, keyed by farm params hash.

This is the first layer of the two-tier cache:
  1. In-memory (this module) — sub-millisecond lookup, process-scoped
  2. Supabase DB (snapshot_cache.py) — persistent, survives restarts

Cache key = SHA-256 of (farm_id, lat, lon, district, main_crop, area_acres, date).
This prevents the same farm with different coordinates/crop being served stale data.
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)

# Module-level store: key -> (payload, expires_at_unix)
_STORE: Dict[str, Tuple[Dict[str, Any], float]] = {}

# Default TTL: 4 hours (matches Supabase SnapshotCache default)
_DEFAULT_TTL_SECONDS = 4 * 60 * 60


def _make_key(
    farm_id: UUID,
    lat: float,
    lon: float,
    district: str,
    main_crop: str,
    area_acres: float,
) -> str:
    """Return a stable SHA-256-based cache key for the given parameter set."""
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).date().isoformat()
    raw = json.dumps(
        {
            "farm_id": str(farm_id),
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "district": district.lower().strip(),
            "main_crop": main_crop.lower().strip(),
            "area_acres": round(area_acres, 2),
            "date": today,
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def params_hash(
    farm_id: UUID,
    lat: float,
    lon: float,
    district: str,
    main_crop: str,
    area_acres: float,
) -> str:
    """Public helper: return the hex hash for a parameter set (used by DB cache)."""
    return _make_key(farm_id, lat, lon, district, main_crop, area_acres)


def get(
    farm_id: UUID,
    lat: float,
    lon: float,
    district: str,
    main_crop: str,
    area_acres: float,
) -> Optional[Dict[str, Any]]:
    """Return cached payload or None if missing / expired."""
    key = _make_key(farm_id, lat, lon, district, main_crop, area_acres)
    entry = _STORE.get(key)
    if entry is None:
        logger.debug("Memory cache MISS for key %s", key[:12])
        return None

    payload, expires_at = entry
    if time.monotonic() > expires_at:
        logger.debug("Memory cache EXPIRED for key %s", key[:12])
        del _STORE[key]
        return None

    logger.info("Memory cache HIT for farm %s (key %s…)", farm_id, key[:12])
    return payload


def put(
    farm_id: UUID,
    lat: float,
    lon: float,
    district: str,
    main_crop: str,
    area_acres: float,
    payload: Dict[str, Any],
    ttl_seconds: int = _DEFAULT_TTL_SECONDS,
) -> None:
    """Store payload in in-memory cache with TTL."""
    key = _make_key(farm_id, lat, lon, district, main_crop, area_acres)
    expires_at = time.monotonic() + ttl_seconds
    _STORE[key] = (payload, expires_at)
    logger.info(
        "Memory cache SET for farm %s (key %s… TTL %ds)",
        farm_id,
        key[:12],
        ttl_seconds,
    )


def invalidate(
    farm_id: UUID,
    lat: float,
    lon: float,
    district: str,
    main_crop: str,
    area_acres: float,
) -> None:
    """Evict an entry from the in-memory cache."""
    key = _make_key(farm_id, lat, lon, district, main_crop, area_acres)
    _STORE.pop(key, None)
    logger.info("Memory cache INVALIDATED for key %s…", key[:12])


def clear_all() -> None:
    """Wipe the entire in-memory store (useful in tests)."""
    _STORE.clear()
