#!/usr/bin/env python3
"""Test minimal API endpoint functionality."""

import asyncio
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.reporting_effort_item import ReportingEffortItemCreate, ReportingEffortItem
from app.crud.reporting_effort_item import reporting_effort_item

app = FastAPI()

@app.post("/test-item", response_model=dict)
async def test_create_item(
    item_in: ReportingEffortItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Test item creation with minimal response."""
    try:
        # Create item
        created_item = await reporting_effort_item.create_with_details(
            db,
            obj_in=item_in,
            auto_create_tracker=True
        )
        
        # Return simple dict response
        return {
            "success": True,
            "id": created_item.id,
            "item_code": created_item.item_code,
            "item_type": created_item.item_type.value if hasattr(created_item.item_type, 'value') else str(created_item.item_type)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)