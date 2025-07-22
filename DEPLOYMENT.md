# AI Video Tool - Cloud Deployment Guide

This guide covers deploying the FastAPI-based AI Video Tool web application to various cloud platforms.

## 🏗️ Architecture Overview

The application consists of:
- **FastAPI** backend with REST API and WebSocket support
- **PostgreSQL** database for persistent storage
- **Redis** for caching and Celery message broker
- **Celery** workers for background job processing
- **Nginx** as reverse proxy
- **Docker** containers for easy deployment

## 🚀 Quick Start (Local Development)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-video-tool

# Create .env file
cp .env.example .env
# Edit .env with your settings
```

### 2. Configure Environment Variables

Create a `.env` file:

```env
# Application
SECRET_KEY=your-very-secret-key-change-this-in-production
DEBUG=False

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ai_video_tool

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# AWS S3 (optional)
USE_S3=false
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET=ai-video-tool
```

### 3. Run with Docker Compose

```bash
# Build and start services
docker-compose up --build

# Access the application
# Web UI: http://localhost
# API: http://localhost/api
# API Docs: http://localhost/docs
```

## 🌐 Cloud Deployment Options

### Option 1: Deploy to AWS EC2

#### Prerequisites
- AWS account
- EC2 instance (t3.medium or larger recommended)
- Domain name (optional)

#### Steps

1. **Launch EC2 Instance**
   ```bash
   # Use Ubuntu 22.04 LTS
   # Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
   ```

2. **Connect to EC2 and Install Dependencies**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip

   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker ubuntu

   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose

   # Install nginx (for SSL)
   sudo apt install nginx certbot python3-certbot-nginx -y
   ```

3. **Deploy Application**
   ```bash
   # Clone repository
   git clone <your-repo-url>
   cd ai-video-tool

   # Create .env file with production settings
   nano .env

   # Start application
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Configure SSL (if using domain)**
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

### Option 2: Deploy to Google Cloud Run

#### Prerequisites
- Google Cloud account
- gcloud CLI installed
- Docker installed locally

#### Steps

1. **Build and Push Image**
   ```bash
   # Configure gcloud
   gcloud auth login
   gcloud config set project YOUR-PROJECT-ID

   # Enable required APIs
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com

   # Build and push image
   docker build -t gcr.io/YOUR-PROJECT-ID/ai-video-tool .
   docker push gcr.io/YOUR-PROJECT-ID/ai-video-tool
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy ai-video-tool \
     --image gcr.io/YOUR-PROJECT-ID/ai-video-tool \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="DATABASE_URL=your-db-url,REDIS_URL=your-redis-url"
   ```

3. **Set up Cloud SQL and Redis**
   ```bash
   # Create Cloud SQL instance
   gcloud sql instances create ai-video-db \
     --database-version=POSTGRES_15 \
     --tier=db-g1-small \
     --region=us-central1

   # Create database
   gcloud sql databases create ai_video_tool \
     --instance=ai-video-db
   ```

### Option 3: Deploy to Heroku

#### Prerequisites
- Heroku account
- Heroku CLI installed

#### Steps

1. **Create Heroku App**
   ```bash
   heroku create your-app-name

   # Add buildpacks
   heroku buildpacks:add heroku/python
   heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
   ```

2. **Add Required Add-ons**
   ```bash
   # PostgreSQL
   heroku addons:create heroku-postgresql:mini

   # Redis
   heroku addons:create heroku-redis:mini
   ```

3. **Configure Environment**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set OPENAI_API_KEY=your-api-key
   ```

4. **Create Procfile**
   ```procfile
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   worker: celery -A tasks worker --loglevel=info
   beat: celery -A tasks beat --loglevel=info
   ```

5. **Deploy**
   ```bash
   git push heroku main
   heroku ps:scale web=1 worker=1 beat=1
   ```

### Option 4: Deploy to DigitalOcean App Platform

#### Prerequisites
- DigitalOcean account
- doctl CLI (optional)

#### Steps

1. **Create App Spec** (`app.yaml`)
   ```yaml
   name: ai-video-tool
   region: nyc
   services:
   - name: web
     github:
       repo: your-github-username/ai-video-tool
       branch: main
     build_command: pip install -r requirements.txt
     run_command: uvicorn main:app --host 0.0.0.0 --port 8080
     http_port: 8080
     instance_count: 1
     instance_size_slug: basic-xs
     envs:
     - key: DATABASE_URL
       scope: RUN_TIME
       value: ${db.DATABASE_URL}
     - key: REDIS_URL
       scope: RUN_TIME
       value: ${redis.REDIS_URL}
   
   workers:
   - name: celery-worker
     github:
       repo: your-github-username/ai-video-tool
       branch: main
     run_command: celery -A tasks worker --loglevel=info
     instance_count: 1
     instance_size_slug: basic-xs
   
   databases:
   - name: db
     engine: PG
     version: "15"
   ```

