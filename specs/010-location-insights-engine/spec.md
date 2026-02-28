# Feature Specification: Location-Based Insights Engine

**Feature Branch**: `010-location-insights-engine`
**Created**: 2026-02-28
**Status**: Draft
**Input**: User description: "Given a farm polygon + location, produce all location-derived attributes (climate, soil, weather, satellite/time-series, market, policy, water, local farming patterns) and generate explainable, actionable insights (crop choice, planting window, irrigation schedule, yield & revenue forecast, harvest timing, storage vs sell recommendation, subsidy eligibility). Respond in farmer's language and provide confidence & provenance for every recommendation."

---

## User Scenarios & Testing *(mandatory)*

> Prioritization: every user story below is independently testable and deployable. Implementing any single P1 story yields a viable MVP.

### User Story 1 - Generate Immediate Farm Snapshot (Priority: P1)

**Brief**: Farmer (or agent) selects farm on map or uploads drawn polygon; system returns an immediate “Farm Snapshot” summarizing: location, area, dominant soil type, last 7-day weather, next 7-day forecast, current NDVI trend, groundwater depth estimate, nearest mandi prices, and top 1 recommended action (e.g., "Water today").

**Why this priority**: This is the primary touchpoint farmers open daily. It must deliver fast, trusted value and build trust.

**Independent Test**: Provide a farm polygon and location. Mock or use live data sources. Validate that the app displays all snapshot fields within SLA (<3s for cached data, <8s for first cold AI call) and that the “recommended action” is present with provenance and confidence.

**Acceptance Scenarios**:

1. **Given** a saved farm polygon and language preference (Tamil), **When** farmer opens the app, **Then** the Farm Snapshot displays area, soil summary, 7-day weather, NDVI trend (last 14 days), nearest mandi modal price, and a single prioritized action card with confidence and data sources.
2. **Given** FarmOps AI must autonomously discover real crop market prices across the internet, analyze sources, detect correct local price, store historical data, and generate future price predictions and actionable farmer recommendations

---

### User Story 2 - Crop Choice & Profit Recommendation (Priority: P1)

**Brief**: Farmer asks “What should I plant this season on this farm?” System returns 3 ranked crop options with expected yield/acre, expected revenue & profit/acre, planting window dates, water requirement, and risk score (drought/pest/market).

**Why this priority**: Directly affects farmer income and is the core monetizable decision.

**Independent Test**: For a given location and season, run the recommendation pipeline. Verify the three proposals include numeric profit estimates, planting dates, and risk reasoning. Check that at least one option aligns with known policy constraints (e.g., local cropping calendar).

**Acceptance Scenarios**:

1. **Given** farm polygon in Thanjavur and season “Samba”, **When** farmer requests crop recommendation, **Then** system returns 3 crops with revenue/profit/acre, planting window, water needs, and risk summary, with data sources listed.
2. **Given** farm is in a groundwater-scarce zone, **When** recommending, **Then** avoid recommending high-water crops unless irrigation subsidy eligibility is present and shown.

---

### User Story 3 - Irrigation & Water Scheduling (Priority: P2)

**Brief**: System produces a schedule of irrigation events for the next 14 days tailored to soil moisture profile, crop stage, and 7-day weather forecast (including rain probability).

**Why this priority**: Saves water and input cost; avoids overwatering and stress.

**Independent Test**: Mock soil moisture + forecast; verify schedule respects rain probability (skip irrigation if >70% chance of >10mm rain next 24h), and shows expected water volume per event.

**Acceptance Scenarios**:

1. **Given** soil moisture = low at 10cm depth, **When** schedule is generated, **Then** an irrigation action appears within 24 hours with volume estimate and estimated cost.
2. **Given** heavy rain forecast in 12 hours, **When** scheduling, **Then** irrigation is postponed and farmer is told why.

---

### User Story 4 - Harvest Timing & Sell vs Store (Priority: P2)

**Brief**: For mature crops, system recommends optimal harvest window and whether to sell immediately or store based on short/medium-term price forecasts, storage cost, and quality loss rates.

**Why this priority**: Maximizes realized revenue and minimizes spoilage.

**Independent Test**: For a given crop with known harvest maturity, run price forecast and storage model; validate decision (sell/store) and show break-even delay days.

**Acceptance Scenarios**:

1. **Given** tomato ready-to-harvest and predicted price rise of 30% in 10 days, **When** farmer requests advice, **Then** system recommends storage with expected extra profit minus storage costs.
2. **Given** high spoilage rates and low storage capacity, **When** advice is requested, **Then** system recommends immediate sale even if price rises later.

