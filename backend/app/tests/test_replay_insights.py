"""
Unit and Integration Tests for InterviewReplayEngine & RecruiterInsightsEngine.
"""

from sqlalchemy.orm import Session

from app.career.insights import RecruiterInsightsEngine
from app.career.replay import InterviewReplayEngine
from app.models import Interview


def test_interview_replay_engine(db_session: Session, sample_interview: Interview):
    """Verify InterviewReplayEngine annotates interview timeline."""
    engine = InterviewReplayEngine(db_session)
    res = engine.get_interview_replay(sample_interview.id)

    assert res.interview_id == sample_interview.id
    assert res.total_annotations >= 3
    assert any("00:35" in a.timestamp_mark for a in res.annotations)


def test_recruiter_insights_engine(db_session: Session, sample_interview: Interview):
    """Verify RecruiterInsightsEngine provides decision metrics and rejection impact factors."""
    engine = RecruiterInsightsEngine(db_session)
    res = engine.get_recruiter_insights(sample_interview.id)

    assert res.interview_id == sample_interview.id
    assert res.recommendation == "PROCEED_TO_OFFER"
    assert res.ai_confidence > 80.0
    assert len(res.primary_rejection_factors) >= 1
