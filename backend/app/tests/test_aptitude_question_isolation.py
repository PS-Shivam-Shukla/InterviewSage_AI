"""
Mandatory Regression Test Suite: Aptitude Evaluation Context Isolation
Verifies that:
1. Technical evaluations do not spill over into Aptitude evaluations.
2. An Aptitude answer evaluates against its EXACT question and never previous technical questions.
3. Cross-round sequence (TECHNICAL -> APTITUDE -> HR -> TECHNICAL) maintains 100% question isolation.
4. Mismatched evaluation context triggers an explicit safety guard rejection.
"""

import uuid
from datetime import datetime, UTC
import pytest
from fastapi import HTTPException

from app.models import User, Resume, JobDescription, Interview, InterviewQuestion, InterviewAnswer, Evaluation
from app.services.interview_service import InterviewService
from app.agents.evaluation_agent import EvaluationAgent


def test_aptitude_evaluation_context_isolation(db_session, mocker):
    """
    REPRODUCE & VERIFY FIX:
    Q1: Technical ("Explain Repository and Adapter patterns")
    Q2: Aptitude ("At what annual simple interest rate will a sum of money double itself in 10 years?")
    Verify Q2 evaluation NEVER contains Repository, Adapter, or MVC context.
    """
    user = User(id=str(uuid.uuid4()), email=f"apt_iso_{uuid.uuid4()}@example.com", password_hash="pw", full_name="Apt User")
    db_session.add(user)

    resume = Resume(
        id=str(uuid.uuid4()),
        user_id=user.id,
        file_path="test_resume.pdf",
        raw_text="Python Backend Engineer with FastAPI and PostgreSQL experience.",
        status="PROCESSED",
    )
    db_session.add(resume)

    jd = JobDescription(
        id=str(uuid.uuid4()),
        user_id=user.id,
        raw_text="Seeking Senior Backend Engineer proficient in Python and FastAPI.",
        target_role="Backend Engineer",
        required_skills='["Python", "FastAPI"]',
    )
    db_session.add(jd)

    interview = Interview(
        id=str(uuid.uuid4()),
        user_id=user.id,
        resume_id=resume.id,
        jd_id=jd.id,
        status="IN_PROGRESS",
    )
    db_session.add(interview)

    # Q1: Technical
    q1 = InterviewQuestion(
        id=str(uuid.uuid4()),
        interview_id=interview.id,
        sequence_number=1,
        round_type="TECHNICAL",
        competency_targeted="Software Architecture",
        difficulty="MEDIUM",
        question_text="Explain the Repository pattern and the Adapter pattern, including their core mechanisms in MVC architecture.",
        status="CONSUMED",
    )
    db_session.add(q1)

    ans1 = InterviewAnswer(
        id=str(uuid.uuid4()),
        question_id=q1.id,
        answer_text="The Repository pattern abstracts data access layer while the Adapter pattern converts interfaces.",
        created_at=datetime.now(UTC),
    )
    db_session.add(ans1)

    eval1 = Evaluation(
        id=str(uuid.uuid4()),
        answer_id=ans1.id,
        score=80,
        rubric_breakdown='{"Correctness": 4, "Communication": 4, "Confidence": 4}',
        feedback="Good explanation of Repository and Adapter patterns in MVC architecture.",
        ideal_answer_summary="The Repository pattern handles persistence abstraction and Adapter pattern translates interfaces.",
    )
    db_session.add(eval1)

    # Q2: Aptitude
    q2 = InterviewQuestion(
        id=str(uuid.uuid4()),
        interview_id=interview.id,
        sequence_number=2,
        round_type="APTITUDE",
        competency_targeted="Quantitative Reasoning",
        difficulty="EASY",
        question_text="At what annual simple interest rate will a sum of money double itself in 10 years?",
        status="PENDING",
    )
    db_session.add(q2)
    db_session.commit()

    service = InterviewService(db_session)
    res = service.submit_answer(
        interview_id=interview.id,
        question_id=q2.id,
        question_text=q2.question_text,
        answer="10%",
    )

    eval_data = res.get("evaluation", {})
    assert eval_data is not None
    assert eval_data.get("round_type") == "APTITUDE"
    assert eval_data.get("question_id") == 2

    fb = (eval_data.get("feedback") or "") + " " + (eval_data.get("ideal_answer_summary") or "")
    
    # CRITICAL SANITY ASSERTS: Must contain aptitude concepts and NOT technical patterns
    assert "Repository" not in fb
    assert "Adapter" not in fb
    assert "MVC" not in fb
    assert "10%" in fb or "10" in fb or "Correct" in fb or "simple interest" in fb.lower()


