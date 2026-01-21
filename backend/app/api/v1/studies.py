"""Studies API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import study, user_study_role, user, audit_log, study_responsible_user, study_default_biostat
from app.crud import database_release, reporting_effort
from app.db.session import get_db
from app.schemas.study import Study, StudyCreate, StudyUpdate, BulkHierarchyRow, BulkHierarchyResponse
from app.schemas.database_release import DatabaseReleaseCreate
from app.schemas.reporting_effort import ReportingEffortCreate
from app.schemas.user_study_role import (
    AssignStudyRoleRequest, UserStudyRole, UserStudyRoleUpdate,
    StudyMembersResponse, StudyMember, StudyPermissions
)
from app.schemas.study_responsible_user import (
    AssignResponsibleUserRequest, UpdateResponsibleUserRequest,
    StudyResponsibleUserWithUser, StudyResponsibleUsersResponse
)
from app.schemas.study_default_biostat import (
    StudyDefaultBiostat, StudyDefaultBiostatWithUser
)
from app.models.user_study_role import StudyRole
from app.models.user import User as UserModel
from app.core.security import get_current_user, require_admin
from app.core.study_permissions import get_user_study_role, is_study_admin, get_study_permissions, require_study_lead_access
from app.core.subscription import require_active_subscription, check_study_limit
from app.api.v1.websocket import (
    broadcast_study_created, broadcast_study_updated, broadcast_study_deleted,
    broadcast_study_responsible_user_created, broadcast_study_responsible_user_updated,
    broadcast_study_responsible_user_deleted
)

router = APIRouter()


@router.post("/", response_model=Study, status_code=status.HTTP_201_CREATED)
async def create_study(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    study_in: StudyCreate,
    current_user: UserModel = Depends(require_admin()),
    _subscription: None = Depends(require_active_subscription),
    _limit: None = Depends(check_study_limit),
) -> Study:
    """
    Create a new study.
    """
    try:
        # Check if study with same label already exists
        existing_study = await study.get_by_label(db, study_label=study_in.study_label)
        if existing_study:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Study with this label already exists"
            )

        created_study = await study.create(db, obj_in=study_in, tenant_id=current_user.tenant_id)

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="studies",
                record_id=created_study.id,
                action="CREATE",
                user_id=current_user.id,
                changes={"study_label": created_study.study_label},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_study_created(created_study)
        except Exception:
            pass  # WebSocket broadcast is best-effort

        return created_study
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create study"
        )


@router.get("/", response_model=List[Study])
async def read_studies(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user),
) -> List[Study]:
    """
    Retrieve studies with pagination.
    Requires authentication.
    """
    try:
        return await study.get_multi(db, skip=skip, limit=limit)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve studies"
        )


@router.get("/{study_id}", response_model=Study)
async def read_study(
    *,
    db: AsyncSession = Depends(get_db),
    study_id: int,
    current_user: UserModel = Depends(get_current_user),
) -> Study:
    """
    Get a specific study by ID.
    Requires authentication.
    """
    try:
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )
        return db_study
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve study"
        )


@router.put("/{study_id}", response_model=Study)
async def update_study(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    study_id: int,
    study_in: StudyUpdate,
    current_user: UserModel = Depends(get_current_user),
) -> Study:
    """
    Update an existing study.
    """
    try:
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )

        # Capture old values for audit
        old_label = db_study.study_label

        # Authorization: require admin or LEAD for this study
        await require_study_lead_access(db, current_user, study_id)

        # Check if new label conflicts with existing study
        if study_in.study_label:
            existing_study = await study.get_by_label(db, study_label=study_in.study_label)
            if existing_study and existing_study.id != study_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Study with this label already exists"
                )

        updated_study = await study.update(db, db_obj=db_study, obj_in=study_in)

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="studies",
                record_id=updated_study.id,
                action="UPDATE",
                user_id=current_user.id,
                changes={"old": {"study_label": old_label}, "new": {"study_label": updated_study.study_label}},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_study_updated(updated_study)
        except Exception:
            pass  # WebSocket broadcast is best-effort

        return updated_study
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update study"
        )


@router.delete("/{study_id}", response_model=Study)
async def delete_study(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    study_id: int,
    current_user: UserModel = Depends(require_admin()),
) -> Study:
    """
    Delete a study. Only admins can delete studies.
    """
    try:
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )

        # Capture values for audit before deletion
        deleted_label = db_study.study_label

        # Check for associated database releases before deletion
        associated_releases = await database_release.get_by_study_id(db, study_id=study_id)
        if associated_releases:
            release_labels = [release.database_release_label for release in associated_releases]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete study '{db_study.study_label}': {len(associated_releases)} associated database release(s) exist: {', '.join(release_labels)}. Please delete all associated database releases first."
            )

        deleted_study = await study.delete(db, id=study_id)

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="studies",
                record_id=study_id,
                action="DELETE",
                user_id=current_user.id,
                changes={"deleted": {"study_label": deleted_label}},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_study_deleted(study_id)
        except Exception:
            pass  # WebSocket broadcast is best-effort

        return deleted_study
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete study"
        )


# ============================================================================
# Bulk hierarchy upload: Study -> Database Release -> Reporting Effort
# ============================================================================


@router.post("/bulk-hierarchy", response_model=BulkHierarchyResponse)
async def bulk_upload_hierarchy(
    *,
    db: AsyncSession = Depends(get_db),
    rows: List[BulkHierarchyRow],
    current_user: UserModel = Depends(require_admin()),
) -> BulkHierarchyResponse:
    """
    Bulk upload studies, database releases, and reporting efforts in one go.
    Duplicates are ignored (counted as skipped_duplicates).
    """
    created_studies = 0
    created_releases = 0
    created_efforts = 0
    skipped_duplicates = 0
    errors: list[str] = []

    for idx, row in enumerate(rows):
        try:
            study_label = row.study_label.strip()
            release_label = row.database_release_label.strip()
            effort_label = row.reporting_effort_label.strip()

            if not study_label or not release_label or not effort_label:
                errors.append(f"Row {idx+1}: All three columns are required")
                continue

            # Study (case/space insensitive handled in CRUD)
            existing_study = await study.get_by_label(db, study_label=study_label)
            if existing_study:
                study_obj = existing_study
                skipped_duplicates += 1
            else:
                study_obj = await study.create(db, obj_in=StudyCreate(study_label=study_label), tenant_id=current_user.tenant_id)
                created_studies += 1

            # Database release (scoped to study)
            existing_release = await database_release.get_by_study_and_label(
                db, study_id=study_obj.id, database_release_label=release_label
            )
            if existing_release:
                release_obj = existing_release
                skipped_duplicates += 1
            else:
                release_obj = await database_release.create(
                    db,
                    obj_in=DatabaseReleaseCreate(
                        study_id=study_obj.id,
                        database_release_label=release_label,
                        database_release_date=None,
                    ),
                )
                created_releases += 1

            # Reporting effort (scoped to release)
            existing_effort = await reporting_effort.get_by_release_and_label(
                db,
                database_release_id=release_obj.id,
                database_release_label=effort_label,
            )
            if existing_effort:
                skipped_duplicates += 1
            else:
                await reporting_effort.create(
                    db,
                    obj_in=ReportingEffortCreate(
                        study_id=study_obj.id,
                        database_release_id=release_obj.id,
                        database_release_label=effort_label,
                    ),
                )
                created_efforts += 1
        except Exception as e:
            errors.append(f"Row {idx+1}: {str(e)}")

    return BulkHierarchyResponse(
        success=len(errors) == 0,
        created_studies=created_studies,
        created_releases=created_releases,
        created_efforts=created_efforts,
        skipped_duplicates=skipped_duplicates,
        errors=errors,
    )


# ============================================================================
# Study Member Management Endpoints (Study-Scoped Access Control)
# ============================================================================

@router.get("/{study_id}/permissions", response_model=StudyPermissions)
async def get_my_study_permissions(
    *,
    db: AsyncSession = Depends(get_db),
    study_id: int,
    current_user: UserModel = Depends(get_current_user),
) -> StudyPermissions:
    """
    Get the current user's permissions for a specific study.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )
        
        role = await get_user_study_role(db, current_user, study_id)
        permissions = get_study_permissions(role)
        
        return StudyPermissions(
            study_id=study_id,
            role=role,
            **permissions
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get study permissions"
        )


