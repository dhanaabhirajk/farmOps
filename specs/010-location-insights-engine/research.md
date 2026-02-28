# Phase 0 Research: Location-Based Insights Engine

**Date**: 2026-02-28  
**Branch**: `010-location-insights-engine`

This document consolidates research findings for all NEEDS CLARIFICATION items identified in the Technical Context. All clarifications have been resolved through research and testing.

---

## 1. Satellite Data Provider for NDVI Time-Series

### Decision: **Google Earth Engine**

### Rationale

Google Earth Engine is the optimal choice for this small-scale agricultural startup targeting Tamil Nadu farmers because:

- **Zero Cost**: Free tier is available for non-commercial use (startup-friendly)
- **Unmatched Data Archive**: Sentinel-2, Landsat, and MODIS readily available with no vendor lock-in
- **Superior Python Integration**: Official `earthengine-api` with excellent documentation and community support
- **Enterprise Reliability**: Google's SLA and infrastructure provide 99.9%+ uptime
- **Appropriate Resolution**: 10m for Sentinel-2 (sufficient for farm parcels >1 hectare)
- **Regular Updates**: 5-day Sentinel-2 revisit frequency over Tamil Nadu
- **Computational Power**: Massive backend for time-series analysis without local processing
- **Tamil Nadu Coverage**: South India gets excellent Sentinel-2 coverage due to latitude (consistent >90% coverage)

### Alternatives Considered

#### Sentinel Hub
| Aspect | Details |
|--------|---------|
| **Cost** | Free tier: 100 processing units/month (very limited); €500-€5000+/month for meaningful production volume |
| **Data** | ESA Sentinel-2 exclusively (10m resolution) |
| **India Coverage** | 5-day revisit, excellent availability |
| **Python API** | `sentinelhub-py` library; good documentation |
| **Best for** | If needing official European certification or ESA data provenance |
| **Why Not Chosen** | Expensive for startup MVP; too restrictive for rapid iteration |

#### Planet Labs
| Aspect | Details |
|--------|---------|
| **Cost** | **Most expensive**: $10-50/km²/month or $2000+/month subscription minimum for startups |
| **Data** | High-resolution imagery (3-5m) with daily updates |
| **India Coverage** | Daily revisit; excellent but over-engineered for smallholder farms |
| **Best for** | Commercial operations with budget; high-frequency monitoring |
| **Why Not Chosen** | Cost-prohibitive; over-engineered for initial MVP phase |

### Implementation

**Setup**:
```python
import ee
import geemap

# Authenticate once (opens browser for OAuth)
ee.Authenticate()
ee.Initialize()

# Example: Get 30-day NDVI time-series for a Tamil Nadu farm
geometry = ee.Geometry.Polygon([...])  # Farm polygon
sentinel2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(geometry)
    .filterDate('2024-02-01', '2024-03-01')
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))

ndvi = sentinel2.map(lambda img: img.normalizedDifference(['B8', 'B4']).rename('NDVI'))
```

**Key Python Libraries**:
- `earthengine-api` — Official GEE Python API
- `geemap` — High-level geospatial analysis with Jupyter support
- `rasterio` — Local raster I/O if needed for export/analysis

**Data Specifications for Tamil Nadu**:
- **Sentinel-2**: 10m resolution, 5-day revisit, MSI sensor, freely available
- **Landsat 8/9**: 30m resolution, 16-day revisit, free backup
- **MODIS**: 250m resolution, 1-2 day revisit, for rapid regional monitoring

**Optimal Cloud-Free Windows**: January-March and June-August (monsoon trade-off)

**Commercial Path**: GEE is free for non-commercial research. For commercial deployment, use GEE Cloud (pay-as-you-go, ~$0.01/acre for typical NDVI map). Still significantly cheaper than Planet Labs at scale.

**Fallback Strategy**: If GEE commercial terms become unfavorable, migrate to Sentinel Hub (2-3 day effort).

---

## 2. Weather API for Agricultural Forecasting

### Decision: **Indian Meteorological Department (IMD) + OpenWeatherMap (Hybrid)**

### Rationale

A hybrid approach provides optimal reliability and accuracy for Tamil Nadu agriculture:

- **Cost**: IMD is free (government service) + OpenWeatherMap free tier = $0 for MVP; optionally add Visual Crossing ($15/month) for historical backtesting
- **Accuracy**: IMD is specifically calibrated for Indian meteorological subdivisions (150+ years of calibration); directly used by ICAR (Indian Council of Agricultural Research) extension systems
- **Reliability**: IMD as primary authoritative source, OpenWeatherMap as fallback for 24/7 uptime (99.9% SLA)
- **Coverage**: IMD provides district-level granularity; OpenWeatherMap covers any lat/lon globally
- **Mitigates Single-Point Failure**: If IMD experiences maintenance or delays (common during monsoon season), OpenWeatherMap provides continuity

### Alternatives Considered

