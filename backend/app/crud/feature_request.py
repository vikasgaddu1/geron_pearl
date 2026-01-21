"""CRUD operations for Feature Request / Bug Report."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.crud.base import BaseCRUD
from app.models.feature_request import FeatureRequest, FeatureRequestStatus, FeatureRequestCategory
from app.schemas.feature_request import (
    FeatureRequestCreate, FeatureRequestUpdate, FeatureRequestWithUser,
    FeatureRequestStatsResponse
)


class CRUDFeatureRequest(BaseCRUD[FeatureRequest, FeatureRequestCreate, FeatureRequestUpdate]):
    """CRUD operations for feature requests."""

    async def create_request(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        tenant_id: int,
        obj_in: FeatureRequestCreate
    ) -> FeatureRequest:
        """Create a new feature request."""
        db_obj = FeatureRequest(
            user_id=user_id,
            tenant_id=tenant_id,
            category=obj_in.category.value if hasattr(obj_in.category, 'value') else obj_in.category,
            title=obj_in.title,
            description=obj_in.description,
            status=FeatureRequestStatus.PENDING.value
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_user_requests(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[FeatureRequest]:
        """Get feature requests submitted by a specific user."""
        query = (
            select(FeatureRequest)
            .where(FeatureRequest.user_id == user_id)
            .order_by(FeatureRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_all_requests(
        self,
        db: AsyncSession,
        *,
        status: Optional[FeatureRequestStatus] = None,
        category: Optional[FeatureRequestCategory] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeatureRequestWithUser]:
        """Get all feature requests with user/tenant details (for super admin)."""
        from app.models.user import User
        from app.models.tenant import Tenant

        query = (
            select(FeatureRequest)
            .options(
                joinedload(FeatureRequest.user),
                joinedload(FeatureRequest.tenant)
            )
            .order_by(FeatureRequest.created_at.desc())
        )

        if status:
            status_value = status.value if hasattr(status, 'value') else status
            query = query.where(FeatureRequest.status == status_value)

        if category:
            category_value = category.value if hasattr(category, 'value') else category
            query = query.where(FeatureRequest.category == category_value)

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        requests = result.unique().scalars().all()

        # Convert to FeatureRequestWithUser
        result_list = []
        for req in requests:
            data = {
                "id": req.id,
                "tenant_id": req.tenant_id,
                "user_id": req.user_id,
                "category": req.category,
                "title": req.title,
                "description": req.description,
                "status": req.status,
                "admin_response": req.admin_response,
                "responded_at": req.responded_at,
                "created_at": req.created_at,
                "updated_at": req.updated_at,
                "user_name": req.user.username if req.user else None,
                "user_email": req.user.email if req.user else None,
                "tenant_name": req.tenant.name if req.tenant else None
            }
            result_list.append(FeatureRequestWithUser(**data))

        return result_list

    async def get_total_count(
        self,
        db: AsyncSession,
        *,
        status: Optional[FeatureRequestStatus] = None,
        category: Optional[FeatureRequestCategory] = None
    ) -> int:
        """Get total count of feature requests with optional filters."""
        query = select(func.count(FeatureRequest.id))

        if status:
            status_value = status.value if hasattr(status, 'value') else status
            query = query.where(FeatureRequest.status == status_value)

        if category:
            category_value = category.value if hasattr(category, 'value') else category
            query = query.where(FeatureRequest.category == category_value)

        result = await db.execute(query)
        return result.scalar() or 0

    async def get_stats(self, db: AsyncSession) -> FeatureRequestStatsResponse:
        """Get counts of feature requests by status."""
        # Count by status
        pending_query = select(func.count(FeatureRequest.id)).where(
            FeatureRequest.status == FeatureRequestStatus.PENDING.value
        )
        working_query = select(func.count(FeatureRequest.id)).where(
            FeatureRequest.status == FeatureRequestStatus.WORKING.value
        )
        done_query = select(func.count(FeatureRequest.id)).where(
            FeatureRequest.status == FeatureRequestStatus.DONE.value
        )
        total_query = select(func.count(FeatureRequest.id))

        pending_result = await db.execute(pending_query)
        working_result = await db.execute(working_query)
        done_result = await db.execute(done_query)
        total_result = await db.execute(total_query)

        return FeatureRequestStatsResponse(
            pending=pending_result.scalar() or 0,
            working=working_result.scalar() or 0,
            done=done_result.scalar() or 0,
            total=total_result.scalar() or 0
        )

    async def update_request(
        self,
        db: AsyncSession,
        *,
        request_id: int,
        obj_in: FeatureRequestUpdate
    ) -> Optional[FeatureRequest]:
        """Update a feature request (for super admin)."""
        db_obj = await self.get(db, id=request_id)
        if not db_obj:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)

        # If admin_response is being set, update responded_at
        if "admin_response" in update_data and update_data["admin_response"]:
            update_data["responded_at"] = datetime.utcnow()

        # Convert enum values
        if "status" in update_data and update_data["status"]:
            update_data["status"] = (
                update_data["status"].value
                if hasattr(update_data["status"], 'value')
                else update_data["status"]
            )

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_request_with_user(
        self,
        db: AsyncSession,
        *,
        request_id: int
    ) -> Optional[FeatureRequestWithUser]:
        """Get a single feature request with user/tenant details."""
        query = (
            select(FeatureRequest)
            .options(
                joinedload(FeatureRequest.user),
                joinedload(FeatureRequest.tenant)
            )
            .where(FeatureRequest.id == request_id)
        )

        result = await db.execute(query)
        req = result.unique().scalar_one_or_none()

        if not req:
            return None

        return FeatureRequestWithUser(
            id=req.id,
            tenant_id=req.tenant_id,
            user_id=req.user_id,
            category=req.category,
            title=req.title,
            description=req.description,
            status=req.status,
            admin_response=req.admin_response,
            responded_at=req.responded_at,
            created_at=req.created_at,
            updated_at=req.updated_at,
            user_name=req.user.username if req.user else None,
            user_email=req.user.email if req.user else None,
            tenant_name=req.tenant.name if req.tenant else None
        )


# Singleton instance
feature_request = CRUDFeatureRequest(FeatureRequest)
