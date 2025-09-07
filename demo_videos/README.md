# Demo Videos for SportsCam

This directory contains sample videos and instructions for setting up demo content.

## 📹 Sample Videos Needed

To fully demonstrate SportsCam, you'll need these types of videos:

### 1. Full Game Recording (demo_game_1.mp4)
- **Duration**: 5-10 minutes
- **Content**: Complete football match footage
- **Resolution**: 1920x1080 (HD)
- **Format**: MP4, H.264 codec

### 2. Training Session (demo_game_2.mp4)
- **Duration**: 3-5 minutes
- **Content**: Football training/practice session
- **Resolution**: 1920x1080 (HD)
- **Format**: MP4, H.264 codec

### 3. Tournament Match (demo_game_3.mp4)
- **Duration**: 8-12 minutes
- **Content**: Competitive match with multiple goals/saves
- **Resolution**: 1920x1080 (HD)
- **Format**: MP4, H.264 codec

## 🎬 Sample Highlights

### Goal Highlights (15-30 seconds each)
- `goal_1.mp4` - Long-range spectacular goal
- `goal_2.mp4` - Team play leading to goal
- `goal_3.mp4` - Individual skill goal

### Save Highlights (10-20 seconds each)
- `save_1.mp4` - Diving goalkeeper save
- `save_2.mp4` - Reflex save from close range
- `save_3.mp4` - Penalty save

### Skill Highlights (10-25 seconds each)
- `skill_1.mp4` - Dribbling sequence
- `skill_2.mp4` - Nutmeg/skill move
- `skill_3.mp4` - Free kick technique

## 📸 Thumbnails

Each video should have a corresponding thumbnail:
- Format: JPG, 1280x720
- Naming: `[video_name]_thumb.jpg`
- Example: `goal_1_thumb.jpg`

## 🚀 Upload to Supabase

### Step 1: Create Storage Buckets
In Supabase Dashboard > Storage:

1. Create bucket: `videos` (public)
2. Create bucket: `highlights` (public)  
3. Create bucket: `thumbnails` (public)

### Step 2: Upload Files

#### Option A: Supabase Dashboard
1. Go to Storage > videos
2. Upload your demo videos
3. Repeat for highlights and thumbnails buckets

#### Option B: Using CLI (if you have supabase CLI)
```bash
# Upload videos
supabase storage cp demo_videos/demo_game_1.mp4 supabase://videos/demo_game_1.mp4
supabase storage cp demo_videos/demo_game_2.mp4 supabase://videos/demo_game_2.mp4
supabase storage cp demo_videos/demo_game_3.mp4 supabase://videos/demo_game_3.mp4

# Upload highlights
supabase storage cp demo_videos/goal_1.mp4 supabase://highlights/goal_1.mp4
supabase storage cp demo_videos/save_1.mp4 supabase://highlights/save_1.mp4
supabase storage cp demo_videos/skill_1.mp4 supabase://highlights/skill_1.mp4

# Upload thumbnails
supabase storage cp demo_videos/goal_1_thumb.jpg supabase://thumbnails/goal_1_thumb.jpg
supabase storage cp demo_videos/save_1_thumb.jpg supabase://thumbnails/save_1_thumb.jpg
supabase storage cp demo_videos/skill_1_thumb.jpg supabase://thumbnails/skill_1_thumb.jpg
```

## 🎯 Where to Get Demo Videos

### Free Sources:
1. **Pexels**: https://www.pexels.com/search/videos/football/
2. **Pixabay**: https://pixabay.com/videos/search/football/
3. **Unsplash**: https://unsplash.com/s/videos/football
4. **YouTube Creative Commons**: Search for CC licensed football videos

### Record Your Own:
1. Use your existing AI camera system
2. Record a short football session
3. Process with your current `gui.py` to test

## 🔧 Processing Demo Videos

Use your existing system to process demo videos:

```bash
# Process a demo video to create highlights
python football_tracker.py --record demo_output.mp4 --offline

# Use GUI to process
python gui.py
# Load demo video and process
```

## 📝 Update Sample Data

After uploading videos, update the URLs in `supabase/sample_data.sql`:

```sql
-- Update with your actual Supabase URLs
UPDATE public.highlights SET 
    video_url = 'https://iifhyrcwuvymcrlmqsfr.supabase.co/storage/v1/object/public/highlights/goal_1.mp4',
    thumbnail_url = 'https://iifhyrcwuvymcrlmqsfr.supabase.co/storage/v1/object/public/thumbnails/goal_1_thumb.jpg'
WHERE id = '770e8400-e29b-41d4-a716-446655440001';
```

## ✅ Verification

Test your demo setup:

1. **Frontend**: Check if videos load in your web interface
2. **Mobile**: Verify videos play in mobile PWA
3. **API**: Test video URLs return valid responses
4. **Thumbnails**: Ensure thumbnails display correctly

Your demo is ready when users can:
- Browse sample highlights
- Watch videos smoothly
- See realistic football content
- Experience the full SportsCam workflow