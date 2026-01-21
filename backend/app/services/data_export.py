"""
Data Export Service

GDPR-compliant data export functionality for tenants.
Exports all tenant data in a structured JSON format.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List
from io import BytesIO
import zipfile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.study import Study
from app.models.database_release import DatabaseRelease
from app.models.reporting_effort import ReportingEffort
from app.models.reporting_effort_item import ReportingEffortItem
from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
from app.models.package import Package
from app.models.package_item import PackageItem
from app.models.text_element import TextElement
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.notification import Notification

logger = logging.getLogger(__name__)


class DataExporter:
    """Export tenant data for GDPR compliance."""
    
    def __init__(self, db: AsyncSession, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
    
    async def export_all(self) -> Dict[str, Any]:
        """
        Export all tenant data as a dictionary.
        
        Returns a structured dictionary containing all tenant data.
        """
        export_data = {
            "export_metadata": {
                "tenant_id": self.tenant_id,
                "exported_at": datetime.utcnow().isoformat(),
                "format_version": "1.0",
            },
            "users": await self._export_users(),
            "studies": await self._export_studies(),
            "packages": await self._export_packages(),
            "text_elements": await self._export_text_elements(),
            "audit_logs": await self._export_audit_logs(),
            "notifications": await self._export_notifications(),
        }
        
        return export_data
    
    async def _export_users(self) -> List[Dict]:
        """Export all tenant users."""
        result = await self.db.execute(
            select(User)
            .where(User.tenant_id == self.tenant_id)
            .order_by(User.id)
        )
        users = result.scalars().all()
        
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            }
            for user in users
        ]
    
    async def _export_studies(self) -> List[Dict]:
        """Export all studies with their hierarchy."""
        result = await self.db.execute(
            select(Study)
            .where(Study.tenant_id == self.tenant_id)
            .options(
                selectinload(Study.database_releases)
                .selectinload(DatabaseRelease.reporting_efforts)
                .selectinload(ReportingEffort.items)
                .selectinload(ReportingEffortItem.trackers)
            )
            .order_by(Study.id)
        )
        studies = result.scalars().unique().all()
        
        return [
            {
                "id": study.id,
                "study_label": study.study_label,
                "description": study.description,
                "created_at": study.created_at.isoformat() if study.created_at else None,
                "updated_at": study.updated_at.isoformat() if study.updated_at else None,
                "database_releases": [
                    {
                        "id": release.id,
                        "release_label": release.release_label,
                        "release_date": release.release_date.isoformat() if release.release_date else None,
                        "description": release.description,
                        "created_at": release.created_at.isoformat() if release.created_at else None,
                        "reporting_efforts": [
                            {
                                "id": effort.id,
                                "effort_label": effort.effort_label,
                                "description": effort.description,
                                "is_locked": effort.is_locked,
                                "locked_at": effort.locked_at.isoformat() if effort.locked_at else None,
                                "lock_reason": effort.lock_reason,
                                "created_at": effort.created_at.isoformat() if effort.created_at else None,
                                "items": [
                                    {
                                        "id": item.id,
                                        "package_item_id": item.package_item_id,
                                        "created_at": item.created_at.isoformat() if item.created_at else None,
                                        "trackers": [
                                            {
                                                "id": tracker.id,
                                                "production_status": tracker.production_status,
                                                "qc_status": tracker.qc_status,
                                                "production_programmer_id": tracker.production_programmer_id,
                                                "qc_programmer_id": tracker.qc_programmer_id,
                                                "production_due_date": tracker.production_due_date.isoformat() if tracker.production_due_date else None,
                                                "qc_due_date": tracker.qc_due_date.isoformat() if tracker.qc_due_date else None,
                                                "notes": tracker.notes,
                                                "created_at": tracker.created_at.isoformat() if tracker.created_at else None,
                                                "updated_at": tracker.updated_at.isoformat() if tracker.updated_at else None,
                                            }
                                            for tracker in item.trackers
                                        ],
                                    }
                                    for item in effort.items
                                ],
                            }
                            for effort in release.reporting_efforts
                        ],
                    }
                    for release in study.database_releases
                ],
            }
            for study in studies
        ]
    
    async def _export_packages(self) -> List[Dict]:
        """Export all packages with items."""
        result = await self.db.execute(
            select(Package)
            .where(Package.tenant_id == self.tenant_id)
            .options(selectinload(Package.items))
            .order_by(Package.id)
        )
        packages = result.scalars().unique().all()
        
        return [
            {
                "id": package.id,
                "package_name": package.package_name,
                "description": package.description,
                "created_at": package.created_at.isoformat() if package.created_at else None,
                "updated_at": package.updated_at.isoformat() if package.updated_at else None,
                "items": [
                    {
                        "id": item.id,
                        "item_type": item.item_type.value if item.item_type else None,
                        "item_subtype": item.item_subtype,
                        "item_code": item.item_code,
                        "description": item.description,
                        "created_at": item.created_at.isoformat() if item.created_at else None,
                    }
                    for item in package.items
                ],
            }
            for package in packages
        ]
    
    async def _export_text_elements(self) -> List[Dict]:
        """Export all text elements."""
        result = await self.db.execute(
            select(TextElement)
            .where(TextElement.tenant_id == self.tenant_id)
            .order_by(TextElement.id)
        )
        elements = result.scalars().all()
        
        return [
            {
                "id": elem.id,
                "element_type": elem.element_type.value if elem.element_type else None,
                "label": elem.label,
                "content": elem.content,
                "created_at": elem.created_at.isoformat() if elem.created_at else None,
                "updated_at": elem.updated_at.isoformat() if elem.updated_at else None,
            }
            for elem in elements
        ]
    
    async def _export_audit_logs(self) -> List[Dict]:
        """Export audit logs (last 90 days)."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=90)
        
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.tenant_id == self.tenant_id)
            .where(AuditLog.created_at >= cutoff)
            .order_by(AuditLog.id.desc())
            .limit(10000)  # Limit to prevent huge exports
        )
        logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "table_name": log.table_name,
                "record_id": log.record_id,
                "action": log.action,
                "user_id": log.user_id,
                "changes": log.changes,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    
    async def _export_notifications(self) -> List[Dict]:
        """Export notifications (last 30 days)."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=30)
        
        result = await self.db.execute(
            select(Notification)
            .where(Notification.tenant_id == self.tenant_id)
            .where(Notification.created_at >= cutoff)
            .order_by(Notification.id.desc())
            .limit(5000)
        )
        notifications = result.scalars().all()
        
        return [
            {
                "id": notif.id,
                "user_id": notif.user_id,
                "notification_type": notif.notification_type,
                "title": notif.title,
                "message": notif.message,
                "is_read": notif.is_read,
                "is_acknowledged": notif.is_acknowledged,
                "created_at": notif.created_at.isoformat() if notif.created_at else None,
            }
            for notif in notifications
        ]


async def export_tenant_data(db: AsyncSession, tenant_id: int) -> Dict[str, Any]:
    """
    Export all data for a tenant.
    
    Returns a dictionary with all tenant data.
    """
    exporter = DataExporter(db, tenant_id)
    return await exporter.export_all()


async def export_tenant_data_as_zip(db: AsyncSession, tenant_id: int) -> bytes:
    """
    Export all tenant data as a ZIP file.
    
    Returns ZIP file bytes containing:
    - data.json: All tenant data
    - metadata.json: Export metadata
    """
    data = await export_tenant_data(db, tenant_id)
    
    # Create ZIP file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add main data file
        zf.writestr(
            'data.json',
            json.dumps(data, indent=2, ensure_ascii=False)
        )
        
        # Add metadata file
        metadata = {
            "export_type": "GDPR_DATA_EXPORT",
            "tenant_id": tenant_id,
            "exported_at": datetime.utcnow().isoformat(),
            "format_version": "1.0",
            "contents": [
                "data.json - Complete tenant data export"
            ],
        }
        zf.writestr(
            'metadata.json',
            json.dumps(metadata, indent=2)
        )
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


async def export_user_data(db: AsyncSession, tenant_id: int, user_id: int) -> Dict[str, Any]:
    """
    Export data for a specific user (GDPR individual request).
    
    Returns user's personal data and activity.
    """
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return {"error": "User not found"}
    
    # Get user's audit log entries
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .order_by(AuditLog.id.desc())
        .limit(1000)
    )
    audit_logs = result.scalars().all()
    
    # Get user's notifications
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.id.desc())
        .limit(500)
    )
    notifications = result.scalars().all()
    
    return {
        "export_metadata": {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "exported_at": datetime.utcnow().isoformat(),
            "export_type": "GDPR_INDIVIDUAL_EXPORT",
        },
        "personal_data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "activity_logs": [
            {
                "id": log.id,
                "action": log.action,
                "table_name": log.table_name,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in audit_logs
        ],
        "notifications": [
            {
                "id": notif.id,
                "title": notif.title,
                "message": notif.message,
                "created_at": notif.created_at.isoformat() if notif.created_at else None,
            }
            for notif in notifications
        ],
    }
