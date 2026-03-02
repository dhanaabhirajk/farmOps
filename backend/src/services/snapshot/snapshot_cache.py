"""Snapshot caching service backed by Supabase farm_snapshots table."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from uuid import UUID

logger = logging.getLogger(__name__)


class SnapshotCache:
    """Service for caching farm snapshots in Supabase."""

    def __init__(self, db_session: Optional[Any] = None, ttl_minutes: int = 240):
        """
        Initialize snapshot cache.

        Args:
            db_session: Unused (kept for API compatibility)
            ttl_minutes: Cache TTL in minutes (default 4 hours)
        """
        self.ttl_minutes = ttl_minutes
        logger.info(f"SnapshotCache initialized with TTL {ttl_minutes} minutes")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_client(self):
        """Return a Supabase service-role client (bypasses RLS)."""
        from ...db.supabase_client import get_supabase_service
        return get_supabase_service()

    def _today(self) -> str:
        """Return today's date as an ISO string (YYYY-MM-DD)."""
        return datetime.now(timezone.utc).date().isoformat()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_cached_snapshot(
        self,
        farm_id: UUID,
        params_hash: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Return today's cached snapshot for *farm_id* if it is still within TTL.

        When *params_hash* is provided the cached row is only returned if its
        stored hash matches — this prevents a cached snapshot for one set of
        query params (lat/lon/district/crop) from being served for a different
        parameter combination pointing to the same farm UUID.

        Args:
            farm_id: Farm UUID
            params_hash: Optional SHA-256 hex digest of the request parameters.

        Returns:
            The ``payload`` dict from the cached row, or ``None`` if no fresh
            snapshot exists or the params hash differs.
        """
        try:
            client = self._get_client()
            today = self._today()

            response = (
                client.table("farm_snapshots")
                .select("payload, created_at, cache_ttl_minutes")
                .eq("farm_id", str(farm_id))
                .eq("snapshot_date", today)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            rows = response.data
            if not rows:
                logger.debug(f"No cached snapshot for farm {farm_id} on {today}")
                return None

            row = rows[0]
            stored_payload = row.get("payload") or {}

            # ── Params-hash guard ─────────────────────────────────────────────
            # The payload is stored wrapped as {"_params_hash": "...", "snapshot": {...}}.
            # For backwards-compat we also accept un-wrapped payloads (no hash check).
            if isinstance(stored_payload, dict) and "_params_hash" in stored_payload:
                stored_hash = stored_payload["_params_hash"]
                actual_payload = stored_payload.get("snapshot", stored_payload)
                if params_hash and stored_hash != params_hash:
                    logger.info(
                        f"Cache PARAMS MISMATCH for farm {farm_id} "
                        f"(stored={stored_hash[:12]}… requested={params_hash[:12]}…)"
                    )
                    return None
            else:
                # Legacy un-wrapped payload — skip hash check
                actual_payload = stored_payload

            # Check TTL — created_at + ttl_minutes must still be in the future
            created_at_str = row.get("created_at", "")
            ttl = row.get("cache_ttl_minutes", self.ttl_minutes)
            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str)
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                age_minutes = (datetime.now(timezone.utc) - created_at).total_seconds() / 60
                if age_minutes > ttl:
                    logger.info(
                        f"Cached snapshot for farm {farm_id} is stale "
                        f"({age_minutes:.0f} min old, TTL {ttl} min)"
                    )
                    return None

            logger.info(f"Cache HIT for farm {farm_id} (today={today})")
            return actual_payload

        except Exception as e:
            logger.error(f"Error retrieving cached snapshot for farm {farm_id}: {e}")
            return None

    def cache_snapshot(
        self,
        farm_id: UUID,
        snapshot_data: Dict[str, Any],
        confidence_overall: int = 0,
        sources_used: Optional[List[str]] = None,
        params_hash: Optional[str] = None,
    ) -> bool:
        """
        Upsert a farm snapshot into the ``farm_snapshots`` table.

        Uses ``(farm_id, snapshot_date)`` as the conflict target so only one
        snapshot per day is kept; re-running the pipeline today overwrites the
        previous entry.

        The payload is stored wrapped as::

            {"_params_hash": "<hex>", "snapshot": {... actual data ...}}

        so that ``get_cached_snapshot`` can detect when a different set of
        query parameters (lat/lon/district/crop) made the request.

        Args:
            farm_id: Farm UUID
            snapshot_data: Full payload dict to store as JSONB
            confidence_overall: Overall confidence score (0-100)
            sources_used: List of data-source strings
            params_hash: Optional SHA-256 hex digest of the request parameters.

        Returns:
            True if the upsert succeeded, False otherwise.
        """
        try:
            client = self._get_client()
            today = self._today()

            # Wrap payload with params hash so we can detect stale-param hits
            wrapped_payload: Dict[str, Any] = {
                "_params_hash": params_hash or "",
                "snapshot": snapshot_data,
            }

            record = {
                "farm_id": str(farm_id),
                "snapshot_date": today,
                "payload": wrapped_payload,
                "confidence_overall": max(0, min(100, confidence_overall)),
                "sources_used": sources_used or [],
                "cache_ttl_minutes": self.ttl_minutes,
            }

            client.table("farm_snapshots").upsert(
                record,
                on_conflict="farm_id,snapshot_date",
            ).execute()

            logger.info(f"Snapshot cached for farm {farm_id} (date={today}, hash={params_hash and params_hash[:12]}…)")
            return True

        except Exception as e:
            logger.error(f"Error caching snapshot for farm {farm_id}: {e}")
            return False

    def invalidate_cache(self, farm_id: UUID) -> bool:
        """
        Delete today's cached snapshot for *farm_id*.

        Args:
            farm_id: Farm UUID

        Returns:
            True if the deletion succeeded.
        """
        try:
            client = self._get_client()
            today = self._today()

            client.table("farm_snapshots").delete().eq(
                "farm_id", str(farm_id)
            ).eq("snapshot_date", today).execute()

            logger.info(f"Cache invalidated for farm {farm_id} (date={today})")
            return True

        except Exception as e:
            logger.error(f"Error invalidating cache for farm {farm_id}: {e}")
            return False

    def is_cache_fresh(
        self, farm_id: UUID, params_hash: Optional[str] = None
    ) -> bool:
        """
        Return True if a fresh cached snapshot exists for *farm_id* today.

        Args:
            farm_id: Farm UUID
            params_hash: Optional parameter hash to validate against stored entry.
        """
        try:
            return self.get_cached_snapshot(farm_id, params_hash=params_hash) is not None
        except Exception as e:
            logger.error(f"Error checking cache freshness: {e}")
            return False
