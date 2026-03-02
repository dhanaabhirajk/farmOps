# FarmOps - Location-Based Insights Engine

**Agricultural Intelligence Platform for Tamil Nadu Farmers**

## Overview

The global agriculture industry, valued at over **$3.5 trillion annually**, relies heavily on small and medium-scale farmers. However, many lack access to real-time financial insights, market intelligence, and predictive tools, leading to income losses of 10–30% due to poor planning, price volatility, and inefficient harvest timing.

FarmOps is an AI-powered farm intelligence platform that helps farmers identify crops, predict profits, optimize harvest timing, and receive personalized recommendations. By leveraging real-time environmental, financial, and agricultural data, FarmOps reduces uncertainty, improves decision-making, and helps farmers maximize profitability while simplifying farm management.

---

## Key Features

**Crop Intelligence:** Identifies crop type, growth stage, and health to estimate yield and predict profits.

**Predictive Financial and Market Analysis:** Forecasts market prices, revenue, and recommends optimal harvest timing.

**Government Scheme Discovery:** Connects farmers with relevant subsidies and agricultural programs.

**AI-Driven Decision Support:** Provides real-time, data-driven recommendations for smarter farm management.


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
