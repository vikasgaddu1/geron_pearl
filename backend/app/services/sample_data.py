"""Sample data seeding service for new tenants.

This module provides functions to seed sample data for new tenants:
- Sample studies with database releases and reporting efforts
- Sample packages with package items
- Sample text elements (titles, footnotes, populations, acronyms)

The sample data demonstrates PEARL's capabilities and provides
a starting point for new users to explore the system.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study import Study
from app.models.database_release import DatabaseRelease
from app.models.reporting_effort import ReportingEffort
from app.models.package import Package
from app.models.package_item import PackageItem
from app.models.text_element import TextElement, TextElementType
from app.models.tenant import Tenant
from app.models.user import User
from app.models.enums import ItemType

logger = logging.getLogger(__name__)


# =============================================================================
# Sample Data Definitions
# =============================================================================

SAMPLE_STUDIES = [
    {
        "study_label": "DEMO-001",
        "database_releases": [
            {
                "release_name": "DBR-001",
                "release_date": date.today() + timedelta(days=30),
                "reporting_efforts": [
                    {"name": "Interim Analysis"},
                ],
            },
            {
                "release_name": "DBR-002",
                "release_date": date.today() + timedelta(days=90),
                "reporting_efforts": [
                    {"name": "Final CSR"},
                ],
            },
        ],
    },
    {
        "study_label": "DEMO-002",
        "database_releases": [
            {
                "release_name": "Final-DBR",
                "release_date": date.today() + timedelta(days=60),
                "reporting_efforts": [
                    {"name": "Primary Analysis"},
                    {"name": "Safety Update"},
                ],
            },
        ],
    },
]

# Package items use: item_type (TLF/Dataset), item_subtype (Table/Listing/Figure or SDTM/ADaM), item_code
SAMPLE_PACKAGES = [
    {
        "package_name": "PKG-SAFETY",
        "items": [
            {"item_type": ItemType.TLF, "item_subtype": "Table", "item_code": "t-ae-summary"},
            {"item_type": ItemType.TLF, "item_subtype": "Table", "item_code": "t-ae-soc-pt"},
            {"item_type": ItemType.TLF, "item_subtype": "Table", "item_code": "t-ae-severity"},
            {"item_type": ItemType.TLF, "item_subtype": "Listing", "item_code": "l-ae-listing"},
            {"item_type": ItemType.TLF, "item_subtype": "Figure", "item_code": "f-ae-overview"},
            {"item_type": ItemType.Dataset, "item_subtype": "ADaM", "item_code": "ADAE"},
        ],
    },
    {
        "package_name": "PKG-EFFICACY",
        "items": [
            {"item_type": ItemType.TLF, "item_subtype": "Table", "item_code": "t-primary-endpoint"},
            {"item_type": ItemType.TLF, "item_subtype": "Table", "item_code": "t-secondary-endpoints"},
            {"item_type": ItemType.TLF, "item_subtype": "Figure", "item_code": "f-kaplan-meier"},
            {"item_type": ItemType.TLF, "item_subtype": "Figure", "item_code": "f-forest-plot"},
            {"item_type": ItemType.Dataset, "item_subtype": "ADaM", "item_code": "ADEFF"},
        ],
    },
    {
        "package_name": "PKG-DEMOGRAPHICS",
        "items": [
            {"item_type": ItemType.TLF, "item_subtype": "Table", "item_code": "t-demographics"},
            {"item_type": ItemType.TLF, "item_subtype": "Table", "item_code": "t-disposition"},
            {"item_type": ItemType.TLF, "item_subtype": "Table", "item_code": "t-medical-history"},
            {"item_type": ItemType.Dataset, "item_subtype": "SDTM", "item_code": "DM"},
            {"item_type": ItemType.Dataset, "item_subtype": "SDTM", "item_code": "MH"},
        ],
    },
]

SAMPLE_TEXT_ELEMENTS = [
    # Titles
    {"type": TextElementType.title, "label": "Safety", "content": "Summary of Adverse Events"},
    {"type": TextElementType.title, "label": "Efficacy", "content": "Primary Efficacy Analysis"},
    {"type": TextElementType.title, "label": "Demographics", "content": "Baseline Demographics and Characteristics"},
    
    # Footnotes
    {"type": TextElementType.footnote, "label": "AE_SOURCE", "content": "Source: ADAE dataset"},
    {"type": TextElementType.footnote, "label": "EFFICACY_SOURCE", "content": "Source: ADEFF dataset"},
    {"type": TextElementType.footnote, "label": "POPULATION", "content": "Analysis performed on the Safety Population"},
    {"type": TextElementType.footnote, "label": "CI_METHOD", "content": "95% CI calculated using Clopper-Pearson method"},
    
    # Population Sets
    {"type": TextElementType.population_set, "label": "SAFFL", "content": "Safety Population"},
    {"type": TextElementType.population_set, "label": "ITTFL", "content": "Intent-to-Treat Population"},
    {"type": TextElementType.population_set, "label": "PPROTFL", "content": "Per-Protocol Population"},
    {"type": TextElementType.population_set, "label": "FASFL", "content": "Full Analysis Set"},
    
    # Acronyms
    {"type": TextElementType.acronyms_set, "label": "AE", "content": "Adverse Event"},
    {"type": TextElementType.acronyms_set, "label": "SAE", "content": "Serious Adverse Event"},
    {"type": TextElementType.acronyms_set, "label": "TEAE", "content": "Treatment-Emergent Adverse Event"},
    {"type": TextElementType.acronyms_set, "label": "CI", "content": "Confidence Interval"},
    {"type": TextElementType.acronyms_set, "label": "SD", "content": "Standard Deviation"},
    {"type": TextElementType.acronyms_set, "label": "ITT", "content": "Intent-to-Treat"},
    {"type": TextElementType.acronyms_set, "label": "PP", "content": "Per-Protocol"},
    
    # ICH Categories
    {"type": TextElementType.ich_category, "label": "ICH_11.4", "content": "Individual Patient Data Listings"},
    {"type": TextElementType.ich_category, "label": "ICH_14.1", "content": "Demographics and Baseline Characteristics"},
    {"type": TextElementType.ich_category, "label": "ICH_14.3", "content": "Efficacy Results"},
    {"type": TextElementType.ich_category, "label": "ICH_12.2", "content": "Summary of Adverse Events"},
]


# =============================================================================
# Seeding Functions
# =============================================================================

async def seed_sample_data(
    db: AsyncSession,
    tenant_id: int,
    admin_user_id: Optional[int] = None,
) -> dict:
    """
    Seed sample data for a new tenant.
    
    Args:
        db: Database session
        tenant_id: Tenant ID to seed data for
        admin_user_id: Optional admin user ID to associate with created data
    
    Returns:
        Dictionary with counts of created entities
    """
    logger.info(f"Seeding sample data for tenant {tenant_id}")
    
    counts = {
        "studies": 0,
        "database_releases": 0,
        "reporting_efforts": 0,
        "packages": 0,
        "package_items": 0,
        "text_elements": 0,
    }
    
    try:
        # Seed studies with database releases and reporting efforts
        for study_data in SAMPLE_STUDIES:
            study = Study(
                tenant_id=tenant_id,
                study_label=study_data["study_label"],
            )
            db.add(study)
            await db.flush()  # Get study.id
            counts["studies"] += 1
            
            # Add database releases for this study
            for release_data in study_data.get("database_releases", []):
                db_release = DatabaseRelease(
                    tenant_id=tenant_id,
                    study_id=study.id,
                    release_name=release_data["release_name"],
                    release_date=release_data["release_date"],
                )
                db.add(db_release)
                await db.flush()  # Get db_release.id
                counts["database_releases"] += 1
                
                # Add reporting efforts for this database release
                for effort_data in release_data.get("reporting_efforts", []):
                    reporting_effort = ReportingEffort(
                        tenant_id=tenant_id,
                        study_id=study.id,
                        database_release_id=db_release.id,
                        name=effort_data["name"],
                    )
                    db.add(reporting_effort)
                    counts["reporting_efforts"] += 1
        
        # Seed packages with package items
        for package_data in SAMPLE_PACKAGES:
            package = Package(
                tenant_id=tenant_id,
                package_name=package_data["package_name"],
            )
            db.add(package)
            await db.flush()  # Get package.id
            counts["packages"] += 1
            
            # Add package items for this package
            for item_data in package_data.get("items", []):
                package_item = PackageItem(
                    package_id=package.id,
                    item_type=item_data["item_type"],
                    item_subtype=item_data["item_subtype"],
                    item_code=item_data["item_code"],
                )
                db.add(package_item)
                counts["package_items"] += 1
        
        # Seed text elements
        for element_data in SAMPLE_TEXT_ELEMENTS:
            text_element = TextElement(
                tenant_id=tenant_id,
                type=element_data["type"],
                label=element_data["label"],
                content=element_data["content"],
            )
            db.add(text_element)
            counts["text_elements"] += 1
        
        # Update tenant's sample_data_seeded flag
        result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if tenant:
            tenant.sample_data_seeded = True
        
        await db.commit()
        
        logger.info(
            f"Sample data seeded for tenant {tenant_id}: "
            f"{counts['studies']} studies, "
            f"{counts['database_releases']} releases, "
            f"{counts['reporting_efforts']} reporting efforts, "
            f"{counts['packages']} packages, "
            f"{counts['package_items']} items, "
            f"{counts['text_elements']} text elements"
        )
        
        return counts
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to seed sample data for tenant {tenant_id}: {e}")
        raise


async def clear_tenant_data(
    db: AsyncSession,
    tenant_id: int,
    exclude_users: bool = True,
) -> dict:
    """
    Clear all data for a tenant (for reset functionality).
    
    Args:
        db: Database session
        tenant_id: Tenant ID to clear data for
        exclude_users: If True, don't delete users (default True)
    
    Returns:
        Dictionary with counts of deleted entities
    """
    logger.info(f"Clearing data for tenant {tenant_id}")
    
    counts = {
        "studies": 0,
        "packages": 0,
        "text_elements": 0,
        "users": 0,
    }
    
    try:
        # Delete studies (cascades to database_releases, reporting_efforts, etc.)
        result = await db.execute(
            delete(Study).where(Study.tenant_id == tenant_id)
        )
        counts["studies"] = result.rowcount
        
        # Delete packages (cascades to package_items)
        result = await db.execute(
            delete(Package).where(Package.tenant_id == tenant_id)
        )
        counts["packages"] = result.rowcount
        
        # Delete text elements
        result = await db.execute(
            delete(TextElement).where(TextElement.tenant_id == tenant_id)
        )
        counts["text_elements"] = result.rowcount
        
        # Optionally delete users (except the current admin)
        if not exclude_users:
            result = await db.execute(
                delete(User).where(User.tenant_id == tenant_id)
            )
            counts["users"] = result.rowcount
        
        await db.commit()
        
        logger.info(
            f"Data cleared for tenant {tenant_id}: "
            f"{counts['studies']} studies, "
            f"{counts['packages']} packages, "
            f"{counts['text_elements']} text elements"
        )
        
        return counts
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to clear data for tenant {tenant_id}: {e}")
        raise


async def reset_to_sample_data(
    db: AsyncSession,
    tenant_id: int,
    admin_user_id: Optional[int] = None,
) -> dict:
    """
    Reset tenant data to sample state.
    
    Clears all existing data (except users) and re-seeds with sample data.
    
    Args:
        db: Database session
        tenant_id: Tenant ID to reset
        admin_user_id: Optional admin user ID to preserve
    
    Returns:
        Dictionary with clear and seed counts
    """
    logger.info(f"Resetting tenant {tenant_id} to sample data")
    
    # Clear existing data
    clear_counts = await clear_tenant_data(db, tenant_id, exclude_users=True)
    
    # Seed sample data
    seed_counts = await seed_sample_data(db, tenant_id, admin_user_id)
    
    return {
        "cleared": clear_counts,
        "seeded": seed_counts,
    }


async def check_has_sample_data(
    db: AsyncSession,
    tenant_id: int,
) -> bool:
    """
    Check if a tenant already has sample data seeded.
    
    Args:
        db: Database session
        tenant_id: Tenant ID to check
    
    Returns:
        True if tenant has at least one study with DEMO- prefix
    """
    result = await db.execute(
        select(Study)
        .where(Study.tenant_id == tenant_id)
        .where(Study.study_label.like("DEMO-%"))
        .limit(1)
    )
    return result.scalar_one_or_none() is not None
