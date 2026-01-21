"""Notification service for creating and broadcasting notifications."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.notification import notification
from app.models.notification import NotificationType
from app.api.v1.websocket import manager


async def broadcast_new_notification(user_id: int, notification_data: dict):
    """Broadcast new notification to the specific user via WebSocket."""
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
        print(f"WebSocket notification broadcast error: {e}")


async def create_assignment_notification(
    db: AsyncSession,
    *,
    assigned_user_id: int,
    assignment_type: str,  # "production" or "qc"
    item_code: str,
    study_label: Optional[str] = None,
    tracker_id: int,
    assigned_by_user_id: Optional[int] = None,
    assigned_by_username: Optional[str] = None
) -> None:
    """
    Create a notification when a user is assigned to a tracker item.
    
    Args:
        db: Database session
        assigned_user_id: The user being assigned
        assignment_type: "production" or "qc"
        item_code: The item code for reference
        study_label: The study label for context
        tracker_id: The tracker ID
        assigned_by_user_id: Who made the assignment
        assigned_by_username: Username of who made the assignment
    """
    if assignment_type == "production":
        notif_type = NotificationType.ASSIGNMENT_PROD.value
        title = "New Production Assignment"
        role_name = "Production Programmer"
    else:
        notif_type = NotificationType.ASSIGNMENT_QC.value
        title = "New QC Assignment"
        role_name = "QC Programmer"
    
    by_text = f" by {assigned_by_username}" if assigned_by_username else ""
    study_text = f" ({study_label})" if study_label else ""
    message = f"You have been assigned as {role_name} for item {item_code}{study_text}{by_text}"
    
    # Create the notification
    notif = await notification.create_notification(
        db,
        user_id=assigned_user_id,
        notification_type=notif_type,
        title=title,
        message=message,
        tracker_id=tracker_id,
        triggered_by_user_id=assigned_by_user_id,
        item_code=item_code,
        study_label=study_label
    )
    
    # Broadcast via WebSocket
    notif_data = {
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
        "created_at": notif.created_at.isoformat(),
        "triggered_by_username": assigned_by_username
    }
    await broadcast_new_notification(assigned_user_id, notif_data)


async def create_comment_notification(
    db: AsyncSession,
    *,
    tracker_id: int,
    item_code: str,
    study_label: Optional[str] = None,
    commenter_user_id: int,
    commenter_username: str,
    production_programmer_id: Optional[int] = None,
    qc_programmer_id: Optional[int] = None
) -> None:
    """
    Create notifications when a comment is added to a tracker item.
    Notifies the production and/or QC programmer if they are different from the commenter.
    
    Args:
        db: Database session
        tracker_id: The tracker ID
        item_code: The item code for reference
        study_label: The study label for context
        commenter_user_id: Who made the comment
        commenter_username: Username of who made the comment
        production_programmer_id: Production programmer user ID (if assigned)
        qc_programmer_id: QC programmer user ID (if assigned)
    """
    title = "New Comment on Your Item"
    study_text = f" ({study_label})" if study_label else ""
    message = f"{commenter_username} commented on item {item_code}{study_text}"
    
    # Collect users to notify (exclude the commenter)
    users_to_notify = set()
    if production_programmer_id and production_programmer_id != commenter_user_id:
        users_to_notify.add(production_programmer_id)
    if qc_programmer_id and qc_programmer_id != commenter_user_id:
        users_to_notify.add(qc_programmer_id)
    
    # Create notifications for each user
    for user_id in users_to_notify:
        notif = await notification.create_notification(
            db,
            user_id=user_id,
            notification_type=NotificationType.COMMENT_ADDED.value,
            title=title,
            message=message,
            tracker_id=tracker_id,
            triggered_by_user_id=commenter_user_id,
            item_code=item_code,
            study_label=study_label
        )
        
        # Broadcast via WebSocket
        notif_data = {
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
            "created_at": notif.created_at.isoformat(),
            "triggered_by_username": commenter_username
        }
        await broadcast_new_notification(user_id, notif_data)


async def create_biostat_assignment_notification(
    db: AsyncSession,
    *,
    assigned_user_id: int,
    item_code: str,
    study_label: Optional[str] = None,
    tracker_id: int,
    assigned_by_username: Optional[str] = None
) -> None:
    """
    Create a notification when a user is assigned as biostat reviewer.

    Args:
        db: Database session
        assigned_user_id: The user being assigned as biostat reviewer
        item_code: The item code for reference
        study_label: The study label for context
        tracker_id: The tracker ID
        assigned_by_username: Username of who made the assignment
    """
    title = "New Biostat Review Assignment"
    by_text = f" by {assigned_by_username}" if assigned_by_username else ""
    study_text = f" ({study_label})" if study_label else ""
    message = f"You have been assigned as Biostat Reviewer for item {item_code}{study_text}{by_text}"

    # Create the notification
    notif = await notification.create_notification(
        db,
        user_id=assigned_user_id,
        notification_type=NotificationType.ASSIGNMENT_BIOSTAT.value,
        title=title,
        message=message,
        tracker_id=tracker_id,
        triggered_by_user_id=None,
        item_code=item_code,
        study_label=study_label
    )

    # Broadcast via WebSocket
    notif_data = {
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
        "created_at": notif.created_at.isoformat(),
        "triggered_by_username": assigned_by_username
    }
    await broadcast_new_notification(assigned_user_id, notif_data)


async def create_biostat_failure_notification(
    db: AsyncSession,
    *,
    production_programmer_id: int,
    item_code: str,
    study_label: Optional[str] = None,
    tracker_id: int,
    biostat_username: str
) -> None:
    """
    Create a notification when a biostat reviewer fails an item.
    Notifies the production programmer that rework is needed.

    Args:
        db: Database session
        production_programmer_id: The production programmer to notify
        item_code: The item code for reference
        study_label: The study label for context
        tracker_id: The tracker ID
        biostat_username: Username of the biostat reviewer who failed the item
    """
    title = "Biostat Review Failed - Rework Required"
    study_text = f" ({study_label})" if study_label else ""
    message = f"Item {item_code}{study_text} failed biostat review by {biostat_username}. Please address the issues and resubmit."

    # Create the notification
    notif = await notification.create_notification(
        db,
        user_id=production_programmer_id,
        notification_type=NotificationType.BIOSTAT_FAILED.value,
        title=title,
        message=message,
        tracker_id=tracker_id,
        triggered_by_user_id=None,
        item_code=item_code,
        study_label=study_label
    )

    # Broadcast via WebSocket
    notif_data = {
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
        "created_at": notif.created_at.isoformat(),
        "triggered_by_username": biostat_username
    }
    await broadcast_new_notification(production_programmer_id, notif_data)
