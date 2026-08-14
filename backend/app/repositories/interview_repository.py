"""
Interview and related repositories.
"""

import json
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import (
    AgentLog,
    CompetencyMatrix,
    Evaluation,
    Interview,
    InterviewAnswer,
    InterviewPlan,
    InterviewQuestion,
    InterviewReport,
)
from app.repositories.base import Repository


class InterviewRepository(Repository[Interview]):
    """Repository for Interview model operations."""

    def __init__(self, db: Session):
        super().__init__(db, Interview)

    def list_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> list[Interview]:
        """Get all interviews for a user."""
        return (
            self.db.query(Interview)
            .filter(Interview.user_id == user_id)
            .order_by(Interview.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_user_and_status(
        self, user_id: str, status: str, skip: int = 0, limit: int = 100
    ) -> list[Interview]:
        """Get interviews for a user filtered by status."""
        return (
            self.db.query(Interview)
            .filter(and_(Interview.user_id == user_id, Interview.status == status))
            .order_by(Interview.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


class CompetencyMatrixRepository(Repository[CompetencyMatrix]):
    """Repository for CompetencyMatrix model operations."""

    def __init__(self, db: Session):
        super().__init__(db, CompetencyMatrix)

    def get_by_interview(self, interview_id: str) -> CompetencyMatrix | None:
        """Get competency matrix for an interview."""
        return (
            self.db.query(CompetencyMatrix)
            .filter(CompetencyMatrix.interview_id == interview_id)
            .first()
        )


class InterviewPlanRepository(Repository[InterviewPlan]):
    """Repository for InterviewPlan model operations."""

    def __init__(self, db: Session):
        super().__init__(db, InterviewPlan)

    def get_by_interview(self, interview_id: str) -> InterviewPlan | None:
        """Get interview plan for an interview."""
        return (
            self.db.query(InterviewPlan)
            .filter(InterviewPlan.interview_id == interview_id)
            .first()
        )


class InterviewQuestionRepository(Repository[InterviewQuestion]):
    """Repository for InterviewQuestion model operations."""

    def __init__(self, db: Session):
        super().__init__(db, InterviewQuestion)

    def list_by_interview(
        self, interview_id: str, skip: int = 0, limit: int = 100
    ) -> list[InterviewQuestion]:
        """Get all questions for an interview in sequence order."""
        return (
            self.db.query(InterviewQuestion)
            .filter(InterviewQuestion.interview_id == interview_id)
            .order_by(InterviewQuestion.sequence_number)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_interview_and_sequence(
        self, interview_id: str, sequence_number: int
    ) -> InterviewQuestion | None:
        """Get a specific question by interview and sequence."""
        return (
            self.db.query(InterviewQuestion)
            .filter(
                and_(
                    InterviewQuestion.interview_id == interview_id,
                    InterviewQuestion.sequence_number == sequence_number,
                )
            )
            .first()
        )


class InterviewAnswerRepository(Repository[InterviewAnswer]):
    """Repository for InterviewAnswer model operations."""

    def __init__(self, db: Session):
        super().__init__(db, InterviewAnswer)

    def get_by_question(self, question_id: str) -> InterviewAnswer | None:
        """Get answer for a question."""
        return (
            self.db.query(InterviewAnswer)
            .filter(InterviewAnswer.question_id == question_id)
            .first()
        )

    def list_answers_with_evaluations_by_interview(self, interview_id: str) -> list[dict[str, Any]]:
        """Get joined questions, answers, and evaluations for an interview session directly from DB."""
        questions = (
            self.db.query(InterviewQuestion)
            .filter(InterviewQuestion.interview_id == interview_id)
            .order_by(InterviewQuestion.sequence_number)
            .all()
        )
        results = []
        for q in questions:
            ans = (
                self.db.query(InterviewAnswer)
                .filter(InterviewAnswer.question_id == q.id)
                .first()
            )
            if ans:
                ev = (
                    self.db.query(Evaluation)
                    .filter(Evaluation.answer_id == ans.id)
                    .first()
                )
                eval_dict = {}
                if ev:
                    try:
                        eval_dict = json.loads(ev.rubric_breakdown) if ev.rubric_breakdown else {}
                    except Exception:
                        eval_dict = {"score": ev.score, "reasoning": ev.feedback}
                    if isinstance(eval_dict, dict):
                        if "score" not in eval_dict:
                            eval_dict["score"] = ev.score
                        if "reasoning" not in eval_dict and ev.feedback:
                            eval_dict["reasoning"] = ev.feedback
                    else:
                        eval_dict = {"score": ev.score, "reasoning": ev.feedback}

                results.append({
                    "question_id": q.id,
                    "question_text": q.question_text,
                    "candidate_answer": ans.answer_text,
                    "evaluation": eval_dict,
                    "timestamp": ans.created_at.isoformat() if ans.created_at else None,
                })
        return results


class EvaluationRepository(Repository[Evaluation]):
    """Repository for Evaluation model operations."""

    def __init__(self, db: Session):
        super().__init__(db, Evaluation)

    def get_by_answer(self, answer_id: str) -> Evaluation | None:
        """Get evaluation for an answer."""
        return (
            self.db.query(Evaluation)
            .filter(Evaluation.answer_id == answer_id)
            .first()
        )


class InterviewReportRepository(Repository[InterviewReport]):
    """Repository for InterviewReport model operations."""

    def __init__(self, db: Session):
        super().__init__(db, InterviewReport)

    def get_by_interview(self, interview_id: str) -> InterviewReport | None:
        """Get report for an interview."""
        return (
            self.db.query(InterviewReport)
            .filter(InterviewReport.interview_id == interview_id)
            .first()
        )


class AgentLogRepository(Repository[AgentLog]):
    """Repository for AgentLog model operations."""

    def __init__(self, db: Session):
        super().__init__(db, AgentLog)

    def list_by_interview(
        self, interview_id: str, skip: int = 0, limit: int = 100
    ) -> list[AgentLog]:
        """Get all agent logs for an interview."""
        return (
            self.db.query(AgentLog)
            .filter(AgentLog.interview_id == interview_id)
            .order_by(AgentLog.created_at)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_interview_and_agent(
        self, interview_id: str, agent_name: str, skip: int = 0, limit: int = 100
    ) -> list[AgentLog]:
        """Get logs for a specific agent in an interview."""
        return (
            self.db.query(AgentLog)
            .filter(
                and_(
                    AgentLog.interview_id == interview_id,
                    AgentLog.agent_name == agent_name,
                )
            )
            .order_by(AgentLog.created_at)
            .offset(skip)
            .limit(limit)
            .all()
        )
