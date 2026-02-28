# Phase 1 Data Model: Location-Based Insights Engine

**Date**: 2026-02-28  
**Branch**: `010-location-insights-engine`  
**Database**: Supabase PostgreSQL with PostGIS extension

This document defines the complete data model for the Location-Based Insights Engine, including entities, fields, relationships, validation rules, and state transitions.

---

## Entity Relationship Diagram (Conceptual)

```
User
  ├── owns → Farm (1:N)
  │   ├── has-many → Recommendation (1:N)
  │   ├── has-one → LocationProfile (1:1, via location)
  │   └── has-one → SoilProfile (1:1, via soil_test_id)
  ├── has-many → UserAction (1:N, queued actions)
  └── has-many → FarmSnapshot (1:N, cached snapshots)

LocationProfile (keyed by geospatial tile)
  ├── climate_normals
  ├── soil_template
  ├── elevation
  └── watershed_id

DataAuditLog (traces all external API calls and AI tool calls)
  ├── source (e.g., "get_market_price", "estimate_yield")
  ├── request_payload
  ├── response_summary
  └── cost_estimate
```

---

## Core Entities

### 1. User

**Purpose**: Farmer account with language/location preferences.

**Table**: `users` (auth table managed by Supabase Auth)

| Field | Type | Nullable | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `id` | UUID | No | `gen_random_uuid()` | PK | Supabase Auth ID |
| `email` | TEXT | No | — | UNIQUE, email format | |
| `phone` | TEXT | Yes | NULL | Unique, E.164 format | +91XXXXXXXXXX |
| `name` | TEXT | Yes | NULL | Length 1-255 | Display name |
| `language` | VARCHAR(5) | No | 'ta' | IN ('ta', 'en', 'hi') | Tamil default for MVP |
| `location_pref` | GEOGRAPHY(POINT, 4326) | Yes | NULL | | Preferred map center (lat/lon) |
| `last_active` | TIMESTAMP WITH TIME ZONE | No | `now()` | | For retention metrics |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |
| `updated_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |

**Indexes**:
- `(email)` — UNIQUE for login
- `(phone)` — UNIQUE for SMS OTP verification
- `(created_at DESC)` — For user cohort analysis

**RLS Policies**:
- Users can only read/update their own record
- Public can insert (signup)

---

### 2. Farm

**Purpose**: Farmer's agricultural plot identified by polygon and location.

**Table**: `farms`

| Field | Type | Nullable | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `id` | UUID | No | `gen_random_uuid()` | PK | |
| `user_id` | UUID | No | — | FK → `users.id`, ON DELETE CASCADE | Owner of farm |
| `name` | TEXT | No | — | Length 1-255 | e.g., "North field", "Paddy block A" |
| `polygon_geojson` | JSONB | No | — | Valid GeoJSON Polygon or MultiPolygon | Stored as GeoJSON; indexed for spatial queries |
| `area_acres` | DECIMAL(10, 2) | No | — | Check > 0, < 10000 | Computed from polygon or user-provided |
| `soil_profile_id` | UUID | Yes | NULL | FK → `soil_profiles.id` | Link to soil test results |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |
| `updated_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | When farm details changed |

**Geo Indexes**:
- `(ST_GeomFromGeoJSON(polygon_geojson))` — PostGIS spatial index for polygon queries

**Computed Columns** (PostgreSQL generated columns):
- `polygon_geom`: `GEOMETRY(POLYGON, 4326)` — Extracted from GeoJSON for spatial functions
- `centroid`: `GEOGRAPHY(POINT, 4326)` — Center of polygon for location lookups
- `polygon_validity`: Boolean — Confirms polygon is valid (no self-intersections)

**Constraints**:
- Polygon must be a valid Polygon or MultiPolygon (ST_IsValid check)
- Area must match polygon extent (±5% tolerance; user override allowed)

**RLS Policies**:
- Users can only CRUD their own farms

---

### 3. LocationProfile

**Purpose**: Static aggregated data for a geospatial tile (climate, soil template, elevation, watershed).

**Table**: `location_profiles`

