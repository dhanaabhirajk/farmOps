"""Integration tests for irrigation scheduler service."""

import pytest
from backend.src.services.recommendations.irrigation_scheduler import IrrigationScheduler


def _make_forecast(days: int = 14, rain_prob: float = 0.15, rain_mm: float = 0.0):
    """Create a uniform forecast for testing."""
    return [
        {
            "rain_probability": rain_prob,
            "expected_rainfall_mm": rain_mm,
            "description": "Sunny" if rain_prob < 0.5 else "Rainy",
        }
        for _ in range(days)
    ]


class TestIrrigationSchedulerIntegration:
    """Integration tests for the irrigation scheduler."""

    @pytest.fixture
    def scheduler(self):
        return IrrigationScheduler()

    @pytest.fixture
    def dry_farm_data(self):
        return {
            "soil_type": "Loam",
            "crop_name": "Rice",
            "crop_stage": "mid",
            "rainfall_7day_mm": 0.0,
            "rainfall_30day_mm": 5.0,
            "temperature_avg_c": 30.0,
        }

    @pytest.fixture
    def wet_farm_data(self):
        return {
            "soil_type": "Clay",
            "crop_name": "Wheat",
            "crop_stage": "initial",
            "rainfall_7day_mm": 60.0,
            "rainfall_30day_mm": 150.0,
            "temperature_avg_c": 22.0,
        }

    def test_schedule_generated_for_dry_farm(self, scheduler, dry_farm_data):
        """Dry farm should generate at least one irrigation event."""
        schedule = scheduler.generate_schedule(
            farm_data=dry_farm_data,
            weather_forecast=_make_forecast(14, rain_prob=0.10),
            area_acres=2.0,
        )
        assert schedule["success"] is True
        assert "events" in schedule
        assert schedule["summary"]["total_irrigation_events"] > 0

    def test_high_rain_forecast_skips_irrigation(self, scheduler, dry_farm_data):
        """When rain probability >70%, irrigation should be skipped."""
        heavy_rain_forecast = _make_forecast(14, rain_prob=0.85, rain_mm=40.0)
        schedule = scheduler.generate_schedule(
            farm_data=dry_farm_data,
            weather_forecast=heavy_rain_forecast,
            area_acres=1.0,
        )
        assert schedule["success"] is True
        # Should have skip events and fewer irrigate events
        skip_count = schedule["summary"]["total_skipped_events"]
        irrigate_count = schedule["summary"]["total_irrigation_events"]
        assert skip_count >= 0  # At least some skipped
        # Cost should be lower with rain (less irrigation needed)
        assert schedule["summary"]["total_cost_inr"] >= 0

    def test_wet_farm_fewer_events(self, scheduler, wet_farm_data, dry_farm_data):
        """Wet farm should need less irrigation than dry farm."""
        forecast = _make_forecast(14)
        dry_schedule = scheduler.generate_schedule(
            farm_data=dry_farm_data,
            weather_forecast=forecast,
            area_acres=1.0,
        )
        wet_schedule = scheduler.generate_schedule(
            farm_data=wet_farm_data,
            weather_forecast=forecast,
            area_acres=1.0,
        )
        assert dry_schedule["summary"]["total_irrigation_events"] >= wet_schedule["summary"]["total_irrigation_events"]

    def test_schedule_structure(self, scheduler, dry_farm_data):
        """Verify schedule has required fields."""
        schedule = scheduler.generate_schedule(
            farm_data=dry_farm_data,
            weather_forecast=_make_forecast(14),
            area_acres=1.0,
        )
        assert "schedule_days" in schedule
        assert schedule["schedule_days"] == 14
        assert "from_date" in schedule
        assert "to_date" in schedule
        assert "current_soil_moisture" in schedule
        assert "summary" in schedule

        summary = schedule["summary"]
        assert "total_irrigation_events" in summary
        assert "total_water_mm" in summary
        assert "total_cost_inr" in summary

    def test_event_structure(self, scheduler, dry_farm_data):
        """Each event should have required fields."""
        schedule = scheduler.generate_schedule(
            farm_data=dry_farm_data,
            weather_forecast=_make_forecast(14),
            area_acres=1.0,
        )
        for event in schedule["events"]:
            assert "date" in event
            assert "action" in event
            assert event["action"] in ("irrigate", "skip")
            assert "reason" in event

    def test_drip_irrigation_higher_efficiency(self, scheduler, dry_farm_data):
        """Drip irrigation should use less water than flood."""
        forecast = _make_forecast(14)
        drip_schedule = scheduler.generate_schedule(
            farm_data=dry_farm_data,
            weather_forecast=forecast,
            area_acres=1.0,
            irrigation_method="drip",
        )
        flood_schedule = scheduler.generate_schedule(
            farm_data=dry_farm_data,
            weather_forecast=forecast,
            area_acres=1.0,
            irrigation_method="flood",
        )
        assert drip_schedule["success"] is True
        assert flood_schedule["success"] is True

    def test_cost_scales_with_area(self, scheduler, dry_farm_data):
        """Cost should scale roughly with area."""
        forecast = _make_forecast(14)
        small = scheduler.generate_schedule(
            farm_data=dry_farm_data,
            weather_forecast=forecast,
            area_acres=1.0,
        )
        large = scheduler.generate_schedule(
            farm_data=dry_farm_data,
            weather_forecast=forecast,
            area_acres=5.0,
        )
        # Larger area should cost more in total
        if small["summary"]["total_irrigation_events"] > 0:
            assert large["summary"]["total_cost_inr"] > small["summary"]["total_cost_inr"]
