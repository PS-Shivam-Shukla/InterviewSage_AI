"""
Unit and Integration Tests for AdaptiveDifficultyEngine.
"""

from sqlalchemy.orm import Session

from app.career.adaptive import AdaptiveDifficultyEngine


def test_adaptive_difficulty_escalation(db_session: Session):
    """Verify high performance (>80%) increases difficulty."""
    engine = AdaptiveDifficultyEngine(db_session)
    session = engine.start_session("intv-adapt-101", "cand-adapt-101", initial_difficulty=5.0)
    assert session.current_difficulty == 5.0

    res1 = engine.process_answer_and_adjust(session.id, performance_score=85.0, response_latency_seconds=10.0)
    assert res1["new_difficulty"] > 5.0

    res2 = engine.process_answer_and_adjust(session.id, performance_score=92.0, response_latency_seconds=12.0)
    assert res2["new_difficulty"] > res1["new_difficulty"]
    assert "Escalating" in res2["adjustment_reason"]


def test_adaptive_difficulty_deescalation(db_session: Session):
    """Verify low performance (<60%) decreases difficulty."""
    engine = AdaptiveDifficultyEngine(db_session)
    session = engine.start_session("intv-adapt-202", "cand-adapt-202", initial_difficulty=6.0)

    res = engine.process_answer_and_adjust(session.id, performance_score=45.0, response_latency_seconds=50.0)
    assert res["new_difficulty"] < 6.0
    assert "Decreasing" in res["adjustment_reason"]