| Field | Type | Nullable | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `id` | UUID | No | `gen_random_uuid()` | PK | |
| `tile_id` | TEXT | No | — | UNIQUE | S2 geometry or H3 tile ID (e.g., "4852a0ed4ffffff") |
| `location` | GEOGRAPHY(POINT, 4326) | No | — | Indexed | Center of tile |
| `climate_zone` | VARCHAR(50) | Yes | NULL | (lookup table) | e.g., "Tropical monsoonal", "Semi-arid" |
| `temperature_c_annual_avg` | DECIMAL(5, 2) | Yes | NULL | | Historical 30-year normal |
| `temperature_c_annual_min` | DECIMAL(5, 2) | Yes | NULL | | Minimum recorded |
| `temperature_c_annual_max` | DECIMAL(5, 2) | Yes | NULL | | Maximum recorded |
| `rainfall_mm_annual` | DECIMAL(8, 1) | Yes | NULL | | Total annual precipitation (30-yr normal) |
| `rainfall_mm_sw_monsoon` | DECIMAL(7, 1) | Yes | NULL | | June-August (SW monsoon) |
| `rainfall_mm_ne_monsoon` | DECIMAL(7, 1) | Yes | NULL | | Sept-Nov (NE monsoon) |
| `soil_type` | VARCHAR(30) | Yes | NULL | e.g., "Vertisol", "Alfisol" | Classification |
| `soil_texture` | VARCHAR(30) | Yes | NULL | "Clay-loam", "Sandy-silt" | Soil texture class |
| `elevation_m` | DECIMAL(8, 1) | Yes | NULL | | Mean elevation in tile |
| `watershed_id` | UUID | Yes | NULL | FK → `watersheds.id` | For water resource planning |
| `groundwater_depth_m` | DECIMAL(6, 2) | Yes | NULL | | Average depth to water table (seasonal) |
| `groundwater_salinity_ec` | DECIMAL(6, 2) | Yes | NULL | | Electrical conductivity (for salinity assessment) |
| `data_sources` | JSONB | Yes | NULL | | Array of {source, date, url} objects |
| `last_refreshed` | TIMESTAMP WITH TIME ZONE | Yes | NULL | | When data was last updated |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |
| `updated_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |

**Indexes**:
- `(tile_id)` — UNIQUE for tile lookup
- `(location)` — GiST spatial index for nearest-neighbor queries

**Cache TTL**: 30 days (refresh monthly or on-demand)

---

### 4. SoilProfile

**Purpose**: Detailed soil test results linked to a farm.

**Table**: `soil_profiles`

| Field | Type | Nullable | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `id` | UUID | No | `gen_random_uuid()` | PK | |
| `farm_id` | UUID | No | — | FK → `farms.id` | Farm this profile belongs to |
| `soil_type` | VARCHAR(30) | Yes | NULL | Lookup | e.g., "Vertisol" |
| `soil_texture` | VARCHAR(30) | Yes | NULL | Lookup | "Clay-loam", "Sandy" |
| `pH` | DECIMAL(3, 2) | Yes | NULL | Check 2–14 | Acidity/alkalinity |
| `organic_carbon_pct` | DECIMAL(4, 2) | Yes | NULL | Check 0–100 | Weight percentage |
| `nitrogen_mg_kg` | DECIMAL(6, 2) | Yes | NULL | | Extractable N (soil test units) |
| `phosphorus_mg_kg` | DECIMAL(6, 2) | Yes | NULL | | Extractable P |
| `potassium_mg_kg` | DECIMAL(6, 2) | Yes | NULL | | Extractable K |
| `depth_cm` | INT | Yes | NULL | Check > 0, ≤ 120 | Sampling depth |
| `drainage_class` | VARCHAR(30) | Yes | NULL | e.g., "Well-drained", "Poorly-drained" | |
| `salinity_ec_ds_m` | DECIMAL(5, 2) | Yes | NULL | | Electrical conductivity (EC) in dS/m |
| `test_date` | DATE | No | — | | When soil test was conducted |
| `lab_name` | TEXT | Yes | NULL | | Which lab performed test |
| `data_source` | VARCHAR(50) | No | 'user-reported' | IN ('user-reported', 'lab-test', 'survey') | Origin of data |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |
| `updated_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | When profile was last updated |

