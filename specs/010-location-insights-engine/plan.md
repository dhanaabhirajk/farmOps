# Implementation Plan: Location-Based Insights Engine

**Branch**: `010-location-insights-engine` | **Date**: 2026-02-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-location-insights-engine/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a location-based agricultural insights engine that accepts farm polygons and generates actionable, explainable recommendations for farmers covering: farm snapshot (climate, soil, weather, NDVI, market prices), crop selection with profit forecasts, irrigation scheduling, harvest timing, and subsidy eligibility. All outputs must include confidence scores and provenance metadata. The system uses a tool-based AI architecture with Mistral LLM, FastAPI backend, Remix frontend, and Supabase for persistence.

## Technical Context

**Language/Version**: Python 3.11+, TypeScript (Remix)  
**Primary Dependencies**: FastAPI, Remix, Mistral AI (via OpenAI-compatible client), Supabase client, geospatial libraries (Shapely, GDAL), satellite data APIs (NEEDS CLARIFICATION: which satellite provider - Sentinel Hub, Planet, Google Earth Engine?), weather APIs (NEEDS CLARIFICATION: OpenWeatherMap, NOAA, or India Meteorological Dept?), market price APIs (NEEDS CLARIFICATION: specific Indian agricultural market data sources?)  
**Storage**: Supabase PostgreSQL with PostGIS extension for geospatial queries  
**Testing**: pytest for backend, Playwright for frontend UI tests  
**Target Platform**: Web application (mobile and desktop responsive), deployed to Cloudflare (Pages for frontend, Workers/Pages Functions for API edge functions, optionally Workers for Python containerized backend)  
**Project Type**: Web service (full-stack: API backend + web frontend)  
**Performance Goals**: <300ms response for cached farm snapshots, <8s for cold AI-driven recommendations, <10s for crop recommendation pipeline  
**Constraints**: 99% uptime SLA, offline-capable UI with queue sync, tool-based AI (no hallucinated financial data), all outputs must include provenance and confidence metadata, rate limiting and caching to control API costs, locally runnable via docker-compose.dev with hot reload for development, containerized deployment, Cloudflare-ready with wrangler.toml configuration, automated Playwright testing after each user story with Docker error log capture and automatic error remediation  
**Scale/Scope**: Multi-tenant farmer platform targeting Tamil Nadu pilot, handling farm polygons with multiple data sources (climate, soil, satellite, weather, market, policy), ~10-15 API endpoints, 5 primary user stories (P1-P3), extensive data audit logging

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gates

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **I. Farmer-First Reliability** | All recommendations must be deterministic, explainable, traceable | ✓ PASS | Spec requires provenance, confidence, and audit logging for all outputs (FR-008, FR-010) |
| **I. Farmer-First Reliability** | Graceful degradation without data loss | ✓ PASS | Spec includes offline-first UI with queue sync (FR-012) and fallback for missing data (Edge Cases) |
| **II. Testing** | UI must be tested with Playwright | ✓ PASS | Specified in Technical Context; automated after each user story |
| **II. Testing** | Extensive logging | ✓ PASS | FR-010 requires audit logs for all external fetches and AI calls; Docker container logs captured during tests |
| **II. Testing** | Automated error remediation | ✓ PASS | Test failures trigger Docker log analysis and automatic error fixing via AI agent |
| **III. Deterministic AI** | Tool-based architecture mandatory | ✓ PASS | Spec explicitly requires tool-based AI architecture (Implementation Notes), no hallucinated financial values |
| **III. Deterministic AI** | All AI calls must log input/output/tools/time/errors | ✓ PASS | FR-010 mandates logging all tool calls with inputs/outputs/execution time/costs |
| **III. Deterministic AI** | AI outputs include confidence and trace | ✓ PASS | FR-008 requires provenance and confidence (0-100%) for every output |
| **IV. Consistent UX** | Simple, action-oriented interfaces | ✓ PASS | User stories focus on actionable outputs ("What should I plant?", "Water today") |
| **IV. Consistent UX** | <300ms for interactive elements | ✓ PASS | NFR-001: ≤300ms for cached snapshots |
| **V. Modular Architecture** | Remix (UI) / Python (logic) / Supabase (persistence) separation | ✓ PASS | Architecture enforced by stack requirements |
| **V. Modular Architecture** | AI tools separate | ✓ PASS | Tool-based approach ensures separation |
| **VII. Data Integrity** | Financial data versioned and validated | ✓ PASS | FR-010 audit logging captures data versions, NFR-007 mandates confidence/sources/explanation |
| **Stack: Frontend** | Remix, TypeScript, mobile+desktop | ✓ PASS | Specified in Technical Context |
| **Stack: Backend** | Python 3.11+, FastAPI, fully typed | ✓ PASS | Specified in Technical Context |
| **Stack: Database** | Supabase PostgreSQL | ✓ PASS | Specified throughout spec |
| **Stack: AI** | Mistral via OpenAI-compatible client, tool-based | ✓ PASS | Specified in Implementation Notes |

