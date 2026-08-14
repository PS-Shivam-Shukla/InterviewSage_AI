"""
Resume repository.
"""

from sqlalchemy.orm import Session

from app.models import Resume
from app.repositories.base import Repository


class ResumeRepository(Repository[Resume]):
    """Repository for Resume model operations."""

    def __init__(self, db: Session):
        super().__init__(db, Resume)

    def list_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> list[Resume]:
        """Get all resumes for a user."""
        return (
            self.db.query(Resume).filter(Resume.user_id == user_id).offset(skip).limit(limit).all()
        )
