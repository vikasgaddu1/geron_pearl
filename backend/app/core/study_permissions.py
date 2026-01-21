"""Study-scoped permission utilities.

This module provides functions to check user permissions within specific studies.
The permission hierarchy is:

1. Global ADMIN (super admin) - Has full access in all studies
2. Study Responsible User - Admin capabilities within that specific study
3. Study EDITOR - Can modify items they're assigned to
4. Study BIOSTAT - Can perform biostat review on TLF items they're assigned to
5. No explicit role (None) - Read-only access (implicit for all authenticated users)
"""

from typing import Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.user_study_role import UserStudyRole, StudyRole


# Pseudo-role for responsible users (admins and assigned responsible users)
# This replaces the old LEAD role with a string constant
RESPONSIBLE_ROLE = "RESPONSIBLE"


async def get_user_study_role(
    db: AsyncSession,
    user: User,
    study_id: int
) -> Optional[Union[StudyRole, str]]:
    """
    Get user's effective role for a specific study.

    Args:
        db: Database session
        user: The user to check
        study_id: The study ID

    Returns:
        StudyRole, "RESPONSIBLE" string, or None - The user's effective role in the study

    Permission Resolution:
        1. Global ADMIN → returns "RESPONSIBLE" (full access everywhere)
        2. Is responsible user for study → returns "RESPONSIBLE"
        3. Has explicit study role (EDITOR/BIOSTAT) → returns that role
        4. No explicit role → returns None (implicit read-only access)
    """
    # Super admin has full access everywhere
    if user.is_admin:
        return RESPONSIBLE_ROLE

    # Check if user is a responsible user for this study
    from app.crud import study_responsible_user
    is_responsible = await study_responsible_user.is_responsible_for_study(
        db, user_id=user.id, study_id=study_id
    )
    if is_responsible:
        return RESPONSIBLE_ROLE

    # Check for explicit study role assignment (EDITOR or BIOSTAT)
    result = await db.execute(
        select(UserStudyRole).where(
            UserStudyRole.user_id == user.id,
            UserStudyRole.study_id == study_id
        )
    )
    study_role = result.scalar_one_or_none()

    if study_role:
        return study_role.role

    # Default: no explicit role (implicit read-only access)
    return None


async def get_user_study_role_for_reporting_effort(
    db: AsyncSession,
    user: User,
    reporting_effort_id: int
) -> Optional[Union[StudyRole, str]]:
    """
    Get user's role for the study that owns a reporting effort.

    Args:
        db: Database session
        user: The user to check
        reporting_effort_id: The reporting effort ID

    Returns:
        StudyRole, "RESPONSIBLE", or None - The user's effective role
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
        return None

    return await get_user_study_role(db, user, study_id)


async def get_user_study_role_for_tracker(
    db: AsyncSession,
    user: User,
    tracker_id: int
) -> Optional[Union[StudyRole, str]]:
    """
    Get user's role for the study that owns a tracker.

    Traces the path: Tracker → ReportingEffortItem → ReportingEffort → Study

    Args:
        db: Database session
        user: The user to check
        tracker_id: The tracker ID

    Returns:
        StudyRole, "RESPONSIBLE", or None - The user's effective role
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
        return None

    return await get_user_study_role(db, user, study_id)


def can_modify_in_study(role: Optional[Union[StudyRole, str]]) -> bool:
    """
    Check if the role allows modifications within a study.

    EDITOR, BIOSTAT and RESPONSIBLE can modify (subject to additional assignment checks).
    None (no explicit role) = read-only access.
    """
    return role in (StudyRole.EDITOR, StudyRole.BIOSTAT, RESPONSIBLE_ROLE)


def is_study_admin(role: Optional[Union[StudyRole, str]]) -> bool:
    """
    Check if the role has admin capabilities within a study.

    Only RESPONSIBLE has study admin capabilities (bulk ops, managing study members, etc.)
    """
    return role == RESPONSIBLE_ROLE


