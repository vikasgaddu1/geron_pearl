"""
Rate Limiting Service

Per-tenant rate limiting using in-memory storage with sliding window algorithm.
For production, consider using Redis for distributed rate limiting.
"""

import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration per plan tier."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    max_concurrent_requests: int = 10


# Rate limits by plan name
PLAN_RATE_LIMITS: Dict[str, RateLimitConfig] = {
    "Free": RateLimitConfig(
        requests_per_minute=30,
        requests_per_hour=300,
        requests_per_day=3000,
        max_concurrent_requests=5,
    ),
    "Starter": RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000,
        max_concurrent_requests=10,
    ),
    "Professional": RateLimitConfig(
        requests_per_minute=120,
        requests_per_hour=3000,
        requests_per_day=30000,
        max_concurrent_requests=20,
    ),
    "Enterprise": RateLimitConfig(
        requests_per_minute=300,
        requests_per_hour=10000,
        requests_per_day=100000,
        max_concurrent_requests=50,
    ),
}

# Default rate limit for unknown plans
DEFAULT_RATE_LIMIT = RateLimitConfig()


@dataclass
class TenantUsage:
    """Track usage for a single tenant."""
    minute_requests: list = field(default_factory=list)  # timestamps
    hour_requests: list = field(default_factory=list)
    day_requests: list = field(default_factory=list)
    concurrent_count: int = 0
    last_cleanup: float = field(default_factory=time.time)


class RateLimiter:
    """
    In-memory rate limiter with sliding window algorithm.
    
    For production at scale, replace with Redis-based implementation.
    """
    
    def __init__(self):
        self._usage: Dict[int, TenantUsage] = defaultdict(TenantUsage)
        self._cleanup_interval = 60  # seconds
    
    def _cleanup_old_entries(self, usage: TenantUsage) -> None:
        """Remove expired timestamps from tracking lists."""
        now = time.time()
        
        # Only cleanup periodically
        if now - usage.last_cleanup < self._cleanup_interval:
            return
        
        minute_ago = now - 60
        hour_ago = now - 3600
        day_ago = now - 86400
        
        usage.minute_requests = [t for t in usage.minute_requests if t > minute_ago]
        usage.hour_requests = [t for t in usage.hour_requests if t > hour_ago]
        usage.day_requests = [t for t in usage.day_requests if t > day_ago]
        usage.last_cleanup = now
    
    def get_rate_limit(self, plan_name: Optional[str]) -> RateLimitConfig:
        """Get rate limit config for a plan."""
        if plan_name and plan_name in PLAN_RATE_LIMITS:
            return PLAN_RATE_LIMITS[plan_name]
        return DEFAULT_RATE_LIMIT
    
    def check_rate_limit(
        self, 
        tenant_id: int, 
        plan_name: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Dict[str, int]]:
        """
        Check if request should be allowed.
        
        Returns:
            Tuple of (allowed, error_message, headers)
        """
        config = self.get_rate_limit(plan_name)
        usage = self._usage[tenant_id]
        now = time.time()
        
        # Cleanup old entries
        self._cleanup_old_entries(usage)
        
        # Count current requests in each window
        minute_ago = now - 60
        hour_ago = now - 3600
        day_ago = now - 86400
        
        minute_count = len([t for t in usage.minute_requests if t > minute_ago])
        hour_count = len([t for t in usage.hour_requests if t > hour_ago])
        day_count = len([t for t in usage.day_requests if t > day_ago])
        
        # Build rate limit headers
        headers = {
            "X-RateLimit-Limit-Minute": config.requests_per_minute,
            "X-RateLimit-Remaining-Minute": max(0, config.requests_per_minute - minute_count),
            "X-RateLimit-Limit-Hour": config.requests_per_hour,
            "X-RateLimit-Remaining-Hour": max(0, config.requests_per_hour - hour_count),
        }
        
        # Check limits
        if minute_count >= config.requests_per_minute:
            return False, "Rate limit exceeded: too many requests per minute", headers
        
        if hour_count >= config.requests_per_hour:
            return False, "Rate limit exceeded: too many requests per hour", headers
        
        if day_count >= config.requests_per_day:
            return False, "Rate limit exceeded: daily limit reached", headers
        
        if usage.concurrent_count >= config.max_concurrent_requests:
            return False, "Rate limit exceeded: too many concurrent requests", headers
        
        return True, None, headers
    
    def record_request(self, tenant_id: int) -> None:
        """Record a new request for a tenant."""
        usage = self._usage[tenant_id]
        now = time.time()
        
        usage.minute_requests.append(now)
        usage.hour_requests.append(now)
        usage.day_requests.append(now)
        usage.concurrent_count += 1
    
    def release_request(self, tenant_id: int) -> None:
        """Release a concurrent request slot."""
        usage = self._usage[tenant_id]
        usage.concurrent_count = max(0, usage.concurrent_count - 1)
    
    def get_usage_stats(self, tenant_id: int) -> Dict:
        """Get current usage statistics for a tenant."""
        usage = self._usage[tenant_id]
        now = time.time()
        
        minute_ago = now - 60
        hour_ago = now - 3600
        day_ago = now - 86400
        
        return {
            "requests_last_minute": len([t for t in usage.minute_requests if t > minute_ago]),
            "requests_last_hour": len([t for t in usage.hour_requests if t > hour_ago]),
            "requests_last_day": len([t for t in usage.day_requests if t > day_ago]),
            "concurrent_requests": usage.concurrent_count,
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce per-tenant rate limits.
    
    Extracts tenant_id from JWT token and checks rate limits.
    Skips rate limiting for public endpoints and super admin.
    """
    
    # Endpoints that don't require rate limiting
    EXEMPT_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/billing/webhook",
        "/api/v1/plans",
    }
    
    # Path prefixes to exempt
    EXEMPT_PREFIXES = (
        "/static/",
        "/admin/",  # Super admin has separate rate limits
    )
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for exempt paths
        path = request.url.path
        if path in self.EXEMPT_PATHS or path.startswith(self.EXEMPT_PREFIXES):
            return await call_next(request)
        
        # Try to extract tenant_id from request state (set by auth middleware)
        tenant_id = getattr(request.state, "tenant_id", None)
        plan_name = getattr(request.state, "plan_name", None)
        
        # If no tenant_id, skip rate limiting (unauthenticated request)
        if not tenant_id:
            return await call_next(request)
        
        # Check rate limit
        allowed, error_message, headers = rate_limiter.check_rate_limit(
            tenant_id, plan_name
        )
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for tenant {tenant_id}: {error_message}"
            )
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": error_message},
            )
            for key, value in headers.items():
                response.headers[key] = str(value)
            response.headers["Retry-After"] = "60"
            return response
        
        # Record the request
        rate_limiter.record_request(tenant_id)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Add rate limit headers to response
            for key, value in headers.items():
                response.headers[key] = str(value)
            
            return response
        finally:
            # Release concurrent request slot
            rate_limiter.release_request(tenant_id)


def get_tenant_usage(tenant_id: int) -> Dict:
    """Get usage statistics for a tenant."""
    return rate_limiter.get_usage_stats(tenant_id)


def get_tenant_limits(plan_name: Optional[str]) -> Dict:
    """Get rate limits for a plan."""
    config = rate_limiter.get_rate_limit(plan_name)
    return {
        "requests_per_minute": config.requests_per_minute,
        "requests_per_hour": config.requests_per_hour,
        "requests_per_day": config.requests_per_day,
        "max_concurrent_requests": config.max_concurrent_requests,
    }
