# PEARL Server Deployment Instructions

> **For deploying PEARL on your own server with Docker**  
> **Last Updated**: January 2026

---

## Prerequisites

Your server needs:
- **Docker** installed
- **Docker Compose** (v2+) installed
- **Git** (to clone the repository)
- At least **2GB RAM** and **10GB disk space**

---

## 🚀 Step-by-Step Deployment (Copy & Paste)

### Step 1: Install Docker (if not installed)

```bash
# Check if Docker is installed
docker --version
docker compose version

# If NOT installed, run these:
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# IMPORTANT: Log out and log back in after this, then continue
```

### Step 2: Clone the Repository

```bash
cd ~
git clone https://github.com/vikasgaddu1/geron_pearl.git PEARL
cd PEARL
git checkout feature/throughput-estimation-system
```

### Step 3: Generate Secure Secrets

Run this command twice and save both outputs:
```bash
openssl rand -hex 32
```

### Step 4: Create Environment File

```bash
nano .env
```

Paste this content (replace the placeholder values with your generated secrets):

```env
DB_PASSWORD=PearlSecure2026!
JWT_SECRET=PASTE_FIRST_OPENSSL_OUTPUT_HERE
JWT_REFRESH_SECRET=PASTE_SECOND_OPENSSL_OUTPUT_HERE
ALLOWED_ORIGINS=["http://localhost","http://YOUR_SERVER_IP"]
```

Save and exit: `Ctrl+O`, `Enter`, `Ctrl+X`

### Step 5: Build and Start

```bash
docker compose up -d --build
```

⏱️ **First run takes 2-5 minutes** as it downloads and builds images.

### Step 6: Monitor Startup

```bash
# Watch the logs (Ctrl+C to exit)
docker compose logs -f
```

Wait until you see:
```
pearl-backend  | Uvicorn running on http://0.0.0.0:8000
```

### Step 7: Verify It's Working

```bash
# Check all containers are running
docker compose ps

# Test health endpoint
curl http://localhost/health
```

### Step 8: Access the Application

Open in your browser:
- **Web App**: `http://YOUR_SERVER_IP/`
- **API Docs**: `http://YOUR_SERVER_IP/api/docs`
- **Health Check**: `http://YOUR_SERVER_IP/health`

---

## ✅ Quick Verification Commands

```bash
# All containers should show "Up" status
docker compose ps

# Should return {"status":"healthy"}
curl http://localhost/health

# Should return API documentation HTML
curl http://localhost/api/docs
```

---

## 📋 Managing the Application

### View Status
```bash
cd ~/PEARL
docker compose ps
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

### Stop Services
```bash
docker compose down
```

### Restart Services
```bash
docker compose restart

# Or restart specific service
docker compose restart backend
```

### Update to Latest Version
```bash
cd ~/PEARL

# Pull latest code
git pull

# Rebuild and restart
docker compose down
docker compose up -d --build

# Run database migrations (if schema changed)
docker compose exec backend alembic upgrade head
```

---

## 🗄️ Database Management

### Run Migrations
```bash
docker compose exec backend alembic upgrade head
```

### Access Database Shell
```bash
docker compose exec db psql -U pearl -d pearl
```

### Backup Database
```bash
docker compose exec db pg_dump -U pearl pearl > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database
```bash
cat backup_file.sql | docker compose exec -T db psql -U pearl -d pearl
```

---

## 🔧 Troubleshooting

### Container Won't Start
```bash
# Check logs for errors
docker compose logs backend
docker compose logs frontend

# Check if ports are in use
sudo netstat -tlnp | grep -E '80|8000'
```

### Database Connection Issues
```bash
# Check if db container is healthy
docker compose ps

# Verify DATABASE_URL is correct
docker compose exec backend env | grep DATABASE_URL

# Test database connection
docker compose exec db psql -U pearl -d pearl -c "SELECT 1;"
```

### Frontend Can't Reach Backend
```bash
# Ensure both containers are on same network
docker network ls

# Check nginx logs
docker compose logs frontend
```

### Permission Issues
```bash
# If you get permission denied on docker commands:
sudo usermod -aG docker $USER
# Log out and back in
```

### Out of Disk Space
```bash
# Clean up unused Docker resources
docker system prune -a

# Check disk usage
df -h
docker system df
```

### Nuclear Reset (Start Fresh)
```bash
docker compose down -v
docker system prune -a
docker compose up -d --build
```

---

## 🔐 Security Recommendations

### 1. Use Strong Secrets
Generate secure random strings for all secrets:
```bash
openssl rand -hex 32
```

### 2. Set Up Firewall
```bash
# Ubuntu/Debian with UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (if using SSL)
sudo ufw enable
```

### 3. Set Up HTTPS (Recommended for Production)
```bash
# Install certbot
sudo apt install certbot

# Get certificate (replace with your domain)
sudo certbot certonly --standalone -d yourdomain.com

# Then update nginx config to use SSL
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                           │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐    │
│  │   Frontend   │   │   Backend    │   │    PostgreSQL    │    │
│  │    (nginx)   │──▶│   (FastAPI)  │──▶│    (Database)    │    │
│  │   Port 80    │   │  Port 8000   │   │    Port 5432     │    │
│  └──────────────┘   └──────────────┘   └──────────────────┘    │
│         ▲                                                       │
│         │                                                       │
│    Web Browser                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| Service | Technology | Port | Purpose |
|---------|------------|------|---------|
| Frontend | nginx + React | 80 | Serves web app, proxies API calls |
| Backend | FastAPI | 8000 (internal) | REST API + WebSocket server |
| Database | PostgreSQL | 5432 (internal) | Data persistence |

---

## 📝 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_PASSWORD` | PostgreSQL password | `MySecure123!` |
| `JWT_SECRET` | Access token signing key | `(openssl rand -hex 32)` |
| `JWT_REFRESH_SECRET` | Refresh token signing key | `(openssl rand -hex 32)` |
| `ALLOWED_ORIGINS` | CORS allowed origins (JSON array) | `["http://localhost"]` |

---

## 🔄 Quick Reference Card

```bash
# ===== STARTUP =====
docker compose up -d --build      # Build and start
docker compose ps                  # Check status
docker compose logs -f             # Watch logs

# ===== SHUTDOWN =====
docker compose down                # Stop all
docker compose down -v             # Stop and delete data

# ===== MAINTENANCE =====
docker compose restart             # Restart all
docker compose exec backend bash   # Shell into backend
docker compose exec db psql -U pearl -d pearl  # Database shell

# ===== UPDATES =====
git pull                           # Get latest code
docker compose up -d --build       # Rebuild
docker compose exec backend alembic upgrade head  # Migrate

# ===== BACKUP =====
docker compose exec db pg_dump -U pearl pearl > backup.sql

# ===== CLEANUP =====
docker system prune -a             # Remove unused images/containers
```

---

## ✅ Production Checklist

- [ ] Strong passwords set in `.env`
- [ ] Firewall configured (ports 22, 80, 443)
- [ ] HTTPS enabled (for production)
- [ ] Regular backups scheduled
- [ ] Server IP added to `ALLOWED_ORIGINS`
- [ ] Tested login functionality
- [ ] Tested WebSocket (real-time updates)

---

## 🆘 Getting Help

If you encounter issues:
1. Check the logs: `docker compose logs -f`
2. Verify all environment variables are set correctly
3. Ensure Docker and Docker Compose are up to date
4. Restart services: `docker compose restart`
5. Nuclear option: `docker compose down -v && docker compose up -d --build`
