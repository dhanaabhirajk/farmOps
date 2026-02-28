# API Response Contracts

**Version**: 1.0  
**Date**: 2026-02-28  
**Purpose**: Define response schemas for all backend API endpoints serving the Remix frontend.

---

## Standard Response Wrapper

All API responses follow this envelope:

```json
{
  "success": true,
  "data": { /* endpoint-specific data */ },
  "metadata": {
    "timestamp": "2026-02-28T10:30:00Z",
    "version": "1.0",
    "request_id": "req_abc123def456"
  },
  "errors": null
}
```

**Error Response**:
```json
{
  "success": false,
  "data": null,
  "metadata": {
    "timestamp": "2026-02-28T10:30:00Z",
    "version": "1.0",
    "request_id": "req_abc123def456"
  },
  "errors": [
    {
      "code": "FARM_NOT_FOUND",
      "message": "Farm with ID 'xyz' not found",
      "field": "farm_id",
      "details": {}
    }
  ]
}
```

---

## Endpoint: GET /api/farm/snapshot

**Purpose**: Retrieve cached Farm Snapshot (or cold-run if not cached).

**Query Parameters**:
- `farm_id` (UUID, required): Farm to fetch snapshot for
- `use_cache` (boolean, optional, default=true): Force refresh if false

**Response Data**:

```json
{
  "farm": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "North Paddy Field",
    "area_acres": 5.2,
    "location": {
      "type": "Point",
      "coordinates": [76.8194, 11.0168]
    },
    "created_at": "2026-01-15T08:00:00Z",
    "updated_at": "2026-02-28T09:30:00Z"
  },
  "snapshot": {
    "soil_summary": {
      "type": "Clay-loam",
      "ph": 7.2,
      "organic_carbon_pct": 2.1,
      "drainage": "Well-drained",
      "status": "healthy",
      "confidence": 0.85,
      "data_age_hours": 45
    },
    "ndvi_trend": {
      "current_value": 0.68,
      "last_7_days": [0.62, 0.63, 0.65, 0.66, 0.67, 0.68, 0.68],
      "trend_direction": "increasing",
      "confidence": 0.92,
      "data_age_hours": 12
    },
    "weather": {
      "current": {
        "temperature_c": 28.5,
        "humidity_pct": 72,
        "wind_speed_kmh": 8,
        "condition": "partly-cloudy"
      },
      "forecast_7_days": [
        {
          "date": "2026-02-28",
          "temp_min_c": 24,
          "temp_max_c": 32,
          "rainfall_mm": 0,
          "rainfall_probability_pct": 5,
          "wind_speed_kmh": 10
        }
      ],
      "confidence": 0.88,
      "data_age_hours": 2
    },
    "nearest_mandi_price": {
      "market_id": 506,
      "market_name": "Koyambedu",
      "distance_km": 12.3,
      "commodity": "Rice",
      "modal_price_per_quintal": 1900,
      "min_price_per_quintal": 1850,
      "max_price_per_quintal": 1950,
      "price_trend_30_days": "stable",
      "currency": "INR",
      "confidence": 0.95,
      "data_age_hours": 1
    },
    "top_action": {
      "priority": "high",
      "action": "Water today",
      "reason": "Soil moisture low at 10cm depth; no rain forecast for 24h",
      "suggested_water_volume_mm": 25,
      "estimated_cost": 500,
      "confidence": 0.92,
      "data_sources": ["soil_profile", "weather_forecast"]
    },
    "data_freshness": {
      "weather": { "hours_ago": 2, "next_refresh": "2026-02-28T12:30:00Z" },
      "ndvi": { "hours_ago": 12, "next_refresh": "2026-03-01T10:30:00Z" },
      "soil": { "hours_ago": 45, "next_refresh": "2026-03-01T05:30:00Z" },
      "market_price": { "hours_ago": 1, "next_refresh": "2026-02-28T22:30:00Z" }
    }
  },
  "cache_status": {
    "was_cached": true,
    "cached_at": "2026-02-28T10:00:00Z",
    "expires_at": "2026-02-28T14:00:00Z"
  }
}
```

**HTTP Status**:
- `200 OK` — Snapshot generated successfully
- `404 Not Found` — Farm not found
- `429 Too Many Requests` — Rate limit exceeded
- `503 Service Unavailable` — External data source down (partial data returned)

**Latency SLA**:
- Cached: ≤300ms (p95)
- Cold: ≤8s (p95)

---

## Endpoint: POST /api/farm/recommendations

**Purpose**: Generate crop, irrigation, harvest, or action recommendations.

**Request Body**:

```json
{
  "farm_id": "550e8400-e29b-41d4-a716-446655440000",
  "recommendation_type": "crop",
  "season": "samba",
  "constraints": {
    "preferred_crops": ["Rice"],
    "exclude_crops": [],
    "budget_constraint": false,
    "water_scarcity": false
  },
  "language": "ta"
}
```

