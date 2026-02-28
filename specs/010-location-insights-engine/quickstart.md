# Quick Start Guide

**Date**: 2026-02-28  
**Branch**: `010-location-insights-engine`

This guide walks you through setting up the Location-Based Insights Engine locally and generating your first recommendation in 15 minutes.

---

## Prerequisites

- **Docker Desktop** (Mac/Windows) or **Docker + Docker Compose** (Linux)
- **Git**
- Modern browser (Chrome, Firefox, Safari)
- Internet connection (for first-run data fetching)

---

## Step 1: Clone and Setup (2 minutes)

```bash
# Clone the repository
git clone https://github.com/dhanaabhirajk/farmOps.git
cd farmOps

# Check out the feature branch (if not already on it)
git checkout 010-location-insights-engine

# Create environment files
cp .env.example .env.dev
cp .env.example .env.prod

# Edit .env.dev with API keys (optional for demo, use mocked data)
# MISTRAL_API_KEY=your-key-here
# AGMARKNET_API_ENABLED=false  # Use mock data for demo
# GEE_ENABLED=false  # Use mock NDVI data for demo
```

---

## Step 2: Start Docker Compose (1 minute)

```bash
# Start all services with hot reload
docker-compose -f docker-compose.dev.yml up -d

# Verify all services are running
docker-compose -f docker-compose.dev.yml ps

# Expected output:
# NAME                COMMAND                  STATUS
# farmops-backend     uvicorn app.main:app...  Up
# farmops-frontend    node run dev...          Up
# supabase            docker-entrypoint.sh...  Up
```

**Services Started**:
- **Frontend**: http://localhost:3000 (Remix dev server with hot reload)
- **Backend API**: http://localhost:8000 (FastAPI with auto-reload)
- **Supabase PostgreSQL**: localhost:54321
- **Supabase Studio**: http://localhost:3001 (optional: inspect DB)

---

## Step 3: Verify Backend Health (1 minute)

```bash
# Check backend is responding
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "timestamp": "2026-02-28T10:30:00Z"
# }
```

If you get a connection error, wait 10-15 seconds for services to fully start.

---

## Step 4: Seed Test Farm (2 minutes)

```bash
# Run database migrations and seed with test farm
docker-compose -f docker-compose.dev.yml exec backend python -m alembic upgrade head

# Seed test data (Tamil Nadu demo farms)
docker-compose -f docker-compose.dev.yml exec backend python scripts/seed_test_data.py

# Expected output:
# Seeding test farms...
# Created farm: "Thanjavur Rice Field" (ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
# Created farm: "Coimbatore Groundnut Farm" (ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
# Created farm: "Madurai Tomato Patch" (ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
# Seeding complete!
```

**Test Farms Created**:
1. **Thanjavur Rice Field** (11.25°N, 79.15°E) — 5 acres, clay-loam soil
2. **Coimbatore Groundnut Farm** (11.00°N, 76.82°E) — 3 acres, sandy-loam soil
3. **Madurai Tomato Patch** (9.93°N, 78.12°E) — 2 acres, red soil

---

## Step 5: Open Frontend and Explore (3 minutes)

Visit http://localhost:3000 in your browser.

**You should see**:
- Login page (demo: use test email/password from seed script)
- Dashboard with 3 test farms listed
- "Farm Snapshot" button to view cached data

**Test Flow**:
1. Click "Thanjavur Rice Field"
2. Click "Farm Snapshot" → See immediate data (cached, <300ms)
3. Click "Get Recommendations" → See crop recommendation (may take 5-8s on cold-run due to AI inference)

---

## Step 6: Generate Your First Recommendation (3 minutes)

### Option A: Via Frontend (UI)

```
1. Login with test credentials
2. Select "Thanjavur Rice Field"
3. Click "Crop Recommendation" button
4. Enter season: "Samba"
5. Click "Generate"
```

**Response** (within 5-8 seconds):
```json
{
  "success": true,
  "data": {
    "recommendation_id": "rec_crop_001",
    "type": "crop",
    "confidence": 0.87,
    "payload": {
      "recommended_crops": [
        {
          "rank": 1,
          "crop_name": "Rice (Samba)",
          "expected_profit_per_acre": 45500,
          "planting_window": "2026-06-01 to 2026-07-15",
          "confidence": 0.90
        }
      ]
    },
    "explanation": "Based on your soil (clay-loam) and Thanjavur's climate, rice is optimal..."
  }
}
```

### Option B: Via API (cURL)

