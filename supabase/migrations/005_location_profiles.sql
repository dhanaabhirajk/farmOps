-- Migration 005: Create location_profiles table
-- Purpose: Static aggregated data for geospatial tiles (climate, soil, elevation, watershed)

CREATE TABLE IF NOT EXISTS location_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tile_id TEXT NOT NULL UNIQUE,
  location GEOGRAPHY(POINT, 4326) NOT NULL,
  climate_zone VARCHAR(50),
  temperature_c_annual_avg DECIMAL(5, 2),
  temperature_c_annual_min DECIMAL(5, 2),
  temperature_c_annual_max DECIMAL(5, 2),
  rainfall_mm_annual DECIMAL(8, 1),
  rainfall_mm_sw_monsoon DECIMAL(7, 1),
  rainfall_mm_ne_monsoon DECIMAL(7, 1),
  soil_type VARCHAR(30),
  soil_texture VARCHAR(30),
  elevation_m DECIMAL(8, 1),
  watershed_id UUID,
  groundwater_depth_m DECIMAL(6, 2),
  groundwater_salinity_ec DECIMAL(6, 2),
  data_sources JSONB,
  last_refreshed TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create indexes
CREATE INDEX idx_location_profiles_tile_id ON location_profiles (tile_id);
CREATE INDEX idx_location_profiles_location ON location_profiles USING GIST (location);

-- Create trigger for updated_at
CREATE TRIGGER trigger_location_profiles_updated_at
  BEFORE UPDATE ON location_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_timestamp();

-- Add RLS policies
ALTER TABLE location_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "location_profiles_public_read" ON location_profiles
  FOR SELECT
  USING (true);
