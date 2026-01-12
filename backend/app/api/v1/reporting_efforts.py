"""Reporting Efforts API endpoints."""

from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import reporting_effort, study, database_release, audit_log
from app.crud.reporting_effort_usecase import reporting_effort_usecase_assignment
from app.db.session import get_db
from app.schemas.reporting_effort import (
    ReportingEffort, ReportingEffortCreate, ReportingEffortUpdate,
    ReportingEffortLockRequest, ReportingEffortLockHistoryEntry
)
from app.api.v1.websocket import broadcast_reporting_effort_created, broadcast_reporting_effort_updated, broadcast_reporting_effort_deleted
from app.core.security import get_current_user
from app.core.study_permissions import require_study_lead_access
from app.models.user import User

router = APIRouter()


def serialize_reporting_effort(effort, use_cases: List[Dict] = None) -> Dict[str, Any]:
    """Serialize reporting effort with expanded study and database release details."""
    data = {
        "id": effort.id,
        "study_id": effort.study_id,
        "database_release_id": effort.database_release_id,
        "database_release_label": effort.database_release_label,
        "created_at": effort.created_at.isoformat() if effort.created_at else None,
        "updated_at": effort.updated_at.isoformat() if effort.updated_at else None,
        "study_label": effort.study.study_label if effort.study else None,
        "database_release_label_full": effort.database_release.database_release_label if effort.database_release else None,
        "use_cases": use_cases or [],
        # Lock status fields
        "is_locked": effort.is_locked,
        "locked_at": effort.locked_at.isoformat() if effort.locked_at else None,
        "locked_by_id": effort.locked_by_id,
        "locked_by_username": effort.locked_by.username if effort.locked_by else None,
        "lock_reason": effort.lock_reason,
    }
    return data


@router.post("/", response_model=ReportingEffort, status_code=status.HTTP_201_CREATED)
async def create_reporting_effort(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    reporting_effort_in: ReportingEffortCreate,
    current_user: User = Depends(get_current_user),
) -> ReportingEffort:
    """
    Create a new reporting effort.

    Requires: Admin or Study LEAD role for the study.
    """
    try:
        # Verify that the study exists
        db_study = await study.get(db, id=reporting_effort_in.study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Study with ID {reporting_effort_in.study_id} not found"
            )

        # Check user has LEAD access to this study
        await require_study_lead_access(db, current_user, reporting_effort_in.study_id)

        # Verify that the database release exists
        db_database_release = await database_release.get(db, id=reporting_effort_in.database_release_id)
        if not db_database_release:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database release with ID {reporting_effort_in.database_release_id} not found"
            )

        # Verify that the database release belongs to the specified study
        if db_database_release.study_id != reporting_effort_in.study_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database release {reporting_effort_in.database_release_id} does not belong to study {reporting_effort_in.study_id}"
            )

        # Check if reporting effort with same label already exists for this database release
        existing_effort = await reporting_effort.get_by_release_and_label(
            db,
            database_release_id=reporting_effort_in.database_release_id,
            database_release_label=reporting_effort_in.database_release_label
        )
        if existing_effort:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reporting effort with this label already exists for this database release"
            )

        created_reporting_effort = await reporting_effort.create(db, obj_in=reporting_effort_in)

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_efforts",
                record_id=created_reporting_effort.id,
                action="CREATE",
                user_id=current_user.id,
                changes={"database_release_label": created_reporting_effort.database_release_label, "study_id": created_reporting_effort.study_id},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_reporting_effort_created(created_reporting_effort)
        except Exception:
            pass  # WebSocket broadcast is best-effort

        return created_reporting_effort
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create reporting effort"
        )


