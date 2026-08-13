"""
Token Accounting Subsystem for AI Gateway.
Estimates token usage, calculates cost, records Prometheus counters, and persists audit logs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.ai.cost_tracker import CostTracker
from app.core.logging import get_logger
from app.core.metrics import LLM_COST_TOTAL, LLM_TOKENS_TOTAL
from app.models.llm_audit import LLMRequest, TokenUsage

logger = get_logger(__name__)


class TokenTracker:
    """Tracks token consumption, calculates cost, and records DB audit logs."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count using baseline 4 chars per token approximation."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    @classmethod
    def record_usage(
        cls,
        provider: str,
        model_name: str,
        prompt_text: str,
        completion_text: str,
        db: Optional[Session] = None,
        interview_id: Optional[str] = None,
        user_id: Optional[str] = None,
        prompt_tokens_override: Optional[int] = None,
        completion_tokens_override: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Compute tokens, calculate cost, update metrics, and optionally persist TokenUsage.
        """
        p_tokens = prompt_tokens_override if prompt_tokens_override is not None else cls.estimate_tokens(prompt_text)
        c_tokens = completion_tokens_override if completion_tokens_override is not None else cls.estimate_tokens(completion_text)
        total_tokens = p_tokens + c_tokens

        cost_usd = CostTracker.calculate_cost(provider, model_name, p_tokens, c_tokens)

        # Prometheus metrics
        LLM_TOKENS_TOTAL.labels(token_type="prompt", provider=provider, model_name=model_name).inc(p_tokens)
        LLM_TOKENS_TOTAL.labels(token_type="completion", provider=provider, model_name=model_name).inc(c_tokens)
        if cost_usd > 0:
            LLM_COST_TOTAL.labels(provider=provider, model_name=model_name).inc(cost_usd)

        # Database audit persistence
        if db is not None:
            try:
                usage_record = TokenUsage(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    interview_id=interview_id,
                    model_name=model_name,
                    provider_name=provider,
                    prompt_tokens=p_tokens,
                    completion_tokens=c_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=cost_usd,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(usage_record)
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.error(f"Failed to persist TokenUsage audit record: {exc}", exc_info=True)

        return {
            "prompt_tokens": p_tokens,
            "completion_tokens": c_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd,
        }
