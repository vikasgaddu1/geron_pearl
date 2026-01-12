"""CRUD operations for ErrorLog."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.error_log import ErrorLog
from app.schemas.error_log import ErrorLogCreate


class ErrorLogCRUD:
    """CRUD operations for ErrorLog."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: ErrorLogCreate
    ) -> ErrorLog:
        """Create a new error log entry."""
        db_obj = ErrorLog(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def log_error(
        self,
        db: AsyncSession,
        *,
        source: str,
        severity: str,
        error_type: str,
        message: str,
        stack_trace: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        request_body: Optional[str] = None,
        response_status: Optional[int] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        component_name: Optional[str] = None,
        browser_info: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> ErrorLog:
        """
        Helper method to log an error.

        Args:
            db: Database session
            source: Error source (BACKEND or FRONTEND)
            severity: Error severity (INFO, WARNING, ERROR, CRITICAL)
            error_type: Type of error (e.g., ValidationError, TypeError)
            message: Error message
            stack_trace: Full stack trace
            request_method: HTTP method
            request_path: Request URL path
            request_body: Sanitized request body
            response_status: HTTP response status code
            user_id: User who encountered the error
            ip_address: Client IP address
            user_agent: Browser user agent
            component_name: React component name (frontend)
            browser_info: Browser/OS info (frontend)
            correlation_id: UUID for tracing related errors

        Returns:
            Created error log entry
        """
        error_data = ErrorLogCreate(
            source=source,
            severity=severity,
            error_type=error_type,
            message=message,
            stack_trace=stack_trace,
            request_method=request_method,
            request_path=request_path,
            request_body=request_body,
            response_status=response_status,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            component_name=component_name,
            browser_info=browser_info,
            correlation_id=correlation_id
        )

        return await self.create(db, obj_in=error_data)

    async def get(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> Optional[ErrorLog]:
        """Get a single error log entry by ID."""
        result = await db.execute(
            select(ErrorLog)
            .options(selectinload(ErrorLog.user))
            .where(ErrorLog.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        source: Optional[str] = None,
        severity: Optional[str] = None,
        error_type: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ErrorLog]:
        """Get multiple error log entries with filters."""
        query = select(ErrorLog).options(selectinload(ErrorLog.user))

        filters = []
        if source:
            filters.append(ErrorLog.source == source)
        if severity:
            filters.append(ErrorLog.severity == severity)
        if error_type:
            filters.append(ErrorLog.error_type == error_type)
        if user_id:
            filters.append(ErrorLog.user_id == user_id)
        if start_date:
            filters.append(ErrorLog.created_at >= start_date)
        if end_date:
            filters.append(ErrorLog.created_at <= end_date)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(ErrorLog.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_statistics(
        self,
        db: AsyncSession,
        *,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get error log statistics for the past N days.

        Returns:
            Dictionary with statistics by severity, source, type, day, and top endpoints
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get all logs in the period
        query = select(ErrorLog).where(ErrorLog.created_at >= start_date)
        result = await db.execute(query)
        logs = list(result.scalars().all())

        stats: Dict[str, Any] = {
            "period_days": days,
            "total_errors": len(logs),
            "by_severity": {},
            "by_source": {},
            "by_type": {},
            "by_day": {},
            "top_endpoints": []
        }

        endpoint_counts: Dict[str, int] = {}

        for log in logs:
            # By severity
            stats["by_severity"][log.severity] = stats["by_severity"].get(log.severity, 0) + 1
            # By source
            stats["by_source"][log.source] = stats["by_source"].get(log.source, 0) + 1
            # By type
            stats["by_type"][log.error_type] = stats["by_type"].get(log.error_type, 0) + 1
            # By day
            day_key = log.created_at.date().isoformat()
            stats["by_day"][day_key] = stats["by_day"].get(day_key, 0) + 1
            # Top endpoints
            if log.request_path:
                endpoint_counts[log.request_path] = endpoint_counts.get(log.request_path, 0) + 1

        # Get top 10 endpoints
        stats["top_endpoints"] = [
            {"path": path, "count": count}
            for path, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        return stats

    async def cleanup_old_logs(
        self,
        db: AsyncSession,
        *,
        days_to_keep: int = 30
    ) -> int:
        """
        Delete error logs older than specified days.

        Args:
            db: Database session
            days_to_keep: Number of days to keep logs

        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Get count before deletion
        count_result = await db.execute(
            select(func.count(ErrorLog.id)).where(ErrorLog.created_at < cutoff_date)
        )
        count = count_result.scalar_one()

        # Delete old logs
        if count > 0:
            await db.execute(
                delete(ErrorLog).where(ErrorLog.created_at < cutoff_date)
            )
            await db.commit()

        return count


# Create singleton instance
error_log = ErrorLogCRUD()
