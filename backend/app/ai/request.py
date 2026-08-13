"""
AI Gateway Request Data Structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AIGatewayRequest:
    """Standardized request payload sent to AI Gateway."""

    task_type: str                            # e.g. "personalize_question", "evaluate_answer", "parse_resume"
    prompt_key: str                           # e.g. "prompt:question_personalizer"
    prompt_version: str = "v1"
    variables: Dict[str, Any] = field(default_factory=dict)
    system_prompt_override: Optional[str] = None
    user_prompt_override: Optional[str] = None
    provider_override: Optional[str] = None   # e.g. "ollama", "nvidia", "openai", "claude", "gemini"
    model_override: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 2000
    timeout_seconds: float = 15.0
    require_json: bool = True
    interview_id: Optional[str] = None
    user_id: Optional[str] = None
