"""Authentication endpoints for login, registration, password reset, and OAuth2."""

from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    generate_reset_token,
    get_reset_token_hash,
    verify_reset_token,
)
from app.core.oauth2 import oauth, get_user_info_from_token, is_provider_configured
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole, AuthProvider
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    Token,
    UserResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    RegisterRequest,
    OAuth2CallbackResponse,
)

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Local username/password login.
    
    Returns JWT access and refresh tokens.
    """
    # Find user by username
    result = await db.execute(
        select(User).where(User.username == login_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Verify password
    if not user.password_hash or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # Create tokens
    token_data = {
        "sub": str(user.id),  # JWT sub must be a string
        "username": user.username,
        "role": user.role.value,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/register", response_model=UserResponse)
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user with local authentication.
    
    Note: In production, this might be admin-only or disabled entirely.
    """
    # Check if username exists
    result = await db.execute(
        select(User).where(User.username == register_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Check if email exists
    if register_data.email:
        result = await db.execute(
            select(User).where(User.email == register_data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    # Create new user
    user = User(
        username=register_data.username,
        email=register_data.email,
        password_hash=get_password_hash(register_data.password),
        role=register_data.role or UserRole.VIEWER,
        department=register_data.department,
        auth_provider=AuthProvider.local,
        is_active=True,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token.
    """
    # Decode and validate refresh token
    payload = decode_token(refresh_data.refresh_token)
    
    # Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Create new tokens
    token_data = {
        "sub": str(user.id),  # JWT sub must be a string
        "username": user.username,
        "role": user.role.value,
    }
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout() -> Any:
    """
    Logout current user.
    
    Note: With JWT, logout is primarily handled client-side by discarding tokens.
    In a production system, you might maintain a token blacklist.
    """
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current authenticated user information."""
    return current_user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Request password reset token.
    
    Generates a reset token and sends it via email (or logs to console in dev).
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request_data.email)
    )
    user = result.scalar_one_or_none()
    
    # Always return success to prevent email enumeration
    if not user:
        return {
            "message": "If an account with that email exists, a password reset link has been sent.",
            "detail": "No user found with that email (not disclosed to user)"
        }
    
    # Only allow password reset for local auth users
    if user.auth_provider != AuthProvider.local:
        return {
            "message": "If an account with that email exists, a password reset link has been sent.",
            "detail": f"User uses {user.auth_provider.value} authentication (not disclosed to user)"
        }
    
    # Generate reset token
    reset_token = generate_reset_token()
    user.reset_token = get_reset_token_hash(reset_token)
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    
    await db.commit()
    
    # In production, send email with reset link
    # For development, just log the token
    reset_url = f"http://localhost:5173/reset-password/{reset_token}"
    
    if settings.env == "development":
        print(f"\n{'='*80}")
        print(f"PASSWORD RESET REQUEST")
        print(f"{'='*80}")
        print(f"User: {user.username} ({user.email})")
        print(f"Reset URL: {reset_url}")
        print(f"Token expires: {user.reset_token_expires}")
        print(f"{'='*80}\n")
    
    # TODO: Send email in production
    # await send_password_reset_email(user.email, reset_url)
    
    return {
        "message": "If an account with that email exists, a password reset link has been sent."
    }


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Reset password using reset token.
    """
    # Find user with matching reset token
    # We need to check all users since we only have the hashed token
    result = await db.execute(
        select(User).where(
            User.reset_token.isnot(None),
            User.reset_token_expires > datetime.utcnow()
        )
    )
    users = result.scalars().all()
    
    user = None
    for potential_user in users:
        if verify_reset_token(reset_data.token, potential_user.reset_token):
            user = potential_user
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    
    # Update password and clear reset token
    user.password_hash = get_password_hash(reset_data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    
    await db.commit()
    
    return {"message": "Password has been reset successfully"}


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Change password for authenticated user.
    """
    # Verify current password
    if not current_user.password_hash or not verify_password(
        password_data.current_password, current_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    await db.commit()
    
    return {"message": "Password changed successfully"}


@router.get("/login/{provider}")
async def oauth_login(
    provider: str,
    request: Request
) -> Any:
    """
    Initiate OAuth2 login flow for specified provider.
    
    Supported providers: google, microsoft, github
    """
    if not is_provider_configured(provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider '{provider}' is not configured"
        )
    
    client = getattr(oauth, provider)
    redirect_uri = request.url_for('oauth_callback', provider=provider)
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/callback/{provider}", response_model=OAuth2CallbackResponse)
async def oauth_callback(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Handle OAuth2 callback from provider.
    
    Creates or updates user account and returns JWT tokens.
    """
    if not is_provider_configured(provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider '{provider}' is not configured"
        )
    
    try:
        # Exchange authorization code for token
        client = getattr(oauth, provider)
        token = await client.authorize_access_token(request)
        
        # Get user info from provider
        user_info = await get_user_info_from_token(provider, token)
        
        # Find or create user
        result = await db.execute(
            select(User).where(
                User.auth_provider == AuthProvider[provider.upper()],
                User.auth_provider_id == user_info['provider_id']
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Check if email already exists with different provider
            if user_info.get('email'):
                result = await db.execute(
                    select(User).where(User.email == user_info['email'])
                )
                existing_user = result.scalar_one_or_none()
                if existing_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"An account with email {user_info['email']} already exists"
                    )
            
            # Create new user from OAuth profile
            username = user_info.get('email', '').split('@')[0] or f"{provider}_user_{user_info['provider_id']}"
            
            # Ensure unique username
            base_username = username
            counter = 1
            while True:
                result = await db.execute(
                    select(User).where(User.username == username)
                )
                if not result.scalar_one_or_none():
                    break
                username = f"{base_username}_{counter}"
                counter += 1
            
            user = User(
                username=username,
                email=user_info.get('email'),
                role=UserRole.VIEWER,  # Default role for new OAuth users
                auth_provider=AuthProvider[provider.upper()],
                auth_provider_id=user_info['provider_id'],
                is_active=True,
                last_login_at=datetime.utcnow(),
            )
            db.add(user)
        else:
            # Update existing user's last login
            user.last_login_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        # Create JWT tokens
        token_data = {
            "sub": str(user.id),  # JWT sub must be a string
            "username": user.username,
            "role": user.role.value,
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth authentication failed: {str(e)}"
        )

