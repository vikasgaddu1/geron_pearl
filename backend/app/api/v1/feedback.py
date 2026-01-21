"""Feedback API endpoints for tenant users to submit feature requests and bug reports."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.crud.feature_request import feature_request
from app.schemas.feature_request import (
    FeatureRequest,
    FeatureRequestCreate,
    FeatureRequestInDB
)

router = APIRouter()


@router.post("/", response_model=FeatureRequest, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_in: FeatureRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FeatureRequest:
    """
    Submit a new feature request or bug report.

    - **category**: "bug" or "feature"
    - **title**: Short title (max 200 characters)
    - **description**: Detailed description
    """
    result = await feature_request.create_request(
        db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        obj_in=feedback_in
    )
    return result


@router.get("/", response_model=List[FeatureRequest])
async def get_my_feedback(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
) -> List[FeatureRequest]:
    """
    Get all feedback submitted by the current user.

    Returns feature requests/bug reports sorted by most recent first.
    Users can see the status and any admin responses to their submissions.
    """
    return await feature_request.get_user_requests(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )


@router.get("/{feedback_id}", response_model=FeatureRequest)
async def get_feedback_detail(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FeatureRequest:
    """
    Get detail of a specific feedback submission.

    Users can only view their own submissions.
    """
    result = await feature_request.get(db, id=feedback_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )

    # Users can only view their own feedback
    if result.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return result
