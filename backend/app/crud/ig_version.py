"""CRUD operations for IGVersion model."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import BaseCRUD
from app.models.ig_version import IGVersion
from app.schemas.ig_version import IGVersionCreate, IGVersionUpdate


class IGVersionCRUD(BaseCRUD[IGVersion, IGVersionCreate, IGVersionUpdate]):
    """CRUD operations for Implementation Guide versions."""

    async def get_all(
        self,
        db: AsyncSession,
        *,
        standard_type: Optional[str] = None,
        active_only: bool = False
    ) -> List[IGVersion]:
        """Get all IG versions, optionally filtered by standard type and active status.
        
        Args:
            db: Database session
            standard_type: Optional filter for SDTM or ADaM
            active_only: If True, only return active versions
            
        Returns:
            List of IG versions ordered by standard_type and version
        """
        query = select(self.model)
        
        if standard_type:
            query = query.where(self.model.standard_type == standard_type)
        
        if active_only:
            query = query.where(self.model.is_active == True)
        
        query = query.order_by(self.model.standard_type, self.model.version)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_standard_and_version(
        self,
        db: AsyncSession,
        *,
        standard_type: str,
        version: str
    ) -> Optional[IGVersion]:
        """Get an IG version by standard type and version number.
        
        Args:
            db: Database session
            standard_type: SDTM or ADaM
            version: Version number (e.g., "3.2")
            
        Returns:
            IGVersion if found, None otherwise
        """
        result = await db.execute(
            select(self.model)
            .where(
                self.model.standard_type == standard_type,
                self.model.version == version
            )
        )
        return result.scalar_one_or_none()

    async def get_by_standard_type(
        self,
        db: AsyncSession,
        *,
        standard_type: str,
        active_only: bool = True
    ) -> List[IGVersion]:
        """Get all IG versions for a specific standard type.
        
        Args:
            db: Database session
            standard_type: SDTM or ADaM
            active_only: If True, only return active versions
            
        Returns:
            List of IG versions for the standard type
        """
        query = select(self.model).where(self.model.standard_type == standard_type)
        
        if active_only:
            query = query.where(self.model.is_active == True)
        
        query = query.order_by(self.model.version)
        
        result = await db.execute(query)
        return list(result.scalars().all())


# Create a global instance
ig_version = IGVersionCRUD(IGVersion)







