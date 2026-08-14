"""
Human Review Queue & Recruiter Feedback Database Models.
Persists low-confidence AI evaluation reviews and recruiter qualitative feedback.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, String, Text

from app.models.base import Base


class ReviewQueue(Base):
    """Stores AI outputs flagged for human reviewer inspection due to low confidence or edge case detection."""

    __tablename__ = "review_queue"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    response_id = Column(String(100), nullable=True, index=True)
    interview_id = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, default=0.5)
    reason = Column(String(255), nullable=False, default="Low confidence evaluation score")
    assigned_admin = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="PENDING", index=True)  # PENDING | IN_REVIEW | APPROVED | REJECTED
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class RecruiterFeedback(Base):
    """Recruiter feedback approving, rejecting, or commenting on AI generated evaluations or questions."""

    __tablename__ = "recruiter_feedbacks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(100), nullable=False, index=True)
    question_id = Column(String(100), nullable=True, index=True)
    recruiter_id = Column(String(100), nullable=False, index=True)
    rating_action = Column(String(50), nullable=False)  # APPROVE | REJECT | NEEDS_REVIEW
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