---

### User Story 5 - Subsidy & Scheme Match (Priority: P3)

**Brief**: System checks farm geolocation against government schemes and subsidies and returns a list of eligible schemes (e.g., micro-irrigation subsidy, seed/grant programs) with links and filing steps.

**Why this priority**: Access to subsidies can materially change crop economics.

**Independent Test**: For a test farm polygon in a known eligible district, validate returned scheme and the eligibility criteria used.

**Acceptance Scenarios**:

1. **Given** farm polygon within a TN program catchment, **When** scheme scan runs, **Then** eligible scheme(s) are presented with application link and required documents.

---

## Edge Cases

* Missing or conflicting data (e.g., satellite NDVI cloudy / soil test outdated): show “confidence low”, use fallback heuristics (historical NDVI, farmer-provided inputs), and provide clear “why uncertain” text.
* Offline/poor connectivity: app must serve last-known snapshot from Supabase cache and allow farmer to create/queue actions offline; queued actions sync when online.
* Incorrect polygon (very small or self-intersecting): prompt farmer to redraw; provide auto-snap heuristics.
* Market API delay or outage: fall back to historical modal price averages for the same market/day-of-week and mark provenance.
* Extreme/unrealistic sensor values (e.g., soil moisture >1.0): validate and drop; alert ops for sensor anomalies.
* Multiple farms overlapping: detect overlapping polygons and ask user to confirm ownership mapping.
* Seasonal anomalies (e.g., unseasonal cyclone): trigger risk-as-high and recommend conservative actions.
* Data privacy: farmer requests data export or deletion — support GDPR-like deletion and Supabase row-level security.

---

## Requirements *(mandatory)*

### Functional Requirements

* **FR-001**: System MUST accept a farm polygon and location and persist it in Supabase.
* **FR-002**: System MUST fetch and store (cached) the following for the polygon: climate normals, soil texture & nutrients (if available), last 30-day NDVI time-series, last 30-day weather observations, 7-day weather forecast, groundwater depth estimate, and nearest 3 mandi prices.
* **FR-003**: System MUST compute and return a Farm Snapshot containing: area, soil summary, NDVI trend, current soil moisture (or estimate), 7-day forecast, nearest mandi modal price, top action, and confidence/provenance metadata.
* **FR-004**: System MUST generate ranked crop recommendations for a requested season with expected yield/acre, revenue/acre, cost/acre, profit/acre, planting window, water requirement, and risk score.
* **FR-005**: System MUST generate a 14-day irrigation plan tied to soil moisture forecasts and crop stage; allow farmer edits and re-run predictions after edits.
* **FR-006**: System MUST generate harvest timing & sell-vs-store recommendation with break-even computation and scenario simulation (hold 0/5/10/20 days).
* **FR-007**: System MUST match farm to government schemes by geospatial criteria and return eligibility and application steps.
* **FR-008**: System MUST return provenance for every numeric output (data sources used, timestamps, AI model version, tool calls) and a confidence score (0–100%).
* **FR-009**: System MUST expose an API for the UI (Remix) with endpoints: `/farm/snapshot`, `/farm/recommendations`, `/farm/irrigation`, `/farm/harvest`, `/farm/schemes`.
* **FR-010**: System MUST log all external data fetches and AI tool calls to an audit table in Supabase (including inputs/outputs, execution time, costs).
* **FR-011**: System MUST enforce rate-limiting & caching to avoid excessive API costs (cache TTLs configurable).
* **FR-012**: System MUST support offline-first UI behavior (serve cached snapshot; queue farmer edits/actions).
* **FR-013**: System MUST be localized: return outputs in selected language and use local units (kg, acres/hectares, ₹).
* **FR-014**: System MUST include a human-review flag: any recommendation with confidence < X% (configurable) must be tagged “Needs Extension Review”.
* **FR-015**: System MUST support test harnesses to inject synthetic data for deterministic unit/integration tests.

### Non-Functional Requirements

* **NFR-001**: Snapshot generation for cached farms: ≤ 300ms; for cold farms requiring remote calls and AI: ≤ 8s.
* **NFR-002**: Crop recommendation pipeline runtime ≤ 10s on first-run; subsequent runs use cached intermediate data.
* **NFR-003**: Uptime 99% for API endpoints.
* **NFR-004**: Data retention policy: raw external fetch logs retained 90 days; summarized provenance retained indefinitely (or per legal requirements).
* **NFR-005**: All AI calls must be traceable and auditable; store model version and prompts used.
* **NFR-006**: Maximum 5% of recommendations with confidence below 40% (target after model tuning).
* **NFR-007**: API responses must include `confidence`, `sources[]`, and `explanation` fields.

