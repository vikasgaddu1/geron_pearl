"""CRUD operations for ReportingEffort Use Cases."""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import BaseCRUD
from app.models.reporting_effort_usecase import ReportingEffortUseCase, ReportingEffortUseCaseAssignment
from app.schemas.reporting_effort_usecase import (
    ReportingEffortUseCaseCreate,
    ReportingEffortUseCaseUpdate,
    BulkOperationResult
)


class CRUDReportingEffortUseCase(BaseCRUD[ReportingEffortUseCase, ReportingEffortUseCaseCreate, ReportingEffortUseCaseUpdate]):
    """CRUD operations for ReportingEffortUseCase (definitions)."""

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[ReportingEffortUseCase]:
        """Get a use case by name (case-insensitive)."""
        result = await db.execute(
            select(ReportingEffortUseCase).where(
                func.lower(ReportingEffortUseCase.name) == name.lower()
            )
        )
        return result.scalar_one_or_none()

    async def get_all_with_counts(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get all use cases with their usage counts."""
        # Subquery for counting assignments
        count_subquery = (
            select(
                ReportingEffortUseCaseAssignment.use_case_id,
                func.count(ReportingEffortUseCaseAssignment.id).label('usage_count')
            )
            .group_by(ReportingEffortUseCaseAssignment.use_case_id)
            .subquery()
        )

        query = (
            select(
                ReportingEffortUseCase,
                func.coalesce(count_subquery.c.usage_count, 0).label('usage_count')
            )
            .outerjoin(count_subquery, ReportingEffortUseCase.id == count_subquery.c.use_case_id)
            .order_by(ReportingEffortUseCase.name)
        )

        result = await db.execute(query)
        rows = result.all()

        return [
            {
                'id': row.ReportingEffortUseCase.id,
                'name': row.ReportingEffortUseCase.name,
                'color': row.ReportingEffortUseCase.color,
                'description': row.ReportingEffortUseCase.description,
                'created_at': row.ReportingEffortUseCase.created_at,
                'updated_at': row.ReportingEffortUseCase.updated_at,
                'usage_count': row.usage_count
            }
            for row in rows
        ]


class CRUDReportingEffortUseCaseAssignment:
    """CRUD operations for UseCase assignments to ReportingEfforts."""

    async def assign(
        self,
        db: AsyncSession,
        *,
        reporting_effort_id: int,
        use_case_id: int
    ) -> Optional[ReportingEffortUseCaseAssignment]:
        """
        Assign a use case to a reporting effort.
        Idempotent - returns existing assignment if already exists.
        """
        # Check if already assigned
        existing = await self.get_assignment(db, reporting_effort_id=reporting_effort_id, use_case_id=use_case_id)
        if existing:
            return existing

        # Create new assignment
        assignment = ReportingEffortUseCaseAssignment(
            reporting_effort_id=reporting_effort_id,
            use_case_id=use_case_id
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment

    async def remove(
        self,
        db: AsyncSession,
        *,
        reporting_effort_id: int,
        use_case_id: int
    ) -> bool:
        """Remove a use case assignment. Returns True if deleted."""
        assignment = await self.get_assignment(db, reporting_effort_id=reporting_effort_id, use_case_id=use_case_id)
        if assignment:
            await db.delete(assignment)
            await db.commit()
            return True
        return False

    async def get_assignment(
        self,
        db: AsyncSession,
        *,
        reporting_effort_id: int,
        use_case_id: int
    ) -> Optional[ReportingEffortUseCaseAssignment]:
        """Get a specific assignment."""
        result = await db.execute(
            select(ReportingEffortUseCaseAssignment).where(
                and_(
                    ReportingEffortUseCaseAssignment.reporting_effort_id == reporting_effort_id,
                    ReportingEffortUseCaseAssignment.use_case_id == use_case_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_use_cases_for_effort(
        self,
        db: AsyncSession,
        *,
        reporting_effort_id: int
    ) -> List[ReportingEffortUseCase]:
        """Get all use cases assigned to a reporting effort."""
        result = await db.execute(
            select(ReportingEffortUseCase)
            .join(ReportingEffortUseCaseAssignment)
            .where(ReportingEffortUseCaseAssignment.reporting_effort_id == reporting_effort_id)
            .order_by(ReportingEffortUseCase.name)
        )
        return list(result.scalars().all())

    async def get_efforts_by_use_case(
        self,
        db: AsyncSession,
        *,
        use_case_id: int
    ) -> List[int]:
        """Get all reporting effort IDs that have a specific use case."""
        result = await db.execute(
            select(ReportingEffortUseCaseAssignment.reporting_effort_id)
            .where(ReportingEffortUseCaseAssignment.use_case_id == use_case_id)
        )
        return [row[0] for row in result.all()]

    async def get_use_cases_for_efforts_bulk(
        self,
        db: AsyncSession,
        *,
        reporting_effort_ids: List[int]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Get use cases for multiple reporting efforts in one query.
        Returns: {effort_id: [{id, name, color}, ...], ...}
        """
        if not reporting_effort_ids:
            return {}

        result = await db.execute(
            select(ReportingEffortUseCaseAssignment, ReportingEffortUseCase)
            .join(ReportingEffortUseCase, ReportingEffortUseCaseAssignment.use_case_id == ReportingEffortUseCase.id)
            .where(ReportingEffortUseCaseAssignment.reporting_effort_id.in_(reporting_effort_ids))
            .order_by(ReportingEffortUseCaseAssignment.reporting_effort_id, ReportingEffortUseCase.name)
        )
        rows = result.all()

        # Initialize dict with empty lists
        use_cases_by_effort: Dict[int, List[Dict[str, Any]]] = {eid: [] for eid in reporting_effort_ids}

        for row in rows:
            effort_id = row.ReportingEffortUseCaseAssignment.reporting_effort_id
            use_case_dict = {
                'id': row.ReportingEffortUseCase.id,
                'name': row.ReportingEffortUseCase.name,
                'color': row.ReportingEffortUseCase.color
            }
            use_cases_by_effort[effort_id].append(use_case_dict)

        return use_cases_by_effort

    async def bulk_assign(
        self,
        db: AsyncSession,
        *,
        reporting_effort_ids: List[int],
        use_case_id: int
    ) -> BulkOperationResult:
        """Assign a use case to multiple reporting efforts."""
        affected = 0
        errors = []

        for effort_id in reporting_effort_ids:
            try:
                existing = await self.get_assignment(db, reporting_effort_id=effort_id, use_case_id=use_case_id)
                if not existing:
                    assignment = ReportingEffortUseCaseAssignment(
                        reporting_effort_id=effort_id,
                        use_case_id=use_case_id
                    )
                    db.add(assignment)
                    affected += 1
            except Exception as e:
                errors.append(f"Effort {effort_id}: {str(e)}")

        await db.commit()
        return BulkOperationResult(success=len(errors) == 0, affected_count=affected, errors=errors)

    async def bulk_remove(
        self,
        db: AsyncSession,
        *,
        reporting_effort_ids: List[int],
        use_case_id: int
    ) -> BulkOperationResult:
        """Remove a use case from multiple reporting efforts."""
        affected = 0
        errors = []

        for effort_id in reporting_effort_ids:
            try:
                assignment = await self.get_assignment(db, reporting_effort_id=effort_id, use_case_id=use_case_id)
                if assignment:
                    await db.delete(assignment)
                    affected += 1
            except Exception as e:
                errors.append(f"Effort {effort_id}: {str(e)}")

        await db.commit()
        return BulkOperationResult(success=len(errors) == 0, affected_count=affected, errors=errors)


# Create singleton instances
reporting_effort_usecase = CRUDReportingEffortUseCase(ReportingEffortUseCase)
reporting_effort_usecase_assignment = CRUDReportingEffortUseCaseAssignment()
