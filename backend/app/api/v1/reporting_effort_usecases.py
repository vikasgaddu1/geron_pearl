"""API endpoints for ReportingEffort Use Cases."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.crud.reporting_effort_usecase import reporting_effort_usecase, reporting_effort_usecase_assignment
from app.crud.reporting_effort import reporting_effort
from app.schemas.reporting_effort_usecase import (
    ReportingEffortUseCase,
    ReportingEffortUseCaseCreate,
    ReportingEffortUseCaseUpdate,
    ReportingEffortUseCaseWithCount,
    UseCaseSummary,
    UseCaseAssignmentCreate,
    BulkUseCaseAssignment,
    BulkUseCaseRemoval,
    BulkOperationResult
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Use Case Management Endpoints
# =============================================================================

@router.post("/", response_model=ReportingEffortUseCase, status_code=status.HTTP_201_CREATED)
async def create_use_case(
    *,
    db: AsyncSession = Depends(get_db),
    use_case_in: ReportingEffortUseCaseCreate
) -> ReportingEffortUseCase:
    """Create a new use case."""
    # Check for duplicate name
    existing = await reporting_effort_usecase.get_by_name(db, name=use_case_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Use case with name '{use_case_in.name}' already exists"
        )

    db_use_case = await reporting_effort_usecase.create(db, obj_in=use_case_in)
    return db_use_case


@router.get("/", response_model=List[ReportingEffortUseCaseWithCount])
async def get_all_use_cases(
    *,
    db: AsyncSession = Depends(get_db)
) -> List[ReportingEffortUseCaseWithCount]:
    """Get all use cases with usage counts."""
    use_cases = await reporting_effort_usecase.get_all_with_counts(db)
    return use_cases


@router.get("/{use_case_id}", response_model=ReportingEffortUseCase)
async def get_use_case(
    *,
    db: AsyncSession = Depends(get_db),
    use_case_id: int
) -> ReportingEffortUseCase:
    """Get a single use case by ID."""
    db_use_case = await reporting_effort_usecase.get(db, id=use_case_id)
    if not db_use_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Use case not found"
        )
    return db_use_case


@router.put("/{use_case_id}", response_model=ReportingEffortUseCase)
async def update_use_case(
    *,
    db: AsyncSession = Depends(get_db),
    use_case_id: int,
    use_case_in: ReportingEffortUseCaseUpdate
) -> ReportingEffortUseCase:
    """Update a use case."""
    db_use_case = await reporting_effort_usecase.get(db, id=use_case_id)
    if not db_use_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Use case not found"
        )

    # Check for duplicate name if name is being changed
    if use_case_in.name and use_case_in.name.lower() != db_use_case.name.lower():
        existing = await reporting_effort_usecase.get_by_name(db, name=use_case_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Use case with name '{use_case_in.name}' already exists"
            )

    updated = await reporting_effort_usecase.update(db, db_obj=db_use_case, obj_in=use_case_in)
    return updated


@router.delete("/{use_case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_use_case(
    *,
    db: AsyncSession = Depends(get_db),
    use_case_id: int
):
    """Delete a use case. Assignments will be cascade deleted."""
    db_use_case = await reporting_effort_usecase.get(db, id=use_case_id)
    if not db_use_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Use case not found"
        )

    await reporting_effort_usecase.delete(db, id=use_case_id)


# =============================================================================
# Assignment Endpoints
# =============================================================================

@router.post("/assign", status_code=status.HTTP_201_CREATED)
async def assign_use_case(
    *,
    db: AsyncSession = Depends(get_db),
    assignment: UseCaseAssignmentCreate
):
    """Assign a use case to a reporting effort."""
    # Verify use case exists
    use_case = await reporting_effort_usecase.get(db, id=assignment.use_case_id)
    if not use_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Use case not found"
        )

    # Verify reporting effort exists
    effort = await reporting_effort.get(db, id=assignment.reporting_effort_id)
    if not effort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporting effort not found"
        )

    await reporting_effort_usecase_assignment.assign(
        db,
        reporting_effort_id=assignment.reporting_effort_id,
        use_case_id=assignment.use_case_id
    )
    return {"message": "Use case assigned successfully"}


@router.delete("/assign/{reporting_effort_id}/{use_case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_use_case_assignment(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_id: int,
    use_case_id: int
):
    """Remove a use case assignment from a reporting effort."""
    removed = await reporting_effort_usecase_assignment.remove(
        db,
        reporting_effort_id=reporting_effort_id,
        use_case_id=use_case_id
    )
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )


@router.get("/effort/{reporting_effort_id}", response_model=List[UseCaseSummary])
async def get_use_cases_for_effort(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_id: int
) -> List[UseCaseSummary]:
    """Get all use cases assigned to a reporting effort."""
    # Verify effort exists
    effort = await reporting_effort.get(db, id=reporting_effort_id)
    if not effort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporting effort not found"
        )

    use_cases = await reporting_effort_usecase_assignment.get_use_cases_for_effort(
        db,
        reporting_effort_id=reporting_effort_id
    )
    return use_cases


@router.get("/by-use-case/{use_case_id}/efforts", response_model=List[int])
async def get_efforts_by_use_case(
    *,
    db: AsyncSession = Depends(get_db),
    use_case_id: int
) -> List[int]:
    """Get all reporting effort IDs that have a specific use case."""
    # Verify use case exists
    use_case = await reporting_effort_usecase.get(db, id=use_case_id)
    if not use_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Use case not found"
        )

    effort_ids = await reporting_effort_usecase_assignment.get_efforts_by_use_case(
        db,
        use_case_id=use_case_id
    )
    return effort_ids


# =============================================================================
# Bulk Operations
# =============================================================================

@router.post("/bulk-assign", response_model=BulkOperationResult)
async def bulk_assign_use_case(
    *,
    db: AsyncSession = Depends(get_db),
    bulk_request: BulkUseCaseAssignment
) -> BulkOperationResult:
    """Assign a use case to multiple reporting efforts."""
    # Verify use case exists
    use_case = await reporting_effort_usecase.get(db, id=bulk_request.use_case_id)
    if not use_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Use case not found"
        )

    result = await reporting_effort_usecase_assignment.bulk_assign(
        db,
        reporting_effort_ids=bulk_request.reporting_effort_ids,
        use_case_id=bulk_request.use_case_id
    )
    return result


@router.post("/bulk-remove", response_model=BulkOperationResult)
async def bulk_remove_use_case(
    *,
    db: AsyncSession = Depends(get_db),
    bulk_request: BulkUseCaseRemoval
) -> BulkOperationResult:
    """Remove a use case from multiple reporting efforts."""
    result = await reporting_effort_usecase_assignment.bulk_remove(
        db,
        reporting_effort_ids=bulk_request.reporting_effort_ids,
        use_case_id=bulk_request.use_case_id
    )
    return result


@router.post("/bulk-get")
async def bulk_get_use_cases(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_ids: List[int]
):
    """Get use cases for multiple reporting efforts in one request."""
    result = await reporting_effort_usecase_assignment.get_use_cases_for_efforts_bulk(
        db,
        reporting_effort_ids=reporting_effort_ids
    )
    return result
