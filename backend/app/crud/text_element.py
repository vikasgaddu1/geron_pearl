"""CRUD operations for TextElement model."""

from typing import List, Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.text_element import TextElement, TextElementType
from app.models.package_tlf_details import PackageTlfDetails
from app.models.package_item_footnote import PackageItemFootnote
from app.models.package_item_acronym import PackageItemAcronym
from app.models.package_item import PackageItem
from app.schemas.text_element import TextElementCreate, TextElementUpdate


class TextElementCRUD:
    """CRUD operations for TextElement model."""
    
    async def create(self, db: AsyncSession, *, obj_in: TextElementCreate) -> TextElement:
        """Create a new text element."""
        db_obj = TextElement(
            type=obj_in.type,
            label=obj_in.label,
            content=obj_in.content
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
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for duplicate checking: remove spaces and convert to uppercase."""
        return text.replace(" ", "").upper() if text else ""

    async def check_duplicate(
        self, db: AsyncSession, *, label: str, content: str, type: TextElementType, exclude_id: Optional[int] = None
    ) -> Optional[TextElement]:
        """
        Check if a text element with the same normalized label AND content already exists for the given type.

        Args:
            label: The label to check for duplicates
            content: The content to check for duplicates
            type: The type of text element
            exclude_id: ID to exclude from the check (useful for updates)

        Returns:
            The existing TextElement if duplicate found, None otherwise
        """
        normalized_label = self._normalize_text(label)
        normalized_content = self._normalize_text(content or "")

        # Build query to find elements of the same type where normalized label AND content match
        query = select(TextElement).where(
            TextElement.type == type,
            func.upper(func.replace(TextElement.label, ' ', '')) == normalized_label,
            func.upper(func.replace(func.coalesce(TextElement.content, ''), ' ', '')) == normalized_content
        )

        # Exclude the current record if updating
        if exclude_id is not None:
            query = query.where(TextElement.id != exclude_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()


    async def get_usage_references(
        self, db: AsyncSession, *, id: int
    ) -> dict:
        """
        Check if a text element is being used by any package items.

        Returns a dictionary with:
        - tlf_titles: list of package items using this as a title
        - tlf_populations: list of package items using this as a population flag
        - tlf_ich_categories: list of package items using this as an ICH category
        - footnotes: list of package items using this as a footnote
        - acronyms: list of package items using this as an acronym
        """
        references = {
            "tlf_titles": [],
            "tlf_populations": [],
            "tlf_ich_categories": [],
            "footnotes": [],
            "acronyms": [],
        }

        # Check package_tlf_details for title references
        result = await db.execute(
            select(PackageItem.item_code, PackageTlfDetails.id)
            .join(PackageItem, PackageItem.id == PackageTlfDetails.package_item_id)
            .where(PackageTlfDetails.title_id == id)
        )
        for row in result.all():
            references["tlf_titles"].append(row[0])

        # Check package_tlf_details for population flag references
        result = await db.execute(
            select(PackageItem.item_code, PackageTlfDetails.id)
            .join(PackageItem, PackageItem.id == PackageTlfDetails.package_item_id)
            .where(PackageTlfDetails.population_flag_id == id)
        )
        for row in result.all():
            references["tlf_populations"].append(row[0])

        # Check package_tlf_details for ICH category references
        result = await db.execute(
            select(PackageItem.item_code, PackageTlfDetails.id)
            .join(PackageItem, PackageItem.id == PackageTlfDetails.package_item_id)
            .where(PackageTlfDetails.ich_category_id == id)
        )
        for row in result.all():
            references["tlf_ich_categories"].append(row[0])

        # Check package_item_footnotes
        result = await db.execute(
            select(PackageItem.item_code)
            .join(PackageItemFootnote, PackageItem.id == PackageItemFootnote.package_item_id)
            .where(PackageItemFootnote.footnote_id == id)
        )
        for row in result.all():
            references["footnotes"].append(row[0])

        # Check package_item_acronyms
        result = await db.execute(
            select(PackageItem.item_code)
            .join(PackageItemAcronym, PackageItem.id == PackageItemAcronym.package_item_id)
            .where(PackageItemAcronym.acronym_id == id)
        )
        for row in result.all():
            references["acronyms"].append(row[0])

        return references

    def has_references(self, references: dict) -> bool:
        """Check if any references exist."""
        return any(len(refs) > 0 for refs in references.values())

    def format_reference_error(self, references: dict) -> str:
        """Format reference error message."""
        messages = []
        if references["tlf_titles"]:
            messages.append(f"title for TLFs: {', '.join(references['tlf_titles'])}")
        if references["tlf_populations"]:
            messages.append(f"population flag for TLFs: {', '.join(references['tlf_populations'])}")
        if references["tlf_ich_categories"]:
            messages.append(f"ICH category for TLFs: {', '.join(references['tlf_ich_categories'])}")
        if references["footnotes"]:
            messages.append(f"footnote for TLFs: {', '.join(references['footnotes'])}")
        if references["acronyms"]:
            messages.append(f"acronym for TLFs: {', '.join(references['acronyms'])}")
        return f"Cannot delete: this text element is used as {'; '.join(messages)}. Remove these references first."

    async def get_all_usage_counts(self, db: AsyncSession) -> dict[int, int]:
        """
        Get usage counts for all text elements in a single efficient query.

        Returns a dictionary mapping text_element_id -> usage_count
        """
        from sqlalchemy import union_all, literal_column

        # Build subqueries for each usage type
        # TLF titles
        title_query = (
            select(PackageTlfDetails.title_id.label('text_element_id'))
            .where(PackageTlfDetails.title_id.isnot(None))
        )

        # TLF population flags
        population_query = (
            select(PackageTlfDetails.population_flag_id.label('text_element_id'))
            .where(PackageTlfDetails.population_flag_id.isnot(None))
        )

        # TLF ICH categories
        ich_query = (
            select(PackageTlfDetails.ich_category_id.label('text_element_id'))
            .where(PackageTlfDetails.ich_category_id.isnot(None))
        )

        # Footnotes
        footnote_query = (
            select(PackageItemFootnote.footnote_id.label('text_element_id'))
        )

        # Acronyms
        acronym_query = (
            select(PackageItemAcronym.acronym_id.label('text_element_id'))
        )

        # Union all queries and count occurrences
        all_usages = union_all(
            title_query,
            population_query,
            ich_query,
            footnote_query,
            acronym_query
        ).subquery()

        # Count by text_element_id
        count_query = (
            select(
                all_usages.c.text_element_id,
                func.count().label('usage_count')
            )
            .group_by(all_usages.c.text_element_id)
        )

        result = await db.execute(count_query)

        # Build dictionary of id -> count
        usage_counts = {}
        for row in result.all():
            usage_counts[row[0]] = row[1]

        return usage_counts

    async def get_multi_with_usage(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[dict]:
        """Get multiple text elements with usage counts."""
        # Get text elements
        text_elements = await self.get_multi(db, skip=skip, limit=limit)

        # Get all usage counts
        usage_counts = await self.get_all_usage_counts(db)

        # Combine
        result = []
        for te in text_elements:
            count = usage_counts.get(te.id, 0)
            result.append({
                "id": te.id,
                "type": te.type,
                "label": te.label,
                "content": te.content,
                "created_at": te.created_at,
                "updated_at": te.updated_at,
                "usage_count": count,
                "is_used": count > 0
            })

        return result

    async def get_by_type_with_usage(
        self, db: AsyncSession, *, type: TextElementType, skip: int = 0, limit: int = 100
    ) -> list[dict]:
        """Get text elements by type with usage counts."""
        # Get text elements
        text_elements = await self.get_by_type(db, type=type, skip=skip, limit=limit)

        # Get all usage counts
        usage_counts = await self.get_all_usage_counts(db)

        # Combine
        result = []
        for te in text_elements:
            count = usage_counts.get(te.id, 0)
            result.append({
                "id": te.id,
                "type": te.type,
                "label": te.label,
                "content": te.content,
                "created_at": te.created_at,
                "updated_at": te.updated_at,
                "usage_count": count,
                "is_used": count > 0
            })

        return result


# Create a global instance
text_element = TextElementCRUD()