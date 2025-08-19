"""
CRUD Endpoint Factory - Phase 2C Implementation
Generic endpoint generators to reduce boilerplate code across FastAPI endpoints.
"""

from typing import Any, Dict, List, Optional, Type, Union, Callable
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.api.v1.utils.validation import (
    raise_not_found_exception,
    raise_business_logic_exception,
    raise_dependency_conflict_exception
)
from app.api.v1.utils.websocket_utils import broadcast_entity_change


# =============================================================================
# CRUD ENDPOINT PATTERNS (Phase 2C - Medium Priority)
# =============================================================================

def create_get_endpoint(
    crud_class: Any,
    response_model: Type[BaseModel],
    entity_type: str,
    dependencies: List[Callable] = None
) -> Callable:
    """
    Create a standardized GET endpoint for retrieving a single entity by ID.
    
    Args:
        crud_class: CRUD class instance with get() method
        response_model: Pydantic response model
        entity_type: Human-readable entity type for errors
        dependencies: Additional FastAPI dependencies
        
    Returns:
        FastAPI endpoint function
    """
    deps = dependencies or []
    
    async def get_entity(
        entity_id: int,
        db: AsyncSession = Depends(get_db),
        *args
    ) -> response_model:
        """Get entity by ID."""
        db_entity = await crud_class.get(db, id=entity_id)
        if not db_entity:
            raise_not_found_exception(entity_type, entity_id)
        return db_entity
    
    # Add dependencies
    for dep in deps:
        get_entity = Depends(dep)(get_entity)
    
    return get_entity


def create_list_endpoint(
    crud_class: Any,
    response_model: Type[BaseModel],
    pagination: bool = True,
    dependencies: List[Callable] = None
) -> Callable:
    """
    Create a standardized GET endpoint for listing entities with optional pagination.
    
    Args:
        crud_class: CRUD class instance with get_multi() method
        response_model: Pydantic response model (should be List[BaseModel])
        pagination: Whether to include skip/limit parameters
        dependencies: Additional FastAPI dependencies
        
    Returns:
        FastAPI endpoint function
    """
    deps = dependencies or []
    
    if pagination:
        async def list_entities(
            skip: int = Query(0, ge=0, description="Number of records to skip"),
            limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
            db: AsyncSession = Depends(get_db),
            *args
        ) -> List[response_model]:
            """List entities with pagination."""
            entities = await crud_class.get_multi(db, skip=skip, limit=limit)
            return entities
    else:
        async def list_entities(
            db: AsyncSession = Depends(get_db),
            *args
        ) -> List[response_model]:
            """List all entities."""
            entities = await crud_class.get_multi(db, skip=0, limit=1000)
            return entities
    
    # Add dependencies
    for dep in deps:
        list_entities = Depends(dep)(list_entities)
    
    return list_entities


def create_post_endpoint(
    crud_class: Any,
    create_model: Type[BaseModel],
    response_model: Type[BaseModel],
    entity_type: str,
    broadcast_func: Optional[Callable] = None,
    dependencies: List[Callable] = None
) -> Callable:
    """
    Create a standardized POST endpoint for creating entities.
    
    Args:
        crud_class: CRUD class instance with create() method
        create_model: Pydantic model for request body
        response_model: Pydantic model for response
        entity_type: Human-readable entity type for broadcasting
        broadcast_func: Optional WebSocket broadcast function
        dependencies: Additional FastAPI dependencies
        
    Returns:
        FastAPI endpoint function
    """
    deps = dependencies or []
    
    async def create_entity(
        entity_in: create_model,
        db: AsyncSession = Depends(get_db),
        *args
    ) -> response_model:
        """Create new entity."""
        try:
            created_entity = await crud_class.create(db, obj_in=entity_in)
            
            # Broadcast WebSocket event if function provided
            if broadcast_func:
                await broadcast_func(created_entity)
            
            return created_entity
            
        except Exception as e:
            # Handle common creation errors
            if "already exists" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            elif "constraint" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid {entity_type} data: {str(e)}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error creating {entity_type}"
                )
    
    # Add dependencies
    for dep in deps:
        create_entity = Depends(dep)(create_entity)
    
    return create_entity


