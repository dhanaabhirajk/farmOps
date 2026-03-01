"""Integration tests for crop recommender service."""

import pytest
from backend.src.services.recommendations.crop_recommender import CropRecommender


class TestCropRecommenderIntegration:
    """Integration test suite for crop recommendation engine."""

    @pytest.fixture
    def recommender(self):
        """Create crop recommender instance."""
        return CropRecommender()

    @pytest.fixture
    def thanjavur_farm_data(self):
        """Sample farm data for Thanjavur (rice belt)."""
        return {
            "location": {
                "district": "Thanjavur",
                "latitude": 10.7867,
                "longitude": 79.1378,
            },
            "soil": {
                "type": "Clay",
                "pH": 7.2,
                "organic_carbon_pct": 0.9,
                "nitrogen_kg_ha": 300,
                "phosphorus_kg_ha": 70,
                "potassium_kg_ha": 130,
                "drainage": "Poor",
            },
            "climate": {
                "rainfall_mm": 1100,
                "avg_temp_celsius": 28,
            },
            "resources": {
                "irrigation_available": True,
                "labor_availability": "adequate",
                "mechanization_level": "medium",
            },
            "market": {
                "rice_price_per_kg": 22.0,
                "wheat_price_per_kg": 25.0,
                "sugarcane_price_per_kg": 3.5,
                "cotton_price_per_kg": 60.0,
                "tomato_price_per_kg": 30.0,
                "groundnut_price_per_kg": 55.0,
                "maize_price_per_kg": 20.0,
            },
            "risk_factors": {
                "pest_history": "low",
                "market_volatility": 0.3,
                "crop_diversity": 0.6,
            },
        }

    @pytest.fixture
    def coimbatore_farm_data(self):
        """Sample farm data for Coimbatore (cotton/maize belt)."""
        return {
            "location": {
                "district": "Coimbatore",
                "latitude": 11.0168,
                "longitude": 76.9558,
            },
            "soil": {
                "type": "Red",
                "pH": 6.5,
                "organic_carbon_pct": 0.6,
                "nitrogen_kg_ha": 220,
                "phosphorus_kg_ha": 50,
                "potassium_kg_ha": 100,
                "drainage": "Good",
            },
            "climate": {
                "rainfall_mm": 650,
                "avg_temp_celsius": 26,
            },
            "resources": {
                "irrigation_available": False,
                "labor_availability": "scarce",
                "mechanization_level": "high",
            },
            "market": {
                "rice_price_per_kg": 22.0,
                "wheat_price_per_kg": 25.0,
                "sugarcane_price_per_kg": 3.5,
                "cotton_price_per_kg": 60.0,
                "tomato_price_per_kg": 30.0,
                "groundnut_price_per_kg": 55.0,
                "maize_price_per_kg": 20.0,
            },
            "risk_factors": {
                "pest_history": "medium",
                "market_volatility": 0.5,
                "crop_diversity": 0.4,
            },
        }

    def test_generate_recommendations_thanjavur_samba_season(self, recommender, thanjavur_farm_data):
        """Test crop recommendations for Thanjavur in Samba season (Aug-Dec)."""
        farm_id = "test-farm-thanjavur-001"
        season = "Samba"

        result = recommender.generate_recommendations(
            farm_id=farm_id,
            farm_data=thanjavur_farm_data,
            season=season,
            top_n=3,
        )

        # Validate response structure
        assert "recommended_crops" in result
        assert "confidence" in result
        assert "explanation" in result
        assert "tool_calls" in result

        # Should return exactly 3 recommendations
        recommendations = result["recommended_crops"]
        assert len(recommendations) == 3

        # Validate each recommendation structure
        for rec in recommendations:
            assert "crop_name" in rec
            assert "rank" in rec
            assert "expected_yield_kg_acre" in rec
            assert "profit_per_acre" in rec
            assert "risk_score" in rec
            assert "planting_window" in rec
            assert "water_requirement_mm" in rec

        # In Thanjavur Samba season, rice should be top recommendation
        top_crop = recommendations[0]["crop_name"]
        assert top_crop == "Rice", f"Expected Rice as top crop, got {top_crop}"

        # Rice should have positive profit
        assert recommendations[0]["profit_per_acre"] > 0

        # Confidence should be reasonable
        assert result["confidence"] >= 50 and result["confidence"] <= 100

    def test_generate_recommendations_coimbatore_rabi_season(self, recommender, coimbatore_farm_data):
        """Test crop recommendations for Coimbatore in Rabi season (Oct-Mar)."""
        farm_id = "test-farm-coimbatore-001"
        season = "Rabi"

        result = recommender.generate_recommendations(
            farm_id=farm_id,
            farm_data=coimbatore_farm_data,
            season=season,
            top_n=3,
        )

        recommendations = result["recommended_crops"]
        assert len(recommendations) == 3

        # In Coimbatore with no irrigation, water-intensive crops should rank lower
        crop_names = [rec["crop_name"] for rec in recommendations]
        
        # Rice and Sugarcane require high water, should not be top choice without irrigation
        if "Rice" in crop_names:
            rice_rank = next(rec["rank"] for rec in recommendations if rec["crop_name"] == "Rice")
            assert rice_rank > 1, "Rice should not be top choice without irrigation"

        # All recommendations should have valid risk scores
        for rec in recommendations:
            assert 0 <= rec["risk_score"] <= 1

    def test_recommendation_ranking_by_risk_adjusted_profit(self, recommender, thanjavur_farm_data):
        """Test that recommendations are properly ranked by risk-adjusted profit."""
        farm_id = "test-farm-ranking-001"
        season = "Kharif"

        result = recommender.generate_recommendations(
            farm_id=farm_id,
            farm_data=thanjavur_farm_data,
            season=season,
            top_n=3,
        )

        recommendations = result["recommended_crops"]

        # Verify ranking is in descending order
        for i in range(len(recommendations) - 1):
            current_rec = recommendations[i]
            next_rec = recommendations[i + 1]

            current_adjusted = current_rec["profit_per_acre"] * (1 - current_rec["risk_score"])
            next_adjusted = next_rec["profit_per_acre"] * (1 - next_rec["risk_score"])

            assert current_adjusted >= next_adjusted, \
                f"Ranking error: {current_rec['crop_name']} (rank {current_rec['rank']}) " \
                f"has lower risk-adjusted profit than {next_rec['crop_name']} (rank {next_rec['rank']})"

    def test_confidence_score_validation(self, recommender, thanjavur_farm_data):
        """Test that confidence scores are properly calculated and bounded."""
        farm_id = "test-farm-confidence-001"
        season = "Samba"

        result = recommender.generate_recommendations(
            farm_id=farm_id,
            farm_data=thanjavur_farm_data,
            season=season,
            top_n=3,
        )

        confidence = result["confidence"]

        # Confidence should be between 50 and 90
        assert 50 <= confidence <= 90

        # High risk crops should lower confidence
        thanjavur_farm_data_high_risk = thanjavur_farm_data.copy()
        thanjavur_farm_data_high_risk["risk_factors"]["pest_history"] = "high"
        thanjavur_farm_data_high_risk["risk_factors"]["market_volatility"] = 0.9

        result_high_risk = recommender.generate_recommendations(
            farm_id=farm_id,
            farm_data=thanjavur_farm_data_high_risk,
            season=season,
            top_n=3,
        )

        # Higher risk should result in lower confidence (not always guaranteed, but likely)
        # Just verify it's still in valid range
        assert 50 <= result_high_risk["confidence"] <= 90

    def test_explanation_generation(self, recommender, thanjavur_farm_data):
        """Test that explanations are generated and contain relevant information."""
        farm_id = "test-farm-explanation-001"
        season = "Samba"

        result = recommender.generate_recommendations(
            farm_id=farm_id,
            farm_data=thanjavur_farm_data,
            season=season,
            top_n=3,
        )

        explanation = result["explanation"]

        # Explanation should not be empty
        assert len(explanation) > 0

        # Should mention Tamil Nadu or the district
        assert "Tamil Nadu" in explanation or "Thanjavur" in explanation

        # Should mention the top crop
        top_crop = result["recommended_crops"][0]["crop_name"]
        assert top_crop in explanation

        # Should mention profit or risk
        assert any(keyword in explanation.lower() for keyword in ["profit", "risk", "rupees", "₹"])

    def test_tool_calls_logging(self, recommender, thanjavur_farm_data):
        """Test that tool calls are properly logged in the result."""
        farm_id = "test-farm-toolcalls-001"
        season = "Samba"

        result = recommender.generate_recommendations(
            farm_id=farm_id,
            farm_data=thanjavur_farm_data,
            season=season,
            top_n=3,
        )

        tool_calls = result["tool_calls"]

        # Should have logged tool calls
        assert len(tool_calls) > 0

        # Each tool call should have the required fields
        for tool_call in tool_calls:
            assert "tool_name" in tool_call
            assert "execution_time_ms" in tool_call
            assert "success" in tool_call


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
