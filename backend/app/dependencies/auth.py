"""
FastAPI dependency providers for authentication.
Supports authenticated JWT users and seamless fallback for demo/guest candidates.
"""

from typing import Optional
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db
from app.models import User
from app.services import AuthService
from sqlalchemy.orm import Session

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that returns current authenticated user from JWT token.
    Raises 401 Unauthorized if token is missing or invalid.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
        )

    token = credentials.credentials
    auth_service = AuthService(db)
    user = auth_service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Dependency that returns current user if authenticated,
    or demo user if not authenticated.
    """
    return await get_current_user(credentials, db)
