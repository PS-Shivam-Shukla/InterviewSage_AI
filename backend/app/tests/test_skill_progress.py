"""
Unit and Integration Tests for Skill Progress & Longitudinal Trend Tracking.
"""

import pytest
from sqlalchemy.orm import Session

from app.memory.repository import MemoryRepository
from app.models import User


def test_skill_progress_upsert_and_trends(db_session: Session, sample_user: User):
    """Verify SkillProgress tracking, average score computation, and trend states."""
    repo = MemoryRepository(db_session)

    # Initial score
    s1 = repo.upsert_skill_progress(sample_user.id, "Python", 70.0)
    assert s1.current_score == 70.0
    assert s1.best_score == 70.0
    assert s1.average_score == 70.0
    assert s1.trend == "STABLE"
    assert s1.total_evaluations == 1

    # Improving score (> +2.0)
    s2 = repo.upsert_skill_progress(sample_user.id, "Python", 85.0)
    assert s2.current_score == 85.0
    assert s2.best_score == 85.0
    assert s2.average_score == 77.5  # (70 + 85) / 2
    assert s2.trend == "IMPROVING"
    assert s2.total_evaluations == 2

    # Regressing score (< -2.0)
    s3 = repo.upsert_skill_progress(sample_user.id, "Python", 75.0)
    assert s3.current_score == 75.0
    assert s3.best_score == 85.0
    assert s3.trend == "REGRESSING"
    assert s3.total_evaluations == 3


def test_list_skill_progress(db_session: Session, sample_user: User):
    """Verify listing multiple skill progression items for a candidate."""
    repo = MemoryRepository(db_session)
    repo.upsert_skill_progress(sample_user.id, "FastAPI", 90.0)
    repo.upsert_skill_progress(sample_user.id, "PostgreSQL", 80.0)
    repo.upsert_skill_progress(sample_user.id, "Docker", 60.0)

    skills = repo.list_skill_progress(sample_user.id)
    assert len(skills) == 3
    skill_names = [s.skill_name for s in skills]
    assert "Docker" in skill_names
    assert "FastAPI" in skill_names
    assert "PostgreSQL" in skill_names
