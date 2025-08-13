"""CRUD operations for AuditLog."""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate


class AuditLogCRUD:
    """CRUD operations for AuditLog."""
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: AuditLogCreate
    ) -> AuditLog:
        """Create a new audit log entry."""
        db_obj = AuditLog(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def log_action(
        self,
        db: AsyncSession,
        *,
        table_name: str,
        record_id: int,
        action: str,
        user_id: Optional[int] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Helper method to log an action.
        
        Args:
            db: Database session
            table_name: Name of the table being modified
            record_id: ID of the record being modified
            action: Action performed (CREATE, UPDATE, DELETE)
            user_id: ID of the user performing the action
            changes: Dictionary of changes made
            ip_address: IP address of the user
            user_agent: User agent string
        
        Returns:
            Created audit log entry
        """
        changes_json = json.dumps(changes) if changes else None
        
        audit_data = AuditLogCreate(
            table_name=table_name,
            record_id=record_id,
            action=action,
            user_id=user_id,
            changes_json=changes_json,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return await self.create(db, obj_in=audit_data)
    
    async def get(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> Optional[AuditLog]:
        """Get a single audit log entry by ID."""
        result = await db.execute(
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(AuditLog.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get multiple audit log entries."""
        result = await db.execute(
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_table(
        self,
        db: AsyncSession,
        *,
        table_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a specific table."""
        result = await db.execute(
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(AuditLog.table_name == table_name)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_record(
        self,
        db: AsyncSession,
        *,
        table_name: str,
        record_id: int
    ) -> List[AuditLog]:
        """Get audit logs for a specific record."""
        result = await db.execute(
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(
                and_(
                    AuditLog.table_name == table_name,
                    AuditLog.record_id == record_id
                )
            )
            .order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for actions by a specific user."""
        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_date_range(
        self,
        db: AsyncSession,
        *,
        start_date: datetime,
        end_date: datetime,
        table_name: Optional[str] = None,
        action: Optional[str] = None
    ) -> List[AuditLog]:
        """Get audit logs within a date range."""
        query = select(AuditLog).options(selectinload(AuditLog.user)).where(
            and_(
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date
            )
        )
        
        if table_name:
            query = query.where(AuditLog.table_name == table_name)
        
        if action:
            query = query.where(AuditLog.action == action)
        
        query = query.order_by(AuditLog.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_statistics(
        self,
        db: AsyncSession,
        *,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get audit log statistics for the past N days.
        
        Returns:
            Dictionary with statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Count by action
        action_counts = await db.execute(
            select(
                AuditLog.action,
                func.count(AuditLog.id).label("count")
            )
            .where(AuditLog.created_at >= start_date)
            .group_by(AuditLog.action)
        )
        
        # Count by table
        table_counts = await db.execute(
            select(
                AuditLog.table_name,
                func.count(AuditLog.id).label("count")
            )
            .where(AuditLog.created_at >= start_date)
            .group_by(AuditLog.table_name)
        )
        
        # Count by user
        user_counts = await db.execute(
            select(
                AuditLog.user_id,
                func.count(AuditLog.id).label("count")
            )
            .where(
                and_(
                    AuditLog.created_at >= start_date,
                    AuditLog.user_id.isnot(None)
                )
            )
            .group_by(AuditLog.user_id)
        )
        
        return {
            "period_days": days,
            "by_action": {row.action: row.count for row in action_counts},
            "by_table": {row.table_name: row.count for row in table_counts},
            "by_user": {row.user_id: row.count for row in user_counts},
            "total": sum(row.count for row in action_counts)
        }
    
    async def cleanup_old_logs(
        self,
        db: AsyncSession,
        *,
        days_to_keep: int = 90
    ) -> int:
        """
        Delete audit logs older than specified days.
        
        Args:
            db: Database session
            days_to_keep: Number of days to keep logs
        
        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Get count before deletion
        count_result = await db.execute(
            select(func.count(AuditLog.id))
            .where(AuditLog.created_at < cutoff_date)
        )
        count = count_result.scalar_one()
        
        # Delete old logs
        if count > 0:
            await db.execute(
                select(AuditLog)
                .where(AuditLog.created_at < cutoff_date)
                .execution_options(synchronize_session="fetch")
            )
            await db.commit()
        
        return count


# Create singleton instance
audit_log = AuditLogCRUD()