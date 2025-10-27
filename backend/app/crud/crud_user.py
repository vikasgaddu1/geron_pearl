from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate


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

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        # Check if username already exists
        existing = await self.get_by_username(db, username=obj_in.username)
        if existing:
            raise IntegrityError(
                params=None,
                orig=Exception(f"Username '{obj_in.username}' already exists"),
                statement=None
            )
        
        db_obj = User(
            username=obj_in.username,
            role=obj_in.role
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


user = UserCRUD()