@router.get("/{study_id}/members", response_model=StudyMembersResponse)
async def get_study_members(
    *,
    db: AsyncSession = Depends(get_db),
    study_id: int,
    include_defaults: bool = True,
    current_user: UserModel = Depends(get_current_user),
) -> StudyMembersResponse:
    """
    Get all members for a study with their roles.
    
    - include_defaults: If True, include users with default viewer access
    
    Only LEAD users (or global ADMIN) can see the full member list with assignments.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )
        
        # Check permissions - LEAD or ADMIN can view members
        user_role = await get_user_study_role(db, current_user, study_id)
        if not is_study_admin(user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only study leads can view member assignments"
            )
        
        members_data = await user_study_role.get_study_members(
            db, study_id=study_id, include_defaults=include_defaults
        )
        
        members = [StudyMember(**m) for m in members_data]
        
        return StudyMembersResponse(
            study_id=study_id,
            study_label=db_study.study_label,
            members=members,
            total_count=len(members)
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get study members"
        )


@router.get("/{study_id}/available-users")
async def get_available_users_for_study(
    *,
    db: AsyncSession = Depends(get_db),
    study_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get all users that can be assigned to a study.

    Returns non-admin, active users from the same tenant.
    Only responsible users (or global ADMIN) can access this endpoint.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )

        # Check permissions - responsible user or ADMIN can view available users
        user_role = await get_user_study_role(db, current_user, study_id)
        if not is_study_admin(user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only study responsible users can view available users"
            )

        # Get all non-admin, active users from the same tenant
        users_list = await user.get_available_for_assignment(
            db, tenant_id=current_user.tenant_id
        )

        return [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "is_admin": u.is_admin,
                "is_active": u.is_active,
            }
            for u in users_list
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available users: {str(e)}"
        )


@router.post("/{study_id}/members", response_model=UserStudyRole)
async def assign_study_member(
    *,
    db: AsyncSession = Depends(get_db),
    study_id: int,
    assignment: AssignStudyRoleRequest,
    current_user: UserModel = Depends(get_current_user),
) -> UserStudyRole:
    """
    Assign or update a user's role in a study.
    
    Only LEAD users (or global ADMIN) can assign roles.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )
        
        # Check permissions - LEAD or ADMIN can assign roles
        user_role = await get_user_study_role(db, current_user, study_id)
        if not is_study_admin(user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only study leads can assign member roles"
            )
        
        # Check if target user exists
        target_user = await user.get(db, id=assignment.user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Cannot assign roles to global admins (they already have LEAD everywhere)
        if target_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign study roles to global administrators"
            )
        
        # Create or update the role assignment
        role_assignment = await user_study_role.assign_role(
            db,
            user_id=assignment.user_id,
            study_id=study_id,
            role=assignment.role
        )
        
        return role_assignment
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign study member"
        )


