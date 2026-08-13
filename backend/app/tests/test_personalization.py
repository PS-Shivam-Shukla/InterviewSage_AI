"""
Unit and Integration Tests for PersonalizationEngine & Retriever.
"""

import pytest
from sqlalchemy.orm import Session

from app.memory.personalization import PersonalizationEngine
from app.memory.retriever import MemoryRetriever
from app.models import User, Interview


def test_personalization_question_recommendation(
    db_session: Session, sample_user: User
):
    """Verify PersonalizationEngine generates personalized question recommendations based on weak areas."""
    engine = PersonalizationEngine(db_session)

    # Initial recommendation without prior history
    rec_init = engine.get_personalized_question_recommendation(sample_user.id)
    assert rec_init.target_skill is not None
    assert rec_init.recommended_difficulty in ["EASY", "MEDIUM", "HARD"]

    # Record weak skill evaluation
    engine.record_interview_skills_eval(
        sample_user.id, {"Concurrency & Async": 45.0, "FastAPI": 90.0}
    )

    rec_personalized = engine.get_personalized_question_recommendation(sample_user.id)
    assert rec_personalized.target_skill == "Concurrency & Async"
    assert rec_personalized.recommended_difficulty == "EASY"
    assert "Concurrency & Async" in rec_personalized.suggested_focus


def test_personalization_generate_learning_roadmap(
    db_session: Session, sample_user: User, sample_interview: Interview
):
    """Verify PersonalizationEngine generates a 4-week learning roadmap."""
    engine = PersonalizationEngine(db_session)

    engine.record_interview_skills_eval(
        sample_user.id,
        {
            "Docker": 50.0,
            "SQL Optimization": 58.0,
            "AsyncIO": 65.0,
            "System Design": 70.0,
        },
    )

    roadmap = engine.generate_learning_roadmap(
        sample_user.id, interview_id=sample_interview.id
    )

    assert len(roadmap) == 4
    week_numbers = [r.week_number for r in roadmap]
    assert week_numbers == [1, 2, 3, 4]
    assert roadmap[0].target_topic == "Docker"
    assert roadmap[0].priority == "HIGH"


def test_retriever_format_agent_prompt_context(
    db_session: Session, sample_user: User, sample_interview: Interview
):
    """Verify MemoryRetriever formats memory context string for agent prompts."""
    retriever = MemoryRetriever(db_session)
    engine = PersonalizationEngine(db_session)

    engine.record_interview_skills_eval(
        sample_user.id, {"Python": 88.0, "PostgreSQL": 55.0}
    )

    prompt_ctx = retriever.format_agent_prompt_context(sample_user.id)
    assert "Candidate Memory Profile" in prompt_ctx
    assert "Python" in prompt_ctx
    assert "PostgreSQL" in prompt_ctx
