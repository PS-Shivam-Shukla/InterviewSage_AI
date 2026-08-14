"""
Enterprise Prompt Registry & Versioning Subsystem.
Manages version-controlled prompt templates, variable substitution, and rollback.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger
from app.core.metrics import PROMPT_VERSION_USAGE_TOTAL

logger = get_logger(__name__)


@dataclass
class PromptTemplateSpec:
    prompt_key: str                           # e.g. "prompt:question_personalizer"
    version: str                              # e.g. "v1", "v2"
    system_template: str
    user_template: str
    description: str = ""
    is_active: bool = True


DEFAULT_REGISTRY_TEMPLATES: dict[str, dict[str, PromptTemplateSpec]] = {
    "prompt:question_personalizer": {
        "v1": PromptTemplateSpec(
            prompt_key="prompt:question_personalizer",
            version="v1",
            system_template=(
                "You are a Principal Technical Interviewer at a top technology enterprise.\n"
                "Your role is to personalize baseline interview questions using actual candidate project context.\n"
                "Do NOT alter the core competency or difficulty of the baseline question.\n"
                "Contextuate the question to refer specifically to projects, technologies, or scale mentioned in the candidate's resume."
            ),
            user_template=(
                "Candidate Level: {{ seniority_level }}\n"
                "Target Competency: {{ target_competency }}\n"
                "Candidate Project Context: {{ project_context }}\n"
                "Baseline Question: {{ baseline_question }}\n\n"
                "Generate a personalized, direct technical interview question for this candidate."
            ),
            description="Initial production baseline question personalizer prompt.",
        ),
        "v2": PromptTemplateSpec(
            prompt_key="prompt:question_personalizer",
            version="v2",
            system_template=(
                "You are a Senior Staff System Architect.\n"
                "Personalize baseline questions with strict technical focus on architectural trade-offs."
            ),
            user_template=(
                "Seniority: {{ seniority_level }}\n"
                "Competency: {{ target_competency }}\n"
                "Context: {{ project_context }}\n"
                "Baseline: {{ baseline_question }}\n"
                "Produce advanced technical interview prompt."
            ),
            description="Architecture-focused question personalizer prompt v2.",
        ),
    },
    "prompt:answer_evaluator": {
        "v1": PromptTemplateSpec(
            prompt_key="prompt:answer_evaluator",
            version="v1",
            system_template=(
                "You are a Technical Evaluation Expert.\n"
                "Evaluate the candidate's answer against the target question and ideal concepts.\n"
                "Provide objective analysis focusing strictly on technical depth, completeness, and clarity."
            ),
            user_template=(
                "Question: {{ question_text }}\n"
                "Target Concepts: {{ target_concepts }}\n"
                "Answer: {{ candidate_answer }}\n"
                "Evaluate technical depth and produce evaluation report JSON."
            ),
            description="Production baseline evaluation agent prompt.",
        ),
    },
    "prompt:report_synthesizer": {
        "v1": PromptTemplateSpec(
            prompt_key="prompt:report_synthesizer",
            version="v1",
            system_template=(
                "You are an Executive Talent Partner preparing a final candidate evaluation report."
            ),
            user_template=(
                "Candidate: {{ candidate_name }}\n"
                "Role: {{ target_role }}\n"
                "Scorecard: {{ scorecard }}\n"
                "Highlights: {{ highlights }}\n"
                "Generate final executive evaluation report."
            ),
            description="Production baseline report synthesizer prompt.",
        ),
    },
}


class PromptRegistry:
    """
    Registry managing prompt template versions, variable rendering, and usage metrics.
    """

    def __init__(self) -> None:
        self._registry: dict[str, dict[str, PromptTemplateSpec]] = dict(DEFAULT_REGISTRY_TEMPLATES)

    def register_prompt(
        self,
        prompt_key: str,
        version: str,
        system_template: str,
        user_template: str,
        description: str = "",
        is_active: bool = True,
    ) -> PromptTemplateSpec:
        """Register a new prompt template version."""
        if prompt_key not in self._registry:
            self._registry[prompt_key] = {}

        spec = PromptTemplateSpec(
            prompt_key=prompt_key,
            version=version,
            system_template=system_template,
            user_template=user_template,
            description=description,
            is_active=is_active,
        )
        self._registry[prompt_key][version] = spec
        logger.info(f"Registered prompt template [{prompt_key}] version [{version}]")
        return spec

    def get_prompt(self, prompt_key: str, version: str = "v1") -> PromptTemplateSpec:
        """Retrieve a specific prompt template spec by key and version, with fallback to v1 or default."""
        versions = self._registry.get(prompt_key)
        if not versions:
            return PromptTemplateSpec(
                prompt_key=prompt_key,
                version="v1",
                system_template=f"You are an AI assistant for task {prompt_key}.",
                user_template="{{ user_input }}",
            )

        spec = versions.get(version) or versions.get("v1") or list(versions.values())[0]
        return spec

    def render(self, prompt_key: str, version: str = "v1", variables: dict[str, Any] | None = None) -> dict[str, str]:
        """
        Render system and user prompt templates with variable substitution.
        """
        spec = self.get_prompt(prompt_key, version)
        vars_dict = variables or {}

        rendered_system = spec.system_template
        rendered_user = spec.user_template

        for key, val in vars_dict.items():
            pattern_str = r"\{\{\s*" + re.escape(key) + r"\s*\}\}"
            pattern = re.compile(pattern_str)
            rendered_system = pattern.sub(str(val), rendered_system)
            rendered_user = pattern.sub(str(val), rendered_user)

        PROMPT_VERSION_USAGE_TOTAL.labels(prompt_key=prompt_key, version=spec.version).inc()

        return {
            "system": rendered_system,
            "user": rendered_user,
            "prompt_key": spec.prompt_key,
            "version": spec.version,
        }

    def list_versions(self, prompt_key: str) -> list[str]:
        """List available versions for a prompt key."""
        return list(self._registry.get(prompt_key, {}).keys())
