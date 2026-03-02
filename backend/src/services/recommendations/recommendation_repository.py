"""Recommendation Repository.

Handles Supabase CRUD operations for persisting and retrieving recommendations.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from ...db.supabase_client import get_supabase, get_supabase_service

logger = logging.getLogger(__name__)

# How long a crop recommendation stays active before expiry
_CROP_TTL_HOURS = 48
_REVIEW_CONFIDENCE_THRESHOLD = 40  # Below this → human_review_required = True


def _client():
    """Return service client when available, anon client otherwise."""
    try:
        return get_supabase_service()
    except ValueError:
        logger.debug("Service role key not set; using anon Supabase client")
        try:
            return get_supabase()
        except ValueError as exc:
            raise RuntimeError(
                "Supabase client not configured: SUPABASE_URL and SUPABASE_KEY "
                "must be set in environment variables."
            ) from exc


class RecommendationRepository:
    """Persist and retrieve recommendations from Supabase."""

    # ---------------------------------------------------------------------------
    # Write
    # ---------------------------------------------------------------------------

    def save(
        self,
        farm_id: UUID,
        rec_type: str,
        payload: Dict[str, Any],
        confidence: int,
        sources: List[Dict[str, Any]],
        explanation: str,
        model_version: str = "rule-based-v1",
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        ttl_hours: int = _CROP_TTL_HOURS,
    ) -> Optional[Dict[str, Any]]:
        """
        Persist a new recommendation and mark previous ones for the same
        (farm_id, type) as 'superseded'.

        Returns the inserted row or None on error.
        """
        try:
            client = _client()

            # Mark existing active recommendations as superseded
            client.table("recommendations").update({"status": "superseded"}).eq(
                "farm_id", str(farm_id)
            ).eq("type", rec_type).eq("status", "active").execute()

            expires_at = (
                datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
            ).isoformat()

            human_review = confidence < _REVIEW_CONFIDENCE_THRESHOLD

            row = {
                "farm_id": str(farm_id),
                "type": rec_type,
                "payload": payload,
                "confidence": max(0, min(100, confidence)),
                "sources": sources,
                "explanation": explanation[:2000],
                "model_version": model_version,
                "tool_calls": tool_calls or [],
                "status": "active",
                "human_review_required": human_review,
                "expires_at": expires_at,
            }

            result = client.table("recommendations").insert(row).execute()

            if result.data:
                logger.info(
                    f"Saved recommendation farm={farm_id} type={rec_type} "
                    f"id={result.data[0].get('id')}"
                )
                return result.data[0]

            logger.error(f"Insert returned no data: {result}")
            return None

        except Exception as exc:
            logger.error(f"Failed to save recommendation: {exc}")
            return None

    # ---------------------------------------------------------------------------
    # Read
    # ---------------------------------------------------------------------------

    def get_active_for_farm(
        self,
        farm_id: UUID,
        rec_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Fetch active (non-expired) recommendations for a farm.

        Args:
            farm_id: Farm UUID
            rec_type: Optional filter ('crop', 'irrigation', 'harvest', …)
            limit: Max rows to return

        Returns:
            List of recommendation rows ordered by created_at DESC.
        """
        try:
            client = _client()

            query = (
                client.table("recommendations")
                .select("*")
                .eq("farm_id", str(farm_id))
                .eq("status", "active")
                .order("created_at", desc=True)
                .limit(limit)
            )

            if rec_type:
                query = query.eq("type", rec_type)

            result = query.execute()
            rows = result.data or []

            # Filter out rows whose expires_at has passed (belt-and-suspenders)
            now = datetime.now(timezone.utc)
            active = []
            for row in rows:
                expires_raw = row.get("expires_at")
                if expires_raw:
                    # Supabase returns ISO strings
                    expires_dt = datetime.fromisoformat(
                        expires_raw.replace("Z", "+00:00")
                    )
                    if expires_dt < now:
                        continue
                active.append(row)

            return active

        except Exception as exc:
            logger.error(f"Failed to fetch recommendations: {exc}")
            return []

    def get_history(
        self,
        farm_id: UUID,
        rec_type: Optional[str] = None,
        season: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all recommendations (all statuses) for a farm, newest first.

        Args:
            farm_id: Farm UUID
            rec_type: Optional type filter
            season: Optional season filter (matched inside payload->season)
            limit: Max rows

        Returns:
            List of rows.
        """
        try:
            client = _client()

            query = (
                client.table("recommendations")
                .select("*")
                .eq("farm_id", str(farm_id))
                .order("created_at", desc=True)
                .limit(limit)
            )

            if rec_type:
                query = query.eq("type", rec_type)

            result = query.execute()
            rows = result.data or []

            # Season filter — compare against payload.season (client-side for MVP)
            if season and rows:
                rows = [
                    r for r in rows
                    if r.get("payload", {}).get("season", "").lower()
                    == season.lower()
                ]

            return rows

        except Exception as exc:
            logger.error(f"Failed to fetch recommendation history: {exc}")
            return []

    def archive(self, recommendation_id: UUID) -> bool:
        """Set a recommendation status to 'archived'."""
        try:
            client = _client()
            client.table("recommendations").update({"status": "archived"}).eq(
                "id", str(recommendation_id)
            ).execute()
            return True
        except Exception as exc:
            logger.error(f"Failed to archive recommendation {recommendation_id}: {exc}")
            return False
