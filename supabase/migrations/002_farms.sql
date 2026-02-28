-- Migration 002: Farms table with PostGIS geometry support
-- Stores farm polygons and metadata

CREATE TABLE IF NOT EXISTS public.farms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (char_length(name) BETWEEN 1 AND 255),
    polygon_geojson JSONB NOT NULL,
    area_acres DECIMAL(10, 2) NOT NULL CHECK (area_acres > 0 AND area_acres < 10000),
    soil_profile_id UUID, -- FK added after soil_profiles table created
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add generated columns for PostGIS operations
ALTER TABLE public.farms
    ADD COLUMN polygon_geom GEOMETRY(POLYGON, 4326) 
    GENERATED ALWAYS AS (ST_GeomFromGeoJSON(polygon_geojson::text)) STORED;

ALTER TABLE public.farms
    ADD COLUMN centroid GEOGRAPHY(POINT, 4326)
    GENERATED ALWAYS AS (ST_Centroid(ST_GeomFromGeoJSON(polygon_geojson::text))::geography) STORED;

ALTER TABLE public.farms
    ADD COLUMN polygon_validity BOOLEAN
    GENERATED ALWAYS AS (ST_IsValid(ST_GeomFromGeoJSON(polygon_geojson::text))) STORED;

-- Add constraint to ensure valid polygons
ALTER TABLE public.farms
    ADD CONSTRAINT check_valid_polygon
    CHECK (polygon_validity = true);

-- Create spatial index for polygon queries
CREATE INDEX idx_farms_polygon_geom ON public.farms USING GIST(polygon_geom);
CREATE INDEX idx_farms_centroid ON public.farms USING GIST(centroid);

-- Create indexes for common queries
CREATE INDEX idx_farms_user_id ON public.farms(user_id);
CREATE INDEX idx_farms_created_at ON public.farms(created_at DESC);

-- Add comments
COMMENT ON TABLE public.farms IS 'Agricultural plots identified by polygon boundaries';
COMMENT ON COLUMN public.farms.polygon_geojson IS 'Farm boundary as GeoJSON Polygon or MultiPolygon';
COMMENT ON COLUMN public.farms.polygon_geom IS 'PostGIS geometry for spatial queries (auto-generated)';
COMMENT ON COLUMN public.farms.centroid IS 'Farm center point for location lookups (auto-generated)';
COMMENT ON COLUMN public.farms.area_acres IS 'Farm area in acres (computed from polygon or user-provided)';

-- Row-Level Security
ALTER TABLE public.farms ENABLE ROW LEVEL SECURITY;

-- Users can only see their own farms
CREATE POLICY "Users can view own farms"
    ON public.farms
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can create their own farms
CREATE POLICY "Users can insert own farms"
    ON public.farms
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own farms
CREATE POLICY "Users can update own farms"
    ON public.farms
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own farms
CREATE POLICY "Users can delete own farms"
    ON public.farms
    FOR DELETE
    USING (auth.uid() = user_id);

-- Trigger to auto-update updated_at
CREATE TRIGGER update_farms_updated_at
    BEFORE UPDATE ON public.farms
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to validate polygon area matches computed area (within 5% tolerance)
CREATE OR REPLACE FUNCTION validate_farm_area()
RETURNS TRIGGER AS $$
DECLARE
    computed_area_acres DECIMAL(10, 2);
BEGIN
    -- Compute area from geometry in acres (1 acre ≈ 4046.86 m²)
    computed_area_acres := ST_Area(NEW.polygon_geom::geography) / 4046.86;
    
    -- Check if user-provided area is within 5% of computed area
    IF ABS(NEW.area_acres - computed_area_acres) > (computed_area_acres * 0.05) THEN
        RAISE WARNING 'Farm area (% acres) differs from computed area (% acres) by more than 5%%',
            NEW.area_acres, computed_area_acres;
        -- Allow override but log warning
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to validate area on insert/update
CREATE TRIGGER validate_farm_area_trigger
    BEFORE INSERT OR UPDATE ON public.farms
    FOR EACH ROW
    EXECUTE FUNCTION validate_farm_area();
