-- SportsCam Database Schema for Supabase
-- Run this in Supabase SQL Editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    role TEXT DEFAULT 'player' CHECK (role IN ('admin', 'turf_owner', 'player')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Turf locations table
CREATE TABLE public.turf_locations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    owner_id UUID REFERENCES public.profiles(id),
    camera_ip INET,
    camera_status TEXT DEFAULT 'offline' CHECK (camera_status IN ('online', 'offline', 'error')),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Game sessions table
CREATE TABLE public.game_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    turf_id UUID REFERENCES public.turf_locations(id) NOT NULL,
    session_name TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration INTEGER, -- in minutes
    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'recording', 'completed', 'processing', 'error')),
    recording_path TEXT,
    recording_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Player sessions (many-to-many)
CREATE TABLE public.player_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    player_id UUID REFERENCES public.profiles(id) NOT NULL,
    session_id UUID REFERENCES public.game_sessions(id) NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, session_id)
);

-- Highlights table
CREATE TABLE public.highlights (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES public.game_sessions(id) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    video_path TEXT NOT NULL,
    video_url TEXT,
    thumbnail_path TEXT,
    thumbnail_url TEXT,
    start_timestamp FLOAT, -- seconds from game start
    end_timestamp FLOAT,
    duration FLOAT,
    tags TEXT[] DEFAULT '{}',
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Social posts table
CREATE TABLE public.social_posts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) NOT NULL,
    highlight_id UUID REFERENCES public.highlights(id) NOT NULL,
    caption TEXT,
    likes INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comments table
CREATE TABLE public.comments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    post_id UUID REFERENCES public.social_posts(id) NOT NULL,
    user_id UUID REFERENCES public.profiles(id) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Likes table
CREATE TABLE public.likes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) NOT NULL,
    highlight_id UUID REFERENCES public.highlights(id),
    post_id UUID REFERENCES public.social_posts(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, highlight_id),
    UNIQUE(user_id, post_id),
    CHECK ((highlight_id IS NOT NULL) OR (post_id IS NOT NULL))
);

-- Create indexes for better performance
CREATE INDEX idx_turf_locations_owner ON public.turf_locations(owner_id);
CREATE INDEX idx_game_sessions_turf ON public.game_sessions(turf_id);
CREATE INDEX idx_game_sessions_created_by ON public.game_sessions(created_by);
CREATE INDEX idx_highlights_session ON public.highlights(session_id);
CREATE INDEX idx_highlights_created_by ON public.highlights(created_by);
CREATE INDEX idx_social_posts_user ON public.social_posts(user_id);
CREATE INDEX idx_social_posts_highlight ON public.social_posts(highlight_id);

-- Row Level Security (RLS) policies
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.turf_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.game_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.player_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.highlights ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.social_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.likes ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Public profiles are viewable by everyone" ON public.profiles
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own profile" ON public.profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Turf locations policies
CREATE POLICY "Turf locations are viewable by everyone" ON public.turf_locations
    FOR SELECT USING (true);

CREATE POLICY "Turf owners can manage their turfs" ON public.turf_locations
    FOR ALL USING (auth.uid() = owner_id OR auth.uid() IN (
        SELECT id FROM public.profiles WHERE role = 'admin'
    ));

-- Game sessions policies
CREATE POLICY "Game sessions are viewable by participants" ON public.game_sessions
    FOR SELECT USING (
        auth.uid() = created_by OR 
        EXISTS (
            SELECT 1 FROM public.player_sessions 
            WHERE session_id = id AND player_id = auth.uid()
        ) OR
        auth.uid() IN (SELECT id FROM public.profiles WHERE role IN ('admin', 'turf_owner'))
    );

CREATE POLICY "Session creators can manage sessions" ON public.game_sessions
    FOR ALL USING (auth.uid() = created_by OR auth.uid() IN (
        SELECT id FROM public.profiles WHERE role = 'admin'
    ));

-- Highlights policies
CREATE POLICY "Highlights are viewable by everyone" ON public.highlights
    FOR SELECT USING (true);

CREATE POLICY "Highlight creators can manage highlights" ON public.highlights
    FOR ALL USING (auth.uid() = created_by OR auth.uid() IN (
        SELECT id FROM public.profiles WHERE role = 'admin'
    ));

-- Social posts policies
CREATE POLICY "Social posts are viewable by everyone" ON public.social_posts
    FOR SELECT USING (true);

CREATE POLICY "Users can manage their own posts" ON public.social_posts
    FOR ALL USING (auth.uid() = user_id);

-- Functions for updated_at timestamps
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER handle_updated_at BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER handle_updated_at BEFORE UPDATE ON public.turf_locations
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER handle_updated_at BEFORE UPDATE ON public.game_sessions
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER handle_updated_at BEFORE UPDATE ON public.highlights
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER handle_updated_at BEFORE UPDATE ON public.social_posts
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();