@router.put("/{study_id}/members/{user_id}", response_model=UserStudyRole)
async def update_study_member_role(
    *,
    db: AsyncSession = Depends(get_db),
    study_id: int,
    user_id: int,
    role_update: UserStudyRoleUpdate,
    current_user: UserModel = Depends(get_current_user),
) -> UserStudyRole:
    """
    Update a user's role in a study.
    
    Only LEAD users (or global ADMIN) can update roles.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )
        
        # Check permissions
        current_user_role = await get_user_study_role(db, current_user, study_id)
        if not is_study_admin(current_user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only study leads can update member roles"
            )
        
        # Check if target user exists
        target_user = await user.get(db, id=user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Cannot modify roles for global admins
        if target_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify study roles for global administrators"
            )
        
        # Update the role
        role_assignment = await user_study_role.assign_role(
            db,
            user_id=user_id,
            study_id=study_id,
            role=role_update.role
        )
        
        return role_assignment
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update study member role"
        )


@router.delete("/{study_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_study_member(
    *,
    db: AsyncSession = Depends(get_db),
    study_id: int,
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
) -> None:
    """
    Remove a user's role assignment from a study.
    
    The user will revert to default viewer access.
    Only LEAD users (or global ADMIN) can remove roles.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )
        
        # Check permissions
        current_user_role = await get_user_study_role(db, current_user, study_id)
        if not is_study_admin(current_user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only study leads can remove member roles"
            )
        
        # Check if there's an explicit role to remove
        existing_role = await user_study_role.get_by_user_and_study(
            db, user_id=user_id, study_id=study_id
        )
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User does not have an explicit role assignment for this study"
            )
        
        # Remove the role assignment
        await user_study_role.remove_role(db, user_id=user_id, study_id=study_id)
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove study member"
        )


