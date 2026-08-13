from __future__ import annotations

from typing import Any
import re

# Fallback default prompt templates for core system nodes
DEFAULT_PROMPTS: dict[str, dict[str, str]] = {
    "prompt:question_personalizer:v1": {
        "system": (
            "You are a Principal Technical Interviewer at a top technology enterprise.\n"
            "Your role is to personalize baseline interview questions using actual candidate project context.\n"
            "Do NOT alter the core competency or difficulty of the baseline question.\n"
            "Contextuate the question to refer specifically to projects, technologies, or scale mentioned in the candidate's resume."
        ),
        "user": (
            "Candidate Level: {{ seniority_level }}\n"
            "Target Competency: {{ target_competency }}\n"
            "Candidate Project Context: {{ project_context }}\n"
            "Baseline Question: {{ baseline_question }}\n\n"
            "Generate a personalized, direct technical interview question for this candidate."
        ),
    },
    "prompt:answer_evaluator:v1": {
        "system": (
            "You are a Technical Evaluation Expert.\n"
            "Evaluate the candidate's answer against the target question and ideal concepts.\n"
            "Provide objective, fair analysis focusing strictly on technical depth, completeness, and clarity."
        ),
        "user": (
            "Question Asked: {{ question_text }}\n"
            "Target Concepts: {{ target_concepts }}\n"
            "Candidate Answer: {{ candidate_answer }}\n\n"
            "Provide a technical evaluation detailing matched concepts, missing concepts, and key feedback."
        ),
    },
    "prompt:report_synthesizer:v1": {
        "system": (
            "You are an Executive Talent Partner preparing a final candidate evaluation report.\n"
            "Synthesize overall interview scorecard, major strengths, areas for improvement, and technical growth recommendations."
        ),
        "user": (
            "Candidate Name: {{ candidate_name }}\n"
            "Applied Role: {{ target_role }}\n"
            "Overall Scorecard: {{ scorecard }}\n"
            "Key Interview Turn Highlights: {{ highlights }}\n\n"
            "Generate a professional, structured executive summary report."
        ),
    },
}


class PromptManager:
    """
    Enterprise Prompt Manager Subsystem.
    Handles semantic prompt retrieval, versioning, template rendering, and variable substitution.
    """

    def __init__(self, custom_prompts: dict[str, dict[str, str]] | None = None) -> None:
        self._registry: dict[str, dict[str, str]] = dict(DEFAULT_PROMPTS)
        if custom_prompts:
            self._registry.update(custom_prompts)

    def register_prompt(self, prompt_key: str, system_template: str, user_template: str) -> None:
        """Register or update a prompt in the registry."""
        self._registry[prompt_key] = {
            "system": system_template,
            "user": user_template,
        }

    def get_prompt_template(self, prompt_key: str) -> dict[str, str]:
        """Retrieve system and user templates by semantic prompt key."""
        if prompt_key in self._registry:
            return self._registry[prompt_key]
        
        # Fallback to default version 1 if specific version not found
        base_key = prompt_key.split(":")[0] if ":" in prompt_key else prompt_key
        fallback_key = f"prompt:{base_key}:v1"
        if fallback_key in self._registry:
            return self._registry[fallback_key]
            
        raise KeyError(f"Prompt template key '{prompt_key}' not found in registry.")

    def render(self, prompt_key: str, variables: dict[str, Any]) -> dict[str, str]:
        """
        Render system and user prompts with the given variable substitutions.
        Uses simple mustache/jinja-style `{{ variable_name }}` syntax.
        """
        templates = self.get_prompt_template(prompt_key)
        
        system_rendered = self._substitute(templates["system"], variables)
        user_rendered = self._substitute(templates["user"], variables)

        return {
            "system": system_rendered,
            "user": user_rendered,
        }

    @staticmethod
    def _substitute(template: str, variables: dict[str, Any]) -> str:
        """Helper to replace {{ var }} in templates with stringified variable values."""
        rendered = template
        for key, val in variables.items():
            pattern = re.compile(r"\{\{\s*" + re.escape(key) + r"\s*\}\}")
            val_str = str(val) if val is not None else ""
            rendered = pattern.sub(val_str, rendered)
        return rendered
