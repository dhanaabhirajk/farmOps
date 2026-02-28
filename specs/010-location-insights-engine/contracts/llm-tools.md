# LLM Tool Schemas

**Version**: 1.0  
**Date**: 2026-02-28  
**Purpose**: Define tool schemas (function signatures) that the Mistral AI can invoke for deterministic, auditable recommendations.

This ensures the LLM cannot hallucinate agricultural/financial data without verification through tool calls.

---

## Tool Framework

All tools follow this pattern:

```javascript
{
  "type": "function",
  "function": {
    "name": "tool_name",
    "description": "Human-readable description of what the tool does",
    "parameters": {
      "type": "object",
      "properties": {
        "param1": { "type": "string", "description": "..." },
        "param2": { "type": "number", "description": "..." }
      },
      "required": ["param1"]
    }
  }
}
```

---

## Data Retrieval Tools

### 1. get_location_profile

**Purpose**: Fetch static location data (climate, soil template, elevation) for a geospatial tile.

**Definition**:
```json
{
  "type": "function",
  "function": {
    "name": "get_location_profile",
    "description": "Retrieve climate normals, soil template, elevation, and watershed info for a location tile (S2 geometry or H3). Used to establish baseline environmental context.",
    "parameters": {
      "type": "object",
      "properties": {
        "tile_id": {
          "type": "string",
          "description": "S2 geometry or H3 tile ID, e.g., '4852a0ed4ffffff'. Used to aggregate data across multiple farms in the same tile."
        }
      },
      "required": ["tile_id"]
    }
  }
}
```

**Returns**:
```json
{
  "tile_id": "4852a0ed4ffffff",
  "location": { "lat": 11.0168, "lon": 76.8194 },
  "climate_zone": "Tropical monsoonal",
  "temperature_c_annual_avg": 27.5,
  "temperature_c_annual_min": 22.0,
  "temperature_c_annual_max": 35.1,
  "rainfall_mm_annual": 1100,
  "rainfall_mm_sw_monsoon": 650,
  "rainfall_mm_ne_monsoon": 350,
  "soil_type": "Vertisol",
  "soil_texture": "Clay",
  "elevation_m": 45,
  "groundwater_depth_m": 8.5,
  "groundwater_salinity_ec": 0.6,
  "data_sources": [
    { "source": "IMD Climate Normals 2000-2020", "date": "2024-01-01" }
  ],
  "last_refreshed": "2024-01-01T00:00:00Z"
}
```

---

### 2. get_soil_profile

**Purpose**: Fetch farm-specific soil test results.

**Definition**:
```json
{
  "type": "function",
  "function": {
    "name": "get_soil_profile",
    "description": "Retrieve detailed soil test results for a farm (nutrients, pH, texture, etc.). Returns user-provided or lab-tested data.",
    "parameters": {
      "type": "object",
      "properties": {
        "farm_id": {
          "type": "string",
          "format": "uuid",
          "description": "UUID of the farm"
        }
      },
      "required": ["farm_id"]
    }
  }
}
```

**Returns**:
```json
{
  "farm_id": "550e8400-e29b-41d4-a716-446655440000",
  "soil_type": "Clay-loam",
  "soil_texture": "Clay-loam",
  "pH": 7.2,
  "organic_carbon_pct": 2.1,
  "nitrogen_mg_kg": 185,
  "phosphorus_mg_kg": 22,
  "potassium_mg_kg": 320,
  "drainage_class": "Well-drained",
  "salinity_ec_ds_m": 0.4,
  "test_date": "2025-01-15",
  "data_source": "lab-test",
  "confidence": 0.95
}
```

---

### 3. get_ndvi_timeseries

**Purpose**: Fetch satellite NDVI time-series for a farm.

**Definition**:
```json
{
  "type": "function",
  "function": {
    "name": "get_ndvi_timeseries",
    "description": "Retrieve NDVI (Normalized Difference Vegetation Index) time-series for a farm polygon for the last N days. Used to assess crop health trend.",
    "parameters": {
      "type": "object",
      "properties": {
        "farm_id": {
          "type": "string",
          "format": "uuid",
          "description": "UUID of the farm"
        },
        "days_back": {
          "type": "integer",
          "minimum": 1,
          "maximum": 365,
          "description": "Number of days to look back (default 30)"
        }
      },
      "required": ["farm_id"]
    }
  }
}
```