**Response Data** (Crop Recommendation):

```json
{
  "farm_id": "550e8400-e29b-41d4-a716-446655440000",
  "recommendation_id": "rec_crop_001",
  "type": "crop",
  "generated_at": "2026-02-28T10:35:00Z",
  "confidence": 0.87,
  "payload": {
    "season": "samba",
    "recommended_crops": [
      {
        "rank": 1,
        "crop_name": "Rice (Samba)",
        "crop_code": "RICE_SAMBA",
        "expected_yield_kg_per_acre": 3500,
        "expected_revenue_per_acre": 87500,
        "expected_cost_per_acre": 42000,
        "expected_profit_per_acre": 45500,
        "roi_pct": 108,
        "planting_window": {
          "start_date": "2026-06-01",
          "end_date": "2026-07-15",
          "ideal_start_date": "2026-06-10"
        },
        "water_requirement_mm": 950,
        "water_source_options": ["Monsoon", "Well", "Canal"],
        "risk": {
          "drought_risk_pct": 15,
          "pest_risk_pct": 22,
          "market_risk_pct": 18,
          "policy_risk_pct": 5,
          "overall_risk_pct": 18
        },
        "risk_mitigation": "Use resistant varieties; monitor for stem borers",
        "alignment_with_policy": "Encouraged under PMKSY subsidy for micro-irrigation",
        "confidence": 0.90
      },
      {
        "rank": 2,
        "crop_name": "Sugarcane",
        "crop_code": "SUGARCANE",
        "expected_profit_per_acre": 38000,
        "planting_window": { "start_date": "2026-05-01", "end_date": "2026-07-31" },
        "water_requirement_mm": 1200,
        "risk": { "overall_risk_pct": 22 },
        "confidence": 0.78
      }
    ]
  },
  "sources": [
    {
      "source_name": "Climate normals (IMD)",
      "data_age_hours": 720,
      "confidence_contribution_pct": 25
    },
    {
      "source_name": "Soil properties (uploaded test)",
      "data_age_hours": 1440,
      "confidence_contribution_pct": 20
    },
    {
      "source_name": "Market price history (AGMARKNET)",
      "data_age_hours": 1,
      "confidence_contribution_pct": 30
    },
    {
      "source_name": "AI model (Mistral 7B)",
      "data_age_hours": 0,
      "confidence_contribution_pct": 25
    }
  ],
  "explanation": "Based on your soil (clay-loam, pH 7.2) and location (Thanjavur district), rice is the top recommendation for Samba season. Your area received 800mm rain in SW monsoon this year, supporting good paddy. Current prices are ₹1900/quintal, giving good profit margin. Market is stable with mild uptrend expected. Risks are moderate (drought unlikely this season per IMD forecast). Cost includes seed, fertilizer, labor — includes subsidy potential.",
  "explanation_ta": "உங்கள் மண் (களிமண், pH 7.2) மற்றும் இடம் (தஞ்சாவூர் மாவட்டம்) அடிப்படையில், சம்பா பருவத்தில் நெல் சிறந்த பரிந்துரை. உங்கள் பகுதி SW பருவத்தில் 800 மிமீ மழை பெற்றது, நல்ல நெல் விளைச்சலை ஆதரிக்கிறது...",
  "human_review_required": false,
  "tool_calls": [
    {
      "tool_name": "get_location_profile",
      "inputs": { "tile_id": "4852a0ed4ffffff" },
      "outputs": { "climate_zone": "Tropical monsoonal", "rainfall_mm_annual": 1100 },
      "execution_time_ms": 45
    },
    {
      "tool_name": "estimate_yield",
      "inputs": { "crop": "RICE_SAMBA", "soil_type": "Clay-loam", "rainfall": 800 },
      "outputs": { "expected_yield_kg_per_acre": 3500 },
      "execution_time_ms": 120
    }
  ]
}
```

**Response Data** (Irrigation Recommendation):

```json
{
  "farm_id": "550e8400-e29b-41d4-a716-446655440000",
  "recommendation_id": "rec_irr_001",
  "type": "irrigation",
  "generated_at": "2026-02-28T10:35:00Z",
  "confidence": 0.89,
  "payload": {
    "irrigation_events": [
      {
        "event_number": 1,
        "scheduled_date": "2026-02-28",
        "reason": "Soil moisture low at 10cm depth",
        "soil_moisture_pct": 35,
        "target_soil_moisture_pct": 60,
        "water_volume_mm": 25,
        "water_volume_liters_per_acre": 10230,
        "cost_estimate": 500,
        "rain_forecast_24h": {
          "probability_pct": 5,
          "expected_rainfall_mm": 0
        },
        "recommendation": "Irrigate today",
        "irrigation_method": "Drip (if available)",
        "confidence": 0.93
      },
      {
        "event_number": 2,
        "scheduled_date": "2026-03-03",
        "reason": "Forecast shows no rain; moisture will deplete",
        "water_volume_mm": 20,
        "cost_estimate": 400,
        "confidence": 0.85
      }
    ],
    "summary": {
      "planning_horizon_days": 14,
      "total_water_needed_mm": 90,
      "total_water_liters_per_acre": 36809,
      "estimated_cost_14_days": 3500,
      "irrigation_efficiency_recommendation": "Use drip for 30% water savings"
    }
  },
  "sources": [...],
  "explanation": "Soil moisture is currently 35%, below optimal 60% for this crop stage. 7-day forecast shows only 5mm rain expected, so two irrigation events are recommended in next 14 days. Drip irrigation would save water and cost compared to flood irrigation.",
  "tool_calls": [...]
}
```

