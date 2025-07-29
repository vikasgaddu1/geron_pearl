"""Database session and engine configuration."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Create async engine with proper configuration
engine = create_async_engine(
    settings.database_url,
    echo=settings.env == "development",
    pool_size=settings.db_pool_size,
    max_overflow=20,
    poolclass=NullPool if "sqlite" in settings.database_url else None,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields a database session.
    Ensures proper session cleanup and error handling.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()