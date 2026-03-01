# Tasks: Location-Based Insights Engine

**Feature**: Location-Based Insights Engine for Tamil Nadu Farmers  
**Branch**: `010-location-insights-engine`  
**Input**: Design documents from `/specs/010-location-insights-engine/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Implementation Strategy**: This feature has 5 user stories organized by priority. User Story 1 and 2 (P1) form the MVP. Each user story is independently testable and can be deployed as an increment.

**Tests**: Included (automated Playwright testing per user story as specified in plan.md constraints)

---

## Task Format

Every task follows: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Task can run in parallel (different files, no blocking dependencies)
- **[Story]**: User story label (US1, US2, US3, US4, US5) - only for user story phases
- **File paths**: Use repository structure from plan.md (backend/, frontend/, supabase/)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, Docker environment, and dependency management

- [X] T001 Initialize backend Python project with uv package manager in backend/
- [X] T002 [P] Initialize frontend Remix project with TypeScript in frontend/
- [X] T003 [P] Create docker-compose.dev.yml with services: backend, frontend, supabase
- [X] T004 [P] Create docker-compose.prod.yml with optimized multi-stage builds
- [X] T005 [P] Create Dockerfile.backend with Python 3.11+ and FastAPI dependencies
- [X] T006 [P] Create Dockerfile.frontend with Node.js and Remix build
- [X] T007 [P] Create .env.dev with mock environment variables (no API keys required)
- [X] T008 [P] Create .env.example documenting all required environment variables
- [X] T009 [P] Configure backend linting (ruff, mypy) in backend/pyproject.toml
- [X] T010 [P] Configure frontend linting (ESLint, Prettier) in frontend/.eslintrc.js
- [X] T011 Install Python dependencies: fastapi, uvicorn, supabase-py, shapely, rasterio, earthengine-api in backend/
- [X] T012 [P] Install frontend dependencies: remix, react, tailwindcss in frontend/
- [X] T013 [P] Setup Cloudflare configuration in wrangler.toml for Pages deployment
- [X] T014 [P] Create scripts/docker-log-capture.sh for test error logging
- [X] T015 [P] Create scripts/test-workflow.sh for automated Playwright test orchestration
- [X] T016 [P] Create .github/workflows/test-user-stories.yml for CI testing pipeline
- [X] T017 [P] Create .github/workflows/deploy.yml for Cloudflare deployment
- [X] T018 Create README.md with project overview and quickstart reference
- [X] T019 [P] Setup backend hot reload configuration (uvicorn --reload) in docker-compose.dev.yml
- [X] T020 [P] Setup frontend hot reload configuration (Remix dev mode) in docker-compose.dev.yml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Foundation

- [X] T021 Initialize Supabase migrations in supabase/migrations/
- [X] T022 [P] Create migration for users table with RLS policies in supabase/migrations/001_users.sql
- [X] T023 [P] Create migration for farms table with PostGIS support in supabase/migrations/002_farms.sql
- [X] T024 [P] Create migration for data_audit_logs table in supabase/migrations/003_data_audit_logs.sql
- [X] T025 Create migration for user_actions table (offline queue) in supabase/migrations/004_user_actions.sql
- [X] T026 Create seed data with 3 test farms (Thanjavur, Coimbatore, Madurai) in supabase/seed.sql

### Backend Foundation

- [X] T027 Create base SQLAlchemy models in backend/src/models/base.py
- [X] T028 [P] Create User model in backend/src/models/user.py
- [X] T029 [P] Create Farm model with PostGIS geometry support in backend/src/models/farm.py
- [X] T030 [P] Create DataAuditLog model in backend/src/models/data_audit_log.py
- [X] T031 Create Supabase client initialization in backend/src/db/supabase_client.py
- [X] T032 Create audit logging service in backend/src/services/audit/audit_logger.py
- [X] T033 [P] Create geospatial utilities (S2/H3 tiling, polygon validation) in backend/src/utils/geospatial.py
- [X] T034 [P] Create rate limiting middleware in backend/src/middleware/rate_limiter.py
- [X] T035 [P] Create error handling middleware in backend/src/middleware/error_handler.py
- [X] T036 Create API router initialization in backend/src/api/__init__.py
- [X] T037 Create FastAPI app initialization with middleware in backend/src/main.py

### AI Foundation

- [X] T038 Create Mistral client initialization (OpenAI-compatible) in backend/src/services/ai/mistral_client.py
- [X] T039 Create base LLM tool definition framework in backend/src/services/ai/tool_registry.py
- [X] T040 Create tool execution wrapper with audit logging in backend/src/services/ai/tool_executor.py

### Frontend Foundation

- [X] T041 Create Remix root layout with responsive design in frontend/app/root.tsx
- [X] T042 [P] Configure Tailwind CSS with custom theme in frontend/tailwind.config.ts
- [X] T043 [P] Create Supabase auth context in frontend/app/contexts/auth.tsx
- [X] T044 [P] Create API client utilities in frontend/app/utils/api-client.ts
- [X] T045 [P] Create common UI components (Button, Card, Loading) in frontend/app/components/ui/
- [X] T046 Create error boundary component in frontend/app/components/ErrorBoundary.tsx

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Farm Snapshot (Priority: P1) 🎯 MVP

**Goal**: Farmer selects farm on map; system returns instant snapshot with location, soil, weather, NDVI, mandi prices, and top recommended action (<300ms cached, <8s cold).

**Independent Test**: Provide test farm polygon (Thanjavur rice field). Verify snapshot displays all fields within SLA, includes confidence scores, and shows prioritized action card.

### Database for User Story 1

- [X] T047 [P] [US1] Create migration for location_profiles table in supabase/migrations/005_location_profiles.sql
- [X] T048 [P] [US1] Create migration for soil_profiles table in supabase/migrations/006_soil_profiles.sql
- [X] T049 [P] [US1] Create migration for weather_snapshots table in supabase/migrations/007_weather_snapshots.sql
- [X] T050 [P] [US1] Create migration for veg_timeseries table (NDVI) in supabase/migrations/008_veg_timeseries.sql
- [X] T051 [P] [US1] Create migration for market_snapshots table in supabase/migrations/009_market_snapshots.sql
- [X] T052 [P] [US1] Create migration for farm_snapshots table (cache) in supabase/migrations/010_farm_snapshots.sql

### Backend Models for User Story 1

- [X] T053 [P] [US1] Create LocationProfile model in backend/src/models/location_profile.py
- [X] T054 [P] [US1] Create SoilProfile model in backend/src/models/soil_profile.py
- [X] T055 [P] [US1] Create WeatherSnapshot model in backend/src/models/weather_snapshot.py
- [X] T056 [P] [US1] Create VegTimeSeries model in backend/src/models/veg_timeseries.py
- [X] T057 [P] [US1] Create MarketSnapshot model in backend/src/models/market_snapshot.py
- [X] T058 [P] [US1] Create FarmSnapshot model in backend/src/models/farm_snapshot.py

### Backend Services - Data Fetching for User Story 1

- [X] T059 [P] [US1] Implement Google Earth Engine integration in backend/src/services/satellite/gee_client.py
- [X] T060 [P] [US1] Implement NDVI time-series fetcher in backend/src/services/satellite/ndvi_fetcher.py
- [X] T061 [P] [US1] Implement IMD weather client in backend/src/services/weather/imd_client.py
- [X] T062 [P] [US1] Implement OpenWeatherMap fallback client in backend/src/services/weather/openweather_client.py
- [X] T063 [US1] Implement weather service coordinator (IMD + fallback) in backend/src/services/weather/weather_service.py
- [X] T064 [P] [US1] Implement AGMARKNET mandi price client in backend/src/services/market/agmarknet_client.py
- [X] T065 [US1] Implement market price service with caching in backend/src/services/market/market_service.py
- [X] T066 [P] [US1] Implement location profile service (climate, soil, elevation) in backend/src/services/location/location_service.py
- [X] T067 [P] [US1] Implement soil profile service in backend/src/services/location/soil_service.py

### Backend LLM Tools for User Story 1

- [X] T068 [P] [US1] Implement get_location_profile tool in backend/src/services/ai_tools/get_location_profile.py
- [X] T069 [P] [US1] Implement get_soil_profile tool in backend/src/services/ai_tools/get_soil_profile.py
- [X] T070 [P] [US1] Implement get_ndvi_timeseries tool in backend/src/services/ai_tools/get_ndvi_timeseries.py
- [X] T071 [P] [US1] Implement get_weather_forecast tool in backend/src/services/ai_tools/get_weather_forecast.py
- [X] T072 [P] [US1] Implement get_market_prices tool in backend/src/services/ai_tools/get_market_prices.py
- [X] T073 Register User Story 1 tools in tool registry in backend/src/services/ai/tool_registry.py

### Backend API for User Story 1

- [X] T074 [US1] Implement farm snapshot generator service in backend/src/services/snapshot/snapshot_generator.py
- [X] T075 [US1] Implement GET /api/farm/snapshot endpoint in backend/src/api/routes/farm.py
- [X] T076 [US1] Add snapshot caching logic (4-hour TTL) in backend/src/services/snapshot/snapshot_cache.py
- [X] T077 [US1] Add validation and error handling for snapshot endpoint in backend/src/api/routes/farm.py

### Frontend UI for User Story 1

- [X] T078 [P] [US1] Create FarmSelector component (map interface) in frontend/app/components/FarmSelector.tsx
- [X] T079 [P] [US1] Create FarmSnapshotCard component in frontend/app/components/FarmSnapshotCard.tsx
- [X] T080 [P] [US1] Create SoilSummary component in frontend/app/components/snapshot/SoilSummary.tsx
- [X] T081 [P] [US1] Create NDVITrend component with chart in frontend/app/components/snapshot/NDVITrend.tsx
- [X] T082 [P] [US1] Create WeatherForecast component in frontend/app/components/snapshot/WeatherForecast.tsx
- [X] T083 [P] [US1] Create MandiPrice component in frontend/app/components/snapshot/MandiPrice.tsx
- [X] T084 [P] [US1] Create TopActionCard component in frontend/app/components/snapshot/TopActionCard.tsx
- [X] T085 [US1] Create farm snapshot page route in frontend/app/routes/farm.$farmId.snapshot.tsx
- [X] T086 [US1] Add snapshot loading states and error handling in frontend/app/routes/farm.$farmId.snapshot.tsx

### Tests for User Story 1

- [X] T087 [P] [US1] Backend unit test for NDVI fetcher in backend/tests/unit/test_ndvi_fetcher.py
- [X] T088 [P] [US1] Backend unit test for weather service in backend/tests/unit/test_weather_service.py
- [X] T089 [P] [US1] Backend unit test for market service in backend/tests/unit/test_market_service.py
- [X] T090 [P] [US1] Backend integration test for snapshot generator in backend/tests/integration/test_snapshot_generator.py
- [X] T091 [P] [US1] Backend API test for /api/farm/snapshot in backend/tests/api/test_farm_snapshot.py
- [X] T092 [US1] Playwright E2E test for User Story 1 in frontend/tests/e2e/user-story-1.spec.ts
- [X] T093 [US1] Add Docker log capture utility for test failures in frontend/tests/utils/docker-logs.ts
- [X] T094 [US1] Add AI-powered auto-fix utility in frontend/tests/utils/auto-fix.ts

**Checkpoint**: User Story 1 (Farm Snapshot) is complete and independently testable. This forms the first half of the MVP.

---

## Phase 4: User Story 2 - Crop Recommendation (Priority: P1) 🎯 MVP

**Goal**: Farmer asks "What should I plant this season?" System returns 3 ranked crops with yield, profit, planting window, water needs, and risk score (<10s cold, <2s cached).

**Independent Test**: For Thanjavur farm in Samba season, verify 3 crop recommendations with profit estimates, planting dates, and risk reasoning. Validate recommendations avoid high-water crops in groundwater-scarce zones unless subsidy eligibility shown.

### Database for User Story 2

- [X] T095 [US2] Create migration for recommendations table in supabase/migrations/011_recommendations.sql
- [X] T096 [P] [US2] Create indexes for recommendations (farm_id, type, created_at) in supabase/migrations/011_recommendations.sql

### Backend Models for User Story 2

- [X] T097 [US2] Create Recommendation model in backend/src/models/recommendation.py
- [ ] T098 [US2] Create RecommendationPayload schema in backend/src/models/schemas/recommendation_payload.py

### Backend LLM Tools for User Story 2

- [X] T099 [P] [US2] Implement estimate_yield tool in backend/src/services/ai_tools/estimate_yield.py
- [X] T100 [P] [US2] Implement estimate_production_cost tool in backend/src/services/ai_tools/estimate_production_cost.py
- [X] T101 [P] [US2] Implement estimate_risk_score tool in backend/src/services/ai_tools/estimate_risk_score.py
- [X] T102 [P] [US2] Implement estimate_profit tool in backend/src/services/ai_tools/estimate_profit.py
- [ ] T103 Register User Story 2 tools in tool registry in backend/src/services/ai/tool_registry.py

### Backend Services for User Story 2

- [X] T104 [US2] Implement crop knowledge base (planting calendars, water needs) in backend/src/services/recommendations/crop_knowledge.py
- [X] T105 [US2] Implement crop recommendation engine in backend/src/services/recommendations/crop_recommender.py
- [X] T106 [US2] Implement recommendation caching service in backend/src/services/recommendations/recommendation_cache.py

### Backend API for User Story 2

- [ ] T107 [US2] Implement POST /api/farm/recommendations endpoint in backend/src/api/routes/recommendations.py
- [ ] T108 [US2] Implement GET /api/farm/recommendations endpoint (retrieve historical) in backend/src/api/routes/recommendations.py
- [ ] T109 [US2] Add validation for recommendation requests in backend/src/api/routes/recommendations.py

### Frontend UI for User Story 2

- [ ] T110 [P] [US2] Create CropRecommendationCard component in frontend/app/components/recommendations/CropRecommendationCard.tsx
- [ ] T111 [P] [US2] Create RiskScoreIndicator component in frontend/app/components/recommendations/RiskScoreIndicator.tsx
- [ ] T112 [P] [US2] Create PlantingWindowCalendar component in frontend/app/components/recommendations/PlantingWindowCalendar.tsx
- [ ] T113 [P] [US2] Create ProfitBreakdown component in frontend/app/components/recommendations/ProfitBreakdown.tsx
- [ ] T114 [P] [US2] Create ConfidenceBar component in frontend/app/components/recommendations/ConfidenceBar.tsx
- [ ] T115 [US2] Create crop recommendation page route in frontend/app/routes/farm.$farmId.recommendations.tsx
- [ ] T116 [US2] Add recommendation request form (season selection) in frontend/app/routes/farm.$farmId.recommendations.tsx

### Tests for User Story 2

- [ ] T117 [P] [US2] Backend unit test for yield estimator in backend/tests/unit/test_estimate_yield.py
- [ ] T118 [P] [US2] Backend unit test for profit calculator in backend/tests/unit/test_estimate_profit.py
- [ ] T119 [P] [US2] Backend unit test for risk scorer in backend/tests/unit/test_estimate_risk_score.py
- [ ] T120 [P] [US2] Backend integration test for crop recommender in backend/tests/integration/test_crop_recommender.py
- [ ] T121 [P] [US2] Backend API test for /api/farm/recommendations in backend/tests/api/test_recommendations.py
- [ ] T122 [US2] Playwright E2E test for User Story 2 in frontend/tests/e2e/user-story-2.spec.ts

**Checkpoint**: User Story 2 (Crop Recommendation) is complete. MVP is now fully functional (US1 + US2).

---

## Phase 5: User Story 3 - Irrigation Scheduling (Priority: P2)

**Goal**: Generate 14-day irrigation schedule based on soil moisture, crop stage, and weather forecast (respects rain probability >70% to skip irrigation).

**Independent Test**: Mock soil moisture = low. Verify irrigation action within 24 hours with volume estimate and cost. Test that heavy rain forecast (>70% probability) postpones irrigation with explanation shown.

### Backend Services for User Story 3

- [ ] T123 [P] [US3] Implement soil moisture estimator in backend/src/services/recommendations/soil_moisture.py
- [ ] T124 [US3] Implement irrigation scheduler in backend/src/services/recommendations/irrigation_scheduler.py
- [ ] T125 [US3] Implement irrigation cost estimator in backend/src/services/recommendations/irrigation_cost.py

### Backend API for User Story 3

- [ ] T126 [US3] Implement POST /api/farm/irrigation endpoint in backend/src/api/routes/irrigation.py
- [ ] T127 [US3] Add validation for irrigation requests in backend/src/api/routes/irrigation.py

### Frontend UI for User Story 3

- [ ] T128 [P] [US3] Create IrrigationScheduleCard component in frontend/app/components/irrigation/IrrigationScheduleCard.tsx
- [ ] T129 [P] [US3] Create IrrigationEventItem component in frontend/app/components/irrigation/IrrigationEventItem.tsx
- [ ] T130 [P] [US3] Create SoilMoistureIndicator component in frontend/app/components/irrigation/SoilMoistureIndicator.tsx
- [ ] T131 [US3] Create irrigation schedule page route in frontend/app/routes/farm.$farmId.irrigation.tsx

### Tests for User Story 3

- [ ] T132 [P] [US3] Backend unit test for soil moisture estimator in backend/tests/unit/test_soil_moisture.py
- [ ] T133 [P] [US3] Backend integration test for irrigation scheduler in backend/tests/integration/test_irrigation_scheduler.py
- [ ] T134 [P] [US3] Backend API test for /api/farm/irrigation in backend/tests/api/test_irrigation.py
- [ ] T135 [US3] Playwright E2E test for User Story 3 in frontend/tests/e2e/user-story-3.spec.ts

**Checkpoint**: User Story 3 (Irrigation Scheduling) is complete and independently testable.

---

## Phase 6: User Story 4 - Harvest Timing (Priority: P2)

**Goal**: For mature crops, recommend optimal harvest window and sell vs store decision based on price forecasts, storage cost, and quality loss rates.

**Independent Test**: For tomato ready-to-harvest with predicted 30% price rise in 10 days, verify system recommends storage with expected extra profit minus storage costs. Test high-spoilage scenario recommends immediate sale.

### Backend LLM Tools for User Story 4

- [ ] T136 [US4] Implement compute_break_even_harvest_delay tool in backend/src/services/ai_tools/compute_break_even_harvest_delay.py
- [ ] T137 Register User Story 4 tools in tool registry in backend/src/services/ai/tool_registry.py

### Backend Services for User Story 4

- [ ] T138 [P] [US4] Implement price trend forecaster in backend/src/services/market/price_forecaster.py
- [ ] T139 [P] [US4] Implement storage cost calculator in backend/src/services/recommendations/storage_calculator.py
- [ ] T140 [US4] Implement harvest timing advisor in backend/src/services/recommendations/harvest_advisor.py

### Backend API for User Story 4

- [ ] T141 [US4] Implement POST /api/farm/harvest-timing endpoint in backend/src/api/routes/harvest.py
- [ ] T142 [US4] Add validation for harvest timing requests in backend/src/api/routes/harvest.py

### Frontend UI for User Story 4

- [ ] T143 [P] [US4] Create HarvestTimingCard component in frontend/app/components/harvest/HarvestTimingCard.tsx
- [ ] T144 [P] [US4] Create SellVsStoreComparison component in frontend/app/components/harvest/SellVsStoreComparison.tsx
- [ ] T145 [P] [US4] Create PriceForecastChart component in frontend/app/components/harvest/PriceForecastChart.tsx
- [ ] T146 [P] [US4] Create ScenarioSimulator component in frontend/app/components/harvest/ScenarioSimulator.tsx
- [ ] T147 [US4] Create harvest timing page route in frontend/app/routes/farm.$farmId.harvest.tsx

### Tests for User Story 4

- [ ] T148 [P] [US4] Backend unit test for price forecaster in backend/tests/unit/test_price_forecaster.py
- [ ] T149 [P] [US4] Backend unit test for break-even calculator in backend/tests/unit/test_compute_break_even.py
- [ ] T150 [P] [US4] Backend integration test for harvest advisor in backend/tests/integration/test_harvest_advisor.py
- [ ] T151 [P] [US4] Backend API test for /api/farm/harvest-timing in backend/tests/api/test_harvest.py
- [ ] T152 [US4] Playwright E2E test for User Story 4 in frontend/tests/e2e/user-story-4.spec.ts

**Checkpoint**: User Story 4 (Harvest Timing) is complete and independently testable.

---

## Phase 7: User Story 5 - Subsidy Match (Priority: P3)

**Goal**: Check farm geolocation against government schemes and return eligible subsidies (micro-irrigation, seed programs) with application links.

**Independent Test**: For test farm in Tamil Nadu program catchment area, validate eligible schemes returned with matched criteria and application links.

### Database for User Story 5

- [ ] T153 [US5] Create migration for scheme_matches table in supabase/migrations/012_scheme_matches.sql
- [ ] T154 [US5] Create migration for government_schemes reference table in supabase/migrations/013_government_schemes.sql
- [ ] T155 [US5] Seed Tamil Nadu government schemes data in supabase/seed.sql

### Backend Models for User Story 5

- [ ] T156 [US5] Create SchemeMatch model in backend/src/models/scheme_match.py
- [ ] T157 [US5] Create GovernmentScheme model in backend/src/models/government_scheme.py

### Backend LLM Tools for User Story 5

- [ ] T158 [US5] Implement check_subsidy_eligibility tool in backend/src/services/ai_tools/check_subsidy_eligibility.py
- [ ] T159 Register User Story 5 tools in tool registry in backend/src/services/ai/tool_registry.py

### Backend Services for User Story 5

- [ ] T160 [US5] Implement scheme matcher service (geospatial + criteria matching) in backend/src/services/recommendations/subsidy_matcher.py
- [ ] T161 [US5] Implement eligibility verifier in backend/src/services/recommendations/eligibility_verifier.py

### Backend API for User Story 5

- [ ] T162 [US5] Implement POST /api/farm/schemes endpoint in backend/src/api/routes/schemes.py
- [ ] T163 [US5] Add validation for scheme match requests in backend/src/api/routes/schemes.py

### Frontend UI for User Story 5

- [ ] T164 [P] [US5] Create SubsidyCard component in frontend/app/components/subsidy/SubsidyCard.tsx
- [ ] T165 [P] [US5] Create EligibilityCriteria component in frontend/app/components/subsidy/EligibilityCriteria.tsx
- [ ] T166 [P] [US5] Create ApplicationSteps component in frontend/app/components/subsidy/ApplicationSteps.tsx
- [ ] T167 [US5] Create subsidy match page route in frontend/app/routes/farm.$farmId.subsidies.tsx

### Tests for User Story 5

- [ ] T168 [P] [US5] Backend unit test for eligibility verifier in backend/tests/unit/test_eligibility_verifier.py
- [ ] T169 [P] [US5] Backend integration test for subsidy matcher in backend/tests/integration/test_subsidy_matcher.py
- [ ] T170 [P] [US5] Backend API test for /api/farm/schemes in backend/tests/api/test_schemes.py
- [ ] T171 [US5] Playwright E2E test for User Story 5 in frontend/tests/e2e/user-story-5.spec.ts

**Checkpoint**: User Story 5 (Subsidy Match) is complete. All user stories now implemented.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Localization

- [ ] T172 [P] Implement translate_to_language LLM tool in backend/src/services/ai_tools/translate_to_language.py
- [ ] T173 [P] Add Tamil language support to all UI components in frontend/app/i18n/ta.ts
- [ ] T174 [P] Add Hindi language support to all UI components in frontend/app/i18n/hi.ts
- [ ] T175 Create language selector component in frontend/app/components/LanguageSelector.tsx

### Offline Capabilities

- [ ] T176 [P] Implement offline queue sync service in frontend/app/services/offline-sync.ts
- [ ] T177 Create service worker for offline caching in frontend/public/sw.js

### Performance Optimization

- [ ] T178 [P] Add Redis caching layer for frequently accessed data in backend/src/cache/redis_cache.py
- [ ] T179 [P] Optimize database queries with covering indexes in supabase/migrations/014_performance_indexes.sql
- [ ] T180 [P] Implement lazy loading for frontend components in frontend/app/routes/
- [ ] T181 Add image optimization and CDN configuration in wrangler.toml

### Security & Compliance

- [ ] T182 [P] Implement row-level security policies for all tables in supabase/migrations/015_rls_policies.sql
- [ ] T183 [P] Add data export functionality in backend/src/api/routes/user.py
- [ ] T184 [P] Add data deletion functionality (GDPR compliance) in backend/src/api/routes/user.py
- [ ] T185 Add input sanitization and SQL injection prevention in backend/src/middleware/security.py

### Documentation

- [ ] T186 [P] Update quickstart.md validation steps
- [ ] T187 [P] Create API documentation with OpenAPI schemas in backend/docs/api.md
- [ ] T188 [P] Create developer setup guide in docs/SETUP.md
- [ ] T189 [P] Create deployment guide for Cloudflare in docs/DEPLOYMENT.md

### Code Quality

- [ ] T190 [P] Add comprehensive logging for all services in backend/src/
- [ ] T191 [P] Refactor duplicated code across recommendation services
- [ ] T192 [P] Add missing type annotations in backend/src/
- [ ] T193 Run full test suite and fix any failing tests

### Final Validation

- [ ] T194 Run quickstart.md end-to-end validation
- [ ] T195 Verify all user stories work independently via Playwright tests
- [ ] T196 Run performance tests to verify SLAs (<300ms cached, <8s cold)
- [ ] T197 Verify constitution compliance (all gates still pass)

---

## Dependencies & Execution Order

### Phase Dependencies

```
Setup (Phase 1)
    ↓
