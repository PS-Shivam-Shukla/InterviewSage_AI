"""
AI Gateway Request Data Structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIGatewayRequest:
    """Standardized request payload sent to AI Gateway."""

    task_type: str  # e.g. "personalize_question", "evaluate_answer", "parse_resume"
    prompt_key: str  # e.g. "prompt:question_personalizer"
    prompt_version: str = "v1"
    variables: dict[str, Any] = field(default_factory=dict)
    system_prompt_override: str | None = None
    user_prompt_override: str | None = None
    provider_override: str | None = None  # e.g. "ollama", "nvidia", "openai", "claude", "gemini"
    model_override: str | None = None
    temperature: float = 0.3
    max_tokens: int = 2000
    timeout_seconds: float = 15.0
    require_json: bool = True
    interview_id: str | None = None
    user_id: str | None = None
