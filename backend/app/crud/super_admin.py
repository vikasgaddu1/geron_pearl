"""CRUD operations for Super Admin."""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.super_admin_security import get_password_hash, verify_password
from app.models.super_admin import SuperAdmin


class CRUDSuperAdmin:
    """CRUD operations for SuperAdmin model."""
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[SuperAdmin]:
        """Get a super admin by ID."""
        result = await db.execute(
            select(SuperAdmin).where(SuperAdmin.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[SuperAdmin]:
        """Get a super admin by email."""
        result = await db.execute(
            select(SuperAdmin).where(SuperAdmin.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[SuperAdmin]:
        """Get all super admins."""
        result = await db.execute(
            select(SuperAdmin)
            .offset(skip)
            .limit(limit)
            .order_by(SuperAdmin.id)
        )
        return list(result.scalars().all())
    
    async def create(
        self,
        db: AsyncSession,
        *,
        email: str,
        password: str,
        name: str,
    ) -> SuperAdmin:
        """Create a new super admin."""
        db_obj = SuperAdmin(
            email=email,
            password_hash=get_password_hash(password),
            name=name,
            is_active=True,
            mfa_enabled=False,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def authenticate(
        self,
        db: AsyncSession,
        *,
        email: str,
        password: str,
    ) -> Optional[SuperAdmin]:
        """
        Authenticate a super admin by email and password.
        
        Returns None if authentication fails.
        Handles lockout after failed attempts.
        """
        super_admin = await self.get_by_email(db, email=email)
        
        if not super_admin:
            return None
        
        if not super_admin.is_active:
            return None
        
        if super_admin.is_locked:
            return None
        
        if not verify_password(password, super_admin.password_hash):
            super_admin.increment_failed_login()
            await db.commit()
            return None
        
        # Successful authentication
        super_admin.reset_failed_login()
        super_admin.last_login_at = datetime.utcnow()
        await db.commit()
        
        return super_admin
    
    async def update_last_login(
        self,
        db: AsyncSession,
        *,
        super_admin: SuperAdmin,
        ip_address: Optional[str] = None,
    ) -> SuperAdmin:
        """Update last login timestamp and IP."""
        super_admin.last_login_at = datetime.utcnow()
        super_admin.last_login_ip = ip_address
        await db.commit()
        await db.refresh(super_admin)
        return super_admin
    
    async def enable_mfa(
        self,
        db: AsyncSession,
        *,
        super_admin: SuperAdmin,
        mfa_secret: str,
        backup_codes: str,
    ) -> SuperAdmin:
        """Enable MFA for a super admin."""
        super_admin.mfa_secret = mfa_secret
        super_admin.mfa_backup_codes = backup_codes
        super_admin.mfa_enabled = True
        await db.commit()
        await db.refresh(super_admin)
        return super_admin
    
    async def disable_mfa(
        self,
        db: AsyncSession,
        *,
        super_admin: SuperAdmin,
    ) -> SuperAdmin:
        """Disable MFA for a super admin."""
        super_admin.mfa_secret = None
        super_admin.mfa_backup_codes = None
        super_admin.mfa_enabled = False
        await db.commit()
        await db.refresh(super_admin)
        return super_admin
    
    async def update_password(
        self,
        db: AsyncSession,
        *,
        super_admin: SuperAdmin,
        new_password: str,
    ) -> SuperAdmin:
        """Update super admin password."""
        super_admin.password_hash = get_password_hash(new_password)
        await db.commit()
        await db.refresh(super_admin)
        return super_admin
    
    async def deactivate(
        self,
        db: AsyncSession,
        *,
        super_admin: SuperAdmin,
    ) -> SuperAdmin:
        """Deactivate a super admin account."""
        super_admin.is_active = False
        await db.commit()
        await db.refresh(super_admin)
        return super_admin
    
    async def activate(
        self,
        db: AsyncSession,
        *,
        super_admin: SuperAdmin,
    ) -> SuperAdmin:
        """Reactivate a super admin account."""
        super_admin.is_active = True
        super_admin.reset_failed_login()
        await db.commit()
        await db.refresh(super_admin)
        return super_admin


# Global instance
super_admin = CRUDSuperAdmin()
