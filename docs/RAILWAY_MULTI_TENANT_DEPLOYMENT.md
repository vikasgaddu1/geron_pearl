# PEARL Multi-Tenant Railway Deployment Guide

This guide covers deploying PEARL as a multi-tenant SaaS platform on Railway.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Railway Project                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Frontend   │  │   Backend   │  │     Cron Worker         │ │
│  │   (nginx)   │  │  (FastAPI)  │  │  (Scheduled Tasks)      │ │
│  │  Port 80    │  │  Port 8000  │  │  Port 8001              │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
│         │                │                      │               │
│         └────────────────┼──────────────────────┘               │
│                          │                                      │
│                    ┌─────┴─────┐                                │
│                    │ PostgreSQL│                                │
│                    │  Database │                                │
│                    └───────────┘                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Services Overview

| Service | Description | Dockerfile | Port |
|---------|-------------|------------|------|
| **Backend** | FastAPI application | `backend/Dockerfile` | 8000 |
| **Frontend** | React + nginx | `react-frontend/Dockerfile` | 80 |
| **Cron Worker** | Background tasks | `backend/Dockerfile.cron` | 8001 |
| **PostgreSQL** | Database | Railway managed | 5432 |

---

## Step-by-Step Deployment

### 1. Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway init
```

### 2. Create PostgreSQL Database

1. In Railway dashboard, click **+ New** → **Database** → **PostgreSQL**
2. Railway will create a PostgreSQL service with `DATABASE_URL` variable

### 3. Deploy Backend Service

1. Click **+ New** → **GitHub Repo** → Select PEARL repository
2. Set root directory: `/backend`
3. Configure environment variables:

```env
# Required
DATABASE_URL=${POSTGRES_URL}  # Auto-linked from PostgreSQL
JWT_SECRET=your-secure-jwt-secret-min-32-chars
ALLOWED_ORIGINS=["https://your-frontend.up.railway.app"]
FRONTEND_URL=https://your-frontend.up.railway.app

# Stripe (for billing)
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_STARTER_PRICE_ID=price_xxx
STRIPE_PROFESSIONAL_PRICE_ID=price_xxx
STRIPE_ENTERPRISE_PRICE_ID=price_xxx

# Email (SendGrid)
SENDGRID_API_KEY=SG.xxx
SENDGRID_FROM_EMAIL=noreply@pearl-app.com

# Optional
APP_VERSION=1.0.0
ENVIRONMENT=production
```

### 4. Deploy Frontend Service

1. Click **+ New** → **GitHub Repo** → Select PEARL repository
2. Set root directory: `/react-frontend`
3. Configure environment variables:

```env
BACKEND_URL=https://your-backend.up.railway.app
```

4. Update `nginx.railway.conf` with backend hostname

### 5. Deploy Cron Worker Service

1. Click **+ New** → **GitHub Repo** → Select PEARL repository
2. Set root directory: `/backend`
3. Set **Dockerfile Path**: `Dockerfile.cron`
4. Configure environment variables (same as backend):

```env
DATABASE_URL=${POSTGRES_URL}
```

5. Set up Railway cron job:
   - Go to service settings
   - Under "Cron", add schedule: `0 */6 * * *` (every 6 hours)
   - Endpoint: `POST /run/all`

---

## Environment Variables Reference

### Backend Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Auto-linked |
| `JWT_SECRET` | JWT signing key (min 32 chars) | Random string |
| `ALLOWED_ORIGINS` | CORS origins (JSON array) | `["https://..."]` |
| `FRONTEND_URL` | Frontend URL for emails | `https://...` |

### Backend Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_VERSION` | App version | `1.0.0` |
| `ENVIRONMENT` | Environment name | `production` |
| `GRACE_PERIOD_DAYS` | Subscription grace period | `7` |

### Stripe Variables (for billing)

| Variable | Description |
|----------|-------------|
| `STRIPE_SECRET_KEY` | Stripe API secret key |
| `STRIPE_WEBHOOK_SECRET` | Webhook signing secret |
| `STRIPE_STARTER_PRICE_ID` | Starter plan price ID |
| `STRIPE_PROFESSIONAL_PRICE_ID` | Professional plan price ID |
| `STRIPE_ENTERPRISE_PRICE_ID` | Enterprise plan price ID |

---

## Cron Worker Tasks

The cron worker runs scheduled background tasks:

