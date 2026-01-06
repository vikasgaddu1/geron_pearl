"""Study-scoped permission utilities.

This module provides functions to check user permissions within specific studies.
The permission hierarchy is:

1. Global ADMIN (super admin) - Has LEAD access in all studies
2. Study LEAD - Admin capabilities within that specific study
3. Study EDITOR - Can modify items they're assigned to
4. Study VIEWER - Read-only access (default for all users)
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.user_study_role import UserStudyRole, StudyRole


async def get_user_study_role(
    db: AsyncSession,
    user: User,
    study_id: int
) -> StudyRole:
    """
    Get user's effective role for a specific study.
    
    Args:
        db: Database session
        user: The user to check
        study_id: The study ID
        
    Returns:
        StudyRole - The user's effective role in the study
        
    Permission Resolution:
        1. Global ADMIN → returns LEAD (full access everywhere)
        2. Has explicit study role → returns that role
        3. No explicit role → returns VIEWER (default access)
    """
    # Super admin has LEAD access everywhere
    if user.is_admin:
        return StudyRole.LEAD
    
    # Check for explicit study role assignment
    result = await db.execute(
        select(UserStudyRole).where(
            UserStudyRole.user_id == user.id,
            UserStudyRole.study_id == study_id
        )
    )
    study_role = result.scalar_one_or_none()
    
    if study_role:
        return study_role.role
    
    # Default: all users have viewer access
    return StudyRole.VIEWER


async def get_user_study_role_for_reporting_effort(
    db: AsyncSession,
    user: User,
    reporting_effort_id: int
) -> StudyRole:
    """
    Get user's role for the study that owns a reporting effort.
    
    Args:
        db: Database session
        user: The user to check
        reporting_effort_id: The reporting effort ID
        
    Returns:
        StudyRole - The user's effective role
    """
    from app.models.reporting_effort import ReportingEffort
    
    # Get the study_id from the reporting effort
    result = await db.execute(
        select(ReportingEffort.study_id).where(
            ReportingEffort.id == reporting_effort_id
        )
    )
    study_id = result.scalar_one_or_none()
    
    if study_id is None:
        return StudyRole.VIEWER
    
    return await get_user_study_role(db, user, study_id)


async def get_user_study_role_for_tracker(
    db: AsyncSession,
    user: User,
    tracker_id: int
) -> StudyRole:
    """
    Get user's role for the study that owns a tracker.
    
    Traces the path: Tracker → ReportingEffortItem → ReportingEffort → Study
    
    Args:
        db: Database session
        user: The user to check
        tracker_id: The tracker ID
        
    Returns:
        StudyRole - The user's effective role
    """
    from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
    from app.models.reporting_effort_item import ReportingEffortItem
    from app.models.reporting_effort import ReportingEffort
    
    # Get study_id through the relationship chain
    result = await db.execute(
        select(ReportingEffort.study_id)
        .select_from(ReportingEffortItemTracker)
        .join(ReportingEffortItem, ReportingEffortItemTracker.reporting_effort_item_id == ReportingEffortItem.id)
        .join(ReportingEffort, ReportingEffortItem.reporting_effort_id == ReportingEffort.id)
        .where(ReportingEffortItemTracker.id == tracker_id)
    )
    study_id = result.scalar_one_or_none()
    
    if study_id is None:
        return StudyRole.VIEWER
    
    return await get_user_study_role(db, user, study_id)


def can_modify_in_study(role: StudyRole) -> bool:
    """
    Check if the role allows modifications within a study.
    
    EDITOR and LEAD can modify (subject to additional assignment checks for EDITOR).
    """
    return role in (StudyRole.EDITOR, StudyRole.LEAD)


def is_study_admin(role: StudyRole) -> bool:
    """
    Check if the role has admin capabilities within a study.
    
    Only LEAD has study admin capabilities (bulk ops, managing study members, etc.)
    """
    return role == StudyRole.LEAD


def get_study_permissions(role: StudyRole) -> Dict[str, bool]:
    """
    Get detailed permission flags for a study role.
    
    Returns:
        Dict with boolean flags for various permission types
    """
    if role == StudyRole.LEAD:
        return {
            "can_view": True,
            "can_edit": True,
            "can_bulk_assign": True,
            "can_bulk_status_update": True,
            "can_delete_items": True,
            "can_manage_members": True,
            "can_bulk_copy": True,
        }
    elif role == StudyRole.EDITOR:
        return {
            "can_view": True,
            "can_edit": True,  # Only items they're assigned to (checked separately)
            "can_bulk_assign": False,
            "can_bulk_status_update": False,
            "can_delete_items": False,
            "can_manage_members": False,
            "can_bulk_copy": False,
        }
    else:  # VIEWER
        return {
            "can_view": True,
            "can_edit": False,
            "can_bulk_assign": False,
            "can_bulk_status_update": False,
            "can_delete_items": False,
            "can_manage_members": False,
            "can_bulk_copy": False,
        }


async def get_user_studies_with_roles(
    db: AsyncSession,
    user: User
) -> Dict[int, StudyRole]:
    """
    Get all studies the user has explicit roles in.
    
    Note: This doesn't include studies where user has default VIEWER access.
    Global ADMINs get an empty dict (they have LEAD everywhere).
    
    Returns:
        Dict mapping study_id to StudyRole
    """
    if user.is_admin:
        return {}  # Admin has LEAD everywhere, no need for explicit roles
    
    result = await db.execute(
        select(UserStudyRole).where(UserStudyRole.user_id == user.id)
    )
    study_roles = result.scalars().all()
    
    return {sr.study_id: sr.role for sr in study_roles}

