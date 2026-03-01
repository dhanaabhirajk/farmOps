-- Migration 006: Create soil_profiles table
-- Purpose: Detailed soil test results linked to a farm

CREATE TABLE IF NOT EXISTS soil_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  soil_type VARCHAR(30),
  soil_texture VARCHAR(30),
  pH DECIMAL(3, 2),
  organic_carbon_pct DECIMAL(4, 2),
  nitrogen_mg_kg DECIMAL(6, 2),
  phosphorus_mg_kg DECIMAL(6, 2),
  potassium_mg_kg DECIMAL(6, 2),
  depth_cm INT,
  drainage_class VARCHAR(30),
  salinity_ec_ds_m DECIMAL(5, 2),
  test_date DATE NOT NULL,
  lab_name TEXT,
  data_source VARCHAR(50) NOT NULL DEFAULT 'user-reported',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  
  -- Constraints
  CONSTRAINT soil_profiles_check_ph CHECK (pH >= 2 AND pH <= 14),
  CONSTRAINT soil_profiles_check_organic_carbon CHECK (organic_carbon_pct >= 0 AND organic_carbon_pct <= 100),
  CONSTRAINT soil_profiles_check_depth CHECK (depth_cm > 0 AND depth_cm <= 120),
  CONSTRAINT soil_profiles_check_data_source CHECK (data_source IN ('user-reported', 'lab-test', 'survey'))
);

-- Create indexes
CREATE INDEX idx_soil_profiles_farm_id ON soil_profiles (farm_id);

-- Create trigger for updated_at
CREATE TRIGGER trigger_soil_profiles_updated_at
  BEFORE UPDATE ON soil_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_timestamp();

-- Add RLS policies
ALTER TABLE soil_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "soil_profiles_owner_access" ON soil_profiles
  FOR ALL
  USING (EXISTS (
    SELECT 1 FROM farms WHERE farms.id = soil_profiles.farm_id AND farms.user_id = auth.uid()
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM farms WHERE farms.id = soil_profiles.farm_id AND farms.user_id = auth.uid()
  ));