**Validation Rules**:
- If `data_source = 'user-reported'`, confidence flags lower in recommendations
- If `test_date < now() - INTERVAL '2 years'`, show "consider fresh test" suggestion

---

### 5. WeatherSnapshot

**Purpose**: Time-series weather observations and forecasts.

**Table**: `weather_snapshots`

| Field | Type | Nullable | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `id` | UUID | No | `gen_random_uuid()` | PK | |
| `farm_id` | UUID | No | — | FK → `farms.id` | Farm location |
| `snapshot_date` | DATE | No | — | | Date of snapshot |
| `observations` | JSONB | No | — | Array of {temp_c, humidity_pct, rainfall_mm, wind_speed_kmh, timestamp} | Last 7 days |
| `forecast` | JSONB | No | — | Array of {temp_c_min, temp_c_max, rainfall_mm, rainfall_probability_pct, wind_speed_kmh, date} | Next 7 days |
| `data_sources` | JSONB | No | — | Array of {source: 'IMD'|'OpenWeatherMap', fetch_time} | Which API provided data |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |
| `updated_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |

**Retention**: Keep 90 days of historical weather snapshots for analysis.

**Indexes**:
- `(farm_id, snapshot_date DESC)` — For time-series queries

---

### 6. VegTimeSeries (NDVI/EVI)

**Purpose**: Satellite vegetation index time-series for farm.

**Table**: `veg_time_series`

| Field | Type | Nullable | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `id` | UUID | No | `gen_random_uuid()` | PK | |
| `farm_id` | UUID | No | — | FK → `farms.id` | Farm this series belongs to |
| `measurement_date` | DATE | No | — | | Date of satellite pass |
| `ndvi_value` | DECIMAL(5, 3) | Yes | NULL | Check -1 ≤ value ≤ 1 | Normalized Difference Vegetation Index |
| `evi_value` | DECIMAL(5, 3) | Yes | NULL | Check -1 ≤ value ≤ 1 | Enhanced Vegetation Index (optional) |
| `cloud_cover_pct` | DECIMAL(5, 2) | Yes | NULL | Check 0–100 | Cloud coverage % (QA metric) |
| `data_source` | VARCHAR(50) | No | 'GEE' | IN ('GEE', 'Sentinel Hub', 'Planet') | Provider |
| `satellite` | VARCHAR(50) | Yes | NULL | e.g., "Sentinel-2", "Landsat-8" | Which satellite |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |

**Indexes**:
- `(farm_id, measurement_date DESC)` — For time-series queries
- `(cloud_cover_pct)` — To filter cloudy observations

**Time-Series Query**: Last 30 days of NDVI values for trend analysis.

---

### 7. MarketSnapshot

**Purpose**: Cached mandi prices for commodities.

**Table**: `market_snapshots`

| Field | Type | Nullable | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `id` | UUID | No | `gen_random_uuid()` | PK | |
| `market_id` | INT | No | — | FK → `markets.id` | Which mandi |
| `commodity` | VARCHAR(50) | No | — | e.g., "Rice", "Tomato" | What crop |
| `modal_price_per_quintal` | DECIMAL(8, 2) | No | — | Check > 0 | Most common transaction price in ₹ |
| `min_price_per_quintal` | DECIMAL(8, 2) | Yes | NULL | | Floor price for date |
| `max_price_per_quintal` | DECIMAL(8, 2) | Yes | NULL | | Ceiling price for date |
| `trade_volume_quintals` | INT | Yes | NULL | | Quantity traded |
| `snapshot_date` | DATE | No | — | | Date of price observation |
| `data_source` | VARCHAR(50) | No | 'AGMARKNET' | IN ('AGMARKNET', 'data.gov.in', ...) | Which source |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |

**Indexes**:
- `(market_id, commodity, snapshot_date DESC)` — For price history queries
- `(snapshot_date DESC)` — For recent prices

**Retention**: Keep 3 years of historical prices for trend analysis and ML training.

---

### 8. Recommendation

**Purpose**: Generated actionable recommendations (crop, irrigation, harvest, subsidy).

**Table**: `recommendations`

| Field | Type | Nullable | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `id` | UUID | No | `gen_random_uuid()` | PK | |
| `farm_id` | UUID | No | — | FK → `farms.id` | Which farm |
| `type` | VARCHAR(50) | No | — | IN ('crop', 'irrigation', 'harvest', 'subsidy', 'action') | Category |
| `payload` | JSONB | No | — | See structure below | Structured recommendation data |
| `confidence` | INT | No | — | Check 0–100 | Confidence score |
| `sources` | JSONB | No | — | Array of {source_name, data_age_hours, confidence_contribution_pct} | Data sources used |
| `explanation` | TEXT | No | — | Max 2000 chars | Human-readable recommendation in farmer's language |
| `model_version` | VARCHAR(30) | No | — | e.g., "v1.0-mistral-7b" | Which AI model generated |
| `tool_calls` | JSONB | Yes | NULL | Array of {tool_name, inputs, outputs, execution_time_ms} | LLM tool calls made |
| `status` | VARCHAR(20) | No | 'active' | IN ('active', 'archived', 'superseded') | Lifecycle |
| `human_review_required` | BOOLEAN | No | `false` | | Flagged if confidence < threshold |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |
| `expires_at` | TIMESTAMP WITH TIME ZONE | Yes | NULL | | When recommendation becomes stale |

**Indexes**:
- `(farm_id, type, status, created_at DESC)` — For recent recommendations by type
- `(confidence DESC)` — For KPI tracking

**Payload Structure** (varies by type):

**Crop Recommendation**:
```json
{
  "recommended_crops": [
    {
      "rank": 1,
      "crop_name": "Rice (Samba)",
      "expected_yield_kg_acre": 3500,
      "expected_revenue_per_acre": 87500,
      "expected_cost_per_acre": 42000,
      "expected_profit_per_acre": 45500,
      "planting_window": {
        "start_date": "2026-06-01",
        "end_date": "2026-07-15"
      },
      "water_requirement_mm": 950,
      "risk_score": {
        "drought_risk": 0.15,
        "pest_risk": 0.22,
        "market_risk": 0.18,
        "overall": 0.18
      }
    }
  ]
}
```

**Irrigation Schedule**:
```json
{
  "irrigation_events": [
    {
      "event_date": "2026-03-01",
      "reason": "Soil moisture low at 10cm",
      "water_volume_mm": 25,
      "water_volume_liters_per_acre": 10230,
      "cost_estimate": 500,
      "rain_probability_pct": 5,
      "recommendation": "Irrigate today"
    }
  ],
  "total_water_14days_mm": 90,
  "cost_estimate_14days": 3500
}
```

**Harvest Recommendation**:
```json
{
  "harvest_status": "mature",
  "optimal_harvest_window": {
    "start_date": "2026-04-15",
    "end_date": "2026-04-25"
  },
  "sell_vs_store": {
    "recommendation": "store",
    "days_to_hold": 10,
    "expected_price_rslt_increase_pct": 22.5,
    "break_even_hold_days": 3,
    "storage_cost_per_day": 150,
    "spoilage_risk_pct": 5
  },
  "scenarios": [
    {"hold_days": 0, "expected_price": 1800, "net_revenue": 90000},
    {"hold_days": 10, "expected_price": 2205, "net_revenue": 108950}
  ]
}
```

---

### 9. SchemeMatch

**Purpose**: Government subsidy/scheme eligibility for a farm.

**Table**: `scheme_matches`

| Field | Type | Nullable | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `id` | UUID | No | `gen_random_uuid()` | PK | |
| `farm_id` | UUID | No | — | FK → `farms.id` | Which farm |
| `scheme_id` | UUID | No | — | FK → `schemes.id` | Which scheme |
| `eligibility_criteria` | JSONB | No | — | e.g., {district: "Thanjavur", land_size_max_acres: 5} | Conditions checked |
| `matched_fields` | JSONB | No | — | e.g., {district: "match", land_size: "match"} | Fields that matched |
| `overall_eligible` | BOOLEAN | No | — | | Is farm eligible? |
| `apply_link` | TEXT | Yes | NULL | | Government portal application link |
| `required_documents` | JSONB | Yes | NULL | Array e.g., ["Land deed copy", "Aadhaar"] | Documents needed |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |
| `updated_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |

