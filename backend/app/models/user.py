from enum import Enum
from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from app.db.base import Base


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class UserDepartment(str, Enum):
    PROGRAMMING = "programming"
    BIOSTATISTICS = "biostatistics"
    MANAGEMENT = "management"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER)
    department = Column(String(50), nullable=True)