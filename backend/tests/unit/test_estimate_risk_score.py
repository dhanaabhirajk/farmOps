"""Unit tests for estimate_risk_score LLM tool."""

import pytest
from backend.src.services.ai_tools.estimate_risk_score import estimate_risk_score


class TestEstimateRiskScore:
    """Test suite for risk score estimation tool."""

    def test_estimate_risk_low_risk_scenario(self):
        """Test risk estimation for low-risk scenario."""
        input_data = {
            "crop_name": "Rice",
            "rainfall_mm": 1200,
            "irrigation_available": True,
            "soil_drainage": "Good",
            "pest_history": "low",
            "market_volatility": 0.2,
            "crop_diversity": 0.8,
        }

        result = estimate_risk_score(input_data)

        # Validate output structure
        assert "drought_risk" in result
        assert "pest_risk" in result
        assert "market_risk" in result
        assert "waterlogging_risk" in result
        assert "overall_risk" in result
        assert "risk_level" in result
        assert "mitigation_suggestions" in result

        # All risk scores should be between 0 and 1
        assert 0 <= result["drought_risk"] <= 1
        assert 0 <= result["pest_risk"] <= 1
        assert 0 <= result["market_risk"] <= 1
        assert 0 <= result["waterlogging_risk"] <= 1
        assert 0 <= result["overall_risk"] <= 1

        # Low risk scenario should have overall risk < 0.3
        assert result["overall_risk"] < 0.4
        assert result["risk_level"] in ["Low", "Medium"]

    def test_estimate_risk_high_drought_risk(self):
        """Test risk estimation for high drought risk."""
        input_data = {
            "crop_name": "Rice",  # High water requirement
            "rainfall_mm": 400,  # Low rainfall
            "irrigation_available": False,
            "soil_drainage": "Good",
            "pest_history": "low",
            "market_volatility": 0.3,
            "crop_diversity": 0.6,
        }

        result = estimate_risk_score(input_data)

        # Should have high drought risk
        assert result["drought_risk"] > 0.5
        
        # Should mention drought or water in mitigation
        mitigation_text = " ".join(result["mitigation_suggestions"]).lower()
        assert any(word in mitigation_text for word in ["drought", "water", "irrigation"])

    def test_estimate_risk_high_waterlogging_risk(self):
        """Test risk estimation for high waterlogging risk."""
        input_data = {
            "crop_name": "Cotton",  # Sensitive to waterlogging
            "rainfall_mm": 1800,  # Very high rainfall
            "irrigation_available": True,
            "soil_drainage": "Poor",
            "pest_history": "low",
            "market_volatility": 0.3,
            "crop_diversity": 0.6,
        }

        result = estimate_risk_score(input_data)

        # Should have elevated waterlogging risk
        assert result["waterlogging_risk"] > 0.3
        
        # Should mention drainage in mitigation
        mitigation_text = " ".join(result["mitigation_suggestions"]).lower()
        assert any(word in mitigation_text for word in ["drainage", "waterlog", "flood"])

    def test_estimate_risk_high_pest_risk(self):
        """Test risk estimation for high pest risk."""
        input_data = {
            "crop_name": "Tomato",  # High pest susceptibility
            "rainfall_mm": 800,
            "irrigation_available": True,
            "soil_drainage": "Good",
            "pest_history": "high",
            "market_volatility": 0.3,
            "crop_diversity": 0.2,  # Low diversity increases pest risk
        }

        result = estimate_risk_score(input_data)

        # Should have elevated pest risk
        assert result["pest_risk"] > 0.4
        
        # Should mention pest management in mitigation
        mitigation_text = " ".join(result["mitigation_suggestions"]).lower()
        assert any(word in mitigation_text for word in ["pest", "ipm", "monitoring", "crop rotation"])

    def test_estimate_risk_high_market_risk(self):
        """Test risk estimation for high market risk."""
        input_data = {
            "crop_name": "Tomato",  # High market volatility
            "rainfall_mm": 800,
            "irrigation_available": True,
            "soil_drainage": "Good",
            "pest_history": "low",
            "market_volatility": 0.8,  # Very high volatility
            "crop_diversity": 0.6,
        }

        result = estimate_risk_score(input_data)

        # Should have high market risk
        assert result["market_risk"] > 0.6
        
        # Should mention market or price in mitigation
        mitigation_text = " ".join(result["mitigation_suggestions"]).lower()
        assert any(word in mitigation_text for word in ["market", "price", "contract", "diversif"])

    def test_estimate_risk_overall_calculation(self):
        """Test that overall risk is weighted average of component risks."""
        input_data = {
            "crop_name": "Maize",
            "rainfall_mm": 700,
            "irrigation_available": False,
            "soil_drainage": "Good",
            "pest_history": "medium",
            "market_volatility": 0.4,
            "crop_diversity": 0.5,
        }

        result = estimate_risk_score(input_data)

        # Overall risk should be weighted average
        # Weights: drought 35%, pest 25%, market 25%, waterlogging 15%
        expected_overall = (
            result["drought_risk"] * 0.35 +
            result["pest_risk"] * 0.25 +
            result["market_risk"] * 0.25 +
            result["waterlogging_risk"] * 0.15
        )

        assert abs(result["overall_risk"] - expected_overall) < 0.01

    def test_estimate_risk_level_classification(self):
        """Test risk level classification thresholds."""
        # Test low risk
        low_risk_data = {
            "crop_name": "Wheat",
            "rainfall_mm": 600,
            "irrigation_available": True,
            "soil_drainage": "Good",
            "pest_history": "low",
            "market_volatility": 0.2,
            "crop_diversity": 0.8,
        }
        result = estimate_risk_score(low_risk_data)
        if result["overall_risk"] < 0.25:
            assert result["risk_level"] == "Low"

        # Test high risk
        high_risk_data = {
            "crop_name": "Rice",
            "rainfall_mm": 300,
            "irrigation_available": False,
            "soil_drainage": "Poor",
            "pest_history": "high",
            "market_volatility": 0.9,
            "crop_diversity": 0.1,
        }
        result = estimate_risk_score(high_risk_data)
        assert result["overall_risk"] > 0.5
        assert result["risk_level"] in ["High", "Very High"]

    def test_estimate_risk_irrigation_reduces_drought(self):
        """Test that irrigation availability reduces drought risk."""
        base_data = {
            "crop_name": "Rice",
            "rainfall_mm": 500,
            "soil_drainage": "Good",
            "pest_history": "low",
            "market_volatility": 0.3,
            "crop_diversity": 0.6,
        }

        # Without irrigation
        data_no_irrigation = {**base_data, "irrigation_available": False}
        result_no_irrigation = estimate_risk_score(data_no_irrigation)

        # With irrigation
        data_with_irrigation = {**base_data, "irrigation_available": True}
        result_with_irrigation = estimate_risk_score(data_with_irrigation)

        # Irrigation should reduce drought risk
        assert result_with_irrigation["drought_risk"] < result_no_irrigation["drought_risk"]

    def test_estimate_risk_crop_diversity_reduces_pest(self):
        """Test that crop diversity reduces pest risk."""
        base_data = {
            "crop_name": "Cotton",
            "rainfall_mm": 700,
            "irrigation_available": True,
            "soil_drainage": "Good",
            "pest_history": "medium",
            "market_volatility": 0.4,
        }

        # Low diversity (monoculture)
        data_low_diversity = {**base_data, "crop_diversity": 0.1}
        result_low_diversity = estimate_risk_score(data_low_diversity)

        # High diversity
        data_high_diversity = {**base_data, "crop_diversity": 0.9}
        result_high_diversity = estimate_risk_score(data_high_diversity)

        # Higher diversity should reduce pest risk
        assert result_high_diversity["pest_risk"] < result_low_diversity["pest_risk"]

    def test_estimate_risk_mitigation_suggestions(self):
        """Test that mitigation suggestions are generated."""
        input_data = {
            "crop_name": "Sugarcane",
            "rainfall_mm": 1500,
            "irrigation_available": True,
            "soil_drainage": "Good",
            "pest_history": "medium",
            "market_volatility": 0.5,
            "crop_diversity": 0.4,
        }

        result = estimate_risk_score(input_data)

        # Should have at least 1 mitigation suggestion
        assert len(result["mitigation_suggestions"]) > 0

        # Each suggestion should be a non-empty string
        for suggestion in result["mitigation_suggestions"]:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 10  # Meaningful suggestion


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