def create_put_endpoint(
    crud_class: Any,
    update_model: Type[BaseModel],
    response_model: Type[BaseModel],
    entity_type: str,
    broadcast_func: Optional[Callable] = None,
    dependencies: List[Callable] = None
) -> Callable:
    """
    Create a standardized PUT endpoint for updating entities.
    
    Args:
        crud_class: CRUD class instance with get() and update() methods
        update_model: Pydantic model for request body
        response_model: Pydantic model for response
        entity_type: Human-readable entity type for errors/broadcasting
        broadcast_func: Optional WebSocket broadcast function
        dependencies: Additional FastAPI dependencies
        
    Returns:
        FastAPI endpoint function
    """
    deps = dependencies or []
    
    async def update_entity(
        entity_id: int,
        entity_in: update_model,
        db: AsyncSession = Depends(get_db),
        *args
    ) -> response_model:
        """Update entity by ID."""
        # Get existing entity
        db_entity = await crud_class.get(db, id=entity_id)
        if not db_entity:
            raise_not_found_exception(entity_type, entity_id)
        
        try:
            # Update entity
            updated_entity = await crud_class.update(db, db_obj=db_entity, obj_in=entity_in)
            
            # Broadcast WebSocket event if function provided
            if broadcast_func:
                await broadcast_func(updated_entity)
            
            return updated_entity
            
        except Exception as e:
            # Handle common update errors
            if "already exists" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            elif "constraint" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid {entity_type} data: {str(e)}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error updating {entity_type}"
                )
    
    # Add dependencies
    for dep in deps:
        update_entity = Depends(dep)(update_entity)
    
    return update_entity


def create_delete_endpoint(
    crud_class: Any,
    entity_type: str,
    broadcast_func: Optional[Callable] = None,
    dependency_checks: List[Dict[str, Any]] = None,
    dependencies: List[Callable] = None
) -> Callable:
    """
    Create a standardized DELETE endpoint with dependency checking.
    
    Args:
        crud_class: CRUD class instance with get() and delete() methods
        entity_type: Human-readable entity type for errors/broadcasting
        broadcast_func: Optional WebSocket broadcast function
        dependency_checks: List of dependency check configs:
                          [{"crud": dependent_crud, "method": "get_by_parent_id", 
                            "dependent_type": "database releases", "label_field": "database_release_label"}]
        dependencies: Additional FastAPI dependencies
        
    Returns:
        FastAPI endpoint function
    """
    deps = dependencies or []
    checks = dependency_checks or []
    
    async def delete_entity(
        entity_id: int,
        db: AsyncSession = Depends(get_db),
        *args
    ) -> Dict[str, str]:
        """Delete entity by ID with dependency checking."""
        # Get existing entity
        db_entity = await crud_class.get(db, id=entity_id)
        if not db_entity:
            raise_not_found_exception(entity_type, entity_id)
        
        # Check for dependent entities
        for check in checks:
            dependent_crud = check["crud"]
            method_name = check["method"]
            dependent_type = check["dependent_type"]
            label_field = check.get("label_field", "label")
            
            # Get dependent entities
            method = getattr(dependent_crud, method_name)
            dependent_entities = await method(db, **{check.get("param_name", f"{entity_type.lower()}_id"): entity_id})
            
            if dependent_entities:
                dependent_names = [getattr(entity, label_field) for entity in dependent_entities]
                entity_label = getattr(db_entity, check.get("entity_label_field", "label"), str(entity_id))
                
                raise_dependency_conflict_exception(
                    entity_type=entity_type,
                    entity_label=entity_label,
                    dependent_count=len(dependent_entities),
                    dependent_type=dependent_type,
                    dependent_names=dependent_names
                )
        
        try:
            # Delete entity
            deleted_entity = await crud_class.delete(db, id=entity_id)
            
            # Broadcast WebSocket event if function provided
            if broadcast_func:
                await broadcast_func(entity_id)
            
            return {"message": f"{entity_type} deleted successfully"}
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting {entity_type}: {str(e)}"
            )
    
    # Add dependencies
    for dep in deps:
        delete_entity = Depends(dep)(delete_entity)
    
    return delete_entity


