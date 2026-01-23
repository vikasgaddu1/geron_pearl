"""Reporting Efforts API endpoints."""

from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.crud import reporting_effort, study, database_release, audit_log, user as user_crud
from app.crud.reporting_effort_usecase import reporting_effort_usecase_assignment
from app.crud.reporting_effort_item_tracker import reporting_effort_item_tracker
from app.db.session import get_db
from app.schemas.reporting_effort import (
    ReportingEffort, ReportingEffortCreate, ReportingEffortUpdate,
    ReportingEffortLockRequest, ReportingEffortLockHistoryEntry,
    ReportingEffortSignRequest, ReportingEffortSignatureHistoryEntry,
    SignatureReadinessResponse, SignatureVerificationResponse
)
from app.api.v1.websocket import broadcast_reporting_effort_created, broadcast_reporting_effort_updated, broadcast_reporting_effort_deleted
from app.core.security import get_current_user
from app.core.study_permissions import require_study_lead_access
from app.core.signature_security import generate_signature_hash
from app.crud.study_responsible_user import study_responsible_user
from app.models.user import User
from app.models.tenant import Tenant

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
        # Signature status fields
        "is_signed": effort.is_signed,
        "signed_at": effort.signed_at.isoformat() if effort.signed_at else None,
        "signed_by_id": effort.signed_by_id,
        "signed_by_username": effort.signed_by.username if effort.signed_by else None,
        "signature_reason": effort.signature_reason,
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
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Retrieve reporting efforts with optional filtering and pagination.
    Requires authentication.
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
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get a specific reporting effort by ID with expanded details.
    Requires authentication.
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

        # Check if reporting effort is signed - signed REs cannot be modified
        if db_reporting_effort.is_signed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update: This reporting effort has been electronically signed and is permanently protected"
            )

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

        # Check if reporting effort is signed - signed REs cannot be deleted
        if db_reporting_effort.is_signed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete: This reporting effort has been electronically signed and is permanently protected"
            )

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

        # Check if signed - cannot unlock signed efforts
        if db_reporting_effort.is_signed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot unlock: This reporting effort has been electronically signed and is permanently locked"
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


# ==================== Electronic Signature Endpoints ====================


@router.get("/{reporting_effort_id}/signature-readiness", response_model=SignatureReadinessResponse)
async def check_signature_readiness(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_id: int,
    current_user: User = Depends(get_current_user),
) -> SignatureReadinessResponse:
    """
    Check if a reporting effort can be signed and what preconditions are met.

    Returns information about:
    - Whether the effort is already signed
    - Whether the user has TOTP setup completed
    - Whether the user is responsible (admin or study LEAD)
    - Whether all items are in production
    - List of blockers if signing is not possible
    """
    try:
        db_reporting_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_reporting_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )

        blockers = []

        # Check if already signed
        is_signed = db_reporting_effort.is_signed
        signed_by_username = None
        signed_at = None
        if is_signed:
            blockers.append("Reporting effort is already signed")
            signed_by_username = db_reporting_effort.signed_by.username if db_reporting_effort.signed_by else None
            signed_at = db_reporting_effort.signed_at

        # Check TOTP setup status
        signature_status = await user_crud.get_signature_status(db, user_id=current_user.id)
        has_totp_setup = signature_status["is_setup_completed"]
        is_locked_out = signature_status["is_locked_out"]
        lockout_remaining_minutes = signature_status["lockout_remaining_minutes"]

        if not has_totp_setup:
            blockers.append("Signature authentication not set up. Go to Settings to set up.")
        if is_locked_out:
            blockers.append(f"Account locked due to failed attempts. Try again in {lockout_remaining_minutes} minutes.")

        # Check if user is responsible (admin or study LEAD)
        is_responsible = current_user.is_admin or await study_responsible_user.is_responsible_for_study(
            db, user_id=current_user.id, study_id=db_reporting_effort.study_id
        )
        if not is_responsible:
            blockers.append("Only admin or study LEAD can sign reporting efforts")

        # Check items in production
        all_in_prod, total_items, items_in_prod = await reporting_effort_item_tracker.are_all_items_in_production(
            db, reporting_effort_id=reporting_effort_id
        )
        if not all_in_prod and total_items > 0:
            blockers.append(f"Not all items in production: {items_in_prod}/{total_items} items are in production")
        if total_items == 0:
            blockers.append("No items in reporting effort - cannot sign an empty effort")

        # Can sign if no blockers
        can_sign = len(blockers) == 0

        return SignatureReadinessResponse(
            can_sign=can_sign,
            is_signed=is_signed,
            has_totp_setup=has_totp_setup,
            is_responsible=is_responsible,
            all_items_in_production=all_in_prod,
            total_items=total_items,
            items_in_production=items_in_prod,
            is_locked_out=is_locked_out,
            lockout_remaining_minutes=lockout_remaining_minutes,
            blockers=blockers,
            signed_by_username=signed_by_username,
            signed_at=signed_at
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check signature readiness"
        )


