from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, UserDepartment


class UserBase(BaseModel):
    username: str = Field(..., min_length=1, description="Username must be at least 1 character")
    role: UserRole = Field(default=UserRole.VIEWER, description="User role")
    department: Optional[str] = Field(None, description="User department")


class UserCreate(UserBase):
    email: EmailStr = Field(..., description="User email address (required for authentication)")
    password: str = Field(..., min_length=8, max_length=100, description="User password (minimum 8 characters)")
    generate_password: Optional[bool] = Field(False, description="Whether to auto-generate password (client-side)")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = Field(None, description="User email address")
    password: Optional[str] = Field(None, min_length=8, max_length=100, description="New password (optional, only set if provided)")
    role: Optional[UserRole] = None
    department: Optional[str] = None


class UserInDBBase(UserBase):
    id: int
    email: Optional[str] = Field(default=None, description="User email address")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    pass