def get_study_permissions(role: Optional[Union[StudyRole, str]]) -> Dict[str, bool]:
    """
    Get detailed permission flags for a study role.

    Returns:
        Dict with boolean flags for various permission types
    """
    if role == RESPONSIBLE_ROLE:
        return {
            "can_view": True,
            "can_edit": True,
            "can_bulk_assign": True,
            "can_bulk_status_update": True,
            "can_delete_items": True,
            "can_manage_members": True,
            "can_manage_responsible_users": True,
            "can_bulk_copy": True,
            "can_manage_packages": True,
            "can_manage_tfl_properties": True,
        }
    elif role == StudyRole.EDITOR:
        return {
            "can_view": True,
            "can_edit": True,  # Only items they're assigned to (checked separately)
            "can_bulk_assign": False,
            "can_bulk_status_update": False,
            "can_delete_items": False,
            "can_manage_members": False,
            "can_manage_responsible_users": False,
            "can_bulk_copy": False,
            "can_manage_packages": False,
            "can_manage_tfl_properties": False,
        }
    elif role == StudyRole.BIOSTAT:
        return {
            "can_view": True,
            "can_edit": True,  # Only items they're assigned as biostat reviewer (checked separately)
            "can_bulk_assign": False,
            "can_bulk_status_update": False,
            "can_delete_items": False,
            "can_manage_members": False,
            "can_manage_responsible_users": False,
            "can_bulk_copy": False,
            "can_manage_packages": False,
            "can_manage_tfl_properties": False,
        }
    else:  # None (no explicit role) = read-only access
        return {
            "can_view": True,
            "can_edit": False,
            "can_bulk_assign": False,
            "can_bulk_status_update": False,
            "can_delete_items": False,
            "can_manage_members": False,
            "can_manage_responsible_users": False,
            "can_bulk_copy": False,
            "can_manage_packages": False,
            "can_manage_tfl_properties": False,
        }


async def get_user_studies_with_roles(
    db: AsyncSession,
    user: User
) -> Dict[int, Union[StudyRole, str]]:
    """
    Get all studies the user has explicit roles in.

    Note: This doesn't include studies where user has no explicit role (implicit read access).
    Global ADMINs get an empty dict (they have full access everywhere).

    Returns:
        Dict mapping study_id to StudyRole or "RESPONSIBLE"
    """
    if user.is_admin:
        return {}  # Admin has full access everywhere, no need for explicit roles

    # Get responsible study assignments
    from app.crud import study_responsible_user
    responsible_assignments = await study_responsible_user.get_by_user(db, user_id=user.id)
    responsible_study_ids = {ra.study_id for ra in responsible_assignments}

    # Get explicit role assignments (EDITOR or BIOSTAT)
    result = await db.execute(
        select(UserStudyRole).where(UserStudyRole.user_id == user.id)
    )
    study_roles = result.scalars().all()

    # Build the result dict
    roles_dict = {}

    # Add responsible studies
    for study_id in responsible_study_ids:
        roles_dict[study_id] = RESPONSIBLE_ROLE

    # Add explicit role assignments (only if not already responsible)
    for sr in study_roles:
        if sr.study_id not in roles_dict:
            roles_dict[sr.study_id] = sr.role

    return roles_dict


async def require_study_access(
    db: AsyncSession,
    user: User,
    study_id: int,
    require_responsible: bool = True
) -> bool:
    """
    Check if user has required access to a study.
    Raises HTTPException if access denied.

    Args:
        db: Database session
        user: The user to check
        study_id: The study ID
        require_responsible: If True, require RESPONSIBLE access; if False, allow any access (VIEWER+)

    Returns:
        True if access is granted

    Raises:
        HTTPException: If access is denied
    """
    from fastapi import HTTPException, status

    # Global admins always have access
    if user.is_admin:
        return True

    # Get user's role for this study
    role = await get_user_study_role(db, user, study_id)

    if require_responsible:
        # Only RESPONSIBLE can perform this action
        if role != RESPONSIBLE_ROLE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Study responsible user privileges required for this study."
            )
    else:
        # Any role can view (VIEWER is default for all users)
        pass

    return True


async def require_study_lead_access(
    db: AsyncSession,
    user: User,
    study_id: int
) -> bool:
    """
    Convenience function to check if user has responsible/lead access to a study.
    Raises HTTPException if not.

    Note: This function name is kept for backward compatibility.
    It now checks for responsible user access.
    """
    return await require_study_access(db, user, study_id, require_responsible=True)


async def is_user_responsible_for_any_study(
    db: AsyncSession,
    user: User
) -> bool:
    """
    Check if user is a responsible user for at least one study.

    Returns:
        True if user is responsible for any study (or is admin)
    """
    if user.is_admin:
        return True

    from app.crud import study_responsible_user
    responsible_studies = await study_responsible_user.get_responsible_study_ids(db, user_id=user.id)
    return len(responsible_studies) > 0