**Indexes**:
- `(farm_id, overall_eligible)` — For eligible schemes by farm
- `(scheme_id)` — For scheme usage tracking

---

### 10. DataAuditLog

**Purpose**: Comprehensive audit trail of all external API calls and AI tool invocations.

**Table**: `data_audit_logs`

| Field | Type | Nullable | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `id` | BIGSERIAL | No | — | PK | |
| `source` | VARCHAR(100) | No | — | e.g., "get_market_price", "estimate_yield", "get_weather_forecast" | Which tool/API |
| `farm_id` | UUID | Yes | NULL | FK → `farms.id` | Associated farm (if applicable) |
| `request_payload` | JSONB | No | — | Complete input to tool/API | For reproducibility |
| `response_summary` | JSONB | No | — | Key outputs, not full raw response | Size-optimized |
| `status` | VARCHAR(20) | No | — | IN ('success', 'error', 'timeout') | Outcome |
| `error_message` | TEXT | Yes | NULL | If status='error', error details | For debugging |
| `execution_time_ms` | INT | No | — | Check > 0 | Latency metric |
| `cost_estimate` | DECIMAL(10, 4) | Yes | NULL | In USD | API costs (for cost tracking) |
| `data_age_hours` | INT | Yes | NULL | How fresh is the data returned? | For confidence calculation |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |

