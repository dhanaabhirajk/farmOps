-- Migration 003: Data Audit Logs table
-- Tracks all external API calls and AI tool executions for provenance

CREATE TABLE IF NOT EXISTS public.data_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    farm_id UUID REFERENCES public.farms(id) ON DELETE SET NULL,
    source TEXT NOT NULL, -- e.g., 'get_market_price', 'estimate_yield', 'gee_ndvi', 'imd_weather'
    source_type TEXT NOT NULL CHECK (source_type IN ('llm_tool', 'external_api', 'computation')),
    request_payload JSONB, -- Input parameters
    response_summary JSONB, -- Key outputs (not full response to save space)
    execution_time_ms INTEGER CHECK (execution_time_ms >= 0),
    cost_estimate_usd DECIMAL(10, 6) CHECK (cost_estimate_usd >= 0), -- API call cost
    status TEXT NOT NULL CHECK (status IN ('success', 'error', 'timeout', 'rate_limited')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX idx_audit_logs_user_id ON public.data_audit_logs(user_id);
CREATE INDEX idx_audit_logs_farm_id ON public.data_audit_logs(farm_id);
CREATE INDEX idx_audit_logs_source ON public.data_audit_logs(source);
CREATE INDEX idx_audit_logs_source_type ON public.data_audit_logs(source_type);
CREATE INDEX idx_audit_logs_created_at ON public.data_audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_status ON public.data_audit_logs(status);

-- Create composite index for common query pattern
CREATE INDEX idx_audit_logs_farm_source_date 
    ON public.data_audit_logs(farm_id, source, created_at DESC);

-- Add comments
COMMENT ON TABLE public.data_audit_logs IS 'Complete audit trail of external data fetches and AI tool calls';
COMMENT ON COLUMN public.data_audit_logs.source IS 'Tool name or API endpoint (e.g., get_ndvi_timeseries, agmarknet_prices)';
COMMENT ON COLUMN public.data_audit_logs.source_type IS 'Category: llm_tool (AI tool call), external_api (GEE/IMD/AGMARKNET), computation (yield calc)';
COMMENT ON COLUMN public.data_audit_logs.request_payload IS 'Input parameters for reproducibility';
COMMENT ON COLUMN public.data_audit_logs.response_summary IS 'Key outputs (summary to avoid storing large responses)';
COMMENT ON COLUMN public.data_audit_logs.execution_time_ms IS 'Latency for performance monitoring';
COMMENT ON COLUMN public.data_audit_logs.cost_estimate_usd IS 'Estimated API call cost for budget tracking';

-- Row-Level Security
ALTER TABLE public.data_audit_logs ENABLE ROW LEVEL SECURITY;

-- Users can view logs for their own actions
CREATE POLICY "Users can view own audit logs"
    ON public.data_audit_logs
    FOR SELECT
    USING (auth.uid() = user_id);

-- Only backend service can insert logs (using service role key)
CREATE POLICY "Service can insert audit logs"
    ON public.data_audit_logs
    FOR INSERT
    WITH CHECK (true); -- Service role bypasses RLS, but policy needed

-- Create view for cost analytics
CREATE OR REPLACE VIEW public.audit_costs_summary AS
SELECT
    user_id,
    source_type,
    source,
    DATE_TRUNC('day', created_at) AS date,
    COUNT(*) AS call_count,
    SUM(cost_estimate_usd) AS total_cost_usd,
    AVG(execution_time_ms) AS avg_latency_ms,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_count
FROM public.data_audit_logs
GROUP BY user_id, source_type, source, DATE_TRUNC('day', created_at);

COMMENT ON VIEW public.audit_costs_summary IS 'Daily aggregated API call costs and performance metrics';

-- Function to clean up old audit logs (retention policy: 90 days for raw, keep aggregates)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.data_audit_logs
    WHERE created_at < NOW() - INTERVAL '90 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_audit_logs IS 'Deletes audit logs older than 90 days (call from scheduled job)';
