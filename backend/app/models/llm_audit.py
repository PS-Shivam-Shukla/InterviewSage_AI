"""
LLM Audit & Token Accounting Database Models.
Persists prompt versioning metadata, LLM request execution traces, response snapshots, and token costs.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base


class PromptVersion(Base):
    """Stores versioned prompt templates with active flags and rollback support."""

    __tablename__ = "prompt_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt_key = Column(String(100), nullable=False, index=True)  # e.g. "prompt:question_personalizer"
    version = Column(String(20), nullable=False, default="v1")     # e.g. "v1", "v2"
    system_template = Column(Text, nullable=False)
    user_template = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class LLMRequest(Base):
    """Tracks individual LLM API requests, latency, provider selection, and token cost accounting."""

    __tablename__ = "llm_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(100), nullable=True, index=True)
    interview_id = Column(String(100), nullable=True, index=True)
    provider = Column(String(50), nullable=False, default="ollama")
    model_name = Column(String(100), nullable=False)
    task_type = Column(String(50), nullable=False, default="general")
    prompt_version = Column(String(20), nullable=True, default="v1")
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    responses = relationship("LLMResponse", back_populates="llm_request", cascade="all, delete-orphan")


class LLMResponse(Base):
    """Stores LLM response payload, raw string, parsed output, and repair metadata."""

    __tablename__ = "llm_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    llm_request_id = Column(String(36), ForeignKey("llm_requests.id"), nullable=False)
    raw_output = Column(Text, nullable=True)
    parsed_output = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    repair_performed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    llm_request = relationship("LLMRequest", back_populates="responses")


class TokenUsage(Base):
    """Aggregates candidate and session token usage and estimated cost tracking."""

    __tablename__ = "token_usages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=True, index=True)
    interview_id = Column(String(100), nullable=True, index=True)
    model_name = Column(String(100), nullable=False)
    provider_name = Column(String(50), nullable=False, default="ollama")
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
