"""
Reporting Effort Milestones API Endpoints

API for managing phases and milestones within reporting efforts.
Phases contain milestones, providing a two-level hierarchy for tracking
key dates and deliverables.
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.crud.reporting_effort import reporting_effort
from app.crud.reporting_effort_phase import reporting_effort_phase
from app.crud.reporting_effort_milestone import reporting_effort_milestone
from app.crud.milestone_tracker_assignment import milestone_tracker_assignment
from app.crud.tracker_tag import tracker_tag
from app.schemas.reporting_effort_phase import (
    ReportingEffortPhase,
    ReportingEffortPhaseCreate,
    ReportingEffortPhaseUpdate,
    ReportingEffortPhaseWithMilestones
)
from app.schemas.reporting_effort_milestone import (
    ReportingEffortMilestone,
    ReportingEffortMilestoneCreate,
    ReportingEffortMilestoneUpdate,
    ReportingEffortMilestoneWithPhase,
    ReportingEffortMilestoneWithTrackers
)
from app.schemas.milestone_tracker_assignment import (
    BulkMilestoneTrackerAssignment,
    BulkOperationResult
)

router = APIRouter()


# =============================================================================
# Phase Endpoints
# =============================================================================

@router.get(
    "/reporting-efforts/{effort_id}/phases",
    response_model=List[ReportingEffortPhaseWithMilestones]
)
async def get_phases_for_effort(
    *,
    db: AsyncSession = Depends(get_db),
    effort_id: int
) -> List[ReportingEffortPhaseWithMilestones]:
    """
    Get all phases with their milestones for a reporting effort.
    
    Returns phases ordered by display_order, with nested milestones
    also ordered by their display_order.
    """
    # Verify reporting effort exists
    effort = await reporting_effort.get(db, id=effort_id)
    if not effort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporting effort not found"
        )
    
    return await reporting_effort_phase.get_all_with_milestones(
        db, 
        reporting_effort_id=effort_id
    )


@router.post(
    "/reporting-efforts/{effort_id}/phases",
    response_model=ReportingEffortPhase,
    status_code=status.HTTP_201_CREATED
)
async def create_phase(
    *,
    db: AsyncSession = Depends(get_db),
    effort_id: int,
    phase_in: ReportingEffortPhaseCreate
) -> ReportingEffortPhase:
    """
    Create a new phase for a reporting effort.
    
    - **name**: Phase name (e.g., "Blinded DMC/DSMT Delivery")
    - **display_order**: Optional order (defaults to next available)
    """
    # Verify reporting effort exists
    effort = await reporting_effort.get(db, id=effort_id)
    if not effort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporting effort not found"
        )
    
    # Override reporting_effort_id from URL
    phase_data = phase_in.model_dump()
    phase_data['reporting_effort_id'] = effort_id
    
    # Set display_order if not provided
    if phase_data.get('display_order', 0) == 0:
        phase_data['display_order'] = await reporting_effort_phase.get_next_display_order(
            db, 
            reporting_effort_id=effort_id
        )
    
    return await reporting_effort_phase.create(
        db, 
        obj_in=ReportingEffortPhaseCreate(**phase_data)
    )


@router.get(
    "/phases/{phase_id}",
    response_model=ReportingEffortPhaseWithMilestones
)
async def get_phase(
    *,
    db: AsyncSession = Depends(get_db),
    phase_id: int
) -> ReportingEffortPhaseWithMilestones:
    """Get a specific phase with its milestones."""
    phase = await reporting_effort_phase.get_with_milestones(db, phase_id=phase_id)
    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phase not found"
        )
    return phase


@router.put(
    "/phases/{phase_id}",
    response_model=ReportingEffortPhase
)
async def update_phase(
    *,
    db: AsyncSession = Depends(get_db),
    phase_id: int,
    phase_in: ReportingEffortPhaseUpdate
) -> ReportingEffortPhase:
    """Update a phase's name or display order."""
    db_phase = await reporting_effort_phase.get(db, id=phase_id)
    if not db_phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phase not found"
        )
    
    return await reporting_effort_phase.update(db, db_obj=db_phase, obj_in=phase_in)


