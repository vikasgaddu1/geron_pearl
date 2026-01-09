"""CRUD operations for Notification."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.crud.base import BaseCRUD
from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationCreate, NotificationUpdate, NotificationWithDetails


class CRUDNotification(BaseCRUD[Notification, NotificationCreate, NotificationUpdate]):
    """CRUD operations for notifications."""
    
    async def create_notification(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        tracker_id: Optional[int] = None,
        triggered_by_user_id: Optional[int] = None,
        item_code: Optional[str] = None,
        study_label: Optional[str] = None
    ) -> Notification:
        """Create a new notification."""
        db_obj = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            tracker_id=tracker_id,
            triggered_by_user_id=triggered_by_user_id,
            item_code=item_code,
            study_label=study_label
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_user_notifications(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        unread_only: bool = False,
        unacknowledged_only: bool = True,
        skip: int = 0,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications for a user with optional filtering."""
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        if unacknowledged_only:
            query = query.where(Notification.is_acknowledged == False)
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_user_notifications_with_details(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        unacknowledged_only: bool = True,
        limit: int = 50
    ) -> List[NotificationWithDetails]:
        """Get notifications for a user with triggered_by user details."""
        from app.models.user import User
        
        query = (
            select(Notification)
            .options(joinedload(Notification.triggered_by))
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        
        if unacknowledged_only:
            query = query.where(Notification.is_acknowledged == False)
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        notifications = result.unique().scalars().all()
        
        # Convert to NotificationWithDetails
        result_list = []
        for notif in notifications:
            data = {
                "id": notif.id,
                "user_id": notif.user_id,
                "tracker_id": notif.tracker_id,
                "triggered_by_user_id": notif.triggered_by_user_id,
                "notification_type": notif.notification_type,
                "title": notif.title,
                "message": notif.message,
                "item_code": notif.item_code,
                "study_label": notif.study_label,
                "is_read": notif.is_read,
                "is_acknowledged": notif.is_acknowledged,
                "created_at": notif.created_at,
                "read_at": notif.read_at,
                "acknowledged_at": notif.acknowledged_at,
                "triggered_by_username": notif.triggered_by.username if notif.triggered_by else None
            }
            result_list.append(NotificationWithDetails(**data))
        
        return result_list
    
    async def get_unread_count(self, db: AsyncSession, *, user_id: int) -> int:
        """Get count of unread notifications for a user."""
        query = (
            select(func.count(Notification.id))
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                    Notification.is_acknowledged == False
                )
            )
        )
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def get_unacknowledged_count(self, db: AsyncSession, *, user_id: int) -> int:
        """Get count of unacknowledged notifications for a user."""
        query = (
            select(func.count(Notification.id))
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_acknowledged == False
                )
            )
        )
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def mark_as_read(self, db: AsyncSession, *, notification_id: int, user_id: int) -> Optional[Notification]:
        """Mark a notification as read."""
        notif = await self.get(db, id=notification_id)
        if notif and notif.user_id == user_id:
            notif.is_read = True
            notif.read_at = datetime.utcnow()
            await db.commit()
            await db.refresh(notif)
            return notif
        return None
    
    async def mark_as_acknowledged(self, db: AsyncSession, *, notification_id: int, user_id: int) -> Optional[Notification]:
        """Mark a notification as acknowledged (dismissed)."""
        notif = await self.get(db, id=notification_id)
        if notif and notif.user_id == user_id:
            notif.is_read = True
            notif.is_acknowledged = True
            notif.read_at = notif.read_at or datetime.utcnow()
            notif.acknowledged_at = datetime.utcnow()
            await db.commit()
            await db.refresh(notif)
            return notif
        return None
    
    async def mark_all_as_read(self, db: AsyncSession, *, user_id: int) -> int:
        """Mark all notifications as read for a user."""
        now = datetime.utcnow()
        query = (
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
            .values(is_read=True, read_at=now)
        )
        result = await db.execute(query)
        await db.commit()
        return result.rowcount
    
    async def acknowledge_all(self, db: AsyncSession, *, user_id: int) -> int:
        """Acknowledge (dismiss) all notifications for a user."""
        now = datetime.utcnow()
        query = (
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_acknowledged == False
                )
            )
            .values(is_read=True, is_acknowledged=True, read_at=now, acknowledged_at=now)
        )
        result = await db.execute(query)
        await db.commit()
        return result.rowcount
    
    async def delete_old_acknowledged(self, db: AsyncSession, *, days: int = 30) -> int:
        """Delete acknowledged notifications older than specified days."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Find notifications to delete
        query = select(Notification).where(
            and_(
                Notification.is_acknowledged == True,
                Notification.acknowledged_at < cutoff
            )
        )
        result = await db.execute(query)
        notifications = result.scalars().all()
        
        count = 0
        for notif in notifications:
            await db.delete(notif)
            count += 1
        
        await db.commit()
        return count


# Singleton instance
notification = CRUDNotification(Notification)
