"""
Data Retention Service

Handles tenant data retention policies:
- Soft-deleted tenants are purged after 90 days
- Cancelled subscriptions are cleaned up after grace period
- Audit logs are retained per compliance requirements
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.study import Study
from app.models.database_release import DatabaseRelease
from app.models.reporting_effort import ReportingEffort
from app.models.reporting_effort_item import ReportingEffortItem
from app.models.reporting_effort_tracker import ReportingEffortTracker
from app.models.package import Package
from app.models.package_item import PackageItem
from app.models.text_element import TextElement
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.notification import Notification

logger = logging.getLogger(__name__)


# Configuration
TENANT_RETENTION_DAYS = 90  # Days to keep soft-deleted tenant data
AUDIT_LOG_RETENTION_DAYS = 365  # Days to keep audit logs
NOTIFICATION_RETENTION_DAYS = 90  # Days to keep notifications


class DataRetentionService:
    """Manage data retention policies."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_tenants_pending_deletion(self) -> List[Tenant]:
        """
        Get tenants that are past the retention period and ready for permanent deletion.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=TENANT_RETENTION_DAYS)
        
        result = await self.db.execute(
            select(Tenant).where(
                and_(
                    Tenant.deleted_at.isnot(None),
                    Tenant.deleted_at < cutoff_date,
                )
            )
        )
        return list(result.scalars().all())
    
    async def permanently_delete_tenant(self, tenant_id: int) -> Dict[str, int]:
        """
        Permanently delete all data for a tenant.
        
        This is irreversible and removes all tenant data from the database.
        
        Returns counts of deleted records.
        """
        counts = {
            "trackers": 0,
            "items": 0,
            "efforts": 0,
            "releases": 0,
            "studies": 0,
            "package_items": 0,
            "packages": 0,
            "text_elements": 0,
            "notifications": 0,
            "audit_logs": 0,
            "users": 0,
        }
        
        logger.info(f"Starting permanent deletion for tenant {tenant_id}")
        
        # Delete study hierarchy
        result = await self.db.execute(
            select(Study.id).where(Study.tenant_id == tenant_id)
        )
        study_ids = [r[0] for r in result.fetchall()]
        
        if study_ids:
            # Get release IDs
            result = await self.db.execute(
                select(DatabaseRelease.id).where(DatabaseRelease.study_id.in_(study_ids))
            )
            release_ids = [r[0] for r in result.fetchall()]
            
            if release_ids:
                # Get effort IDs
                result = await self.db.execute(
                    select(ReportingEffort.id).where(
                        ReportingEffort.database_release_id.in_(release_ids)
                    )
                )
                effort_ids = [r[0] for r in result.fetchall()]
                
                if effort_ids:
                    # Get item IDs
                    result = await self.db.execute(
                        select(ReportingEffortItem.id).where(
                            ReportingEffortItem.reporting_effort_id.in_(effort_ids)
                        )
                    )
                    item_ids = [r[0] for r in result.fetchall()]
                    
                    if item_ids:
                        # Delete trackers
                        result = await self.db.execute(
                            delete(ReportingEffortTracker).where(
                                ReportingEffortTracker.reporting_effort_item_id.in_(item_ids)
                            )
                        )
                        counts["trackers"] = result.rowcount
                    
                    # Delete items
                    result = await self.db.execute(
                        delete(ReportingEffortItem).where(
                            ReportingEffortItem.reporting_effort_id.in_(effort_ids)
                        )
                    )
                    counts["items"] = result.rowcount
                
                # Delete efforts
                result = await self.db.execute(
                    delete(ReportingEffort).where(
                        ReportingEffort.database_release_id.in_(release_ids)
                    )
                )
                counts["efforts"] = result.rowcount
            
            # Delete releases
            result = await self.db.execute(
                delete(DatabaseRelease).where(DatabaseRelease.study_id.in_(study_ids))
            )
            counts["releases"] = result.rowcount
        
        # Delete studies
        result = await self.db.execute(
            delete(Study).where(Study.tenant_id == tenant_id)
        )
        counts["studies"] = result.rowcount
        
        # Delete packages
        result = await self.db.execute(
            select(Package.id).where(Package.tenant_id == tenant_id)
        )
        package_ids = [r[0] for r in result.fetchall()]
        
        if package_ids:
            result = await self.db.execute(
                delete(PackageItem).where(PackageItem.package_id.in_(package_ids))
            )
            counts["package_items"] = result.rowcount
        
        result = await self.db.execute(
            delete(Package).where(Package.tenant_id == tenant_id)
        )
        counts["packages"] = result.rowcount
        
        # Delete text elements
        result = await self.db.execute(
            delete(TextElement).where(TextElement.tenant_id == tenant_id)
        )
        counts["text_elements"] = result.rowcount
        
        # Delete notifications
        result = await self.db.execute(
            delete(Notification).where(Notification.tenant_id == tenant_id)
        )
        counts["notifications"] = result.rowcount
        
        # Delete audit logs (keep for compliance? depends on requirements)
        result = await self.db.execute(
            delete(AuditLog).where(AuditLog.tenant_id == tenant_id)
        )
        counts["audit_logs"] = result.rowcount
        
        # Delete users
        result = await self.db.execute(
            delete(User).where(User.tenant_id == tenant_id)
        )
        counts["users"] = result.rowcount
        
        # Delete tenant itself
        await self.db.execute(
            delete(Tenant).where(Tenant.id == tenant_id)
        )
        
        await self.db.commit()
        
        logger.info(f"Permanently deleted tenant {tenant_id}: {counts}")
        return counts
    
    async def cleanup_old_audit_logs(self) -> int:
        """
        Clean up audit logs older than retention period.
        
        Returns count of deleted records.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=AUDIT_LOG_RETENTION_DAYS)
        
        result = await self.db.execute(
            delete(AuditLog).where(AuditLog.created_at < cutoff_date)
        )
        count = result.rowcount
        await self.db.commit()
        
        if count > 0:
            logger.info(f"Cleaned up {count} old audit logs")
        
        return count
    
    async def cleanup_old_notifications(self) -> int:
        """
        Clean up acknowledged notifications older than retention period.
        
        Returns count of deleted records.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=NOTIFICATION_RETENTION_DAYS)
        
        result = await self.db.execute(
            delete(Notification).where(
                and_(
                    Notification.is_acknowledged == True,
                    Notification.created_at < cutoff_date,
                )
            )
        )
        count = result.rowcount
        await self.db.commit()
        
        if count > 0:
            logger.info(f"Cleaned up {count} old notifications")
        
        return count
    
    async def run_retention_cleanup(self) -> Dict[str, any]:
        """
        Run all retention cleanup tasks.
        
        Returns summary of cleanup actions.
        """
        results = {
            "deleted_tenants": [],
            "audit_logs_cleaned": 0,
            "notifications_cleaned": 0,
        }
        
        # Find and delete expired tenants
        tenants = await self.get_tenants_pending_deletion()
        for tenant in tenants:
            try:
                counts = await self.permanently_delete_tenant(tenant.id)
                results["deleted_tenants"].append({
                    "tenant_id": tenant.id,
                    "name": tenant.name,
                    "counts": counts,
                })
            except Exception as e:
                logger.error(f"Failed to delete tenant {tenant.id}: {e}")
        
        # Cleanup old audit logs
        results["audit_logs_cleaned"] = await self.cleanup_old_audit_logs()
        
        # Cleanup old notifications
        results["notifications_cleaned"] = await self.cleanup_old_notifications()
        
        return results


async def soft_delete_tenant(db: AsyncSession, tenant_id: int) -> None:
    """
    Soft delete a tenant (mark as deleted, start retention countdown).
    """
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if tenant:
        tenant.deleted_at = datetime.utcnow()
        tenant.is_active = False
        await db.commit()
        logger.info(f"Soft deleted tenant {tenant_id}")


async def restore_tenant(db: AsyncSession, tenant_id: int) -> bool:
    """
    Restore a soft-deleted tenant (if within retention period).
    
    Returns True if restored, False if not found or past retention.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=TENANT_RETENTION_DAYS)
    
    result = await db.execute(
        select(Tenant).where(
            and_(
                Tenant.id == tenant_id,
                Tenant.deleted_at.isnot(None),
                Tenant.deleted_at >= cutoff_date,
            )
        )
    )
    tenant = result.scalar_one_or_none()
    
    if tenant:
        tenant.deleted_at = None
        tenant.is_active = True
        await db.commit()
        logger.info(f"Restored tenant {tenant_id}")
        return True
    
    return False


async def get_tenant_deletion_info(db: AsyncSession, tenant_id: int) -> Optional[Dict]:
    """
    Get information about a soft-deleted tenant.
    
    Returns deletion date and days until permanent deletion.
    """
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant or not tenant.deleted_at:
        return None
    
    days_since_deletion = (datetime.utcnow() - tenant.deleted_at).days
    days_until_permanent = max(0, TENANT_RETENTION_DAYS - days_since_deletion)
    
    return {
        "tenant_id": tenant_id,
        "tenant_name": tenant.name,
        "deleted_at": tenant.deleted_at.isoformat(),
        "days_since_deletion": days_since_deletion,
        "days_until_permanent_deletion": days_until_permanent,
        "can_restore": days_until_permanent > 0,
    }


async def run_scheduled_cleanup(db: AsyncSession) -> Dict[str, any]:
    """
    Run scheduled retention cleanup.
    
    This should be called by a cron job or scheduled task.
    """
    service = DataRetentionService(db)
    return await service.run_retention_cleanup()
