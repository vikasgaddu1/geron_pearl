"""CRUD operations for ItemCompletionRecord."""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import BaseCRUD
from app.models.item_completion_record import ItemCompletionRecord
from app.models.user import User
from app.models.study import Study
from app.schemas.item_completion_record import (
    ItemCompletionRecordCreate,
    WeeklyVelocity,
    ProgrammerVelocity,
    VelocityByItemType
)


class ItemCompletionRecordCRUD(BaseCRUD[ItemCompletionRecord, ItemCompletionRecordCreate, ItemCompletionRecordCreate]):
    """CRUD operations for ItemCompletionRecord with velocity calculations."""

    async def record_completion(
        self,
        db: AsyncSession,
        *,
        tracker_id: int,
        study_id: int,
        item_type: str,
        item_subtype: str,
        item_code: str,
        complexity: int,
        production_programmer_id: Optional[int],
        programmer_experience_level: Optional[str] = None,
        programmer_allocation_percent: Optional[int] = None,
        had_sister_study: bool = False,
        sister_study_id: Optional[int] = None
    ) -> ItemCompletionRecord:
        """
        Record a completion event.
        
        Called automatically when tracker production_status becomes 'completed'.
        """
        now = datetime.utcnow()
        iso_cal = now.isocalendar()
        
        record = ItemCompletionRecord(
            tracker_id=tracker_id,
            study_id=study_id,
            item_type=item_type,
            item_subtype=item_subtype,
            item_code=item_code,
            complexity=complexity,
            production_programmer_id=production_programmer_id,
            programmer_experience_level=programmer_experience_level,
            programmer_allocation_percent=programmer_allocation_percent,
            completed_at=now,
            iso_week=iso_cal.week,
            iso_year=iso_cal.year,
            had_sister_study=had_sister_study,
            sister_study_id=sister_study_id
        )
        
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    async def get_programmer_velocity(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        study_id: Optional[int] = None,
        weeks: int = 8
    ) -> Optional[ProgrammerVelocity]:
        """
        Calculate velocity for a programmer over the specified weeks.
        
        Returns None if no completion data exists.
        """
        # Calculate date range
        now = datetime.utcnow()
        start_date = now - timedelta(weeks=weeks)
        
        # Build query
        query = (
            select(
                ItemCompletionRecord.iso_year,
                ItemCompletionRecord.iso_week,
                func.sum(ItemCompletionRecord.complexity).label('complexity_total'),
                func.count(ItemCompletionRecord.id).label('item_count'),
                func.avg(ItemCompletionRecord.complexity).label('complexity_avg')
            )
            .where(
                and_(
                    ItemCompletionRecord.production_programmer_id == user_id,
                    ItemCompletionRecord.completed_at >= start_date
                )
            )
            .group_by(
                ItemCompletionRecord.iso_year,
                ItemCompletionRecord.iso_week
            )
            .order_by(
                ItemCompletionRecord.iso_year.desc(),
                ItemCompletionRecord.iso_week.desc()
            )
        )
        
        if study_id:
            query = query.where(ItemCompletionRecord.study_id == study_id)
        
        result = await db.execute(query)
        rows = result.all()
        
        if not rows:
            return None
        
        # Get user info
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        # Get study info if specified
        study_label = None
        if study_id:
            study_result = await db.execute(select(Study).where(Study.id == study_id))
            study_obj = study_result.scalar_one_or_none()
            if study_obj:
                study_label = study_obj.study_label
        
        # Build weekly data
        weekly_data = [
            WeeklyVelocity(
                iso_year=row.iso_year,
                iso_week=row.iso_week,
                complexity_points=row.complexity_total,
                item_count=row.item_count,
                avg_complexity=float(row.complexity_avg) if row.complexity_avg else 0
            )
            for row in rows
        ]
        
        # Calculate totals
        total_complexity = sum(w.complexity_points for w in weekly_data)
        total_items = sum(w.item_count for w in weekly_data)
        data_points = len(weekly_data)
        
        # Determine confidence
        if data_points >= 8:
            confidence = "high"
        elif data_points >= 4:
            confidence = "medium"
        else:
            confidence = "low"
        
        return ProgrammerVelocity(
            user_id=user_id,
            username=user.username if user else "Unknown",
            study_id=study_id,
            study_label=study_label,
            weeks_analyzed=weeks,
            total_complexity_points=total_complexity,
            total_items_completed=total_items,
            avg_points_per_week=total_complexity / weeks if weeks > 0 else 0,
            weekly_data=weekly_data,
            data_points=data_points,
            confidence=confidence
        )

    async def get_study_velocity(
        self,
        db: AsyncSession,
        *,
        study_id: int,
        weeks: int = 12
    ) -> dict:
        """
        Calculate team velocity for a study.
        """
        now = datetime.utcnow()
        start_date = now - timedelta(weeks=weeks)
        
        # Get weekly totals for the study
        query = (
            select(
                ItemCompletionRecord.iso_year,
                ItemCompletionRecord.iso_week,
                func.sum(ItemCompletionRecord.complexity).label('complexity_total'),
                func.count(ItemCompletionRecord.id).label('item_count')
            )
            .where(
                and_(
                    ItemCompletionRecord.study_id == study_id,
                    ItemCompletionRecord.completed_at >= start_date
                )
            )
            .group_by(
                ItemCompletionRecord.iso_year,
                ItemCompletionRecord.iso_week
            )
            .order_by(
                ItemCompletionRecord.iso_year.desc(),
                ItemCompletionRecord.iso_week.desc()
            )
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        weekly_data = [
            {
                "iso_year": row.iso_year,
                "iso_week": row.iso_week,
                "complexity_points": row.complexity_total,
                "item_count": row.item_count
            }
            for row in rows
        ]
        
        total_complexity = sum(w["complexity_points"] for w in weekly_data)
        total_items = sum(w["item_count"] for w in weekly_data)
        
        return {
            "study_id": study_id,
            "weeks_analyzed": weeks,
            "total_complexity_points": total_complexity,
            "total_items_completed": total_items,
            "avg_points_per_week": total_complexity / weeks if weeks > 0 else 0,
            "weekly_data": weekly_data
        }

    async def get_velocity_by_item_type(
        self,
        db: AsyncSession,
        *,
        study_id: int,
        weeks: int = 12
    ) -> List[VelocityByItemType]:
        """
        Get velocity breakdown by item subtype for a study.
        """
        now = datetime.utcnow()
        start_date = now - timedelta(weeks=weeks)
        
        query = (
            select(
                ItemCompletionRecord.item_subtype,
                func.avg(ItemCompletionRecord.complexity).label('complexity_avg'),
                func.count(ItemCompletionRecord.id).label('items_completed'),
                func.sum(ItemCompletionRecord.complexity).label('complexity_total')
            )
            .where(
                and_(
                    ItemCompletionRecord.study_id == study_id,
                    ItemCompletionRecord.completed_at >= start_date
                )
            )
            .group_by(ItemCompletionRecord.item_subtype)
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        return [
            VelocityByItemType(
                item_subtype=row.item_subtype,
                complexity_avg=float(row.complexity_avg) if row.complexity_avg else 0,
                items_completed=row.items_completed,
                complexity_total=row.complexity_total
            )
            for row in rows
        ]

    async def get_completion_count_by_week(
        self,
        db: AsyncSession,
        *,
        study_id: int,
        weeks: int = 12
    ) -> List[dict]:
        """
        Get completion count by week for burndown/burnup charts.
        """
        now = datetime.utcnow()
        start_date = now - timedelta(weeks=weeks)
        
        query = (
            select(
                ItemCompletionRecord.iso_year,
                ItemCompletionRecord.iso_week,
                ItemCompletionRecord.item_subtype,
                func.count(ItemCompletionRecord.id).label('count'),
                func.sum(ItemCompletionRecord.complexity).label('complexity_sum')
            )
            .where(
                and_(
                    ItemCompletionRecord.study_id == study_id,
                    ItemCompletionRecord.completed_at >= start_date
                )
            )
            .group_by(
                ItemCompletionRecord.iso_year,
                ItemCompletionRecord.iso_week,
                ItemCompletionRecord.item_subtype
            )
            .order_by(
                ItemCompletionRecord.iso_year,
                ItemCompletionRecord.iso_week
            )
        )
        
        result = await db.execute(query)
        return [
            {
                "iso_year": row.iso_year,
                "iso_week": row.iso_week,
                "item_subtype": row.item_subtype,
                "count": row.count,
                "complexity_sum": row.complexity_sum
            }
            for row in result.all()
        ]

    async def check_completion_exists(
        self,
        db: AsyncSession,
        *,
        tracker_id: int
    ) -> bool:
        """Check if a completion record already exists for a tracker."""
        result = await db.execute(
            select(ItemCompletionRecord.id)
            .where(ItemCompletionRecord.tracker_id == tracker_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None


# Singleton instance
item_completion_record = ItemCompletionRecordCRUD(ItemCompletionRecord)

