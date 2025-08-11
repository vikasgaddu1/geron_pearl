"""Reporting Efforts API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import reporting_effort, study, database_release
from app.db.session import get_db
from app.schemas.reporting_effort import ReportingEffort, ReportingEffortCreate, ReportingEffortUpdate
from app.api.v1.websocket import broadcast_reporting_effort_created, broadcast_reporting_effort_updated, broadcast_reporting_effort_deleted

router = APIRouter()


@router.post("/", response_model=ReportingEffort, status_code=status.HTTP_201_CREATED)
async def create_reporting_effort(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_in: ReportingEffortCreate,
) -> ReportingEffort:
    """
    Create a new reporting effort.
    """
    try:
        # Verify that the study exists
        db_study = await study.get(db, id=reporting_effort_in.study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Study with ID {reporting_effort_in.study_id} not found"
            )

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
        print(f"✅ Reporting effort created successfully: {created_reporting_effort.database_release_label} (ID: {created_reporting_effort.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"🚀 About to broadcast reporting_effort_created...")
            await broadcast_reporting_effort_created(created_reporting_effort)
            print(f"✅ Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return created_reporting_effort
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create reporting effort"
        )


@router.get("/", response_model=List[ReportingEffort])
async def read_reporting_efforts(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    study_id: int = Query(None, description="Filter by study ID"),
    database_release_id: int = Query(None, description="Filter by database release ID"),
) -> List[ReportingEffort]:
    """
    Retrieve reporting efforts with optional filtering and pagination.
    """
    try:
        if study_id and database_release_id:
            return await reporting_effort.get_by_study_and_database_release(
                db, study_id=study_id, database_release_id=database_release_id
            )
        elif study_id:
            return await reporting_effort.get_by_study(db, study_id=study_id, skip=skip, limit=limit)
        elif database_release_id:
            return await reporting_effort.get_by_database_release(
                db, database_release_id=database_release_id, skip=skip, limit=limit
            )
        else:
            return await reporting_effort.get_multi(db, skip=skip, limit=limit)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reporting efforts"
        )


@router.get("/{reporting_effort_id}", response_model=ReportingEffort)
async def read_reporting_effort(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_id: int,
) -> ReportingEffort:
    """
    Get a specific reporting effort by ID.
    """
    try:
        db_reporting_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_reporting_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )
        return db_reporting_effort
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
    reporting_effort_id: int,
    reporting_effort_in: ReportingEffortUpdate,
) -> ReportingEffort:
    """
    Update an existing reporting effort.
    """
    try:
        db_reporting_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_reporting_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
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
        print(f"✅ Reporting effort updated successfully: {updated_reporting_effort.database_release_label} (ID: {updated_reporting_effort.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"📝 About to broadcast reporting_effort_updated...")
            await broadcast_reporting_effort_updated(updated_reporting_effort)
            print(f"✅ Update broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
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
    reporting_effort_id: int,
) -> ReportingEffort:
    """
    Delete a reporting effort.
    """
    try:
        db_reporting_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_reporting_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )
        
        deleted_reporting_effort = await reporting_effort.delete(db, id=reporting_effort_id)
        print(f"✅ Reporting effort deleted successfully: {deleted_reporting_effort.database_release_label} (ID: {deleted_reporting_effort.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            await broadcast_reporting_effort_deleted(reporting_effort_id)
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"WebSocket broadcast error: {ws_error}")
        
        return deleted_reporting_effort
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting reporting effort: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete reporting effort"
        )