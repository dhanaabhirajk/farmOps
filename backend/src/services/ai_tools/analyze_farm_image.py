"""analyze_farm_image - Farm Diagram to Digital Farm Land Tool.

Converts a farm sketch/photograph/satellite image to:
1. A GeoJSON polygon boundary
2. Area estimate
3. Detected features (water bodies, roads, trees, structures)
4. Soil color analysis (rough indicator of soil type)

Uses Mistral's Pixtral vision model for the analysis.

This is the "farm land diagram to digital farm land" feature the user requested.
The LLM analyzes the uploaded image and returns structured JSON with polygon
coordinates or relative boundary descriptions.
"""

import base64
import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

TOOL_NAME = "analyze_farm_image"

TOOL_DESCRIPTION = """\
Analyze a farm image (photograph, hand-drawn sketch, or satellite screenshot) 
and extract farm boundary coordinates, area estimate, visible features (water 
bodies, trees, roads, buildings), and soil color hints. Use this tool when a 
farmer uploads or draws their farm boundary. Returns a GeoJSON polygon and 
detected landscape features."""

TOOL_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "image_base64": {
            "type": "string",
            "description": "Base64-encoded image data (JPEG or PNG)",
        },
        "image_mime": {
            "type": "string",
            "description": "MIME type: 'image/jpeg' or 'image/png'",
            "default": "image/jpeg",
        },
        "reference_lat": {
            "type": "number",
            "description": "Reference latitude to anchor the polygon (optional)",
        },
        "reference_lon": {
            "type": "number",
            "description": "Reference longitude to anchor the polygon (optional)",
        },
        "area_hint_acres": {
            "type": "number",
            "description": "Approximate known area in acres (optional, helps calibrate)",
        },
    },
    "required": ["image_base64"],
}


# System prompt for the vision model
VISION_SYSTEM_PROMPT = """\
You are an expert agricultural field analyst with deep knowledge of Indian farming.
You analyze images of farm land to help farmers digitize their fields.

When given a farm image (aerial/satellite/hand-drawn/photo), you will:
1. Identify and describe the farm boundary
2. Estimate the area if scale information is visible
3. Detect visible features: water bodies, irrigation channels, roads, trees, buildings, crop rows
4. Analyze soil/land color for soil type hints (dark = fertile, red = laterite, light = sandy)
5. If GPS coordinates are provided, generate approximate GeoJSON polygon coordinates
6. If no GPS provided, describe boundary as relative compass directions and distances

ALWAYS respond in this EXACT JSON format (no markdown, pure JSON):
{
  "boundary_type": "approximate|sketch|satellite|photo",
  "area_estimate_acres": <number or null>,
  "shape_description": "<brief boundary shape description>",
  "features_detected": {
    "water_bodies": ["<description>"],
    "roads": ["<description>"],
    "trees_orchards": ["<description>"],
    "buildings": ["<description>"],
    "crop_rows": "<crop type if visible or null>",
    "irrigation_channels": ["<description>"]
  },
  "soil_color_analysis": {
    "dominant_color": "<dark brown|red|light brown|grey|black|mixed>",
    "soil_type_hint": "<clay|loam|sandy|laterite|black cotton|unknown>",
    "fertility_indicator": "<high|medium|low|unknown>"
  },
  "geojson_polygon": {
    "type": "Polygon",
    "coordinates": [[[lon1,lat1],[lon2,lat2],[lon3,lat3],[lon4,lat4],[lon1,lat1]]]
  },
  "confidence": <0.0 to 1.0>,
  "notes": "<any important observations about the farm>",
  "recommended_actions": ["<actionable suggestion 1>", "<actionable suggestion 2>"]
}
"""


