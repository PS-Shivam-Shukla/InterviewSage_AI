from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.job_description import JobDescription
    from app.models.resume import Resume
    from app.models.user import User


class Interview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interviews"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("resumes.id", ondelete="RESTRICT"), nullable=False
    )
    jd_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_descriptions.id", ondelete="RESTRICT"), nullable=False
    )
    # PLANNING | IN_PROGRESS | PAUSED | COMPLETED | FAILED
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PLANNING", index=True)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # HR | TECHNICAL | COMPLETE | null
    current_round: Mapped[str | None] = mapped_column(String(20), nullable=True)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="interviews")
    resume: Mapped[Resume] = relationship("Resume", back_populates="interviews")
    job_description: Mapped[JobDescription] = relationship(
        "JobDescription", back_populates="interviews"
    )
    competency_matrix: Mapped[CompetencyMatrix | None] = relationship(
        "CompetencyMatrix", back_populates="interview", uselist=False, cascade="all, delete-orphan"
    )
    interview_plan: Mapped[InterviewPlan | None] = relationship(
        "InterviewPlan", back_populates="interview", uselist=False, cascade="all, delete-orphan"
    )
    questions: Mapped[list[InterviewQuestion]] = relationship(
        "InterviewQuestion",
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.sequence_number",
    )
    report: Mapped[InterviewReport | None] = relationship(
        "InterviewReport", back_populates="interview", uselist=False, cascade="all, delete-orphan"
    )
    agent_logs: Mapped[list[AgentLog]] = relationship(
        "AgentLog",
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="AgentLog.created_at",
    )

    @property
    def total_questions(self) -> int:
        if self.questions:
            return len(self.questions)
        try:
            if self.resume and (self.resume.seniority_signal or "").upper() == "FRESHER":
                return 7
        except Exception:
            pass
        return 5

    def __repr__(self) -> str:
        return f"<Interview id={self.id!r} status={self.status!r}>"


class CompetencyMatrix(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "competency_matrices"

    interview_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    # JSON list of {name, weight, description}
    competencies: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    interview: Mapped[Interview] = relationship("Interview", back_populates="competency_matrix")

    def __repr__(self) -> str:
        return f"<CompetencyMatrix id={self.id!r} interview_id={self.interview_id!r}>"


class InterviewPlan(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "interview_plans"

    interview_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    hr_question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    technical_question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    # JSON round structure
    round_structure: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    interview: Mapped[Interview] = relationship("Interview", back_populates="interview_plan")

    def __repr__(self) -> str:
        return f"<InterviewPlan id={self.id!r} interview_id={self.interview_id!r}>"


class InterviewQuestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interview_questions"
    __table_args__ = (
        UniqueConstraint("interview_id", "sequence_number", name="uq_question_sequence"),
    )

    interview_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # HR | TECHNICAL
    round_type: Mapped[str] = mapped_column(String(20), nullable=False)
    competency_targeted: Mapped[str] = mapped_column(String(255), nullable=False)
    # EASY | MEDIUM | HARD | ADVANCED
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    interview: Mapped[Interview] = relationship("Interview", back_populates="questions")
    answer: Mapped[InterviewAnswer | None] = relationship(
        "InterviewAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<InterviewQuestion id={self.id!r} seq={self.sequence_number}>"


class InterviewAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interview_answers"

    question_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # one answer per question
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_time_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    question: Mapped[InterviewQuestion] = relationship("InterviewQuestion", back_populates="answer")
    evaluation: Mapped[Evaluation | None] = relationship(
        "Evaluation", back_populates="answer", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<InterviewAnswer id={self.id!r} question_id={self.question_id!r}>"


class Evaluation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "evaluations"

    answer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("interview_answers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # one evaluation per answer
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    # JSON: {dimension: sub_score}
    rubric_breakdown: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ideal_answer_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")

    answer: Mapped[InterviewAnswer] = relationship("InterviewAnswer", back_populates="evaluation")

    def __repr__(self) -> str:
        return f"<Evaluation id={self.id!r} score={self.score}>"


class InterviewReport(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "interview_reports"

    interview_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    # JSON lists
    competency_scorecard: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    improvement_plan: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    transcript_snapshot: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    interview: Mapped[Interview] = relationship("Interview", back_populates="report")

    def __repr__(self) -> str:
        return f"<InterviewReport id={self.id!r} interview_id={self.interview_id!r}>"


class AgentLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_logs"

    interview_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    node_status: Mapped[str] = mapped_column(String(20), nullable=False)  # SUCCESS|RETRY|FAILED
    # JSON snapshots
    input_snapshot: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    output_snapshot: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # prompt versioning
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)

    interview: Mapped[Interview] = relationship("Interview", back_populates="agent_logs")

    def __repr__(self) -> str:
        return f"<AgentLog id={self.id!r} agent={self.agent_name!r} status={self.node_status!r}>"
