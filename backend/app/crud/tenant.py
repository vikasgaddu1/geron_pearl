"""CRUD operations for Tenant model."""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant, SubscriptionStatus
from app.schemas.tenant import TenantCreate, TenantUpdate


class TenantCRUD:
    """CRUD operations for Tenant model."""
    
    async def create(self, db: AsyncSession, *, obj_in: TenantCreate) -> Tenant:
        """Create a new tenant."""
        db_obj = Tenant(
            name=obj_in.name,
            display_name=obj_in.display_name,
            stripe_customer_id=obj_in.stripe_customer_id,
            stripe_subscription_id=obj_in.stripe_subscription_id,
            subscription_status=obj_in.subscription_status or SubscriptionStatus.trialing,
            trial_ends_at=obj_in.trial_ends_at,
            plan_id=obj_in.plan_id,
            is_active=True,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[Tenant]:
        """Get a tenant by ID."""
        result = await db.execute(select(Tenant).where(Tenant.id == id))
        return result.scalar_one_or_none()
    
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Tenant]:
        """Get a tenant by name (slug)."""
        result = await db.execute(select(Tenant).where(Tenant.name == name))
        return result.scalar_one_or_none()
    
    async def get_by_stripe_customer_id(
        self, db: AsyncSession, *, stripe_customer_id: str
    ) -> Optional[Tenant]:
        """Get a tenant by Stripe customer ID."""
        result = await db.execute(
            select(Tenant).where(Tenant.stripe_customer_id == stripe_customer_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_stripe_subscription_id(
        self, db: AsyncSession, *, stripe_subscription_id: str
    ) -> Optional[Tenant]:
        """Get a tenant by Stripe subscription ID."""
        result = await db.execute(
            select(Tenant).where(Tenant.stripe_subscription_id == stripe_subscription_id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Tenant]:
        """Get multiple tenants with pagination."""
        query = select(Tenant)
        if not include_deleted:
            query = query.where(Tenant.deleted_at.is_(None))
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_active_tenants(self, db: AsyncSession) -> List[Tenant]:
        """Get all active tenants."""
        result = await db.execute(
            select(Tenant).where(
                and_(
                    Tenant.is_active == True,
                    Tenant.deleted_at.is_(None)
                )
            )
        )
        return list(result.scalars().all())
    
    async def update(
        self, db: AsyncSession, *, db_obj: Tenant, obj_in: TenantUpdate
    ) -> Tenant:
        """Update an existing tenant."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update_subscription_status(
        self,
        db: AsyncSession,
        *,
        tenant_id: int,
        status: SubscriptionStatus,
        grace_period_ends_at: Optional[datetime] = None
    ) -> Optional[Tenant]:
        """Update tenant subscription status."""
        tenant = await self.get(db, id=tenant_id)
        if not tenant:
            return None
        
        tenant.subscription_status = status
        if grace_period_ends_at:
            tenant.grace_period_ends_at = grace_period_ends_at
        
        await db.commit()
        await db.refresh(tenant)
        return tenant
    
    async def soft_delete(self, db: AsyncSession, *, id: int) -> Optional[Tenant]:
        """Soft delete a tenant (set deleted_at timestamp)."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            db_obj.deleted_at = datetime.utcnow()
            db_obj.is_active = False
            await db.commit()
            await db.refresh(db_obj)
        return db_obj
    
    async def hard_delete(self, db: AsyncSession, *, id: int) -> Optional[Tenant]:
        """Hard delete a tenant (permanent, use with caution)."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
    
    async def count(self, db: AsyncSession, *, include_deleted: bool = False) -> int:
        """Count total tenants."""
        from sqlalchemy import func
        query = select(func.count(Tenant.id))
        if not include_deleted:
            query = query.where(Tenant.deleted_at.is_(None))
        result = await db.execute(query)
        return result.scalar() or 0


# Create a global instance
tenant = TenantCRUD()