@router.get("/")
async def read_reporting_efforts(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    study_id: int = Query(None, description="Filter by study ID"),
    database_release_id: int = Query(None, description="Filter by database release ID"),
) -> List[Dict[str, Any]]:
    """
    Retrieve reporting efforts with optional filtering and pagination.
    Returns expanded data with study and database release labels.
    """
    try:
        if study_id and database_release_id:
            efforts = await reporting_effort.get_by_study_and_database_release(
                db, study_id=study_id, database_release_id=database_release_id
            )
        elif study_id:
            efforts = await reporting_effort.get_by_study(db, study_id=study_id, skip=skip, limit=limit)
        elif database_release_id:
            efforts = await reporting_effort.get_by_database_release(
                db, database_release_id=database_release_id, skip=skip, limit=limit
            )
        else:
            efforts = await reporting_effort.get_multi(db, skip=skip, limit=limit)

        # Bulk load use cases for all efforts
        effort_ids = [e.id for e in efforts]
        use_cases_by_effort = await reporting_effort_usecase_assignment.get_use_cases_for_efforts_bulk(
            db, reporting_effort_ids=effort_ids
        )

        return [serialize_reporting_effort(e, use_cases_by_effort.get(e.id, [])) for e in efforts]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reporting efforts"
        )


@router.get("/{reporting_effort_id}")
async def read_reporting_effort(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_id: int,
) -> Dict[str, Any]:
    """
    Get a specific reporting effort by ID with expanded details.
    """
    try:
        db_reporting_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_reporting_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )

        # Load use cases for this effort
        use_cases = await reporting_effort_usecase_assignment.get_use_cases_for_effort(
            db, reporting_effort_id=reporting_effort_id
        )
        use_case_dicts = [{'id': uc.id, 'name': uc.name, 'color': uc.color} for uc in use_cases]

        return serialize_reporting_effort(db_reporting_effort, use_case_dicts)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reporting effort"
        )


@router.put("/{reporting_effort_id}", response_model=ReportingEffort)
async def update_reporting_effort(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    reporting_effort_id: int,
    reporting_effort_in: ReportingEffortUpdate,
    current_user: User = Depends(get_current_user),
) -> ReportingEffort:
    """
    Update an existing reporting effort.

    Requires: Admin or Study LEAD role for the study.
    """
    try:
        db_reporting_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_reporting_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )

        # Capture old values for audit
        old_label = db_reporting_effort.database_release_label

        # Check user has LEAD access to this study
        await require_study_lead_access(db, current_user, db_reporting_effort.study_id)

        # Check if reporting effort is locked
        if db_reporting_effort.is_locked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update: This reporting effort is locked. Reason: {db_reporting_effort.lock_reason}. Unlock to make changes."
            )

        # Check if new label conflicts with existing reporting effort for same database release
        if reporting_effort_in.database_release_label:
            existing_effort = await reporting_effort.get_by_release_and_label(
                db,
                database_release_id=db_reporting_effort.database_release_id,
                database_release_label=reporting_effort_in.database_release_label
            )
            if existing_effort and existing_effort.id != reporting_effort_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reporting effort with this label already exists for this database release"
                )

        updated_reporting_effort = await reporting_effort.update(
            db, db_obj=db_reporting_effort, obj_in=reporting_effort_in
        )

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_efforts",
                record_id=updated_reporting_effort.id,
                action="UPDATE",
                user_id=current_user.id,
                changes={"old": {"database_release_label": old_label}, "new": {"database_release_label": updated_reporting_effort.database_release_label}},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_reporting_effort_updated(updated_reporting_effort)
        except Exception:
            pass  # WebSocket broadcast is best-effort

        return updated_reporting_effort
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reporting effort"
        )


@router.delete("/{reporting_effort_id}", response_model=ReportingEffort)
async def delete_reporting_effort(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    reporting_effort_id: int,
    current_user: User = Depends(get_current_user),
) -> ReportingEffort:
    """
    Delete a reporting effort.

    Requires: Admin or Study LEAD role for the study.
    Cannot delete if reporting effort has associated items.
    """
    try:
        db_reporting_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_reporting_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )

        # Check user has LEAD access to this study
        await require_study_lead_access(db, current_user, db_reporting_effort.study_id)

        # Check if reporting effort is locked
        if db_reporting_effort.is_locked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete: This reporting effort is locked. Reason: {db_reporting_effort.lock_reason}. Unlock to make changes."
            )

        # Check for associated items before deletion
        items_count = await reporting_effort.get_items_count(db, id=reporting_effort_id)
        if items_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete reporting effort: {items_count} associated item(s) exist. Delete them first."
            )

        # Capture values for audit before deletion
        deleted_label = db_reporting_effort.database_release_label
        deleted_study_id = db_reporting_effort.study_id

        deleted_reporting_effort = await reporting_effort.delete(db, id=reporting_effort_id)

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_efforts",
                record_id=reporting_effort_id,
                action="DELETE",
                user_id=current_user.id,
                changes={"deleted": {"database_release_label": deleted_label, "study_id": deleted_study_id}},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_reporting_effort_deleted(reporting_effort_id)
        except Exception:
            pass  # WebSocket broadcast is best-effort

        return deleted_reporting_effort
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete reporting effort"
        )