@router.delete(
    "/phases/{phase_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_phase(
    *,
    db: AsyncSession = Depends(get_db),
    phase_id: int
) -> None:
    """
    Delete a phase and all its milestones.
    
    This action cascades to delete all milestones within the phase.
    """
    result = await reporting_effort_phase.delete(db, id=phase_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phase not found"
        )


@router.post(
    "/reporting-efforts/{effort_id}/phases/reorder",
    response_model=List[ReportingEffortPhase]
)
async def reorder_phases(
    *,
    db: AsyncSession = Depends(get_db),
    effort_id: int,
    phase_ids: List[int]
) -> List[ReportingEffortPhase]:
    """
    Reorder phases by providing the desired order of phase IDs.
    
    - **phase_ids**: List of phase IDs in the desired display order
    """
    # Verify reporting effort exists
    effort = await reporting_effort.get(db, id=effort_id)
    if not effort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporting effort not found"
        )
    
    return await reporting_effort_phase.reorder_phases(
        db,
        reporting_effort_id=effort_id,
        phase_ids=phase_ids
    )


# =============================================================================
# Dashboard Endpoints (MUST be before /{milestone_id} routes to avoid route conflict)
# =============================================================================

@router.get(
    "/dashboard",
    response_model=List[ReportingEffortMilestoneWithPhase]
)
async def get_milestones_for_dashboard(
    *,
    db: AsyncSession = Depends(get_db),
    study_id: Optional[int] = Query(None, description="Filter by study ID"),
    reporting_effort_id: Optional[int] = Query(None, description="Filter by reporting effort ID"),
    include_completed: bool = Query(True, description="Include completed milestones"),
    start_date: Optional[date] = Query(None, description="Filter milestones from this date"),
    end_date: Optional[date] = Query(None, description="Filter milestones until this date")
) -> List[ReportingEffortMilestoneWithPhase]:
    """
    Get all milestones with full context for dashboard display.

    Returns milestones with phase name, reporting effort label, and study label
    for display in the Gantt chart or timeline view.
    """
    return await reporting_effort_milestone.get_all_for_dashboard(
        db,
        study_id=study_id,
        reporting_effort_id=reporting_effort_id,
        include_completed=include_completed,
        start_date=start_date,
        end_date=end_date
    )


@router.get(
    "/upcoming",
    response_model=List[ReportingEffortMilestoneWithPhase]
)
async def get_upcoming_milestones(
    *,
    db: AsyncSession = Depends(get_db),
    days_ahead: int = Query(14, ge=1, le=365, description="Number of days to look ahead"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of milestones to return")
) -> List[ReportingEffortMilestoneWithPhase]:
    """
    Get upcoming milestones for the next N days.

    Useful for showing a summary of what's coming up soon.
    """
    return await reporting_effort_milestone.get_upcoming(
        db,
        days_ahead=days_ahead,
        limit=limit
    )


# =============================================================================
# Milestone Endpoints
# =============================================================================

@router.post(
    "/phases/{phase_id}/milestones",
    response_model=ReportingEffortMilestone,
    status_code=status.HTTP_201_CREATED
)
async def create_milestone(
    *,
    db: AsyncSession = Depends(get_db),
    phase_id: int,
    milestone_in: ReportingEffortMilestoneCreate
) -> ReportingEffortMilestone:
    """
    Create a new milestone within a phase.
    
    - **name**: Milestone description
    - **due_date**: Target date for completion
    - **responsibility**: Party responsible (e.g., "Tigermed", "Geron")
    - **comments**: Optional notes
    """
    # Verify phase exists
    phase = await reporting_effort_phase.get(db, id=phase_id)
    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phase not found"
        )
    
    # Override phase_id from URL
    milestone_data = milestone_in.model_dump()
    milestone_data['phase_id'] = phase_id
    
    # Set display_order if not provided
    if milestone_data.get('display_order', 0) == 0:
        milestone_data['display_order'] = await reporting_effort_milestone.get_next_display_order(
            db,
            phase_id=phase_id
        )
    
    return await reporting_effort_milestone.create(
        db,
        obj_in=ReportingEffortMilestoneCreate(**milestone_data)
    )


