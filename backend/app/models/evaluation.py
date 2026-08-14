"""
AI Evaluation Framework Database Models.
Persists evaluation runs, sample evaluation results, benchmark metrics, prompt quality scores, and model quality scores.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class EvaluationRun(Base):
    """Represents a full evaluation run execution across a dataset."""

    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_name = Column(String(100), nullable=False, index=True)
    prompt_version = Column(String(50), nullable=False, default="v1")
    model_name = Column(String(100), nullable=False)
    dataset_name = Column(String(100), nullable=False, default="golden_dataset")
    total_samples = Column(Integer, default=0)
    passed_samples = Column(Integer, default=0)
    failed_samples = Column(Integer, default=0)
    avg_correctness = Column(Float, default=0.0)
    avg_faithfulness = Column(Float, default=0.0)
    avg_hallucination = Column(Float, default=0.0)
    avg_relevancy = Column(Float, default=0.0)
    avg_cost_usd = Column(Float, default=0.0)
    avg_latency_ms = Column(Float, default=0.0)
    pass_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    results = relationship("EvaluationResult", back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    """Detailed score result for an individual sample within an evaluation run."""

    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("evaluation_runs.id"), nullable=False)
    sample_id = Column(String(100), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    candidate_answer = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=True)
    correctness_score = Column(Float, default=0.0)
    faithfulness_score = Column(Float, default=0.0)
    hallucination_score = Column(Float, default=0.0)
    relevancy_score = Column(Float, default=0.0)
    passed = Column(Boolean, default=True)
    error_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    run = relationship("EvaluationRun", back_populates="results")


class BenchmarkResult(Base):
    """Summary record for model benchmarking comparison runs."""

    __tablename__ = "benchmark_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    benchmark_name = Column(String(100), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    prompt_version = Column(String(50), nullable=False, default="v1")
    overall_score = Column(Float, default=0.0)
    latency_p95_ms = Column(Float, default=0.0)
    total_cost_usd = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class PromptScore(Base):
    """Historical quality aggregate for a specific prompt version."""

    __tablename__ = "prompt_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt_key = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    average_accuracy = Column(Float, default=0.0)
    average_latency_ms = Column(Float, default=0.0)
    average_cost_usd = Column(Float, default=0.0)
    total_evaluations = Column(Integer, default=0)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class ModelScore(Base):
    """Historical quality aggregate for a specific model provider/tier."""

    __tablename__ = "model_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_name = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False, index=True)
    accuracy_score = Column(Float, default=0.0)
    latency_p95_ms = Column(Float, default=0.0)
    cost_per_1k_tokens = Column(Float, default=0.0)
    quality_rating = Column(String(20), default="STRONG")
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
