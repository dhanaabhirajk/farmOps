-- Migration 009: Create market_snapshots table and markets reference table
-- Purpose: Cached mandi prices for commodities

-- Create markets reference table first
CREATE TABLE IF NOT EXISTS markets (
  id INT PRIMARY KEY,
  name TEXT NOT NULL,
  district VARCHAR(50) NOT NULL,
  location GEOGRAPHY(POINT, 4326),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create indexes for markets
CREATE INDEX idx_markets_district ON markets (district);
CREATE INDEX idx_markets_location ON markets USING GIST (location);

-- Create market_snapshots table
CREATE TABLE IF NOT EXISTS market_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  market_id INT NOT NULL REFERENCES markets(id) ON DELETE RESTRICT,
  commodity VARCHAR(50) NOT NULL,
  modal_price_per_quintal DECIMAL(8, 2) NOT NULL,
  min_price_per_quintal DECIMAL(8, 2),
  max_price_per_quintal DECIMAL(8, 2),
  trade_volume_quintals INT,
  snapshot_date DATE NOT NULL,
  data_source VARCHAR(50) NOT NULL DEFAULT 'AGMARKNET',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  
  -- Constraints
  CONSTRAINT market_snapshots_check_modal_price CHECK (modal_price_per_quintal > 0),
  CONSTRAINT market_snapshots_check_data_source CHECK (data_source IN ('AGMARKNET', 'data.gov.in', 'other'))
);

-- Create indexes for market_snapshots
CREATE INDEX idx_market_snapshots_market_commodity_date ON market_snapshots (market_id, commodity, snapshot_date DESC);
CREATE INDEX idx_market_snapshots_snapshot_date ON market_snapshots (snapshot_date DESC);

-- Add RLS policies
ALTER TABLE market_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "market_snapshots_public_read" ON market_snapshots
  FOR SELECT
  USING (true);

-- Add retention policy comment (3 years)
COMMENT ON TABLE market_snapshots IS 'Retention: Keep 3 years of historical prices for trend analysis and ML training';