@router.get(
    "/{milestone_id}",
    response_model=ReportingEffortMilestone
)
async def get_milestone(
    *,
    db: AsyncSession = Depends(get_db),
    milestone_id: int
) -> ReportingEffortMilestone:
    """Get a specific milestone."""
    milestone = await reporting_effort_milestone.get(db, id=milestone_id)
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found"
        )
    return milestone


@router.put(
    "/{milestone_id}",
    response_model=ReportingEffortMilestone
)
async def update_milestone(
    *,
    db: AsyncSession = Depends(get_db),
    milestone_id: int,
    milestone_in: ReportingEffortMilestoneUpdate
) -> ReportingEffortMilestone:
    """Update a milestone."""
    db_milestone = await reporting_effort_milestone.get(db, id=milestone_id)
    if not db_milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found"
        )
    
    return await reporting_effort_milestone.update(
        db, 
        db_obj=db_milestone, 
        obj_in=milestone_in
    )


@router.delete(
    "/{milestone_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_milestone(
    *,
    db: AsyncSession = Depends(get_db),
    milestone_id: int
) -> None:
    """Delete a milestone."""
    result = await reporting_effort_milestone.delete(db, id=milestone_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found"
        )


@router.post(
    "/{milestone_id}/complete",
    response_model=ReportingEffortMilestone
)
async def mark_milestone_complete(
    *,
    db: AsyncSession = Depends(get_db),
    milestone_id: int,
    completion_date: Optional[date] = None
) -> ReportingEffortMilestone:
    """Mark a milestone as completed."""
    milestone = await reporting_effort_milestone.mark_completed(
        db,
        milestone_id=milestone_id,
        completion_date=completion_date
    )
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found"
        )
    return milestone


@router.post(
    "/{milestone_id}/incomplete",
    response_model=ReportingEffortMilestone
)
async def mark_milestone_incomplete(
    *,
    db: AsyncSession = Depends(get_db),
    milestone_id: int
) -> ReportingEffortMilestone:
    """Mark a milestone as incomplete (not completed)."""
    milestone = await reporting_effort_milestone.mark_incomplete(
        db,
        milestone_id=milestone_id
    )
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found"
        )
    return milestone


@router.post(
    "/phases/{phase_id}/milestones/reorder",
    response_model=List[ReportingEffortMilestone]
)
async def reorder_milestones(
    *,
    db: AsyncSession = Depends(get_db),
    phase_id: int,
    milestone_ids: List[int]
) -> List[ReportingEffortMilestone]:
    """
    Reorder milestones within a phase.

    - **milestone_ids**: List of milestone IDs in the desired display order
    """
    # Verify phase exists
    phase = await reporting_effort_phase.get(db, id=phase_id)
    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phase not found"
        )

    return await reporting_effort_milestone.reorder_milestones(
        db,
        phase_id=phase_id,
        milestone_ids=milestone_ids
    )


# =============================================================================
# Milestone-Tracker Linking Endpoints
# =============================================================================

@router.get(
    "/{milestone_id}/with-trackers",
    response_model=ReportingEffortMilestoneWithTrackers
)
async def get_milestone_with_trackers(
    *,
    db: AsyncSession = Depends(get_db),
    milestone_id: int
) -> dict:
    """
    Get a milestone with linked tracker information.

    Returns the milestone with:
    - linked_tracker_count: Total number of linked trackers
    - trackers_past_due: Count of trackers with due_date > milestone due_date
    - linked_tag_name: Name of the linked tag (if any)
    - linked_tracker_ids: IDs of manually linked trackers
    """
    result = await reporting_effort_milestone.get_milestone_with_tracker_info(
        db, milestone_id=milestone_id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found"
        )
    return result


