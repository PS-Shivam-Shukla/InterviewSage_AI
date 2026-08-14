"""
Authentication service — user registration, login, token validation.
"""

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.repositories import UserRepository
from app.schemas.auth import UserResponse


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register_user(self, email: str, password: str, full_name: str) -> User | None:
        """
        Register a new user.

        Args:
            email: User email
            password: Plain text password
            full_name: User's full name

        Returns:
            Created User object or None if email already exists
        """
        # Check if user already exists
        existing = self.user_repo.get_by_email(email)
        if existing:
            return None

        # Hash password and create user
        hashed_pwd = hash_password(password)
        user = User(
            email=email,
            password_hash=hashed_pwd,
            full_name=full_name,
        )

        return self.user_repo.create(user)

    def authenticate_user(self, email: str, password: str) -> User | None:
        """
        Authenticate a user by email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            User object if credentials valid, None otherwise
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    def create_user_token(self, user: User) -> str:
        """
        Create a JWT access token for a user.

        Args:
            user: User object

        Returns:
            JWT token string
        """
        token_data = {
            "sub": user.id,  # subject claim (user ID)
            "email": user.email,
        }

        return create_access_token(token_data)

    def verify_token(self, token: str) -> str | None:
        """
        Verify a JWT token and extract user ID.

        Args:
            token: JWT token string

        Returns:
            User ID if token valid, None otherwise
        """
        payload = decode_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        return user_id

    def get_current_user(self, token: str) -> User | None:
        """
        Get the current user from a token.

        Args:
            token: JWT token string

        Returns:
            User object if token valid, None otherwise
        """
        user_id = self.verify_token(token)
        if not user_id:
            return None

        return self.user_repo.get_by_id(user_id)

    def user_to_response(self, user: User) -> UserResponse:
        """Convert User model to response DTO."""
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at.isoformat(),
        )