2. **Deploy via CLI or UI**
   ```bash
   doctl apps create --spec app.yaml
   ```

## 🔒 Production Security Checklist

### 1. Environment Variables
- [ ] Generate strong `SECRET_KEY`
- [ ] Use environment-specific `.env` files
- [ ] Never commit `.env` to version control

### 2. Database Security
- [ ] Use strong database passwords
- [ ] Enable SSL for database connections
- [ ] Regular backups configured
- [ ] Limited database access (IP whitelist)

### 3. API Security
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Input validation on all endpoints
- [ ] File upload size limits enforced

### 4. Infrastructure
- [ ] SSL/TLS certificates installed
- [ ] Firewall rules configured
- [ ] Regular security updates
- [ ] Monitoring and logging enabled

## 📊 Monitoring and Maintenance

### 1. Application Monitoring

```python
# Add to main.py for Sentry integration
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
    )
```

### 2. Health Checks

```bash
# Check API health
curl https://your-domain.com/health

# Check Celery workers
docker-compose exec celery_worker celery -A tasks inspect active

# Check Redis
docker-compose exec redis redis-cli ping
```

### 3. Backup Strategy

```bash
# Backup database
docker-compose exec db pg_dump -U postgres ai_video_tool > backup_$(date +%Y%m%d).sql

# Backup uploaded files
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/

# Restore database
docker-compose exec -T db psql -U postgres ai_video_tool < backup_20240101.sql
```

### 4. Scaling Considerations

#### Horizontal Scaling
```yaml
# docker-compose.scale.yml
services:
  celery_worker:
    scale: 3  # Run 3 worker instances
  
  api:
    scale: 2  # Run 2 API instances
```

#### Vertical Scaling
- Increase instance sizes for CPU/memory intensive tasks
- Use GPU instances for AI processing if needed
- Consider dedicated video processing servers

## 🚨 Troubleshooting

### Common Issues

1. **FFmpeg not found**
   ```bash
   # Install FFmpeg in container
   docker-compose exec api apt-get update && apt-get install -y ffmpeg
   ```

2. **Out of memory during video processing**
   ```bash
   # Increase Docker memory limit
   docker-compose --compatibility up
   ```

3. **Slow AI image generation**
   - Check OpenAI API rate limits
   - Implement caching for repeated requests
   - Use webhook callbacks instead of polling

4. **Database connection issues**
   ```bash
   # Check database logs
   docker-compose logs db
   
   # Test connection
   docker-compose exec api python -c "from database import init_db; import asyncio; asyncio.run(init_db())"
   ```

## 📈 Performance Optimization

### 1. Caching Strategy
```python
# Add Redis caching for frequent queries
from functools import lru_cache
import redis

redis_client = redis.from_url(settings.REDIS_URL)

@lru_cache(maxsize=100)
def get_cached_result(key: str):
    return redis_client.get(key)
```

### 2. CDN Integration
```nginx
# nginx.conf for static files
location /static {
    alias /usr/share/nginx/html/static;
    expires 365d;
    add_header Cache-Control "public, immutable";
}

location /outputs {
    alias /usr/share/nginx/html/outputs;
    expires 30d;
    add_header Cache-Control "public";
}
```

### 3. Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_jobs_user_id ON job_status(user_id);
CREATE INDEX idx_jobs_created_at ON job_status(created_at);
CREATE INDEX idx_files_user_id ON file_records(user_id);
```

## 🎯 Next Steps

1. **Set up CI/CD Pipeline**
   - GitHub Actions for automated testing
   - Automated deployment on main branch

2. **Add Monitoring**
   - Prometheus + Grafana for metrics
   - ELK stack for log aggregation

3. **Implement Auto-scaling**
   - Kubernetes for container orchestration
   - Auto-scale based on queue length

4. **Enhance Security**
   - Implement 2FA for user accounts
   - Add API rate limiting per user
   - Regular security audits

## 📞 Support

For deployment issues:
1. Check application logs: `docker-compose logs -f`
2. Review error tracking in Sentry (if configured)
3. Check the [FAQ section](#common-issues)
4. Open an issue on GitHub with deployment logs

---

**Note**: Always test your deployment in a staging environment before going to production!