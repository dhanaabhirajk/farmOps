"""Schemes API route — GET /farm/schemes, POST /farm/schemes/refresh.

User Story 5: Subsidy & Scheme Match (P3)
Endpoint spec: /api/v1/farm/schemes
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...services.schemes.scheme_service import SchemeService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["schemes"])

# Singleton service (dependency-injected in production)
_scheme_service = SchemeService()


# ─── Request / Response Models ─────────────────────────────────────────────────

class SchemeItem(BaseModel):
    """A single matched government scheme."""
    scheme_id: str
    name: str
    authority: str
    type: str
    benefit: str
    eligibility_explanation: str
    required_documents: List[str]
    apply_link: str
    application_portal: str
    deadline: str
    confidence: int
    tags: List[str]


class SchemeMatchData(BaseModel):
    """Structured payload returned by scheme scan."""
    state: str
    district: Optional[str] = None
    crops: List[str] = []
    area_acres: Optional[float] = None
    farmer_category: str
    schemes: List[SchemeItem]
    total_matched: int
    top_scheme_ids: List[str]
    scan_timestamp: str


class SchemeMatchResponse(BaseModel):
    """Standard API response for /farm/schemes."""
    success: bool
    data: Optional[SchemeMatchData] = None
    metadata: dict
    error: Optional[str] = None


class RefreshRequest(BaseModel):
    """Body for POST /farm/schemes/refresh."""
    farm_id: UUID = Field(..., description="Farm UUID")
    state: str = Field(default="Tamil Nadu", description="State name")
    district: Optional[str] = Field(default=None, description="District name")
    crops: Optional[List[str]] = Field(default=None, description="Crops grown or planned")
    area_acres: Optional[float] = Field(default=None, description="Farm area in acres")
    farmer_category: str = Field(
        default="small",
        description="Landholding category: marginal, small, medium, large",
    )
    language: str = Field(default="en", description="Response language: en, ta, hi")


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/schemes", response_model=SchemeMatchResponse)
async def get_schemes(
    farm_id: UUID = Query(..., description="Farm UUID"),
    state: str = Query(default="Tamil Nadu", description="State name"),
    district: Optional[str] = Query(default=None, description="District"),
    crops: Optional[str] = Query(
        default=None,
        description="Comma-separated crop names (e.g., 'Rice,Sugarcane')",
    ),
    area_acres: Optional[float] = Query(default=None, description="Farm area in acres"),
    farmer_category: str = Query(default="small", description="marginal|small|medium|large"),
    language: str = Query(default="en", description="Response language: en, ta, hi"),
    force_refresh: bool = Query(default=False, description="Bypass cache and re-run scan"),
):
    """
    Retrieve eligible government schemes for a farm.

    Returns cached results if available (valid for 7 days), or runs a fresh
    LLM-powered scheme scan. Use `force_refresh=true` to trigger a new scan.

    - **Cached**: ~50ms  
    - **Fresh LLM scan**: ~3-6s
    """
    start_time = datetime.utcnow()

    crops_list: Optional[List[str]] = None
    if crops:
        crops_list = [c.strip() for c in crops.split(",") if c.strip()]

    try:
        result = await _scheme_service.get_schemes(
            farm_id=farm_id,
            state=state,
            district=district,
            crops=crops_list,
            area_acres=area_acres,
            farmer_category=farmer_category,
            language=language,
            use_cache=not force_refresh,
        )
    except Exception as exc:
        logger.error("Scheme service error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    if not result.get("success"):
        elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
        return SchemeMatchResponse(
            success=False,
            error=result.get("error", "Scheme scan failed"),
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": round(elapsed, 2),
            },
        )

    elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
    data_payload = result.get("data", {})

    return SchemeMatchResponse(
        success=True,
        data=SchemeMatchData(**data_payload) if data_payload else None,
        metadata={
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(elapsed, 2),
            "cached": result.get("cached", False),
            "cached_at": result.get("cached_at"),
            "expires_at": result.get("expires_at"),
            "confidence": result.get("confidence", 0),
            "sources": result.get("sources", []),
            "explanation": result.get("explanation", ""),
            "model_version": result.get("model_version", ""),
            "human_review_required": result.get("human_review_required", False),
            "tool_calls_count": len(result.get("tool_calls", [])),
        },
    )


@router.post("/schemes/refresh", response_model=SchemeMatchResponse)
async def refresh_schemes(request: RefreshRequest):
    """
    Force a fresh LLM-powered government scheme scan for a farm.

    Archives the previous cached result and runs a new scan, then persists
    and returns the updated result.

    Response time: 3-6 seconds (LLM + tool calls).
    """
    start_time = datetime.utcnow()

    try:
        result = await _scheme_service.get_schemes(
            farm_id=request.farm_id,
            state=request.state,
            district=request.district,
            crops=request.crops,
            area_acres=request.area_acres,
            farmer_category=request.farmer_category,
            language=request.language,
            use_cache=False,  # always force fresh
        )
    except Exception as exc:
        logger.error("Scheme refresh error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000

    if not result.get("success"):
        return SchemeMatchResponse(
            success=False,
            error=result.get("error", "Scheme refresh failed"),
            metadata={"timestamp": datetime.utcnow().isoformat(), "response_time_ms": round(elapsed, 2)},
        )

    data_payload = result.get("data", {})
    return SchemeMatchResponse(
        success=True,
        data=SchemeMatchData(**data_payload) if data_payload else None,
        metadata={
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(elapsed, 2),
            "cached": False,
            "cached_at": None,
            "expires_at": result.get("expires_at"),
            "confidence": result.get("confidence", 0),
            "sources": result.get("sources", []),
            "explanation": result.get("explanation", ""),
            "model_version": result.get("model_version", ""),
            "human_review_required": result.get("human_review_required", False),
            "tool_calls_count": len(result.get("tool_calls", [])),
        },
    )
