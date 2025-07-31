"""AcronymSetMember API endpoints for managing acronym set memberships."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import acronym_set_member, acronym_set, acronym
from app.db.session import get_db
from app.schemas.acronym_set_member import AcronymSetMember, AcronymSetMemberCreate, AcronymSetMemberUpdate
from app.api.v1.websocket import broadcast_acronym_set_member_created, broadcast_acronym_set_member_updated, broadcast_acronym_set_member_deleted

router = APIRouter()


@router.post("/", response_model=AcronymSetMember, status_code=status.HTTP_201_CREATED)
async def add_acronym_to_set(
    *,
    db: AsyncSession = Depends(get_db),
    member_in: AcronymSetMemberCreate,
) -> AcronymSetMember:
    """
    Add an acronym to an acronym set.
    """
    try:
        # Validate that the acronym set exists
        db_acronym_set = await acronym_set.get(db, id=member_in.acronym_set_id)
        if not db_acronym_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acronym set not found"
            )
        
        # Validate that the acronym exists
        db_acronym = await acronym.get(db, id=member_in.acronym_id)
        if not db_acronym:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acronym not found"
            )
        
        # Check if this membership already exists
        existing_member = await acronym_set_member.get_by_set_and_acronym(
            db, 
            acronym_set_id=member_in.acronym_set_id, 
            acronym_id=member_in.acronym_id
        )
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Acronym '{db_acronym.key}' is already a member of set '{db_acronym_set.name}'"
            )
        
        created_member = await acronym_set_member.create(db, obj_in=member_in)
        print(f"✅ AcronymSetMember created successfully: Added '{db_acronym.key}' to '{db_acronym_set.name}' (ID: {created_member.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"🚀 About to broadcast acronym_set_member_created...")
            await broadcast_acronym_set_member_created(created_member)
            print(f"✅ Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return created_member
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        print(f"❌ Error creating acronym set member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add acronym to set"
        )


@router.get("/", response_model=List[AcronymSetMember])
async def read_acronym_set_members(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    acronym_set_id: int = Query(None, description="Filter by acronym set ID"),
    acronym_id: int = Query(None, description="Filter by acronym ID")
) -> List[AcronymSetMember]:
    """
    Retrieve acronym set members with optional filtering.
    """
    try:
        if acronym_set_id:
            members = await acronym_set_member.get_by_set_id(db, acronym_set_id=acronym_set_id)
            # Apply manual pagination since get_by_set_id doesn't support it
            total_members = len(members)
            members = members[skip:skip + limit] if skip < total_members else []
        elif acronym_id:
            members = await acronym_set_member.get_by_acronym_id(db, acronym_id=acronym_id)
            # Apply manual pagination
            total_members = len(members)
            members = members[skip:skip + limit] if skip < total_members else []
        else:
            members = await acronym_set_member.get_multi(db, skip=skip, limit=limit)
        
        print(f"📋 Retrieved {len(members)} acronym set members")
        return members
    except Exception as e:
        print(f"❌ Error retrieving acronym set members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve acronym set members"
        )


@router.get("/{member_id}", response_model=AcronymSetMember)
async def read_acronym_set_member(
    *,
    db: AsyncSession = Depends(get_db),
    member_id: int,
) -> AcronymSetMember:
    """
    Get a specific acronym set member by ID.
    """
    try:
        db_member = await acronym_set_member.get(db, id=member_id)
        if not db_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acronym set member not found"
            )
        
        print(f"📄 Retrieved acronym set member: ID {db_member.id}")
        return db_member
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving acronym set member {member_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve acronym set member"
        )


@router.put("/{member_id}", response_model=AcronymSetMember)
async def update_acronym_set_member(
    *,
    db: AsyncSession = Depends(get_db),
    member_id: int,
    member_in: AcronymSetMemberUpdate,
) -> AcronymSetMember:
    """
    Update an acronym set member (primarily for updating sort_order).
    """
    try:
        db_member = await acronym_set_member.get(db, id=member_id)
        if not db_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acronym set member not found"
            )
        
        updated_member = await acronym_set_member.update(db, db_obj=db_member, obj_in=member_in)
        print(f"✏️ AcronymSetMember updated successfully: ID {updated_member.id}")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"🚀 About to broadcast acronym_set_member_updated...")
            await broadcast_acronym_set_member_updated(updated_member)
            print(f"✅ Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return updated_member
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating acronym set member {member_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update acronym set member"
        )


@router.delete("/{member_id}", response_model=AcronymSetMember)
async def remove_acronym_from_set(
    *,
    db: AsyncSession = Depends(get_db),
    member_id: int,
) -> AcronymSetMember:
    """
    Remove an acronym from an acronym set.
    """
    try:
        db_member = await acronym_set_member.get(db, id=member_id)
        if not db_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acronym set member not found"
            )
        
        deleted_member = await acronym_set_member.delete(db, id=member_id)
        print(f"🗑️ AcronymSetMember deleted successfully: ID {member_id}")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"🚀 About to broadcast acronym_set_member_deleted...")
            await broadcast_acronym_set_member_deleted(deleted_member)
            print(f"✅ Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return deleted_member
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting acronym set member {member_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove acronym from set"
        )


@router.post("/bulk-add", response_model=List[AcronymSetMember], status_code=status.HTTP_201_CREATED)
async def bulk_add_acronyms_to_set(
    *,
    db: AsyncSession = Depends(get_db),
    acronym_set_id: int,
    acronym_ids: List[int],
) -> List[AcronymSetMember]:
    """
    Add multiple acronyms to an acronym set in bulk.
    """
    try:
        # Validate that the acronym set exists
        db_acronym_set = await acronym_set.get(db, id=acronym_set_id)
        if not db_acronym_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acronym set not found"
            )
        
        created_members = []
        errors = []
        
        for acronym_id in acronym_ids:
            try:
                # Check if acronym exists
                db_acronym = await acronym.get(db, id=acronym_id)
                if not db_acronym:
                    errors.append(f"Acronym ID {acronym_id} not found")
                    continue
                
                # Check if membership already exists
                existing_member = await acronym_set_member.get_by_set_and_acronym(
                    db, acronym_set_id=acronym_set_id, acronym_id=acronym_id
                )
                if existing_member:
                    errors.append(f"Acronym '{db_acronym.key}' is already a member of set '{db_acronym_set.name}'")
                    continue
                
                # Create the membership
                member_data = AcronymSetMemberCreate(
                    acronym_set_id=acronym_set_id,
                    acronym_id=acronym_id,
                    sort_order=len(created_members)
                )
                created_member = await acronym_set_member.create(db, obj_in=member_data)
                created_members.append(created_member)
                
            except Exception as e:
                errors.append(f"Error adding acronym ID {acronym_id}: {str(e)}")
        
        if errors and not created_members:
            # All operations failed
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to add any acronyms: {'; '.join(errors)}"
            )
        elif errors:
            # Some operations failed, log warnings but return successes
            print(f"⚠️ Bulk add completed with errors: {'; '.join(errors)}")
        
        print(f"✅ Bulk add completed: Added {len(created_members)} acronyms to '{db_acronym_set.name}'")
        
        # Broadcast WebSocket events for all created members
        for member in created_members:
            try:
                await broadcast_acronym_set_member_created(member)
            except Exception as ws_error:
                print(f"❌ WebSocket broadcast error for member {member.id}: {ws_error}")
        
        return created_members
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        print(f"❌ Error in bulk add acronyms to set: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk add acronyms to set"
        )