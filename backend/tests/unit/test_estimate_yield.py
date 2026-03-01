"""Unit tests for estimate_yield LLM tool."""

import pytest
from backend.src.services.ai_tools.estimate_yield import estimate_yield


class TestEstimateYield:
    """Test suite for yield estimation tool."""

    def test_estimate_yield_rice_optimal_conditions(self):
        """Test yield estimation for rice under optimal conditions."""
        input_data = {
            "crop_name": "Rice",
            "area_acres": 2.5,
            "soil": {
                "type": "Clay",
                "pH": 7.0,
                "organic_carbon_pct": 0.8,
                "nitrogen_kg_ha": 280,
                "phosphorus_kg_ha": 60,
                "potassium_kg_ha": 120,
            },
            "climate": {
                "rainfall_mm": 1200,
                "avg_temp_celsius": 28,
            },
            "irrigation_available": True,
        }

        result = estimate_yield(input_data)

        # Validate output structure
        assert "expected_yield_kg_acre" in result
        assert "yield_quality_grade" in result
        assert "confidence" in result
        assert "factors_considered" in result

        # Validate values
        assert result["expected_yield_kg_acre"] > 0
        assert result["confidence"] >= 0 and result["confidence"] <= 100
        assert result["yield_quality_grade"] in ["excellent", "good", "average", "poor"]

        # Optimal conditions should give high confidence and good quality
        assert result["confidence"] >= 70
        assert result["yield_quality_grade"] in ["excellent", "good"]

    def test_estimate_yield_wheat_poor_soil(self):
        """Test yield estimation for wheat with poor soil conditions."""
        input_data = {
            "crop_name": "Wheat",
            "area_acres": 5.0,
            "soil": {
                "type": "Sandy",
                "pH": 5.5,  # Too acidic for wheat
                "organic_carbon_pct": 0.3,  # Low organic matter
                "nitrogen_kg_ha": 100,  # Low nitrogen
                "phosphorus_kg_ha": 20,
                "potassium_kg_ha": 40,
            },
            "climate": {
                "rainfall_mm": 300,
                "avg_temp_celsius": 25,
            },
            "irrigation_available": False,
        }

        result = estimate_yield(input_data)

        # Poor conditions should result in lower yield and confidence
        assert result["expected_yield_kg_acre"] > 0  # Should still produce something
        assert result["confidence"] < 70  # Lower confidence
        assert result["yield_quality_grade"] in ["average", "poor"]

    def test_estimate_yield_sugarcane_high_water(self):
        """Test yield estimation for water-intensive sugarcane."""
        input_data = {
            "crop_name": "Sugarcane",
            "area_acres": 10.0,
            "soil": {
                "type": "Alluvial",
                "pH": 7.5,
                "organic_carbon_pct": 1.0,
                "nitrogen_kg_ha": 350,
                "phosphorus_kg_ha": 80,
                "potassium_kg_ha": 150,
            },
            "climate": {
                "rainfall_mm": 1500,
                "avg_temp_celsius": 30,
            },
            "irrigation_available": True,
        }

        result = estimate_yield(input_data)

        # Sugarcane with good conditions should have high yield
        assert result["expected_yield_kg_acre"] > 10000  # Sugarcane has very high yield
        assert result["confidence"] >= 75
        assert result["yield_quality_grade"] in ["excellent", "good"]

    def test_estimate_yield_tomato_without_irrigation(self):
        """Test yield estimation for tomato without irrigation in low rainfall."""
        input_data = {
            "crop_name": "Tomato",
            "area_acres": 1.0,
            "soil": {
                "type": "Red",
                "pH": 6.5,
                "organic_carbon_pct": 0.6,
                "nitrogen_kg_ha": 200,
                "phosphorus_kg_ha": 50,
                "potassium_kg_ha": 100,
            },
            "climate": {
                "rainfall_mm": 400,  # Low rainfall
                "avg_temp_celsius": 26,
            },
            "irrigation_available": False,
        }

        result = estimate_yield(input_data)

        # Water stress should reduce yield and confidence
        assert result["expected_yield_kg_acre"] > 0
        assert result["confidence"] < 80  # Should reflect uncertainty
        # Check that water stress is mentioned in factors
        assert any("water" in factor.lower() or "irrigation" in factor.lower() 
                   for factor in result["factors_considered"])

    def test_estimate_yield_invalid_crop(self):
        """Test yield estimation with unsupported crop."""
        input_data = {
            "crop_name": "InvalidCrop",
            "area_acres": 2.0,
            "soil": {
                "type": "Clay",
                "pH": 7.0,
                "organic_carbon_pct": 0.8,
                "nitrogen_kg_ha": 280,
                "phosphorus_kg_ha": 60,
                "potassium_kg_ha": 120,
            },
            "climate": {
                "rainfall_mm": 1000,
                "avg_temp_celsius": 28,
            },
            "irrigation_available": True,
        }

        # Should raise an error for unsupported crop
        with pytest.raises(ValueError, match="not supported"):
            estimate_yield(input_data)

    def test_estimate_yield_extreme_temperature(self):
        """Test yield estimation with extreme temperatures."""
        input_data = {
            "crop_name": "Wheat",
            "area_acres": 3.0,
            "soil": {
                "type": "Loamy",
                "pH": 7.0,
                "organic_carbon_pct": 0.8,
                "nitrogen_kg_ha": 280,
                "phosphorus_kg_ha": 60,
                "potassium_kg_ha": 120,
            },
            "climate": {
                "rainfall_mm": 600,
                "avg_temp_celsius": 40,  # Too hot for wheat
            },
            "irrigation_available": True,
        }

        result = estimate_yield(input_data)

        # Extreme temperature should negatively impact yield
        assert result["confidence"] < 70
        assert any("temperature" in factor.lower() for factor in result["factors_considered"])

    def test_estimate_yield_boundary_conditions(self):
        """Test yield estimation with boundary condition values."""
        input_data = {
            "crop_name": "Maize",
            "area_acres": 0.5,  # Small area
            "soil": {
                "type": "Black",
                "pH": 8.5,  # High pH
                "organic_carbon_pct": 0.2,  # Low organic carbon
                "nitrogen_kg_ha": 50,  # Very low nitrogen
                "phosphorus_kg_ha": 10,
                "potassium_kg_ha": 20,
            },
            "climate": {
                "rainfall_mm": 200,  # Very low rainfall
                "avg_temp_celsius": 35,
            },
            "irrigation_available": False,
        }

        result = estimate_yield(input_data)

        # Should complete without errors even with poor conditions
        assert result["expected_yield_kg_acre"] > 0
        assert result["confidence"] >= 0 and result["confidence"] <= 100
        assert len(result["factors_considered"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
