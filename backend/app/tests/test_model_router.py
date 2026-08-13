"""
Unit Tests for ModelRouter Subsystem.
Verifies task-based model selection, provider overrides, and fallback resolution.
"""

import pytest
from app.ai.router import ModelRouter, ModelSpec


def test_model_router_task_selection():
    """Verify ModelRouter maps tasks to appropriate model specs."""
    router = ModelRouter(default_provider="ollama")

    spec_fast = router.select_model("FAST_EXTRACTION")
    assert spec_fast.provider == "ollama"
    assert "qwen" in spec_fast.model_name

    spec_eval = router.select_model("DEEP_EVALUATION")
    assert "deepseek" in spec_eval.model_name or "qwen" in spec_eval.model_name


def test_model_router_provider_overrides():
    """Verify provider overrides map to correct provider specs."""
    router = ModelRouter()

    spec_openai = router.select_model("PERSONALIZATION", provider_override="openai")
    assert spec_openai.provider == "openai"
    assert spec_openai.model_name == "gpt-4o"

    spec_claude = router.select_model("REPORT_SYNTHESIS", provider_override="claude")
    assert spec_claude.provider == "claude"
    assert "claude" in spec_claude.model_name

    spec_nvidia = router.select_model("PERSONALIZATION", provider_override="nvidia")
    assert spec_nvidia.provider == "nvidia"


def test_model_router_fallback_chain():
    """Verify fallback chain returns valid secondary model spec."""
    router = ModelRouter()
    primary = router.select_model("PERSONALIZATION", provider_override="openai")
    fallback = router.get_fallback(primary)

    assert fallback is not None
    assert fallback.provider == "ollama"
    assert fallback.model_name == "qwen2.5:7b"
