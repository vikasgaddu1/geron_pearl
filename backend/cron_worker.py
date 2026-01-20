#!/usr/bin/env python
"""
PEARL Cron Worker

Runs scheduled background tasks for the PEARL multi-tenant SaaS platform.
This script is designed to be run as a separate Railway service or cron job.

Tasks:
- Data retention cleanup (soft-deleted tenants, old audit logs, notifications)
- Subscription expiration checks
- Usage statistics aggregation

Usage:
    # Run all tasks
    python cron_worker.py --all
    
    # Run specific tasks
    python cron_worker.py --retention
    python cron_worker.py --subscriptions
    
    # Run as HTTP server for Railway cron
    python cron_worker.py --server
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lazy imports to avoid loading everything at module level
async def get_db_session():
    """Get a database session for cron tasks."""
    from app.db.session import async_session_factory
    async with async_session_factory() as session:
        yield session


async def run_retention_cleanup() -> Dict[str, Any]:
    """
    Run data retention cleanup tasks.
    
    - Delete soft-deleted tenants past retention period (90 days)
    - Clean up old audit logs (365 days)
    - Clean up old notifications (90 days)
    """
    logger.info("Starting data retention cleanup...")
    
    from app.db.session import async_session_factory
    from app.services.data_retention import run_scheduled_cleanup
    
    async with async_session_factory() as db:
        results = await run_scheduled_cleanup(db)
    
    logger.info(f"Retention cleanup complete: {results}")
    return results


async def run_subscription_checks() -> Dict[str, Any]:
    """
    Check for subscription issues and send alerts.
    
    - Check for subscriptions in grace period
    - Check for expired subscriptions
    - Send warning emails for upcoming expirations
    """
    logger.info("Starting subscription checks...")
    
    from sqlalchemy import select, and_
    from datetime import timedelta
    from app.db.session import async_session_factory
    from app.models.tenant import Tenant
    
    results = {
        "grace_period_count": 0,
        "expired_count": 0,
        "warnings_sent": 0,
    }
    
    async with async_session_factory() as db:
        now = datetime.utcnow()
        
        # Count tenants in grace period
        result = await db.execute(
            select(Tenant).where(
                and_(
                    Tenant.subscription_status == "grace_period",
                    Tenant.is_active == True,
                )
            )
        )
        grace_period_tenants = result.scalars().all()
        results["grace_period_count"] = len(grace_period_tenants)
        
        # Count expired tenants
        result = await db.execute(
            select(Tenant).where(
                and_(
                    Tenant.subscription_status == "expired",
                    Tenant.is_active == True,
                )
            )
        )
        expired_tenants = result.scalars().all()
        results["expired_count"] = len(expired_tenants)
        
        # Log warning for high counts
        if results["grace_period_count"] > 0:
            logger.warning(f"{results['grace_period_count']} tenants in grace period")
        
        if results["expired_count"] > 0:
            logger.warning(f"{results['expired_count']} tenants with expired subscriptions")
    
    logger.info(f"Subscription checks complete: {results}")
    return results


async def run_usage_aggregation() -> Dict[str, Any]:
    """
    Aggregate usage statistics for billing and analytics.
    
    This is a placeholder for future usage tracking.
    """
    logger.info("Starting usage aggregation...")
    
    results = {
        "status": "not_implemented",
        "message": "Usage aggregation will be implemented when needed",
    }
    
    logger.info(f"Usage aggregation complete: {results}")
    return results


async def run_all_tasks() -> Dict[str, Any]:
    """Run all scheduled tasks."""
    results = {
        "started_at": datetime.utcnow().isoformat(),
        "tasks": {},
    }
    
    # Run retention cleanup
    try:
        results["tasks"]["retention"] = await run_retention_cleanup()
    except Exception as e:
        logger.error(f"Retention cleanup failed: {e}")
        results["tasks"]["retention"] = {"error": str(e)}
    
    # Run subscription checks
    try:
        results["tasks"]["subscriptions"] = await run_subscription_checks()
    except Exception as e:
        logger.error(f"Subscription checks failed: {e}")
        results["tasks"]["subscriptions"] = {"error": str(e)}
    
    results["completed_at"] = datetime.utcnow().isoformat()
    return results


# =============================================================================
# HTTP Server for Railway Cron
# =============================================================================

app = FastAPI(
    title="PEARL Cron Worker",
    description="Background task runner for PEARL multi-tenant SaaS",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    return {
        "status": "healthy",
        "service": "cron-worker",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/run/all")
async def trigger_all_tasks():
    """Trigger all scheduled tasks (called by Railway cron)."""
    try:
        results = await run_all_tasks()
        return JSONResponse(content=results)
    except Exception as e:
        logger.error(f"Failed to run tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run/retention")
async def trigger_retention_cleanup():
    """Trigger retention cleanup task."""
    try:
        results = await run_retention_cleanup()
        return JSONResponse(content=results)
    except Exception as e:
        logger.error(f"Failed to run retention cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run/subscriptions")
async def trigger_subscription_checks():
    """Trigger subscription checks task."""
    try:
        results = await run_subscription_checks()
        return JSONResponse(content=results)
    except Exception as e:
        logger.error(f"Failed to run subscription checks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="PEARL Cron Worker")
    parser.add_argument("--all", action="store_true", help="Run all tasks")
    parser.add_argument("--retention", action="store_true", help="Run retention cleanup")
    parser.add_argument("--subscriptions", action="store_true", help="Run subscription checks")
    parser.add_argument("--server", action="store_true", help="Run as HTTP server")
    parser.add_argument("--port", type=int, default=8001, help="Server port (default: 8001)")
    
    args = parser.parse_args()
    
    if args.server:
        # Run as HTTP server
        port = int(os.environ.get("PORT", args.port))
        logger.info(f"Starting cron worker HTTP server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    elif args.all:
        asyncio.run(run_all_tasks())
    elif args.retention:
        asyncio.run(run_retention_cleanup())
    elif args.subscriptions:
        asyncio.run(run_subscription_checks())
    else:
        # Default: run all tasks
        asyncio.run(run_all_tasks())


if __name__ == "__main__":
    main()