def create_search_endpoint(
    crud_class: Any,
    response_model: Type[BaseModel],
    entity_type: str,
    search_method: str = "search",
    dependencies: List[Callable] = None
) -> Callable:
    """
    Create a standardized search endpoint for entities with search capability.
    
    Args:
        crud_class: CRUD class instance with search method
        response_model: Pydantic response model
        entity_type: Human-readable entity type for errors
        search_method: Name of the search method on CRUD class
        dependencies: Additional FastAPI dependencies
        
    Returns:
        FastAPI endpoint function
    """
    deps = dependencies or []
    
    async def search_entities(
        q: str = Query(..., min_length=1, description="Search term"),
        limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
        db: AsyncSession = Depends(get_db),
        *args
    ) -> List[response_model]:
        """Search entities by query term."""
        if not hasattr(crud_class, search_method):
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Search not implemented for {entity_type}"
            )
        
        try:
            search_func = getattr(crud_class, search_method)
            entities = await search_func(db, search_term=q, limit=limit)
            return entities
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error searching {entity_type}: {str(e)}"
            )
    
    # Add dependencies
    for dep in deps:
        search_entities = Depends(dep)(search_entities)
    
    return search_entities


def create_health_endpoint() -> Callable:
    """Create a standardized health check endpoint."""
    async def health_check() -> Dict[str, str]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": str(datetime.now()),
            "service": "PEARL API"
        }
    
    return health_check


class EndpointFactory:
    """
    Factory class for creating standardized CRUD endpoints with consistent patterns.
    Reduces boilerplate code and ensures consistent error handling across all endpoints.
    """
    
    def __init__(self, crud_class: Any, entity_type: str):
        self.crud_class = crud_class
        self.entity_type = entity_type
        
    def create_full_crud_router(
        self,
        create_model: Type[BaseModel],
        update_model: Type[BaseModel], 
        response_model: Type[BaseModel],
        broadcast_functions: Dict[str, Callable] = None,
        dependency_checks: List[Dict[str, Any]] = None,
        search_enabled: bool = False,
        pagination: bool = True
    ) -> APIRouter:
        """
        Create a complete CRUD router with all standard endpoints.
        
        Args:
            create_model: Pydantic model for POST requests
            update_model: Pydantic model for PUT requests
            response_model: Pydantic model for responses
            broadcast_functions: Dict with 'created', 'updated', 'deleted' WebSocket functions
            dependency_checks: Dependency check configuration for DELETE endpoint
            search_enabled: Whether to include search endpoint
            pagination: Whether list endpoint should include pagination
            
        Returns:
            Configured APIRouter with all CRUD endpoints
        """
        router = APIRouter()
        broadcasts = broadcast_functions or {}
        
        # GET /{entity_id} - Get single entity
        get_func = create_get_endpoint(
            self.crud_class, response_model, self.entity_type
        )
        router.add_api_route(
            "/{entity_id}",
            get_func,
            methods=["GET"],
            response_model=response_model,
            summary=f"Get {self.entity_type} by ID"
        )
        
        # GET / - List entities
        list_func = create_list_endpoint(
            self.crud_class, response_model, pagination
        )
        router.add_api_route(
            "/",
            list_func,
            methods=["GET"],
            response_model=List[response_model],
            summary=f"List {self.entity_type}s"
        )
        
        # POST / - Create entity
        create_func = create_post_endpoint(
            self.crud_class, create_model, response_model, 
            self.entity_type, broadcasts.get('created')
        )
        router.add_api_route(
            "/",
            create_func,
            methods=["POST"],
            response_model=response_model,
            status_code=status.HTTP_201_CREATED,
            summary=f"Create {self.entity_type}"
        )
        
        # PUT /{entity_id} - Update entity
        update_func = create_put_endpoint(
            self.crud_class, update_model, response_model,
            self.entity_type, broadcasts.get('updated')
        )
        router.add_api_route(
            "/{entity_id}",
            update_func,
            methods=["PUT"],
            response_model=response_model,
            summary=f"Update {self.entity_type}"
        )
        
        # DELETE /{entity_id} - Delete entity
        delete_func = create_delete_endpoint(
            self.crud_class, self.entity_type,
            broadcasts.get('deleted'), dependency_checks
        )
        router.add_api_route(
            "/{entity_id}",
            delete_func,
            methods=["DELETE"],
            response_model=Dict[str, str],
            summary=f"Delete {self.entity_type}"
        )
        
        # GET /search - Search entities (optional)
        if search_enabled:
            search_func = create_search_endpoint(
                self.crud_class, response_model, self.entity_type
            )
            router.add_api_route(
                "/search",
                search_func,
                methods=["GET"],
                response_model=List[response_model],
                summary=f"Search {self.entity_type}s"
            )
        
        return router
    
    def create_custom_endpoint(
        self,
        path: str,
        method: str,
        endpoint_func: Callable,
        response_model: Type[BaseModel] = None,
        summary: str = None
    ) -> Callable:
        """
        Create a custom endpoint with standardized error handling.
        
        Args:
            path: Endpoint path
            method: HTTP method
            endpoint_func: Custom endpoint function
            response_model: Optional response model
            summary: Endpoint summary for documentation
            
        Returns:
            Wrapped endpoint function with error handling
        """
        async def wrapped_endpoint(*args, **kwargs):
            try:
                return await endpoint_func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except Exception as e:
                # Convert other exceptions to HTTP 500
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error in {self.entity_type} operation: {str(e)}"
                )
        
        return wrapped_endpoint


