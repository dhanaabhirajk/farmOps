-- Migration 008: Create veg_timeseries table (NDVI/EVI)
-- Purpose: Satellite vegetation index time-series for farm

CREATE TABLE IF NOT EXISTS veg_timeseries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  measurement_date DATE NOT NULL,
  ndvi_value DECIMAL(5, 3),
  evi_value DECIMAL(5, 3),
  cloud_cover_pct DECIMAL(5, 2),
  data_source VARCHAR(50) NOT NULL DEFAULT 'GEE',
  satellite VARCHAR(50),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  
  -- Constraints
  CONSTRAINT veg_timeseries_check_ndvi CHECK (ndvi_value IS NULL OR (ndvi_value >= -1 AND ndvi_value <= 1)),
  CONSTRAINT veg_timeseries_check_evi CHECK (evi_value IS NULL OR (evi_value >= -1 AND evi_value <= 1)),
  CONSTRAINT veg_timeseries_check_cloud_cover CHECK (cloud_cover_pct IS NULL OR (cloud_cover_pct >= 0 AND cloud_cover_pct <= 100)),
  CONSTRAINT veg_timeseries_check_data_source CHECK (data_source IN ('GEE', 'Sentinel Hub', 'Planet'))
);

-- Create indexes
CREATE INDEX idx_veg_timeseries_farm_id_date ON veg_timeseries (farm_id, measurement_date DESC);
CREATE INDEX idx_veg_timeseries_cloud_cover ON veg_timeseries (cloud_cover_pct);

-- Add RLS policies
ALTER TABLE veg_timeseries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "veg_timeseries_owner_access" ON veg_timeseries
  FOR ALL
  USING (EXISTS (
    SELECT 1 FROM farms WHERE farms.id = veg_timeseries.farm_id AND farms.user_id = auth.uid()
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM farms WHERE farms.id = veg_timeseries.farm_id AND farms.user_id = auth.uid()
  ));
