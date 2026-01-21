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
from app.models.super_admin import SuperAdmin

logger = logging.getLogger(__name__)

# Default admin credentials
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

# Default super admin credentials
DEFAULT_SUPER_ADMIN_EMAIL = "superadmin@pearl.local"
DEFAULT_SUPER_ADMIN_PASSWORD = "superadmin123"


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


async def create_default_tenant() -> int:
    """
    Create default tenant if it doesn't exist.
    Returns the tenant ID.

    Note: This should be called AFTER seed_subscription_plans() so we can
    assign a default plan to the tenant.
    """
    from app.models.tenant import Tenant, SubscriptionStatus
    from app.models.tenant_settings import TenantSettings
    from app.models.subscription_plan import SubscriptionPlan

    async with AsyncSessionLocal() as session:
        try:
            # Check if default tenant exists
            result = await session.execute(
                select(Tenant).where(Tenant.id == 1)
            )
            existing_tenant = result.scalar_one_or_none()

            if existing_tenant:
                # Update plan_id if not set
                if not existing_tenant.plan_id:
                    plan_result = await session.execute(
                        select(SubscriptionPlan).where(SubscriptionPlan.name == "professional")
                    )
                    plan = plan_result.scalar_one_or_none()
                    if plan:
                        existing_tenant.plan_id = plan.id
                        await session.commit()
                        logger.info(f"Assigned Professional plan to default tenant")
                logger.info("Default tenant already exists")
                return existing_tenant.id

            # Get the Professional plan for the default tenant (dev/demo purposes)
            plan_result = await session.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.name == "professional")
            )
            plan = plan_result.scalar_one_or_none()

            # Create default tenant
            default_tenant = Tenant(
                id=1,
                name="default",
                display_name="Default Tenant",
                subscription_status=SubscriptionStatus.active,
                plan_id=plan.id if plan else None,
                is_active=True,
                onboarding_completed=True,
                sample_data_seeded=False
            )
            session.add(default_tenant)
            await session.flush()  # Get the ID

            # Create tenant settings
            tenant_settings = TenantSettings(
                tenant_id=default_tenant.id,
                timezone="UTC",
                date_format="YYYY-MM-DD",
                time_format="HH:mm"
            )
            session.add(tenant_settings)
            await session.commit()

            logger.info(f"Created default tenant: {default_tenant.name}")
            return default_tenant.id

        except Exception as e:
            logger.error(f"Error creating default tenant: {e}")
            await session.rollback()
            raise