# Utility functions for common endpoint patterns

def add_standard_routes(
    router: APIRouter,
    crud_class: Any,
    entity_type: str,
    models: Dict[str, Type[BaseModel]],
    broadcasts: Dict[str, Callable] = None,
    dependency_checks: List[Dict[str, Any]] = None
) -> None:
    """
    Add standard CRUD routes to an existing router.
    
    Args:
        router: FastAPI router to add routes to
        crud_class: CRUD class instance
        entity_type: Human-readable entity type
        models: Dict with 'create', 'update', 'response' model classes
        broadcasts: Dict with 'created', 'updated', 'deleted' functions
        dependency_checks: Dependency check configuration for DELETE
    """
    factory = EndpointFactory(crud_class, entity_type)
    
    # Add each endpoint individually for fine-grained control
    create_func = create_post_endpoint(
        crud_class, models['create'], models['response'],
        entity_type, broadcasts.get('created') if broadcasts else None
    )
    
    get_func = create_get_endpoint(
        crud_class, models['response'], entity_type
    )
    
    list_func = create_list_endpoint(
        crud_class, models['response']
    )
    
    update_func = create_put_endpoint(
        crud_class, models['update'], models['response'],
        entity_type, broadcasts.get('updated') if broadcasts else None
    )
    
    delete_func = create_delete_endpoint(
        crud_class, entity_type,
        broadcasts.get('deleted') if broadcasts else None,
        dependency_checks
    )
    
    # Add routes to router
    router.add_api_route("/", create_func, methods=["POST"], 
                        response_model=models['response'], status_code=201)
    router.add_api_route("/{entity_id}", get_func, methods=["GET"], 
                        response_model=models['response'])
    router.add_api_route("/", list_func, methods=["GET"], 
                        response_model=List[models['response']])
    router.add_api_route("/{entity_id}", update_func, methods=["PUT"], 
                        response_model=models['response'])
    router.add_api_route("/{entity_id}", delete_func, methods=["DELETE"],
                        response_model=Dict[str, str])