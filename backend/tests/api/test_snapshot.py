"""API tests for GET /api/v1/farm/snapshot endpoint."""

import json
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend.src.main import app

client = TestClient(app)

# Minimal AgentResult-like object returned by the mocked LLM agent
MOCK_AGENT_RESULT_DICT = {
    "final_response": json.dumps({
        "top_action": {
            "priority": "high",
            "action": "Irrigate within 24 hours",
            "reason": "No rainfall forecast; soil moisture low",
            "confidence": 85,
        },
        "weather_insight": "Hot and dry — 35 °C, 0 mm rain in 7 days",
        "ndvi_insight": "NDVI 0.65 — healthy moderate vegetation",
        "market_insight": "Rice ₹1,900/quintal at Koyambedu — stable trend",
        "overall_confidence": 82,
        "data_sources": ["OpenWeatherMap", "Sentinel-2 / GEE", "data.gov.in/AGMARKNET"],
    }),
    "tool_calls_made": [
        {"tool_name": "get_weather_forecast", "arguments": {}, "result": {
            "current": {"temperature_c": 35, "humidity_pct": 60},
            "forecast_7_days": [],
            "rainfall_probability_24h": 0.05,
            "source": "OpenWeatherMap",
        }, "round": 1},
        {"tool_name": "get_ndvi_timeseries", "arguments": {}, "result": {
            "ndvi_values": [0.62, 0.63, 0.64, 0.65],
            "current_ndvi": 0.65,
            "trend": "stable",
            "interpretation": "Good crop cover",
        }, "round": 1},
        {"tool_name": "search_web_market_prices", "arguments": {}, "result": {
            "success": True,
            "commodity": "Rice",
            "price_summary": {
                "modal_price_inr_per_quintal": 1900,
                "min_price_inr_per_quintal": 1800,
                "max_price_inr_per_quintal": 2000,
                "price_per_kg_inr": 19.0,
                "market": "Koyambedu",
                "source": "data.gov.in/AGMARKNET",
                "is_live_data": True,
                "confidence": 0.9,
            },
            "trend": "stable",
        }, "round": 2},
    ],
    "rounds": 2,
    "usage": {"prompt_tokens": 500, "completion_tokens": 300, "total_tokens": 800},
}


class _FakeAgentResult:
    """Minimal stand-in for AgentResult."""

    def __init__(self, d: dict) -> None:
        self.final_response = d["final_response"]
        self.tool_calls_made = d["tool_calls_made"]
        self.rounds = d["rounds"]
        self.usage = d["usage"]


class TestFarmSnapshotAPI:
    """Tests for the farm snapshot endpoint."""

    @pytest.fixture(autouse=True)
    def _patch_llm(self):
        """Patch the LLM agent so tests never hit Mistral API."""
        fake = _FakeAgentResult(MOCK_AGENT_RESULT_DICT)
        with patch(
            "backend.src.services.ai.llm_agent.get_llm_agent"
        ) as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value=fake)
            mock_get_agent.return_value = mock_agent
            yield

    def test_snapshot_success(self):
        """Snapshot endpoint should return 200 with correct structure."""
        response = client.get(
            "/api/v1/farm/snapshot",
            params={"farm_id": "00000000-0000-0000-0000-000000000001"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "metadata" in data

    def test_snapshot_data_structure(self):
        """Snapshot data should contain all required keys."""
        response = client.get(
            "/api/v1/farm/snapshot",
            params={"farm_id": "00000000-0000-0000-0000-000000000001"},
        )
        payload = response.json()["data"]
        assert "farm" in payload
        assert "soil_summary" in payload
        assert "weather" in payload
        assert "ndvi_trend" in payload
        assert "nearest_mandi_price" in payload
        assert "top_action" in payload

    def test_snapshot_top_action_has_required_fields(self):
        """top_action must have priority, action, reason, confidence."""
        response = client.get(
            "/api/v1/farm/snapshot",
            params={"farm_id": "00000000-0000-0000-0000-000000000001"},
        )
        top_action = response.json()["data"]["top_action"]
        assert "priority" in top_action
        assert "action" in top_action
        assert "reason" in top_action
        assert "confidence" in top_action

    def test_snapshot_llm_audit_in_metadata(self):
        """Metadata should expose the LLM tool-call audit trail."""
        response = client.get(
            "/api/v1/farm/snapshot",
            params={"farm_id": "00000000-0000-0000-0000-000000000001"},
        )
        metadata = response.json()["metadata"]
        assert "llm_audit" in metadata
        audit = metadata["llm_audit"]
        assert "rounds" in audit
        assert "tool_calls_made" in audit

    def test_snapshot_with_custom_location(self):
        """Lat/lon/district/crop params should be accepted and used."""
        response = client.get(
            "/api/v1/farm/snapshot",
            params={
                "farm_id": "00000000-0000-0000-0000-000000000002",
                "lat": 10.787,
                "lon": 79.138,
                "district": "Thanjavur",
                "main_crop": "Sugarcane",
                "area_acres": 8.0,
            },
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_snapshot_invalid_farm_id(self):
        """Invalid UUID should return 400."""
        response = client.get(
            "/api/v1/farm/snapshot",
            params={"farm_id": "not-a-uuid"},
        )
        assert response.status_code == 400

    def test_snapshot_missing_farm_id(self):
        """Missing farm_id should return 422."""
        response = client.get("/api/v1/farm/snapshot")
        assert response.status_code == 422

    def test_snapshot_health_endpoint(self):
        """Health check sub-endpoint should always return ok."""
        response = client.get("/api/v1/farm/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
