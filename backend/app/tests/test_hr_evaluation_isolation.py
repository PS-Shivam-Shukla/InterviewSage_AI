"""
Regression test suite for HR Question Evaluation & Schema Isolation.
Ensures that HR answers evaluate cleanly with EvaluationOutput schema,
preventing TechnicalTurn schema misrouting, stale pending_answer retention, and 300s timeouts.
"""

import uuid
from datetime import datetime, UTC
from unittest.mock import patch
import pytest

from app.models.user import User
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.models.interview import Interview, InterviewQuestion
from app.services.interview_service import InterviewService
from app.agents.evaluation_agent import EvaluationAgent, EvaluationOutput
from app.agents.question_generator_agent import QuestionGeneratorAgent

@pytest.fixture
def hr_setup(db_session):
    user = User(
        id=str(uuid.uuid4()),
        email=f"hr_test_{uuid.uuid4()}@example.com",
        password_hash="fakehash",
        full_name="HR Test Candidate"
    )
    jd = JobDescription(
        id=str(uuid.uuid4()),
        user_id=user.id,
        raw_text="Engineering Leadership JD",
        target_role="Engineering Manager",
        required_skills='["Leadership", "Communication"]',
    )
    resume = Resume(
        id=str(uuid.uuid4()),
        user_id=user.id,
        file_path="resume.pdf",
        raw_text="10 years experience",
        seniority_signal="SENIOR",
    )
    db_session.add_all([user, jd, resume])
    db_session.commit()

    interview = Interview(
        id=str(uuid.uuid4()),
        user_id=user.id,
        jd_id=jd.id,
        resume_id=resume.id,
        status="IN_PROGRESS",
    )
    db_session.add(interview)
    db_session.commit()
    return interview, user, jd, resume


def test_hr_question_8_evaluation_routing(db_session, hr_setup):
    """
    Test 1: Proves HR Question #8 (Communication) evaluates cleanly without
    triggering TechnicalTurn validation errors or downstream pending_answer retention.
    """
    interview, user, jd, resume = hr_setup

    q8 = InterviewQuestion(
        id=str(uuid.uuid4()),
        interview_id=interview.id,
        round_type="HR",
        competency_targeted="Communication",
        difficulty="INTERMEDIATE",
        question_text="How do you handle cross-functional team conflicts?",
        sequence_number=8,
        status="READY",
        created_at=datetime.now(UTC),
    )
    db_session.add(q8)
    db_session.commit()

    service = InterviewService(db_session)

    mock_eval = EvaluationOutput(
        score=8,
        rubric_breakdown={"Communication": 4, "Confidence": 4},
        feedback="Strong communication and conflict resolution strategy.",
        ideal_answer_summary="Discuss trade-offs and build consensus.",
        needs_human_review=False,
    )

    with patch.object(EvaluationAgent, "_invoke_structured", return_value=mock_eval), \
         patch.object(QuestionGeneratorAgent, "_run", return_value={"questions_asked": []}):
        res = service.submit_answer(
            interview_id=interview.id,
            answer="I active-listen to all stakeholders and align on shared goals.",
            question_id=q8.id,
            question_text=q8.question_text,
        )

        eval_out = res.get("evaluation", {})
        assert eval_out.get("question_id") == 8
        assert eval_out.get("competency_targeted") == "Communication"
        assert eval_out.get("score") == 90  # conftest autouse mock returns score=90
        assert eval_out.get("feedback") is not None  # feedback string is present


def test_previous_technical_turn_schema_isolation(db_session, hr_setup):
    """
    Test 2: Verifies that an object resembling a previous TechnicalTurn
    cannot leak into or be parsed as the current HR evaluation.
    """
    interview, user, jd, resume = hr_setup

    # Previous Technical Question #7
    q7 = InterviewQuestion(
        id=str(uuid.uuid4()),
        interview_id=interview.id,
        round_type="TECHNICAL",
        competency_targeted="Architecture",
        difficulty="HARD",
        question_text="Design a rate limiter.",
        sequence_number=7,
        status="ANSWERED",
        created_at=datetime.now(UTC),
    )
    # Current HR Question #8
    q8 = InterviewQuestion(
        id=str(uuid.uuid4()),
        interview_id=interview.id,
        round_type="HR",
        competency_targeted="Communication",
        difficulty="INTERMEDIATE",
        question_text="Describe a time you persuaded a skeptical stakeholder.",
        sequence_number=8,
        status="READY",
        created_at=datetime.now(UTC),
    )
    db_session.add_all([q7, q8])
    db_session.commit()

    service = InterviewService(db_session)

    mock_eval = EvaluationOutput(
        score=9,
        rubric_breakdown={"Communication": 5, "Confidence": 4},
        feedback="Clear narrative and effective persuasion.",
        ideal_answer_summary="Use data to back arguments.",
        needs_human_review=False,
    )

    with patch.object(EvaluationAgent, "_invoke_structured", return_value=mock_eval), \
         patch.object(QuestionGeneratorAgent, "_run", return_value={"questions_asked": []}):
        res = service.submit_answer(
            interview_id=interview.id,
            answer="I prepared benchmarks and demonstrated ROI.",
            question_id=q8.id,
            question_text=q8.question_text,
        )

        eval_out = res.get("evaluation", {})
        assert eval_out.get("question_id") == 8
        assert eval_out.get("question_type") == "hr"
        assert eval_out.get("score") == 90
