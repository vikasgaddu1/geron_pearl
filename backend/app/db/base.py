"""Database base models and utilities."""

from sqlalchemy.orm import DeclarativeBase

# Create base class for all SQLAlchemy models
class Base(DeclarativeBase):
    pass