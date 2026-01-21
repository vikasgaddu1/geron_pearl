"""CRUD operations for AccessRequest."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.crud.base import BaseCRUD
from app.models.access_request import AccessRequest, AccessRequestType, AccessRequestStatus
from app.models.user import User
from app.models.study import Study
from app.models.study_responsible_user import StudyResponsibleUser
from app.schemas.access_request import AccessRequestCreate, AccessRequestWithDetails


class AccessRequestCRUD(BaseCRUD[AccessRequest, AccessRequestCreate, AccessRequestCreate]):
    """CRUD operations for access requests."""

    async def create_request(
        self,
        db: AsyncSession,
        *,
        requester_id: int,
        study_id: int,
        request_type: AccessRequestType,
        request_reason: Optional[str] = None
    ) -> AccessRequest:
        """Create a new access request."""
        db_obj = AccessRequest(
            requester_id=requester_id,
            study_id=study_id,
            request_type=request_type.value,
            status=AccessRequestStatus.PENDING.value,
            request_reason=request_reason
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_pending_request(
        self,
        db: AsyncSession,
        *,
        requester_id: int,
        study_id: int,
        request_type: AccessRequestType
    ) -> Optional[AccessRequest]:
        """Check if user already has a pending request for this study/type."""
        result = await db.execute(
            select(AccessRequest).where(
                and_(
                    AccessRequest.requester_id == requester_id,
                    AccessRequest.study_id == study_id,
                    AccessRequest.request_type == request_type.value,
                    AccessRequest.status == AccessRequestStatus.PENDING.value
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_with_details(
        self,
        db: AsyncSession,
        *,
        request_id: int
    ) -> Optional[AccessRequest]:
        """Get a request with related objects loaded."""
        result = await db.execute(
            select(AccessRequest)
            .where(AccessRequest.id == request_id)
            .options(
                joinedload(AccessRequest.requester),
                joinedload(AccessRequest.study),
                joinedload(AccessRequest.resolved_by)
            )
        )
        return result.unique().scalar_one_or_none()

    async def get_requests_for_approver(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        is_admin: bool,
        status_filter: Optional[AccessRequestStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[AccessRequestWithDetails]:
        """
        Get access requests that this user can approve.

        - Admins see all requests
        - Responsible users see requests for their studies
        """
        query = (
            select(AccessRequest)
            .options(
                joinedload(AccessRequest.requester),
                joinedload(AccessRequest.study),
                joinedload(AccessRequest.resolved_by)
            )
        )

        if not is_admin:
            # Get study IDs where user is responsible
            subquery = select(StudyResponsibleUser.study_id).where(
                StudyResponsibleUser.user_id == user_id
            )
            query = query.where(AccessRequest.study_id.in_(subquery))

        if status_filter:
            query = query.where(AccessRequest.status == status_filter.value)

        query = query.order_by(AccessRequest.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        requests = result.unique().scalars().all()

        # Convert to response schema
        return [self._to_details(req) for req in requests]

    async def get_requests_by_requester(
        self,
        db: AsyncSession,
        *,
        requester_id: int,
        status_filter: Optional[AccessRequestStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[AccessRequestWithDetails]:
        """Get all access requests made by a user."""
        query = (
            select(AccessRequest)
            .options(
                joinedload(AccessRequest.requester),
                joinedload(AccessRequest.study),
                joinedload(AccessRequest.resolved_by)
            )
            .where(AccessRequest.requester_id == requester_id)
        )

        if status_filter:
            query = query.where(AccessRequest.status == status_filter.value)

        query = query.order_by(AccessRequest.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        requests = result.unique().scalars().all()

        return [self._to_details(req) for req in requests]

    async def get_pending_count_for_approver(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        is_admin: bool
    ) -> int:
        """Count pending requests that this user can approve."""
        query = select(func.count(AccessRequest.id)).where(
            AccessRequest.status == AccessRequestStatus.PENDING.value
        )

        if not is_admin:
            subquery = select(StudyResponsibleUser.study_id).where(
                StudyResponsibleUser.user_id == user_id
            )
            query = query.where(AccessRequest.study_id.in_(subquery))

        result = await db.execute(query)
        return result.scalar() or 0

    async def approve_request(
        self,
        db: AsyncSession,
        *,
        request_id: int,
        resolved_by_id: int
    ) -> Optional[AccessRequest]:
        """Approve an access request."""
        request = await self.get(db, id=request_id)
        if not request or request.status != AccessRequestStatus.PENDING.value:
            return None

        request.status = AccessRequestStatus.APPROVED.value
        request.resolved_by_id = resolved_by_id
        request.resolved_at = datetime.utcnow()

        await db.commit()
        await db.refresh(request)
        return request

    async def deny_request(
        self,
        db: AsyncSession,
        *,
        request_id: int,
        resolved_by_id: int,
        denial_reason: Optional[str] = None
    ) -> Optional[AccessRequest]:
        """Deny an access request."""
        request = await self.get(db, id=request_id)
        if not request or request.status != AccessRequestStatus.PENDING.value:
            return None

        request.status = AccessRequestStatus.DENIED.value
        request.resolved_by_id = resolved_by_id
        request.resolved_at = datetime.utcnow()
        request.denial_reason = denial_reason

        await db.commit()
        await db.refresh(request)
        return request

    async def get_approvers_for_study(
        self,
        db: AsyncSession,
        *,
        study_id: int
    ) -> List[int]:
        """Get user IDs of all users who can approve requests for a study."""
        # Get responsible user IDs
        result = await db.execute(
            select(StudyResponsibleUser.user_id).where(
                StudyResponsibleUser.study_id == study_id
            )
        )
        responsible_ids = list(result.scalars().all())

        # Get admin user IDs
        result = await db.execute(
            select(User.id).where(User.is_admin == True)
        )
        admin_ids = list(result.scalars().all())

        # Combine and deduplicate
        return list(set(responsible_ids + admin_ids))

    def _to_details(self, request: AccessRequest) -> AccessRequestWithDetails:
        """Convert AccessRequest model to AccessRequestWithDetails schema."""
        return AccessRequestWithDetails(
            id=request.id,
            requester_id=request.requester_id,
            study_id=request.study_id,
            request_type=request.request_type,
            status=request.status,
            request_reason=request.request_reason,
            resolved_by_id=request.resolved_by_id,
            resolved_at=request.resolved_at,
            denial_reason=request.denial_reason,
            created_at=request.created_at,
            updated_at=request.updated_at,
            requester_username=request.requester.username,
            requester_email=request.requester.email,
            study_label=request.study.study_label,
            resolved_by_username=request.resolved_by.username if request.resolved_by else None
        )


# Singleton instance
access_request = AccessRequestCRUD(AccessRequest)
