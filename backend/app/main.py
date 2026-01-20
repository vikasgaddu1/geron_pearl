"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.v1 import api_router
from app.core.config import settings
from app.core.tenant import TenantContextMiddleware
from app.core.rate_limiting import RateLimitMiddleware
from app.db.init_db import init_db
from app.db.session import engine
from app.middleware.error_logging import ErrorLoggingMiddleware
from app.middleware.impersonation import ImpersonationReadOnlyMiddleware

# MCP is optional - only load if available
try:
    from fastapi_mcp import FastApiMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up PEARL Backend...")
    try:
        # Initialize database tables
        await init_db(engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down PEARL Backend...")
    await engine.dispose()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    description="PEARL FastAPI backend with async PostgreSQL",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    redirect_slashes=False,  # Don't redirect - auth headers get lost in redirects
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error logging middleware (logs errors to database)
app.add_middleware(ErrorLoggingMiddleware)

# Add impersonation read-only middleware (blocks mutations in read-only mode)
app.add_middleware(ImpersonationReadOnlyMiddleware)

# Add tenant context middleware (extracts tenant_id from JWT for RLS)
app.add_middleware(TenantContextMiddleware)

# Add rate limiting middleware (uses tenant_id from request.state)
# Note: Must be added AFTER TenantContextMiddleware in code, which means
# it runs BEFORE TenantContextMiddleware in the request flow
app.add_middleware(RateLimitMiddleware)

# Add MCP integration (if available)
if MCP_AVAILABLE:
    mcp = FastApiMCP(app)
    mcp.mount()  # This mounts MCP server at /mcp endpoint
    logger.info("MCP integration enabled")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions.
    Error is already logged by ErrorLoggingMiddleware.
    """
    correlation_id = getattr(request.state, 'correlation_id', None)
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "path": str(request.url),
            "method": request.method,
            "correlation_id": correlation_id,
        }
    )


# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "PEARL Backend API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }