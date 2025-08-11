"""Database releases API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import database_release, study, reporting_effort
from app.db.session import get_db
from app.schemas.database_release import DatabaseRelease, DatabaseReleaseCreate, DatabaseReleaseUpdate
from app.api.v1.websocket import broadcast_database_release_created, broadcast_database_release_updated, broadcast_database_release_deleted

router = APIRouter()


@router.post("/", response_model=DatabaseRelease, status_code=status.HTTP_201_CREATED)
async def create_database_release(
    *,
    db: AsyncSession = Depends(get_db),
    database_release_in: DatabaseReleaseCreate,
) -> DatabaseRelease:
    """
    Create a new database release.
    """
    try:
        # Check if study exists
        db_study = await study.get(db, id=database_release_in.study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )
        
        # Check if database release with same label already exists for this study
        existing_release = await database_release.get_by_study_and_label(
            db, 
            study_id=database_release_in.study_id,
            database_release_label=database_release_in.database_release_label
        )
        if existing_release:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database release with this label already exists for this study"
            )
        
        created_release = await database_release.create(db, obj_in=database_release_in)
        print(f"✅ Database release created successfully: {created_release.database_release_label} for study {created_release.study_id} (ID: {created_release.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"🚀 About to broadcast database_release_created...")
            await broadcast_database_release_created(created_release)
            print(f"✅ Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return created_release
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create database release"
        )


@router.get("/", response_model=List[DatabaseRelease])
async def read_database_releases(
    *,
    db: AsyncSession = Depends(get_db),
    study_id: int = Query(None, description="Filter by study ID"),
    skip: int = 0,
    limit: int = 100,
) -> List[DatabaseRelease]:
    """
    Retrieve database releases with pagination.
    Optionally filter by study_id.
    """
    try:
        if study_id is not None:
            return await database_release.get_by_study(db, study_id=study_id, skip=skip, limit=limit)
        else:
            return await database_release.get_multi(db, skip=skip, limit=limit)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve database releases"
        )


@router.get("/{database_release_id}", response_model=DatabaseRelease)
async def read_database_release(
    *,
    db: AsyncSession = Depends(get_db),
    database_release_id: int,
) -> DatabaseRelease:
    """
    Get a specific database release by ID.
    """
    try:
        db_release = await database_release.get(db, id=database_release_id)
        if not db_release:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Database release not found"
            )
        return db_release
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve database release"
        )


@router.put("/{database_release_id}", response_model=DatabaseRelease)
async def update_database_release(
    *,
    db: AsyncSession = Depends(get_db),
    database_release_id: int,
    database_release_in: DatabaseReleaseUpdate,
) -> DatabaseRelease:
    """
    Update an existing database release.
    """
    try:
        db_release = await database_release.get(db, id=database_release_id)
        if not db_release:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Database release not found"
            )
        
        # Check if new label conflicts with existing database release for same study
        if database_release_in.database_release_label:
            existing_release = await database_release.get_by_study_and_label(
                db, 
                study_id=db_release.study_id,
                database_release_label=database_release_in.database_release_label
            )
            if existing_release and existing_release.id != database_release_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Database release with this label already exists for this study"
                )
        
        print(f"About to update database release ID {database_release_id} to '{database_release_in.database_release_label}'")
        updated_release = await database_release.update(db, db_obj=db_release, obj_in=database_release_in)
        print(f"✅ Database release updated successfully: {updated_release.database_release_label} (ID: {updated_release.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"📝 About to broadcast database_release_updated...")
            await broadcast_database_release_updated(updated_release)
            print(f"✅ Update broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return updated_release
    except HTTPException:
        raise


@router.delete("/{database_release_id}", response_model=DatabaseRelease)
async def delete_database_release(
    *,
    db: AsyncSession = Depends(get_db),
    database_release_id: int,
) -> DatabaseRelease:
    """
    Delete a database release.
    """
    try:
        db_release = await database_release.get(db, id=database_release_id)
        if not db_release:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Database release not found"
            )
        
        # Check for associated reporting efforts before deletion
        associated_efforts = await reporting_effort.get_by_database_release_id(db, database_release_id=database_release_id)
        if associated_efforts:
            effort_labels = [effort.database_release_label for effort in associated_efforts]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete database release '{db_release.database_release_label}': {len(associated_efforts)} associated reporting effort(s) exist: {', '.join(effort_labels)}. Please delete all associated reporting efforts first."
            )
        
        deleted_release = await database_release.delete(db, id=database_release_id)
        
        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_database_release_deleted(database_release_id)
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"WebSocket broadcast error: {ws_error}")
        
        return deleted_release
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete database release"
        )