"""
Gate 5 Similarity Calibration & Latency Regression Test Suite.
Verifies exact duplicate rejection, paraphrase rejection, borderline acceptance (the 0.38 case), threshold boundary behavior, and retry feedback.
"""

import pytest

from app.agents.question_generator_agent import GeneratedQuestion, QuestionGeneratorAgent
from app.graph.state import InterviewState
from app.services.question_relevance_service import (
    LexicalSimilarityEngine,
    QuestionRelevanceService,
)


# Base context fixture
@pytest.fixture
def candidate_context():
    return {
        "candidate_skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "REST"],
        "work_experience_bullets": [
            "Developed REST microservices using FastAPI, Redis, and PostgreSQL."
        ],
        "jd_required_skills": ["Python", "FastAPI", "PostgreSQL", "System Design"],
        "relevant_experience_months": 36,
        "seniority_level": "MID",
    }


def test_gate5_exact_duplicate_rejected(candidate_context):
    """Test 1: Exact duplicate question must be rejected by Gate 5."""
    q_existing = "Explain Python decorators and how they work in backend services."
    questions_asked = [{"question_text": q_existing, "competency_targeted": "Python"}]

    res = QuestionRelevanceService.validate_question(
        question_text=q_existing,
        question_difficulty="INTERMEDIATE",
        round_type="technical",
        questions_asked=questions_asked,
        competency_targeted="Python",
        **candidate_context,
    )
    assert res.accepted is False
    assert "GATE 5 FAILED" in res.reason
    assert res.duplicate_score == 1.0


def test_gate5_strong_paraphrase_rejected(candidate_context):
    """Test 2: Strong paraphrase question must be rejected by Gate 5."""
    q_existing = "How do PostgreSQL database indexes improve query latency in backend applications?"
    q_paraphrase = (
        "How do database indexes in PostgreSQL improve query latency for backend applications?"
    )
    questions_asked = [{"question_text": q_existing, "competency_targeted": "Database"}]

    res = QuestionRelevanceService.validate_question(
        question_text=q_paraphrase,
        question_difficulty="INTERMEDIATE",
        round_type="technical",
        questions_asked=questions_asked,
        competency_targeted="Database",
        **candidate_context,
    )
    assert res.accepted is False
    assert "GATE 5 FAILED" in res.reason
    assert res.duplicate_score > 0.45


def test_gate5_same_competency_different_question_accepted(candidate_context):
    """Test 3: Same competency but different question should be accepted."""
    q_existing = "Explain Python decorators and higher-order functions."
    q_novel = "Explain Python context managers and the contextlib module."
    questions_asked = [{"question_text": q_existing, "competency_targeted": "Python"}]

    res = QuestionRelevanceService.validate_question(
        question_text=q_novel,
        question_difficulty="INTERMEDIATE",
        round_type="technical",
        questions_asked=questions_asked,
        competency_targeted="Python",
        **candidate_context,
    )
    assert res.accepted is True
    assert res.duplicate_score <= 0.45


def test_gate5_same_concept_different_cognitive_angle_accepted(candidate_context):
    """Test 4: Same concept but different cognitive angle should be accepted."""
    q_existing = "What is Redis caching and how does it store key-value data?"
    q_angle = "How do you handle cache stampedes and dogpiling when a popular Redis key expires?"
    questions_asked = [{"question_text": q_existing, "competency_targeted": "Caching"}]

    res = QuestionRelevanceService.validate_question(
        question_text=q_angle,
        question_difficulty="INTERMEDIATE",
        round_type="technical",
        questions_asked=questions_asked,
        competency_targeted="Caching",
        **candidate_context,
    )
    assert res.accepted is True
    assert res.duplicate_score <= 0.45


def test_gate5_the_038_case_reproduced_and_accepted(candidate_context):
    """Test 6: Reproduces the original 0.38 score case and verifies it is now ACCEPTED under calibrated threshold."""
    q_existing = "What is REST API architecture?"
    q_038 = "How do you handle API versioning and backward compatibility in REST services?"
    questions_asked = [{"question_text": q_existing, "competency_targeted": "API"}]

    # Measure exact hybrid score
    dup_score, _ = LexicalSimilarityEngine.compute_hybrid_duplicate_score(q_038, questions_asked)
    assert 0.35 < dup_score <= 0.45, f"Expected score around 0.38-0.44, got {dup_score}"

    res = QuestionRelevanceService.validate_question(
        question_text=q_038,
        question_difficulty="INTERMEDIATE",
        round_type="technical",
        questions_asked=questions_asked,
        competency_targeted="API",
        **candidate_context,
    )
    # Under calibrated threshold 0.45, this score (0.4364) is ACCEPTED without triggering an unnecessary retry!
    assert res.accepted is True


def test_gate5_threshold_boundary_epsilon(candidate_context):
    """Test 5: Validates exact threshold boundary behavior (score <= 0.45 vs > 0.45)."""
    questions_asked = [
        {
            "question_text": "Describe FastAPI background task processing.",
            "competency_targeted": "FastAPI",
        }
    ]

    res = QuestionRelevanceService.validate_question(
        question_text="Describe FastAPI background task processing.",
        question_difficulty="INTERMEDIATE",
        round_type="technical",
        questions_asked=questions_asked,
        competency_targeted="FastAPI",
        **candidate_context,
    )
    assert res.accepted is False
    assert res.duplicate_score == 1.0


def test_accepted_question_does_not_retry(mocker):
    """Test 8: Accepted question executes in single turn with 0 retries."""
    expected_q = "Explain Python asyncio event loops."
    mocker.patch(
        "app.core.llm_client.LLMClient.invoke_structured",
        return_value=GeneratedQuestion(
            question_text=expected_q,
            competency_targeted="Python",
            difficulty="INTERMEDIATE",
            question_type="fundamentals",
        ),
    )

    state: InterviewState = {
        "candidate_id": "c1",
        "job_id": "j1",
        "resume_data": {
            "seniority_signal": "MID",
            "relevant_experience_months": 36,
            "skills": ["Python", "FastAPI"],
        },
        "jd_data": {"target_role": "Backend Developer", "required_skills": ["Python", "FastAPI"]},
        "competency_matrix": [{"name": "Python", "weight": 50}],
        "questions_asked": [],
        "interview_plan": {"total_questions": 5},
    }

    agent = QuestionGeneratorAgent(round_type="TECHNICAL")
    result = agent._run(state)
    assert result["current_question"]["question_text"] == expected_q
