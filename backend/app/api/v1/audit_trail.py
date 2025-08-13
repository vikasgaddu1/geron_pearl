"""Audit Trail API endpoints."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.crud import audit_log as audit_crud, user
from app.db.session import get_db
from app.schemas.audit_log import AuditLog, AuditLogWithDetails
from app.models.audit_log import AuditLog as AuditLogModel
from app.models.user import UserRole

router = APIRouter()

def check_admin_access(request: Request):
    """Check if user has admin access."""
    # In production, get from session/token
    # For now, check header
    user_role = request.headers.get("X-User-Role", "viewer")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return True

@router.get("/", response_model=List[AuditLogWithDetails])
async def get_audit_logs(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    table_name: Optional[str] = None,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    _: bool = Depends(check_admin_access)
) -> List[AuditLogWithDetails]:
    """
    Get audit logs with filtering options (admin only).
    
    Parameters:
    - table_name: Filter by table name
    - user_id: Filter by user who performed action
    - action: Filter by action type (CREATE, UPDATE, DELETE)
    - start_date: Filter logs after this date
    - end_date: Filter logs before this date
    """
    try:
        # Build query
        query = select(AuditLogModel)
        
        # Apply filters
        filters = []
        if table_name:
            filters.append(AuditLogModel.table_name == table_name)
        if user_id:
            filters.append(AuditLogModel.user_id == user_id)
        if action:
            filters.append(AuditLogModel.action == action)
        if start_date:
            filters.append(AuditLogModel.created_at >= start_date)
        if end_date:
            filters.append(AuditLogModel.created_at <= end_date)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Order by most recent first
        query = query.order_by(desc(AuditLogModel.created_at))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        logs = list(result.scalars().all())
        
        # Enrich with user details
        enriched_logs = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "table_name": log.table_name,
                "record_id": log.record_id,
                "action": log.action,
                "user_id": log.user_id,
                "changes_json": log.changes_json,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at,
                "user_name": None,
                "user_email": None
            }
            
            if log.user_id:
                db_user = await user.get(db, id=log.user_id)
                if db_user:
                    log_dict["user_name"] = db_user.full_name or db_user.username
                    log_dict["user_email"] = db_user.email
            
            enriched_logs.append(AuditLogWithDetails(**log_dict))
        
        return enriched_logs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )

@router.get("/summary", response_model=Dict[str, Any])
async def get_audit_summary(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    days: int = Query(7, ge=1, le=365),
    _: bool = Depends(check_admin_access)
) -> Dict[str, Any]:
    """
    Get audit log summary for the last N days (admin only).
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get logs for date range
        query = select(AuditLogModel).where(
            AuditLogModel.created_at >= start_date
        )
        result = await db.execute(query)
        logs = list(result.scalars().all())
        
        # Calculate statistics
        stats = {
            "total_actions": len(logs),
            "actions_by_type": {},
            "actions_by_table": {},
            "actions_by_user": {},
            "actions_by_day": {}
        }
        
        for log in logs:
            # By action type
            if log.action not in stats["actions_by_type"]:
                stats["actions_by_type"][log.action] = 0
            stats["actions_by_type"][log.action] += 1
            
            # By table
            if log.table_name not in stats["actions_by_table"]:
                stats["actions_by_table"][log.table_name] = 0
            stats["actions_by_table"][log.table_name] += 1
            
            # By user
            if log.user_id:
                if log.user_id not in stats["actions_by_user"]:
                    stats["actions_by_user"][log.user_id] = {
                        "count": 0,
                        "username": None
                    }
                stats["actions_by_user"][log.user_id]["count"] += 1
            
            # By day
            day_key = log.created_at.date().isoformat()
            if day_key not in stats["actions_by_day"]:
                stats["actions_by_day"][day_key] = 0
            stats["actions_by_day"][day_key] += 1
        
        # Enrich user information
        for user_id in stats["actions_by_user"]:
            db_user = await user.get(db, id=user_id)
            if db_user:
                stats["actions_by_user"][user_id]["username"] = db_user.username
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate audit summary: {str(e)}"
        )

@router.get("/record/{table_name}/{record_id}", response_model=List[AuditLogWithDetails])
async def get_record_history(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    table_name: str,
    record_id: int,
    _: bool = Depends(check_admin_access)
) -> List[AuditLogWithDetails]:
    """
    Get complete audit history for a specific record (admin only).
    """
    try:
        # Get all logs for this record
        query = select(AuditLogModel).where(
            and_(
                AuditLogModel.table_name == table_name,
                AuditLogModel.record_id == record_id
            )
        ).order_by(desc(AuditLogModel.created_at))
        
        result = await db.execute(query)
        logs = list(result.scalars().all())
        
        # Enrich with user details
        enriched_logs = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "table_name": log.table_name,
                "record_id": log.record_id,
                "action": log.action,
                "user_id": log.user_id,
                "changes_json": log.changes_json,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at,
                "user_name": None,
                "user_email": None
            }
            
            if log.user_id:
                db_user = await user.get(db, id=log.user_id)
                if db_user:
                    log_dict["user_name"] = db_user.full_name or db_user.username
                    log_dict["user_email"] = db_user.email
            
            enriched_logs.append(AuditLogWithDetails(**log_dict))
        
        return enriched_logs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve record history: {str(e)}"
        )

@router.delete("/cleanup")
async def cleanup_old_logs(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    days_to_keep: int = Query(90, ge=30, le=365),
    _: bool = Depends(check_admin_access)
) -> Dict[str, Any]:
    """
    Delete audit logs older than specified days (admin only).
    
    Parameters:
    - days_to_keep: Number of days of logs to keep (minimum 30)
    """
    try:
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Count logs to be deleted
        count_query = select(AuditLogModel).where(
            AuditLogModel.created_at < cutoff_date
        )
        count_result = await db.execute(count_query)
        logs_to_delete = len(list(count_result.scalars().all()))
        
        # Delete old logs
        if logs_to_delete > 0:
            await audit_crud.cleanup_old_logs(db, days_to_keep=days_to_keep)
        
        return {
            "message": f"Cleanup completed successfully",
            "logs_deleted": logs_to_delete,
            "cutoff_date": cutoff_date.isoformat(),
            "days_kept": days_to_keep
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup audit logs: {str(e)}"
        )