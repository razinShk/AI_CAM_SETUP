# 🚀 SportsCam Complete Deployment Guide

## Step-by-Step Deployment Process

### Phase 1: Local Development Setup ✅

You've already completed this by creating all the files locally!

### Phase 2: GitHub Repository Setup

```bash
# 1. Initialize git (if not already done)
git init

# 2. Add all files
git add .

# 3. Commit changes
git commit -m "Initial SportsCam setup with Supabase integration"

# 4. Create GitHub repository and push
git remote add origin https://github.com/your-username/sportscam.git
git branch -M main
git push -u origin main
```

### Phase 3: Supabase Setup

1. **Go to Supabase Dashboard**: https://supabase.com/dashboard/project/iifhyrcwuvymcrlmqsfr

2. **Run Database Schema**:
   - Go to SQL Editor
   - Copy content from `supabase/schema.sql`
   - Run the query

3. **Add Sample Data**:
   - Copy content from `supabase/sample_data.sql`
   - Run the query

4. **Create Storage Buckets**:
   - Go to Storage
   - Create buckets: `videos`, `highlights`, `thumbnails`
   - Make all buckets public

5. **Get Service Role Key**:
   - Go to Settings > API
   - Copy the `service_role` key (keep it secret!)

### Phase 4: Raspberry Pi Deployment

```bash
# On Raspberry Pi:

# 1. Clone your repository
git clone https://github.com/your-username/sportscam.git
cd sportscam

# 2. Run setup script
chmod +x pi_setup.sh
./pi_setup.sh

# 3. Configure environment
nano .env
# Update CAMERA_ID, TURF_ID, and add SERVICE_KEY

# 4. Test the system
source venv/bin/activate
python raspberry_pi_server.py

# 5. Start as service
sudo systemctl start sportscam-camera
sudo systemctl status sportscam-camera
```

### Phase 5: Frontend Deployment

#### Option A: Vercel (Recommended)
```bash
cd frontend
npx vercel

# Follow prompts:
# - Link to existing project: No
# - Project name: sportscam
# - Directory: ./
# - Build command: (leave empty)
# - Output directory: (leave empty)
```

#### Option B: Netlify
1. Go to netlify.com
2. Drag and drop your `frontend` folder
3. Update site name to something memorable

### Phase 6: Testing

1. **Test Camera**: 
   ```bash
   curl http://raspberry-pi-ip:5000/api/status
   ```

2. **Test Supabase**:
   ```bash
   curl -X GET 'https://iifhyrcwuvymcrlmqsfr.supabase.co/rest/v1/turf_locations' \
     -H "apikey: your-anon-key"
   ```

3. **Test Frontend**: Visit your deployed URL

4. **End-to-End Test**:
   - Register user
   - Start recording
   - Stop recording
   - Check highlights

### Phase 7: Production Optimization

1. **Security**:
   - Change default passwords
   - Set up firewall rules
   - Use HTTPS for frontend

2. **Monitoring**:
   - Set up log monitoring
   - Configure alerts
   - Monitor system resources

3. **Scaling**:
   - Add more Raspberry Pi cameras
   - Optimize video processing
   - Set up CDN for videos

## 🎯 Success Checklist

- [ ] Repository created and pushed to GitHub
- [ ] Supabase database schema deployed
- [ ] Storage buckets created and configured
- [ ] Raspberry Pi setup completed
- [ ] Camera service running and registered
- [ ] Frontend deployed and accessible
- [ ] End-to-end recording test successful
- [ ] Demo videos uploaded and accessible
- [ ] Mobile PWA working correctly
- [ ] Social features functional

## 🚨 Troubleshooting

### Common Issues:

**Camera not connecting**:
```bash
# Check camera hardware
libcamera-hello --list-cameras

# Check service logs
sudo journalctl -u sportscam-camera -f
```

**Supabase connection failed**:
```bash
# Verify environment variables
cat .env

# Test connection
python3 -c "from supabase_client import SupabaseClient; SupabaseClient()"
```

**Frontend not loading**:
- Check browser console for errors
- Verify API URLs in JavaScript
- Ensure CORS is configured in Supabase

## 📞 Support

If you encounter issues:
1. Check the logs: `sudo journalctl -u sportscam-camera`
2. Verify environment variables
3. Test individual components
4. Check network connectivity

Your SportsCam system is now ready for production! 🎉