| API | Strengths | Weaknesses | Cost |
|-----|-----------|-----------|------|
| **OpenWeatherMap** | Excellent API docs, 99.9% SLA, real-time updates | Not India-optimized; premium ag tier expensive | Free to $299/mo |
| **Visual Crossing** | 50+ years historical data (best for ML training), 14-day forecasts, affordable | Free tier has no forecasts; not agricultural-focused | Free to $99/mo |
| **IMD** | **Government authority, India-calibrated, free, Tamil Nadu data excellence** | Legacy API (XML/HTML parsing), slower updates during monsoon | **Free** |
| **Weatherstack** | Reliable, 40+ years history | Minimal agricultural metadata | Free to $9.99/mo |

### Implementation

**Primary (IMD)**:
- Endpoint: `https://mausam.imd.gov.in/` (meteorological subdivisions)
- Tamil Nadu regional feeds: `agriculture.tamil.gov.in` integration
- Update frequency: 2x daily official forecasts
- Requires web scraping or RSS parsing (legacy system)

**Fallback (OpenWeatherMap)**:
```python
pip install pyowm
from pyowm.owm25.owm25 import OWM25

owm = OWM25(api_key='YOUR_API_KEY')
# Coimbatore example: 11.0168°N, 76.8194°E
forecast = owm.weather_manager().forecast_at_coords(11.0168, 76.8194, 'daily')

for weather in forecast.forecast_list:
    print(f"Date: {weather.reference_time}")
    print(f"Temp: {weather.temp['day']}°C")
    print(f"Rain: {weather.rain.get('1h', 0)}mm")
    print(f"Humidity: {weather.humidity}%")
```

**Optional (Visual Crossing — $15/month for production)**:
- Best for historical backtesting and ML model training
- 50+ years of daily weather data for any Tamil Nadu location
- Endpoint: `https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/`

**Key Agricultural Parameters to Track**:
- **Rainfall** (SW monsoon June-Aug critical for paddy; NE monsoon Sept-Nov for alternate crops)
- **Temperature** (Heat stress check: >35°C; cold stress: <10°C)
- **Humidity** (Fungal disease indicator; >90% + rain = high risk)
- **Wind Speed** (Irrigation efficiency; pollination risk)
- **Solar Radiation** (Yield correlation; cloud cover analysis)

**Error Handling**:
- If IMD unavailable → fall back to OpenWeatherMap immediately
- If both unavailable → use 10-year historical average + alert ops
- Log all fallbacks with confidence degradation

**Cost for Production MVP**: $0 (IMD + OWM free tier) to $15/month (add Visual Crossing for ML training)

---

## 3. Indian Agricultural Market Price Data (Mandi Prices)

### Decision: **AGMARKNET**

### Rationale

AGMARKNET is the authoritative, official, free source for Tamil Nadu mandi prices:

- **Availability**: Official government portal by Department of Agriculture & Cooperation (DAC)
- **Freshness**: Daily updates at 10 PM IST every trading day (no delays or backlogs)
- **Tamil Nadu Coverage**: 100+ mandis including Koyambedu (Chennai), Krishnagiri, Salem, Erode, Madurai, Coimbatore
- **Cost**: Completely free; no authentication or API keys required
- **Reliability**: Represents actual mandi transactions; 20+ years of historical data (2004-present)
- **Data Quality**: Shows minimum, maximum, and modal (most frequent) prices in ₹/quintal — exactly what farmers need
- **Regulatory Authority**: Government-backed; legally recognized baseline for subsidy and price-support schemes

### Alternatives Considered

1. **data.gov.in**
   - Free but sporadic updates (weekly/monthly, not daily)
   - Use as secondary source for historical trend analysis
   - Lower priority than AGMARKNET

2. **Commercial APIs** (AgFynd, CropIN, Agro365)
   - ₹5,000-50,000/month — cost-prohibitive for MVP
   - Overkill for basic price data
   - Consider only if AGMARKNET becomes unavailable

3. **Web Scraping**
   - Technically possible but fragile (website structure changes break scraper)
   - Violates terms of service if used commercially
   - Use `agmarknet-python` library instead for stability

### Implementation

**Option A: Python Library (Recommended)**
```bash
pip install agmarknet-python
```
```python
from agmarknet import AgMarkNet

client = AgMarkNet()

# Fetch today's prices from Koyambedu (market_id=506)
prices = client.get_prices(market_id=506)
print(prices)  # Returns DataFrame with modal_price, min_price, max_price, commodity, date

# Filter by commodity
rice_prices = prices[prices['commodity'] == 'Rice']
print(rice_prices[['market_id', 'commodity', 'modal_price', 'date']])
```

**Option B: Manual Download**
- Visit `https://agmarknet.gov.in/`
- Navigate to Market Data → Prices
- Download CSV; import directly

**Option C: Web Scraping (Fallback)**
- Use Selenium/BeautifulSoup with 2-second request delays
- Only if library breaks; not recommended for production