@router.post("/{reporting_effort_id}/sign")
async def sign_reporting_effort_endpoint(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    reporting_effort_id: int,
    sign_request: ReportingEffortSignRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Electronically sign a reporting effort.

    This action is PERMANENT and cannot be reversed.

    Requirements:
    - User must be admin or study LEAD
    - User must have signature TOTP set up
    - All items must have in_production_flag = true
    - Effort must not be already signed

    The effort will be auto-locked after signing.
    """
    try:
        db_reporting_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_reporting_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )

        # Check if already signed
        if db_reporting_effort.is_signed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reporting effort is already signed"
            )

        # Check user is responsible (admin or study LEAD)
        is_responsible = current_user.is_admin or await study_responsible_user.is_responsible_for_study(
            db, user_id=current_user.id, study_id=db_reporting_effort.study_id
        )
        if not is_responsible:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin or study LEAD can sign reporting efforts"
            )

        # Verify TOTP token
        verification_result = await user_crud.verify_signature_token(
            db, user_id=current_user.id, totp_code=sign_request.totp_token
        )

        if not verification_result["success"]:
            if verification_result.get("is_locked"):
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Account locked due to too many failed attempts. Try again in {verification_result.get('lockout_minutes', 15)} minutes."
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid TOTP code. {verification_result.get('remaining_attempts', 0)} attempts remaining before lockout."
            )

        # Check all items are in production
        all_in_prod, total_items, items_in_prod = await reporting_effort_item_tracker.are_all_items_in_production(
            db, reporting_effort_id=reporting_effort_id
        )
        if total_items == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot sign: No items in reporting effort"
            )
        if not all_in_prod:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot sign: {total_items - items_in_prod} items are not in production"
            )

        # Get tenant settings to determine auto-lock behavior
        auto_lock = True  # Default to auto-lock
        try:
            tenant_result = await db.execute(
                select(Tenant).options(selectinload(Tenant.settings)).where(Tenant.id == current_user.tenant_id)
            )
            tenant = tenant_result.scalar_one_or_none()
            if tenant and tenant.settings:
                auto_lock = tenant.settings.signature_locks_effort
        except Exception:
            pass  # Default to auto-lock if settings can't be loaded

        # Get items snapshot for hash
        items_snapshot = await reporting_effort_item_tracker.get_items_snapshot(
            db, reporting_effort_id=reporting_effort_id
        )

        # Get client info for audit
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Sign the reporting effort
        signed_effort = await reporting_effort.sign(
            db,
            id=reporting_effort_id,
            user_id=current_user.id,
            username=current_user.username,
            reason=sign_request.reason,
            items_snapshot=items_snapshot,
            items_count=total_items,
            ip_address=ip_address,
            user_agent=user_agent,
            auto_lock=auto_lock
        )

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_efforts",
                record_id=reporting_effort_id,
                action="UPDATE",
                user_id=current_user.id,
                changes={"action": "SIGN", "reason": sign_request.reason, "items_count": total_items},
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_reporting_effort_updated(signed_effort)
        except Exception:
            pass  # WebSocket broadcast is best-effort

        # Get use cases for response
        use_cases = await reporting_effort_usecase_assignment.get_use_cases_for_effort(
            db, reporting_effort_id=reporting_effort_id
        )
        use_case_dicts = [{'id': uc.id, 'name': uc.name, 'color': uc.color} for uc in use_cases]

        return serialize_reporting_effort(signed_effort, use_case_dicts)
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
            detail="Failed to sign reporting effort"
        )


@router.get("/{reporting_effort_id}/signature-history", response_model=List[ReportingEffortSignatureHistoryEntry])
async def get_signature_history(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_id: int,
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Get the signature history for a reporting effort.

    Requires: Authenticated user.
    """
    try:
        db_reporting_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_reporting_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )

        history = await reporting_effort.get_signature_history(db, id=reporting_effort_id)

        return [
            {
                "id": entry.id,
                "signed_by_id": entry.signed_by_id,
                "signed_by_username": entry.signed_by_username,
                "signature_hash": entry.signature_hash,
                "reason": entry.reason,
                "items_count": entry.items_count,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "ip_address": entry.ip_address,
            }
            for entry in history
        ]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve signature history"
        )


@router.get("/{reporting_effort_id}/verify-signature", response_model=SignatureVerificationResponse)
async def verify_signature(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_id: int,
    current_user: User = Depends(get_current_user),
) -> SignatureVerificationResponse:
    """
    Verify the integrity of a signed reporting effort.

    Checks if:
    - The signature hash is valid
    - The current items match the items at signing time
    """
    try:
        db_reporting_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_reporting_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )

        if not db_reporting_effort.is_signed:
            return SignatureVerificationResponse(
                is_valid=False,
                signed_at=None,
                signed_by_username=None,
                items_match=False,
                items_at_signing=0,
                items_current=0
            )

        # Get the signature history to get the items snapshot
        history = await reporting_effort.get_signature_history(db, id=reporting_effort_id)
        if not history:
            return SignatureVerificationResponse(
                is_valid=False,
                signed_at=db_reporting_effort.signed_at,
                signed_by_username=db_reporting_effort.signed_by.username if db_reporting_effort.signed_by else None,
                items_match=False,
                items_at_signing=0,
                items_current=0
            )

        # Get the latest signature entry
        latest_signature = history[0]

        # Regenerate hash and compare
        current_snapshot = await reporting_effort_item_tracker.get_items_snapshot(
            db, reporting_effort_id=reporting_effort_id
        )
        expected_hash = generate_signature_hash(
            effort_id=reporting_effort_id,
            user_id=db_reporting_effort.signed_by_id,
            timestamp=db_reporting_effort.signed_at,
            items_snapshot=latest_signature.items_snapshot
        )

        is_valid = db_reporting_effort.signature_hash == expected_hash

        # Check if items match
        items_match = current_snapshot == latest_signature.items_snapshot

        # Get current item count
        _, items_current, _ = await reporting_effort_item_tracker.are_all_items_in_production(
            db, reporting_effort_id=reporting_effort_id
        )

        return SignatureVerificationResponse(
            is_valid=is_valid,
            signed_at=db_reporting_effort.signed_at,
            signed_by_username=db_reporting_effort.signed_by.username if db_reporting_effort.signed_by else None,
            items_match=items_match,
            items_at_signing=latest_signature.items_count,
            items_current=items_current
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify signature"
        )