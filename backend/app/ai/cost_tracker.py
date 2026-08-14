"""
Cost Tracking Engine for AI Gateway.
Estimates token cost in USD based on provider pricing tables per 1K tokens.
"""

from __future__ import annotations

# Pricing Table: (prompt_cost_per_1k, completion_cost_per_1k)
MODEL_PRICING_TABLE: dict[str, tuple[float, float]] = {
    # Free local models
    "ollama": (0.0, 0.0),
    "qwen2.5:7b": (0.0, 0.0),
    "qwen2.5:3b": (0.0, 0.0),
    "qwen2.5:32b": (0.0, 0.0),
    "deepseek-r1-distill-qwen:8b": (0.0, 0.0),
    
    # OpenAI
    "openai:gpt-4o": (0.0025, 0.010),
    "openai:gpt-4-turbo": (0.010, 0.030),
    "openai:gpt-3.5-turbo": (0.0005, 0.0015),
    
    # Anthropic Claude
    "claude:claude-3-5-sonnet": (0.003, 0.015),
    "claude:claude-3-haiku": (0.00025, 0.00125),
    
    # Google Gemini
    "gemini:gemini-1.5-pro": (0.00125, 0.005),
    "gemini:gemini-1.5-flash": (0.000075, 0.0003),
    
    # NVIDIA NIM
    "nvidia:nemotron-4-340b": (0.001, 0.003),
    "nvidia:llama-3.1-70b-instruct": (0.0008, 0.0024),
}


class CostTracker:
    """Calculates estimated financial cost in USD for LLM request/response token usage."""

    @staticmethod
    def calculate_cost(
        provider: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Calculate cost in USD for given token usage.
        """
        if provider.lower() == "ollama":
            return 0.0

        key = f"{provider.lower()}:{model_name.lower()}"
        rates = MODEL_PRICING_TABLE.get(key) or MODEL_PRICING_TABLE.get(model_name.lower()) or (0.001, 0.003)

        prompt_cost = (prompt_tokens / 1000.0) * rates[0]
        completion_cost = (completion_tokens / 1000.0) * rates[1]

        return round(prompt_cost + completion_cost, 6)
