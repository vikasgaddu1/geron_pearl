"""CRUD operations for UserStudyRole."""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import BaseCRUD
from app.models.user_study_role import UserStudyRole, StudyRole
from app.models.user import User
from app.models.study import Study
from app.schemas.user_study_role import UserStudyRoleCreate, UserStudyRoleUpdate


class UserStudyRoleCRUD(BaseCRUD[UserStudyRole, UserStudyRoleCreate, UserStudyRoleUpdate]):
    """CRUD operations for UserStudyRole."""

    async def get_by_user_and_study(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        study_id: int
    ) -> Optional[UserStudyRole]:
        """Get a user's role for a specific study."""
        result = await db.execute(
            select(UserStudyRole).where(
                and_(
                    UserStudyRole.user_id == user_id,
                    UserStudyRole.study_id == study_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int
    ) -> List[UserStudyRole]:
        """Get all study roles for a user."""
        result = await db.execute(
            select(UserStudyRole)
            .where(UserStudyRole.user_id == user_id)
            .options(selectinload(UserStudyRole.study))
        )
        return list(result.scalars().all())

    async def get_by_study(
        self, 
        db: AsyncSession, 
        *, 
        study_id: int
    ) -> List[UserStudyRole]:
        """Get all user roles for a study."""
        result = await db.execute(
            select(UserStudyRole)
            .where(UserStudyRole.study_id == study_id)
            .options(selectinload(UserStudyRole.user))
        )
        return list(result.scalars().all())

    async def get_study_members(
        self, 
        db: AsyncSession, 
        *, 
        study_id: int,
        include_defaults: bool = True
    ) -> List[dict]:
        """
        Get all members for a study with their roles.
        
        Args:
            db: Database session
            study_id: Study ID
            include_defaults: If True, include users with default viewer access
            
        Returns:
            List of member dictionaries with user info and role
        """
        # Get explicit role assignments for this study
        explicit_roles = await self.get_by_study(db, study_id=study_id)
        explicit_user_ids = {r.user_id for r in explicit_roles}
        
        members = []
        
        # Add explicit role assignments
        for role_assignment in explicit_roles:
            user = role_assignment.user
            members.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": role_assignment.role,
                "is_admin": user.is_admin,
                "is_explicit_assignment": True,
                "assigned_at": role_assignment.created_at
            })
        
        if include_defaults:
            # Get all active users who don't have explicit assignments
            result = await db.execute(
                select(User).where(
                    and_(
                        User.is_active == True,
                        User.id.notin_(explicit_user_ids) if explicit_user_ids else True
                    )
                )
            )
            other_users = result.scalars().all()
            
            for user in other_users:
                # Admins have full access everywhere (shown as Global Admin in UI)
                # Non-admins without explicit roles have implicit read-only access
                effective_role = "RESPONSIBLE" if user.is_admin else None

                members.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": effective_role,
                    "is_admin": user.is_admin,
                    "is_explicit_assignment": False,
                    "assigned_at": None
                })
        
        return members

    async def assign_role(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        study_id: int, 
        role: StudyRole
    ) -> UserStudyRole:
        """
        Assign or update a user's role in a study.
        
        Creates a new assignment if one doesn't exist, otherwise updates.
        """
        existing = await self.get_by_user_and_study(db, user_id=user_id, study_id=study_id)
        
        if existing:
            # Update existing role
            existing.role = role
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Create new role assignment
            obj_in = UserStudyRoleCreate(user_id=user_id, study_id=study_id, role=role)
            return await self.create(db, obj_in=obj_in)

    async def remove_role(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        study_id: int
    ) -> Optional[UserStudyRole]:
        """
        Remove a user's role assignment from a study.
        
        User will revert to default viewer access.
        """
        existing = await self.get_by_user_and_study(db, user_id=user_id, study_id=study_id)
        
        if existing:
            await db.delete(existing)
            await db.commit()
            return existing
        
        return None

    async def get_users_with_role(
        self, 
        db: AsyncSession, 
        *, 
        study_id: int, 
        role: StudyRole
    ) -> List[User]:
        """Get all users with a specific role in a study."""
        result = await db.execute(
            select(User)
            .join(UserStudyRole, User.id == UserStudyRole.user_id)
            .where(
                and_(
                    UserStudyRole.study_id == study_id,
                    UserStudyRole.role == role
                )
            )
        )
        return list(result.scalars().all())

    async def get_leads_for_study(
        self,
        db: AsyncSession,
        *,
        study_id: int
    ) -> List[User]:
        """
        DEPRECATED: Use study_responsible_user CRUD instead.
        Get all users with LEAD role in a study (excluding global admins).
        Note: LEAD role is no longer used - use responsible users system.
        """
        # This method is kept for backward compatibility but should not be used
        # Use study_responsible_user.get_by_study instead
        return []

    async def bulk_assign_roles(
        self, 
        db: AsyncSession, 
        *, 
        study_id: int, 
        assignments: List[dict]
    ) -> List[UserStudyRole]:
        """
        Bulk assign roles to a study.
        
        Args:
            db: Database session
            study_id: Study ID
            assignments: List of {"user_id": int, "role": StudyRole}
            
        Returns:
            List of created/updated role assignments
        """
        results = []
        for assignment in assignments:
            role_assignment = await self.assign_role(
                db,
                user_id=assignment["user_id"],
                study_id=study_id,
                role=assignment["role"]
            )
            results.append(role_assignment)
        
        return results


# Singleton instance
user_study_role = UserStudyRoleCRUD(UserStudyRole)

