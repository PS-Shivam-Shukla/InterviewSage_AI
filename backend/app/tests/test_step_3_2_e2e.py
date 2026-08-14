from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.interview import Evaluation, InterviewAnswer, InterviewQuestion
from app.services.interview_service import InterviewService


def test_e2e_question_and_evaluation_loop(client: TestClient, db_session: Session, sample_user, sample_resume, sample_jd):
    svc = InterviewService(db_session)
    user_id = sample_user.id
    resume_id = sample_resume.id
    jd_id = sample_jd.id

    # 1. Create Interview
    interview = svc.create_interview(
        user_id=user_id,
        resume_id=resume_id,
        jd_id=jd_id,
        payload={"role": "Senior Backend Engineer", "skills": ["Python", "FastAPI", "PostgreSQL", "LangGraph"]},
    )
    assert interview is not None
    interview_id = interview.id
    assert interview.status == "PLANNING"

    # 2. Get Interview Plan
    plan_res = svc.get_interview_plan(interview_id)
    assert plan_res is not None
    plan = plan_res.get("plan", {})
    first_q = plan.get("first_question", {})
    assert first_q.get("text") is not None

    # 3. Submit Turn 1 Answer
    turn1_res = svc.submit_answer(
        interview_id=interview_id,
        answer="I implement connection pooling with min_size=2 and max_size=10 using SQLAlchemy and asyncpg.",
        question_id=first_q.get("id"),
        question_text=first_q.get("text"),
    )
    assert turn1_res.get("evaluation") is not None
    eval1 = turn1_res["evaluation"]
    next_q1 = turn1_res.get("next_question")
    assert eval1.get("score") is not None
    assert next_q1 is not None
    assert next_q1.get("sequence_number") == 2

    # 4. Submit Turn 2 Answer
    turn2_res = svc.submit_answer(
        interview_id=interview_id,
        answer="I use Redis for distributed locks and Celery with RabbitMQ for event-driven async task execution.",
        question_id=next_q1.get("id"),
        question_text=next_q1.get("text"),
    )
    assert turn2_res.get("evaluation") is not None
    eval2 = turn2_res["evaluation"]
    next_q2 = turn2_res.get("next_question")
    assert eval2.get("score") is not None
    assert next_q2 is not None
    assert next_q2.get("sequence_number") == 3

    # 5. Verify PostgreSQL Persistence & No Duplicate Questions
    db_questions = db_session.query(InterviewQuestion).filter(InterviewQuestion.interview_id == interview_id).order_by(InterviewQuestion.sequence_number).all()
    db_answers = db_session.query(InterviewAnswer).filter(InterviewAnswer.question_id.in_([q.id for q in db_questions])).all()
    db_evals = db_session.query(Evaluation).filter(Evaluation.answer_id.in_([a.id for a in db_answers])).all()

    assert len(db_answers) == 2
    assert len(db_evals) == 2