**Returns**:
```json
{
  "farm_id": "550e8400-e29b-41d4-a716-446655440000",
  "timeseries": [
    {
      "date": "2026-02-27",
      "ndvi_value": 0.68,
      "evi_value": 0.42,
      "cloud_cover_pct": 5,
      "satellite": "Sentinel-2"
    },
    {
      "date": "2026-02-25",
      "ndvi_value": 0.67,
      "cloud_cover_pct": 12
    }
  ],
  "trend": "increasing",
  "confidence": 0.92,
  "data_sources": [
    { "source": "Google Earth Engine (Sentinel-2)", "count": 8 }
  ]
}
```

---

### 4. get_weather_forecast

**Purpose**: Fetch 7-day weather observations and forecast.

**Definition**:
```json
{
  "type": "function",
  "function": {
    "name": "get_weather_forecast",
    "description": "Retrieve current weather and 7-day forecast for a farm location (temperature, rainfall, humidity, wind). Primary source: IMD; fallback: OpenWeatherMap.",
    "parameters": {
      "type": "object",
      "properties": {
        "farm_id": {
          "type": "string",
          "format": "uuid",
          "description": "UUID of the farm"
        },
        "forecast_days": {
          "type": "integer",
          "minimum": 1,
          "maximum": 14,
          "description": "Number of forecast days (default 7)"
        }
      },
      "required": ["farm_id"]
    }
  }
}
```

**Returns**:
```json
{
  "farm_id": "550e8400-e29b-41d4-a716-446655440000",
  "location": { "lat": 11.0168, "lon": 76.8194 },
  "current": {
    "temperature_c": 28.5,
    "humidity_pct": 72,
    "wind_speed_kmh": 8,
    "condition": "partly-cloudy",
    "timestamp": "2026-02-28T10:30:00Z"
  },
  "observations_7_days": [
    {
      "date": "2026-02-27",
      "temperature_c_avg": 27.8,
      "humidity_pct_avg": 71,
      "rainfall_mm": 0,
      "wind_speed_kmh_avg": 7
    }
  ],
  "forecast_7_days": [
    {
      "date": "2026-02-28",
      "temperature_c_min": 24,
      "temperature_c_max": 32,
      "rainfall_mm": 0,
      "rainfall_probability_pct": 5,
      "wind_speed_kmh": 10,
      "condition": "sunny"
    }
  ],
  "data_source": "IMD",
  "confidence": 0.88,
  "last_updated": "2026-02-28T10:15:00Z"
}
```

---

### 5. get_market_prices

**Purpose**: Fetch current and historical mandi prices.

**Definition**:
```json
{
  "type": "function",
  "function": {
    "name": "get_market_prices",
    "description": "Retrieve current and historical (7/30-day average) mandi prices for commodities in nearby mandis. Used for revenue forecasting and market risk assessment.",
    "parameters": {
      "type": "object",
      "properties": {
        "farm_id": {
          "type": "string",
          "format": "uuid",
          "description": "UUID of the farm"
        },
        "commodity": {
          "type": "string",
          "description": "Commodity code, e.g., 'RICE', 'TOMATO', 'SUGARCANE'"
        },
        "days_history": {
          "type": "integer",
          "minimum": 1,
          "maximum": 365,
          "description": "Days of historical prices to include (default 30)"
        }
      },
      "required": ["farm_id", "commodity"]
    }
  }
}
```

**Returns**:
```json
{
  "farm_id": "550e8400-e29b-41d4-a716-446655440000",
  "commodity": "RICE",
  "nearest_mandis": [
    {
      "market_id": 506,
      "market_name": "Koyambedu",
      "distance_km": 12.3,
      "current_price": {
        "modal_per_quintal": 1900,
        "min_per_quintal": 1850,
        "max_per_quintal": 1950,
        "trade_volume_quintals": 2500,
        "date": "2026-02-28"
      },
      "price_history": [
        { "date": "2026-02-27", "modal_per_quintal": 1895 },
        { "date": "2026-02-26", "modal_per_quintal": 1890 }
      ],
      "average_7_days": 1898,
      "average_30_days": 1875,
      "trend_30_days": "up_2pct"
    }
  ],
  "data_source": "AGMARKNET",
  "confidence": 0.95,
  "last_updated": "2026-02-28T22:00:00Z"
}
```

