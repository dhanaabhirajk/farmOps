"""Crop Knowledge Base Service.

Provides crop-specific data for cultivating timing, water requirements, growth stages,
and best practices for Tamil Nadu agriculture.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CropKnowledge:
    """Crop knowledge base for Tamil Nadu agriculture."""

    def __init__(self):
        """Initialize crop knowledge base."""
        self._load_crop_data()

    def _load_crop_data(self):
        """Load crop cultivation data."""
        self.crop_database = {
            "Rice": {
                "scientific_name": "Oryza sativa",
                "seasons": ["Kar", "Samba", "Thaladi"],
                "planting_windows": {
                    "Kar": {"start": "06-01", "end": "07-15"},
                    "Samba": {"start": "08-01", "end": "09-30"},
                    "Thaladi": {"start": "12-15", "end": "01-31"},
                },
                "duration_days": 120,
                "water_requirement_mm": 1200,
                "suitable_soil": ["Clay", "Clay-Loam"],
                "optimal_ph": [6.0, 7.5],
                "optimal_temp_c": [25, 35],
                "npk_ratio": "120:60:40",
            },
            "Wheat": {
                "scientific_name": "Triticum aestivum",
                "seasons": ["Rabi"],
                "planting_windows": {
                    "Rabi": {"start": "11-01", "end": "12-15"},
                },
                "duration_days": 110,
                "water_requirement_mm": 450,
                "suitable_soil": ["Loamy", "Clay-Loam"],
                "optimal_ph": [6.5, 7.5],
                "optimal_temp_c": [20, 25],
                "npk_ratio": "120:60:40",
            },
            "Sugarcane": {
                "scientific_name": "Saccharum officinarum",
                "seasons": ["Year-round"],
                "planting_windows": {
                    "Main": {"start": "10-01", "end": "03-31"},
                },
                "duration_days": 360,
                "water_requirement_mm": 1500,
                "suitable_soil": ["Loamy", "Clay-Loam"],
                "optimal_ph": [6.5, 7.5],
                "optimal_temp_c": [25, 32],
                "npk_ratio": "250:80:120",
            },
            "Cotton": {
                "scientific_name": "Gossypium hirsutum",
                "seasons": ["Kharif"],
                "planting_windows": {
                    "Kharif": {"start": "06-01", "end": "07-15"},
                },
                "duration_days": 180,
                "water_requirement_mm": 700,
                "suitable_soil": ["Black", "Clay-Loam"],
                "optimal_ph": [6.5, 8.0],
                "optimal_temp_c": [21, 35],
                "npk_ratio": "150:60:60",
            },
            "Tomato": {
                "scientific_name": "Solanum lycopersicum",
                "seasons": ["Rabi", "Summer"],
                "planting_windows": {
                    "Rabi": {"start": "10-15", "end": "11-30"},
                    "Summer": {"start": "01-15", "end": "02-28"},
                },
                "duration_days": 90,
                "water_requirement_mm": 600,
                "suitable_soil": ["Loamy", "Sandy-Loam"],
                "optimal_ph": [6.0, 7.0],
                "optimal_temp_c": [18, 27],
                "npk_ratio": "150:75:75",
            },
            "Groundnut": {
                "scientific_name": "Arachis hypogaea",
                "seasons": ["Kharif", "Rabi", "Samba"],
                "planting_windows": {
                    "Kharif": {"start": "06-01", "end": "07-15"},
                    "Rabi": {"start": "10-15", "end": "11-30"},
                    "Samba": {"start": "08-15", "end": "09-30"},
                },
                "duration_days": 110,
                "water_requirement_mm": 500,
                "suitable_soil": ["Sandy-Loam", "Loamy"],
                "optimal_ph": [6.0, 7.0],
                "optimal_temp_c": [25, 30],
                "npk_ratio": "25:50:75",
            },
            "Maize": {
                "scientific_name": "Zea mays",
                "seasons": ["Kharif", "Rabi"],
                "planting_windows": {
                    "Kharif": {"start": "06-01", "end": "07-15"},
                    "Rabi": {"start": "10-15", "end": "11-30"},
                },
                "duration_days": 100,
                "water_requirement_mm": 550,
                "suitable_soil": ["Loamy", "Clay-Loam"],
                "optimal_ph": [5.5, 7.5],
                "optimal_temp_c": [21, 30],
                "npk_ratio": "120:60:40",
            },
        }

    def get_crop_info(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """Get complete crop information."""
        return self.crop_database.get(crop_name)

    def get_available_crops(self) -> List[str]:
        """Get list of all available crops."""
        return list(self.crop_database.keys())

    def get_planting_window(self, crop_name: str, season: str) -> Optional[Dict[str, str]]:
        """Get planting window for crop and season."""
        crop_info = self.get_crop_info(crop_name)
        if crop_info:
            return crop_info.get("planting_windows", {}).get(season)
        return None

    def is_suitable_soil(self, crop_name: str, soil_type: str) -> bool:
        """Check if soil type is suitable for crop."""
        crop_info = self.get_crop_info(crop_name)
        if crop_info:
            return soil_type in crop_info.get("suitable_soil", [])
        return False

    def get_water_requirement(self, crop_name: str) -> float:
        """Get water requirement in mm/season."""
        crop_info = self.get_crop_info(crop_name)
        if crop_info:
            return crop_info.get("water_requirement_mm", 0.0)
        return 0.0

    def get_duration_days(self, crop_name: str) -> int:
        """Get crop duration in days."""
        crop_info = self.get_crop_info(crop_name)
        if crop_info:
            return crop_info.get("duration_days", 0)
        return 0
