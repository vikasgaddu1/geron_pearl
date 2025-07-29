"""Studies API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import study
from app.db.session import get_db
from app.schemas.study import Study, StudyCreate, StudyUpdate
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
        
        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_study_created(created_study)
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
        
        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_study_updated(updated_study)
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
        
        deleted_study = await study.delete(db, id=study_id)
        
        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_study_deleted(study_id)
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"WebSocket broadcast error: {ws_error}")
        
        return deleted_study
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete study"
        )