---

## Key Entities *(include if feature involves data)*

* **User**: farmer account; attrs: `id`, `name`, `language`, `location_pref`, `phone`, `last_active`.
* **Farm**: `id`, `user_id`, `polygon_geojson`, `area_acres`, `named`, `last_snapshot_id`.
* **LocationProfile**: aggregated static data for a lat/lon tile (climate normals, soil template, elevation, watershed id).
* **SoilProfile**: `soil_type`, `texture`, `pH`, `organic_carbon`, `NPK`, `depth`, `drainage`.
* **WeatherSnapshot**: `observations[]`, `forecast[]`, `timestamp`.
* **VegTimeSeries**: NDVI/EVI time series for polygon with timestamps.
* **MarketSnapshot**: `market_id`, `distance_km`, `modal_price`, `date`, `commodity`.
* **Recommendation**: `id`, `farm_id`, `type` (crop/irrigation/harvest), `payload` (structured numbers), `confidence`, `sources`, `created_at`, `model_version`.
* **SchemeMatch**: `scheme_id`, `eligibility_criteria`, `matched_fields`, `apply_link`.
* **DataAuditLog**: logs for external API calls & AI tool calls: `source`, `request_payload`, `response_summary`, `latency_ms`, `cost_estimate`, `status`.
* **UserAction**: queued farmer actions from UI (e.g., “mark irrigation done”), sync status.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

* **SC-001**: Farm Snapshot loads for cached farms < 300ms 95% of the time.
* **SC-002**: Cold-run Snapshot (first-time farm) completes and returns full payload < 8s in 90% of cases.
* **SC-003**: Crop recommendation accuracy: top-1 recommendation aligns with historical profitable crop choices for the location in ≥ 70% of validation test cases (synthetic + historical).
* **SC-004**: Price forecast MAE ≤ 18% over 30-day horizon on held-out Tamil Nadu mandi data (benchmark target; refine via model tuning).
* **SC-005**: Irrigation schedule reduces unnecessary water events by ≥ 25% in pilot controlled tests (simulated or field pilot compared to baseline).
* **SC-006**: User workflow time: farmers complete farm→snapshot→one action in ≤ 2 minutes in 90% of usability tests.
* **SC-007**: Provenance completeness: 100% of numeric recommendations include `sources[]` and `model_version`.
* **SC-008**: Offline capability: queued actions sync successfully in 99% of reconnection tests.
* **SC-009**: Confidence distribution: after tuning, ≤ 20% of recommendations have confidence < 50%.
* **SC-010**: Adoption metric: 30-day active retention ≥ 40% in early pilot (indicative; target for growth).

---

## Implementation Notes & Testing Guidance (concise)

* **Data ingestion**: build a LocationProfile cache keyed by S2 / H3 tile for quick aggregation of climate/soil/static features; refresh cadence: climate normals monthly, soil static monthly/on-change, satellite NDVI daily (or as imagery arrives), market prices daily.
* **AI tooling**: use Mistral (via OpenAI-compatible client) for reasoning and language; separate numeric computation modules (Python) for deterministic math (yield calc, break-even) and ensure LLM statements are only for explanation & scenario synthesis. Enforce tool-based calls where LLM must call `get_market_price(tile,date)`, `get_ndvi_timeseries(polygon)`, `estimate_yield(params)` and then compose.
* **Provenance**: persist dataAuditLog entries for each external fetch and AI tool call; include `data_age` and `confidence`. UI must show "Data as of <timestamp>" prominently.
* **Testing**: create test fixtures for Tamil Nadu districts (Thanjavur, Coimbatore, Madurai) with historical mandi prices, satellite NDVI slices, and soil samples to validate end-to-end behavior. Unit test deterministic functions (yield formulas) and integration tests for AI interaction using recorded tool-call transcripts.
* **Privacy**: use Supabase RLS policies to restrict farm data; offer export & deletion endpoints.
* **Fallback UX**: when data missing, show a short-form question to farmer (e.g., "Is your soil heavy/clayey?") to allow manual override and keep flow moving.

---

If you want, I can now:

* Generate the **Supabase schema** for the entities above.
* Draft the **Python tool interfaces** (signatures) that the LLM will call (e.g., `estimate_yield`, `get_market_prices`, `predict_price_trend`).
* Create **sample test fixtures** for 3 Tamil Nadu pilot farms (Thanjavur rice, Coimbatore groundnut, Madurai tomato) and deterministic expected outputs for unit/integration tests.

Which of those should I produce next?
