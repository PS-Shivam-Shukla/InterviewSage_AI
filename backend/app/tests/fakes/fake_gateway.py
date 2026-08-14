"""
Test-Only Fake AI Gateway Double.
Strictly isolated in app/tests/fakes/ for unit and integration testing.
Must NEVER be imported or used in production application code.
"""

from __future__ import annotations

import json
from typing import Any

from app.ai.gateway import AIGateway


class FakeAIGateway(AIGateway):
    """
    Test double providing deterministic responses for unit testing without live LLM dependencies.
    Overriding `_execute_llm_call` allows full DB audit logging and token accounting to run cleanly.
    """

    def __init__(self, predefined_response: dict[str, Any] | None = None) -> None:
        super().__init__()
        self.predefined_response = predefined_response or {
            "status": "COMPLETED",
            "tier": "Senior Engineer",
            "level": 3,
            "score": 85.0,
            "question_text": "How do you design scalable backend architectures?",
            "reasoning": "Clear explanation of architectural concepts.",
            "technical_coverage": 85,
            "confidence_score": 90,
        }

    def _execute_llm_call(
        self,
        provider: str,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Return predefined JSON string for unit testing."""
        return json.dumps(self.predefined_response)
