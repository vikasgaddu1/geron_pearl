"""Access Request API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User as UserModel
from app.models.access_request import AccessRequestType, AccessRequestStatus
from app.models.user_study_role import StudyRole
from app.crud import access_request, study, user_study_role, study_responsible_user, notification, audit_log
from app.schemas.access_request import (
    AccessRequestCreate, AccessRequestDeny, AccessRequestWithDetails,
    AccessRequestListResponse, PendingRequestCountResponse
)
from app.api.v1.websocket import manager
from app.api.v1.notifications import broadcast_notification_count

router = APIRouter()


async def broadcast_access_request_created(request_data: dict):
    """Broadcast new access request to WebSocket."""
    try:
        message = {
            "type": "access_request_created",
            "data": request_data
        }
        await manager.broadcast_json(message)
    except Exception:
        pass  # WebSocket broadcast is best-effort


async def broadcast_access_request_resolved(request_data: dict):
    """Broadcast resolved access request to WebSocket."""
    try:
        message = {
            "type": "access_request_resolved",
            "data": request_data
        }
        await manager.broadcast_json(message)
    except Exception:
        pass  # WebSocket broadcast is best-effort


@router.post("/", response_model=AccessRequestWithDetails, status_code=status.HTTP_201_CREATED)
async def create_access_request(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    request_in: AccessRequestCreate,
    current_user: UserModel = Depends(get_current_user),
) -> AccessRequestWithDetails:
    """
    Create a new access request.

    Any authenticated user can request access to studies they don't have access to.
    """
    try:
        # Validate study exists
        db_study = await study.get(db, id=request_in.study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )

        # Global admins already have full access
        if current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Global administrators already have full access to all studies"
            )

        # Check if user already has the requested access
        if request_in.request_type == AccessRequestType.EDITOR:
            existing_role = await user_study_role.get_by_user_and_study(
                db, user_id=current_user.id, study_id=request_in.study_id
            )
            if existing_role and existing_role.role == StudyRole.EDITOR:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You already have EDITOR access to this study"
                )
        elif request_in.request_type == AccessRequestType.RESPONSIBLE_USER:
            is_responsible = await study_responsible_user.is_responsible_for_study(
                db, user_id=current_user.id, study_id=request_in.study_id
            )
            if is_responsible:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You are already a responsible user for this study"
                )

        # Check for existing pending request
        existing_request = await access_request.get_pending_request(
            db,
            requester_id=current_user.id,
            study_id=request_in.study_id,
            request_type=request_in.request_type
        )
        if existing_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have a pending request for this access type"
            )

        # Create the request
        created = await access_request.create_request(
            db,
            requester_id=current_user.id,
            study_id=request_in.study_id,
            request_type=request_in.request_type,
            request_reason=request_in.request_reason
        )

        # Get the full details for response
        created_with_details = await access_request.get_with_details(db, request_id=created.id)
        if not created_with_details:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created request"
            )

        created_details = access_request._to_details(created_with_details)

        # Notify approvers (responsible users and admins)
        approver_ids = await access_request.get_approvers_for_study(db, study_id=request_in.study_id)
        for approver_id in approver_ids:
            if approver_id != current_user.id:  # Don't notify self
                await notification.create_notification(
                    db,
                    user_id=approver_id,
                    notification_type="access_request_new",
                    title="New Access Request",
                    message=f"{current_user.username} requested {request_in.request_type.value} access to {db_study.study_label}",
                    triggered_by_user_id=current_user.id,
                    study_label=db_study.study_label
                )
                # Broadcast notification count update
                unread_count = await notification.get_unread_count(db, user_id=approver_id)
                await broadcast_notification_count(approver_id, unread_count)

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="access_requests",
                record_id=created.id,
                action="CREATE",
                user_id=current_user.id,
                changes={
                    "study_id": request_in.study_id,
                    "study_label": db_study.study_label,
                    "request_type": request_in.request_type.value,
                    "request_reason": request_in.request_reason
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Broadcast WebSocket event
        await broadcast_access_request_created(created_details.model_dump(mode='json'))

        return created_details

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create access request: {str(e)}"
        )


@router.get("/", response_model=AccessRequestListResponse)
async def list_access_requests(
    *,
    db: AsyncSession = Depends(get_db),
    view: str = Query("approver", description="View mode: 'approver' or 'requester'"),
    status_filter: Optional[str] = Query(None, description="Filter by status: PENDING, APPROVED, or DENIED"),
    skip: int = 0,
    limit: int = 50,
    current_user: UserModel = Depends(get_current_user),
) -> AccessRequestListResponse:
    """
    List access requests.

    - view='approver': Returns requests the user can approve (admins see all, responsible users see their studies)
    - view='requester': Returns requests made by the current user
    """
    try:
        # Parse status filter
        parsed_status = None
        if status_filter:
            try:
                parsed_status = AccessRequestStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}. Must be PENDING, APPROVED, or DENIED"
                )

        if view == "approver":
            requests = await access_request.get_requests_for_approver(
                db,
                user_id=current_user.id,
                is_admin=current_user.is_admin,
                status_filter=parsed_status,
                skip=skip,
                limit=limit
            )
        else:
            requests = await access_request.get_requests_by_requester(
                db,
                requester_id=current_user.id,
                status_filter=parsed_status,
                skip=skip,
                limit=limit
            )

        return AccessRequestListResponse(
            requests=requests,
            total_count=len(requests)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list access requests: {str(e)}"
        )


@router.get("/pending-count", response_model=PendingRequestCountResponse)
async def get_pending_count(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> PendingRequestCountResponse:
    """
    Get count of pending access requests the user can approve.
    """
    try:
        count = await access_request.get_pending_count_for_approver(
            db,
            user_id=current_user.id,
            is_admin=current_user.is_admin
        )
        return PendingRequestCountResponse(pending_count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending count: {str(e)}"
        )


@router.post("/{request_id}/approve", response_model=AccessRequestWithDetails)
async def approve_access_request(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    request_id: int,
    current_user: UserModel = Depends(get_current_user),
) -> AccessRequestWithDetails:
    """
    Approve an access request.

    Only study responsible users (for their studies) or global admins can approve.
    """
    try:
        # Get the request with details
        db_request = await access_request.get_with_details(db, request_id=request_id)
        if not db_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Access request not found"
            )

        if db_request.status != AccessRequestStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request has already been resolved"
            )

        # Check authorization
        if not current_user.is_admin:
            is_responsible = await study_responsible_user.is_responsible_for_study(
                db, user_id=current_user.id, study_id=db_request.study_id
            )
            if not is_responsible:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to approve this request"
                )

        # Approve the request
        approved = await access_request.approve_request(
            db, request_id=request_id, resolved_by_id=current_user.id
        )

        if not approved:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to approve request"
            )

        # Grant the requested access
        if db_request.request_type == AccessRequestType.EDITOR.value:
            await user_study_role.assign_role(
                db,
                user_id=db_request.requester_id,
                study_id=db_request.study_id,
                role=StudyRole.EDITOR
            )
        elif db_request.request_type == AccessRequestType.RESPONSIBLE_USER.value:
            await study_responsible_user.assign(
                db,
                study_id=db_request.study_id,
                user_id=db_request.requester_id,
                is_primary=False
            )

        # Get study label for notification
        study_label = db_request.study.study_label

        # Notify the requester
        await notification.create_notification(
            db,
            user_id=db_request.requester_id,
            notification_type="access_request_approved",
            title="Access Request Approved",
            message=f"Your request for {db_request.request_type} access to {study_label} was approved by {current_user.username}",
            triggered_by_user_id=current_user.id,
            study_label=study_label
        )
        unread_count = await notification.get_unread_count(db, user_id=db_request.requester_id)
        await broadcast_notification_count(db_request.requester_id, unread_count)

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="access_requests",
                record_id=request_id,
                action="UPDATE",
                user_id=current_user.id,
                changes={
                    "status": "APPROVED",
                    "resolved_by": current_user.username,
                    "access_granted": db_request.request_type
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Get updated details
        approved_with_details = await access_request.get_with_details(db, request_id=request_id)
        if not approved_with_details:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve approved request"
            )

        approved_details = access_request._to_details(approved_with_details)

        # Broadcast WebSocket event
        await broadcast_access_request_resolved(approved_details.model_dump(mode='json'))

        return approved_details

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve request: {str(e)}"
        )


@router.post("/{request_id}/deny", response_model=AccessRequestWithDetails)
async def deny_access_request(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    request_id: int,
    denial_data: AccessRequestDeny,
    current_user: UserModel = Depends(get_current_user),
) -> AccessRequestWithDetails:
    """
    Deny an access request.

    Only study responsible users (for their studies) or global admins can deny.
    """
    try:
        # Get the request with details
        db_request = await access_request.get_with_details(db, request_id=request_id)
        if not db_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Access request not found"
            )

        if db_request.status != AccessRequestStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request has already been resolved"
            )

        # Check authorization
        if not current_user.is_admin:
            is_responsible = await study_responsible_user.is_responsible_for_study(
                db, user_id=current_user.id, study_id=db_request.study_id
            )
            if not is_responsible:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to deny this request"
                )

        # Deny the request
        denied = await access_request.deny_request(
            db,
            request_id=request_id,
            resolved_by_id=current_user.id,
            denial_reason=denial_data.denial_reason
        )

        if not denied:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deny request"
            )

        # Get study label for notification
        study_label = db_request.study.study_label

        # Notify the requester
        denial_msg = f" Reason: {denial_data.denial_reason}" if denial_data.denial_reason else ""
        await notification.create_notification(
            db,
            user_id=db_request.requester_id,
            notification_type="access_request_denied",
            title="Access Request Denied",
            message=f"Your request for {db_request.request_type} access to {study_label} was denied.{denial_msg}",
            triggered_by_user_id=current_user.id,
            study_label=study_label
        )
        unread_count = await notification.get_unread_count(db, user_id=db_request.requester_id)
        await broadcast_notification_count(db_request.requester_id, unread_count)

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="access_requests",
                record_id=request_id,
                action="UPDATE",
                user_id=current_user.id,
                changes={
                    "status": "DENIED",
                    "resolved_by": current_user.username,
                    "denial_reason": denial_data.denial_reason
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        # Get updated details
        denied_with_details = await access_request.get_with_details(db, request_id=request_id)
        if not denied_with_details:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve denied request"
            )

        denied_details = access_request._to_details(denied_with_details)

        # Broadcast WebSocket event
        await broadcast_access_request_resolved(denied_details.model_dump(mode='json'))

        return denied_details

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deny request: {str(e)}"
        )
