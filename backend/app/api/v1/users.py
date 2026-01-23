from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app import crud, schemas
from app.crud import audit_log
from app.db.session import get_db
from app.api.v1.websocket import broadcast_user_created, broadcast_user_updated, broadcast_user_deleted
from app.core.security import require_admin, get_current_user
from app.core.subscription import require_active_subscription, check_user_limit
from app.core.signature_security import get_signature_uri
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
        user = await crud.user.create(db, obj_in=user_in, tenant_id=current_user.tenant_id)

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


# ==================== Electronic Signature TOTP Endpoints ====================


@router.post("/me/signature/setup", response_model=schemas.SignatureSetupResponse)
async def setup_signature_totp(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Start TOTP setup for electronic signatures.

    Returns a provisioning URI (for QR code) and 10 backup codes.
    The setup is NOT complete until verify-setup is called with a valid TOTP code.

    If already set up, this will generate a NEW secret (requiring re-verification).
    """
    result = await crud.user.setup_signature_totp(db, user_id=current_user.id)

    # Generate provisioning URI for QR code
    provisioning_uri = get_signature_uri(
        email=current_user.email or current_user.username,
        secret=result["secret"]
    )

    return schemas.SignatureSetupResponse(
        provisioning_uri=provisioning_uri,
        backup_codes=result["backup_codes"],
        message="Scan the QR code with your authenticator app, then verify with a 6-digit code"
    )


@router.post("/me/signature/verify-setup", response_model=schemas.SignatureVerifySetupResponse)
async def verify_signature_setup(
    *,
    db: AsyncSession = Depends(get_db),
    request_body: schemas.SignatureVerifySetupRequest,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Complete TOTP setup by verifying a code from the authenticator app.

    This must be called after setup to confirm the user has correctly
    configured their authenticator app.
    """
    success = await crud.user.complete_signature_setup(
        db,
        user_id=current_user.id,
        totp_code=request_body.totp_code
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code. Please check your authenticator app and try again."
        )

    return schemas.SignatureVerifySetupResponse(
        success=True,
        message="Signature authentication setup complete"
    )


@router.get("/me/signature/status", response_model=schemas.SignatureStatusResponse)
async def get_signature_status(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Get the current status of signature TOTP setup.

    Returns whether setup is complete, lockout status, and failed attempt count.
    """
    status_info = await crud.user.get_signature_status(db, user_id=current_user.id)

    return schemas.SignatureStatusResponse(
        is_setup_completed=status_info["is_setup_completed"],
        is_locked_out=status_info["is_locked_out"],
        lockout_remaining_minutes=status_info["lockout_remaining_minutes"],
        failed_attempts=status_info["failed_attempts"]
    )


@router.post("/me/signature/reset", response_model=schemas.SignatureSetupResponse)
async def reset_signature_totp(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Reset/revoke TOTP and generate a new secret.

    This invalidates the old authenticator setup and requires the user
    to set up their authenticator app again.

    Returns new provisioning URI and backup codes.
    """
    # Reset first (clears lockout and failed attempts too)
    await crud.user.reset_signature_totp(db, user_id=current_user.id)

    # Then set up fresh
    result = await crud.user.setup_signature_totp(db, user_id=current_user.id)

    # Generate provisioning URI for QR code
    provisioning_uri = get_signature_uri(
        email=current_user.email or current_user.username,
        secret=result["secret"]
    )

    return schemas.SignatureSetupResponse(
        provisioning_uri=provisioning_uri,
        backup_codes=result["backup_codes"],
        message="Previous authenticator revoked. Scan the new QR code with your authenticator app."
    )


@router.post("/me/signature/use-backup-code", response_model=schemas.SignatureUseBackupCodeResponse)
async def use_signature_backup_code(
    *,
    db: AsyncSession = Depends(get_db),
    request_body: schemas.SignatureUseBackupCodeRequest,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Use a one-time backup code for signing.

    Backup codes are used when the user doesn't have access to their
    authenticator app. Each code can only be used once.

    Returns success status and number of remaining codes.
    """
    result = await crud.user.use_backup_code(
        db,
        user_id=current_user.id,
        backup_code=request_body.backup_code
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used backup code"
        )

    return schemas.SignatureUseBackupCodeResponse(
        success=True,
        remaining_codes=result["remaining_codes"],
        message=f"Backup code accepted. {result['remaining_codes']} codes remaining."
    )