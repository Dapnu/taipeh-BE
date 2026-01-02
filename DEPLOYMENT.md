# 🚀 Deployment Guide - Coolify (Digital Ocean)

## Prerequisites
- Digital Ocean VPS with Coolify installed
- SSH access to VPS
- GitHub repository (without large files)

## 📋 Deployment Steps

### 1. Upload Large Files to VPS

Since `taipei.graphml` (~70MB) is too large for GitHub, upload it directly to VPS:

```bash
# From your local machine
scp data/taipei.graphml root@YOUR_VPS_IP:/opt/data/taipei.graphml
```

Or use SFTP/rsync:
```bash
rsync -avz --progress data/taipei.graphml root@YOUR_VPS_IP:/opt/data/
```

### 2. Push Code to GitHub

```bash
# Commit all changes
git add .
git commit -m "Add Docker configuration for Coolify deployment"
git push origin main
```

### 3. Configure Coolify

#### A. Create New Project in Coolify
1. Go to Coolify dashboard
2. Click "New Project"
3. Select "Docker Compose"
4. Connect your GitHub repository

#### B. Set Environment Variables
Add these in Coolify environment settings:
```env
APP_NAME=TaipeiSim Traffic API
APP_VERSION=1.0.0
DEBUG=False
ENVIRONMENT=production
API_V1_PREFIX=/api/v1
ALLOWED_ORIGINS=https://your-domain.com
```

#### C. Add Volume Mapping
In Coolify project settings, add volume:
```
Host Path: /opt/data/taipei.graphml
Container Path: /app/data/taipei.graphml
Mode: Read Only
```

#### D. Configure Ports
- Backend: 8000
- Frontend: 3000 (or 80)

### 4. Deploy

Click "Deploy" in Coolify dashboard. It will:
1. Clone your repo
2. Build Docker images
3. Start containers
4. Map volumes
5. Expose ports

### 5. Verify Deployment

```bash
# Check backend health
curl https://your-domain.com/api/v1/health

# Check frontend
curl https://your-domain.com
```

## 🔧 Alternative: Use Object Storage

If you prefer not to upload manually:

### Option A: DigitalOcean Spaces
```python
# In your app startup, download from Spaces
import boto3

s3 = boto3.client('s3',
    endpoint_url='https://nyc3.digitaloceanspaces.com',
    aws_access_key_id='YOUR_KEY',
    aws_secret_access_key='YOUR_SECRET'
)

s3.download_file('your-bucket', 'taipei.graphml', '/app/data/taipei.graphml')
```

### Option B: Direct Download URL
```dockerfile
# In Dockerfile
RUN wget https://your-storage-url/taipei.graphml -O /app/data/taipei.graphml
```

## 📊 File Size Management

Current file sizes:
- `taipei.graphml`: ~70MB (excluded from Git, mounted as volume)
- `predictions_*.csv`: ~2-5MB each (included in Git)
- `taipeh_detectors.csv`: ~50KB (included in Git)

## 🐳 Docker Commands

Test locally:
```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Logs
docker-compose logs -f

# Stop
docker-compose down
```

## 🔐 Security Notes

1. **Never commit** `.env` with production credentials
2. Use Coolify's **Secret Management** for sensitive data
3. Enable **HTTPS** via Coolify's built-in Let's Encrypt
4. Set proper **CORS** origins in production

## 📝 Troubleshooting

### Issue: Container can't find graphml file
**Solution**: Check volume mapping in Coolify:
```bash
docker exec -it <container-id> ls -lh /app/data/
```

### Issue: Out of memory during build
**Solution**: Add to docker-compose.yml:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
```

### Issue: Frontend can't connect to backend
**Solution**: Update nginx.conf proxy_pass or set proper VITE_API_URL

## 🎯 Monitoring

Add to Coolify monitoring:
- Health check endpoints: `/api/v1/health`
- Resource limits: CPU 1 core, RAM 2GB
- Auto-restart: enabled

## 📞 Support

For issues, check:
1. Coolify logs
2. Docker container logs: `docker logs <container-id>`
3. Application logs inside container

---

✅ **Deployment Complete!**
Your app should be live at: https://your-domain.com
