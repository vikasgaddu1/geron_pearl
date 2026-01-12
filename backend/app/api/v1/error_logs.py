"""Error Logs API endpoints."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.crud.error_log import error_log as error_crud
from app.crud import user
from app.db.session import get_db
from app.schemas.error_log import (
    ErrorLog,
    ErrorLogWithDetails,
    FrontendErrorReport,
    ErrorLogSummary
)
from app.models.error_log import ErrorLog as ErrorLogModel
from app.models.user import User as UserModel
from app.core.security import require_admin, get_current_user

router = APIRouter()

# Optional security for the report endpoint
optional_security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: AsyncSession = Depends(get_db)
) -> Optional[UserModel]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None
    try:
        from app.core.security import decode_token
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        user_id = int(user_id_str)
        result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        return result.scalar_one_or_none()
    except Exception:
        return None


@router.get("/", response_model=List[ErrorLogWithDetails])
async def get_error_logs(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source: Optional[str] = Query(None, description="Filter by source: BACKEND or FRONTEND"),
    severity: Optional[str] = Query(None, description="Filter by severity: INFO, WARNING, ERROR, CRITICAL"),
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter logs after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs before this date"),
    current_user: UserModel = Depends(require_admin())
) -> List[ErrorLogWithDetails]:
    """
    Get error logs with filtering options (admin only).

    Parameters:
    - source: Filter by BACKEND or FRONTEND
    - severity: Filter by INFO, WARNING, ERROR, CRITICAL
    - error_type: Filter by error type/category
    - user_id: Filter by user who encountered error
    - start_date: Filter logs after this date
    - end_date: Filter logs before this date
    """
    try:
        logs = await error_crud.get_multi(
            db,
            skip=skip,
            limit=limit,
            source=source,
            severity=severity,
            error_type=error_type,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )

        # Enrich with user details
        enriched_logs = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "source": log.source,
                "severity": log.severity,
                "error_type": log.error_type,
                "message": log.message,
                "stack_trace": log.stack_trace,
                "request_method": log.request_method,
                "request_path": log.request_path,
                "request_body": log.request_body,
                "response_status": log.response_status,
                "user_id": log.user_id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "component_name": log.component_name,
                "browser_info": log.browser_info,
                "correlation_id": log.correlation_id,
                "created_at": log.created_at,
                "user_name": None,
                "user_email": None
            }

            if log.user_id:
                db_user = await user.get(db, id=log.user_id)
                if db_user:
                    log_dict["user_name"] = db_user.username
                    log_dict["user_email"] = db_user.email

            enriched_logs.append(ErrorLogWithDetails(**log_dict))

        return enriched_logs

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve error logs: {str(e)}"
        )


@router.get("/summary", response_model=ErrorLogSummary)
async def get_error_summary(
    *,
    db: AsyncSession = Depends(get_db),
    days: int = Query(7, ge=1, le=90, description="Number of days to include"),
    current_user: UserModel = Depends(require_admin())
) -> ErrorLogSummary:
    """
    Get error log summary for the last N days (admin only).
    """
    try:
        stats = await error_crud.get_statistics(db, days=days)
        return ErrorLogSummary(**stats)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate error summary: {str(e)}"
        )


@router.get("/{error_id}", response_model=ErrorLogWithDetails)
async def get_error_log(
    *,
    db: AsyncSession = Depends(get_db),
    error_id: int,
    current_user: UserModel = Depends(require_admin())
) -> ErrorLogWithDetails:
    """
    Get a single error log by ID (admin only).
    """
    try:
        log = await error_crud.get(db, id=error_id)
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Error log not found"
            )

        log_dict = {
            "id": log.id,
            "source": log.source,
            "severity": log.severity,
            "error_type": log.error_type,
            "message": log.message,
            "stack_trace": log.stack_trace,
            "request_method": log.request_method,
            "request_path": log.request_path,
            "request_body": log.request_body,
            "response_status": log.response_status,
            "user_id": log.user_id,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "component_name": log.component_name,
            "browser_info": log.browser_info,
            "correlation_id": log.correlation_id,
            "created_at": log.created_at,
            "user_name": None,
            "user_email": None
        }

        if log.user_id:
            db_user = await user.get(db, id=log.user_id)
            if db_user:
                log_dict["user_name"] = db_user.username
                log_dict["user_email"] = db_user.email

        return ErrorLogWithDetails(**log_dict)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve error log: {str(e)}"
        )


@router.post("/report", status_code=status.HTTP_201_CREATED)
async def report_frontend_error(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    error_report: FrontendErrorReport,
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
) -> Dict[str, str]:
    """
    Report a frontend error (public endpoint).

    No authentication required to allow capturing errors during login/auth flows.
    User is associated if authenticated.
    """
    try:
        await error_crud.log_error(
            db,
            source="FRONTEND",
            severity=error_report.severity,
            error_type=error_report.error_type,
            message=error_report.message[:2000] if error_report.message else "",
            stack_trace=error_report.stack_trace[:10000] if error_report.stack_trace else None,
            request_path=error_report.request_path,
            component_name=error_report.component_name,
            browser_info=error_report.browser_info,
            user_id=current_user.id if current_user else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            correlation_id=error_report.correlation_id
        )
        return {"status": "logged"}
    except Exception:
        # Best-effort - don't fail on logging errors
        return {"status": "failed"}


@router.delete("/cleanup")
async def cleanup_old_logs(
    *,
    db: AsyncSession = Depends(get_db),
    days_to_keep: int = Query(30, ge=7, le=365, description="Number of days to keep"),
    current_user: UserModel = Depends(require_admin())
) -> Dict[str, Any]:
    """
    Delete error logs older than specified days (admin only).

    Parameters:
    - days_to_keep: Number of days of logs to keep (minimum 7)
    """
    try:
        count = await error_crud.cleanup_old_logs(db, days_to_keep=days_to_keep)
        return {
            "message": "Cleanup completed successfully",
            "logs_deleted": count,
            "days_kept": days_to_keep
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup error logs: {str(e)}"
        )