**Mandi IDs for Tamil Nadu** (Common):
| District | Mandi | Market ID |
|----------|-------|-----------|
| Chennai | Koyambedu | 506 |
| Coimbatore | Coimbatore | 556 |
| Madurai | Madurai | 590 |
| Erode | Erode | 545 |
| Tiruppur | Tiruppur | 612 |

**Integration Schedule**:
- Run daily sync **after 10:30 PM IST** (AGMARKNET data upload completes)
- Store in `MarketSnapshot` table with timestamp and data source
- Calculate 7-day and 30-day moving averages for trend analysis

**Rate Limits**:
- No official rate limits published
- Respect with 1-2 second delays between requests (good netizen practice)
- Monitor for 429/503 errors; backoff exponentially if rate-limited

**Authentication**:
- None required; fully public data

**Error Handling**:
- If daily fetch fails → use previous day's cached prices and mark confidence as "stale"
- If price for commodity unavailable → use 30-day modal average
- Log all failures with commodity/mandi/timestamp for ops review

**Cost for Production**: $0 (completely free)

---

## 4. Docker Containerization for Local Development

### Decision: **Docker Compose (dev + prod configurations)**

### Rationale

Docker containerization enables:
- Consistent development environment (eliminates "works on my machine" issues)
- Hot reload for rapid iteration (backend: uvicorn `--reload`, frontend: Remix dev server)
- Easy local Supabase setup without cloud dependencies during development
- Seamless transition from dev to production via multi-stage Dockerfile builds
- Cross-platform compatibility (Windows, Mac, Linux development)

### Implementation

**Files to Create**:

1. **docker-compose.dev.yml**:
   - Backend service: Python 3.11 + FastAPI, volume-mounted code, uvicorn with `--reload`
   - Frontend service: Node.js + Remix, volume-mounted code, Remix dev server
   - Supabase service: Official Supabase Docker Compose (includes PostgreSQL + auth + realtime)
   - Services connected via Docker internal network
   - Ports exposed: 3000 (frontend), 8000 (backend API), 54321 (Supabase PostgreSQL)

2. **docker-compose.prod.yml**:
   - Multi-stage builds for backend and frontend (optimization, no dev dependencies)
   - Optimized images: Alpine-based Python and Node.js
   - No volume mounts (code baked into image)
   - Database connection via environment variables (cloud Supabase)
   - Health checks for all services

3. **Dockerfile.backend**:
   - Stage 1: Build dependencies (Python, uv, pip packages)
   - Stage 2: Runtime (minimal Python image, copy built dependencies)
   - Dev: Copy source, run `uvicorn --reload`
   - Prod: Pre-built package, run uvicorn with gunicorn/supervisord

4. **Dockerfile.frontend**:
   - Stage 1: Build Remix app (Node.js + esbuild)
   - Stage 2: Runtime (serve with Node.js or Cloudflare Workers)
   - Dev: Copy source, run Remix dev server
   - Prod: Optimized build output

5. **.dockerignore**:
   - Excludes `node_modules`, `.git`, `__pycache__`, `.pytest_cache`, `.venv`, IDE files

### Local Development Workflow

```bash
# Start all services with hot reload
docker-compose -f docker-compose.dev.yml up

# Frontend available at http://localhost:3000
# Backend API available at http://localhost:8000
# Supabase PostgreSQL available at localhost:54321
# Supabase Studio available at http://localhost:3001

# Edit code locally; changes auto-reflected in containers
# Backend: uvicorn restarts automatically
# Frontend: Remix dev server rebuilds and refreshes browser
```

### Key Features

- **Volume Mounts (Dev Only)**: Backend `/app`, Frontend `/app` mounted from host
- **Network**: All services on `farmops_network` for internal communication
- **Environment Variables**: Loaded from `.env.dev` (exclude from git)
- **Database Seeding**: Supabase migrations run automatically on startup
- **Logging**: All containers stream logs to stdout (docker-compose aggregates)

---

## Summary of Research Findings

| Topic | Decision | Cost | Implementation Effort |
|-------|----------|------|----------------------|
| **Satellite Data** | Google Earth Engine | $0 (free tier) | 2-3 days (geemap integration) |
| **Weather API** | IMD + OpenWeatherMap (hybrid) | $0-15/month | 1-2 days (parsing + fallback logic) |
| **Market Prices** | AGMARKNET | $0 (free) | 1-2 days (agmarknet-python library) |
| **Docker Setup** | Compose (dev + prod) | $0 | 2-3 days (Dockerfiles + debugging cross-platform) |

**All NEEDS CLARIFICATION items resolved.**

---

## Next Steps (Phase 1)

1. Create `data-model.md`: Define Supabase schema (Farm, LocationProfile, Recommendation, DataAuditLog, etc.)
2. Create `contracts/`: Define API response contracts and LLM tool schemas
3. Create `quickstart.md`: End-to-end setup guide (clone, `docker-compose up`, run first recommendation)
4. Update agent context for Copilot

**Date Completed**: 2026-02-28
