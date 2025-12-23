from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app import crud, schemas
from app.db.session import get_db
from app.api.v1.websocket import broadcast_user_created, broadcast_user_updated, broadcast_user_deleted

router = APIRouter()


@router.post("/", response_model=schemas.User)
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user with email and password.
    """
    try:
        user = await crud.user.create(db, obj_in=user_in)
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
    id: int,
    user_in: schemas.UserUpdate,
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
    
    try:
        user = await crud.user.update(db, db_obj=user, obj_in=user_in)
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
    id: int,
) -> Any:
    """
    Delete a user.
    """
    user = await crud.user.get(db, id=id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = await crud.user.remove(db, id=id)
    await broadcast_user_deleted(user)
    return user