"""Acronym API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import acronym
from app.db.session import get_db
from app.schemas.acronym import Acronym, AcronymCreate, AcronymUpdate
from app.api.v1.websocket import broadcast_acronym_created, broadcast_acronym_updated, broadcast_acronym_deleted

router = APIRouter()


@router.post("/", response_model=Acronym, status_code=status.HTTP_201_CREATED)
async def create_acronym(
    *,
    db: AsyncSession = Depends(get_db),
    acronym_in: AcronymCreate,
) -> Acronym:
    """
    Create a new acronym.
    """
    try:
        # Check if acronym with same key already exists
        existing_acronym = await acronym.get_by_key(db, key=acronym_in.key)
        if existing_acronym:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Acronym with key '{acronym_in.key}' already exists"
            )
        
        created_acronym = await acronym.create(db, obj_in=acronym_in)
        print(f"✅ Acronym created successfully: {created_acronym.key} = {created_acronym.value} (ID: {created_acronym.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"🚀 About to broadcast acronym_created...")
            await broadcast_acronym_created(created_acronym)
            print(f"✅ Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return created_acronym
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        print(f"❌ Error creating acronym: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create acronym"
        )


@router.get("/", response_model=List[Acronym])
async def read_acronyms(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
) -> List[Acronym]:
    """
    Retrieve acronyms with pagination.
    """
    try:
        acronyms = await acronym.get_multi(db, skip=skip, limit=limit)
        print(f"📋 Retrieved {len(acronyms)} acronyms")
        return acronyms
    except Exception as e:
        print(f"❌ Error retrieving acronyms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve acronyms"
        )


@router.get("/search", response_model=List[Acronym])
async def search_acronyms(
    *,
    db: AsyncSession = Depends(get_db),
    q: str = Query(..., min_length=1, description="Search term for key or value"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
) -> List[Acronym]:
    """
    Search acronyms by key or value content.
    """
    try:
        acronyms = await acronym.search(db, search_term=q, skip=skip, limit=limit)
        print(f"🔍 Found {len(acronyms)} acronyms matching '{q}'")
        return acronyms
    except Exception as e:
        print(f"❌ Error searching acronyms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search acronyms"
        )


@router.get("/{acronym_id}", response_model=Acronym)
async def read_acronym(
    *,
    db: AsyncSession = Depends(get_db),
    acronym_id: int,
) -> Acronym:
    """
    Get a specific acronym by ID.
    """
    try:
        db_acronym = await acronym.get(db, id=acronym_id)
        if not db_acronym:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acronym not found"
            )
        
        print(f"📄 Retrieved acronym: {db_acronym.key} = {db_acronym.value}")
        return db_acronym
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving acronym {acronym_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve acronym"
        )


@router.put("/{acronym_id}", response_model=Acronym)
async def update_acronym(
    *,
    db: AsyncSession = Depends(get_db),
    acronym_id: int,
    acronym_in: AcronymUpdate,
) -> Acronym:
    """
    Update an acronym.
    """
    try:
        db_acronym = await acronym.get(db, id=acronym_id)
        if not db_acronym:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acronym not found"
            )
        
        # Check if new key conflicts with existing acronym
        if acronym_in.key and acronym_in.key != db_acronym.key:
            existing_acronym = await acronym.get_by_key(db, key=acronym_in.key)
            if existing_acronym and existing_acronym.id != acronym_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Acronym with key '{acronym_in.key}' already exists"
                )
        
        updated_acronym = await acronym.update(db, db_obj=db_acronym, obj_in=acronym_in)
        print(f"✏️ Acronym updated successfully: {updated_acronym.key} = {updated_acronym.value} (ID: {updated_acronym.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"🚀 About to broadcast acronym_updated...")
            await broadcast_acronym_updated(updated_acronym)
            print(f"✅ Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return updated_acronym
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating acronym {acronym_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update acronym"
        )


@router.delete("/{acronym_id}", response_model=Acronym)
async def delete_acronym(
    *,
    db: AsyncSession = Depends(get_db),
    acronym_id: int,
) -> Acronym:
    """
    Delete an acronym.
    """
    try:
        db_acronym = await acronym.get(db, id=acronym_id)
        if not db_acronym:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acronym not found"
            )
        
        # Note: Deletion protection for acronym sets is handled via CASCADE delete
        # The database will automatically remove entries from acronym_set_members
        
        deleted_acronym = await acronym.delete(db, id=acronym_id)
        print(f"🗑️ Acronym deleted successfully: {deleted_acronym.key} = {deleted_acronym.value} (ID: {acronym_id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"🚀 About to broadcast acronym_deleted...")
            await broadcast_acronym_deleted(deleted_acronym)
            print(f"✅ Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return deleted_acronym
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting acronym {acronym_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete acronym"
        )