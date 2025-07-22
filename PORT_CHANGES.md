# Port Configuration Changes

The AI Video Tool has been configured to run on different ports to avoid conflicts with other services.

## New Port Configuration

- **Backend API**: Port 8080 (changed from 8000)
- **Frontend**: Served by the backend on port 8080 (no separate frontend server)
- **Database**: Port 5432 (PostgreSQL)
- **Redis**: Port 6379
- **Nginx**: Ports 80/443 (in production)

## How to Run the Project

### Option 1: Direct Python Execution
```bash
# Run the development server
python run_dev.py
```

### Option 2: Windows Batch File
```cmd
# Double-click or run in command prompt
start_dev.bat
```

### Option 3: PowerShell Script
```powershell
# Run in PowerShell
.\start_dev.ps1
```

### Option 4: Docker Compose
```bash
# Development environment
docker-compose up

# Production environment
docker-compose -f docker-compose.prod.yml up -d
```

## Access URLs

Once the server is running, you can access:

- **Web Interface**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health
- **ReDoc Documentation**: http://localhost:8080/redoc

## Environment Variables

The following environment variables can be set to customize the configuration:

```bash
# Server settings
HOST=0.0.0.0
PORT=8080

# Database
DATABASE_URL=sqlite+aiosqlite:///./ai_video_tool.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here

# OpenAI
OPENAI_API_KEY=your-openai-api-key
```

## Troubleshooting

### Port Already in Use
If port 8080 is already in use, you can change it by:

1. Modifying `config.py`:
   ```python
   PORT: int = 8081  # or any other available port
   ```

2. Updating `main.py`:
   ```python
   port=8081  # or any other available port
   ```

3. Updating `docker-compose.yml` if using Docker:
   ```yaml
   ports:
     - "8081:8081"
   ```

### CORS Issues
If you encounter CORS issues, make sure the new port is added to `ALLOWED_ORIGINS` in `config.py`:

```python
ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8080",  # New port
    "https://yourdomain.com"
]
```

## Services Overview

- **FastAPI Backend**: Main application server
- **Celery Worker**: Background task processing
- **PostgreSQL**: Database for user data and job status
- **Redis**: Message broker for Celery tasks
- **Nginx**: Reverse proxy (production only)

All services are now configured to work together on the new port configuration. 