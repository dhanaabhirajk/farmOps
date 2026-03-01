-- Migration: Create recommendations table
-- Purpose: Store crop recommendations, irrigation schedules, harvest timing, and subsidy matches
-- User Story: User Story 2 - Crop Recommendation (Phase 4)

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create recommendations table
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('crop', 'irrigation', 'harvest', 'subsidy', 'action')),
    payload JSONB NOT NULL,
    confidence INT NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    sources JSONB NOT NULL,
    explanation TEXT NOT NULL CHECK (char_length(explanation) <= 2000),
    model_version VARCHAR(30) NOT NULL,
    tool_calls JSONB DEFAULT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'superseded')),
    human_review_required BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    
    -- Foreign key constraint
    CONSTRAINT fk_recommendations_farm
        FOREIGN KEY (farm_id)
        REFERENCES farms(id)
        ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_recommendations_farm_type_status 
    ON recommendations(farm_id, type, status, created_at DESC);

CREATE INDEX idx_recommendations_confidence 
    ON recommendations(confidence DESC);

CREATE INDEX idx_recommendations_expires_at 
    ON recommendations(expires_at) 
    WHERE expires_at IS NOT NULL AND status = 'active';

-- Add comments for documentation
COMMENT ON TABLE recommendations IS 'Stores AI-generated recommendations for farms: crop choices, irrigation schedules, harvest timing, and subsidy matches';
COMMENT ON COLUMN recommendations.type IS 'Recommendation type: crop (planting), irrigation (watering), harvest (timing), subsidy (eligibility), action (general)';
COMMENT ON COLUMN recommendations.payload IS 'Structured recommendation data (JSON varies by type)';
COMMENT ON COLUMN recommendations.confidence IS 'Overall confidence score 0-100 based on data quality and model certainty';
COMMENT ON COLUMN recommendations.sources IS 'Array of data sources used: [{source_name, data_age_hours, confidence_contribution_pct}]';
COMMENT ON COLUMN recommendations.explanation IS 'Human-readable recommendation in farmer''s language (Tamil/Hindi/English)';
COMMENT ON COLUMN recommendations.tool_calls IS 'LLM tool execution log: [{tool_name, inputs, outputs, execution_time_ms}]';
COMMENT ON COLUMN recommendations.status IS 'Lifecycle: active (current), archived (old), superseded (replaced by newer)';
COMMENT ON COLUMN recommendations.human_review_required IS 'True if confidence < threshold or conflicting data detected';
COMMENT ON COLUMN recommendations.expires_at IS 'When recommendation becomes stale (NULL = valid indefinitely)';

-- Enable Row-Level Security (RLS)
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only read their own farm recommendations
CREATE POLICY recommendations_user_read_policy ON recommendations
    FOR SELECT
    USING (
        farm_id IN (
            SELECT id FROM farms WHERE user_id = auth.uid()
        )
    );

-- RLS Policy: Backend service can insert recommendations
CREATE POLICY recommendations_service_insert_policy ON recommendations
    FOR INSERT
    WITH CHECK (true);

-- RLS Policy: Backend service can update recommendations
CREATE POLICY recommendations_service_update_policy ON recommendations
    FOR UPDATE
    USING (true);