```bash
# Get auth token
AUTH_RESPONSE=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}')

TOKEN=$(echo $AUTH_RESPONSE | jq -r '.data.token')

# Get farm ID
FARMS_RESPONSE=$(curl http://localhost:8000/api/farms \
  -H "Authorization: Bearer $TOKEN")

FARM_ID=$(echo $FARMS_RESPONSE | jq -r '.data[0].id')

# Generate crop recommendation
curl -X POST http://localhost:8000/api/farm/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"farm_id\": \"$FARM_ID\",
    \"recommendation_type\": \"crop\",
    \"season\": \"samba\"
  }"
```

---

## Step 7: Check Logs and Audit Trail

```bash
# View backend logs
docker-compose -f docker-compose.dev.yml logs backend -f

# View frontend logs
docker-compose -f docker-compose.dev.yml logs frontend -f

# Check DataAuditLog for tool calls
curl http://localhost:8000/api/audit-logs \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

You should see entries for:
- `get_location_profile` — climate/soil data fetch
- `get_market_prices` — mandi price fetch
- `estimate_yield` — yield computation
- `estimate_profit` — profit calculation
- AI tool calls to Mistral (if enabled)

---

## Step 8: Modify Code and Test Hot Reload

### Backend Example: Modify yield calculator

```bash
# Edit backend/src/services/recommendations/yield_estimator.py

# Change yield formula or add log statement
# Save and watch uvicorn auto-reload:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

Backend reloads in ~1-2 seconds. Test by generating another recommendation.

### Frontend Example: Modify UI text

```bash
# Edit frontend/app/routes/farm.snapshot.tsx

# Change text or styling
# Watch Remix dev server rebuild and hot-reload browser
```

Remix reloads in ~200ms on save.

---

## Step 9: Run Tests

### Automated User Story Testing with Error Remediation

The project includes an automated testing workflow that:
1. Runs Playwright tests for each user story
2. Captures Docker container logs if tests fail
3. Analyzes error logs using AI
4. Attempts automatic error fixes
5. Re-runs tests to verify fixes

```bash
# Run full automated test workflow
./scripts/test-workflow.sh

# Output example:
# [1/5] Running User Story 1 tests (Farm Snapshot)...
# ✓ PASS - Farm Snapshot loads < 300ms
# 
# [2/5] Running User Story 2 tests (Crop Recommendation)...
# ✗ FAIL - TypeError: Cannot read property 'profit_per_acre'
# 
# Capturing Docker logs...
# Backend logs: /tmp/test-logs/backend-20260228-103000.log
# Frontend logs: /tmp/test-logs/frontend-20260228-103000.log
# 
# Analyzing errors with AI...
# Error identified: Missing field in API response schema
# Suggested fix: Update RecommendationPayload schema in backend/src/models/recommendation.py
# 
# Applying fix...
# ✓ Fix applied
# 
# Re-running tests...
# ✓ PASS - Crop Recommendation returns valid payload
```

### Manual Test Commands

```bash
# Backend unit tests
docker-compose -f docker-compose.dev.yml exec backend pytest tests/unit/ -v

# Backend integration tests
docker-compose -f docker-compose.dev.yml exec backend pytest tests/integration/ -v

# Frontend E2E tests (Playwright) - all user stories
docker-compose -f docker-compose.dev.yml exec frontend npm run test:e2e

# Run specific user story test
docker-compose -f docker-compose.dev.yml exec frontend npm run test:e2e -- --grep "User Story 1"

# Run tests with Docker log capture (on failure only)
docker-compose -f docker-compose.dev.yml exec frontend npm run test:e2e:with-logs
```

**Expected Results**:
- Unit tests: 20+ tests pass in ~5 seconds
- Integration tests: 10+ tests pass in ~15 seconds
- E2E tests: 5+ user story scenarios pass in ~30 seconds

### Docker Log Capture on Test Failure

When a Playwright test fails, logs are automatically captured:

```bash
# Manually capture logs
./scripts/docker-log-capture.sh

# Logs saved to:
# - backend-YYYYMMDD-HHMMSS.log
# - frontend-YYYYMMDD-HHMMSS.log
# - supabase-YYYYMMDD-HHMMSS.log
```

### Auto-Fix Workflow

The auto-fix system uses AI to analyze Docker logs and suggest fixes:

```typescript
// frontend/tests/utils/auto-fix.ts
import { analyzeLogsAndFix } from './auto-fix';

test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== 'passed') {
    // Capture Docker logs
    const logs = await captureDockerLogs();
    
    // Analyze and attempt fix
    const fixResult = await analyzeLogsAndFix(logs, testInfo.error);
    
    if (fixResult.fixed) {
      console.log('Auto-fix applied:', fixResult.description);
      // Re-run test
      await test.step('Re-running after auto-fix', async () => {
        await page.reload();
        // Test assertions...
      });
    }
  }
});
```

**Auto-Fix Capabilities**:
- Missing environment variables → Add to `.env.dev`
- Database connection errors → Restart Supabase container
- Port conflicts → Detect and kill conflicting processes
- Missing dependencies → Install via `npm install` or `pip install`
- Schema mismatches → Update model definitions
- API endpoint errors → Fix route handlers based on error stack traces

