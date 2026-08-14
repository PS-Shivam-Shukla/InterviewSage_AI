"""
Unit and Integration Tests for HiringPredictionEngine.
"""

from sqlalchemy.orm import Session

from app.career.prediction import HiringPredictionEngine
from app.models import SkillProgress, User


def test_hiring_prediction_engine(db_session: Session, sample_user: User):
    """Verify HiringPredictionEngine calculates probability, outcome, and reasoning."""
    engine = HiringPredictionEngine(db_session)

    # Seed skill progress
    sp = SkillProgress(
        candidate_id=sample_user.id, skill_name="System Design", current_score=88.0, best_score=92.0
    )
    db_session.add(sp)
    db_session.commit()

    pred = engine.predict_hiring_outcome(sample_user.id)
    assert pred.candidate_id == sample_user.id
    assert 0.0 <= pred.hire_probability <= 100.0
    assert 0.0 <= pred.confidence_score <= 100.0
    assert pred.outcome in ["Hire", "Borderline", "Reject"]
