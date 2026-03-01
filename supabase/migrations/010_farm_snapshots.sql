-- Migration 010: Create farm_snapshots table (cached)
-- Purpose: Cached "Farm Snapshot" to serve <300ms responses

CREATE TABLE IF NOT EXISTS farm_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  snapshot_date DATE NOT NULL,
  payload JSONB NOT NULL,
  confidence_overall INT NOT NULL,
  sources_used JSONB NOT NULL,
  cache_ttl_minutes INT NOT NULL DEFAULT 240,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  
  -- Composite unique key
  CONSTRAINT farm_snapshots_unique_farm_date UNIQUE (farm_id, snapshot_date),
  
  -- Constraints
  CONSTRAINT farm_snapshots_check_confidence CHECK (confidence_overall >= 0 AND confidence_overall <= 100)
);

-- Create indexes
CREATE INDEX idx_farm_snapshots_farm_id_date ON farm_snapshots (farm_id, snapshot_date DESC);
CREATE INDEX idx_farm_snapshots_created_at ON farm_snapshots (created_at DESC);

-- Add RLS policies
ALTER TABLE farm_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "farm_snapshots_owner_access" ON farm_snapshots
  FOR ALL
  USING (EXISTS (
    SELECT 1 FROM farms WHERE farms.id = farm_snapshots.farm_id AND farms.user_id = auth.uid()
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM farms WHERE farms.id = farm_snapshots.farm_id AND farms.user_id = auth.uid()
  ));