@router.get(
    "/{milestone_id}/trackers"
)
async def get_linked_trackers(
    *,
    db: AsyncSession = Depends(get_db),
    milestone_id: int
) -> List[dict]:
    """
    Get all trackers linked to a milestone.

    Returns trackers linked via:
    - Subtype (milestone.linked_subtype matches item.item_subtype)
    - Tag (milestone.linked_tag_id matches tracker's tag)
    - Manual assignment (milestone_tracker_assignments)

    Each tracker includes:
    - id, item_code, item_subtype, due_date
    - link_type: 'subtype', 'tag', or 'manual'
    - is_past_due: True if tracker due_date > milestone due_date
    """
    milestone = await reporting_effort_milestone.get(db, id=milestone_id)
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found"
        )

    return await reporting_effort_milestone.get_linked_trackers(
        db, milestone_id=milestone_id
    )


@router.get(
    "/{milestone_id}/available-trackers"
)
async def get_available_trackers(
    *,
    db: AsyncSession = Depends(get_db),
    milestone_id: int
) -> List[dict]:
    """
    Get trackers that can be manually linked to this milestone.

    Returns trackers in the same reporting effort that are NOT already linked
    (by subtype, tag, or manual assignment).

    Useful for the manual selection UI in the milestone editor.
    """
    milestone = await reporting_effort_milestone.get(db, id=milestone_id)
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found"
        )

    return await reporting_effort_milestone.get_available_trackers(
        db, milestone_id=milestone_id
    )


@router.post(
    "/{milestone_id}/trackers",
    response_model=BulkOperationResult
)
async def link_trackers_to_milestone(
    *,
    db: AsyncSession = Depends(get_db),
    milestone_id: int,
    tracker_ids: List[int] = Query(..., description="List of tracker IDs to link")
) -> BulkOperationResult:
    """
    Manually link trackers to a milestone.

    This creates manual links (separate from subtype/tag auto-linking).
    Trackers already linked (by any method) will be skipped.

    - **tracker_ids**: List of tracker IDs to link
    """
    milestone = await reporting_effort_milestone.get(db, id=milestone_id)
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found"
        )

    result = await milestone_tracker_assignment.bulk_assign(
        db,
        milestone_id=milestone_id,
        tracker_ids=tracker_ids
    )
    return BulkOperationResult(**result)


@router.delete(
    "/{milestone_id}/trackers",
    response_model=BulkOperationResult
)
async def unlink_trackers_from_milestone(
    *,
    db: AsyncSession = Depends(get_db),
    milestone_id: int,
    tracker_ids: List[int] = Query(..., description="List of tracker IDs to unlink")
) -> BulkOperationResult:
    """
    Remove manual links between trackers and a milestone.

    This only removes manual links. Subtype and tag links cannot be
    removed this way (change the milestone's linked_subtype/linked_tag_id instead).

    - **tracker_ids**: List of tracker IDs to unlink
    """
    milestone = await reporting_effort_milestone.get(db, id=milestone_id)
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found"
        )

    result = await milestone_tracker_assignment.bulk_remove(
        db,
        milestone_id=milestone_id,
        tracker_ids=tracker_ids
    )
    return BulkOperationResult(**result)


