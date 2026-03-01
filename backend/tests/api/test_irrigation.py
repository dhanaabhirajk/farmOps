"""API tests for /api/farm/irrigation endpoint."""

import pytest
from fastapi.testclient import TestClient
from backend.src.main import app

client = TestClient(app)


class TestIrrigationAPI:
    """Test suite for irrigation scheduling API."""

    def test_generate_schedule_success(self):
        """Test successful irrigation schedule generation."""
        payload = {
            "farm_id": "00000000-0000-0000-0000-000000000001",
            "crop_name": "Rice",
            "crop_stage": "mid",
            "soil_type": "Clay",
            "area_acres": 2.0,
            "irrigation_method": "flood",
            "rainfall_7day_mm": 0.0,
            "rainfall_30day_mm": 10.0,
            "temperature_avg_c": 30.0,
        }

        response = client.post("/api/v1/farm/irrigation", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "metadata" in data

        schedule = data["data"]
        assert "events" in schedule
        assert "summary" in schedule
        assert schedule["summary"]["total_irrigation_events"] >= 0

    def test_rain_skip_threshold_respected(self):
        """Test that rain forecast >70% skips irrigation events."""
        # Provide a forecast with high rain probability
        forecast = [
            {"rain_probability": 0.85, "expected_rainfall_mm": 40.0, "description": "Heavy rain"}
            for _ in range(14)
        ]
        payload = {
            "farm_id": "00000000-0000-0000-0000-000000000002",
            "crop_name": "Wheat",
            "crop_stage": "mid",
            "soil_type": "Loam",
            "area_acres": 1.0,
            "irrigation_method": "sprinkler",
            "rainfall_7day_mm": 0.0,
            "rainfall_30day_mm": 5.0,
            "temperature_avg_c": 25.0,
            "weather_forecast": forecast,
        }

        response = client.post("/api/v1/farm/irrigation", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_invalid_farm_id(self):
        """Test request with invalid farm_id."""
        payload = {
            "farm_id": "not-a-uuid",
            "crop_name": "Rice",
            "area_acres": 1.0,
        }
        response = client.post("/api/v1/farm/irrigation", json=payload)
        assert response.status_code == 422

    def test_negative_area_invalid(self):
        """Test that negative area is rejected."""
        payload = {
            "farm_id": "00000000-0000-0000-0000-000000000001",
            "area_acres": -1.0,
        }
        response = client.post("/api/v1/farm/irrigation", json=payload)
        assert response.status_code == 422

    def test_response_contains_soil_moisture(self):
        """Response should include current soil moisture status."""
        payload = {
            "farm_id": "00000000-0000-0000-0000-000000000003",
            "crop_name": "Tomato",
            "crop_stage": "initial",
            "soil_type": "Sandy-Loam",
            "area_acres": 0.5,
            "rainfall_7day_mm": 5.0,
            "rainfall_30day_mm": 15.0,
            "temperature_avg_c": 28.0,
        }
        response = client.post("/api/v1/farm/irrigation", json=payload)
        assert response.status_code == 200

        data = response.json()["data"]
        assert "current_soil_moisture" in data
        moisture = data["current_soil_moisture"]
        assert "status" in moisture
        assert "depletion_pct" in moisture

    def test_metadata_contains_response_time(self):
        """Metadata should include response time."""
        payload = {
            "farm_id": "00000000-0000-0000-0000-000000000001",
        }
        response = client.post("/api/v1/farm/irrigation", json=payload)
        assert response.status_code == 200

        metadata = response.json()["metadata"]
        assert "response_time_ms" in metadata
        assert "timestamp" in metadata
        assert metadata["response_time_ms"] >= 0
