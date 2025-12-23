# PEARL Docker Containerization Guide

> **Author**: Auto-generated containerization plan  
> **Date**: December 2024  
> **Status**: Ready to implement

---

## Overview

This guide explains how to containerize the PEARL application and deploy it to any server that has Docker installed. No other dependencies (Python, Node.js, PostgreSQL) are needed on the server.

### What Gets Containerized

| Service | Technology | Port |
|---------|------------|------|
| Backend | FastAPI (Python) | 8000 |
| Frontend | React + nginx | 80 |
| Database | PostgreSQL | 5432 |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                           │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐    │
│  │   Frontend   │   │   Backend    │   │    PostgreSQL    │    │
│  │    (nginx)   │──▶│   (FastAPI)  │──▶│    (Database)    │    │
│  │   Port 80    │   │  Port 8000   │   │    Port 5432     │    │
│  └──────────────┘   └──────────────┘   └──────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Files to Create

### 1.1 Backend Dockerfile

**Location**: `backend/Dockerfile`

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application (production mode - no reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### 1.2 Backend .dockerignore

**Location**: `backend/.dockerignore`

```
__pycache__
*.pyc
*.pyo
.venv
venv
.env
.git
.gitignore
*.md
htmlcov
.coverage
.pytest_cache
tests/
backups/
```

---

### 1.3 Frontend Dockerfile

**Location**: `react-frontend/Dockerfile`

```dockerfile
# Frontend Dockerfile - Multi-stage build
# Stage 1: Build the React app
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

### 1.4 Frontend nginx.conf

**Location**: `react-frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Handle React Router (SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Proxy health endpoint
    location /health {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Proxy WebSocket connections
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

---

### 1.5 Frontend .dockerignore

**Location**: `react-frontend/.dockerignore`

```
node_modules
dist
.git
.gitignore
*.md
.env
.env.*
```

---

### 1.6 Docker Compose (for local testing with build)

**Location**: `docker-compose.yml` (project root)

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: pearl-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: pearl
      POSTGRES_PASSWORD: ${DB_PASSWORD:-pearl_secret_password}
      POSTGRES_DB: pearl
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pearl -d pearl"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - pearl-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: pearl-backend
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://pearl:${DB_PASSWORD:-pearl_secret_password}@db:5432/pearl
      JWT_SECRET: ${JWT_SECRET:-change-me-in-production}
      ENV: production
      ALLOWED_ORIGINS: '["http://localhost", "http://localhost:80", "http://frontend"]'
    ports:
      - "8000:8000"
    networks:
      - pearl-network

  frontend:
    build:
      context: ./react-frontend
      dockerfile: Dockerfile
    container_name: pearl-frontend
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "80:80"
    networks:
      - pearl-network

volumes:
  postgres_data:

networks:
  pearl-network:
    driver: bridge
```

---

### 1.7 Docker Compose (for production - pulls from registry)

**Location**: `docker-compose.prod.yml` (project root)

> **Note**: Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: pearl-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: pearl
      POSTGRES_PASSWORD: ${DB_PASSWORD:-pearl_secret_password}
      POSTGRES_DB: pearl
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pearl -d pearl"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - pearl-network

  backend:
    image: ghcr.io/YOUR_GITHUB_USERNAME/pearl-backend:latest
    container_name: pearl-backend
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://pearl:${DB_PASSWORD:-pearl_secret_password}@db:5432/pearl
      JWT_SECRET: ${JWT_SECRET:-change-me-in-production}
      ENV: production
      ALLOWED_ORIGINS: '["http://localhost", "http://localhost:80", "http://frontend"]'
    ports:
      - "8000:8000"
    networks:
      - pearl-network

  frontend:
    image: ghcr.io/YOUR_GITHUB_USERNAME/pearl-frontend:latest
    container_name: pearl-frontend
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "80:80"
    networks:
      - pearl-network

volumes:
  postgres_data:

networks:
  pearl-network:
    driver: bridge
```

---

### 1.8 Environment File

**Location**: `.env` (project root - DO NOT COMMIT TO GIT)

```env
# Production secrets - change these values!
DB_PASSWORD=your_secure_database_password_here
JWT_SECRET=your_super_secure_jwt_secret_key_here
```

---

## Part 2: GitHub Container Registry Setup

### 2.1 Create Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Name it: `Docker PEARL`
4. Select permissions:
   - ✅ `write:packages`
   - ✅ `read:packages`
   - ✅ `delete:packages`
5. Click **Generate token**
6. **⚠️ COPY AND SAVE THE TOKEN** — you won't see it again!

### 2.2 Login to GitHub Container Registry

```powershell
# On your Windows machine
docker login ghcr.io -u YOUR_GITHUB_USERNAME
# When prompted, paste your Personal Access Token as the password
```

---

## Part 3: Build and Push Images

### 3.1 Build Images Locally

```powershell
cd C:\python\PEARL

# Build backend image
docker build -t ghcr.io/YOUR_GITHUB_USERNAME/pearl-backend:latest ./backend

# Build frontend image  
docker build -t ghcr.io/YOUR_GITHUB_USERNAME/pearl-frontend:latest ./react-frontend
```

### 3.2 Push to GitHub Container Registry

```powershell
# Push backend
docker push ghcr.io/YOUR_GITHUB_USERNAME/pearl-backend:latest

# Push frontend
docker push ghcr.io/YOUR_GITHUB_USERNAME/pearl-frontend:latest
```

### 3.3 Verify Upload

Go to: `https://github.com/YOUR_USERNAME?tab=packages`

You should see your two packages listed.

---

## Part 4: Test Locally

Before deploying to the server, test everything locally:

```powershell
cd C:\python\PEARL

# Start all services (builds images locally)
docker-compose up --build

# Or run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Stop and remove volumes (deletes database!)
docker-compose down -v
```

Access the app at: http://localhost

---

## Part 5: Server Deployment

### 5.1 Server Prerequisites (One-Time)

SSH into your server and run:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Add your user to docker group (logout/login after)
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### 5.2 Create Project Directory

```bash
mkdir ~/pearl
cd ~/pearl
```

### 5.3 Create Required Files on Server

Create `docker-compose.yml` on the server with the production content from section 1.7.

Create `.env` file:
```bash
nano .env
```

Add:
```env
DB_PASSWORD=your_secure_database_password_here
JWT_SECRET=your_super_secure_jwt_secret_key_here
```

### 5.4 Login to GitHub Container Registry

```bash
docker login ghcr.io -u YOUR_GITHUB_USERNAME
# Enter your Personal Access Token as password
```

### 5.5 Start the Application

```bash
cd ~/pearl

# Pull images and start
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### 5.6 Run Database Migrations (First Time Only)

```bash
# Run Alembic migrations
docker compose exec backend alembic upgrade head

# Or initialize database
docker compose exec backend python -m app.db.init_db
```

---

## Part 6: Accessing the Application

| Service | URL |
|---------|-----|
| Main App (React) | `http://your-server-ip/` |
| API Documentation | `http://your-server-ip/api/docs` |
| Health Check | `http://your-server-ip/health` |

---

## Part 7: Updating the Application

When you make code changes:

### On Your Development Machine:

```powershell
# Rebuild images
docker build -t ghcr.io/YOUR_GITHUB_USERNAME/pearl-backend:latest ./backend
docker build -t ghcr.io/YOUR_GITHUB_USERNAME/pearl-frontend:latest ./react-frontend

# Push new versions
docker push ghcr.io/YOUR_GITHUB_USERNAME/pearl-backend:latest
docker push ghcr.io/YOUR_GITHUB_USERNAME/pearl-frontend:latest
```

### On the Server:

```bash
cd ~/pearl

# Pull new images
docker compose pull

# Restart with new images
docker compose up -d

# Run migrations if database changed
docker compose exec backend alembic upgrade head
```

---

## Part 8: Useful Commands

### View Status
```bash
docker compose ps
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
```

### Restart Services
```bash
docker compose restart
```

### Stop Services
```bash
docker compose down
```

### Access Container Shell
```bash
# Backend
docker compose exec backend bash

# Database
docker compose exec db psql -U pearl -d pearl
```

### Check Image Sizes
```bash
docker images | grep pearl
```

---

## Part 9: Troubleshooting

### Container won't start
```bash
docker compose logs backend
```

### Database connection issues
- Check if db container is healthy: `docker compose ps`
- Verify DATABASE_URL matches docker-compose.yml

### Frontend can't reach backend
- Ensure both containers are on same network
- Check nginx.conf proxy settings

### Images too large
- Use `python:3.11-slim` instead of `python:3.11`
- Use multi-stage builds for frontend
- Add more items to `.dockerignore`

---

## Storage Estimates

| Image | Expected Size |
|-------|--------------|
| Backend | ~250-300 MB |
| Frontend | ~25-35 MB |
| **Total** | ~275-335 MB |

GitHub Free Tier: 500 MB (should be enough!)

---

## Quick Reference Card

```
# Login to registry
docker login ghcr.io -u USERNAME

# Build
docker build -t ghcr.io/USERNAME/pearl-backend:latest ./backend
docker build -t ghcr.io/USERNAME/pearl-frontend:latest ./react-frontend

# Push
docker push ghcr.io/USERNAME/pearl-backend:latest
docker push ghcr.io/USERNAME/pearl-frontend:latest

# On server - start
docker compose up -d

# On server - update
docker compose pull && docker compose up -d

# On server - logs
docker compose logs -f
```

---

## Checklist

- [ ] Create `backend/Dockerfile`
- [ ] Create `backend/.dockerignore`
- [ ] Create `react-frontend/Dockerfile`
- [ ] Create `react-frontend/nginx.conf`
- [ ] Create `react-frontend/.dockerignore`
- [ ] Create `docker-compose.yml`
- [ ] Create `docker-compose.prod.yml`
- [ ] Create `.env` (add to .gitignore!)
- [ ] Create GitHub Personal Access Token
- [ ] Login to ghcr.io
- [ ] Build and test locally
- [ ] Push images to registry
- [ ] Set up server with Docker
- [ ] Deploy to server
- [ ] Run database migrations
- [ ] Test application

---

**Enjoy your vacation! 🏖️**

