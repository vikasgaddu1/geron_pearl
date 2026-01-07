"""Studies API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import study, user_study_role, user
from app.crud import database_release, reporting_effort
from app.db.session import get_db
from app.schemas.study import Study, StudyCreate, StudyUpdate, BulkHierarchyRow, BulkHierarchyResponse
from app.schemas.database_release import DatabaseReleaseCreate
from app.schemas.reporting_effort import ReportingEffortCreate
from app.schemas.user_study_role import (
    AssignStudyRoleRequest, UserStudyRole, UserStudyRoleUpdate,
    StudyMembersResponse, StudyMember, StudyPermissions
)
from app.models.user_study_role import StudyRole
from app.models.user import User as UserModel
from app.core.security import get_current_user
from app.core.study_permissions import get_user_study_role, is_study_admin, get_study_permissions
from app.api.v1.websocket import broadcast_study_created, broadcast_study_updated, broadcast_study_deleted

router = APIRouter()


@router.post("/", response_model=Study, status_code=status.HTTP_201_CREATED)
async def create_study(
    *,
    db: AsyncSession = Depends(get_db),
    study_in: StudyCreate,
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
        
        created_study = await study.create(db, obj_in=study_in)
        print(f"Study created successfully: {created_study.study_label} (ID: {created_study.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"About to broadcast study_created...")
            await broadcast_study_created(created_study)
            print(f"Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"WebSocket broadcast error: {ws_error}")
        
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
) -> List[Study]:
    """
    Retrieve studies with pagination.
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
) -> Study:
    """
    Get a specific study by ID.
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
    study_id: int,
    study_in: StudyUpdate,
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
        
        # Check if new label conflicts with existing study
        if study_in.study_label:
            existing_study = await study.get_by_label(db, study_label=study_in.study_label)
            if existing_study and existing_study.id != study_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Study with this label already exists"
                )
        
        updated_study = await study.update(db, db_obj=db_study, obj_in=study_in)
        print(f"Study updated successfully: {updated_study.study_label} (ID: {updated_study.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"About to broadcast study_updated...")
            await broadcast_study_updated(updated_study)
            print(f"Update broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"WebSocket broadcast error: {ws_error}")
        
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
    study_id: int,
) -> Study:
    """
    Delete a study.
    """
    try:
        db_study = await study.get(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )
        
        # Check for associated database releases before deletion
        associated_releases = await database_release.get_by_study_id(db, study_id=study_id)
        if associated_releases:
            release_labels = [release.database_release_label for release in associated_releases]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete study '{db_study.study_label}': {len(associated_releases)} associated database release(s) exist: {', '.join(release_labels)}. Please delete all associated database releases first."
            )
        
        deleted_study = await study.delete(db, id=study_id)
        print(f"Study deleted successfully: {deleted_study.study_label} (ID: {deleted_study.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_study_deleted(study_id)
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"WebSocket broadcast error: {ws_error}")
        
        return deleted_study
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting study: {e}")
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
                study_obj = await study.create(db, obj_in=StudyCreate(study_label=study_label))
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
    except Exception as e:
        print(f"Error getting study permissions: {e}")
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
    except Exception as e:
        print(f"Error getting study members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get study members"
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
    except Exception as e:
        print(f"Error assigning study member: {e}")
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
    except Exception as e:
        print(f"Error updating study member role: {e}")
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
    except Exception as e:
        print(f"Error removing study member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove study member"
        )