async def create_default_admin_user(tenant_id: int = 1) -> None:
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

            # Create admin user with tenant_id
            admin_user = User(
                tenant_id=tenant_id,
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


async def create_default_super_admin() -> None:
    """
    Create a default super admin user for platform administration.
    Super admins can manage all tenants and have platform-level access.
    """
    from app.core.security import get_password_hash

    async with AsyncSessionLocal() as session:
        try:
            # Check if super admin already exists
            result = await session.execute(
                select(SuperAdmin).where(SuperAdmin.email == DEFAULT_SUPER_ADMIN_EMAIL)
            )
            existing_super_admin = result.scalar_one_or_none()

            if existing_super_admin:
                logger.info(f"Default super admin '{DEFAULT_SUPER_ADMIN_EMAIL}' already exists")
                return

            # Create super admin
            super_admin = SuperAdmin(
                email=DEFAULT_SUPER_ADMIN_EMAIL,
                name="Super Admin",
                password_hash=get_password_hash(DEFAULT_SUPER_ADMIN_PASSWORD),
                is_active=True,
                mfa_enabled=False,  # Should be enabled in production
            )
            session.add(super_admin)
            await session.commit()

            logger.info(f"Created default super admin: {DEFAULT_SUPER_ADMIN_EMAIL}")
            logger.info(f"Default super admin password: {DEFAULT_SUPER_ADMIN_PASSWORD}")
            logger.info("⚠️  IMPORTANT: Change the default super admin password and enable MFA!")

        except Exception as e:
            logger.error(f"Error creating default super admin: {e}")
            await session.rollback()
            raise


async def seed_subscription_plans() -> None:
    """
    Seed subscription plans with Stripe price IDs from environment.

    Plans are created/updated based on DEFAULT_PLANS in subscription_plan.py.
    Stripe price IDs are loaded from environment variables.
    """
    from app.models.subscription_plan import SubscriptionPlan, DEFAULT_PLANS

    # Map plan names to environment variable price IDs
    stripe_price_map = {
        "starter": {
            "monthly": settings.stripe_price_starter,
            "yearly": settings.stripe_price_starter_yearly,
        },
        "professional": {
            "monthly": settings.stripe_price_professional,
            "yearly": settings.stripe_price_professional_yearly,
        },
        "enterprise": {
            "monthly": settings.stripe_price_enterprise,
            "yearly": None,  # Enterprise has no yearly auto-signup
        },
    }

    async with AsyncSessionLocal() as session:
        try:
            for plan_data in DEFAULT_PLANS:
                plan_name = plan_data["name"]

                # Check if plan already exists
                result = await session.execute(
                    select(SubscriptionPlan).where(SubscriptionPlan.name == plan_name)
                )
                existing_plan = result.scalar_one_or_none()

                # Get Stripe price IDs from environment
                stripe_prices = stripe_price_map.get(plan_name, {})

                if existing_plan:
                    # Update existing plan with latest values
                    existing_plan.display_name = plan_data["display_name"]
                    existing_plan.description = plan_data["description"]
                    existing_plan.price_monthly = plan_data["price_monthly"]
                    existing_plan.price_yearly = plan_data.get("price_yearly")
                    existing_plan.max_users = plan_data["max_users"]
                    existing_plan.max_studies = plan_data["max_studies"]
                    existing_plan.max_storage_mb = plan_data["max_storage_mb"]
                    existing_plan.max_tracker_items = plan_data.get("max_tracker_items", 1000)
                    existing_plan.features = plan_data["features"]
                    existing_plan.sort_order = plan_data["sort_order"]
                    existing_plan.is_popular = plan_data.get("is_popular", False)
                    # Update Stripe price IDs from environment
                    existing_plan.stripe_price_id = stripe_prices.get("monthly")
                    existing_plan.stripe_price_id_yearly = stripe_prices.get("yearly")
                    logger.info(f"Updated subscription plan: {plan_name}")
                else:
                    # Create new plan
                    new_plan = SubscriptionPlan(
                        name=plan_name,
                        display_name=plan_data["display_name"],
                        description=plan_data["description"],
                        price_monthly=plan_data["price_monthly"],
                        price_yearly=plan_data.get("price_yearly"),
                        max_users=plan_data["max_users"],
                        max_studies=plan_data["max_studies"],
                        max_storage_mb=plan_data["max_storage_mb"],
                        max_tracker_items=plan_data.get("max_tracker_items", 1000),
                        features=plan_data["features"],
                        sort_order=plan_data["sort_order"],
                        is_popular=plan_data.get("is_popular", False),
                        stripe_price_id=stripe_prices.get("monthly"),
                        stripe_price_id_yearly=stripe_prices.get("yearly"),
                        is_active=True,
                    )
                    session.add(new_plan)
                    logger.info(f"Created subscription plan: {plan_name}")

            await session.commit()
            logger.info("Subscription plans seeded successfully")

        except Exception as e:
            logger.error(f"Error seeding subscription plans: {e}")
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

    # Seed subscription plans FIRST (so tenant can be assigned a plan)
    await seed_subscription_plans()

    # Create default tenant (required for multi-tenant setup)
    # This is called AFTER plans so we can assign a default plan
    tenant_id = await create_default_tenant()

    # Create default admin user
    await create_default_admin_user(tenant_id)

    # Create default super admin (platform administrator)
    await create_default_super_admin()


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