"""Unit tests for estimate_profit LLM tool."""

import pytest
from backend.src.services.ai_tools.estimate_profit import estimate_profit


class TestEstimateProfit:
    """Test suite for profit estimation tool."""

    def test_estimate_profit_basic_calculation(self):
        """Test basic profit calculation."""
        input_data = {
            "crop_name": "Rice",
            "expected_yield_kg_acre": 3000,
            "production_cost_per_acre": 40000,
            "market_price_per_kg": 22.0,
            "price_trend": "stable",
        }

        result = estimate_profit(input_data)

        # Validate output structure
        assert "revenue_per_acre" in result
        assert "total_cost_per_acre" in result
        assert "profit_per_acre" in result
        assert "profit_margin_percent" in result
        assert "breakeven_yield_kg_acre" in result
        assert "price_sensitivity" in result

        # Validate calculations
        expected_revenue = 3000 * 22.0  # 66,000
        assert result["revenue_per_acre"] == expected_revenue
        assert result["total_cost_per_acre"] == 40000
        assert result["profit_per_acre"] == expected_revenue - 40000  # 26,000
        
        # Validate profit margin
        expected_margin = ((expected_revenue - 40000) / expected_revenue) * 100
        assert abs(result["profit_margin_percent"] - expected_margin) < 0.01

        # Validate breakeven
        expected_breakeven = 40000 / 22.0
        assert abs(result["breakeven_yield_kg_acre"] - expected_breakeven) < 0.01

    def test_estimate_profit_increasing_price(self):
        """Test profit calculation with increasing price trend."""
        input_data = {
            "crop_name": "Tomato",
            "expected_yield_kg_acre": 8000,
            "production_cost_per_acre": 60000,
            "market_price_per_kg": 30.0,
            "price_trend": "increasing",
        }

        result = estimate_profit(input_data)

        # With increasing trend, price should be adjusted upward (+10%)
        expected_adjusted_price = 30.0 * 1.10
        expected_revenue = 8000 * expected_adjusted_price
        
        assert abs(result["revenue_per_acre"] - expected_revenue) < 1.0
        assert result["profit_per_acre"] > 0  # Should be profitable

    def test_estimate_profit_decreasing_price(self):
        """Test profit calculation with decreasing price trend."""
        input_data = {
            "crop_name": "Groundnut",
            "expected_yield_kg_acre": 1200,
            "production_cost_per_acre": 50000,
            "market_price_per_kg": 55.0,
            "price_trend": "decreasing",
        }

        result = estimate_profit(input_data)

        # With decreasing trend, price should be adjusted downward (-10%)
        expected_adjusted_price = 55.0 * 0.90
        expected_revenue = 1200 * expected_adjusted_price
        
        assert abs(result["revenue_per_acre"] - expected_revenue) < 1.0
        
        # Profit might be positive or negative depending on adjusted price
        profit = result["profit_per_acre"]
        assert isinstance(profit, (int, float))

    def test_estimate_profit_negative_profit(self):
        """Test profit calculation when cost exceeds revenue."""
        input_data = {
            "crop_name": "Wheat",
            "expected_yield_kg_acre": 1500,
            "production_cost_per_acre": 50000,
            "market_price_per_kg": 25.0,
            "price_trend": "stable",
        }

        result = estimate_profit(input_data)

        # Revenue: 1500 * 25 = 37,500
        # Cost: 50,000
        # Profit: -12,500 (loss)
        
        assert result["revenue_per_acre"] == 37500
        assert result["profit_per_acre"] < 0  # Loss
        assert result["profit_margin_percent"] < 0

    def test_estimate_profit_price_sensitivity(self):
        """Test price sensitivity scenarios."""
        input_data = {
            "crop_name": "Cotton",
            "expected_yield_kg_acre": 800,
            "production_cost_per_acre": 35000,
            "market_price_per_kg": 60.0,
            "price_trend": "stable",
        }

        result = estimate_profit(input_data)

        # Should have 5 scenarios: -20%, -10%, current, +10%, +20%
        sensitivity = result["price_sensitivity"]
        assert len(sensitivity) == 5

        # Validate structure of each scenario
        for scenario in sensitivity:
            assert "price_change_percent" in scenario
            assert "price_per_kg" in scenario
            assert "revenue_per_acre" in scenario
            assert "profit_per_acre" in scenario

        # Scenarios should be in order from -20% to +20%
        assert sensitivity[0]["price_change_percent"] == -20
        assert sensitivity[2]["price_change_percent"] == 0  # Current price
        assert sensitivity[4]["price_change_percent"] == 20

        # Higher price should result in higher profit
        assert sensitivity[0]["profit_per_acre"] < sensitivity[4]["profit_per_acre"]

    def test_estimate_profit_high_margin_crop(self):
        """Test profit for high-margin crop (sugarcane)."""
        input_data = {
            "crop_name": "Sugarcane",
            "expected_yield_kg_acre": 30000,
            "production_cost_per_acre": 80000,
            "market_price_per_kg": 3.5,
            "price_trend": "stable",
        }

        result = estimate_profit(input_data)

        # Revenue: 30,000 * 3.5 = 105,000
        # Cost: 80,000
        # Profit: 25,000
        
        assert result["revenue_per_acre"] == 105000
        assert result["profit_per_acre"] == 25000
        assert result["profit_margin_percent"] > 20  # Healthy margin

    def test_estimate_profit_breakeven_calculation(self):
        """Test breakeven yield calculation."""
        input_data = {
            "crop_name": "Maize",
            "expected_yield_kg_acre": 2500,
            "production_cost_per_acre": 35000,
            "market_price_per_kg": 20.0,
            "price_trend": "stable",
        }

        result = estimate_profit(input_data)

        # Breakeven = Cost / Price = 35,000 / 20 = 1,750 kg/acre
        expected_breakeven = 35000 / 20.0
        assert abs(result["breakeven_yield_kg_acre"] - expected_breakeven) < 0.01

        # Actual yield is higher than breakeven, so should be profitable
        assert result["expected_yield_kg_acre"] > result["breakeven_yield_kg_acre"]
        assert result["profit_per_acre"] > 0

    def test_estimate_profit_zero_yield(self):
        """Test profit calculation with zero yield (crop failure)."""
        input_data = {
            "crop_name": "Rice",
            "expected_yield_kg_acre": 0,
            "production_cost_per_acre": 40000,
            "market_price_per_kg": 22.0,
            "price_trend": "stable",
        }

        result = estimate_profit(input_data)

        # No yield means no revenue, full loss
        assert result["revenue_per_acre"] == 0
        assert result["profit_per_acre"] == -40000
        assert result["profit_margin_percent"] == -100  # Total loss

    def test_estimate_profit_boundary_values(self):
        """Test profit calculation with edge cases."""
        input_data = {
            "crop_name": "Rice",
            "expected_yield_kg_acre": 1,  # Very low yield
            "production_cost_per_acre": 1000,
            "market_price_per_kg": 1.0,
            "price_trend": "stable",
        }

        result = estimate_profit(input_data)

        # Should complete without errors
        assert result["revenue_per_acre"] == 1
        assert result["profit_per_acre"] == -999
        assert len(result["price_sensitivity"]) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
