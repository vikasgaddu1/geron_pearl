"""
Tracker Tags API Endpoints

API for managing tracker tags - create, update, delete tags,
and assign/remove tags from tracker items.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.crud.tracker_tag import tracker_tag, tracker_item_tag
from app.schemas.tracker_tag import (
    TrackerTag, TrackerTagCreate, TrackerTagUpdate, TrackerTagWithCount,
    TrackerItemTag, TrackerItemTagCreate,
    BulkTagAssignment, BulkTagRemoval, BulkOperationResult, TagSummary
)

router = APIRouter()


# =============================================================================
# Tag Management Endpoints
# =============================================================================

@router.post("/", response_model=TrackerTag, status_code=status.HTTP_201_CREATED)
async def create_tag(
    *,
    db: AsyncSession = Depends(get_db),
    tag_in: TrackerTagCreate
) -> TrackerTag:
    """
    Create a new tag.
    
    - **name**: Unique tag name (e.g., "Topline", "Batch 1")
    - **color**: Hex color code (e.g., "#FF5733")
    - **description**: Optional description
    """
    # Check if name already exists
    existing = await tracker_tag.get_by_name(db, name=tag_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag with name '{tag_in.name}' already exists"
        )
    
    return await tracker_tag.create(db, obj_in=tag_in)


@router.get("/", response_model=List[TrackerTagWithCount])
async def get_all_tags(
    *,
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get all tags with usage counts.
    
    Returns all tags ordered by name, with count of how many trackers use each tag.
    """
    return await tracker_tag.get_all_with_counts(db)


@router.get("/{tag_id}", response_model=TrackerTag)
async def get_tag(
    *,
    db: AsyncSession = Depends(get_db),
    tag_id: int
) -> TrackerTag:
    """
    Get a specific tag by ID.
    """
    db_tag = await tracker_tag.get(db, id=tag_id)
    if not db_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return db_tag


@router.put("/{tag_id}", response_model=TrackerTag)
async def update_tag(
    *,
    db: AsyncSession = Depends(get_db),
    tag_id: int,
    tag_in: TrackerTagUpdate
) -> TrackerTag:
    """
    Update an existing tag.
    
    Can update name, color, and/or description.
    """
    db_tag = await tracker_tag.get(db, id=tag_id)
    if not db_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    # Check name uniqueness if updating name
    if tag_in.name and tag_in.name != db_tag.name:
        existing = await tracker_tag.get_by_name(db, name=tag_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag with name '{tag_in.name}' already exists"
            )
    
    return await tracker_tag.update(db, db_obj=db_tag, obj_in=tag_in)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    *,
    db: AsyncSession = Depends(get_db),
    tag_id: int
) -> None:
    """
    Delete a tag.
    
    This will also remove the tag from all trackers that have it assigned.
    """
    success = await tracker_tag.delete(db, id=tag_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )


# =============================================================================
# Tag Assignment Endpoints
# =============================================================================

@router.post("/assign", response_model=TrackerItemTag, status_code=status.HTTP_201_CREATED)
async def assign_tag_to_tracker(
    *,
    db: AsyncSession = Depends(get_db),
    assignment: TrackerItemTagCreate
) -> TrackerItemTag:
    """
    Assign a tag to a tracker item.
    
    If the tag is already assigned, returns the existing assignment.
    """
    # Verify tag exists
    db_tag = await tracker_tag.get(db, id=assignment.tag_id)
    if not db_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    result = await tracker_item_tag.assign_tag(
        db,
        tracker_id=assignment.tracker_id,
        tag_id=assignment.tag_id
    )
    return result


@router.delete("/assign/{tracker_id}/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_tracker(
    *,
    db: AsyncSession = Depends(get_db),
    tracker_id: int,
    tag_id: int
) -> None:
    """
    Remove a tag from a tracker item.
    """
    success = await tracker_item_tag.remove_tag(
        db,
        tracker_id=tracker_id,
        tag_id=tag_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag assignment not found"
        )


@router.get("/tracker/{tracker_id}", response_model=List[TagSummary])
async def get_tracker_tags(
    *,
    db: AsyncSession = Depends(get_db),
    tracker_id: int
) -> List[TagSummary]:
    """
    Get all tags assigned to a specific tracker.
    """
    tags = await tracker_item_tag.get_tags_for_tracker(db, tracker_id=tracker_id)
    return tags


@router.get("/by-tag/{tag_id}/trackers", response_model=List[int])
async def get_trackers_by_tag(
    *,
    db: AsyncSession = Depends(get_db),
    tag_id: int
) -> List[int]:
    """
    Get all tracker IDs that have a specific tag assigned.
    
    Useful for filtering trackers by tag.
    """
    # Verify tag exists
    db_tag = await tracker_tag.get(db, id=tag_id)
    if not db_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    return await tracker_item_tag.get_trackers_by_tag(db, tag_id=tag_id)


# =============================================================================
# Bulk Operations
# =============================================================================

@router.post("/bulk-assign", response_model=BulkOperationResult)
async def bulk_assign_tag(
    *,
    db: AsyncSession = Depends(get_db),
    data: BulkTagAssignment
) -> BulkOperationResult:
    """
    Assign a tag to multiple trackers at once.
    
    - **tracker_ids**: List of tracker IDs to assign the tag to
    - **tag_id**: Tag ID to assign
    """
    # Verify tag exists
    db_tag = await tracker_tag.get(db, id=data.tag_id)
    if not db_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    return await tracker_item_tag.bulk_assign_tag(
        db,
        tracker_ids=data.tracker_ids,
        tag_id=data.tag_id
    )


@router.post("/bulk-remove", response_model=BulkOperationResult)
async def bulk_remove_tag(
    *,
    db: AsyncSession = Depends(get_db),
    data: BulkTagRemoval
) -> BulkOperationResult:
    """
    Remove a tag from multiple trackers at once.
    
    - **tracker_ids**: List of tracker IDs to remove the tag from
    - **tag_id**: Tag ID to remove
    """
    return await tracker_item_tag.bulk_remove_tag(
        db,
        tracker_ids=data.tracker_ids,
        tag_id=data.tag_id
    )


@router.post("/bulk-get", response_model=Dict[int, List[TagSummary]])
async def get_tags_for_trackers_bulk(
    *,
    db: AsyncSession = Depends(get_db),
    tracker_ids: List[int]
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Get tags for multiple trackers at once (optimized bulk loading).
    
    Returns a dictionary mapping tracker_id to list of tags.
    """
    return await tracker_item_tag.get_tags_for_trackers_bulk(
        db,
        tracker_ids=tracker_ids
    )

