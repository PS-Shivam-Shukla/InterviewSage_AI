"""
Enterprise Model Router for AI Gateway.
Supports Ollama, NVIDIA NIM, OpenAI, Claude (Anthropic), and Gemini (Google) with fallback chains.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model_name: str
    context_window: int
    expected_latency_ms: int
    fallback_provider: str
    fallback_model: str


TASK_MODEL_MAPPING: dict[str, dict[str, ModelSpec]] = {
    "FAST_EXTRACTION": {
        "ollama": ModelSpec("ollama", "qwen2.5:3b", 8192, 800, "ollama", "qwen2.5:7b"),
        "openai": ModelSpec("openai", "gpt-3.5-turbo", 16384, 600, "ollama", "qwen2.5:3b"),
        "claude": ModelSpec("claude", "claude-3-haiku", 200000, 700, "ollama", "qwen2.5:3b"),
        "gemini": ModelSpec("gemini", "gemini-1.5-flash", 1000000, 500, "ollama", "qwen2.5:3b"),
        "nvidia": ModelSpec("nvidia", "llama-3.1-70b-instruct", 128000, 900, "ollama", "qwen2.5:3b"),
    },
    "PERSONALIZATION": {
        "ollama": ModelSpec("ollama", "qwen2.5:7b", 8192, 1800, "ollama", "qwen2.5:3b"),
        "openai": ModelSpec("openai", "gpt-4o", 128000, 1200, "ollama", "qwen2.5:7b"),
        "claude": ModelSpec("claude", "claude-3-5-sonnet", 200000, 1400, "ollama", "qwen2.5:7b"),
        "gemini": ModelSpec("gemini", "gemini-1.5-pro", 1000000, 1100, "ollama", "qwen2.5:7b"),
        "nvidia": ModelSpec("nvidia", "nemotron-4-340b", 128000, 1600, "ollama", "qwen2.5:7b"),
    },
    "DEEP_EVALUATION": {
        "ollama": ModelSpec("ollama", "deepseek-r1-distill-qwen:8b", 8192, 3000, "ollama", "qwen2.5:7b"),
        "openai": ModelSpec("openai", "gpt-4o", 128000, 2000, "ollama", "deepseek-r1-distill-qwen:8b"),
        "claude": ModelSpec("claude", "claude-3-5-sonnet", 200000, 2200, "ollama", "deepseek-r1-distill-qwen:8b"),
        "gemini": ModelSpec("gemini", "gemini-1.5-pro", 1000000, 1800, "ollama", "deepseek-r1-distill-qwen:8b"),
        "nvidia": ModelSpec("nvidia", "nemotron-4-340b", 128000, 2500, "ollama", "deepseek-r1-distill-qwen:8b"),
    },
    "REPORT_SYNTHESIS": {
        "ollama": ModelSpec("ollama", "qwen2.5:32b", 8192, 7000, "ollama", "qwen2.5:7b"),
        "openai": ModelSpec("openai", "gpt-4o", 128000, 3000, "ollama", "qwen2.5:7b"),
        "claude": ModelSpec("claude", "claude-3-5-sonnet", 200000, 3200, "ollama", "qwen2.5:7b"),
        "gemini": ModelSpec("gemini", "gemini-1.5-pro", 1000000, 2800, "ollama", "qwen2.5:7b"),
        "nvidia": ModelSpec("nvidia", "nemotron-4-340b", 128000, 4000, "ollama", "qwen2.5:7b"),
    },
}


class ModelRouter:
    """
    Enterprise Model Router for AI Gateway.
    Selects optimal model provider and executes provider fallback resolution.
    """

    def __init__(self, default_provider: str | None = None) -> None:
        self.default_provider = (default_provider or settings.llm_provider).lower()

    def select_model(
        self,
        task_type: str,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> ModelSpec:
        """
        Select ModelSpec based on task_type and optional overrides.
        """
        provider = (provider_override or self.default_provider).lower()
        if provider not in ["ollama", "openai", "claude", "gemini", "nvidia"]:
            provider = "ollama"

        task_key = task_type.upper()
        if task_key not in TASK_MODEL_MAPPING:
            task_key = "PERSONALIZATION"

        spec_dict = TASK_MODEL_MAPPING.get(task_key, TASK_MODEL_MAPPING["PERSONALIZATION"])
        spec = spec_dict.get(provider, spec_dict["ollama"])

        if model_override:
            return ModelSpec(
                provider=provider,
                model_name=model_override,
                context_window=spec.context_window,
                expected_latency_ms=spec.expected_latency_ms,
                fallback_provider=spec.fallback_provider,
                fallback_model=spec.fallback_model,
            )

        return spec

    def get_fallback(self, spec: ModelSpec) -> ModelSpec:
        """
        Return secondary fallback ModelSpec when primary model fails.
        """
        return ModelSpec(
            provider=spec.fallback_provider,
            model_name=spec.fallback_model,
            context_window=8192,
            expected_latency_ms=2000,
            fallback_provider="ollama",
            fallback_model="qwen2.5:7b",
        )
