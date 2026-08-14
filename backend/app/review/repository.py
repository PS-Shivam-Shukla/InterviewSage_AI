"""
Review Repository — Manages database queries for Human Review Queue and Recruiter Feedback.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.review_queue import RecruiterFeedback, ReviewQueue


class ReviewRepository:
    """SQLAlchemy Repository for Review Queue & Recruiter Feedback."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_review_item(
        self,
        interview_id: str,
        confidence: float = 0.5,
        reason: str = "Low confidence evaluation score",
        response_id: str | None = None,
    ) -> ReviewQueue:
        """Create a new ReviewQueue item."""
        item = ReviewQueue(
            id=str(uuid.uuid4()),
            interview_id=interview_id,
            response_id=response_id,
            confidence=confidence,
            reason=reason,
            status="PENDING",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_review_queue(self, status: str | None = None, limit: int = 100) -> list[ReviewQueue]:
        """List review queue items, optionally filtered by status."""
        query = self.db.query(ReviewQueue)
        if status:
            query = query.filter(ReviewQueue.status == status)
        return query.order_by(ReviewQueue.created_at.desc()).limit(limit).all()

    def update_review_status(self, review_id: str, status: str, admin_id: str | None = None) -> ReviewQueue | None:
        """Update review item status."""
        item = self.db.query(ReviewQueue).filter(ReviewQueue.id == review_id).first()
        if item:
            item.status = status
            if admin_id:
                item.assigned_admin = admin_id
            item.updated_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(item)
        return item

    def add_recruiter_feedback(
        self,
        interview_id: str,
        recruiter_id: str,
        rating_action: str,
        question_id: str | None = None,
        comment: str | None = None,
    ) -> RecruiterFeedback:
        """Add recruiter qualitative feedback."""
        fb = RecruiterFeedback(
            id=str(uuid.uuid4()),
            interview_id=interview_id,
            question_id=question_id,
            recruiter_id=recruiter_id,
            rating_action=rating_action,
            comment=comment,
            created_at=datetime.now(UTC),
        )
        self.db.add(fb)
        self.db.commit()
        self.db.refresh(fb)
        return fb
