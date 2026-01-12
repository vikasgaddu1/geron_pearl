"""TextElement API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import text_element, audit_log
from app.db.session import get_db
from app.models.text_element import TextElementType
from app.schemas.text_element import TextElement, TextElementCreate, TextElementUpdate
from app.api.v1.websocket import broadcast_text_element_created, broadcast_text_element_updated, broadcast_text_element_deleted
from app.core.security import require_admin_or_lead
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=TextElement, status_code=status.HTTP_201_CREATED)
async def create_text_element(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    text_element_in: TextElementCreate,
    current_user: User = Depends(require_admin_or_lead()),
) -> TextElement:
    """
    Create a new text element.

    Requires: Admin or Study LEAD role (in any study).
    """
    try:
        # Check for duplicate label+content combination (case-insensitive, ignoring spaces)
        existing_element = await text_element.check_duplicate(
            db, label=text_element_in.label, content=text_element_in.content or "", type=text_element_in.type
        )
        if existing_element:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A {text_element_in.type.value} with this label and content already exists. Duplicate entries are not allowed."
            )

        created_text_element = await text_element.create(db, obj_in=text_element_in)
        print(f"TextElement created successfully: {created_text_element.type.value} - {created_text_element.label[:50]}... (ID: {created_text_element.id})")

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="text_elements",
                record_id=created_text_element.id,
                action="CREATE",
                user_id=current_user.id,
                changes={"type": created_text_element.type.value, "label": created_text_element.label},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")

        # Broadcast WebSocket event for real-time updates
        try:
            print(f"About to broadcast text_element_created...")
            await broadcast_text_element_created(created_text_element)
            print(f"Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"WebSocket broadcast error: {ws_error}")

        return created_text_element
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        print(f"Error creating text element: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create text element"
        )


@router.get("/", response_model=List[TextElement])
async def read_text_elements(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    type: Optional[TextElementType] = Query(None, description="Filter by text element type")
) -> List[TextElement]:
    """
    Retrieve text elements with optional filtering by type.
    """
    try:
        if type:
            text_elements = await text_element.get_by_type(db, type=type, skip=skip, limit=limit)
        else:
            text_elements = await text_element.get_multi(db, skip=skip, limit=limit)
        
        print(f"Retrieved {len(text_elements)} text elements")
        return text_elements
    except Exception as e:
        print(f"Error retrieving text elements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve text elements"
        )


@router.get("/search", response_model=List[TextElement])
async def search_text_elements(
    *,
    db: AsyncSession = Depends(get_db),
    q: str = Query(..., min_length=1, description="Search term"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
) -> List[TextElement]:
    """
    Search text elements by label content.
    """
    try:
        text_elements = await text_element.search_by_label(db, search_term=q, skip=skip, limit=limit)
        print(f"Found {len(text_elements)} text elements matching '{q}'")
        return text_elements
    except Exception as e:
        print(f"Error searching text elements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search text elements"
        )


@router.get("/{text_element_id}", response_model=TextElement)
async def read_text_element(
    *,
    db: AsyncSession = Depends(get_db),
    text_element_id: int,
) -> TextElement:
    """
    Get a specific text element by ID.
    """
    try:
        db_text_element = await text_element.get(db, id=text_element_id)
        if not db_text_element:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text element not found"
            )
        
        print(f"Retrieved text element: {db_text_element.type.value} - {db_text_element.label[:50]}...")
        return db_text_element
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving text element {text_element_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve text element"
        )


@router.put("/{text_element_id}", response_model=TextElement)
async def update_text_element(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    text_element_id: int,
    text_element_in: TextElementUpdate,
    current_user: User = Depends(require_admin_or_lead()),
) -> TextElement:
    """
    Update a text element.

    Requires: Admin or Study LEAD role (in any study).
    """
    try:
        db_text_element = await text_element.get(db, id=text_element_id)
        if not db_text_element:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text element not found"
            )

        # Capture old values for audit
        old_values = {"type": db_text_element.type.value, "label": db_text_element.label}

        # Check for duplicate label+content combination if any field is being updated
        if text_element_in.label is not None or text_element_in.type is not None or text_element_in.content is not None:
            # Use the new values if provided, otherwise use existing values
            check_label = text_element_in.label if text_element_in.label is not None else db_text_element.label
            check_content = text_element_in.content if text_element_in.content is not None else (db_text_element.content or "")
            check_type = text_element_in.type if text_element_in.type is not None else db_text_element.type

            existing_element = await text_element.check_duplicate(
                db, label=check_label, content=check_content, type=check_type, exclude_id=text_element_id
            )
            if existing_element:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A {check_type.value} with this label and content already exists. Duplicate entries are not allowed."
                )

        updated_text_element = await text_element.update(db, db_obj=db_text_element, obj_in=text_element_in)
        print(f"TextElement updated successfully: ID {updated_text_element.id}")

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="text_elements",
                record_id=updated_text_element.id,
                action="UPDATE",
                user_id=current_user.id,
                changes={"old": old_values, "new": {"type": updated_text_element.type.value, "label": updated_text_element.label}},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")

        # Broadcast WebSocket event for real-time updates
        try:
            print(f"About to broadcast text_element_updated...")
            await broadcast_text_element_updated(updated_text_element)
            print(f"Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"WebSocket broadcast error: {ws_error}")

        return updated_text_element
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating text element {text_element_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update text element"
        )


@router.delete("/{text_element_id}", response_model=TextElement)
async def delete_text_element(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    text_element_id: int,
    current_user: User = Depends(require_admin_or_lead()),
) -> TextElement:
    """
    Delete a text element.

    Requires: Admin or Study LEAD role (in any study).
    """
    try:
        db_text_element = await text_element.get(db, id=text_element_id)
        if not db_text_element:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text element not found"
            )

        # Capture values for audit before deletion
        deleted_type = db_text_element.type.value
        deleted_label = db_text_element.label

        deleted_text_element = await text_element.delete(db, id=text_element_id)
        print(f"TextElement deleted successfully: ID {text_element_id}")

        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="text_elements",
                record_id=text_element_id,
                action="DELETE",
                user_id=current_user.id,
                changes={"deleted": {"type": deleted_type, "label": deleted_label}},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")

        # Broadcast WebSocket event for real-time updates
        try:
            print(f"About to broadcast text_element_deleted...")
            await broadcast_text_element_deleted(deleted_text_element)
            print(f"Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"WebSocket broadcast error: {ws_error}")

        return deleted_text_element
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting text element {text_element_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete text element"
        )