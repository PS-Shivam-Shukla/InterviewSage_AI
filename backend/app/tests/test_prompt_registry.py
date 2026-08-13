"""
Unit Tests for PromptRegistry & JSONValidator Subsystems.
Verifies prompt versioning, rendering, variable substitution, and JSON validation & repair.
"""

import pytest
from app.ai.validator import JSONValidator
from app.prompts.registry import PromptRegistry, PromptTemplateSpec


def test_prompt_registry_get_and_render():
    """Verify registry retrieves versioned template and renders variables correctly."""
    registry = PromptRegistry()
    rendered = registry.render(
        prompt_key="prompt:question_personalizer",
        version="v1",
        variables={
            "seniority_level": "Senior Staff",
            "target_competency": "System Architecture",
            "project_context": "High-throughput messaging",
            "baseline_question": "Discuss Kafka partition key strategies.",
        },
    )

    assert rendered["version"] == "v1"
    assert "Senior Staff" in rendered["user"]
    assert "Kafka partition key strategies" in rendered["user"]


def test_prompt_registry_custom_registration():
    """Verify registering new prompt versions works and updates version listing."""
    registry = PromptRegistry()
    registry.register_prompt(
        prompt_key="prompt:custom_task",
        version="v3",
        system_template="System prompt for {{ task }}",
        user_template="User prompt for {{ task }}",
        description="Custom prompt v3",
    )

    versions = registry.list_versions("prompt:custom_task")
    assert "v3" in versions

    rendered = registry.render("prompt:custom_task", version="v3", variables={"task": "benchmarking"})
    assert "benchmarking" in rendered["user"]


def test_json_validator_and_repair():
    """Verify JSONValidator repairs markdown code blocks, trailing commas, and unclosed JSON."""
    # 1. Clean JSON
    valid, data, repaired = JSONValidator.validate_and_repair('{"key": "value"}')
    assert valid is True
    assert data == {"key": "value"}
    assert repaired is False

    # 2. Markdown fenced JSON
    fenced = "```json\n{\"status\": \"OK\"}\n```"
    valid, data, repaired = JSONValidator.validate_and_repair(fenced)
    assert valid is True
    assert data == {"status": "OK"}
    assert repaired is True

    # 3. Trailing comma repair
    trailing = '{"a": 1, "b": 2,}'
    valid, data, repaired = JSONValidator.validate_and_repair(trailing)
    assert valid is True
    assert data == {"a": 1, "b": 2}
    assert repaired is True

    # 4. Unclosed JSON repair
    unclosed = '{"tier": "Senior", "score": 90'
    valid, data, repaired = JSONValidator.validate_and_repair(unclosed)
    assert valid is True
    assert data == {"tier": "Senior", "score": 90}
    assert repaired is True
