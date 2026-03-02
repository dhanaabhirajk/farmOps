"""LLM Insight Generator.

Uses Mistral AI to generate rich, actionable narrative insights for each
crop recommendation. Adds human-readable explanations that go beyond the
rule-based numeric outputs — covering timing strategy, risk mitigation,
and sell-vs-store advice.

Falls back gracefully if the MISTRAL_API_KEY is not configured.
"""

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """\
You are an expert agricultural advisor for Tamil Nadu, India.
Your job is to write short, practical, farmer-friendly insights for
AI-computed crop recommendations. Always use simple language.
Respond only in the JSON format requested — no extra text.
"""


def _build_crop_prompt(
    crop: Dict[str, Any],
    season: str,
    district: str,
    soil_type: str,
    climate_zone: str,
    rainfall_mm: float,
) -> str:
    name = crop.get("crop_name", "Unknown")
    profit = crop.get("expected_profit_per_acre", 0)
    revenue = crop.get("expected_revenue_per_acre", 0)
    cost = crop.get("expected_cost_per_acre", 0)
    yield_kg = crop.get("expected_yield_kg_acre", 0)
    risk_overall = crop.get("risk_score", {}).get("overall", 0.5)
    drought = crop.get("risk_score", {}).get("drought_risk", 0.5)
    pest = crop.get("risk_score", {}).get("pest_risk", 0.5)
    market_risk = crop.get("risk_score", {}).get("market_risk", 0.5)
    pw = crop.get("planting_window")
    planting_str = (
        f"{pw['start']} to {pw['end']}" if pw else "consult local calendar"
    )
    water_mm = crop.get("water_requirement_mm", "unknown")
    rank = crop.get("rank", 1)

    return f"""\
Generate a JSON insight object for a #{rank} ranked crop recommendation.

Crop: {name}
Season: {season}
District: {district}
Soil type: {soil_type}
Climate zone: {climate_zone}
Annual rainfall: {rainfall_mm} mm

Numbers (already computed — do NOT invent new numbers):
- Expected yield: {yield_kg:,.0f} kg/acre
- Expected revenue: ₹{revenue:,.0f}/acre
- Production cost: ₹{cost:,.0f}/acre
- Expected profit: ₹{profit:,.0f}/acre
- Overall risk score: {risk_overall:.0%}  (drought {drought:.0%}, pest {pest:.0%}, market {market_risk:.0%})
- Planting window: {planting_str}
- Seasonal water need: {water_mm} mm

Return ONLY this JSON (no markdown, no extra keys):
{{
  "why_this_crop": "<2 sentences: why this crop suits the location & season>",
  "key_risks": "<1-2 sentences: main risks and how to mitigate them>",
  "planting_tip": "<1 sentence: best planting practice for this region>",
  "harvest_advice": "<1 sentence: when to harvest and whether to sell immediately or store>",
  "one_liner": "<≤12 words: a punchy summary for the card header>"
}}
"""


def _build_summary_prompt(
    crops: List[Dict[str, Any]],
    season: str,
    district: str,
) -> str:
    crop_list = "\n".join(
        f"  #{c['rank']} {c['crop_name']} — profit ₹{c.get('expected_profit_per_acre', 0):,.0f}/acre, "
        f"risk {c.get('risk_score', {}).get('overall', 0.5):.0%}"
        for c in crops
    )
    return f"""\
Write a concise 3-sentence strategic farm advisory for {season} season in {district}.

Top 3 ranked crops:
{crop_list}

Return ONLY this JSON (no markdown):
{{
  "summary": "<3 sentence strategic advisory: best overall approach, diversification advice, one key risk to watch>",
  "action_items": ["<specific action 1>", "<specific action 2>", "<specific action 3>"]
}}
"""


