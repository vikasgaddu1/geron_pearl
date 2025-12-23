#!/usr/bin/env python3
"""
Script to update python_only_tracker.md from JWT to session-based auth
"""

import re

# Read the file
with open('C:/python/PEARL/python_only_tracker.md', 'r', encoding='utf-8') as f:
    content = f.read()

changes_made = []

# 1. Update login endpoint (lines 756-793)
old_login = '''#### POST `/auth/login`
**Purpose:** Authenticate and receive JWT token

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**Response:** 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "john_doe",
    "full_name": "John Doe",
    "role": "EDITOR",
    "department": "programming",
    "permissions": {
      "can_create": true,
      "can_edit": true,
      "can_delete": false,
      "can_manage_users": false,
      "can_view_audit": false
    }
  }
}
```

**Usage in subsequent requests:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```'''

new_login = '''#### POST `/auth/login`
**Purpose:** Authenticate and create session cookie

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**Response:** 200 OK
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "full_name": "John Doe",
    "role": "EDITOR",
    "department": "programming",
    "permissions": {
      "can_create": true,
      "can_edit": true,
      "can_delete": false,
      "can_manage_users": false,
      "can_view_audit": false
    }
  }
}
```

**Response Headers:**
```
Set-Cookie: session_id=<secure_random_token>; HttpOnly; Secure; SameSite=Strict; Max-Age=28800
```

**Notes:**
- Session cookie is automatically included in subsequent requests by the browser
- Session expires after 8 hours (28800 seconds) of inactivity
- HttpOnly flag prevents JavaScript access (XSS protection)
- Secure flag ensures HTTPS-only transmission (in production)'''

if old_login in content:
    content = content.replace(old_login, new_login)
    changes_made.append('✓ Updated login endpoint')

# 2. Update /auth/me endpoint
old_me = '''#### GET `/auth/me`
**Purpose:** Get current user info from JWT token

**Headers:**
```
Authorization: Bearer <token>
```'''

new_me = '''#### GET `/auth/me`
**Purpose:** Get current user info from session cookie

**Headers:**
```
Cookie: session_id=<session_token>
```

**Notes:**
- Session cookie is automatically sent by the browser
- No need to manually include authorization headers'''

if old_me in content:
    content = content.replace(old_me, new_me)
    changes_made.append('✓ Updated /auth/me endpoint')

# 3. Update architecture diagram references
content = content.replace(
    '│  │  - JWT token validation',
    '│  │  - Session cookie validation'
)
content = content.replace(
    '│  │  - JWT token generation/validation',
    '│  │  - Session management and validation'
)
content = content.replace(
    'Reflex Frontend → POST /api/v1/studies (with JWT token)',
    'Reflex Frontend → POST /api/v1/studies (with session cookie)'
)
content = content.replace(
    'FastAPI Backend → Validates JWT → Checks role (EDITOR or ADMIN)',
    'FastAPI Backend → Validates session → Checks role (EDITOR or ADMIN)'
)
changes_made.append('✓ Updated architecture diagrams')

# 4. Update config.py comment
content = content.replace(
    '│   │   ├── config.py              # Settings (database URL, JWT secret, etc.)',
    '│   │   ├── config.py              # Settings (database URL, session secret, etc.)'
)
content = content.replace(
    '│   │   ├── security.py            # Password hashing, JWT tokens',
    '│   │   ├── security.py            # Password hashing, session management'
)
changes_made.append('✓ Updated file structure comments')

# 5. Update backend security implementation
old_security = '''from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.core.config import settings
from app.crud.crud_user import user_crud

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Validate JWT token and return current user

    Usage in endpoints:
        current_user: User = Depends(get_current_user)
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = user_crud.get(db, id=user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")'''

new_security = '''from fastapi import Cookie, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.config import settings
from app.crud.crud_user import user_crud
import secrets
from typing import Optional

# In-memory session store (for production, use Redis or database)
sessions = {}  # {session_id: {"user_id": int, "expires_at": datetime}}

def create_session(user_id: int) -> str:
    """Create a new session and return session ID"""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "user_id": user_id,
        "expires_at": datetime.utcnow() + timedelta(hours=8)
    }
    return session_id

def get_current_user(
    session_id: str = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Validate session cookie and return current user

    Usage in endpoints:
        current_user: User = Depends(get_current_user)
    """
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = sessions[session_id]

    # Check if session expired
    if datetime.utcnow() > session["expires_at"]:
        del sessions[session_id]
        raise HTTPException(status_code=401, detail="Session expired")

    # Get user
    user = user_crud.get(db, id=session["user_id"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Extend session expiration on activity
    sessions[session_id]["expires_at"] = datetime.utcnow() + timedelta(hours=8)

    return user'''

if 'from jose import JWTError, jwt' in content:
    content = content.replace(old_security, new_security)
    changes_made.append('✓ Updated backend security implementation')

# 6. Update login endpoint implementation
old_login_impl = '''@router.post("/login")
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT token"""
    user = user_crud.authenticate(db, username=credentials.username, password=credentials.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    # Create JWT token
    token = create_access_token({"sub": user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 3600,
        "user": UserResponse.from_orm(user)
    }'''

new_login_impl = '''@router.post("/login")
def login(
    response: Response,
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user and create session cookie"""
    user = user_crud.authenticate(db, username=credentials.username, password=credentials.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    # Create session
    session_id = create_session(user.id)

    # Set HTTP-only cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,  # Only over HTTPS in production
        samesite="strict",
        max_age=28800  # 8 hours
    )

    return {
        "user": UserResponse.from_orm(user)
    }'''

if 'Create JWT token' in content:
    content = content.replace(old_login_impl, new_login_impl)
    changes_made.append('✓ Updated login implementation')

# 7. Update frontend authentication
content = content.replace(
    'self.token = response["access_token"]',
    'self.user_info = response["user"]  # Session cookie set automatically'
)
changes_made.append('✓ Updated frontend authentication')

# 8. Update test examples
content = content.replace(
    'token = login_resp.json()["access_token"]',
    '# Session cookie is automatically stored in the session'
)
content = content.replace(
    'headers={"Authorization": f"Bearer {token}"}',
    '# Cookies are automatically sent with requests'
)
changes_made.append('✓ Updated test examples')

# 9. Update requirements section
content = re.sub(
    r'python-jose\[cryptography\].*?\n',
    '# JWT library removed - using simple session-based auth\n',
    content
)
changes_made.append('✓ Updated requirements (removed python-jose)')

# 10. Update feature checklist
content = content.replace(
    '- ✅ JWT token authentication',
    '- ✅ Session-based authentication with HTTP-only cookies'
)
changes_made.append('✓ Updated feature checklist')

# Write back
with open('C:/python/PEARL/python_only_tracker.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n🎉 Authentication update complete!\n")
print(f"Made {len(changes_made)} changes:")
for change in changes_made:
    print(f"  {change}")
print("\n✅ File saved: python_only_tracker.md")