# ============================================================================
# Study Responsible Users Management Endpoints
# ============================================================================

@router.get("/{study_id}/responsible-users", response_model=StudyResponsibleUsersResponse)
async def get_study_responsible_users(
    *,
    db: AsyncSession = Depends(get_db),
    study_id: int,
    current_user: UserModel = Depends(get_current_user),
) -> StudyResponsibleUsersResponse:
    """
    Get all responsible users for a study.

    Responsible users have admin-level permissions within the study.
    Only study responsible users (or global admins) can view this list.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )

        # Check permissions - responsible user or admin can view responsible users
        user_role = await get_user_study_role(db, current_user, study_id)
        if not is_study_admin(user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only study responsible users or admins can view responsible user assignments"
            )

        # Get responsible users with details
        responsible_users_data = await study_responsible_user.get_responsible_users_with_details(
            db, study_id=study_id
        )

        responsible_users = [StudyResponsibleUserWithUser(**ru) for ru in responsible_users_data]

        return StudyResponsibleUsersResponse(
            study_id=study_id,
            study_label=db_study.study_label,
            responsible_users=responsible_users,
            total_count=len(responsible_users)
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get study responsible users"
        )


@router.post("/{study_id}/responsible-users", response_model=StudyResponsibleUserWithUser)
async def assign_responsible_user(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    study_id: int,
    assignment: AssignResponsibleUserRequest,
    current_user: UserModel = Depends(get_current_user),
) -> StudyResponsibleUserWithUser:
    """
    Assign a user as responsible for a study.

    Only admins or existing responsible users can assign new responsible users.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )

        # Check permissions - admin or existing responsible user
        user_role = await get_user_study_role(db, current_user, study_id)
        if not is_study_admin(user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only study responsible users or admins can assign responsible users"
            )

        # Check if target user exists
        target_user = await user.get(db, id=assignment.user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Cannot assign global admins (they already have full access everywhere)
        if target_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign global administrators as responsible users (they already have full access)"
            )

        # Check if already assigned
        existing = await study_responsible_user.get_by_user_and_study(
            db, user_id=assignment.user_id, study_id=study_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a responsible user for this study"
            )

        # Create the assignment
        created = await study_responsible_user.assign(
            db,
            study_id=study_id,
            user_id=assignment.user_id,
            is_primary=assignment.is_primary
        )

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="study_responsible_users",
                record_id=created.id,
                action="CREATE",
                user_id=current_user.id,
                changes={
                    "study_id": study_id,
                    "user_id": assignment.user_id,
                    "username": target_user.username,
                    "is_primary": assignment.is_primary
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Build response
        response = StudyResponsibleUserWithUser(
            id=created.id,
            study_id=created.study_id,
            user_id=created.user_id,
            is_primary=created.is_primary,
            username=target_user.username,
            email=target_user.email,
            created_at=created.created_at,
            updated_at=created.updated_at
        )

        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_study_responsible_user_created(response.model_dump(mode='json'))
        except Exception:
            pass  # WebSocket broadcast is best-effort

        return response
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign responsible user"
        )