# ==================== Lock/Unlock Endpoints ====================


@router.post("/{reporting_effort_id}/lock")
async def lock_reporting_effort_endpoint(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    reporting_effort_id: int,
    lock_request: ReportingEffortLockRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Lock a reporting effort to prevent modifications.

    Requires: Admin or Study LEAD role for the study.
    """
    try:
        db_reporting_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_reporting_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )

        # Check user has LEAD access to this study
        await require_study_lead_access(db, current_user, db_reporting_effort.study_id)

        # Check if already locked
        if db_reporting_effort.is_locked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reporting effort is already locked"
            )

        # Lock the reporting effort
        locked_effort = await reporting_effort.lock(
            db, id=reporting_effort_id, user_id=current_user.id, reason=lock_request.reason
        )

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_efforts",
                record_id=reporting_effort_id,
                action="UPDATE",
                user_id=current_user.id,
                changes={"action": "LOCK", "reason": lock_request.reason},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_reporting_effort_updated(locked_effort)
        except Exception:
            pass  # WebSocket broadcast is best-effort

        # Get use cases for response
        use_cases = await reporting_effort_usecase_assignment.get_use_cases_for_effort(
            db, reporting_effort_id=reporting_effort_id
        )
        use_case_dicts = [{'id': uc.id, 'name': uc.name, 'color': uc.color} for uc in use_cases]

        return serialize_reporting_effort(locked_effort, use_case_dicts)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to lock reporting effort"
        )


@router.post("/{reporting_effort_id}/unlock")
async def unlock_reporting_effort_endpoint(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    reporting_effort_id: int,
    lock_request: ReportingEffortLockRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Unlock a reporting effort to allow modifications.

    Requires: Admin or Study LEAD role for the study.
    """
    try:
        db_reporting_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_reporting_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )

        # Check user has LEAD access to this study
        await require_study_lead_access(db, current_user, db_reporting_effort.study_id)

        # Check if not locked
        if not db_reporting_effort.is_locked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reporting effort is not locked"
            )

        # Unlock the reporting effort
        unlocked_effort = await reporting_effort.unlock(
            db, id=reporting_effort_id, user_id=current_user.id, reason=lock_request.reason
        )

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_efforts",
                record_id=reporting_effort_id,
                action="UPDATE",
                user_id=current_user.id,
                changes={"action": "UNLOCK", "reason": lock_request.reason},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_reporting_effort_updated(unlocked_effort)
        except Exception:
            pass  # WebSocket broadcast is best-effort

        # Get use cases for response
        use_cases = await reporting_effort_usecase_assignment.get_use_cases_for_effort(
            db, reporting_effort_id=reporting_effort_id
        )
        use_case_dicts = [{'id': uc.id, 'name': uc.name, 'color': uc.color} for uc in use_cases]

        return serialize_reporting_effort(unlocked_effort, use_case_dicts)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlock reporting effort"
        )


@router.get("/{reporting_effort_id}/lock-history", response_model=List[ReportingEffortLockHistoryEntry])
async def get_lock_history(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_id: int,
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Get the lock/unlock history for a reporting effort.

    Requires: Authenticated user.
    """
    try:
        db_reporting_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_reporting_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )

        history = await reporting_effort.get_lock_history(db, id=reporting_effort_id)

        return [
            {
                "id": entry.id,
                "action": entry.action.value,
                "reason": entry.reason,
                "performed_by_id": entry.performed_by_id,
                "performed_by_username": entry.performed_by.username if entry.performed_by else "Unknown",
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
            }
            for entry in history
        ]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve lock history"
        )