**HTTP Status**:
- `200 OK` — Recommendation generated
- `202 Accepted` — Long-running recommendation queued for async processing
- `400 Bad Request` — Invalid parameters
- `429 Too Many Requests` — Rate limit exceeded
- `503 Service Unavailable` — AI service temporarily down

**Latency SLA**: ≤10s (p95) for first-run, ≤3s (p95) for cached intermediate data

---

## Endpoint: GET /api/farm/recommendations

**Purpose**: List all historical recommendations for a farm.

**Query Parameters**:
- `farm_id` (UUID, required)
- `type` (string, optional): Filter by type (crop, irrigation, harvest, subsidy)
- `status` (string, optional): Filter by status (active, superseded, archived)
- `limit` (integer, optional, default=10): Max results to return
- `offset` (integer, optional, default=0): Pagination offset

**Response Data**:

```json
{
  "recommendations": [
    { /* full recommendation object as above */ }
  ],
  "pagination": {
    "total_count": 25,
    "returned_count": 10,
    "limit": 10,
    "offset": 0,
    "has_more": true
  }
}
```

---

## Endpoint: POST /api/farm/schemes

**Purpose**: Scan farm for eligible government subsidies/schemes.

**Request Body**:

```json
{
  "farm_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response Data**:

```json
{
  "farm_id": "550e8400-e29b-41d4-a716-446655440000",
  "scanned_at": "2026-02-28T10:35:00Z",
  "eligible_schemes": [
    {
      "scheme_id": "sch_pmksy_micro",
      "scheme_name": "Pradhan Mantri Krishi Sinchayee Yojana (PMKSY) - Micro Irrigation",
      "description": "Subsidy for drip and sprinkler irrigation systems",
      "subsidy_amount": 95000,
      "subsidy_coverage_pct": 55,
      "eligibility_criteria": {
        "location_match": true,
        "land_size_match": true,
        "crop_match": true,
        "water_source_match": true
      },
      "matched_fields": {
        "district": "Thanjavur",
        "land_size_acres": 5.2,
        "preferred_crops": ["Rice", "Sugarcane"],
        "water_availability": "Well + Canal"
      },
      "apply_link": "https://pmksy.gov.in/apply",
      "required_documents": [
        "Land deed copy (Patta)",
        "Aadhaar card",
        "Passport-size photos",
        "Quotation from equipment supplier"
      ],
      "application_deadline": "2026-05-31",
      "confidence": 0.96
    }
  ],
  "total_schemes_in_area": 8,
  "total_eligible": 3,
  "confidence_overall": 0.92,
  "sources": [...]
}
```

---

## Endpoint: POST /api/user/actions (Offline Sync)

**Purpose**: Sync queued farmer actions (created while offline).

**Request Body**:

```json
{
  "actions": [
    {
      "id": "act_123",
      "farm_id": "550e8400-e29b-41d4-a716-446655440000",
      "action_type": "mark_irrigated",
      "action_data": {
        "irrigation_date": "2026-02-28",
        "water_volume_mm": 25
      },
      "created_at": "2026-02-28T09:00:00Z"
    }
  ]
}
```

**Response Data**:

```json
{
  "synced_actions": [
    {
      "id": "act_123",
      "status": "synced",
      "synced_at": "2026-02-28T10:35:00Z"
    }
  ],
  "failed_actions": [],
  "total_synced": 1
}
```

---

## Error Codes Reference

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `FARM_NOT_FOUND` | 404 | Farm ID does not exist |
| `INVALID_POLYGON` | 400 | Farm polygon is invalid (self-intersecting, etc.) |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests from IP/user |
| `EXTERNAL_SERVICE_UNAVAILABLE` | 503 | Weather/satellite/market API down |
| `INSUFFICIENT_DATA` | 400 | Not enough data to generate recommendation |
| `UNAUTHORIZED` | 401 | User not authenticated or not farm owner |
| `INVALID_REQUEST` | 400 | Malformed request body |
| `AI_SERVICE_ERROR` | 503 | Mistral API error |

---

**Next**: Define LLM tool schemas in `llm-tools.md`