@router.put("/{study_id}/responsible-users/{user_id}", response_model=StudyResponsibleUserWithUser)
async def update_responsible_user(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    study_id: int,
    user_id: int,
    update_data: UpdateResponsibleUserRequest,
    current_user: UserModel = Depends(get_current_user),
) -> StudyResponsibleUserWithUser:
    """
    Update a responsible user's status (e.g., set as primary).

    Only admins or existing responsible users can update.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )

        # Check permissions
        current_user_role = await get_user_study_role(db, current_user, study_id)
        if not is_study_admin(current_user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only study responsible users or admins can update responsible users"
            )

        # Check if target user exists
        target_user = await user.get(db, id=user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if assignment exists
        existing = await study_responsible_user.get_by_user_and_study(
            db, user_id=user_id, study_id=study_id
        )
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a responsible user for this study"
            )

        # Update the assignment
        updated = await study_responsible_user.set_primary(
            db,
            study_id=study_id,
            user_id=user_id,
            is_primary=update_data.is_primary
        )

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="study_responsible_users",
                record_id=updated.id,
                action="UPDATE",
                user_id=current_user.id,
                changes={
                    "study_id": study_id,
                    "user_id": user_id,
                    "username": target_user.username,
                    "is_primary": update_data.is_primary
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Build response
        response = StudyResponsibleUserWithUser(
            id=updated.id,
            study_id=updated.study_id,
            user_id=updated.user_id,
            is_primary=updated.is_primary,
            username=target_user.username,
            email=target_user.email,
            created_at=updated.created_at,
            updated_at=updated.updated_at
        )

        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_study_responsible_user_updated(response.model_dump(mode='json'))
        except Exception:
            pass  # WebSocket broadcast is best-effort

        return response
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update responsible user"
        )


@router.delete("/{study_id}/responsible-users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_responsible_user(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    study_id: int,
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
) -> None:
    """
    Remove a user's responsible status from a study.

    Only admins or existing responsible users can remove.
    Cannot remove the last responsible user from a study.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )

        # Check permissions
        current_user_role = await get_user_study_role(db, current_user, study_id)
        if not is_study_admin(current_user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only study responsible users or admins can remove responsible users"
            )

        # Check if target user exists
        target_user = await user.get(db, id=user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if assignment exists
        existing = await study_responsible_user.get_by_user_and_study(
            db, user_id=user_id, study_id=study_id
        )
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a responsible user for this study"
            )

        # Check if this is the last responsible user (don't allow removal)
        all_responsible = await study_responsible_user.get_by_study(db, study_id=study_id)
        if len(all_responsible) == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last responsible user from a study"
            )

        # Remove the assignment
        await study_responsible_user.remove(db, study_id=study_id, user_id=user_id)

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="study_responsible_users",
                record_id=existing.id,
                action="DELETE",
                user_id=current_user.id,
                changes={
                    "study_id": study_id,
                    "user_id": user_id,
                    "username": target_user.username
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_study_responsible_user_deleted(study_id, user_id, target_user.username)
        except Exception:
            pass  # WebSocket broadcast is best-effort

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove responsible user"
        )


# ========================================================================
# DEFAULT BIOSTAT ENDPOINTS
# ========================================================================

