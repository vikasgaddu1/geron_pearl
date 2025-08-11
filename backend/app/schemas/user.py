from pydantic import BaseModel, Field
from typing import Optional
from app.models.user import UserRole


class UserBase(BaseModel):
    username: str = Field(..., min_length=1, description="Username must be at least 1 character")
    role: UserRole = Field(default=UserRole.VIEWER, description="User role")


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1)
    role: Optional[UserRole] = None


class UserInDBBase(UserBase):
    id: int

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    pass