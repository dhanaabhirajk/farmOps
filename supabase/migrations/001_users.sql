-- Migration 001: Users table with Row-Level Security
-- Extends Supabase Auth users with application-specific fields

-- Enable PostGIS extension for geospatial data
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users profile table (extends auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    phone TEXT UNIQUE CHECK (phone ~ '^\+[1-9]\d{1,14}$'), -- E.164 format
    name TEXT CHECK (char_length(name) BETWEEN 1 AND 255),
    language VARCHAR(5) NOT NULL DEFAULT 'ta' CHECK (language IN ('ta', 'en', 'hi')),
    location_pref GEOGRAPHY(POINT, 4326), -- Preferred map center (lat/lon)
    last_active TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_phone ON public.users(phone) WHERE phone IS NOT NULL;
CREATE INDEX idx_users_created_at ON public.users(created_at DESC);
CREATE INDEX idx_users_last_active ON public.users(last_active DESC);

-- Add comments for documentation
COMMENT ON TABLE public.users IS 'Farmer accounts with language and location preferences';
COMMENT ON COLUMN public.users.language IS 'UI language preference: ta (Tamil), en (English), hi (Hindi)';
COMMENT ON COLUMN public.users.location_pref IS 'User preferred map center for quick farm access';

-- Row-Level Security Policies
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Users can read their own record
CREATE POLICY "Users can view own profile"
    ON public.users
    FOR SELECT
    USING (auth.uid() = id);

-- Users can update their own record
CREATE POLICY "Users can update own profile"
    ON public.users
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Allow insert during signup (triggered by auth.users insert)
CREATE POLICY "Users can insert own profile"
    ON public.users
    FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to create user profile on auth.users insert
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'name', NEW.email)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on auth.users to create profile
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
