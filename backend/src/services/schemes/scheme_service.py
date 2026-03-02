"""Scheme Service.

Orchestrates LLM-powered government scheme matching for a farm.
Uses the `search_government_schemes` AI tool to discover eligible schemes,
then persists results as `subsidy` recommendations in Supabase.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..ai.llm_agent import LLMAgent
from ..recommendations.recommendation_repository import RecommendationRepository

logger = logging.getLogger(__name__)

# Scheme recommendations are valid for 7 days (schemes don't change daily)
_SCHEME_TTL_HOURS = 7 * 24

_SCHEME_SYSTEM_PROMPT = """\
You are FarmOps, an expert agricultural advisor for Indian farmers. Your task is to
identify all government subsidies, schemes, and grant programs that a farmer may be
eligible for based on their farm profile.

MANDATORY RULES:
1. You MUST call the `search_government_schemes` tool to get scheme data — do NOT
   guess or invent scheme details.
2. After receiving tool results, provide a clear, farmer-friendly summary in the
   farmer's language that explains:
   - Which schemes they qualify for and why
   - What benefit they receive (in INR amounts where applicable)
   - The most important required documents
   - Next actionable step (e.g., "Visit agriculture office with your Aadhaar and Patta")
3. Highlight the top 3 most impactful schemes (highest monetary or risk benefit).
4. Always include a note that eligibility should be verified with official sources.
5. Respond in simple, friendly language — avoid bureaucratic jargon.
"""


class SchemeService:
    """Orchestrates scheme matching via LLM and persists results."""

    def __init__(
        self,
        llm_agent: Optional[LLMAgent] = None,
        recommendation_repo: Optional[RecommendationRepository] = None,
    ) -> None:
        self.agent = llm_agent or LLMAgent()
        self.repo = recommendation_repo or RecommendationRepository()

    async def get_schemes(
        self,
        farm_id: UUID,
        state: str = "Tamil Nadu",
        district: Optional[str] = None,
        crops: Optional[List[str]] = None,
        area_acres: Optional[float] = None,
        farmer_category: str = "small",
        language: str = "en",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Return eligible government schemes for a farm.

        If a valid cached result exists (not expired) and use_cache=True, returns it.
        Otherwise, runs the LLM agent to discover and score eligible schemes, then
        persists and returns the result.

        Args:
            farm_id: Farm UUID
            state: Indian state name
            district: District name for localised filtering
            crops: List of crops grown/planned
            area_acres: Total area in acres
            farmer_category: 'marginal', 'small', 'medium', or 'large'
            language: Response language code ('en', 'ta', 'hi')
            use_cache: Return cached result if valid

        Returns:
            Structured scheme match result with provenance metadata.
        """
        start = datetime.now(timezone.utc)

        # ── Cache lookup ──────────────────────────────────────────────────────
        if use_cache:
            cached = self.repo.get_active_for_farm(
                farm_id=farm_id,
                rec_type="subsidy",
                limit=1,
            )
            if cached:
                row = cached[0]
                logger.info("Returning cached scheme match for farm=%s", farm_id)
                return {
                    "success": True,
                    "cached": True,
                    "cached_at": row.get("created_at"),
                    "expires_at": row.get("expires_at"),
                    "data": row.get("payload", {}),
                    "confidence": row.get("confidence", 0),
                    "sources": row.get("sources", []),
                    "explanation": row.get("explanation", ""),
                    "model_version": row.get("model_version", ""),
                    "tool_calls": row.get("tool_calls", []),
                    "human_review_required": row.get("human_review_required", False),
                }

        # ── Build farm context message for the LLM ────────────────────────────
        lang_instructions = {
            "ta": "Respond in Tamil (தமிழ்) for the explanation field.",
            "hi": "Respond in Hindi (हिंदी) for the explanation field.",
            "en": "Respond in English.",
        }
        lang_note = lang_instructions.get(language, "Respond in English.")

        crops_str = ", ".join(crops) if crops else "not specified"
        user_message = (
            f"Farm profile:\n"
            f"  State: {state}\n"
            f"  District: {district or 'not specified'}\n"
            f"  Crops grown: {crops_str}\n"
            f"  Area: {area_acres or 'not specified'} acres\n"
            f"  Farmer category: {farmer_category}\n"
            f"\n"
            f"Find all government schemes, subsidies, and grant programs this farmer "
            f"is eligible for. Call the search_government_schemes tool with the farm "
            f"profile above, then summarise the top eligible schemes clearly.\n"
            f"{lang_note}"
        )

        # ── Run LLM agent ─────────────────────────────────────────────────────
        try:
            result = await self.agent.run(
                system_prompt=_SCHEME_SYSTEM_PROMPT,
                user_message=user_message,
                tool_names=["search_government_schemes"],
                temperature=0.2,
                max_tokens=3000,
            )
        except Exception as exc:
            logger.error("LLM agent failed for scheme matching: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "cached": False,
            }

        # ── Extract scheme results from tool calls ────────────────────────────
        schemes: List[Dict[str, Any]] = []
        tool_confidence = 70  # default
        sources: List[Dict[str, Any]] = []

        for call in result.tool_calls_made:
            if call.get("tool") == "search_government_schemes":
                output = call.get("output", {})
                if isinstance(output, dict) and output.get("success"):
                    schemes = output.get("schemes", [])
                    tool_confidence = max(
                        (s["confidence"] for s in schemes), default=70
                    )
                    sources.append({
                        "source_name": output.get("data_source", "FarmOps Scheme DB"),
                        "data_age_hours": 0,
                        "confidence_contribution_pct": 100,
                        "note": output.get("data_note", ""),
                    })

        if not sources:
            sources = [{
                "source_name": "FarmOps Scheme Database",
                "data_age_hours": 0,
                "confidence_contribution_pct": 100,
            }]

        # ── Build structured payload ──────────────────────────────────────────
        payload: Dict[str, Any] = {
            "state": state,
            "district": district,
            "crops": crops or [],
            "area_acres": area_acres,
            "farmer_category": farmer_category,
            "schemes": schemes,
            "total_matched": len(schemes),
            "top_scheme_ids": [s["scheme_id"] for s in schemes[:3]],
            "scan_timestamp": start.isoformat(),
        }

        elapsed_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        model_ver = f"mistral-large-latest/scheme-v1"

        # ── Persist to Supabase ───────────────────────────────────────────────
        saved_row = self.repo.save(
            farm_id=farm_id,
            rec_type="subsidy",
            payload=payload,
            confidence=min(100, max(0, tool_confidence)),
            sources=sources,
            explanation=result.final_response[:2000],
            model_version=model_ver,
            tool_calls=result.tool_calls_made,
            ttl_hours=_SCHEME_TTL_HOURS,
        )

        logger.info(
            "Scheme scan complete farm=%s schemes=%d confidence=%d elapsed=%.0fms",
            farm_id, len(schemes), tool_confidence, elapsed_ms,
        )

        return {
            "success": True,
            "cached": False,
            "cached_at": None,
            "expires_at": saved_row.get("expires_at") if saved_row else None,
            "data": payload,
            "confidence": tool_confidence,
            "sources": sources,
            "explanation": result.final_response,
            "model_version": model_ver,
            "tool_calls": result.tool_calls_made,
            "human_review_required": tool_confidence < 40,
            "response_time_ms": round(elapsed_ms, 2),
        }
