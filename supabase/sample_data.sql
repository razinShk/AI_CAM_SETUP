-- Sample data for SportsCam demo
-- Run this after the main schema

-- Note: Profiles will be created automatically when users sign up through Supabase Auth
-- For now, we'll create basic data that doesn't require user authentication

-- Insert sample turf locations (without owner for now)
INSERT INTO public.turf_locations (id, name, address, camera_status) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Premier Sports Complex', '123 Football Street, Mumbai, Maharashtra', 'online'),
('550e8400-e29b-41d4-a716-446655440002', 'Elite Football Arena', '456 Sports Avenue, Delhi, Delhi', 'offline'),
('550e8400-e29b-41d4-a716-446655440003', 'Champions Turf', '789 Victory Road, Bangalore, Karnataka', 'online');

-- Insert sample game sessions
INSERT INTO public.game_sessions (id, turf_id, session_name, start_time, end_time, duration, status, recording_url) VALUES
('660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'Evening Match - Team A vs Team B', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour', 60, 'completed', 'https://iifhyrcwuvymcrlmqsfr.supabase.co/storage/v1/object/public/videos/demo_game_1.mp4'),
('660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'Morning Training Session', NOW() - INTERVAL '4 hours', NOW() - INTERVAL '3 hours', 60, 'completed', 'https://iifhyrcwuvymcrlmqsfr.supabase.co/storage/v1/object/public/videos/demo_game_2.mp4'),
('660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440003', 'Weekend Tournament - Semi Final', NOW() - INTERVAL '6 hours', NOW() - INTERVAL '5 hours', 60, 'completed', 'https://iifhyrcwuvymcrlmqsfr.supabase.co/storage/v1/object/public/videos/demo_game_3.mp4');

-- Insert sample highlights
INSERT INTO public.highlights (id, session_id, title, description, video_path, video_url, thumbnail_path, thumbnail_url, start_timestamp, end_timestamp, duration, tags, likes, views) VALUES
('770e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 'Amazing Goal - 15m', 'Spectacular long-range goal that found the top corner', '/recordings/highlights/goal_1.mp4', 'https://iifhyrcwuvymcrlmqsfr.supabase.co/storage/v1/object/public/highlights/goal_1.mp4', '/recordings/thumbnails/goal_1_thumb.jpg', 'https://iifhyrcwuvymcrlmqsfr.supabase.co/storage/v1/object/public/thumbnails/goal_1_thumb.jpg', 900, 920, 20, ARRAY['goal', 'long_range', 'spectacular'], 45, 234),
('770e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440001', 'Great Save - 28m', 'Goalkeeper makes an incredible diving save', '/recordings/highlights/save_1.mp4', 'https://iifhyrcwuvymcrlmqsfr.supabase.co/storage/v1/object/public/highlights/save_1.mp4', '/recordings/thumbnails/save_1_thumb.jpg', 'https://iifhyrcwuvymcrlmqsfr.supabase.co/storage/v1/object/public/thumbnails/save_1_thumb.jpg', 1680, 1695, 15, ARRAY['save', 'goalkeeper', 'diving'], 32, 189),
('770e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440002', 'Skill Move - 12m', 'Player shows incredible footwork to beat defender', '/recordings/highlights/skill_1.mp4', 'https://iifhyrcwuvymcrlmqsfr.supabase.co/storage/v1/object/public/highlights/skill_1.mp4', '/recordings/thumbnails/skill_1_thumb.jpg', 'https://iifhyrcwuvymcrlmqsfr.supabase.co/storage/v1/object/public/thumbnails/skill_1_thumb.jpg', 720, 735, 15, ARRAY['skill', 'dribbling', 'footwork'], 28, 156),
('770e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440003', 'Team Goal - 22m', 'Beautiful team play leads to a well-worked goal', '/recordings/highlights/team_goal_1.mp4', 'https://iifhyrcwuvymcrlmqsfr.supabase.co/storage/v1/object/public/highlights/team_goal_1.mp4', '/recordings/thumbnails/team_goal_1_thumb.jpg', 'https://iifhyrcwuvymcrlmqsfr.supabase.co/storage/v1/object/public/thumbnails/team_goal_1_thumb.jpg', 1320, 1340, 20, ARRAY['goal', 'teamwork', 'passing'], 67, 312);

-- Social posts will be created when users sign up and start sharing highlights
-- You can add sample social posts after creating test users through Supabase Auth