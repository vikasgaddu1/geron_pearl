"""
Script to reset users in the database.
Removes all existing users and creates three test users:
- test_admin (admin@pearl.com, password123, ADMIN)
- test_editor (editor@pearl.com, password123, EDITOR)
- test_viewer (viewer@pearl.com, password123, VIEWER)
"""

import asyncio
from sqlalchemy import select, delete, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine
from app.models.user import User, UserRole, AuthProvider
from app.core.security import get_password_hash


async def reset_users():
    """Delete all users and create test users."""
    async with AsyncSessionLocal() as session:
        try:
            # First, clear or delete records that reference users
            print("Clearing user references in related tables...")
            
            # Delete tracker comments (user_id is NOT NULL, so we can't set it to NULL)
            # Comments will be recreated as needed with new users
            comments_deleted = await session.execute(
                text("DELETE FROM tracker_comments")
            )
            print(f"  - Deleted {comments_deleted.rowcount} comment(s)")
            
            # Clear production_programmer_id and qc_programmer_id in tracker table
            await session.execute(
                text("UPDATE reporting_effort_item_tracker SET production_programmer_id = NULL, qc_programmer_id = NULL")
            )
            
            # Clear user_id in audit_log (should already be SET NULL, but just in case)
            await session.execute(
                text("UPDATE audit_log SET user_id = NULL")
            )
            
            await session.commit()
            print("Cleared user references")
            
            # Now delete all existing users
            print("Deleting all existing users...")
            result = await session.execute(delete(User))
            deleted_count = result.rowcount
            await session.commit()
            print(f"Deleted {deleted_count} user(s)")
            
            # Create test users
            test_users = [
                {
                    "username": "test_admin",
                    "email": "admin@pearl.com",
                    "password": "password123",
                    "role": UserRole.ADMIN,
                },
                {
                    "username": "test_editor",
                    "email": "editor@pearl.com",
                    "password": "password123",
                    "role": UserRole.EDITOR,
                },
                {
                    "username": "test_viewer",
                    "email": "viewer@pearl.com",
                    "password": "password123",
                    "role": UserRole.VIEWER,
                },
            ]
            
            print("\nCreating test users...")
            for user_data in test_users:
                password_hash = get_password_hash(user_data["password"])
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=password_hash,
                    role=user_data["role"],
                    auth_provider=AuthProvider.local,
                    is_active=True,
                )
                session.add(user)
                print(f"  - Created {user_data['username']} ({user_data['email']}) with role {user_data['role'].value}")
            
            await session.commit()
            print("\nSuccessfully reset users!")
            print("\nTest users created:")
            print("  Username: test_admin    | Email: admin@pearl.com   | Password: password123 | Role: ADMIN")
            print("  Username: test_editor   | Email: editor@pearl.com  | Password: password123 | Role: EDITOR")
            print("  Username: test_viewer   | Email: viewer@pearl.com | Password: password123 | Role: VIEWER")
            
        except Exception as e:
            await session.rollback()
            print(f"\nError resetting users: {e}")
            raise
        finally:
            await session.close()


async def main():
    """Main entry point."""
    try:
        await reset_users()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

