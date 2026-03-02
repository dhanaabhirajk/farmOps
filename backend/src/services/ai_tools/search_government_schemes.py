"""search_government_schemes LLM Tool.

Dynamically searches for Indian government agricultural schemes using the LLM's
trained knowledge, reasoned against the farmer's specific profile. No static
database — the model identifies applicable schemes based on state, crops, area,
and farmer category, then returns structured eligibility details.

Usage example (LLM perspective):
    Tool: search_government_schemes
    Args: {
      "state": "Tamil Nadu",
      "district": "Thanjavur",
      "crops": ["Rice", "Sugarcane"],
      "area_acres": 5.2,
      "has_irrigation": true,
      "farmer_category": "small"
    }
    → Returns list of matching schemes with eligibility criteria and apply links
"""

import json
import logging
from typing import Any

from ..ai.mistral_client import get_mistral_client

logger = logging.getLogger(__name__)

# ─── Tool Definition for LLM function-calling ─────────────────────────────────
TOOL_NAME = "search_government_schemes"

TOOL_DESCRIPTION = """\
Search for Indian central and state government agricultural schemes, subsidies and grant
programs that a farmer may be eligible for based on their farm location, crops grown,
land area, and profile. Returns matching schemes with eligibility criteria, benefit
amount/type, application link, required documents, and filing deadline. ALWAYS call
this tool when asked about government schemes, subsidies, PMKSY, PM-KISAN, TNAU,
micro-irrigation subsidy, crop insurance (PMFBY/RWBCIS), soil health card,
e-NAM registration, or any similar program. Never hallucinate scheme details — use
this tool to get accurate, up-to-date data."""

TOOL_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "state": {
            "type": "string",
            "description": "Indian state name (e.g., 'Tamil Nadu', 'Maharashtra', 'Punjab')",
            "default": "Tamil Nadu",
        },
        "district": {
            "type": "string",
            "description": (
                "District name for state-level filtering "
                "(e.g., 'Thanjavur', 'Coimbatore', 'Madurai')"
            ),
        },
        "crops": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of crops currently grown or planned (e.g., ['Rice', 'Sugarcane'])",
        },
        "area_acres": {
            "type": "number",
            "description": "Total farm area in acres",
            "minimum": 0.1,
        },
        "has_irrigation": {
            "type": "boolean",
            "description": "Whether the farm has irrigation infrastructure",
            "default": False,
        },
        "farmer_category": {
            "type": "string",
            "enum": ["marginal", "small", "medium", "large"],
            "description": (
                "Farmer landholding category: marginal (<1 ha), small (1-2 ha), "
                "medium (2-10 ha), large (>10 ha)"
            ),
            "default": "small",
        },
        "scheme_types": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "subsidy",
                    "insurance",
                    "credit",
                    "price_support",
                    "input_support",
                    "technology",
                    "training",
                    "all",
                ],
            },
            "description": "Types of schemes to search (default: all types)",
            "default": ["all"],
        },
    },
    "required": ["state"],
}


# ─── System prompt for dynamic scheme discovery ───────────────────────────────
_SCHEME_SYSTEM_PROMPT = """\
You are an expert on Indian government agricultural schemes — central (Ministry of Agriculture)
and state-level programs. Given a farmer's profile, identify ALL applicable schemes they are
likely eligible for and return them as a JSON array.

For EACH scheme include:
- id: short unique identifier (e.g., "PM-KISAN", "PMFBY", "KCC")
- name: full official scheme name
- authority: issuing authority (Central Government / State name)
- type: one of [subsidy, insurance, credit, price_support, input_support, technology, training]
- benefit: concise benefit description with ₹ amounts where known (1 sentence)
- description: 2-3 sentence description with ONE key caveat (keep it brief)
- action_plan: ordered list of 4-5 steps the farmer should take (keep each step short)
- eligibility_explanation: why this farmer qualifies (1-2 sentences)
- required_documents: list of documents needed to apply
- apply_link: official portal URL
- application_portal: direct application URL (if different from apply_link)
- deadline: application deadline or "Rolling"
- confidence: integer 0-100 (how confident you are this farmer qualifies)
- tags: list of relevant tags

RULES:
1. Include BOTH central and state-specific schemes applicable to the given state
2. Only include schemes the farmer has a reasonable chance of qualifying for
3. Set confidence < 60 only if eligibility is uncertain; exclude if clearly ineligible
4. Never fabricate scheme names or URLs — use real, verifiable schemes
5. Be specific about benefit amounts using current government figures
6. Warn about common pitfalls (e.g., must apply before sowing, not for govt employees)
7. Return ONLY valid JSON — no markdown, no explanation outside the JSON

Output format:
{
  "schemes": [ { ...scheme object... }, ... ],
  "search_notes": "brief note about what was searched and any caveats"
}
"""

