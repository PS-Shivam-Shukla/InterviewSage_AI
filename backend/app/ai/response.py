"""
AI Gateway Response Data Structures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AIGatewayResponse:
    """Standardized response payload returned by AI Gateway."""

    success: bool
    raw_content: str
    parsed_json: dict[str, Any] | None = None
    provider: str = "ollama"
    model_name: str = "qwen2.5:7b"
    prompt_version: str = "v1"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    retry_count: int = 0
    repair_performed: bool = False
    error_message: str | None = None
