#!/usr/bin/env python3
"""Debug script for TextElement CRUD operations."""

import asyncio
from app.db.session import AsyncSessionLocal
from app.models.text_element import TextElementType
from app.crud import text_element
from app.schemas.text_element import TextElementCreate

async def test_text_element_crud():
    """Test TextElement CRUD operations directly."""
    print("🔍 Testing TextElement CRUD operations...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Test creating a text element
            text_element_data = TextElementCreate(
                type=TextElementType.title,
                label="Test Title Direct"
            )
            
            print(f"📝 Creating text element: {text_element_data}")
            created_element = await text_element.create(db, obj_in=text_element_data)
            print(f"✅ Created: {created_element.type.value} - {created_element.label} (ID: {created_element.id})")
            
            # Test retrieving the text element
            print(f"📄 Retrieving text element by ID: {created_element.id}")
            retrieved_element = await text_element.get(db, id=created_element.id)
            if retrieved_element:
                print(f"✅ Retrieved: {retrieved_element.type.value} - {retrieved_element.label}")
            else:
                print("❌ Could not retrieve text element")
            
            # Test updating the text element
            print("✏️ Updating text element label...")
            from app.schemas.text_element import TextElementUpdate
            update_data = TextElementUpdate(label="Updated Test Title Direct")
            updated_element = await text_element.update(db, db_obj=created_element, obj_in=update_data)
            print(f"✅ Updated: {updated_element.label}")
            
            # Test listing text elements
            print("📋 Listing all text elements...")
            all_elements = await text_element.get_multi(db, skip=0, limit=10)
            print(f"✅ Found {len(all_elements)} text elements")
            for elem in all_elements:
                print(f"  - {elem.type.value}: {elem.label[:50]}...")
            
            # Test filtering by type
            print("🔍 Filtering by type 'title'...")
            title_elements = await text_element.get_by_type(db, type=TextElementType.title, skip=0, limit=10)
            print(f"✅ Found {len(title_elements)} title elements")
            
            # Test search
            print("🔍 Searching for 'Test'...")
            search_results = await text_element.search_by_label(db, search_term="Test", skip=0, limit=10)
            print(f"✅ Found {len(search_results)} search results")
            
            # Test delete
            print("🗑️ Deleting text element...")
            deleted_element = await text_element.delete(db, id=created_element.id)
            print(f"✅ Deleted: {deleted_element.type.value} - {deleted_element.label}")
            
            print("✅ All TextElement CRUD operations completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during CRUD operations: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_text_element_crud())