async def handler(
    image_base64: str,
    image_mime: str = "image/jpeg",
    reference_lat: float | None = None,
    reference_lon: float | None = None,
    area_hint_acres: float | None = None,
) -> dict[str, Any]:
    """
    Analyze a farm image using Mistral vision model.

    Args:
        image_base64: Base64-encoded image
        image_mime: Image MIME type
        reference_lat: Reference latitude for polygon anchoring
        reference_lon: Reference longitude for polygon anchoring
        area_hint_acres: Known area to help calibrate polygon

    Returns:
        Structured farm boundary and feature analysis
    """
    from ..ai.llm_agent import get_llm_agent

    # Build text prompt with any reference coordinates
    context_parts = ["Please analyze this farm image and extract the boundary and features."]
    if reference_lat and reference_lon:
        context_parts.append(
            f"Reference location: {reference_lat:.6f}°N, {reference_lon:.6f}°E "
            f"(Tamil Nadu, India). Use these coordinates to generate a realistic GeoJSON polygon."
        )
    if area_hint_acres:
        context_parts.append(
            f"The farmer says this farm is approximately {area_hint_acres} acres."
        )

    context_parts.append(
        "Respond ONLY with the JSON object as specified. "
        "Generate plausible GeoJSON polygon coordinates based on the reference location if provided."
    )

    prompt = " ".join(context_parts)

    agent = get_llm_agent()

    try:
        raw_response = await agent.run_vision(
            system_prompt=VISION_SYSTEM_PROMPT,
            image_base64=image_base64,
            image_mime=image_mime,
            text_prompt=prompt,
        )

        # Parse JSON from response
        analysis = _parse_vision_response(raw_response)

        # If no GeoJSON polygon and we have reference coordinates, generate a simple one
        if (
            reference_lat
            and reference_lon
            and (
                not analysis.get("geojson_polygon")
                or not analysis["geojson_polygon"].get("coordinates")
            )
        ):
            analysis["geojson_polygon"] = _generate_bounding_polygon(
                reference_lat, reference_lon, area_hint_acres or analysis.get("area_estimate_acres") or 5.0
            )
            analysis["notes"] = (
                (analysis.get("notes") or "") + " [Polygon auto-generated from reference coordinates.]"
            ).strip()

        return {
            "success": True,
            "analysis": analysis,
            "geojson_polygon": analysis.get("geojson_polygon"),
            "area_estimate_acres": analysis.get("area_estimate_acres"),
            "features": analysis.get("features_detected", {}),
            "soil_hints": analysis.get("soil_color_analysis", {}),
            "confidence": analysis.get("confidence", 0.5),
            "raw_model_response": raw_response,
        }

    except Exception as e:
        logger.error(f"Farm image analysis failed: {e}")
        # If we have reference coords, still generate a basic polygon
        if reference_lat and reference_lon:
            polygon = _generate_bounding_polygon(
                reference_lat, reference_lon, area_hint_acres or 5.0
            )
            return {
                "success": True,
                "analysis": {
                    "boundary_type": "auto_generated",
                    "area_estimate_acres": area_hint_acres,
                    "geojson_polygon": polygon,
                    "confidence": 0.3,
                    "notes": "Vision analysis failed; polygon auto-generated from coordinates.",
                },
                "geojson_polygon": polygon,
                "area_estimate_acres": area_hint_acres,
                "confidence": 0.3,
                "error": str(e),
            }
        return {
            "success": False,
            "error": str(e),
            "message": "Farm image analysis failed. Please ensure the image is clear and try again.",
        }


def _parse_vision_response(raw: str) -> dict[str, Any]:
    """Extract and parse JSON from vision model response."""
    # Try direct JSON parse
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract JSON block from markdown
    code_block = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    if code_block:
        try:
            return json.loads(code_block.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to extract the first {...} block
    brace_match = re.search(r"\{[\s\S]+\}", raw)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    # Return a minimal fallback
    logger.warning("Could not parse vision model JSON response")
    return {
        "boundary_type": "unknown",
        "area_estimate_acres": None,
        "geojson_polygon": None,
        "confidence": 0.1,
        "notes": f"Raw model output: {raw[:500]}",
    }


def _generate_bounding_polygon(
    center_lat: float, center_lon: float, area_acres: float
) -> dict[str, Any]:
    """
    Generate an approximate rectangular GeoJSON polygon around a center point.

    Uses: 1 degree lat ≈ 111,000m; 1 degree lon ≈ 111,000m * cos(lat)
    For a square of ~area_acres:
        side_m = sqrt(area_acres * 4046.86)
    """
    import math

    side_m = math.sqrt(area_acres * 4046.86)  # 1 acre = 4046.86 m²
    delta_lat = (side_m / 2) / 111000
    delta_lon = (side_m / 2) / (111000 * math.cos(math.radians(center_lat)))

    # Slightly irregular shape (more realistic than perfect rectangle)
    coords = [
        [center_lon - delta_lon * 0.9, center_lat - delta_lat * 1.0],
        [center_lon + delta_lon * 1.05, center_lat - delta_lat * 0.95],
        [center_lon + delta_lon * 1.0, center_lat + delta_lat * 1.0],
        [center_lon - delta_lon * 0.95, center_lat + delta_lat * 0.9],
        [center_lon - delta_lon * 0.9, center_lat - delta_lat * 1.0],  # close ring
    ]

    return {
        "type": "Polygon",
        "coordinates": [coords],
    }
