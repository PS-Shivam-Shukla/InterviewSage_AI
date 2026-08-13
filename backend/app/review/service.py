"""
Review Service — Manages Human Review Queue workflows and Recruiter Feedback processing.
"""

from __future__ import annotations

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.review_queue import RecruiterFeedback, ReviewQueue
from app.review.repository import ReviewRepository


class ReviewService:
    """Service handling low-confidence review queue flagging and recruiter feedback."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ReviewRepository(db)

    def flag_for_review(
        self,
        interview_id: str,
        confidence: float,
        reason: str = "Low confidence evaluation score",
        response_id: Optional[str] = None,
    ) -> ReviewQueue:
        """Flag response for human review."""
        return self.repo.create_review_item(
            interview_id=interview_id,
            confidence=confidence,
            reason=reason,
            response_id=response_id,
        )

    def get_queue(self, status: Optional[str] = None) -> List[ReviewQueue]:
        """Get items in review queue."""
        return self.repo.list_review_queue(status=status)

    def process_review(self, review_id: str, status: str, admin_id: Optional[str] = None) -> Optional[ReviewQueue]:
        """Update review item status (APPROVED | REJECTED | IN_REVIEW)."""
        return self.repo.update_review_status(review_id=review_id, status=status, admin_id=admin_id)

    def record_feedback(
        self,
        interview_id: str,
        recruiter_id: str,
        rating_action: str,
        question_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> RecruiterFeedback:
        """Record recruiter feedback."""
        return self.repo.add_recruiter_feedback(
            interview_id=interview_id,
            recruiter_id=recruiter_id,
            rating_action=rating_action,
            question_id=question_id,
            comment=comment,
        )
