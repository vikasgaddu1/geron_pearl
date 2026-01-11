"""Database initialization utilities."""

import asyncio
import logging
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import text, select

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, AsyncSessionLocal
from app.models import study, database_release  # Import to register models with Base
from app.models.user import User, AuthProvider

logger = logging.getLogger(__name__)

# Default admin credentials
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


async def create_database_if_not_exists() -> None:
    """
    Create the database if it doesn't exist.
    """
    # Parse the database URL
    parsed_url = urlparse(settings.database_url)
    database_name = parsed_url.path.lstrip('/')
    
    # Create connection URL without database name (connect to postgres default db)
    base_url = settings.database_url.replace(f'/{database_name}', '/postgres')
    
    # Create engine for connecting to postgres database
    temp_engine = create_async_engine(base_url, isolation_level="AUTOCOMMIT")
    
    try:
        async with temp_engine.connect() as conn:
            # Check if database exists
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": database_name}
            )
            
            if not result.fetchone():
                logger.info(f"Creating database: {database_name}")
                # Create the database
                await conn.execute(text(f'CREATE DATABASE "{database_name}"'))
                logger.info(f"Database {database_name} created successfully")
            else:
                logger.info(f"Database {database_name} already exists")
    
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise
    finally:
        await temp_engine.dispose()


async def create_default_admin_user() -> None:
    """
    Create default admin user if it doesn't exist.
    This ensures there's always at least one admin account to log in with.
    """
    from app.core.security import get_password_hash
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if admin user already exists
            result = await session.execute(
                select(User).where(User.username == DEFAULT_ADMIN_USERNAME)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.info(f"Default admin user '{DEFAULT_ADMIN_USERNAME}' already exists")
                return
            
            # Create admin user
            admin_user = User(
                username=DEFAULT_ADMIN_USERNAME,
                email="admin@pearl.local",
                password_hash=get_password_hash(DEFAULT_ADMIN_PASSWORD),
                is_admin=True,
                is_active=True,
                auth_provider=AuthProvider.local,
                department="management"
            )
            session.add(admin_user)
            await session.commit()
            
            logger.info(f"Created default admin user: {DEFAULT_ADMIN_USERNAME}")
            logger.info(f"Default admin password: {DEFAULT_ADMIN_PASSWORD}")
            logger.info("⚠️  IMPORTANT: Change the default admin password after first login!")
            
        except Exception as e:
            logger.error(f"Error creating default admin user: {e}")
            await session.rollback()
            raise


async def init_db(engine: AsyncEngine) -> None:
    """
    Initialize database by creating the database (if needed) and all tables.
    This should be called during application startup.
    """
    # First ensure the database exists
    await create_database_if_not_exists()
    
    # Then create all tables
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    
    # Create default admin user
    await create_default_admin_user()


async def drop_db(engine: AsyncEngine) -> None:
    """
    Drop all database tables.
    WARNING: This will delete all data!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def main() -> None:
    """Main function for database initialization."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting database initialization...")
    
    try:
        await init_db(engine)
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    # Run database initialization directly
    asyncio.run(main())