@router.get("/{study_id}/default-biostat", response_model=StudyDefaultBiostatWithUser | None)
async def get_study_default_biostat(
    *,
    db: AsyncSession = Depends(get_db),
    study_id: int,
    current_user: UserModel = Depends(get_current_user),
) -> StudyDefaultBiostatWithUser | None:
    """
    Get the default biostat reviewer for a study.

    Returns the active default biostat with user details, or None if not set.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )

        # Get the default biostat
        default = await study_default_biostat.get_by_study_with_user(db, study_id=study_id)
        if not default:
            return None

        # Build response with user details
        return StudyDefaultBiostatWithUser(
            id=default.id,
            study_id=default.study_id,
            user_id=default.user_id,
            is_active=default.is_active,
            created_at=default.created_at,
            updated_at=default.updated_at,
            user_name=default.user.full_name if default.user else None,
            user_email=default.user.email if default.user else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get default biostat: {str(e)}"
        )


@router.put("/{study_id}/default-biostat", response_model=StudyDefaultBiostatWithUser)
async def set_study_default_biostat(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    study_id: int,
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
) -> StudyDefaultBiostatWithUser:
    """
    Set the default biostat reviewer for a study.

    Only admins or study leads can set the default biostat.
    The user should have BIOSTAT role for the study.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )

        # Check permissions - admin or study lead
        user_role = await get_user_study_role(db, current_user, study_id)
        if not is_study_admin(user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators or study leads can set the default biostat"
            )

        # Check if target user exists
        target_user = await user.get(db, id=user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify user has BIOSTAT role for this study (optional validation)
        target_user_role = await user_study_role.get_user_role(db, user_id=user_id, study_id=study_id)
        if target_user_role != StudyRole.BIOSTAT:
            # Log warning but allow assignment anyway (admin may want flexibility)
            pass

        # Set the default biostat
        default = await study_default_biostat.set_default_biostat(
            db, study_id=study_id, user_id=user_id
        )

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="study_default_biostats",
                record_id=default.id,
                action="SET_DEFAULT_BIOSTAT",
                user_id=current_user.id,
                changes={
                    "study_id": study_id,
                    "user_id": user_id,
                    "username": target_user.username
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Build response with user details
        return StudyDefaultBiostatWithUser(
            id=default.id,
            study_id=default.study_id,
            user_id=default.user_id,
            is_active=default.is_active,
            created_at=default.created_at,
            updated_at=default.updated_at,
            user_name=target_user.full_name,
            user_email=target_user.email
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set default biostat: {str(e)}"
        )


@router.delete("/{study_id}/default-biostat")
async def remove_study_default_biostat(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    study_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Remove the default biostat reviewer for a study.

    Only admins or study leads can remove the default biostat.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )

        # Check permissions - admin or study lead
        user_role = await get_user_study_role(db, current_user, study_id)
        if not is_study_admin(user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators or study leads can remove the default biostat"
            )

        # Remove the default biostat
        removed = await study_default_biostat.remove_default_biostat(db, study_id=study_id)

        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active default biostat found for this study"
            )

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="study_default_biostats",
                record_id=study_id,
                action="REMOVE_DEFAULT_BIOSTAT",
                user_id=current_user.id,
                changes={"study_id": study_id},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        return {"status": "success", "message": "Default biostat removed"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove default biostat: {str(e)}"
        )


@router.get("/{study_id}/biostat-users", response_model=list)
async def get_study_biostat_users(
    *,
    db: AsyncSession = Depends(get_db),
    study_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get all users with BIOSTAT role for a study.

    Returns a list of users who can be assigned as biostat reviewers.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )

        # Get users with BIOSTAT role
        biostat_roles = await user_study_role.get_users_with_role(
            db, study_id=study_id, role=StudyRole.BIOSTAT
        )

        # Build response with user details
        result = []
        for role in biostat_roles:
            role_user = await user.get(db, id=role.user_id)
            if role_user:
                result.append({
                    "user_id": role_user.id,
                    "username": role_user.username,
                    "full_name": role_user.full_name,
                    "email": role_user.email
                })

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get biostat users: {str(e)}"
        )