**Indexes**:
- `(source, created_at DESC)` — For source-specific audits
- `(farm_id, created_at DESC)` — For farm-specific traces
- `(status, created_at DESC)` — For error tracking

**Retention**: 90 days of raw logs; indefinite summary for compliance.

---

### 11. UserAction (Offline Queue)

**Purpose**: Queue of farmer actions created offline or during slow connectivity; sync when online.

**Table**: `user_actions`

| Field | Type | Nullable | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `id` | UUID | No | `gen_random_uuid()` | PK | |
| `user_id` | UUID | No | — | FK → `users.id` | Which farmer |
| `farm_id` | UUID | No | — | FK → `farms.id` | Which farm |
| `action_type` | VARCHAR(50) | No | — | e.g., "mark_irrigated", "note_pest_sighting" | What action |
| `action_data` | JSONB | No | — | e.g., {date: "2026-03-01", volume_mm: 25} | Action details |
| `sync_status` | VARCHAR(20) | No | 'pending' | IN ('pending', 'synced', 'failed') | Offline sync status |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | When farmer created action |
| `synced_at` | TIMESTAMP WITH TIME ZONE | Yes | NULL | | When it synced to server |
| `error_message` | TEXT | Yes | NULL | | If sync failed |

**RLS Policies**:
- Users can only CRUD their own actions

---

### 12. FarmSnapshot (Cached)

**Purpose**: Cached "Farm Snapshot" to serve <300ms responses.

**Table**: `farm_snapshots`

| Field | Type | Nullable | Default | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `id` | UUID | No | `gen_random_uuid()` | PK | |
| `farm_id` | UUID | No | — | FK → `farms.id`, UNIQUE in combination with snapshot_date | Which farm |
| `snapshot_date` | DATE | No | — | | Date of snapshot |
| `payload` | JSONB | No | — | Compiled Farm Snapshot (see below) | Pre-computed response |
| `confidence_overall` | INT | No | — | Check 0–100 | Weighted confidence |
| `sources_used` | JSONB | No | — | e.g., ["LocationProfile", "WeatherSnapshot", "VegTimeSeries"] | Which tables/APIs |
| `cache_ttl_minutes` | INT | No | 240 | Default 4 hours | How long to serve from cache |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | `now()` | | |

**Payload Structure**:
```json
{
  "farm": {
    "id": "...",
    "name": "North field",
    "area_acres": 5.2,
    "location": {
      "lat": 11.0168,
      "lon": 76.8194
    }
  },
  "soil_summary": {
    "type": "Clay-loam",
    "pH": 7.2,
    "organic_carbon_pct": 2.1,
    "status": "healthy"
  },
  "ndvi_trend": {
    "current_value": 0.68,
    "trend_7days": "increasing",
    "confidence": 0.85
  },
  "weather": {
    "current_temp_c": 28,
    "current_humidity_pct": 72,
    "forecast_7days": [...],
    "last_updated_hours_ago": 2
  },
  "nearest_mandi_price": {
    "market": "Koyambedu",
    "distance_km": 12,
    "commodity": "Rice",
    "modal_price": 1900,
    "trend_30days": "stable",
    "currency": "INR"
  },
  "top_action": {
    "priority": "high",
    "text": "Water today: Soil moisture low at 10cm",
    "reason": "Forecast shows no rain in 24h",
    "confidence": 0.92
  },
  "data_freshness": {
    "weather": "2h",
    "ndvi": "12h",
    "soil": "45d",
    "market_price": "1h"
  }
}
```