@router.get(
    "/tags/for-linking"
)
async def get_tags_for_linking(
    *,
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """
    Get all available tags for milestone linking.

    Returns list of tags with id, name, and color.
    Used for the tag selection dropdown in milestone editor.
    """
    tags = await tracker_tag.get_multi(db, skip=0, limit=1000)
    return [
        {
            'id': tag.id,
            'name': tag.name,
            'color': tag.color
        }
        for tag in tags
    ]


# =============================================================================
# Copy Milestones Endpoints
# =============================================================================

@router.post(
    "/reporting-efforts/{effort_id}/copy-from/{source_effort_id}",
    response_model=List[ReportingEffortPhaseWithMilestones],
    status_code=status.HTTP_201_CREATED
)
async def copy_milestones_from_effort(
    *,
    db: AsyncSession = Depends(get_db),
    effort_id: int,
    source_effort_id: int,
    date_offset_days: Optional[int] = Query(None, description="Days to offset all due dates (positive = future)")
) -> List[ReportingEffortPhaseWithMilestones]:
    """
    Copy all phases and milestones from another reporting effort.
    
    This creates a complete copy of the milestone structure from the source effort.
    Optionally offset all due dates by a number of days.
    
    - **effort_id**: Target reporting effort to copy milestones into
    - **source_effort_id**: Source reporting effort to copy from
    - **date_offset_days**: Optional number of days to shift all due dates
    """
    # Verify both reporting efforts exist
    target_effort = await reporting_effort.get(db, id=effort_id)
    if not target_effort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target reporting effort not found"
        )
    
    source_effort = await reporting_effort.get(db, id=source_effort_id)
    if not source_effort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source reporting effort not found"
        )
    
    # Get source phases with milestones
    source_phases = await reporting_effort_phase.get_all_with_milestones(
        db, 
        reporting_effort_id=source_effort_id
    )
    
    if not source_phases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source reporting effort has no phases to copy"
        )
    
    # Copy each phase and its milestones
    from datetime import timedelta
    from app.schemas.reporting_effort_phase import ReportingEffortPhaseCreate
    from app.schemas.reporting_effort_milestone import ReportingEffortMilestoneCreate
    
    for source_phase in source_phases:
        # Create new phase
        new_phase_data = ReportingEffortPhaseCreate(
            reporting_effort_id=effort_id,
            name=source_phase.name,
            display_order=source_phase.display_order
        )
        new_phase = await reporting_effort_phase.create(db, obj_in=new_phase_data)
        
        # Copy milestones
        if source_phase.milestones:
            for source_milestone in source_phase.milestones:
                # Calculate new dates if offset provided
                new_start_date = source_milestone.start_date
                new_due_date = source_milestone.due_date
                if date_offset_days:
                    if new_start_date:
                        new_start_date = new_start_date + timedelta(days=date_offset_days)
                    if new_due_date:
                        new_due_date = new_due_date + timedelta(days=date_offset_days)

                new_milestone_data = ReportingEffortMilestoneCreate(
                    phase_id=new_phase.id,
                    name=source_milestone.name,
                    start_date=new_start_date,
                    due_date=new_due_date,
                    responsibility=source_milestone.responsibility,
                    comments=source_milestone.comments,
                    is_completed=False,  # Always start as not completed
                    completion_date=None,
                    display_order=source_milestone.display_order
                )
                await reporting_effort_milestone.create(db, obj_in=new_milestone_data)
    
    # Return the newly created phases with milestones
    return await reporting_effort_phase.get_all_with_milestones(
        db, 
        reporting_effort_id=effort_id
    )


@router.get(
    "/reporting-efforts/available-sources",
    response_model=List[dict]
)
async def get_available_source_efforts(
    *,
    db: AsyncSession = Depends(get_db),
    exclude_effort_id: Optional[int] = Query(None, description="Effort ID to exclude from results")
) -> List[dict]:
    """
    Get list of reporting efforts that have milestones (can be used as copy sources).
    
    Returns reporting efforts with at least one phase, along with study/release context.
    """
    from sqlalchemy import select, func
    from app.models.reporting_effort_phase import ReportingEffortPhase
    from app.models.reporting_effort import ReportingEffort
    from app.models.study import Study
    
    # Query efforts that have phases
    query = (
        select(
            ReportingEffort.id,
            ReportingEffort.database_release_label,
            Study.study_label,
            func.count(ReportingEffortPhase.id).label('phase_count')
        )
        .join(Study, ReportingEffort.study_id == Study.id)
        .join(ReportingEffortPhase, ReportingEffort.id == ReportingEffortPhase.reporting_effort_id)
        .group_by(ReportingEffort.id, ReportingEffort.database_release_label, Study.study_label)
        .having(func.count(ReportingEffortPhase.id) > 0)
    )
    
    if exclude_effort_id:
        query = query.where(ReportingEffort.id != exclude_effort_id)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            'id': row.id,
            'label': f"{row.study_label} - {row.database_release_label}",
            'study_label': row.study_label,
            'database_release_label': row.database_release_label,
            'phase_count': row.phase_count
        }
        for row in rows
    ]

