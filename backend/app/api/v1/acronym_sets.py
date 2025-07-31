"""AcronymSet API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import acronym_set, acronym_set_member
from app.db.session import get_db
from app.schemas.acronym_set import AcronymSet, AcronymSetCreate, AcronymSetUpdate, AcronymSetWithMembers
from app.api.v1.websocket import broadcast_acronym_set_created, broadcast_acronym_set_updated, broadcast_acronym_set_deleted

router = APIRouter()


@router.post("/", response_model=AcronymSet, status_code=status.HTTP_201_CREATED)
async def create_acronym_set(
    *,
    db: AsyncSession = Depends(get_db),
    acronym_set_in: AcronymSetCreate,
) -> AcronymSet:
    """
    Create a new acronym set.
    """
    try:
        # Check if acronym set with same name already exists
        existing_set = await acronym_set.get_by_name(db, name=acronym_set_in.name)
        if existing_set:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Acronym set with name '{acronym_set_in.name}' already exists"
            )
        
        created_set = await acronym_set.create(db, obj_in=acronym_set_in)
        print(f"✅ AcronymSet created successfully: {created_set.name} (ID: {created_set.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"🚀 About to broadcast acronym_set_created...")
            await broadcast_acronym_set_created(created_set)
            print(f"✅ Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return created_set
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        print(f"❌ Error creating acronym set: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create acronym set"
        )


@router.get("/", response_model=List[AcronymSet])
async def read_acronym_sets(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
) -> List[AcronymSet]:
    """
    Retrieve acronym sets with pagination.
    """
    try:
        acronym_sets = await acronym_set.get_multi(db, skip=skip, limit=limit)
        print(f"📋 Retrieved {len(acronym_sets)} acronym sets")
        return acronym_sets
    except Exception as e:
        print(f"❌ Error retrieving acronym sets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve acronym sets"
        )


@router.get("/search", response_model=List[AcronymSet])
async def search_acronym_sets(
    *,
    db: AsyncSession = Depends(get_db),
    q: str = Query(..., min_length=1, description="Search term for name or description"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
) -> List[AcronymSet]:
    """
    Search acronym sets by name or description content.
    """
    try:
        acronym_sets = await acronym_set.search(db, search_term=q, skip=skip, limit=limit)
        print(f"🔍 Found {len(acronym_sets)} acronym sets matching '{q}'")
        return acronym_sets
    except Exception as e:
        print(f"❌ Error searching acronym sets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search acronym sets"
        )


@router.get("/{acronym_set_id}", response_model=AcronymSet)
async def read_acronym_set(
    *,
    db: AsyncSession = Depends(get_db),
    acronym_set_id: int,
) -> AcronymSet:
    """
    Get a specific acronym set by ID.
    """
    try:
        db_acronym_set = await acronym_set.get(db, id=acronym_set_id)
        if not db_acronym_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acronym set not found"
            )
        
        print(f"📄 Retrieved acronym set: {db_acronym_set.name}")
        return db_acronym_set
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving acronym set {acronym_set_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve acronym set"
        )


@router.get("/{acronym_set_id}/with-members", response_model=AcronymSetWithMembers)
async def read_acronym_set_with_members(
    *,
    db: AsyncSession = Depends(get_db),
    acronym_set_id: int,
) -> AcronymSetWithMembers:
    """
    Get a specific acronym set by ID with all its member acronyms.
    """
    try:
        db_acronym_set = await acronym_set.get_with_members(db, id=acronym_set_id)
        if not db_acronym_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acronym set not found"
            )
        
        print(f"📄 Retrieved acronym set with members: {db_acronym_set.name} ({len(db_acronym_set.acronym_set_members)} members)")
        return db_acronym_set
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving acronym set with members {acronym_set_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve acronym set with members"
        )


@router.put("/{acronym_set_id}", response_model=AcronymSet)
async def update_acronym_set(
    *,
    db: AsyncSession = Depends(get_db),
    acronym_set_id: int,
    acronym_set_in: AcronymSetUpdate,
) -> AcronymSet:
    """
    Update an acronym set.
    """
    try:
        db_acronym_set = await acronym_set.get(db, id=acronym_set_id)
        if not db_acronym_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acronym set not found"
            )
        
        # Check if new name conflicts with existing acronym set
        if acronym_set_in.name and acronym_set_in.name != db_acronym_set.name:
            existing_set = await acronym_set.get_by_name(db, name=acronym_set_in.name)
            if existing_set and existing_set.id != acronym_set_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Acronym set with name '{acronym_set_in.name}' already exists"
                )
        
        updated_set = await acronym_set.update(db, db_obj=db_acronym_set, obj_in=acronym_set_in)
        print(f"✏️ AcronymSet updated successfully: {updated_set.name} (ID: {updated_set.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"🚀 About to broadcast acronym_set_updated...")
            await broadcast_acronym_set_updated(updated_set)
            print(f"✅ Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return updated_set
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating acronym set {acronym_set_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update acronym set"
        )


@router.delete("/{acronym_set_id}", response_model=AcronymSet)
async def delete_acronym_set(
    *,
    db: AsyncSession = Depends(get_db),
    acronym_set_id: int,
) -> AcronymSet:
    """
    Delete an acronym set.
    """
    try:
        db_acronym_set = await acronym_set.get(db, id=acronym_set_id)
        if not db_acronym_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acronym set not found"
            )
        
        # Check for associated members before deletion
        associated_members = await acronym_set_member.get_by_set_id(db, acronym_set_id=acronym_set_id)
        if associated_members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete acronym set '{db_acronym_set.name}': {len(associated_members)} associated member(s) exist. Please remove all members first."
            )
        
        deleted_set = await acronym_set.delete(db, id=acronym_set_id)
        print(f"🗑️ AcronymSet deleted successfully: {deleted_set.name} (ID: {acronym_set_id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"🚀 About to broadcast acronym_set_deleted...")
            await broadcast_acronym_set_deleted(deleted_set)
            print(f"✅ Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return deleted_set
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting acronym set {acronym_set_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete acronym set"
        )