---

## Computation Tools

### 6. estimate_yield

**Purpose**: Compute expected crop yield based on inputs (crop, soil, rainfall, variety).

**Definition**:
```json
{
  "type": "function",
  "function": {
    "name": "estimate_yield",
    "description": "Estimate crop yield (kg/acre) based on soil properties, climate, variety, and management. Deterministic function: same inputs always give same output.",
    "parameters": {
      "type": "object",
      "properties": {
        "crop_code": {
          "type": "string",
          "description": "Crop identifier, e.g., 'RICE_SAMBA', 'SUGARCANE', 'TOMATO'"
        },
        "soil_type": {
          "type": "string",
          "description": "Soil classification, e.g., 'Vertisol', 'Alfisol'"
        },
        "soil_texture": {
          "type": "string",
          "description": "Soil texture, e.g., 'Clay', 'Sandy-loam'"
        },
        "soil_ph": {
          "type": "number",
          "minimum": 2,
          "maximum": 14,
          "description": "Soil pH"
        },
        "organic_carbon_pct": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Soil organic carbon %"
        },
        "annual_rainfall_mm": {
          "type": "number",
          "minimum": 0,
          "maximum": 5000,
          "description": "Mean annual rainfall in mm"
        },
        "irrigation_source": {
          "type": "string",
          "enum": ["rainfed", "well", "canal", "mixed"],
          "description": "Primary water source"
        },
        "variety": {
          "type": "string",
          "description": "Crop variety if known, e.g., 'IR-64', 'CO-51'"
        }
      },
      "required": ["crop_code", "soil_type", "annual_rainfall_mm"]
    }
  }
}
```

**Returns**:
```json
{
  "crop_code": "RICE_SAMBA",
  "estimated_yield_kg_per_acre": 3500,
  "confidence": 0.85,
  "factors": {
    "soil_contribution": 0.3,
    "climate_contribution": 0.4,
    "variety_contribution": 0.2,
    "management_assumption": 0.1
  },
  "assumptions": "Assumes good management practices (timely sowing, adequate fertilizer, pest control)",
  "limitations": "Yield sensitive to monsoon timing; poor management can reduce by 20-30%"
}
```

---

### 7. estimate_production_cost

**Purpose**: Estimate total cost to produce a crop per acre.

**Definition**:
```json
{
  "type": "function",
  "function": {
    "name": "estimate_production_cost",
    "description": "Compute expected production cost per acre (seed, fertilizer, labor, pesticide, water, machinery). Based on location, crop, and farm size.",
    "parameters": {
      "type": "object",
      "properties": {
        "crop_code": {
          "type": "string",
          "description": "Crop code, e.g., 'RICE_SAMBA'"
        },
        "region": {
          "type": "string",
          "description": "Region code for cost variation, e.g., 'TN_NORTHERN'"
        },
        "area_acres": {
          "type": "number",
          "minimum": 0.1,
          "maximum": 1000,
          "description": "Farm size in acres (economies of scale)"
        },
        "irrigation_type": {
          "type": "string",
          "enum": ["rainfed", "flood", "drip", "sprinkler"],
          "description": "Irrigation method"
        }
      },
      "required": ["crop_code", "region"]
    }
  }
}
```

**Returns**:
```json
{
  "crop_code": "RICE_SAMBA",
  "region": "TN_NORTHERN",
  "total_cost_per_acre": 42000,
  "breakdown": {
    "seed_cost": 1500,
    "fertilizer_cost": 8000,
    "pesticide_cost": 2500,
    "labor_cost": 15000,
    "water_cost": 4500,
    "machinery_rent_cost": 6000,
    "land_tax_other": 4000
  },
  "confidence": 0.80,
  "year": 2026,
  "notes": "Assumes market wage labor; adjust if family labor"
}
```

---

### 8. estimate_risk_score

**Purpose**: Assess multi-dimensional risk (drought, pest, market, policy).

