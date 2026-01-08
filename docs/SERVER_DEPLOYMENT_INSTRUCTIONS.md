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

## Quick Start (5-Minute Deploy)

### Step 1: Clone the Repository

```bash
# SSH into your server, then:
cd ~
git clone https://github.com/YOUR_USERNAME/PEARL.git
cd PEARL
```

### Step 2: Create Environment File

```bash
# Create .env file with secure secrets
cat > .env << 'EOF'
# Database password - CHANGE THIS!
DB_PASSWORD=your_secure_db_password_$(openssl rand -hex 8)

# JWT secrets - CHANGE THESE!
JWT_SECRET=$(openssl rand -hex 32)
JWT_REFRESH_SECRET=$(openssl rand -hex 32)

# CORS - Update with your server IP or domain
ALLOWED_ORIGINS=["http://localhost","http://YOUR_SERVER_IP"]
EOF

# Or manually create and edit:
nano .env
```

**⚠️ Generate secure secrets:**
```bash
# Generate random passwords/secrets:
openssl rand -hex 32
```

### Step 3: Start PEARL

```bash
# Build and start all services
docker compose up -d --build

# Wait for services to be ready (about 30-60 seconds)
docker compose ps
```

### Step 4: Access the Application

- **Web App**: `http://YOUR_SERVER_IP/`
- **API Docs**: `http://YOUR_SERVER_IP/api/docs`
- **Health Check**: `http://YOUR_SERVER_IP/health`

---

## Detailed Setup Instructions

### Installing Docker (if not installed)

#### Ubuntu/Debian:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Add current user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then verify:
docker --version
docker compose version
```

#### CentOS/RHEL:
```bash
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### Environment Variables Reference

Create a `.env` file in the project root with these variables:

```env
# ===========================================
# DATABASE CONFIGURATION
# ===========================================
DB_PASSWORD=your_secure_database_password_here

# ===========================================
# SECURITY / JWT CONFIGURATION
# ===========================================
# Secret key for signing JWT access tokens
JWT_SECRET=your_super_secure_jwt_secret_key_here

# Secret key for signing JWT refresh tokens
JWT_REFRESH_SECRET=your_super_secure_refresh_secret_here

# ===========================================
# CORS CONFIGURATION
# ===========================================
# Allowed origins for CORS (JSON array format)
ALLOWED_ORIGINS=["http://localhost","http://localhost:80","http://your-server-ip"]

# ===========================================
# FRONTEND CONFIGURATION (optional)
# ===========================================
# Leave empty for relative URLs (default)
VITE_API_BASE_URL=
```

---

## Managing the Application

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
git pull origin main

# Rebuild and restart
docker compose down
docker compose up -d --build

# Run database migrations (if needed)
docker compose exec backend alembic upgrade head
```

---

## Database Management

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

## Troubleshooting

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
- Ensure both containers are on same network: `docker network ls`
- Check nginx logs: `docker compose logs frontend`
- Verify nginx config is correct

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

---

## Security Recommendations

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

### 3. Set Up HTTPS (Recommended)
For production, add an SSL certificate using Let's Encrypt:

```bash
# Install certbot
sudo apt install certbot

# Get certificate (replace with your domain)
sudo certbot certonly --standalone -d yourdomain.com

# Then update nginx config to use SSL
```

### 4. Regular Updates
```bash
# Keep Docker images updated
docker compose pull
docker compose up -d
```

---

## Production Checklist

- [ ] Strong passwords set in `.env`
- [ ] Firewall configured
- [ ] HTTPS enabled (for production)
- [ ] Regular backups scheduled
- [ ] Monitoring set up
- [ ] Log rotation configured

---

## Architecture Overview

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

- **Frontend (nginx)**: Serves React app, proxies API/WebSocket requests
- **Backend (FastAPI)**: REST API + WebSocket server
- **PostgreSQL**: Persistent data storage

---

## Useful Commands Quick Reference

```bash
# Start
docker compose up -d --build

# Stop
docker compose down

# Logs
docker compose logs -f

# Status
docker compose ps

# Update
git pull && docker compose up -d --build

# Migrate
docker compose exec backend alembic upgrade head

# Shell into backend
docker compose exec backend bash

# Database shell
docker compose exec db psql -U pearl -d pearl

# Backup
docker compose exec db pg_dump -U pearl pearl > backup.sql

# Clean up
docker system prune -a
```

---

## Support

If you encounter issues:
1. Check the logs: `docker compose logs -f`
2. Verify all environment variables are set
3. Ensure Docker and Docker Compose are up to date
4. Check GitHub Issues for known problems

