"""
Unit and Integration Tests for SkillGapAnalyzer & CareerRoadmapGenerator.
"""

import pytest
from sqlalchemy.orm import Session

from app.career.roadmap import CareerRoadmapGenerator
from app.career.skill_gap import SkillGapAnalyzer
from app.models import User, SkillProgress


def test_skill_gap_analyzer(db_session: Session, sample_user: User):
    """Verify SkillGapAnalyzer identifies missing concepts per topic."""
    sp = SkillProgress(candidate_id=sample_user.id, skill_name="redis", current_score=55.0)
    db_session.add(sp)
    db_session.commit()

    analyzer = SkillGapAnalyzer(db_session)
    res = analyzer.analyze_skill_gaps(sample_user.id)

    assert res.candidate_id == sample_user.id
    assert res.total_gaps >= 1
    assert any("redis" in g.topic.lower() for g in res.gaps)


def test_career_roadmap_generator(db_session: Session, sample_user: User):
    """Verify CareerRoadmapGenerator creates daily, weekly, and monthly action plans."""
    gen = CareerRoadmapGenerator(db_session)
    res = gen.generate_career_roadmap(sample_user.id)

    assert res.candidate_id == sample_user.id
    assert len(res.daily_plan) >= 3
    assert len(res.weekly_plan) >= 2
    assert len(res.monthly_plan) >= 1
