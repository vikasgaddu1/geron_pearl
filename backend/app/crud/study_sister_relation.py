"""CRUD operations for StudySisterRelation."""

from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import BaseCRUD
from app.models.study_sister_relation import StudySisterRelation
from app.models.study import Study
from app.schemas.study_sister_relation import (
    StudySisterRelationCreate,
    StudySisterRelationUpdate,
    SisterStudyInfo
)


class StudySisterRelationCRUD(BaseCRUD[StudySisterRelation, StudySisterRelationCreate, StudySisterRelationUpdate]):
    """CRUD operations for StudySisterRelation."""

    async def get_by_study_pair(
        self,
        db: AsyncSession,
        *,
        primary_study_id: int,
        sister_study_id: int
    ) -> Optional[StudySisterRelation]:
        """Get relation between two specific studies."""
        result = await db.execute(
            select(StudySisterRelation)
            .where(
                StudySisterRelation.primary_study_id == primary_study_id,
                StudySisterRelation.sister_study_id == sister_study_id
            )
        )
        return result.scalar_one_or_none()

    async def get_sisters_for_study(
        self,
        db: AsyncSession,
        *,
        study_id: int
    ) -> List[StudySisterRelation]:
        """
        Get all sister studies that this study can reuse code FROM.
        """
        result = await db.execute(
            select(StudySisterRelation)
            .where(StudySisterRelation.primary_study_id == study_id)
            .options(selectinload(StudySisterRelation.sister_study))
        )
        return list(result.scalars().all())

    async def get_studies_reusing_from(
        self,
        db: AsyncSession,
        *,
        study_id: int
    ) -> List[StudySisterRelation]:
        """
        Get all studies that reuse code FROM this study.
        """
        result = await db.execute(
            select(StudySisterRelation)
            .where(StudySisterRelation.sister_study_id == study_id)
            .options(selectinload(StudySisterRelation.primary_study))
        )
        return list(result.scalars().all())

    async def get_all_relations_for_study(
        self,
        db: AsyncSession,
        *,
        study_id: int
    ) -> dict:
        """
        Get all sister study relationships for a study.
        
        Returns both studies it can reuse FROM and studies that reuse FROM it.
        """
        # Studies this study can reuse FROM
        can_reuse_from = await self.get_sisters_for_study(db, study_id=study_id)
        
        # Studies that reuse FROM this study
        provides_code_to = await self.get_studies_reusing_from(db, study_id=study_id)
        
        # Get the primary study info
        study_result = await db.execute(
            select(Study).where(Study.id == study_id)
        )
        study = study_result.scalar_one_or_none()
        
        return {
            "study_id": study_id,
            "study_label": study.study_label if study else "Unknown",
            "can_reuse_from": [
                SisterStudyInfo(
                    study_id=r.sister_study_id,
                    study_label=r.sister_study.study_label,
                    code_reuse_percentage=r.code_reuse_percentage,
                    effort_reduction_factor=r.effort_reduction_factor,
                    reusable_components=r.reusable_components,
                    notes=r.notes
                )
                for r in can_reuse_from
            ],
            "provides_code_to": [
                SisterStudyInfo(
                    study_id=r.primary_study_id,
                    study_label=r.primary_study.study_label,
                    code_reuse_percentage=r.code_reuse_percentage,
                    effort_reduction_factor=r.effort_reduction_factor,
                    reusable_components=r.reusable_components,
                    notes=r.notes
                )
                for r in provides_code_to
            ]
        }

    async def create_relation(
        self,
        db: AsyncSession,
        *,
        primary_study_id: int,
        sister_study_id: int,
        code_reuse_percentage: int = 50,
        notes: Optional[str] = None,
        reusable_components: Optional[str] = None
    ) -> StudySisterRelation:
        """
        Create a new sister study relationship.
        
        Raises ValueError if:
        - Studies are the same
        - Relation already exists
        """
        if primary_study_id == sister_study_id:
            raise ValueError("A study cannot be its own sister study")
        
        # Check if relation already exists
        existing = await self.get_by_study_pair(
            db, 
            primary_study_id=primary_study_id,
            sister_study_id=sister_study_id
        )
        if existing:
            raise ValueError("Sister study relation already exists")
        
        obj_in = StudySisterRelationCreate(
            primary_study_id=primary_study_id,
            sister_study_id=sister_study_id,
            code_reuse_percentage=code_reuse_percentage,
            notes=notes,
            reusable_components=reusable_components
        )
        return await self.create(db, obj_in=obj_in)

    async def get_best_sister_for_study(
        self,
        db: AsyncSession,
        *,
        study_id: int
    ) -> Optional[StudySisterRelation]:
        """
        Get the sister study with highest code reuse percentage.
        
        Used when calculating estimates - uses the best available sister.
        """
        result = await db.execute(
            select(StudySisterRelation)
            .where(StudySisterRelation.primary_study_id == study_id)
            .order_by(StudySisterRelation.code_reuse_percentage.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def calculate_adjusted_estimate(
        self,
        db: AsyncSession,
        *,
        study_id: int,
        base_estimate: float
    ) -> dict:
        """
        Calculate adjusted estimate accounting for best sister study.
        
        Returns dict with original estimate, adjusted estimate, and details.
        """
        best_sister = await self.get_best_sister_for_study(db, study_id=study_id)
        
        if not best_sister:
            return {
                "original_estimate": base_estimate,
                "adjusted_estimate": base_estimate,
                "reduction_percentage": 0,
                "has_sister_study": False,
                "sister_study_id": None,
                "code_reuse_percentage": 0
            }
        
        adjusted = best_sister.calculate_adjusted_estimate(base_estimate)
        reduction_pct = ((base_estimate - adjusted) / base_estimate) * 100 if base_estimate > 0 else 0
        
        return {
            "original_estimate": base_estimate,
            "adjusted_estimate": adjusted,
            "reduction_percentage": round(reduction_pct, 1),
            "has_sister_study": True,
            "sister_study_id": best_sister.sister_study_id,
            "code_reuse_percentage": best_sister.code_reuse_percentage
        }


# Singleton instance
study_sister_relation = StudySisterRelationCRUD(StudySisterRelation)