**Pre-Design Result**: ✓ ALL GATES PASS - No violations. Constitution fully aligned with feature spec.

## Project Structure

### Documentation (this feature)

```text
specs/010-location-insights-engine/
├── spec.md              # Feature specification (already exists)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (to be generated)
├── data-model.md        # Phase 1 output (to be generated)
├── quickstart.md        # Phase 1 output (to be generated)
└── contracts/           # Phase 1 output (to be generated)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/              # Supabase ORM models: Farm, LocationProfile, Recommendation, etc.
│   ├── services/            
│   │   ├── location/        # LocationProfile, soil, climate data fetching
│   │   ├── satellite/       # NDVI time-series integration
│   │   ├── weather/         # Weather observations & forecasts
│   │   ├── market/          # Mandi price fetching & caching
│   │   ├── ai_tools/        # Tool definitions for LLM (get_market_price, estimate_yield, etc.)
│   │   ├── recommendations/ # Crop, irrigation, harvest recommendation engines
│   │   └── audit/           # DataAuditLog service
│   ├── api/                 # FastAPI routes: /farm/snapshot, /farm/recommendations, etc.
│   └── config/              # Settings, rate limits, cache TTLs
├── scripts/
│   ├── seed_test_data.py    # Seed test farms
│   └── analyze_logs.py      # Docker log analysis and auto-fix suggestions
├── tests/
│   ├── unit/                # Unit tests for deterministic functions (yield calc, break-even)
│   ├── integration/         # API integration tests
│   └── fixtures/            # Test data for Tamil Nadu districts (Thanjavur, Coimbatore, Madurai)
└── pyproject.toml           # uv managed dependencies

frontend/
├── app/
│   ├── components/          # Reusable UI: FarmSnapshot, RecommendationCard, ConfidenceBar
│   ├── routes/              # Remix routes: farm.snapshot, farm.recommendations, etc.
│   ├── services/            # API client, offline queue sync
│   └── utils/               # Localization, formatting
├── tests/
│   ├── e2e/                 # Playwright end-to-end tests (one per user story)
│   ├── fixtures/            # Test data and page objects
│   └── utils/
│       ├── docker-logs.ts   # Docker error log capture utility
│       └── auto-fix.ts      # Automated error remediation via AI
└── package.json

.specify/                    # Specify framework files (already exists)
supabase/
├── migrations/              # Schema migrations for Farm, Recommendation, DataAuditLog, etc.
└── seed.sql                 # Test data

.github/
└── workflows/
    ├── test-user-stories.yml # CI workflow: run Playwright tests per user story, capture logs, auto-fix
    └── deploy.yml           # Cloudflare deployment workflow

scripts/
├── test-workflow.sh         # Test orchestration: run Playwright → capture Docker logs → attempt auto-fix
└── docker-log-capture.sh    # Capture logs from all containers during test failures

docker-compose.dev.yml       # Development environment with hot reload (Remix watcher, uvicorn reload)
docker-compose.prod.yml      # Production deployment configuration
Dockerfile.backend           # Multi-stage backend build (Python 3.11+)
Dockerfile.frontend          # Frontend build stage (Node.js, Remix build)
.dockerignore               # Files to exclude from Docker builds
wrangler.toml                # Cloudflare Workers/Pages configuration
.dev.vars                    # Local development environment variables for Cloudflare
cloudflare-deploy.sh         # Deployment script for Cloudflare Pages + Workers
README.md
```

**Structure Decision**: Web application with backend (FastAPI/Python) and frontend (Remix/TypeScript). The backend handles all business logic, external data fetching, AI orchestration, and persistence. The frontend provides a responsive UI with offline capabilities. This aligns with the constitution's requirement for modular architecture (Principle V) and the tech stack constraints.

**Docker Setup**: 
- `docker-compose.dev.yml` enables local development with hot reload: Remix dev server watches frontend code for changes, uvicorn backend runs with `--reload` flag to detect code changes
- Services communicate via internal Docker network; database and cache services available
- Volume mounts allow code to be edited locally and reflected immediately in running containers
- `docker-compose.prod.yml` uses optimized, multi-stage builds for production deployment
- Supabase local development instance included via official docker-compose

**Cloudflare Deployment**:
- Frontend deploys to **Cloudflare Pages** with automatic builds from Git push (Remix SSR or static export)
- Backend options: 
  - **Option A**: Deploy FastAPI to Cloudflare Workers using Python Workers (beta) or containerized API via Cloudflare's container runtime
  - **Option B**: Use Cloudflare Pages Functions (lightweight edge functions) for simple API endpoints; external service for complex AI/computation
