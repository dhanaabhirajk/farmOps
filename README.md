# FarmOps - Location-Based Insights Engine

**Agricultural Intelligence Platform for Tamil Nadu Farmers**

## Overview

FarmOps provides actionable, explainable agricultural insights for farmers by analyzing farm locations and generating data-driven recommendations covering:

- **Farm Snapshot**: Real-time climate, soil, weather, NDVI satellite data, and market prices
- **Crop Recommendations**: Profit forecasts, planting windows, water requirements, and risk scores
- **Irrigation Scheduling**: 14-day irrigation plans based on soil moisture and weather
- **Harvest Timing**: Sell vs store recommendations with price forecasts
- **Subsidy Matching**: Government scheme eligibility checking

## Tech Stack

**Backend**: Python 3.11+, FastAPI, Supabase (PostgreSQL + PostGIS)  
**Frontend**: Remix (React Router), TypeScript, Tailwind CSS  
**AI**: Mistral LLM with 12 deterministic tools  
**Data Sources**: Google Earth Engine, IMD, OpenWeatherMap, AGMARKNET

## Quick Start

```bash
# Start all services with hot reload
docker-compose -f docker-compose.dev.yml up

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

See [specs/010-location-insights-engine/quickstart.md](specs/010-location-insights-engine/quickstart.md) for detailed setup.

## Documentation

- [Feature Spec](specs/010-location-insights-engine/spec.md) - 5 user stories
- [Implementation Plan](specs/010-location-insights-engine/plan.md) - Architecture
- [Task Breakdown](specs/010-location-insights-engine/tasks.md) - 197 tasks
- [Data Model](specs/010-location-insights-engine/data-model.md) - Database schema
- [API Contracts](specs/010-location-insights-engine/contracts/) - Endpoints & tools

## Status

**Phase 1**: Setup & Infrastructure ✅ (In Progress)  
**Branch**: `010-location-insights-engine`  
**Target**: Tamil Nadu farmers (pilot)
