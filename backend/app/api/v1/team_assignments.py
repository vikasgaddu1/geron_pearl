"""Team Assignment API endpoints for managing study team allocations."""

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import study_team_assignment, study
from app.db.session import get_db
from app.schemas.study_team_assignment import (
    StudyTeamAssignment,
    StudyTeamAssignmentCreate,
    StudyTeamAssignmentUpdate,
    CreateTeamAssignmentRequest,
    ChangeAllocationRequest,
    EndAssignmentRequest,
    StudyTeamResponse,
    TeamMemberSummary,
    UserAssignmentsResponse,
    AllocationHistoryResponse,
    OrphanedItemsWarning,
    StudyTeamAssignmentWithUser,
    StudyTeamAssignmentWithStudy
)
from app.models.user import User as UserModel
from app.core.security import get_current_user
from app.core.study_permissions import require_study_lead_access

router = APIRouter()


@router.get("/study/{study_id}", response_model=StudyTeamResponse)
async def get_study_team(
    study_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> StudyTeamResponse:
    """
    Get all active team members for a study with their allocations.
    """
    # Verify study exists
    study_obj = await study.get(db, id=study_id)
    if not study_obj:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Get active assignments
    assignments = await study_team_assignment.get_active_by_study(db, study_id=study_id)
    
    # Build member summaries
    members = []
    for assignment in assignments:
        members.append(TeamMemberSummary(
            user_id=assignment.user_id,
            username=assignment.user.username,
            email=assignment.user.email,
            job_type=assignment.job_type,
            allocation_percentage=assignment.allocation_percentage,
            productive_time_factor=assignment.productive_time_factor,
            experience_level=assignment.experience_level,
            effective_start_date=assignment.effective_start_date,
            is_active=assignment.is_active,
            effective_weekly_hours=assignment.effective_weekly_hours,
            assignment_id=assignment.id
        ))
    
    # Calculate totals
    total_allocation = sum(m.allocation_percentage for m in members)
    total_weekly_hours = sum(m.effective_weekly_hours for m in members)
    
    return StudyTeamResponse(
        study_id=study_id,
        study_label=study_obj.study_label,
        active_members=members,
        total_allocation_percentage=total_allocation,
        total_weekly_capacity_hours=total_weekly_hours,
        member_count=len(members)
    )


@router.get("/user/{user_id}", response_model=UserAssignmentsResponse)
async def get_user_assignments(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> UserAssignmentsResponse:
    """
    Get all active study assignments for a user.
    """
    from app.crud import user as user_crud
    
    user_obj = await user_crud.get(db, id=user_id)
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    
    assignments = await study_team_assignment.get_active_by_user(db, user_id=user_id)
    
    # Convert to schema with study info
    assignment_schemas = []
    for a in assignments:
        assignment_schemas.append(StudyTeamAssignmentWithStudy(
            id=a.id,
            user_id=a.user_id,
            study_id=a.study_id,
            job_type=a.job_type,
            allocation_percentage=a.allocation_percentage,
            productive_time_factor=a.productive_time_factor,
            experience_level=a.experience_level,
            effective_start_date=a.effective_start_date,
            effective_end_date=a.effective_end_date,
            is_active=a.is_active,
            departure_reason=a.departure_reason,
            notes=a.notes,
            created_at=a.created_at,
            updated_at=a.updated_at,
            study_label=a.study.study_label
        ))
    
    total_allocation = await study_team_assignment.get_user_total_allocation(db, user_id=user_id)
    
    return UserAssignmentsResponse(
        user_id=user_id,
        username=user_obj.username,
        active_assignments=assignment_schemas,
        total_allocation_percentage=total_allocation,
        is_over_allocated=total_allocation > 100
    )


@router.get("/history/{user_id}/{study_id}", response_model=AllocationHistoryResponse)
async def get_allocation_history(
    user_id: int,
    study_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> AllocationHistoryResponse:
    """
    Get full allocation history for a user on a specific study.
    """
    from app.crud import user as user_crud
    
    user_obj = await user_crud.get(db, id=user_id)
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    
    study_obj = await study.get(db, id=study_id)
    if not study_obj:
        raise HTTPException(status_code=404, detail="Study not found")
    
    assignments = await study_team_assignment.get_allocation_history(
        db, user_id=user_id, study_id=study_id
    )
    
    return AllocationHistoryResponse(
        user_id=user_id,
        username=user_obj.username,
        study_id=study_id,
        study_label=study_obj.study_label,
        assignments=[StudyTeamAssignment.model_validate(a) for a in assignments]
    )


@router.post("/study/{study_id}", response_model=StudyTeamAssignment, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    study_id: int,
    request: CreateTeamAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> StudyTeamAssignment:
    """
    Add a new team member to a study.
    
    Requires: Admin or Study LEAD role.
    """
    # Check authorization: must be admin or study LEAD
    await require_study_lead_access(db, current_user, study_id)
    
    # Verify study exists
    study_obj = await study.get(db, id=study_id)
    if not study_obj:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Verify user exists
    from app.crud import user as user_crud
    user_obj = await user_crud.get(db, id=request.user_id)
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        assignment = await study_team_assignment.add_team_member(
            db,
            user_id=request.user_id,
            study_id=study_id,
            job_type=request.job_type,
            allocation_percentage=request.allocation_percentage,
            productive_time_factor=request.productive_time_factor,
            experience_level=request.experience_level,
            effective_start_date=request.effective_start_date,
            notes=request.notes
        )
        return StudyTeamAssignment.model_validate(assignment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{assignment_id}/change-allocation", response_model=StudyTeamAssignment)
async def change_team_member_allocation(
    assignment_id: int,
    request: ChangeAllocationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> StudyTeamAssignment:
    """
    Change a team member's allocation.
    
    This closes the current assignment and creates a new one to preserve history.
    
    Requires: Admin or Study LEAD role.
    """
    # Get the current assignment
    current = await study_team_assignment.get(db, id=assignment_id)
    if not current:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Check authorization: must be admin or study LEAD
    await require_study_lead_access(db, current_user, current.study_id)
    
    if not current.is_active:
        raise HTTPException(status_code=400, detail="Cannot modify an inactive assignment")
    
    try:
        new_assignment = await study_team_assignment.change_allocation(
            db,
            user_id=current.user_id,
            study_id=current.study_id,
            request=request
        )
        return StudyTeamAssignment.model_validate(new_assignment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{assignment_id}/end", response_model=StudyTeamAssignment)
async def end_team_assignment(
    assignment_id: int,
    request: EndAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> StudyTeamAssignment:
    """
    End a team member's assignment on a study.
    
    Items assigned to this user will remain assigned but flagged for reassignment.
    
    Requires: Admin or Study LEAD role.
    """
    # Get the current assignment
    current = await study_team_assignment.get(db, id=assignment_id)
    if not current:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Check authorization: must be admin or study LEAD
    await require_study_lead_access(db, current_user, current.study_id)
    
    if not current.is_active:
        raise HTTPException(status_code=400, detail="Assignment is already ended")
    
    try:
        ended_assignment = await study_team_assignment.end_assignment(
            db,
            user_id=current.user_id,
            study_id=current.study_id,
            request=request
        )
        return StudyTeamAssignment.model_validate(ended_assignment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/warnings/orphaned-items", response_model=List[OrphanedItemsWarning])
async def get_orphaned_items_warnings(
    study_id: Optional[int] = Query(None, description="Filter by study ID"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> List[OrphanedItemsWarning]:
    """
    Get warnings about tracker items assigned to inactive team members.
    
    These items need to be reassigned.
    """
    orphaned = await study_team_assignment.get_inactive_members_with_items(
        db, study_id=study_id
    )
    
    return [
        OrphanedItemsWarning(
            user_id=o["user_id"],
            username=o["username"],
            study_id=o["study_id"],
            study_label=o["study_label"],
            departure_reason=o["departure_reason"],
            departure_date=o["departure_date"],
            orphaned_item_count=o["orphaned_item_count"],
            item_ids=[]  # Would need additional query to get IDs
        )
        for o in orphaned
    ]


@router.get("/warnings/over-allocated", response_model=List[dict])
async def get_over_allocated_users(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> List[dict]:
    """
    Get list of users whose total allocation exceeds 100%.
    """
    return await study_team_assignment.get_over_allocated_users(db)


@router.get("/{assignment_id}", response_model=StudyTeamAssignment)
async def get_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> StudyTeamAssignment:
    """
    Get a specific team assignment by ID.
    """
    assignment = await study_team_assignment.get(db, id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return StudyTeamAssignment.model_validate(assignment)


@router.put("/{assignment_id}", response_model=StudyTeamAssignment)
async def update_assignment(
    assignment_id: int,
    update_data: StudyTeamAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> StudyTeamAssignment:
    """
    Update a team assignment (for correcting data entry errors).
    
    For allocation changes, use the change-allocation endpoint instead.
    
    Requires: Admin or Study LEAD role.
    """
    assignment = await study_team_assignment.get(db, id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Check authorization: must be admin or study LEAD
    await require_study_lead_access(db, current_user, assignment.study_id)
    
    updated = await study_team_assignment.update(db, db_obj=assignment, obj_in=update_data)
    return StudyTeamAssignment.model_validate(updated)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Delete a team assignment record.
    
    Warning: This permanently removes the record. Consider using end_assignment instead.
    
    Requires: Admin or Study LEAD role.
    """
    assignment = await study_team_assignment.get(db, id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Check authorization: must be admin or study LEAD
    await require_study_lead_access(db, current_user, assignment.study_id)
    
    await study_team_assignment.delete(db, id=assignment_id)