| Task | Endpoint | Description | Recommended Schedule |
|------|----------|-------------|---------------------|
| All tasks | `POST /run/all` | Run all scheduled tasks | Every 6 hours |
| Retention | `POST /run/retention` | Clean up old data | Daily at 3 AM |
| Subscriptions | `POST /run/subscriptions` | Check subscriptions | Every 6 hours |

### Setting Up Railway Cron

1. Go to cron worker service settings
2. Add a cron schedule under "Triggers"
3. Configure the schedule (cron expression)
4. Set the HTTP endpoint to trigger

Example cron expressions:
- `0 */6 * * *` - Every 6 hours
- `0 3 * * *` - Daily at 3 AM UTC
- `0 0 * * 0` - Weekly on Sunday at midnight

---

## Health Checks

### Backend Health Check

```
GET /api/v1/system/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0",
  "timestamp": "2026-01-20T10:30:00Z"
}
```

### Cron Worker Health Check

```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "cron-worker",
  "timestamp": "2026-01-20T10:30:00Z"
}
```

---

## Cost Monitoring

### Setting Up Cost Alerts

1. Go to Railway Project Settings → Usage
2. Click "Set Usage Limit"
3. Configure alert thresholds:
   - Warning: 80% of budget
   - Critical: 95% of budget

### Estimated Monthly Costs

| Service | Estimated Cost | Notes |
|---------|---------------|-------|
| Backend | $5-20/mo | Scales with traffic |
| Frontend | $5-10/mo | Static assets, low CPU |
| Cron Worker | $2-5/mo | Runs periodically |
| PostgreSQL | $5-20/mo | Scales with data |
| **Total** | **$17-55/mo** | Hobby tier |

For production with higher traffic:
- Use Railway's Pro plan for better resources
- Consider horizontal scaling for backend
- Monitor database performance

---

## Database Management

### Running Migrations

Migrations run automatically on backend deployment via `start.sh`.

Manual migration (Railway CLI):
```bash
railway run alembic upgrade head
```

### Database Backup

Railway provides automatic daily backups for PostgreSQL.

For manual backup:
```bash
railway run pg_dump $DATABASE_URL > backup.sql
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 502 Bad Gateway | Backend not responding | Check backend logs |
| CORS errors | Wrong ALLOWED_ORIGINS | Update to match frontend URL |
| Database connection failed | Wrong DATABASE_URL | Verify PostgreSQL linkage |
| Cron not running | Wrong endpoint or schedule | Check cron configuration |

### Viewing Logs

```bash
# View backend logs
railway logs -s backend

# View cron worker logs
railway logs -s cron-worker

# Follow logs in real-time
railway logs -s backend --follow
```

### Restarting Services

```bash
# Redeploy a service
railway redeploy -s backend
```

---

## Security Checklist

- [ ] JWT_SECRET is at least 32 characters and random
- [ ] ALLOWED_ORIGINS only includes your frontend URL
- [ ] Stripe keys are for production (not test)
- [ ] Database has strong password
- [ ] HTTPS enforced on all services
- [ ] Environment variables not logged
- [ ] Rate limiting enabled

---

## Monitoring Recommendations

1. **Uptime Monitoring**: Use Railway's built-in health checks or external service (UptimeRobot, Pingdom)

2. **Error Tracking**: Integrate Sentry for error reporting
   ```env
   SENTRY_DSN=https://xxx@sentry.io/xxx
   ```

3. **Log Aggregation**: Railway provides built-in logging, or integrate with Papertrail/Datadog

4. **Performance Monitoring**: Monitor response times via Railway metrics

---

## Scaling Considerations

### Horizontal Scaling

For high traffic:
1. Enable Railway replicas for backend
2. Use Redis for session storage and rate limiting
3. Consider read replicas for database

### Vertical Scaling

1. Upgrade to Railway Pro for more resources
2. Increase PostgreSQL plan for more connections
3. Monitor CPU/memory usage in Railway dashboard

---

## Quick Reference

### Railway CLI Commands

```bash
# Login
railway login

# Link to project
railway link

# Deploy
railway up

# View logs
railway logs

# Run command
railway run <command>

# Open service in browser
railway open
```

### Health Check URLs

- Backend: `https://your-backend.up.railway.app/api/v1/system/health`
- Cron: `https://your-cron.up.railway.app/health`
- Frontend: `https://your-frontend.up.railway.app/`
