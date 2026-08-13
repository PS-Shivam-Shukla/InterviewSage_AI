"""
JobDescription repository.
"""

from typing import List
from sqlalchemy.orm import Session

from app.models import JobDescription
from app.repositories.base import Repository


class JobDescriptionRepository(Repository[JobDescription]):
    """Repository for JobDescription model operations."""

    def __init__(self, db: Session):
        super().__init__(db, JobDescription)

    def list_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[JobDescription]:
        """Get all job descriptions for a user."""
        return (
            self.db.query(JobDescription)
            .filter(JobDescription.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
