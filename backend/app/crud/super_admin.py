"""CRUD operations for SuperAdmin model."""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.super_admin import SuperAdmin
from app.schemas.super_admin import SuperAdminCreate, SuperAdminUpdate
from app.core.security import get_password_hash


class SuperAdminCRUD:
    """CRUD operations for SuperAdmin model."""
    
    async def create(self, db: AsyncSession, *, obj_in: SuperAdminCreate) -> SuperAdmin:
        """Create a new super admin."""
        db_obj = SuperAdmin(
            email=obj_in.email,
            password_hash=get_password_hash(obj_in.password),
            name=obj_in.name,
            mfa_enabled=False,
            is_active=True,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[SuperAdmin]:
        """Get a super admin by ID."""
        result = await db.execute(select(SuperAdmin).where(SuperAdmin.id == id))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[SuperAdmin]:
        """Get a super admin by email."""
        result = await db.execute(select(SuperAdmin).where(SuperAdmin.email == email))
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[SuperAdmin]:
        """Get multiple super admins with pagination."""
        result = await db.execute(
            select(SuperAdmin).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_active(self, db: AsyncSession) -> List[SuperAdmin]:
        """Get all active super admins."""
        result = await db.execute(
            select(SuperAdmin).where(SuperAdmin.is_active == True)
        )
        return list(result.scalars().all())
    
    async def update(
        self, db: AsyncSession, *, db_obj: SuperAdmin, obj_in: SuperAdminUpdate
    ) -> SuperAdmin:
        """Update an existing super admin."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Hash password if being updated
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update_last_login(
        self, db: AsyncSession, *, admin_id: int, ip_address: Optional[str] = None
    ) -> Optional[SuperAdmin]:
        """Update last login timestamp and IP."""
        admin = await self.get(db, id=admin_id)
        if not admin:
            return None
        
        admin.last_login_at = datetime.utcnow()
        if ip_address:
            admin.last_login_ip = ip_address
        admin.failed_login_attempts = 0
        admin.locked_until = None
        
        await db.commit()
        await db.refresh(admin)
        return admin
    
    async def record_failed_login(
        self, db: AsyncSession, *, admin_id: int
    ) -> Optional[SuperAdmin]:
        """Record a failed login attempt."""
        admin = await self.get(db, id=admin_id)
        if not admin:
            return None
        
        admin.increment_failed_login()
        await db.commit()
        await db.refresh(admin)
        return admin
    
    async def enable_mfa(
        self, db: AsyncSession, *, admin_id: int, mfa_secret: str, backup_codes: str
    ) -> Optional[SuperAdmin]:
        """Enable MFA for a super admin."""
        admin = await self.get(db, id=admin_id)
        if not admin:
            return None
        
        admin.mfa_enabled = True
        admin.mfa_secret = mfa_secret
        admin.mfa_backup_codes = backup_codes
        
        await db.commit()
        await db.refresh(admin)
        return admin
    
    async def disable_mfa(self, db: AsyncSession, *, admin_id: int) -> Optional[SuperAdmin]:
        """Disable MFA for a super admin."""
        admin = await self.get(db, id=admin_id)
        if not admin:
            return None
        
        admin.mfa_enabled = False
        admin.mfa_secret = None
        admin.mfa_backup_codes = None
        
        await db.commit()
        await db.refresh(admin)
        return admin
    
    async def delete(self, db: AsyncSession, *, id: int) -> Optional[SuperAdmin]:
        """Delete a super admin."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
    
    async def count(self, db: AsyncSession) -> int:
        """Count total super admins."""
        from sqlalchemy import func
        result = await db.execute(select(func.count(SuperAdmin.id)))
        return result.scalar() or 0


# Create a global instance
super_admin = SuperAdminCRUD()