- `wrangler.toml` configures both Pages and Workers; separate configs for staging/production
- Environment variables managed via Cloudflare dashboard or `wrangler secret put`
- Supabase connection via environment variables (connection string, API keys)
- Deployment: `npm run deploy` → builds Remix + publishes to Cloudflare Pages; `wrangler deploy` → deploys Workers
- Built-in CDN, DDoS protection, zero cold starts for static/edge routes

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. All constitution gates pass without requiring justification.

---

## Post-Design Constitution Check (Phase 1 Complete)

*GATE RE-EVALUATION: Verify design still complies with constitution.*

### Post-Design Result: ✓ ALL GATES STILL PASS

Detailed verification:

| Principle | Gate | Phase 1 Status | Evidence |
|-----------|------|----------------|----------|
| **I. Farmer-First Reliability** | Deterministic, explainable, traceable | ✓ PASS | LLM tool schemas ensure all numeric outputs computed by auditable tools; DataAuditLog captures every tool call with inputs/outputs/execution time |
| **I. Farmer-First Reliability** | Graceful degradation without data loss | ✓ PASS | data-model.md defines fallback logic for missing data (weather unavailable → historical average); UserAction queue ensures offline actions sync without loss |
| **II. Testing** | UI tested with Playwright | ✓ PASS | quickstart.md includes `npm run test:e2e` step; project structure includes `frontend/tests/`; automated after each user story |
| **II. Testing** | Extensive logging | ✓ PASS | DataAuditLog schema includes source, request_payload, response_summary, execution_time_ms, error_message; all tool calls logged; Docker logs captured |
| **II. Testing** | Automated error remediation | ✓ PASS | Test failures trigger Docker log analysis; AI agent analyzes logs and attempts automatic fixes; fixed code re-tested |
| **III. Deterministic AI** | Tool-based architecture mandatory | ✓ PASS | llm-tools.md defines 12 deterministic tools (get_location_profile, estimate_yield, estimate_profit, etc.) that LLM must call; no direct hallucination possible |
| **III. Deterministic AI** | All AI calls log input/output/tools/time/errors | ✓ PASS | Recommendation payload includes tool_calls array with {tool_name, inputs, outputs, execution_time_ms} |
| **III. Deterministic AI** | AI outputs include confidence and trace | ✓ PASS | Recommendation schema includes confidence(0-100%), sources[], and explanation fields |
| **IV. Consistent UX** | Simple, action-oriented interfaces | ✓ PASS | User stories (spec.md) and Recommendation payloads all action-focused ("Water today", "Sell now vs store") |
| **IV. Consistent UX** | <300ms for interactive elements | ✓ PASS | NFR-001 cached: ≤300ms; FarmSnapshot cached with 4-hour TTL in data-model.md |
| **V. Modular Architecture** | Remix (UI) / Python (logic) / Supabase (persistence) | ✓ PASS | Project structure separates: backend/src/{models,services,api}, frontend/app/{components,routes}, supabase/{migrations} |
| **V. Modular Architecture** | AI tools separate | ✓ PASS | backend/src/services/ai_tools/ directory structure; tool definitions in llm-tools.md contract |
| **VII. Data Integrity** | Financial data versioned, validated | ✓ PASS | Recommendation table includes model_version, created_at, expires_at; checks on profit, cost, revenue values |
| **Stack: Frontend** | Remix, TypeScript, mobile+desktop | ✓ PASS | Specified in Technical Context; quickstart.md confirms Remix dev server |
| **Stack: Backend** | Python 3.11+, FastAPI, fully typed | ✓ PASS | Specified in Technical Context |
| **Stack: Database** | Supabase PostgreSQL | ✓ PASS | data-model.md complete schema with PostGIS for geospatial queries |
| **Stack: AI** | Mistral via OpenAI-compatible API | ✓ PASS | Tool-based; llm-tools.md defines function schema for OpenAI-compatible client |
| **Docker Requirement** | Locally runnable via docker-compose.dev | ✓ PASS | docker-compose.dev.yml with hot reload for backend (uvicorn --reload) and frontend (Remix dev server) |

### Design Validation Summary

- **Data Model** (`data-model.md`): 12 core entities + 2 reference tables, all indexes and constraints defined, RLS policies for multi-tenancy
- **API Contracts** (`contracts/api-responses.md`): 6 primary endpoints with full request/response schemas, error codes, latency SLAs
- **LLM Tools** (`contracts/llm-tools.md`): 12 deterministic tools covering data retrieval, computation, and decision logic
- **Quick Start** (`quickstart.md`): End-to-end setup in 15 minutes, includes test farm seeding, recommendation generation demo, hot reload verification
- **Docker Setup**: `docker-compose.dev.yml` for local development with inline reload, `.env.dev` for mock data (zero API keys required for demo)

### No Violations Identified

All constitution principles are upheld by the detailed design. No complexity trade-offs required.

**Date Completed**: 2026-02-28  
**Design Status**: Ready for Phase 2 (Task Breakdown & Implementation)
