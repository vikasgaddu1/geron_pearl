"""Database initialization utilities."""

import asyncio
import logging
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import text

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import study  # Import to register models with Base

logger = logging.getLogger(__name__)


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