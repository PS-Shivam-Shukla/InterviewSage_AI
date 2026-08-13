from __future__ import annotations

from typing import Any
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    alias: str
    model_name: str
    vram_mb: int
    expected_latency_ms: int
    context_window: int


MODEL_REGISTRY: dict[str, ModelSpec] = {
    "FAST_EXTRACTION": ModelSpec(
        alias="FAST_EXTRACTION",
        model_name="qwen2.5:3b",
        vram_mb=4200,
        expected_latency_ms=1200,
        context_window=8192,
    ),
    "PERSONALIZATION": ModelSpec(
        alias="PERSONALIZATION",
        model_name="qwen2.5:7b",
        vram_mb=5500,
        expected_latency_ms=2000,
        context_window=8192,
    ),
    "DEEP_EVALUATION": ModelSpec(
        alias="DEEP_EVALUATION",
        model_name="deepseek-r1-distill-qwen:8b",
        vram_mb=9200,
        expected_latency_ms=3500,
        context_window=8192,
    ),
    "REPORT_SYNTHESIS": ModelSpec(
        alias="REPORT_SYNTHESIS",
        model_name="qwen2.5:32b",
        vram_mb=19500,
        expected_latency_ms=8000,
        context_window=8192,
    ),
}


class ModelRouter:
    """
    Model Routing Architecture Subsystem.
    Assigns tasks to optimal local Ollama models based on capability, latency, and VRAM limits.
    """

    def __init__(self, default_provider: str = "ollama") -> None:
        self.provider = default_provider

    def select_model(self, task_type: str) -> ModelSpec:
        """
        Select model specification based on task type.
        """
        task_map = {
            "parse_resume": "FAST_EXTRACTION",
            "parse_jd": "FAST_EXTRACTION",
            "extract_skills": "FAST_EXTRACTION",
            "personalize_question": "PERSONALIZATION",
            "evaluate_answer": "DEEP_EVALUATION",
            "generate_report": "REPORT_SYNTHESIS",
        }
        alias = task_map.get(task_type, "PERSONALIZATION")
        return MODEL_REGISTRY[alias]

    def build_ollama_request(
        self,
        task_type: str,
        prompt_payload: dict[str, str],
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """
        Build standardized payload for Ollama HTTP API request.
        """
        spec = self.select_model(task_type)
        return {
            "model": spec.model_name,
            "messages": [
                {"role": "system", "content": prompt_payload.get("system", "")},
                {"role": "user", "content": prompt_payload.get("user", "")},
            ],
            "options": {
                "temperature": temperature,
                "num_ctx": spec.context_window,
            },
            "stream": False,
        }