# ─── Legacy static database (kept for reference / offline fallback) ───────────
# fmt: off
# Known scheme IDs for reference / prompt seeding only (no filtering done here)
_FALLBACK_SCHEME_IDS: list[str] = [
    "PM-KISAN", "PMFBY", "PMKSY-PDMC", "SHC", "eNAM",
    "TNAU-SUBSIDY-DRIP", "TN-SEED-SUBSIDY", "TN-CROP-INSURANCE-RWBCIS",
    "TN-HORTICULTURE-SUBSIDY", "PMGDISHA-KISAAN", "KCC",
]



def _acres_to_ha(acres: float) -> float:
    return acres * 0.404686


def _categorize_area(area_acres: float) -> str:
    ha = _acres_to_ha(area_acres)
    if ha < 1.0:
        return "marginal"
    elif ha < 2.0:
        return "small"
    elif ha < 10.0:
        return "medium"
    else:
        return "large"


# ─── Dynamic LLM-powered handler ─────────────────────────────────────────────

async def handler(
    state: str = "Tamil Nadu",
    district: str | None = None,
    crops: list[str] | None = None,
    area_acres: float | None = None,
    has_irrigation: bool = False,
    farmer_category: str = "small",
    scheme_types: list[str] | None = None,
) -> dict[str, Any]:
    """
    Async handler for the search_government_schemes tool.

    Calls the Mistral LLM to dynamically reason about applicable Indian government
    agricultural schemes for the given farmer profile. Returns structured scheme data
    with eligibility explanations and application links.
    """
    if scheme_types is None:
        scheme_types = ["all"]
    crops = crops or []

    # Derive farmer category from area if not explicitly provided
    if area_acres is not None and farmer_category == "small":
        farmer_category = _categorize_area(area_acres)

    logger.info(
        "search_government_schemes called: state=%s district=%s crops=%s "
        "area_acres=%s farmer_category=%s scheme_types=%s",
        state, district, crops, area_acres, farmer_category, scheme_types,
    )

    # ── Build the farmer profile prompt ───────────────────────────────────────
    profile_parts = [
        f"State: {state}",
        f"District: {district}" if district else "District: not specified",
        f"Crops grown: {', '.join(crops)}" if crops else "Crops: not specified",
        f"Farm area: {area_acres:.2f} acres" if area_acres else "Farm area: not specified",
        f"Farmer category: {farmer_category}",
        f"Has irrigation: {'Yes' if has_irrigation else 'No'}",
        f"Scheme types requested: {', '.join(scheme_types)}",
    ]
    farmer_profile = "\n".join(profile_parts)

    type_filter = "" if "all" in scheme_types else (
        f"\nOnly return schemes of these types: {', '.join(scheme_types)}"
    )

    user_message = (
        f"Find all applicable Indian government agricultural schemes for this farmer:\n\n"
        f"{farmer_profile}"
        f"{type_filter}\n\n"
        f"Include both central government and {state} state-specific schemes. "
        f"Known scheme IDs to consider: {', '.join(_FALLBACK_SCHEME_IDS)}.\n"
        f"Also include any other relevant schemes not in that list.\n"
        f"Return the JSON response as specified."
    )

    # ── Call Mistral for dynamic scheme recommendations ────────────────────────
    try:
        client = get_mistral_client()
        response = await client.chat_completion(
            messages=[
                {"role": "system", "content": _SCHEME_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            tools=None,
            temperature=0.1,   # Low temperature for factual, consistent output
            max_tokens=8192,   # Increased — detailed scheme JSON needs more tokens
        )

        raw_content = response.get("content") or ""

        # ── Parse JSON response ────────────────────────────────────────────────
        # Strip any accidental markdown fences
        clean = raw_content.strip()
        if clean.startswith("```"):
            clean = clean.split("```", 2)[1]
            if clean.startswith("json"):
                clean = clean[4:]
            clean = clean.rsplit("```", 1)[0].strip()

        # Attempt parse; if truncated, salvage completed scheme objects
        try:
            parsed = json.loads(clean)
        except json.JSONDecodeError:
            # Find the last complete scheme object and close the JSON array
            last_complete = clean.rfind("},")
            if last_complete == -1:
                last_complete = clean.rfind("}")
            if last_complete != -1:
                salvaged = clean[: last_complete + 1]
                # Wrap into valid structure
                array_start = salvaged.find("[")
                if array_start != -1:
                    salvaged = '{"schemes":' + salvaged[array_start:] + '],"search_notes":"Response truncated — partial results shown."}'
                    try:
                        parsed = json.loads(salvaged)
                        logger.warning("Salvaged partial JSON from truncated LLM response")
                    except json.JSONDecodeError:
                        raise
                else:
                    raise
            else:
                raise
        schemes_raw: list[dict[str, Any]] = parsed.get("schemes", [])
        search_notes: str = parsed.get("search_notes", "")

        # ── Normalise and sort by confidence ──────────────────────────────────
        matched_schemes: list[dict[str, Any]] = []
        for s in schemes_raw:
            confidence = int(s.get("confidence", 70))
            if confidence < 40:
                continue  # Skip very low confidence matches
            matched_schemes.append({
                "scheme_id": s.get("id", "UNKNOWN"),
                "name": s.get("name", ""),
                "authority": s.get("authority", ""),
                "type": s.get("type", "subsidy"),
                "benefit": s.get("benefit", ""),
                "description": s.get("description", ""),
                "action_plan": s.get("action_plan", []),
                "eligibility_explanation": s.get("eligibility_explanation", ""),
                "required_documents": s.get("required_documents", []),
                "apply_link": s.get("apply_link", ""),
                "application_portal": s.get("application_portal", s.get("apply_link", "")),
                "deadline": s.get("deadline", "Check official portal"),
                "confidence": confidence,
                "tags": s.get("tags", []),
            })

        matched_schemes.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "success": True,
            "state": state,
            "district": district,
            "farmer_category": farmer_category,
            "total_matched": len(matched_schemes),
            "schemes": matched_schemes,
            "data_source": "Mistral AI — dynamic scheme reasoning based on farmer profile",
            "data_note": (
                search_notes or
                "Scheme details are based on current government programs. "
                "Always verify requirements with the official portal before applying."
            ),
            "confidence": (
                min(s["confidence"] for s in matched_schemes)
                if matched_schemes else 0
            ),
        }

    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse LLM scheme response as JSON: %s", exc)
        return {
            "success": False,
            "state": state,
            "district": district,
            "farmer_category": farmer_category,
            "total_matched": 0,
            "schemes": [],
            "error": "LLM returned non-JSON response for scheme search",
            "data_source": "search_government_schemes",
            "confidence": 0,
        }
    except Exception as exc:
        logger.error("search_government_schemes handler error: %s", exc, exc_info=True)
        return {
            "success": False,
            "state": state,
            "district": district,
            "farmer_category": farmer_category,
            "total_matched": 0,
            "schemes": [],
            "error": str(exc),
            "data_source": "search_government_schemes",
            "confidence": 0,
        }
