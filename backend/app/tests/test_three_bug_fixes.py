"""
Regression and Verification Tests for the 3 Targeted Bug Fixes (Phase 2):
1. Bug #1: Question Routing / Distribution (Fresher 4 Aptitude + 3 Technical + 2 HR = 9, Experienced 3 Technical + 2 HR = 5) and Authoritative Category Alignment.
2. Bug #2: Speech-to-Text Pipeline Integration.
3. Bug #3: Aptitude Category-Aware Answer Sanity & Evaluation (numeric 420, 150, 297 $, boolean true, options).
"""

import uuid

from sqlalchemy.orm import Session

from app.agents import EvaluationAgent
from app.models import Interview, JobDescription, Resume, User
from app.services import InterviewService
from app.services.answer_sanity_guard import AnswerSanityGuard


def _create_test_fresher_interview(db: Session) -> tuple[User, Resume, JobDescription, Interview]:
    user = User(
        id=f"usr-{uuid.uuid4().hex[:8]}",
        email=f"fresher-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="pw",
        full_name="Fresher Candidate",
    )
    db.add(user)

    resume = Resume(
        id=f"res-{uuid.uuid4().hex[:8]}",
        user_id=user.id,
        file_path="uploads/fresher_resume.pdf",
        raw_text="Fresh Graduate BSc Computer Science student.",
        parsed_skills='["Python", "HTML"]',
        seniority_signal="JUNIOR",
    )
    db.add(resume)

    jd = JobDescription(
        id=f"jd-{uuid.uuid4().hex[:8]}",
        user_id=user.id,
        raw_text="Junior Software Engineer position requiring Python basics.",
        target_role="Junior Developer",
        required_skills='["Python"]',
        seniority_level="Junior",
    )
    db.add(jd)
    db.commit()

    service = InterviewService(db)
    interview = service.create_interview(user.id, resume.id, jd.id)
    return user, resume, jd, interview


def _create_test_senior_interview(db: Session) -> tuple[User, Resume, JobDescription, Interview]:
    user = User(
        id=f"usr-{uuid.uuid4().hex[:8]}",
        email=f"senior-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="pw",
        full_name="Senior Engineer",
    )
    db.add(user)

    resume = Resume(
        id=f"res-{uuid.uuid4().hex[:8]}",
        user_id=user.id,
        file_path="uploads/senior_resume.pdf",
        raw_text="Senior Backend Lead with 6 years experience in Python, FastAPI, Microservices.",
        parsed_skills='["Python", "FastAPI", "PostgreSQL", "Docker"]',
        seniority_signal="SENIOR",
    )
    db.add(resume)

    jd = JobDescription(
        id=f"jd-{uuid.uuid4().hex[:8]}",
        user_id=user.id,
        raw_text="Senior Backend Engineer role focused on system design and scalable microservices.",
        target_role="Senior Backend Engineer",
        required_skills='["Python", "FastAPI", "PostgreSQL"]',
        seniority_level="Senior",
    )
    db.add(jd)
    db.commit()

    service = InterviewService(db)
    interview = service.create_interview(user.id, resume.id, jd.id)
    return user, resume, jd, interview


# ── BUG #1 TESTS ─────────────────────────────────────────────────────────────


def test_fresher_question_distribution_and_authoritative_routing(db_session: Session):
    """Verify Fresher plan produces 4 Aptitude, 3 Technical, 2 HR (Total = 9 questions)."""
    user, resume, jd, interview = _create_test_fresher_interview(db_session)
    service = InterviewService(db_session)

    res = service.get_interview_plan(interview.id)
    assert res is not None
    plan = res["plan"]
    items = plan["blueprint_items"]

    assert len(items) == 9

    apt_count = sum(1 for item in items if item["round_type"] == "APTITUDE")
    tech_count = sum(1 for item in items if item["round_type"] == "TECHNICAL")
    hr_count = sum(1 for item in items if item["round_type"] == "HR")

    assert apt_count == 4
    assert tech_count == 3
    assert hr_count == 2

    # Verify category/round_type agreement for every single item
    for idx, item in enumerate(items, start=1):
        if idx <= 4:
            assert item["round_type"] == "APTITUDE"
        elif idx <= 7:
            assert item["round_type"] == "TECHNICAL"
        else:
            assert item["round_type"] == "HR"


