"""CRUD operations for TextElement model."""

from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.text_element import TextElement, TextElementType
from app.schemas.text_element import TextElementCreate, TextElementUpdate


class TextElementCRUD:
    """CRUD operations for TextElement model."""
    
    async def create(self, db: AsyncSession, *, obj_in: TextElementCreate) -> TextElement:
        """Create a new text element."""
        db_obj = TextElement(
            type=obj_in.type,
            label=obj_in.label
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[TextElement]:
        """Get a text element by ID."""
        result = await db.execute(select(TextElement).where(TextElement.id == id))
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[TextElement]:
        """Get multiple text elements with pagination."""
        result = await db.execute(select(TextElement).offset(skip).limit(limit))
        return list(result.scalars().all())
    
    async def get_by_type(
        self, db: AsyncSession, *, type: TextElementType, skip: int = 0, limit: int = 100
    ) -> List[TextElement]:
        """Get text elements by type with pagination."""
        result = await db.execute(
            select(TextElement)
            .where(TextElement.type == type)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_type_and_label(
        self, db: AsyncSession, *, type: TextElementType, label: str
    ) -> Optional[TextElement]:
        """Get a text element by type and exact label."""
        result = await db.execute(
            select(TextElement)
            .where(TextElement.type == type)
            .where(TextElement.label == label)
        )
        return result.scalar_one_or_none()
    
    async def update(
        self, db: AsyncSession, *, db_obj: TextElement, obj_in: TextElementUpdate
    ) -> TextElement:
        """Update an existing text element."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: int) -> Optional[TextElement]:
        """Delete a text element by ID."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
    
    async def search_by_label(
        self, db: AsyncSession, *, search_term: str, skip: int = 0, limit: int = 100
    ) -> List[TextElement]:
        """Search text elements by label content."""
        result = await db.execute(
            select(TextElement)
            .where(TextElement.label.ilike(f"%{search_term}%"))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    def _normalize_label(self, label: str) -> str:
        """Normalize label for duplicate checking: remove spaces and convert to uppercase."""
        return label.replace(" ", "").upper()
    
    async def check_duplicate_label(
        self, db: AsyncSession, *, label: str, type: TextElementType, exclude_id: Optional[int] = None
    ) -> Optional[TextElement]:
        """
        Check if a text element with the same normalized label already exists for the given type.
        
        Args:
            label: The label to check for duplicates
            type: The type of text element
            exclude_id: ID to exclude from the check (useful for updates)
            
        Returns:
            The existing TextElement if duplicate found, None otherwise
        """
        normalized_input = self._normalize_label(label)
        
        # Build query to find elements of the same type where normalized labels match
        query = select(TextElement).where(
            TextElement.type == type,
            func.upper(func.replace(TextElement.label, ' ', '')) == normalized_input
        )
        
        # Exclude the current record if updating
        if exclude_id is not None:
            query = query.where(TextElement.id != exclude_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()


# Create a global instance
text_element = TextElementCRUD()