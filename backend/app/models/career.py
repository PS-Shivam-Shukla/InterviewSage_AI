"""
AI Career Intelligence Engine ORM Models.
Tables:
- adaptive_sessions & difficulty_history
- company_profiles
- industry_benchmarks
- candidate_predictions
- skill_gap_analysis
- career_roadmaps
- interview_annotations
- knowledge_graph_nodes & knowledge_graph_edges
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class AdaptiveSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "adaptive_sessions"

    interview_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    current_difficulty: Mapped[float] = mapped_column(
        Float, nullable=False, default=5.0
    )  # 1.0 - 10.0 scale
    target_difficulty: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    consecutive_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consecutive_incorrect: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    history: Mapped[list["DifficultyHistory"]] = relationship(
        "DifficultyHistory", back_populates="session", cascade="all, delete-orphan"
    )


class DifficultyHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "difficulty_history"

    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("adaptive_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty_assigned: Mapped[float] = mapped_column(Float, nullable=False)
    performance_score: Mapped[float] = mapped_column(Float, nullable=False)
    response_latency_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    adjustment_reason: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["AdaptiveSession"] = relationship("AdaptiveSession", back_populates="history")


class CompanyProfile(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "company_profiles"

    company_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    coding_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.35)
    system_design_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.35)
    behavioral_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.30)
    key_principles: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )  # JSON List of principles

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )


class IndustryBenchmark(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "industry_benchmarks"

    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # Coding, System Design, Communication, etc.
    average_score: Mapped[float] = mapped_column(Float, nullable=False, default=68.0)
    top_10_percentile_score: Mapped[float] = mapped_column(Float, nullable=False, default=91.0)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )


class CandidatePrediction(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "candidate_predictions"

    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hire_probability: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 100.0%
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 100.0%
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)  # Hire | Borderline | Reject
    key_reasons: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON List

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )


class SkillGapAnalysis(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "skill_gap_analysis"

    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    missing_concepts: Mapped[str] = mapped_column(Text, nullable=False)  # JSON List
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="HIGH")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )


class CareerRoadmap(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "career_roadmaps"

    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    daily_plan: Mapped[str] = mapped_column(Text, nullable=False)  # JSON structured plan
    weekly_plan: Mapped[str] = mapped_column(Text, nullable=False)  # JSON structured plan
    monthly_plan: Mapped[str] = mapped_column(Text, nullable=False)  # JSON structured plan

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )


class InterviewAnnotation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "interview_annotations"

    interview_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp_mark: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "02:15"
    annotation_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "EXCELLENT", "PAUSE", "WEAKNESS", etc.
    note: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )


class KnowledgeGraphNode(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_graph_nodes"

    node_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # Candidate, Interview, Skill, Weakness, etc.
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    properties_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )


class KnowledgeGraphEdge(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_graph_edges"

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("knowledge_graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("knowledge_graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # "HAS_SKILL", "EVALUATED_BY", etc.

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
