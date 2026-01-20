from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app import crud, schemas
from app.crud import audit_log
from app.db.session import get_db
from app.api.v1.websocket import broadcast_user_created, broadcast_user_updated, broadcast_user_deleted
from app.core.security import require_admin
from app.core.subscription import require_active_subscription, check_user_limit
from app.models.user import User as UserModel

router = APIRouter()


@router.post("/", response_model=schemas.User)
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    user_in: schemas.UserCreate,
    current_user: UserModel = Depends(require_admin()),
    _subscription: None = Depends(require_active_subscription),
    _limit: None = Depends(check_user_limit),
) -> Any:
    """
    Create new user with email and password.
    """
    try:
        user = await crud.user.create(db, obj_in=user_in)

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="users",
                record_id=user.id,
                action="CREATE",
                user_id=current_user.id,
                changes={"username": user.username, "email": user.email, "is_admin": user.is_admin},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        await broadcast_user_created(user)
        return user
    except IntegrityError as e:
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if "already exists" in error_msg:
            if "Username" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Username '{user_in.username}' already exists"
                )
            elif "Email" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{user_in.email}' already exists"
                )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user"
        )


@router.get("/", response_model=List[schemas.User], response_model_exclude_none=False)
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(require_admin()),
) -> Any:
    """
    Retrieve users.
    """
    users = await crud.user.get_multi(db, skip=skip, limit=limit)
    return users


@router.get("/{id}", response_model=schemas.User, response_model_exclude_none=False)
async def read_user(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: UserModel = Depends(require_admin()),
) -> Any:
    """
    Get user by ID.
    """
    user = await crud.user.get(db, id=id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{id}", response_model=schemas.User, response_model_exclude_none=False)
async def update_user(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    id: int,
    user_in: schemas.UserUpdate,
    current_user: UserModel = Depends(require_admin()),
) -> Any:
    """
    Update a user.
    """
    user = await crud.user.get(db, id=id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Capture old values for audit
    old_values = {"username": user.username, "email": user.email, "is_admin": user.is_admin}

    try:
        user = await crud.user.update(db, db_obj=user, obj_in=user_in)

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="users",
                record_id=user.id,
                action="UPDATE",
                user_id=current_user.id,
                changes={"old": old_values, "new": {"username": user.username, "email": user.email, "is_admin": user.is_admin}},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        await broadcast_user_updated(user)
        return user
    except IntegrityError as e:
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if "already exists" in error_msg:
            if "Username" in error_msg:
                username = user_in.username if user_in.username else user.username
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Username '{username}' already exists"
                )
            elif "Email" in error_msg:
                email = user_in.email if user_in.email else user.email
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{email}' already exists"
                )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user"
        )


@router.delete("/{id}", response_model=schemas.User)
async def delete_user(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    id: int,
    current_user: UserModel = Depends(require_admin()),
) -> Any:
    """
    Delete a user.

    Cannot delete if:
    - User is assigned to trackers as production or QC programmer
    - User has study role assignments
    - User is the only admin
    """
    user = await crud.user.get(db, id=id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check for references before deletion
    references = await crud.user.get_usage_references(db, id=id)
    if crud.user.has_blocking_references(references):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=crud.user.format_reference_error(references)
        )

    # Capture values for audit before deletion
    deleted_username = user.username
    deleted_email = user.email

    user = await crud.user.remove(db, id=id)

    # Log audit trail
    try:
        await audit_log.log_action(
            db,
            table_name="users",
            record_id=id,
            action="DELETE",
            user_id=current_user.id,
            changes={"deleted": {"username": deleted_username, "email": deleted_email}},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        pass  # Audit logging is best-effort

    await broadcast_user_deleted(user)
    return user