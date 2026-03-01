"""API tests for /api/farm/recommendations endpoint."""

import pytest
from fastapi.testclient import TestClient
from backend.src.main import app


client = TestClient(app)


class TestRecommendationsAPI:
    """Test suite for crop recommendations API."""

    def test_generate_recommendations_success(self):
        """Test successful recommendation generation."""
        payload = {
            "farm_id": "00000000-0000-0000-0000-000000000001",
            "season": "Samba",
            "use_cache": False,
        }

        response = client.post("/api/v1/farm/recommendations", json=payload)

        # Validate response status
        assert response.status_code == 200

        # Validate response structure
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        assert "metadata" in data

        # Validate data structure
        rec_data = data["data"]
        assert "recommended_crops" in rec_data
        assert "season" in rec_data
        assert "confidence" in rec_data
        assert "explanation" in rec_data
        assert "tool_calls" in rec_data

        # Should return 3 recommendations
        assert len(rec_data["recommended_crops"]) == 3

        # Validate each recommendation
        for rec in rec_data["recommended_crops"]:
            assert "crop_name" in rec
            assert "rank" in rec
            assert "expected_yield_kg_acre" in rec
            assert "profit_per_acre" in rec
            assert "risk_score" in rec
            assert "planting_window" in rec
            assert "water_requirement_mm" in rec

        # Validate metadata
        metadata = data["metadata"]
        assert "cached" in metadata
        assert "response_time_ms" in metadata
        assert "timestamp" in metadata

    def test_generate_recommendations_with_cache(self):
        """Test recommendation generation with caching."""
        payload = {
            "farm_id": "00000000-0000-0000-0000-000000000002",
            "season": "Kharif",
            "use_cache": True,
        }

        # First request (cold)
        response1 = client.post("/api/v1/farm/recommendations", json=payload)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["metadata"]["cached"] is False

        # Second request (should be cached)
        response2 = client.post("/api/v1/farm/recommendations", json=payload)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["metadata"]["cached"] is True

        # Cached response should be faster
        assert data2["metadata"]["response_time_ms"] < data1["metadata"]["response_time_ms"]

    def test_generate_recommendations_different_seasons(self):
        """Test recommendation generation for different seasons."""
        farm_id = "00000000-0000-0000-0000-000000000003"
        seasons = ["Kharif", "Rabi", "Summer", "Kar", "Samba", "Thaladi"]

        for season in seasons:
            payload = {
                "farm_id": farm_id,
                "season": season,
                "use_cache": False,
            }

            response = client.post("/api/v1/farm/recommendations", json=payload)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["data"]["season"] == season
            assert len(data["data"]["recommended_crops"]) == 3

    def test_generate_recommendations_invalid_farm_id(self):
        """Test recommendation generation with invalid farm ID format."""
        payload = {
            "farm_id": "invalid-uuid",
            "season": "Samba",
            "use_cache": False,
        }

        response = client.post("/api/v1/farm/recommendations", json=payload)

        # Should return validation error
        assert response.status_code == 422  # Unprocessable Entity

    def test_generate_recommendations_missing_fields(self):
        """Test recommendation generation with missing required fields."""
        # Missing season
        payload = {
            "farm_id": "00000000-0000-0000-0000-000000000001",
            "use_cache": False,
        }

        response = client.post("/api/v1/farm/recommendations", json=payload)
        assert response.status_code == 422

    def test_get_recommendations_history(self):
        """Test retrieving historical recommendations."""
        farm_id = "00000000-0000-0000-0000-000000000001"

        response = client.get(f"/api/v1/farm/recommendations/{farm_id}")

        # Currently stubbed, but should return 200
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True

    def test_get_recommendations_history_with_filters(self):
        """Test retrieving historical recommendations with filters."""
        farm_id = "00000000-0000-0000-0000-000000000001"
        params = {
            "season": "Samba",
            "status": "active",
            "limit": 10,
        }

        response = client.get(f"/api/v1/farm/recommendations/{farm_id}", params=params)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_invalidate_cache(self):
        """Test cache invalidation."""
        farm_id = "00000000-0000-0000-0000-000000000001"

        response = client.delete(f"/api/v1/farm/recommendations/cache/{farm_id}")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "message" in data

    def test_invalidate_cache_specific_season(self):
        """Test cache invalidation for specific season."""
        farm_id = "00000000-0000-0000-0000-000000000001"
        params = {"season": "Samba"}

        response = client.delete(f"/api/v1/farm/recommendations/cache/{farm_id}", params=params)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_recommendation_ranking_order(self):
        """Test that recommendations are properly ranked."""
        payload = {
            "farm_id": "00000000-0000-0000-0000-000000000001",
            "season": "Samba",
            "use_cache": False,
        }

        response = client.post("/api/v1/farm/recommendations", json=payload)
        data = response.json()

        recommendations = data["data"]["recommended_crops"]

        # Verify ranks are sequential
        for i, rec in enumerate(recommendations):
            assert rec["rank"] == i + 1

        # Verify risk-adjusted profit is in descending order
        for i in range(len(recommendations) - 1):
            current = recommendations[i]
            next_rec = recommendations[i + 1]

            current_adjusted = current["profit_per_acre"] * (1 - current["risk_score"])
            next_adjusted = next_rec["profit_per_acre"] * (1 - next_rec["risk_score"])

            assert current_adjusted >= next_adjusted

    def test_recommendation_confidence_bounds(self):
        """Test that confidence scores are within valid bounds."""
        payload = {
            "farm_id": "00000000-0000-0000-0000-000000000001",
            "season": "Samba",
            "use_cache": False,
        }

        response = client.post("/api/v1/farm/recommendations", json=payload)
        data = response.json()

        confidence = data["data"]["confidence"]

        # Confidence should be between 50 and 90
        assert 50 <= confidence <= 90

    def test_response_time_sla(self):
        """Test that response times meet SLA requirements."""
        payload = {
            "farm_id": "00000000-0000-0000-0000-000000000001",
            "season": "Samba",
            "use_cache": False,
        }

        # Cold request
        response1 = client.post("/api/v1/farm/recommendations", json=payload)
        data1 = response1.json()
        cold_time = data1["metadata"]["response_time_ms"]

        # Should be < 10 seconds (10,000 ms) for cold
        assert cold_time < 10000

        # Cached request
        response2 = client.post("/api/v1/farm/recommendations", json=payload)
        data2 = response2.json()
        cached_time = data2["metadata"]["response_time_ms"]

        # Should be < 2 seconds (2,000 ms) for cached
        assert cached_time < 2000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
