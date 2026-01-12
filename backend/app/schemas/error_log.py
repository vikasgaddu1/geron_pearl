"""Pydantic schemas for ErrorLog."""

from typing import Optional, Literal, Dict, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ErrorLogBase(BaseModel):
    """Base schema for ErrorLog."""

    source: Literal["BACKEND", "FRONTEND"] = Field(..., description="Error source")
    severity: Literal["INFO", "WARNING", "ERROR", "CRITICAL"] = Field(..., description="Error severity")
    error_type: str = Field(..., max_length=100, description="Error type/category")
    message: str = Field(..., description="Error message")


class ErrorLogCreate(ErrorLogBase):
    """Schema for creating an ErrorLog entry (backend use)."""

    stack_trace: Optional[str] = None
    request_method: Optional[str] = Field(None, max_length=10)
    request_path: Optional[str] = Field(None, max_length=500)
    request_body: Optional[str] = None
    response_status: Optional[int] = None
    user_id: Optional[int] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None
    component_name: Optional[str] = Field(None, max_length=200)
    browser_info: Optional[str] = None
    correlation_id: Optional[str] = Field(None, max_length=36)


class FrontendErrorReport(BaseModel):
    """Schema for frontend error reports (public endpoint)."""

    severity: Literal["INFO", "WARNING", "ERROR", "CRITICAL"] = "ERROR"
    error_type: str = Field(..., max_length=100, description="Error type")
    message: str = Field(..., max_length=2000, description="Error message")
    stack_trace: Optional[str] = Field(None, max_length=10000)
    component_name: Optional[str] = Field(None, max_length=200)
    request_path: Optional[str] = Field(None, max_length=500, description="Page URL")
    browser_info: Optional[str] = Field(None, max_length=500)
    correlation_id: Optional[str] = Field(None, max_length=36)


class ErrorLogInDB(ErrorLogBase):
    """Schema for ErrorLog from database."""

    id: int
    stack_trace: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    request_body: Optional[str] = None
    response_status: Optional[int] = None
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    component_name: Optional[str] = None
    browser_info: Optional[str] = None
    correlation_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ErrorLog(ErrorLogInDB):
    """Schema for ErrorLog response."""
    pass


class ErrorLogWithDetails(ErrorLogInDB):
    """Schema for ErrorLog with user details."""

    user_name: Optional[str] = None
    user_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ErrorLogSummary(BaseModel):
    """Schema for error log statistics."""

    period_days: int
    total_errors: int
    by_severity: Dict[str, int]
    by_source: Dict[str, int]
    by_type: Dict[str, int]
    by_day: Dict[str, int]
    top_endpoints: List[Dict[str, Any]]
