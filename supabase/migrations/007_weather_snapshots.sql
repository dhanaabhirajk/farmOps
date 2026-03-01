-- Migration 007: Create weather_snapshots table
-- Purpose: Time-series weather observations and forecasts

CREATE TABLE IF NOT EXISTS weather_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  snapshot_date DATE NOT NULL,
  observations JSONB NOT NULL,
  forecast JSONB NOT NULL,
  data_sources JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create indexes
CREATE INDEX idx_weather_snapshots_farm_id_date ON weather_snapshots (farm_id, snapshot_date DESC);
CREATE INDEX idx_weather_snapshots_created_at ON weather_snapshots (created_at DESC);

-- Create trigger for updated_at
CREATE TRIGGER trigger_weather_snapshots_updated_at
  BEFORE UPDATE ON weather_snapshots
  FOR EACH ROW
  EXECUTE FUNCTION update_timestamp();

-- Add RLS policies
ALTER TABLE weather_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "weather_snapshots_owner_access" ON weather_snapshots
  FOR ALL
  USING (EXISTS (
    SELECT 1 FROM farms WHERE farms.id = weather_snapshots.farm_id AND farms.user_id = auth.uid()
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM farms WHERE farms.id = weather_snapshots.farm_id AND farms.user_id = auth.uid()
  ));

-- Add retention policy comment (90 days)
COMMENT ON TABLE weather_snapshots IS 'Retention: 90 days of historical weather snapshots for analysis';