**Definition**:
```json
{
  "type": "function",
  "function": {
    "name": "estimate_risk_score",
    "description": "Calculate risk scores (0-100%) for drought, pest, market, and policy factors. Uses historical data and current conditions.",
    "parameters": {
      "type": "object",
      "properties": {
        "farm_id": {
          "type": "string",
          "format": "uuid",
          "description": "Farm UUID"
        },
        "crop_code": {
          "type": "string",
          "description": "Crop code"
        },
        "season": {
          "type": "string",
          "enum": ["samba", "summer", "spring"],
          "description": "Season being considered"
        }
      },
      "required": ["farm_id", "crop_code", "season"]
    }
  }
}
```

**Returns**:
```json
{
  "crop_code": "RICE_SAMBA",
  "season": "samba",
  "risk_scores": {
    "drought_risk_pct": 15,
    "drought_reasoning": "IMD forecast shows normal SW monsoon; groundwater at 8.5m (safe). Drought risk low."
  },
    "pest_risk_pct": 22,
    "pest_reasoning": "High humidity (avg 72%) and moderate temps (27°C) favor stem borer and sheath blight. Medium risk."
  },
    "market_risk_pct": 18,
    "market_reasoning": "Rice prices stable at ₹1900/quintal; 30-day trend flat. Market risk moderate."
  },
    "policy_risk_pct": 5,
    "policy_reasoning": "No recent policy changes; MSP support continued. Policy risk low."
  },
    "overall_risk_pct": 18
  },
  "confidence": 0.82
}
```

---

### 9. estimate_profit

**Purpose**: Calculate expected profit per acre.

**Definition**:
```json
{
  "type": "function",
  "function": {
    "name": "estimate_profit",
    "description": "Compute expected profit per acre = (yield × price) - cost. Uses yield, price, and cost estimates.",
    "parameters": {
      "type": "object",
      "properties": {
        "crop_code": {
          "type": "string",
          "description": "Crop code"
        },
        "expected_yield_kg_per_acre": {
          "type": "number",
          "minimum": 0,
          "description": "Estimated yield in kg/acre"
        },
        "expected_price_per_kg": {
          "type": "number",
          "minimum": 0,
          "description": "Expected selling price in ₹/kg"
        },
        "production_cost_per_acre": {
          "type": "number",
          "minimum": 0,
          "description": "Cost estimate in ₹/acre"
        }
      },
      "required": ["crop_code", "expected_yield_kg_per_acre", "expected_price_per_kg", "production_cost_per_acre"]
    }
  }
}
```

**Returns**:
```json
{
  "crop_code": "RICE_SAMBA",
  "expected_yield_kg_per_acre": 3500,
  "expected_price_per_kg": 25,
  "revenue_per_acre": 87500,
  "production_cost_per_acre": 42000,
  "profit_per_acre": 45500,
  "roi_pct": 108,
  "confidence": 0.82,
  "notes": "ROI assumes no major losses to pests/disease"
}
```

---

### 10. compute_break_even_harvest_delay

**Purpose**: Calculate days of storage before price rise offsets storage costs (harvest timing).

**Definition**:
```json
{
  "type": "function",
  "function": {
    "name": "compute_break_even_harvest_delay",
    "description": "For mature crops, calculate how many days storage breaks even with expected price increase. Returns recommendation: sell now or store.",
    "parameters": {
      "type": "object",
      "properties": {
        "commodity": {
          "type": "string",
          "description": "Commodity, e.g., 'TOMATO', 'RICE'"
        },
        "current_price_per_kg": {
          "type": "number",
          "description": "Today's price in ₹"
        },
        "expected_price_in_7_days": {
          "type": "number",
          "description": "Forecasted price in 7 days (from AI model or trend)"
        },
        "expected_price_in_14_days": {
          "type": "number",
          "description": "Forecasted price in 14 days"
        },
        "storage_cost_per_day": {
          "type": "number",
          "description": "Daily storage cost in ₹/MT or similar unit"
        },
        "spoilage_rate_pct_per_day": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Daily loss % (rot, shrinkage, etc.)"
        }
      },
      "required": ["commodity", "current_price_per_kg", "expected_price_in_7_days", "storage_cost_per_day", "spoilage_rate_pct_per_day"]
    }
  }
}
```

**Returns**:
```json
{
  "commodity": "TOMATO",
  "current_price_per_kg": 18,
  "break_even_delay_days": 3,
  "recommendation": "store",
  "scenarios": [
    {
      "hold_days": 0,
      "expected_price_per_kg": 18,
      "expected_revenue": 180000
    },
    {
      "hold_days": 7,
      "expected_price_per_kg": 22,
      "expected_spoilage_loss_pct": 8,
      "expected_net_revenue": 184480
    }
  ],
  "confidence": 0.70,
  "notes": "Price trend is +2.5% per week; storage cost justified if stay below 8% spoilage"
}
```