**Limitations**:
- Complex logic errors require manual intervention
- Auto-fix success rate: ~70% for common infrastructure issues
- All fixes logged to `test-results/auto-fix-log.json` for review

---

## Step 10: Stop Services

```bash
# Stop all services (data persisted in Docker volumes)
docker-compose -f docker-compose.dev.yml down

# Stop and clear data
docker-compose -f docker-compose.dev.yml down -v

# View logs before stopping (useful for debugging)
docker-compose -f docker-compose.dev.yml logs --tail=50
```

---

## Troubleshooting

### Port Already in Use

```bash
# If port 3000 or 8000 already in use:
docker-compose -f docker-compose.dev.yml down
lsof -i :3000  # Find process using port 3000
kill -9 <PID>
docker-compose -f docker-compose.dev.yml up
```

### Services Not Starting

```bash
# Check Docker daemon is running
docker ps

# If error, restart Docker:
# - Mac: Docker menu → Restart
# - Linux: sudo systemctl restart docker

# Check logs for errors:
docker-compose -f docker-compose.dev.yml logs
```

### Database Connection Errors

```bash
# Re-initialize database
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up
```

### API Returns 503 (External Service Down)

- Graceful degradation: Recommendation uses fallback data
- Check `data_freshness` field in response to see data age
- In demo mode, uses mocked data (no real API calls)

### Slow Recommendation Generation (>10s)

- First recommendation involves remote AI calls (5-8s is normal)
- Subsequent recommendations use cached results (<300ms)
- Check `docker-compose logs backend` for LLM call timing

---

## Demo Mode (No API Keys Required)

By default, the dev environment uses **mocked data** for:
- Satellite NDVI (synthetic time-series)
- Weather forecasts (IMD mock, ±2°C variation)
- Market prices (AGMARKNET mock, ±5% variance)
- AI recommendations (cached Mistral responses)

This allows full local development without external API keys.

**To enable real APIs**, update `.env.dev`:

```bash
MISTRAL_API_KEY=your-actual-key
GEE_ENABLED=true
AGMARKNET_ENABLED=true
WEATHER_API_ENABLED=true
```

---

## Project Structure Overview

```
farmOps/
├── backend/
│   ├── src/
│   │   ├── models/          # Database ORM
│   │   ├── services/        # Business logic
│   │   │   ├── location/
│   │   │   ├── satellite/
│   │   │   ├── weather/
│   │   │   ├── market/
│   │   │   ├── ai_tools/
│   │   │   └── recommendations/
│   │   └── api/             # FastAPI routes
│   ├── tests/               # Unit & integration tests
│   └── pyproject.toml       # uv dependencies
│
├── frontend/
│   ├── app/
│   │   ├── components/      # Reusable UI components
│   │   ├── routes/          # Remix routes
│   │   └── services/        # API client
│   └── tests/               # Playwright E2E tests
│
├── supabase/
│   ├── migrations/          # Database schema
│   └── seed.sql             # Test data
│
├── .specify/                # Specify framework
├── specs/010-location-.../ # This planning document
│
├── docker-compose.dev.yml   # Development compose
├── docker-compose.prod.yml  # Production compose
├── Dockerfile.backend       # Backend build
├── Dockerfile.frontend      # Frontend build
└── README.md
```

---

## Next Steps

1. **Customize Test Farms**: Edit `scripts/seed_test_data.py` to add your own farm polygon
2. **Integrate Real APIs**: Add Google Earth Engine, IMD, AGMARKNET API keys
3. **Develop Features**: Use hot reload to rapidly iterate on recommendations
4. **Run Full Test Suite**: `docker-compose exec backend pytest` before pushing code
5. **Deploy to Production**: Use `docker-compose.prod.yml` for optimized builds

---

## Performance Tips

- **Cached Snapshots** (<300ms): Farm Snapshot uses 4-hour TTL. Hit "Refresh" to force cold-run.
- **Parallel Data Fetching**: Backend fetches weather, NDVI, prices in parallel (not sequential).
- **LLM Tool Caching**: Repeated tool calls with same inputs cached (5-minute TTL).
- **Frontend Bundling**: Remix builds are incremental (2-100ms depending on change scope).

---

## Support & Documentation

- **Backend API Docs**: http://localhost:8000/docs (auto-generated by FastAPI)
- **Data Model**: See `data-model.md` for complete schema
- **API Contracts**: See `contracts/api-responses.md` for response schemas
- **LLM Tools**: See `contracts/llm-tools.md` for AI tool definitions
- **Research**: See `research.md` for technology choices and rationale

---

**You're all set! 🚀 Happy farming! 🌾**
