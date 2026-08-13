"""
Step 4.1 — Session Completion & Auto-Termination Engine Tests
Verifies that:
1. Final configured question completion sets Interview.status = COMPLETED.
2. No extra fallback question is created after the final question is answered.
3. InterviewReport is generated and persisted to PostgreSQL.
4. Completion and report generation are idempotent (no duplicates).
5. Non-final questions continue interview with next_question.
6. Voice turn and REST text turn completion contracts operate identically.
"""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

from app.agents.evaluation_agent import EvaluationAgent
from app.models import (
    User, Resume, JobDescription, Interview, InterviewQuestion,
    InterviewAnswer, Evaluation, InterviewReport
)
from app.services.interview_service import InterviewService
from app.services.report_service import ReportService
from app.speech.streaming import AudioStreamingService





def _setup_mock_interview(db: Session, question_count: int = 5) -> Interview:
    """Helper to create a valid user, resume, JD, interview, and N configured questions."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"candidate-{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hashed_secret",
        full_name="Candidate Tester",
    )
    db.add(user)

    resume = Resume(
        id=str(uuid.uuid4()),
        user_id=user.id,
        file_path="uploads/samples/sample_resume.pdf",
        raw_text="Candidate resume text",
        parsed_skills='["Python", "FastAPI"]',
    )
    db.add(resume)

    jd = JobDescription(
        id=str(uuid.uuid4()),
        user_id=user.id,
        target_role="Senior Python Engineer",
        raw_text="Job requirements",
        required_skills='["Python", "FastAPI", "PostgreSQL"]',
    )
    db.add(jd)

    interview = Interview(
        id=str(uuid.uuid4()),
        user_id=user.id,
        resume_id=resume.id,
        jd_id=jd.id,
        status="IN_PROGRESS",
        current_round="TECHNICAL",
        started_at=datetime.now(timezone.utc),
    )
    db.add(interview)
    db.flush()

    for idx in range(1, question_count + 1):
        q = InterviewQuestion(
            id=str(uuid.uuid4()),
            interview_id=interview.id,
            round_type="TECHNICAL" if idx <= 3 else "HR",
            competency_targeted="Backend Architecture" if idx <= 3 else "Leadership & Culture",
            difficulty="MEDIUM",
            question_text=f"Question #{idx}: Explain system component #{idx}.",
            sequence_number=idx,
            created_at=datetime.now(timezone.utc),
        )
        db.add(q)

    db.commit()
    db.refresh(interview)
    return interview


def test_non_final_question_continues_interview(db_session: Session):
    """Answering a non-final question advances the interview without completing or creating a report."""
    interview = _setup_mock_interview(db_session, question_count=5)
    service = InterviewService(db_session)

    # Answer Question 1 of 5
    res = service.submit_answer(
        interview_id=interview.id,
        answer="Answer to question 1",
        question_id=f"q-1-{interview.id}",
        question_text="Question #1: Explain system component #1.",
    )

    assert res["status"] == "IN_PROGRESS"
    assert res["next_question"] is not None
    assert res["next_question"]["sequence_number"] == 2
    assert res["report_id"] is None

    db_session.expire_all()
    reloaded = service.get_interview(interview.id)
    assert reloaded.status == "IN_PROGRESS"

    report = db_session.query(InterviewReport).filter(InterviewReport.interview_id == interview.id).first()
    assert report is None


def test_final_question_completes_interview_and_creates_report(db_session: Session):
    """Answering the final question marks interview COMPLETED and generates an InterviewReport."""
    interview = _setup_mock_interview(db_session, question_count=5)
    service = InterviewService(db_session)

    # Answer Questions 1 through 4
    for idx in range(1, 5):
        service.submit_answer(
            interview_id=interview.id,
            answer=f"Answer to question {idx}",
            question_id=f"q-{idx}-{interview.id}",
            question_text=f"Question #{idx}: Explain system component #{idx}.",
        )

    # Answer Question 5 (Final)
    final_res = service.submit_answer(
        interview_id=interview.id,
        answer="Answer to final question 5",
        question_id=f"q-5-{interview.id}",
        question_text="Question #5: Explain system component #5.",
    )

    assert final_res["status"] == "COMPLETED"
    assert final_res["next_question"] is None
    assert final_res["report_id"] == interview.id

    db_session.expire_all()
    reloaded = service.get_interview(interview.id)
    assert reloaded.status == "COMPLETED"
    assert reloaded.completed_at is not None
    assert reloaded.overall_score is not None

    report = db_session.query(InterviewReport).filter(InterviewReport.interview_id == interview.id).first()
    assert report is not None
    assert report.interview_id == interview.id

    # Verify 5 questions were created
    questions = db_session.query(InterviewQuestion).filter(InterviewQuestion.interview_id == interview.id).all()
    assert len(questions) == 5


def test_duplicate_completion_is_idempotent(db_session: Session):
    """Submitting an answer to an already COMPLETED interview returns COMPLETED status idempotently."""
    interview = _setup_mock_interview(db_session, question_count=5)
    service = InterviewService(db_session)

    # Answer Questions 1 to 5 to complete
    for idx in range(1, 6):
        service.submit_answer(
            interview_id=interview.id,
            answer=f"Answer {idx}",
            question_id=f"q-{idx}-{interview.id}",
            question_text=f"Question #{idx}",
        )

    res1 = service.get_interview(interview.id)
    assert res1.status == "COMPLETED"

    # Duplicate submission call after completion
    res2 = service.submit_answer(
        interview_id=interview.id,
        answer="Duplicate answer call",
        question_id=f"q-5-{interview.id}",
        question_text="Question #5",
    )

    assert res2["status"] == "COMPLETED"
    assert res2["next_question"] is None
    assert res2["report_id"] == interview.id

    # Verify exactly 1 report exists
    reports = db_session.query(InterviewReport).filter(InterviewReport.interview_id == interview.id).all()
    assert len(reports) == 1


def test_voice_turn_final_question_completion(db_session: Session):
    """Voice turn execution on final question completes interview via AudioStreamingService."""
    interview = _setup_mock_interview(db_session, question_count=5)
    service = InterviewService(db_session)
    for idx in range(1, 5):
        service.submit_answer(
            interview_id=interview.id,
            answer=f"Answer {idx}",
            question_id=f"q-{idx}-{interview.id}",
            question_text=f"Question #{idx}",
        )

    streaming_service = AudioStreamingService(db=db_session)

    voice_res = streaming_service.process_voice_turn_orchestrated(
        session_id=interview.id,
        db=db_session,
        audio_bytes=b"\x00\x01\x02\x03" * 100,
    )

    assert voice_res["error"] is False
    assert not voice_res["next_question"]

    db_session.expire_all()
    reloaded_interview = db_session.query(Interview).filter(Interview.id == interview.id).first()
    assert reloaded_interview.status == "COMPLETED"

    report = db_session.query(InterviewReport).filter(InterviewReport.interview_id == interview.id).first()
    assert report is not None