class LLMInsightGenerator:
    """Generates LLM-powered narrative insights for crop recommendations."""

    def __init__(self) -> None:
        self._client: Optional[Any] = None

    def _get_client(self) -> Optional[Any]:
        """Lazy-init Mistral client; returns None if not configured."""
        if self._client is not None:
            return self._client
        try:
            from ..ai.mistral_client import MistralClient
            self._client = MistralClient()
            return self._client
        except (ValueError, ImportError) as exc:
            logger.warning(f"Mistral client unavailable: {exc}")
            return None

    async def enrich_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        season: str,
        farm_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Add `ai_insight` dict to each recommendation and return an `ai_summary`.

        Args:
            recommendations: List of crop evaluations (rule-based numbers).
            season: Season name.
            farm_data: Full farm snapshot dict with location_profile, soil_profile.

        Returns:
            {
                "recommendations": [...same list with ai_insight injected...],
                "ai_summary": { "summary": "...", "action_items": [...] }
            }
        """
        client = self._get_client()
        if client is None:
            # No API key — attach stub insights so UI still gets placeholders
            for rec in recommendations:
                rec["ai_insight"] = _stub_insight(rec, season)
            return {
                "recommendations": recommendations,
                "ai_summary": {
                    "summary": (
                        f"AI insights require a Mistral API key. "
                        f"Top recommendation for {season} season: "
                        f"{recommendations[0]['crop_name'] if recommendations else 'N/A'}."
                    ),
                    "action_items": [
                        "Configure MISTRAL_API_KEY to unlock AI insights.",
                        "Review numeric estimates above.",
                        "Consult local extension officer.",
                    ],
                },
            }

        location = farm_data.get("location_profile", {})
        soil = farm_data.get("soil_profile", {})
        district = location.get("district", "your region")
        soil_type = soil.get("soil_type", "Loamy")
        climate_zone = location.get("climate_zone", "tropical")
        rainfall_mm = float(location.get("rainfall_annual_avg_mm", 900))

        # Generate per-crop insights concurrently (sequential for simplicity)
        enriched = []
        for rec in recommendations:
            insight = await self._generate_crop_insight(
                client=client,
                crop=rec,
                season=season,
                district=district,
                soil_type=soil_type,
                climate_zone=climate_zone,
                rainfall_mm=rainfall_mm,
            )
            rec_copy = dict(rec)
            rec_copy["ai_insight"] = insight
            enriched.append(rec_copy)

        # Generate overall summary
        ai_summary = await self._generate_summary(
            client=client,
            crops=enriched,
            season=season,
            district=district,
        )

        return {"recommendations": enriched, "ai_summary": ai_summary}

    async def _generate_crop_insight(
        self,
        client: Any,
        crop: Dict[str, Any],
        season: str,
        district: str,
        soil_type: str,
        climate_zone: str,
        rainfall_mm: float,
    ) -> Dict[str, Any]:
        """Call Mistral to generate one crop's insight JSON."""
        try:
            prompt = _build_crop_prompt(crop, season, district, soil_type, climate_zone, rainfall_mm)
            response = await client.chat_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=512,
            )
            content = response.get("content", "")
            return _parse_json_response(content, _stub_insight(crop, season))
        except Exception as exc:
            logger.error(f"LLM crop insight failed for {crop.get('crop_name')}: {exc}")
            return _stub_insight(crop, season)

    async def _generate_summary(
        self,
        client: Any,
        crops: List[Dict[str, Any]],
        season: str,
        district: str,
    ) -> Dict[str, Any]:
        """Call Mistral to generate overall season strategy."""
        stub = {
            "summary": f"Strong prospects for {season} season in {district}.",
            "action_items": [
                f"Plant {crops[0]['crop_name'] if crops else 'top crop'} first.",
                "Monitor soil moisture weekly.",
                "Track mandi prices before harvest.",
            ],
        }
        try:
            prompt = _build_summary_prompt(crops, season, district)
            response = await client.chat_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=400,
            )
            content = response.get("content", "")
            return _parse_json_response(content, stub)
        except Exception as exc:
            logger.error(f"LLM summary failed: {exc}")
            return stub


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _stub_insight(crop: Dict[str, Any], season: str) -> Dict[str, Any]:
    """Fallback insight when LLM is unavailable."""
    name = crop.get("crop_name", "this crop")
    risk = crop.get("risk_score", {}).get("overall", 0.5)
    risk_text = "low" if risk < 0.3 else "moderate" if risk < 0.6 else "high"
    profit = crop.get("expected_profit_per_acre", 0)
    return {
        "why_this_crop": (
            f"{name} is well-suited for the {season} season given local soil "
            f"and climatic conditions."
        ),
        "key_risks": (
            f"Overall risk is {risk_text}. Monitor weather and market prices closely."
        ),
        "planting_tip": "Follow recommended spacing and use certified seeds.",
        "harvest_advice": (
            "Harvest at peak maturity. Compare mandi prices before deciding to sell or store."
        ),
        "one_liner": f"₹{profit:,.0f}/acre profit potential this {season}.",
    }


def _parse_json_response(content: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the first JSON object from LLM content."""
    if not content:
        return fallback
    # Strip markdown code fences if present
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            l for l in lines if not l.strip().startswith("```")
        ).strip()
    try:
        # Find first { ... }
        start = text.index("{")
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start : i + 1])
    except (ValueError, json.JSONDecodeError) as exc:
        logger.warning(f"Failed to parse LLM JSON: {exc}. Raw: {content[:200]}")
    return fallback
