"""Implementation Guide Version API endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import ig_version
from app.db.session import get_db
from app.schemas.ig_version import IGVersion, IGVersionCreate, IGVersionUpdate
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[IGVersion])
async def get_ig_versions(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    standard_type: Optional[str] = Query(None, description="Filter by standard type: SDTM or ADaM"),
    active_only: bool = Query(False, description="Only return active versions"),
) -> List[IGVersion]:
    """
    Get all Implementation Guide versions.
    
    Optionally filter by standard type (SDTM/ADaM) and active status.
    """
    return await ig_version.get_all(
        db, 
        standard_type=standard_type, 
        active_only=active_only
    )


@router.get("/{version_id}", response_model=IGVersion)
async def get_ig_version(
    *,
    db: AsyncSession = Depends(get_db),
    version_id: int,
    current_user: User = Depends(get_current_user),
) -> IGVersion:
    """
    Get a specific Implementation Guide version by ID.
    """
    db_version = await ig_version.get(db, id=version_id)
    if not db_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IG version with ID {version_id} not found"
        )
    return db_version


@router.post("/", response_model=IGVersion, status_code=status.HTTP_201_CREATED)
async def create_ig_version(
    *,
    db: AsyncSession = Depends(get_db),
    version_in: IGVersionCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
) -> IGVersion:
    """
    Create a new Implementation Guide version (Admin only).
    """
    # Check if version already exists for this standard type
    existing = await ig_version.get_by_standard_and_version(
        db, 
        standard_type=version_in.standard_type, 
        version=version_in.version
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Version {version_in.version} already exists for {version_in.standard_type}"
        )
    
    return await ig_version.create(db, obj_in=version_in)


@router.put("/{version_id}", response_model=IGVersion)
async def update_ig_version(
    *,
    db: AsyncSession = Depends(get_db),
    version_id: int,
    version_in: IGVersionUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
) -> IGVersion:
    """
    Update an Implementation Guide version (Admin only).
    """
    db_version = await ig_version.get(db, id=version_id)
    if not db_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IG version with ID {version_id} not found"
        )
    
    # If updating standard_type or version, check for duplicates
    new_type = version_in.standard_type or db_version.standard_type
    new_version = version_in.version or db_version.version
    
    if version_in.standard_type or version_in.version:
        existing = await ig_version.get_by_standard_and_version(
            db, 
            standard_type=new_type, 
            version=new_version
        )
        if existing and existing.id != version_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Version {new_version} already exists for {new_type}"
            )
    
    return await ig_version.update(db, db_obj=db_version, obj_in=version_in)


@router.delete("/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ig_version(
    *,
    db: AsyncSession = Depends(get_db),
    version_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
) -> None:
    """
    Delete an Implementation Guide version (Admin only).
    
    Note: Will fail if version is in use by any dataset details.
    """
    db_version = await ig_version.get(db, id=version_id)
    if not db_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IG version with ID {version_id} not found"
        )
    
    try:
        await ig_version.delete(db, id=version_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete IG version that is in use by datasets"
        )