def test_cross_round_sequence_isolation(db_session):
    """
    Tests sequence of TECHNICAL -> APTITUDE -> HR -> TECHNICAL.
    Verifies that no round reuses context or rubrics from another round.
    """
    user = User(id=str(uuid.uuid4()), email=f"cross_round_{uuid.uuid4()}@example.com", password_hash="pw", full_name="Cross Round User")
    db_session.add(user)

    resume = Resume(
        id=str(uuid.uuid4()),
        user_id=user.id,
        file_path="test.pdf",
        raw_text="Fullstack Engineer",
        status="PROCESSED",
    )
    db_session.add(resume)

    jd = JobDescription(
        id=str(uuid.uuid4()),
        user_id=user.id,
        raw_text="Seeking Senior Software Engineer",
        target_role="Software Engineer",
        required_skills='["Python"]',
    )
    db_session.add(jd)

    interview = Interview(
        id=str(uuid.uuid4()),
        user_id=user.id,
        resume_id=resume.id,
        jd_id=jd.id,
        status="IN_PROGRESS",
    )
    db_session.add(interview)

    rounds = [
        (1, "TECHNICAL", "Python GIL", "How does the Python Global Interpreter Lock affect multithreading?", "It limits CPU-bound thread execution to one core."),
        (2, "APTITUDE", "Quantitative", "If 5 workers build 5 bikes in 5 hours, how many hours do 100 workers take for 100 bikes?", "5 hours"),
        (3, "HR", "Behavioral", "Tell me about a time you resolved a conflict with a teammate.", "I listened to their technical concerns and reached a consensus."),
        (4, "TECHNICAL", "Database", "What is the difference between SQL JOIN and UNION?", "JOIN combines columns from tables; UNION combines rows."),
    ]

    # Pre-add all questions to DB so total_questions is 4
    q_map = {}
    for seq, r_type, comp, q_txt, ans_txt in rounds:
        q = InterviewQuestion(
            id=str(uuid.uuid4()),
            interview_id=interview.id,
            sequence_number=seq,
            round_type=r_type,
            competency_targeted=comp,
            difficulty="MEDIUM",
            question_text=q_txt,
            status="PENDING",
        )
        db_session.add(q)
        q_map[seq] = q
    db_session.commit()

    service = InterviewService(db_session)

    for seq, r_type, comp, q_txt, ans_txt in rounds:
        q = q_map[seq]
        resp = service.submit_answer(
            interview_id=interview.id,
            question_id=q.id,
            question_text=q_txt,
            answer=ans_txt,
        )

        ev = resp.get("evaluation", {})
        assert ev.get("question_id") == seq
        assert ev.get("round_type") == r_type


def test_question_context_mismatch_safety_guard(mocker, db_session):
    """
    Verifies that if an evaluator node returns an evaluation with a mismatched sequence number,
    the backend safety guard immediately catches it and rejects execution.
    """
    user = User(id=str(uuid.uuid4()), email=f"mismatch_guard_{uuid.uuid4()}@example.com", password_hash="pw", full_name="Guard User")
    db_session.add(user)

    resume = Resume(id=str(uuid.uuid4()), user_id=user.id, file_path="r.pdf", raw_text="Dev", status="PROCESSED")
    db_session.add(resume)
    jd = JobDescription(id=str(uuid.uuid4()), user_id=user.id, raw_text="JD", target_role="Dev", required_skills='["Go"]')
    db_session.add(jd)
    interview = Interview(id=str(uuid.uuid4()), user_id=user.id, resume_id=resume.id, jd_id=jd.id, status="IN_PROGRESS")
    db_session.add(interview)

    q = InterviewQuestion(
        id=str(uuid.uuid4()),
        interview_id=interview.id,
        sequence_number=2,
        round_type="APTITUDE",
        competency_targeted="Math",
        difficulty="EASY",
        question_text="What is 10 + 20?",
        status="PENDING",
    )
    db_session.add(q)
    db_session.commit()

    # Mock master_workflow.invoke to simulate a mismatched evaluation return (seq 1 instead of seq 2)
    mocker.patch(
        "app.services.interview_service.master_workflow.invoke",
        return_value={
            "evaluations": [
                {
                    "score": 5,
                    "rubric_breakdown": {"Correctness": 3},
                    "feedback": "Mismatched evaluation return",
                    "ideal_answer_summary": "30",
                    "needs_human_review": False,
                    "question_id": 1, # MISMATCHED! Expected 2
                }
            ]
        },
    )

    service = InterviewService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        service.submit_answer(
            interview_id=interview.id,
            question_id=q.id,
            question_text=q.question_text,
            answer="30",
        )

    assert exc_info.value.status_code == 500
    assert "QUESTION_CONTEXT_MISMATCH" in exc_info.value.detail
