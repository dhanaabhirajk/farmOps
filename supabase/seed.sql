-- Seed data: 3 test farms in Tamil Nadu
-- Locations: Thanjavur (rice), Coimbatore (groundnut), Madurai (tomato)

-- Seed test user (for development only)
-- Password: testpass123
INSERT INTO auth.users (
    id,
    email,
    encrypted_password,
    email_confirmed_at,
    created_at,
    updated_at
) VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,
    'test@farmops.dev',
    crypt('testpass123', gen_salt('bf')),
    NOW(),
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- User profile will be auto-created by trigger
-- Update user profile with test data
UPDATE public.users
SET
    name = 'Test Farmer',
    language = 'ta',
    phone = '+919876543210',
    location_pref = ST_SetSRID(ST_MakePoint(78.6569, 10.7905), 4326)::geography -- Tamil Nadu center
WHERE id = '00000000-0000-0000-0000-000000000001';

-- Farm 1: Thanjavur - Rice paddy field
INSERT INTO public.farms (
    id,
    user_id,
    name,
    polygon_geojson,
    area_acres
) VALUES (
    '10000000-0000-0000-0000-000000000001'::uuid,
    '00000000-0000-0000-0000-000000000001'::uuid,
    'Thanjavur Paddy Field A',
    '{
        "type": "Polygon",
        "coordinates": [[
            [79.1410, 10.7830],
            [79.1420, 10.7830],
            [79.1420, 10.7820],
            [79.1410, 10.7820],
            [79.1410, 10.7830]
        ]]
    }'::jsonb,
    2.47 -- ~1 hectare = 2.47 acres
) ON CONFLICT (id) DO NOTHING;

-- Farm 2: Coimbatore - Groundnut field
INSERT INTO public.farms (
    id,
    user_id,
    name,
    polygon_geojson,
    area_acres
) VALUES (
    '10000000-0000-0000-0000-000000000002'::uuid,
    '00000000-0000-0000-0000-000000000001'::uuid,
    'Coimbatore Groundnut Farm',
    '{
        "type": "Polygon",
        "coordinates": [[
            [76.9558, 11.0168],
            [76.9578, 11.0168],
            [76.9578, 11.0148],
            [76.9558, 11.0148],
            [76.9558, 11.0168]
        ]]
    }'::jsonb,
    4.94 -- ~2 hectares
) ON CONFLICT (id) DO NOTHING;

-- Farm 3: Madurai - Tomato cultivation
INSERT INTO public.farms (
    id,
    user_id,
    name,
    polygon_geojson,
    area_acres
) VALUES (
    '10000000-0000-0000-0000-000000000003'::uuid,
    '00000000-0000-0000-0000-000000000001'::uuid,
    'Madurai Tomato Field',
    '{
        "type": "Polygon",
        "coordinates": [[
            [78.1198, 9.9252],
            [78.1218, 9.9252],
            [78.1218, 9.9232],
            [78.1198, 9.9232],
            [78.1198, 9.9252]
        ]]
    }'::jsonb,
    3.71 -- ~1.5 hectares
) ON CONFLICT (id) DO NOTHING;

-- Add sample audit log entries for testing
INSERT INTO public.data_audit_logs (
    user_id,
    farm_id,
    source,
    source_type,
    request_payload,
    response_summary,
    execution_time_ms,
    cost_estimate_usd,
    status
) VALUES
(
    '00000000-0000-0000-0000-000000000001'::uuid,
    '10000000-0000-0000-0000-000000000001'::uuid,
    'get_ndvi_timeseries',
    'external_api',
    '{"farm_id": "10000000-0000-0000-0000-000000000001", "days": 30}'::jsonb,
    '{"mean_ndvi": 0.68, "trend": "increasing", "data_points": 6}'::jsonb,
    2340,
    0.00,
    'success'
),
(
    '00000000-0000-0000-0000-000000000001'::uuid,
    '10000000-0000-0000-0000-000000000002'::uuid,
    'get_market_prices',
    'external_api',
    '{"commodity": "groundnut", "market": "coimbatore"}'::jsonb,
    '{"modal_price": 5800, "currency": "INR", "unit": "quintal"}'::jsonb,
    850,
    0.00,
    'success'
);

-- Add sample user action (for offline queue testing)
INSERT INTO public.user_actions (
    user_id,
    farm_id,
    action_type,
    action_payload,
    sync_status
) VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,
    '10000000-0000-0000-0000-000000000001'::uuid,
    'update_crop_status',
    '{"crop": "rice", "stage": "flowering", "health": "good"}'::jsonb,
    'synced'
);

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- Refresh RLS policies
ALTER TABLE public.users FORCE ROW LEVEL SECURITY;
ALTER TABLE public.farms FORCE ROW LEVEL SECURITY;
ALTER TABLE public.data_audit_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE public.user_actions FORCE ROW LEVEL SECURITY;
