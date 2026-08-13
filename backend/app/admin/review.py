"""
Admin Review Subsystem Wrapper.
"""

from __future__ import annotations

from typing import Any, List, Optional
from sqlalchemy.orm import Session

from app.review.service import ReviewService


class AdminReviewManager:
    """Wrapper providing Admin Review Queue operations."""

    def __init__(self, db: Session) -> None:
        self.service = ReviewService(db)

    def get_queue(self, status: Optional[str] = None) -> List[Any]:
        return self.service.get_queue(status=status)

    def update_status(self, review_id: str, status: str, admin_id: Optional[str] = None) -> Any:
        return self.service.process_review(review_id=review_id, status=status, admin_id=admin_id)

    def submit_feedback(self, interview_id: str, recruiter_id: str, rating_action: str, question_id: Optional[str] = None, comment: Optional[str] = None) -> Any:
        return self.service.record_feedback(
            interview_id=interview_id,
            recruiter_id=recruiter_id,
            rating_action=rating_action,
            question_id=question_id,
            comment=comment,
        )
