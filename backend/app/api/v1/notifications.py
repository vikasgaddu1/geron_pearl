"""Notification API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.crud.notification import notification
from app.schemas.notification import (
    Notification,
    NotificationWithDetails,
    NotificationCountResponse
)
from app.api.v1.websocket import manager

router = APIRouter()


async def broadcast_notification_count(user_id: int, unread_count: int):
    """Broadcast updated notification count to the specific user."""
    try:
        message = {
            "type": "notification_count_updated",
            "data": {
                "user_id": user_id,
                "unread_count": unread_count
            }
        }
        await manager.broadcast_json(message)
    except Exception as e:
        print(f"WebSocket broadcast error: {e}")


async def broadcast_new_notification(user_id: int, notification_data: dict):
    """Broadcast new notification to the specific user."""
    try:
        message = {
            "type": "notification_created",
            "data": {
                "user_id": user_id,
                "notification": notification_data
            }
        }
        await manager.broadcast_json(message)
    except Exception as e:
        print(f"WebSocket broadcast error: {e}")


@router.get("/", response_model=List[NotificationWithDetails])
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50
) -> List[NotificationWithDetails]:
    """
    Get notifications for the current user.
    
    Returns unacknowledged notifications sorted by most recent first.
    """
    return await notification.get_user_notifications_with_details(
        db,
        user_id=current_user.id,
        unacknowledged_only=True,
        limit=limit
    )


@router.get("/count", response_model=NotificationCountResponse)
async def get_notification_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NotificationCountResponse:
    """
    Get notification counts for the current user.
    
    Returns count of unread and total unacknowledged notifications.
    """
    unread_count = await notification.get_unread_count(db, user_id=current_user.id)
    total_unacknowledged = await notification.get_unacknowledged_count(db, user_id=current_user.id)
    
    return NotificationCountResponse(
        unread_count=unread_count,
        total_unacknowledged=total_unacknowledged
    )


@router.post("/{notification_id}/read", response_model=Notification)
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Notification:
    """
    Mark a notification as read.
    """
    result = await notification.mark_as_read(
        db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied"
        )
    
    # Broadcast updated count
    unread_count = await notification.get_unread_count(db, user_id=current_user.id)
    await broadcast_notification_count(current_user.id, unread_count)
    
    return result


@router.post("/{notification_id}/acknowledge", response_model=Notification)
async def acknowledge_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Notification:
    """
    Acknowledge (dismiss) a notification.
    
    Acknowledged notifications will no longer appear in the notification list.
    """
    result = await notification.mark_as_acknowledged(
        db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied"
        )
    
    # Broadcast updated count
    unread_count = await notification.get_unread_count(db, user_id=current_user.id)
    await broadcast_notification_count(current_user.id, unread_count)
    
    return result


@router.post("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Mark all notifications as read for the current user.
    """
    count = await notification.mark_all_as_read(db, user_id=current_user.id)
    
    # Broadcast updated count
    await broadcast_notification_count(current_user.id, 0)
    
    return {"message": f"Marked {count} notifications as read"}


@router.post("/acknowledge-all")
async def acknowledge_all_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Acknowledge (dismiss) all notifications for the current user.
    """
    count = await notification.acknowledge_all(db, user_id=current_user.id)
    
    # Broadcast updated count
    await broadcast_notification_count(current_user.id, 0)
    
    return {"message": f"Acknowledged {count} notifications"}
