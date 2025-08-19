"""Utilities for deletion protection and referential integrity."""

from typing import Any, List, Callable, Awaitable
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


async def check_deletion_dependencies(
    db: AsyncSession,
    entity_name: str,
    entity_label: str,
    dependencies: List[tuple[Callable[[AsyncSession, int], Awaitable[List[Any]]], str, str]]
) -> None:
    """
    Check for dependent entities before allowing deletion.
    
    Args:
        db: Database session
        entity_name: Name of the entity being deleted (e.g., "study")
        entity_label: Label/name of the specific entity instance
        dependencies: List of tuples containing:
            - dependency_query_func: Async function to query dependent entities
            - dependent_type_singular: Name of dependent type singular (e.g., "database release")  
            - dependent_type_plural: Name of dependent type plural (e.g., "database releases")
            - label_attribute: Attribute name to get the label from dependent entity
    
    Raises:
        HTTPException: If dependent entities exist
        
    Example:
        await check_deletion_dependencies(
            db=db,
            entity_name="study",
            entity_label=study.study_label,
            dependencies=[
                (
                    lambda db, id: database_release_crud.get_by_study_id(db, study_id=id),
                    "database release",
                    "database releases", 
                    "database_release_label"
                )
            ]
        )
    """
    for dependency_query_func, dependent_type_singular, dependent_type_plural, label_attribute in dependencies:
        # Extract entity ID from the dependency query function
        # This is a bit hacky but works for our current patterns
        dependent_entities = await dependency_query_func(db)
        
        if dependent_entities:
            # Get labels from dependent entities (limit to first 5 for readability)
            dependent_labels = []
            for entity in dependent_entities[:5]:
                if hasattr(entity, label_attribute):
                    dependent_labels.append(getattr(entity, label_attribute))
                else:
                    dependent_labels.append(f"ID {entity.id}")
            
            count = len(dependent_entities)
            type_name = dependent_type_plural if count > 1 else dependent_type_singular
            labels_text = ", ".join(dependent_labels)
            
            # Add "and X more" if we have more than 5
            if count > 5:
                labels_text += f" (and {count - 5} more)"
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete {entity_name} '{entity_label}': {count} associated {type_name}(s) exist: {labels_text}. Please delete all associated {dependent_type_plural} first."
            )


async def check_study_deletion_dependencies(
    db: AsyncSession,
    study_id: int,
    study_label: str,
    database_release_crud: Any
) -> None:
    """Check study deletion dependencies."""
    dependent_releases = await database_release_crud.get_by_study_id(db, study_id=study_id)
    
    if dependent_releases:
        release_labels = [release.database_release_label for release in dependent_releases[:5]]
        count = len(dependent_releases)
        labels_text = ", ".join(release_labels)
        
        if count > 5:
            labels_text += f" (and {count - 5} more)"
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete study '{study_label}': {count} associated database release(s) exist: {labels_text}. Please delete all associated database releases first."
        )


async def check_database_release_deletion_dependencies(
    db: AsyncSession,
    database_release_id: int,
    database_release_label: str,
    reporting_effort_crud: Any
) -> None:
    """Check database release deletion dependencies."""
    dependent_efforts = await reporting_effort_crud.get_by_database_release_id(db, database_release_id=database_release_id)
    
    if dependent_efforts:
        effort_labels = [effort.reporting_effort_label for effort in dependent_efforts[:5]]
        count = len(dependent_efforts)
        labels_text = ", ".join(effort_labels)
        
        if count > 5:
            labels_text += f" (and {count - 5} more)"
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete database release '{database_release_label}': {count} associated reporting effort(s) exist: {labels_text}. Please delete all associated reporting efforts first."
        )


async def check_package_deletion_dependencies(
    db: AsyncSession,
    package_id: int,
    package_name: str,
    package_item_crud: Any
) -> None:
    """Check package deletion dependencies."""
    dependent_items = await package_item_crud.get_by_package_id(db, package_id=package_id)
    
    if dependent_items:
        # Get item codes or IDs for display
        item_labels = []
        for item in dependent_items[:5]:
            if hasattr(item, 'item_code'):
                item_labels.append(item.item_code)
            else:
                item_labels.append(f"Item {item.id}")
        
        count = len(dependent_items)
        labels_text = ", ".join(item_labels)
        
        if count > 5:
            labels_text += f" (and {count - 5} more)"
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete package '{package_name}': {count} associated package item(s) exist: {labels_text}. Please delete all associated package items first."
        )