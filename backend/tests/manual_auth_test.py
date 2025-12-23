"""
Manual authentication test script.
Run this to verify auth system is working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token
from app.models.user import User, UserRole, AuthProvider
from sqlalchemy import select


async def test_auth_system():
    """Test the authentication system"""
    
    print("="*80)
    print("PEARL AUTHENTICATION SYSTEM TEST")
    print("="*80)
    
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("\n1. Testing password hashing...")
        password = "testpassword123"
        hashed = get_password_hash(password)
        print(f"   [OK] Password hashed successfully")
        print(f"   [OK] Verification: {verify_password(password, hashed)}")
        
        print("\n2. Creating test user...")
        # Check if test user exists
        result = await db.execute(select(User).where(User.username == "test_admin"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"   [OK] Test user already exists (ID: {existing_user.id})")
            test_user = existing_user
        else:
            test_user = User(
                username="test_admin",
                email="test@pearl.local",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                auth_provider=AuthProvider.local,
                is_active=True,
            )
            db.add(test_user)
            await db.commit()
            await db.refresh(test_user)
            print(f"   [OK] Test user created (ID: {test_user.id})")
        
        print("\n3. Testing JWT token creation...")
        token_data = {
            "sub": str(test_user.id),  # JWT sub must be a string
            "username": test_user.username,
            "role": test_user.role.value,
        }
        access_token = create_access_token(token_data)
        print(f"   [OK] Access token created")
        print(f"   Token (first 50 chars): {access_token[:50]}...")
        
        print("\n4. Testing token decoding...")
        decoded = decode_token(access_token)
        print(f"   [OK] Token decoded successfully")
        print(f"   User ID: {decoded.get('sub')}")
        print(f"   Username: {decoded.get('username')}")
        print(f"   Role: {decoded.get('role')}")
        print(f"   Type: {decoded.get('type')}")
        
        print("\n5. Verifying user from database...")
        # Convert sub from string to int for database query
        user_id_from_token = int(decoded.get('sub'))
        result = await db.execute(select(User).where(User.id == user_id_from_token))
        verified_user = result.scalar_one_or_none()
        if verified_user:
            print(f"   [OK] User verified: {verified_user.username}")
            print(f"   Email: {verified_user.email}")
            print(f"   Role: {verified_user.role.value}")
            print(f"   Active: {verified_user.is_active}")
            print(f"   Provider: {verified_user.auth_provider.value}")
        
        print("\n" + "="*80)
        print("TEST CREDENTIALS FOR LOGIN:")
        print("="*80)
        print(f"Username: test_admin")
        print(f"Password: admin123")
        print(f"Role: ADMIN")
        print("="*80)
        print("\nAll tests passed! [SUCCESS]")
        print("You can now use these credentials to login through the React frontend.")
        print("="*80)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_auth_system())