---

### 11. check_subsidy_eligibility

**Purpose**: Determine if farm qualifies for subsidies based on geospatial and farm criteria.

**Definition**:
```json
{
  "type": "function",
  "function": {
    "name": "check_subsidy_eligibility",
    "description": "Check farm eligibility for government schemes (micro-irrigation, seeds, input subsidies, etc.) based on location, land size, crop, and water source.",
    "parameters": {
      "type": "object",
      "properties": {
        "farm_id": {
          "type": "string",
          "format": "uuid",
          "description": "Farm UUID"
        },
        "scheme_id": {
          "type": "string",
          "description": "Scheme code, e.g., 'PMKSY_MICRO', 'SEED_SUBSIDY'"
        }
      },
      "required": ["farm_id", "scheme_id"]
    }
  }
}
```

**Returns**:
```json
{
  "farm_id": "550e8400-e29b-41d4-a716-446655440000",
  "scheme_id": "PMKSY_MICRO",
  "scheme_name": "Pradhan Mantri Krishi Sinchayee Yojana - Micro Irrigation",
  "eligible": true,
  "eligibility_breakdown": {
    "location_check": { "pass": true, "reason": "District Thanjavur is covered" },
    "land_size_check": { "pass": true, "reason": "5.2 acres < 5 acre max" },
    "water_source_check": { "pass": true, "reason": "Well available" },
    "crop_check": { "pass": true, "reason": "Rice is in eligible crop list" }
  },
  "subsidy_amount": 95000,
  "subsidy_coverage_pct": 55,
  "required_documents": ["Land deed", "Aadhaar", "Equipment quotation"],
  "application_link": "https://pmksy.gov.in/apply",
  "deadline": "2026-05-31",
  "confidence": 0.95
}
```

---

## Formatting/Language Tools

### 12. translate_to_language

**Purpose**: Translate recommendation text to farmer's preferred language.

**Definition**:
```json
{
  "type": "function",
  "function": {
    "name": "translate_to_language",
    "description": "Translate agricultural recommendation text to farmer's language (Tamil, Hindi, English). Preserves technical terms and local idioms.",
    "parameters": {
      "type": "object",
      "properties": {
        "text": {
          "type": "string",
          "description": "English recommendation text (max 2000 chars)"
        },
        "target_language": {
          "type": "string",
          "enum": ["ta", "hi", "en"],
          "description": "Target language code"
        },
        "context": {
          "type": "string",
          "enum": ["crop_recommendation", "irrigation", "harvest", "subsidy"],
          "description": "Context for domain-specific terminology"
        }
      },
      "required": ["text", "target_language"]
    }
  }
}
```

**Returns**:
```json
{
  "original_text": "Based on your soil (clay-loam, pH 7.2) and location (Thanjavur district), rice is the top recommendation for Samba season.",
  "translated_text": "உங்கள் மண் (களிமண், pH 7.2) மற்றும் இடம் (தஞ்சாவூர் மாவட்டம்) அடிப்படையில், சம்பா பருவத்தில் நெல் சிறந்த பரிந்துரை.",
  "target_language": "ta",
  "confidence": 0.98
}
```

---

## Tool Usage Rules

1. **No Hallucination**: If a tool returns "not found" or "insufficient data", LLM must NOT invent data. Instead, explain the gap and suggest next steps.

2. **Tool Chaining**: Multi-step recommendations require chaining tools. For example:
   - Crop recommendation: `get_location_profile()` → `get_soil_profile()` → `estimate_yield()` → `estimate_production_cost()` → `get_market_prices()` → `estimate_profit()`

3. **Confidence Attribution**: Each tool call's confidence contributes to overall recommendation confidence. Aggregate as weighted average.

4. **Error Handling**: If a tool fails, gracefully fall back (e.g., if satellite NDVI unavailable, use historical average + lower confidence).

5. **Audit Trail**: Every tool call must be logged with inputs, outputs, execution time, and cost.

---

**Next**: Implement tool backends in backend Python service.
