from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.exc import IntegrityError
from app.models.user import User, AuthProvider
from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
from app.models.user_study_role import UserStudyRole
from app.models.tracker_comment import TrackerComment
from app.models.notification import Notification
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserCRUD:
    async def get(self, db: AsyncSession, id: int) -> Optional[User]:
        result = await db.execute(select(User).filter(User.id == id))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[User]:
        result = await db.execute(
            select(User).offset(skip).limit(limit).order_by(User.username)
        )
        return result.scalars().all()

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate, tenant_id: int = None) -> User:
        # Check if username already exists (within the same tenant)
        existing = await self.get_by_username(db, username=obj_in.username)
        if existing:
            raise IntegrityError(
                params=None,
                orig=Exception(f"Username '{obj_in.username}' already exists"),
                statement=None
            )

        # Check if email already exists
        existing_email = await self.get_by_email(db, email=obj_in.email)
        if existing_email:
            raise IntegrityError(
                params=None,
                orig=Exception(f"Email '{obj_in.email}' already exists"),
                statement=None
            )

        # Hash password
        password_hash = get_password_hash(obj_in.password)

        # Use provided tenant_id or default to 1
        user_tenant_id = tenant_id if tenant_id is not None else 1

        db_obj = User(
            tenant_id=user_tenant_id,
            username=obj_in.username,
            email=obj_in.email,
            password_hash=password_hash,
            is_admin=obj_in.is_admin,
            department=obj_in.department,
            auth_provider=AuthProvider.local,
            is_active=True
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: User, obj_in: UserUpdate
    ) -> User:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # If username is being updated, check for duplicates
        if "username" in update_data and update_data["username"] != db_obj.username:
            existing = await self.get_by_username(db, username=update_data["username"])
            if existing:
                raise IntegrityError(
                    params=None,
                    orig=Exception(f"Username '{update_data['username']}' already exists"),
                    statement=None
                )
        
        # If email is being updated, check for duplicates
        if "email" in update_data and update_data["email"] != db_obj.email:
            existing_email = await self.get_by_email(db, email=update_data["email"])
            if existing_email:
                raise IntegrityError(
                    params=None,
                    orig=Exception(f"Email '{update_data['email']}' already exists"),
                    statement=None
                )
            db_obj.email = update_data["email"]
            update_data.pop("email")  # Remove from update_data since we handled it
        
        # If password is being updated, hash it
        if "password" in update_data and update_data["password"]:
            db_obj.password_hash = get_password_hash(update_data["password"])
            update_data.pop("password")  # Remove from update_data since we handled it
        
        # Update other fields
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> User:
        result = await db.execute(select(User).filter(User.id == id))
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def get_usage_references(self, db: AsyncSession, *, id: int) -> Dict[str, Any]:
        """
        Check if a user is being referenced by other entities.

        Returns a dictionary with:
        - tracker_assignments: count of tracker assignments (prod or QC)
        - study_roles: count of study role assignments
        - comments: count of comments created by this user
        - is_only_admin: whether this is the only admin user
        """
        references = {
            "tracker_assignments": 0,
            "study_roles": 0,
            "comments": 0,
            "is_only_admin": False,
        }

        # Check tracker assignments (production or QC programmer)
        result = await db.execute(
            select(func.count(ReportingEffortItemTracker.id))
            .where(
                or_(
                    ReportingEffortItemTracker.production_programmer_id == id,
                    ReportingEffortItemTracker.qc_programmer_id == id
                )
            )
        )
        references["tracker_assignments"] = result.scalar() or 0

        # Check study role assignments
        result = await db.execute(
            select(func.count(UserStudyRole.id))
            .where(UserStudyRole.user_id == id)
        )
        references["study_roles"] = result.scalar() or 0

        # Check comments created by this user
        result = await db.execute(
            select(func.count(TrackerComment.id))
            .where(TrackerComment.user_id == id)
        )
        references["comments"] = result.scalar() or 0

        # Check if this is the only admin
        user = await self.get(db, id=id)
        if user and user.is_admin:
            result = await db.execute(
                select(func.count(User.id))
                .where(User.is_admin == True, User.id != id)
            )
            other_admins = result.scalar() or 0
            references["is_only_admin"] = other_admins == 0

        return references

    def has_blocking_references(self, references: Dict[str, Any]) -> bool:
        """Check if any blocking references exist."""
        return (
            references["tracker_assignments"] > 0 or
            references["study_roles"] > 0 or
            references["is_only_admin"]
        )

    def format_reference_error(self, references: Dict[str, Any]) -> str:
        """Format reference error message."""
        messages = []
        if references["is_only_admin"]:
            messages.append("this is the only admin user")
        if references["tracker_assignments"] > 0:
            messages.append(f"assigned to {references['tracker_assignments']} tracker(s) as programmer")
        if references["study_roles"] > 0:
            messages.append(f"has {references['study_roles']} study role assignment(s)")
        return f"Cannot delete user: {'; '.join(messages)}. Remove these assignments first."

    async def get_available_for_assignment(
        self, db: AsyncSession, *, tenant_id: int
    ) -> List[User]:
        """
        Get all non-admin, active users from a tenant that can be assigned study roles.

        Args:
            db: Database session
            tenant_id: Tenant ID to filter users by

        Returns:
            List of users available for study role assignment
        """
        result = await db.execute(
            select(User)
            .where(
                User.tenant_id == tenant_id,
                User.is_active == True,
                User.is_admin == False,
            )
            .order_by(User.username)
        )
        return list(result.scalars().all())


user = UserCRUD()