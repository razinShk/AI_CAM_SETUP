# 🚀 SportsCam Deployment Guide

Complete guide for deploying the AI Football Tracking Camera System for your turf business.

## 📋 System Overview

SportsCam is a complete AI-powered football tracking system that consists of:

- **Raspberry Pi 5 + IMX500 AI Camera** (at each turf location)
- **Web Backend API** (cloud server)
- **Web Frontend** (turf management dashboard)
- **Mobile PWA** (Instagram-like player app)
- **AI Processing Pipeline** (highlight generation)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Turf Camera   │    │   Cloud Server  │    │   Mobile App    │
│  Raspberry Pi   │◄──►│   Backend API   │◄──►│   PWA/Web      │
│   + IMX500      │    │   + Database    │    │   Dashboard     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Prerequisites

### Hardware Requirements
- **Raspberry Pi 5** (4GB+ RAM recommended)
- **IMX500 AI Camera Module**
- **MicroSD Card** (64GB+ Class 10)
- **Stable Internet Connection** (WiFi/Ethernet)
- **Mounting Equipment** (tripod/pole mount)

### Software Requirements
- **Cloud Server** (VPS with 4GB+ RAM)
- **Domain Name** (for web access)
- **SSL Certificate** (Let's Encrypt recommended)
- **PostgreSQL Database**
- **Redis** (for background tasks)

## 📦 Installation Steps

### Step 1: Cloud Server Setup

#### 1.1 Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git

# Install Docker (optional but recommended)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### 1.2 Database Setup
```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE sportscam;
CREATE USER sportscam_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE sportscam TO sportscam_user;
\q
```

#### 1.3 Backend Deployment
```bash
# Clone repository
git clone https://github.com/your-repo/sportscam.git
cd sportscam

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
cp .env.example .env
nano .env
```

**Environment Variables (.env):**
```env
SECRET_KEY=your_very_secure_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
DATABASE_URL=postgresql://sportscam_user:your_secure_password@localhost/sportscam
REDIS_URL=redis://localhost:6379
MAIN_SERVER_URL=https://your-domain.com
UPLOAD_FOLDER=/var/www/sportscam/uploads
```

#### 1.4 Initialize Database
```bash
# Run database migrations
python backend/app.py db init
python backend/app.py db migrate
python backend/app.py db upgrade
```

#### 1.5 Setup Systemd Services

**Backend Service (/etc/systemd/system/sportscam-backend.service):**
```ini
[Unit]
Description=SportsCam Backend API
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/sportscam
Environment=PATH=/var/www/sportscam/venv/bin
ExecStart=/var/www/sportscam/venv/bin/gunicorn --workers 4 --bind unix:sportscam.sock -m 007 backend.app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

**Celery Worker Service (/etc/systemd/system/sportscam-celery.service):**
```ini
[Unit]
Description=SportsCam Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/sportscam
Environment=PATH=/var/www/sportscam/venv/bin
ExecStart=/var/www/sportscam/venv/bin/celery -A backend.app.celery worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 1.6 Nginx Configuration

**/etc/nginx/sites-available/sportscam:**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Frontend
    location / {
        root /var/www/sportscam/frontend;
        try_files $uri $uri/ /index.html;
    }

    # Mobile PWA
    location /mobile {
        root /var/www/sportscam/frontend;
        try_files /mobile.html =404;
    }

    # API
    location /api {
        include proxy_params;
        proxy_pass http://unix:/var/www/sportscam/sportscam.sock;
    }

    # Static files
    location /static {
        alias /var/www/sportscam/uploads;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Video files with range support
    location ~* \.(mp4|webm|mov)$ {
        alias /var/www/sportscam/uploads;
        add_header Accept-Ranges bytes;
        expires 7d;
    }
}
```

#### 1.7 SSL Certificate
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

#### 1.8 Start Services
```bash
# Enable and start services
sudo systemctl enable sportscam-backend sportscam-celery nginx postgresql redis
sudo systemctl start sportscam-backend sportscam-celery nginx postgresql redis

# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/sportscam /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 2: Raspberry Pi Setup

#### 2.1 Raspberry Pi OS Installation
1. Download **Raspberry Pi Imager**
2. Flash **Raspberry Pi OS (64-bit)** to SD card
3. Enable SSH and camera in advanced options
4. Boot and complete initial setup

#### 2.2 Camera Installation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install IMX500 support
sudo apt install imx500-models

# Enable camera interface
sudo raspi-config
# Interface Options > Camera > Enable

# Reboot
sudo reboot
```

#### 2.3 SportsCam Camera Software
```bash
# Clone repository
git clone https://github.com/your-repo/sportscam.git
cd sportscam

# Install dependencies
pip install -r requirements-raspberry-pi.txt

# Set environment variables
export MAIN_SERVER_URL=https://your-domain.com
export CAMERA_ID=turf_1_camera_1

# Test camera
python test_raspberry_pi.py
```

#### 2.4 Camera Server Service

**/etc/systemd/system/sportscam-camera.service:**
```ini
[Unit]
Description=SportsCam Camera Server
After=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/sportscam
Environment=MAIN_SERVER_URL=https://your-domain.com
Environment=CAMERA_ID=turf_1_camera_1
ExecStart=/usr/bin/python3 raspberry_pi_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start camera service
sudo systemctl enable sportscam-camera
sudo systemctl start sportscam-camera

# Check status
sudo systemctl status sportscam-camera
```

### Step 3: Frontend Deployment

#### 3.1 Copy Frontend Files
```bash
# Copy frontend files to web directory
sudo cp -r frontend/* /var/www/sportscam/frontend/
sudo chown -R www-data:www-data /var/www/sportscam/
```

#### 3.2 Configure API Endpoints
Edit `/var/www/sportscam/frontend/js/app.js` and `/var/www/sportscam/frontend/js/mobile-app.js`:

```javascript
// Update API URL
this.apiUrl = 'https://your-domain.com/api';
```

### Step 4: Testing and Verification

#### 4.1 System Health Checks
```bash
# Check backend API
curl https://your-domain.com/api/health

# Check camera connectivity
curl http://raspberry-pi-ip:5000/health

# Check database connection
sudo -u postgres psql -d sportscam -c "SELECT version();"

# Check Redis
redis-cli ping
```

#### 4.2 End-to-End Testing
1. **Web Dashboard**: Visit `https://your-domain.com`
2. **Mobile App**: Visit `https://your-domain.com/mobile.html`
3. **Camera Control**: Start/stop recording from dashboard
4. **Video Processing**: Verify highlights are generated
5. **Social Features**: Test sharing and viewing highlights

## 🔧 Configuration

### Camera Positioning
- **Height**: 3-5 meters above field
- **Angle**: Cover full field of play
- **Stability**: Secure mounting to prevent shake
- **Power**: Reliable power source with backup

### Network Requirements
- **Bandwidth**: 10+ Mbps upload per camera
- **Latency**: <100ms to server
- **Reliability**: Stable connection during games

### Storage Planning
- **Video Storage**: ~2GB per hour of recording
- **Highlights**: ~100MB per game session
- **Database**: Minimal storage requirements
- **Backup**: Regular automated backups

## 📊 Monitoring and Maintenance

### System Monitoring
```bash
# Monitor services
sudo systemctl status sportscam-backend sportscam-celery sportscam-camera

# Check logs
sudo journalctl -u sportscam-backend -f
sudo journalctl -u sportscam-camera -f

# Monitor resources
htop
df -h
```

### Performance Optimization
- **Database**: Regular VACUUM and ANALYZE
- **Video Files**: Implement cleanup policies
- **Cache**: Monitor Redis memory usage
- **CDN**: Consider CDN for video delivery

### Backup Strategy
```bash
# Database backup
pg_dump sportscam > backup_$(date +%Y%m%d).sql

# Video files backup
rsync -av /var/www/sportscam/uploads/ backup_server:/backups/sportscam/

# Configuration backup
tar -czf config_backup.tar.gz /etc/nginx/sites-available/sportscam /etc/systemd/system/sportscam-*
```

## 🔒 Security

### Server Security
- **Firewall**: Configure UFW/iptables
- **SSH**: Key-based authentication only
- **Updates**: Automatic security updates
- **SSL**: Strong cipher suites

### Application Security
- **JWT**: Secure token management
- **CORS**: Proper origin restrictions
- **Rate Limiting**: API rate limits
- **Input Validation**: Sanitize all inputs

### Camera Security
- **Network**: Isolated VLAN for cameras
- **Authentication**: Strong passwords
- **Updates**: Regular firmware updates
- **Access Control**: Restrict camera access

## 📱 Mobile App Installation

### PWA Installation
1. Visit `https://your-domain.com/mobile.html`
2. Tap "Add to Home Screen" (iOS) or "Install" (Android)
3. App will install as native-like experience

### App Store Distribution (Optional)
- **iOS**: Use Capacitor to create iOS app
- **Android**: Use Capacitor to create Android app
- **Submission**: Follow app store guidelines

## 🎯 Business Setup

### Turf Owner Onboarding
1. **Registration**: Create turf owner account
2. **Camera Installation**: Schedule installation
3. **Training**: Provide system training
4. **Testing**: Conduct test recordings
5. **Go Live**: Begin regular operations

### Player Onboarding
1. **App Download**: Install mobile PWA
2. **Account Creation**: Register player account
3. **Session Joining**: Join game sessions
4. **Highlight Viewing**: Access personal highlights
5. **Social Sharing**: Share to social media

### Pricing Strategy
- **Setup Fee**: One-time installation cost
- **Monthly Subscription**: Per-camera monthly fee
- **Usage-Based**: Per-hour recording charges
- **Premium Features**: Advanced analytics, longer storage

## 🚨 Troubleshooting

### Common Issues

#### Camera Not Connecting
```bash
# Check camera hardware
libcamera-hello --list-cameras

# Check network connectivity
ping your-domain.com

# Restart camera service
sudo systemctl restart sportscam-camera
```

#### Video Processing Fails
```bash
# Check Celery worker
sudo systemctl status sportscam-celery

# Check disk space
df -h

# Check FFmpeg installation
ffmpeg -version
```

#### Web App Not Loading
```bash
# Check Nginx status
sudo systemctl status nginx

# Check backend API
curl localhost:8000/api/health

# Check SSL certificate
sudo certbot certificates
```

### Performance Issues
- **High CPU**: Scale horizontally with more workers
- **High Memory**: Optimize video processing settings
- **Slow Database**: Add indexes, optimize queries
- **Network Issues**: Check bandwidth and latency

## 📞 Support

### Documentation
- **API Documentation**: `/api/docs`
- **User Manual**: Available in dashboard
- **Video Tutorials**: Link to training videos

### Support Channels
- **Email**: support@sportscam.com
- **Phone**: +1-XXX-XXX-XXXX
- **Chat**: Live chat in dashboard
- **Community**: Discord/Slack community

### Maintenance Windows
- **Scheduled**: Weekly maintenance windows
- **Emergency**: 24/7 emergency support
- **Updates**: Automatic updates with rollback

## 🎉 Success Metrics

### Key Performance Indicators
- **Camera Uptime**: >99% availability
- **Video Quality**: HD recording with <5% loss
- **Processing Time**: Highlights ready within 10 minutes
- **User Engagement**: Daily active users
- **Revenue**: Monthly recurring revenue growth

### Analytics Dashboard
- **Real-time Monitoring**: System health dashboard
- **Usage Analytics**: Recording hours, user activity
- **Business Metrics**: Revenue, customer satisfaction
- **Performance Metrics**: Response times, error rates

---

## 🎯 Next Steps

1. **Complete Installation**: Follow all steps above
2. **Test Thoroughly**: Verify all functionality
3. **Train Users**: Provide comprehensive training
4. **Monitor Performance**: Set up monitoring and alerts
5. **Scale Gradually**: Add more turfs and cameras
6. **Gather Feedback**: Continuously improve based on user feedback

Your SportsCam system is now ready to revolutionize football training and entertainment! 🚀⚽