Foundational (Phase 2) — BLOCKS all user stories
    ↓
    ├─→ User Story 1 (Phase 3) [P1] 🎯 MVP
    ├─→ User Story 2 (Phase 4) [P1] 🎯 MVP
    ├─→ User Story 3 (Phase 5) [P2]
    ├─→ User Story 4 (Phase 6) [P2]
    └─→ User Story 5 (Phase 7) [P3]
    ↓
Polish (Phase 8)
```

**Key Points**:
- **Phase 1 (Setup)**: Can start immediately, all [P] tasks run in parallel
- **Phase 2 (Foundational)**: MUST complete before any user story work begins
- **User Stories (Phase 3-7)**: Can ALL start in parallel after Phase 2 completion (if team capacity allows)
- **MVP Delivery**: Complete only Phase 1 + Phase 2 + Phase 3 (US1) + Phase 4 (US2) for first deployment
- **Phase 8 (Polish)**: Start after all desired user stories complete

### User Story Dependencies

- **US1 (Farm Snapshot)**: Independent - only depends on Foundational phase
- **US2 (Crop Recommendation)**: Independent - only depends on Foundational phase (uses US1 data but not US1 code)
- **US3 (Irrigation)**: Independent - uses same weather/location services as US1 but can be implemented separately
- **US4 (Harvest Timing)**: Independent - uses market data from US1 but no code dependencies
- **US5 (Subsidy Match)**: Independent - pure geospatial matching with no dependencies on other stories

**All user stories are designed for independent implementation and testing.**

### Within Each User Story

1. **Database migrations first** (create tables)
2. **Models next** (all [P] tasks parallel)
3. **LLM tools** (can run parallel with services)
4. **Services** (data fetching before business logic)
5. **API endpoints** (after services complete)
6. **Frontend components** (all [P] tasks parallel)
7. **Page routes** (after components ready)
8. **Tests last** (after implementation complete)

### Parallel Opportunities Summary

**Phase 1 (Setup)**: 15 out of 20 tasks can run in parallel:
- All Docker files parallel
- All linting configs parallel
- All script files parallel
- Frontend/backend setup parallel

**Phase 2 (Foundational)**: 18 out of 26 tasks can run in parallel:
- All migrations parallel (except sequence dependencies)
- All base models parallel
- All middleware parallel
- Frontend/backend foundation parallel

**Within User Stories**: High parallelism:
- All models parallel
- All LLM tools parallel
- All UI components parallel
- All unit tests parallel

**Cross-Story Parallelism**: 
- After Phase 2 completes, all 5 user stories can be assigned to different developers
- Example: Developer 1 → US1, Developer 2 → US2, Developer 3 → US3
- Estimated completion: 2-3 weeks with 3 developers vs 6-8 weeks with 1 developer

---

## Parallel Execution Examples

### Example 1: MVP Sprint (US1 + US2)

**Week 1**: Setup + Foundation
```bash
# Day 1-2: All setup tasks T001-T020 (parallel where marked [P])
# Day 3-4: All foundational tasks T021-T046 (parallel where marked [P])
# Day 5: Checkpoint - Foundation ready
```

**Week 2-3**: User Story 1 (Farm Snapshot)
```bash
# Team splits:
# Developer A: Database (T047-T052) → Models (T053-T058)
# Developer B: Satellite/Weather services (T059-T063) → Weather coordinator (T064)
# Developer C: Market/Location services (T065-T067)
# Developer D: LLM tools (T068-T073) → API (T074-T077)
# Developer E: Frontend components (T078-T084) → Routes (T085-T086)
# QA: Tests (T087-T094) in parallel with late-stage implementation
```

**Week 4**: User Story 2 (Crop Recommendation)
```bash
# Continue similar parallel pattern:
# Backend: Database + Models + Tools + Services + API
# Frontend: Components + Routes
# QA: Tests
```

**Week 5**: Polish + Deploy MVP

### Example 2: Full Feature (All User Stories)

**After Week 2** (Foundation complete):
- **Track 1**: US1 (Developer Team A)
- **Track 2**: US2 (Developer Team B)
- **Track 3**: US3 (Developer Team C)
- **Track 4**: US4 (Developer Team D)
- **Track 5**: US5 (Developer Team E)

All tracks proceed independently with checkpoints every 3 days.

---

## Task Count Summary

| Phase | Task Count | Parallelizable | Critical Path |
|-------|------------|----------------|---------------|
| Setup (Phase 1) | 20 | 15 (75%) | ~2 days |
| Foundational (Phase 2) | 26 | 18 (69%) | ~4 days |
| User Story 1 (Phase 3) | 48 | 35 (73%) | ~8 days |
| User Story 2 (Phase 4) | 28 | 18 (64%) | ~5 days |
| User Story 3 (Phase 5) | 13 | 8 (62%) | ~3 days |
| User Story 4 (Phase 6) | 17 | 11 (65%) | ~4 days |
| User Story 5 (Phase 7) | 20 | 12 (60%) | ~4 days |
| Polish (Phase 8) | 25 | 17 (68%) | ~4 days |
| **Total** | **197** | **134 (68%)** | **34 days (solo)** |

**Team Estimates**:
- **Solo developer**: 34 working days (7 weeks)
- **2 developers**: 20 working days (4 weeks)
- **5 developers**: 12 working days (2.5 weeks) - optimal for user story parallelism

---

## MVP Scope Recommendation

**Minimum Deployable Product**: Phase 1 + Phase 2 + Phase 3 (US1) only

This gives farmers:
- ✅ Farm polygon upload
- ✅ Instant snapshot with soil, weather, NDVI, market prices
- ✅ Top action recommendation
- ✅ Confidence scores and data provenance
- ✅ Mobile-responsive UI
- ✅ Offline capability

**Estimated effort**: ~14 days solo, ~8 days with 2 developers

**Next Increment**: Add Phase 4 (US2 - Crop Recommendation) → Full MVP

**Future Increments**: Add phases 5-7 based on user feedback and priority

---

**Total Tasks**: 197  
**Format Validation**: ✓ All tasks follow checklist format with IDs, file paths, and story labels  
**Independent Testing**: ✓ Each user story has validation criteria and E2E tests  
**Parallel Opportunities**: ✓ 134 tasks (68%) marked [P] for parallel execution  
**MVP Path**: ✓ Clear (Phase 1→2→3→4 delivers complete MVP)
