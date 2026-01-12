"""Middleware package."""

from app.middleware.error_logging import ErrorLoggingMiddleware

__all__ = ["ErrorLoggingMiddleware"]
