"""
User repository.
"""

from sqlalchemy.orm import Session

from app.models import User
from app.repositories.base import Repository


class UserRepository(Repository[User]):
    """Repository for User model operations."""

    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        return self.db.query(User).filter(User.email == email).first()