---

## Lookup / Reference Tables

### Markets

**Table**: `markets`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | INT | PK | Market ID from AGMARKNET |
| `name` | TEXT | — | e.g., "Koyambedu" |
| `district` | VARCHAR(50) | — | Tamil Nadu district |
| `location` | GEOGRAPHY(POINT, 4326) | GiST index | Market coordinates |

---

### Schemes

**Table**: `schemes`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID | PK | |
| `name` | TEXT | — | e.g., "Micro Irrigation Subsidy" |
| `description` | TEXT | — | Details of scheme |
| `eligibility_criteria` | JSONB | — | e.g., {district, land_size, crops} |
| `subsidy_amount` | DECIMAL(10, 2) | — | Max subsidy in ₹ |
| `apply_link` | TEXT | — | Government portal URL |

---

## Migration Strategy

### Phase 1: Core Tables (Week 1)
1. Create `users`, `farms`, `location_profiles`, `soil_profiles`
2. Create `weather_snapshots`, `veg_time_series`, `market_snapshots`
3. Add PostGIS extensions; enable RLS

### Phase 2: recommendations & audit (Week 2)
4. Create `recommendations`, `data_audit_logs`, `farm_snapshots`
5. Add triggers for `updated_at` columns

### Phase 3: Lookup & Offline (Week 3)
6. Populate `markets` and `schemes` reference tables
7. Create `user_actions` for offline-first support
8. Create `scheme_matches` join table

---

## Validation Rules & Constraints

| Entity | Rule | Implementation |
|--------|------|-----------------|
| **Farm** | Polygon must be valid (no self-intersections) | PostgreSQL CHECK + trigger |
| **Farm** | Area must match polygon (±5% tolerance) | Application logic + trigger |
| **Recommendation** | Confidence must be 0–100 | CHECK constraint |
| **Weather** | Temperature rational (-50 to +60°C) | CHECK constraint |
| **NDVI** | Value must be -1 to +1 | CHECK constraint |
| **Market Price** | Modal price > 0 | CHECK constraint |

---

## State Transitions

### Recommendation Status Workflow

```
active (newly created)
  ├→ superseded (newer recommendation replaces it)
  └→ archived (user dismisses)
```

### UserAction Sync Workflow

```
pending (created offline/locally)
  ├→ synced (successfully uploaded to server)
  └→ failed (retry logic implemented in UI)
```

---

## Indexes Summary

| Table | Index Columns | Type | Priority |
|-------|---------------|------|----------|
| `users` | `(email)` | UNIQUE | High |
| `farms` | `(user_id, created_at DESC)` | B-tree | High |
| `farms` | `(ST_GeomFromGeoJSON(polygon_geojson))` | GiST | High |
| `weather_snapshots` | `(farm_id, snapshot_date DESC)` | B-tree | High |
| `veg_time_series` | `(farm_id, measurement_date DESC)` | B-tree | High |
| `market_snapshots` | `(market_id, commodity, snapshot_date DESC)` | B-tree | High |
| `recommendations` | `(farm_id, type, status, created_at DESC)` | B-tree | High |
| `data_audit_logs` | `(source, created_at DESC)` | B-tree | Medium |
| `farm_snapshots` | `(farm_id, snapshot_date)` | B-tree | High |

---

## Next Steps

1. Write Supabase migration SQL files in `supabase/migrations/`
2. Add RLS policy definitions
3. Create test fixtures for Tamil Nadu pilot farms (Thanjavur, Coimbatore, Madurai)
4. Define API response contracts (see `contracts/` directory)

**Date**: 2026-02-28
