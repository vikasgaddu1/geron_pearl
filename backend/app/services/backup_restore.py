"""
Backup and Restore Service

Provides functionality to create backups and restore tenant data.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from io import BytesIO
import zipfile

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study import Study
from app.models.database_release import DatabaseRelease
from app.models.reporting_effort import ReportingEffort
from app.models.reporting_effort_item import ReportingEffortItem
from app.models.reporting_effort_tracker import ReportingEffortTracker
from app.models.package import Package
from app.models.package_item import PackageItem
from app.models.text_element import TextElement
from app.models.enums import ItemType, TextElementType

logger = logging.getLogger(__name__)


class BackupRestoreService:
    """Service for creating and restoring backups."""
    
    BACKUP_VERSION = "1.0"
    
    def __init__(self, db: AsyncSession, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
    
    async def create_backup(self) -> Dict[str, Any]:
        """
        Create a full backup of tenant data.
        
        Returns a dictionary that can be used for restoration.
        """
        from app.services.data_export import DataExporter
        
        exporter = DataExporter(self.db, self.tenant_id)
        data = await exporter.export_all()
        
        # Add backup-specific metadata
        data["backup_metadata"] = {
            "backup_version": self.BACKUP_VERSION,
            "tenant_id": self.tenant_id,
            "created_at": datetime.utcnow().isoformat(),
            "type": "FULL_BACKUP",
        }
        
        return data
    
    async def create_backup_zip(self) -> bytes:
        """Create a ZIP file backup."""
        data = await self.create_backup()
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                'backup.json',
                json.dumps(data, indent=2, ensure_ascii=False)
            )
            zf.writestr(
                'manifest.json',
                json.dumps({
                    "backup_version": self.BACKUP_VERSION,
                    "created_at": datetime.utcnow().isoformat(),
                    "tenant_id": self.tenant_id,
                    "files": ["backup.json"],
                }, indent=2)
            )
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    async def validate_backup(self, backup_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate backup data before restoration.
        
        Returns (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        if "backup_metadata" not in backup_data and "export_metadata" not in backup_data:
            errors.append("Missing metadata in backup file")
        
        # Check for required sections
        required_sections = ["studies", "packages", "text_elements"]
        for section in required_sections:
            if section not in backup_data:
                errors.append(f"Missing required section: {section}")
        
        # Validate version compatibility
        metadata = backup_data.get("backup_metadata") or backup_data.get("export_metadata", {})
        version = metadata.get("format_version") or metadata.get("backup_version", "1.0")
        if version not in ["1.0"]:
            errors.append(f"Unsupported backup version: {version}")
        
        return len(errors) == 0, errors
    
    async def restore_from_backup(
        self, 
        backup_data: Dict[str, Any],
        clear_existing: bool = False,
        admin_user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Restore tenant data from a backup.
        
        Args:
            backup_data: The backup data to restore
            clear_existing: If True, clears existing data first
            admin_user_id: User ID to associate with created records
        
        Returns:
            Dictionary with restoration statistics
        """
        # Validate backup
        is_valid, errors = await self.validate_backup(backup_data)
        if not is_valid:
            raise ValueError(f"Invalid backup: {', '.join(errors)}")
        
        stats = {
            "studies_created": 0,
            "database_releases_created": 0,
            "reporting_efforts_created": 0,
            "packages_created": 0,
            "package_items_created": 0,
            "text_elements_created": 0,
        }
        
        # Clear existing data if requested
        if clear_existing:
            await self._clear_existing_data()
        
        # Restore packages first (they're referenced by other entities)
        id_mappings = {"packages": {}, "package_items": {}}
        
        for pkg_data in backup_data.get("packages", []):
            old_id = pkg_data["id"]
            new_package = Package(
                tenant_id=self.tenant_id,
                package_name=pkg_data["package_name"],
                description=pkg_data.get("description"),
            )
            self.db.add(new_package)
            await self.db.flush()
            
            id_mappings["packages"][old_id] = new_package.id
            stats["packages_created"] += 1
            
            # Restore package items
            for item_data in pkg_data.get("items", []):
                old_item_id = item_data["id"]
                item_type = None
                if item_data.get("item_type"):
                    try:
                        item_type = ItemType(item_data["item_type"])
                    except ValueError:
                        pass
                
                new_item = PackageItem(
                    package_id=new_package.id,
                    item_type=item_type,
                    item_subtype=item_data.get("item_subtype"),
                    item_code=item_data.get("item_code"),
                    description=item_data.get("description"),
                )
                self.db.add(new_item)
                await self.db.flush()
                
                id_mappings["package_items"][old_item_id] = new_item.id
                stats["package_items_created"] += 1
        
        # Restore text elements
        for elem_data in backup_data.get("text_elements", []):
            elem_type = None
            if elem_data.get("element_type"):
                try:
                    elem_type = TextElementType(elem_data["element_type"])
                except ValueError:
                    pass
            
            new_elem = TextElement(
                tenant_id=self.tenant_id,
                element_type=elem_type,
                label=elem_data.get("label"),
                content=elem_data.get("content"),
            )
            self.db.add(new_elem)
            stats["text_elements_created"] += 1
        
        # Restore studies hierarchy
        for study_data in backup_data.get("studies", []):
            new_study = Study(
                tenant_id=self.tenant_id,
                study_label=study_data["study_label"],
                description=study_data.get("description"),
            )
            self.db.add(new_study)
            await self.db.flush()
            stats["studies_created"] += 1
            
            # Restore database releases
            for release_data in study_data.get("database_releases", []):
                release_date = None
                if release_data.get("release_date"):
                    try:
                        release_date = datetime.fromisoformat(
                            release_data["release_date"].replace("Z", "+00:00")
                        ).date()
                    except:
                        pass
                
                new_release = DatabaseRelease(
                    study_id=new_study.id,
                    release_label=release_data["release_label"],
                    release_date=release_date,
                    description=release_data.get("description"),
                )
                self.db.add(new_release)
                await self.db.flush()
                stats["database_releases_created"] += 1
                
                # Restore reporting efforts
                for effort_data in release_data.get("reporting_efforts", []):
                    new_effort = ReportingEffort(
                        database_release_id=new_release.id,
                        study_id=new_study.id,
                        effort_label=effort_data["effort_label"],
                        description=effort_data.get("description"),
                    )
                    self.db.add(new_effort)
                    await self.db.flush()
                    stats["reporting_efforts_created"] += 1
                    
                    # Restore reporting effort items (with mapped package_item_id)
                    for item_data in effort_data.get("items", []):
                        old_pkg_item_id = item_data.get("package_item_id")
                        new_pkg_item_id = id_mappings["package_items"].get(old_pkg_item_id)
                        
                        if new_pkg_item_id:
                            new_item = ReportingEffortItem(
                                reporting_effort_id=new_effort.id,
                                package_item_id=new_pkg_item_id,
                            )
                            self.db.add(new_item)
        
        await self.db.commit()
        
        logger.info(f"Backup restored for tenant {self.tenant_id}: {stats}")
        return stats
    
    async def _clear_existing_data(self) -> None:
        """Clear all existing tenant data (except users)."""
        # Delete in order to respect foreign keys
        # Trackers -> Items -> Efforts -> Releases -> Studies
        # Package Items -> Packages
        # Text Elements
        
        # Get study IDs
        result = await self.db.execute(
            select(Study.id).where(Study.tenant_id == self.tenant_id)
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
                        await self.db.execute(
                            delete(ReportingEffortTracker).where(
                                ReportingEffortTracker.reporting_effort_item_id.in_(item_ids)
                            )
                        )
                    
                    # Delete items
                    await self.db.execute(
                        delete(ReportingEffortItem).where(
                            ReportingEffortItem.reporting_effort_id.in_(effort_ids)
                        )
                    )
                
                # Delete efforts
                await self.db.execute(
                    delete(ReportingEffort).where(
                        ReportingEffort.database_release_id.in_(release_ids)
                    )
                )
            
            # Delete releases
            await self.db.execute(
                delete(DatabaseRelease).where(DatabaseRelease.study_id.in_(study_ids))
            )
        
        # Delete studies
        await self.db.execute(
            delete(Study).where(Study.tenant_id == self.tenant_id)
        )
        
        # Get package IDs
        result = await self.db.execute(
            select(Package.id).where(Package.tenant_id == self.tenant_id)
        )
        package_ids = [r[0] for r in result.fetchall()]
        
        if package_ids:
            # Delete package items
            await self.db.execute(
                delete(PackageItem).where(PackageItem.package_id.in_(package_ids))
            )
        
        # Delete packages
        await self.db.execute(
            delete(Package).where(Package.tenant_id == self.tenant_id)
        )
        
        # Delete text elements
        await self.db.execute(
            delete(TextElement).where(TextElement.tenant_id == self.tenant_id)
        )
        
        await self.db.flush()


async def create_tenant_backup(db: AsyncSession, tenant_id: int) -> Dict[str, Any]:
    """Create a backup for a tenant."""
    service = BackupRestoreService(db, tenant_id)
    return await service.create_backup()


async def create_tenant_backup_zip(db: AsyncSession, tenant_id: int) -> bytes:
    """Create a ZIP backup for a tenant."""
    service = BackupRestoreService(db, tenant_id)
    return await service.create_backup_zip()


async def restore_tenant_backup(
    db: AsyncSession,
    tenant_id: int,
    backup_data: Dict[str, Any],
    clear_existing: bool = False,
    admin_user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Restore a tenant from backup data."""
    service = BackupRestoreService(db, tenant_id)
    return await service.restore_from_backup(backup_data, clear_existing, admin_user_id)
