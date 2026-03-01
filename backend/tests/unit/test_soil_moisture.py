"""Unit tests for soil moisture estimator."""

import pytest
from backend.src.services.recommendations.soil_moisture import SoilMoistureEstimator


class TestSoilMoistureEstimator:
    """Test suite for soil moisture estimation."""

    @pytest.fixture
    def estimator(self):
        return SoilMoistureEstimator()

    def test_critical_dry_conditions(self, estimator):
        """Very low rainfall should produce critical moisture status."""
        result = estimator.estimate(
            soil_type="Loam",
            rainfall_7day_mm=0.0,
            rainfall_30day_mm=5.0,
            temperature_avg_c=35.0,
        )
        assert result["success"] is True
        assert result["status"] in ("critical", "low")
        assert result["irrigation_needed"] is True
        assert result["depletion_pct"] >= 40

    def test_adequate_moisture_after_rain(self, estimator):
        """Heavy recent rainfall should indicate adequate moisture."""
        result = estimator.estimate(
            soil_type="Clay",
            rainfall_7day_mm=80.0,
            rainfall_30day_mm=150.0,
            temperature_avg_c=26.0,
        )
        assert result["success"] is True
        assert result["status"] in ("adequate", "moderate")
        assert result["irrigation_needed"] is False

    def test_with_crop_info(self, estimator):
        """Including crop name increases confidence."""
        result = estimator.estimate(
            soil_type="Clay-Loam",
            rainfall_7day_mm=20.0,
            rainfall_30day_mm=60.0,
            temperature_avg_c=28.0,
            crop_name="Rice",
            crop_growth_stage="mid",
        )
        assert result["success"] is True
        assert result["confidence"] > 50
        assert "crop_etc_7day_mm" in result

    def test_confidence_range(self, estimator):
        """Confidence must be between 0 and 100."""
        result = estimator.estimate(
            soil_type="Sandy",
            rainfall_7day_mm=5.0,
            rainfall_30day_mm=20.0,
            temperature_avg_c=30.0,
        )
        assert 0 <= result["confidence"] <= 100

    def test_output_structure(self, estimator):
        """Verify all required fields in output."""
        result = estimator.estimate(
            soil_type="Loam",
            rainfall_7day_mm=15.0,
            rainfall_30day_mm=50.0,
            temperature_avg_c=27.0,
        )
        required_fields = [
            "success",
            "soil_type",
            "current_moisture_mm",
            "available_water_mm",
            "depletion_mm",
            "depletion_pct",
            "status",
            "irrigation_needed",
            "urgency",
            "confidence",
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_unknown_soil_type_defaults(self, estimator):
        """Unknown soil type should fallback gracefully."""
        result = estimator.estimate(
            soil_type="Unknown Exotic Soil",
            rainfall_7day_mm=10.0,
            rainfall_30day_mm=35.0,
            temperature_avg_c=28.0,
        )
        assert result["success"] is True
        assert result["status"] in ("critical", "low", "moderate", "adequate")

    def test_high_temperature_stress(self, estimator):
        """High temperature should reduce moisture fraction."""
        result_hot = estimator.estimate(
            soil_type="Loam",
            rainfall_7day_mm=20.0,
            rainfall_30day_mm=60.0,
            temperature_avg_c=40.0,
        )
        result_mild = estimator.estimate(
            soil_type="Loam",
            rainfall_7day_mm=20.0,
            rainfall_30day_mm=60.0,
            temperature_avg_c=22.0,
        )
        # Hotter conditions should show higher depletion
        assert result_hot["depletion_pct"] >= result_mild["depletion_pct"]

    def test_urgency_levels(self, estimator):
        """Different moisture conditions should produce different urgency levels."""
        # Dry — should be urgent
        dry = estimator.estimate(
            soil_type="Sandy",
            rainfall_7day_mm=0.0,
            rainfall_30day_mm=0.0,
            temperature_avg_c=32.0,
        )
        assert dry["urgency"] in ("immediate", "within_24h")

        # Wet — should not be urgent
        wet = estimator.estimate(
            soil_type="Clay",
            rainfall_7day_mm=100.0,
            rainfall_30day_mm=200.0,
            temperature_avg_c=24.0,
        )
        assert wet["urgency"] in ("none", "within_3days")
