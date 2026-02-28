-- Migration 004: User Actions table (offline queue)
-- Stores user actions performed offline for later sync

CREATE TABLE IF NOT EXISTS public.user_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    farm_id UUID REFERENCES public.farms(id) ON DELETE SET NULL,
    action_type TEXT NOT NULL, -- e.g., 'mark_irrigation_done', 'update_crop_status', 'add_expense'
    action_payload JSONB NOT NULL, -- Action-specific data
    sync_status TEXT NOT NULL DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'failed')),
    sync_error TEXT,
    synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_user_actions_user_id ON public.user_actions(user_id);
CREATE INDEX idx_user_actions_farm_id ON public.user_actions(farm_id);
CREATE INDEX idx_user_actions_sync_status ON public.user_actions(sync_status);
CREATE INDEX idx_user_actions_created_at ON public.user_actions(created_at DESC);
CREATE INDEX idx_user_actions_user_pending 
    ON public.user_actions(user_id, created_at DESC) 
    WHERE sync_status = 'pending';

-- Add comments
COMMENT ON TABLE public.user_actions IS 'Offline action queue for sync when connection returns';
COMMENT ON COLUMN public.user_actions.action_type IS 'Type of action performed (e.g., mark_irrigation_done, update_crop_status)';
COMMENT ON COLUMN public.user_actions.action_payload IS 'Action-specific data (e.g., {irrigation_event_id, actual_volume_liters})';
COMMENT ON COLUMN public.user_actions.sync_status IS 'Sync state: pending (not yet synced), synced (successfully synced), failed (sync error)';

-- Row-Level Security
ALTER TABLE public.user_actions ENABLE ROW LEVEL SECURITY;

-- Users can view their own actions
CREATE POLICY "Users can view own actions"
    ON public.user_actions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can create their own actions
CREATE POLICY "Users can insert own actions"
    ON public.user_actions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own actions (for retry after failed sync)
CREATE POLICY "Users can update own actions"
    ON public.user_actions
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete synced actions (cleanup)
CREATE POLICY "Users can delete synced actions"
    ON public.user_actions
    FOR DELETE
    USING (auth.uid() = user_id AND sync_status = 'synced');

-- Trigger to auto-update updated_at
CREATE TRIGGER update_user_actions_updated_at
    BEFORE UPDATE ON public.user_actions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to mark action as synced
CREATE OR REPLACE FUNCTION mark_action_synced(action_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE public.user_actions
    SET 
        sync_status = 'synced',
        synced_at = NOW(),
        sync_error = NULL
    WHERE id = action_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to mark action as failed
CREATE OR REPLACE FUNCTION mark_action_failed(action_id UUID, error_msg TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE public.user_actions
    SET 
        sync_status = 'failed',
        sync_error = error_msg
    WHERE id = action_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to get pending actions for user
CREATE OR REPLACE FUNCTION get_pending_actions(p_user_id UUID)
RETURNS TABLE (
    id UUID,
    farm_id UUID,
    action_type TEXT,
    action_payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ua.id,
        ua.farm_id,
        ua.action_type,
        ua.action_payload,
        ua.created_at
    FROM public.user_actions ua
    WHERE ua.user_id = p_user_id
      AND ua.sync_status = 'pending'
    ORDER BY ua.created_at ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_pending_actions IS 'Get all pending actions for a user (for offline sync)';

-- Function to cleanup old synced actions (retention: 30 days)
CREATE OR REPLACE FUNCTION cleanup_synced_actions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.user_actions
    WHERE sync_status = 'synced'
      AND synced_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_synced_actions IS 'Delete synced actions older than 30 days (call from scheduled job)';