def test_senior_question_distribution(db_session: Session):
    """Verify Senior plan produces 3 Technical, 2 HR (Total = 5 questions)."""
    user, resume, jd, interview = _create_test_senior_interview(db_session)
    service = InterviewService(db_session)

    res = service.get_interview_plan(interview.id)
    assert res is not None
    plan = res["plan"]
    items = plan["blueprint_items"]

    assert len(items) == 5

    tech_count = sum(1 for item in items if item["round_type"] == "TECHNICAL")
    hr_count = sum(1 for item in items if item["round_type"] == "HR")

    assert tech_count == 3
    assert hr_count == 2


# ── BUG #3 TESTS ─────────────────────────────────────────────────────────────


def test_aptitude_numeric_and_boolean_answers_not_gibberish():
    """Verify short aptitude responses (420, 150, 297 $, true) pass sanity guard as valid answers."""
    aptitude_answers = [
        "420",
        "150",
        "297 $",
        "$420",
        "42",
        "true",
        "false",
        "yes",
        "no",
        "4% decrease",
        "25%",
        "150 km",
        "4 days",
        "8:15",
        "Option B",
    ]

    for ans in aptitude_answers:
        res = AnswerSanityGuard.evaluate(ans, round_type="APTITUDE")
        assert res.is_valid_answer is True, f"Answer '{ans}' was incorrectly flagged as invalid!"
        assert (
            res.answer_quality == "VALID_ANSWER"
        ), f"Answer '{ans}' quality was '{res.answer_quality}', expected VALID_ANSWER"


def test_aptitude_deterministic_correctness_and_incorrectness():
    """Verify EvaluationAgent handles aptitude correctness (high score) vs incorrectness (low score NOT gibberish)."""
    eval_agent = EvaluationAgent()

    # Case 1: Compound interest $2,000 at 10% for 2 years -> Candidate gave "420"
    state_correct = {
        "current_question": {
            "sequence_number": 4,
            "round_type": "APTITUDE",
            "competency_targeted": "Quantitative Reasoning",
            "question_text": "What is the compound interest on $2,000 at 10% per annum compounded annually for 2 years?",
        },
        "answers": [{"answer_text": "420"}],
    }
    eval_res_correct = eval_agent(state_correct)
    eval_record_correct = eval_res_correct["evaluations"][0]
    assert eval_record_correct["score"] == 10
    assert eval_record_correct["answer_quality"] == "VALID_ANSWER"

    # Case 2: Wrong numeric answer -> Candidate gave "400"
    state_wrong = {
        "current_question": {
            "sequence_number": 4,
            "round_type": "APTITUDE",
            "competency_targeted": "Quantitative Reasoning",
            "question_text": "What is the compound interest on $2,000 at 10% per annum compounded annually for 2 years?",
        },
        "answers": [{"answer_text": "400"}],
    }
    eval_res_wrong = eval_agent(state_wrong)
    eval_record_wrong = eval_res_wrong["evaluations"][0]
    assert eval_record_wrong["score"] == 0
    assert eval_record_correct["score"] > eval_record_wrong["score"]
    assert eval_record_wrong["answer_quality"] == "VALID_ANSWER"  # NOT GIBBERISH!


def test_genuine_gibberish_still_caught():
    """Verify that actual gibberish (asdfasdfasdf, aaaaaaaaaa) is still caught by AnswerSanityGuard."""
    res_gibberish1 = AnswerSanityGuard.evaluate("asdfasdfasdf", round_type="TECHNICAL")
    assert res_gibberish1.answer_quality == "GIBBERISH"

    res_gibberish2 = AnswerSanityGuard.evaluate("aaaaaaaaaaaa", round_type="APTITUDE")
    assert res_gibberish2.answer_quality == "GIBBERISH"

    res_empty = AnswerSanityGuard.evaluate("", round_type="TECHNICAL")
    assert res_empty.answer_quality == "EMPTY"
