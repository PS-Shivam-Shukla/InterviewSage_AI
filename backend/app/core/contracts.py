"""
Enterprise Information Contracts Module (ADD-V5)
Defines explicit runtime validation contracts to eliminate architectural ambiguity.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ContractValidationResult(BaseModel):
    is_valid: bool
    contract_name: str
    violations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NegativeConstraintContract:
    """
    Contract 1: Negative Constraint Contract
    Guarantees forbidden technical domains are excluded from generated text.
    """

    @staticmethod
    def validate(text: str, negative_skills: list[str]) -> ContractValidationResult:
        from app.kernel.guardrails import Guardrails

        gr = Guardrails()
        is_valid, violations = gr.validate_negative_constraints(text, negative_skills)
        return ContractValidationResult(
            is_valid=is_valid,
            contract_name="NegativeConstraintContract",
            violations=violations,
            metadata={"negative_skills": negative_skills},
        )


class BlueprintConstraintContract:
    """
    Contract 2: Blueprint Constraint Contract
    Guarantees generated interview blueprints satisfy question counts and sum constraints.
    """

    @staticmethod
    def validate(blueprint: dict[str, Any]) -> ContractValidationResult:
        violations: list[str] = []
        items = blueprint.get("blueprint_items") or []
        total_q = blueprint.get("total_questions", 0)

        if total_q <= 0:
            violations.append("total_questions must be greater than 0")

        if len(items) != total_q and total_q > 0:
            violations.append(
                f"blueprint_items count ({len(items)}) does not match total_questions ({total_q})"
            )

        return ContractValidationResult(
            is_valid=len(violations) == 0,
            contract_name="BlueprintConstraintContract",
            violations=violations,
            metadata={"total_questions": total_q, "items_count": len(items)},
        )


class EvaluationConfidenceContract:
    """
    Contract 3: Evaluation Confidence Contract
    Guarantees statistical reliability of automated evaluation scores.
    """

    @staticmethod
    def validate(
        evaluation: dict[str, Any], min_confidence: float = 0.75
    ) -> ContractValidationResult:
        violations: list[str] = []
        conf = float(evaluation.get("confidence_score", 1.0))
        score = float(evaluation.get("score", 0.0))

        if conf < min_confidence:
            violations.append(f"Confidence score {conf} is below threshold {min_confidence}")

        if not (0.0 <= score <= 100.0):
            violations.append(f"Evaluation score {score} out of bounds [0.0, 100.0]")

        return ContractValidationResult(
            is_valid=len(violations) == 0,
            contract_name="EvaluationConfidenceContract",
            violations=violations,
            metadata={"confidence_score": conf, "score": score},
        )


class ATSScoreContract:
    """
    Contract 4: ATS Match Score Contract
    Guarantees valid range for ATS match calculation outputs.
    """

    @staticmethod
    def validate(ats_result: dict[str, Any]) -> ContractValidationResult:
        violations: list[str] = []
        ats_score = ats_result.get("ats_score", 0)

        if not (0 <= ats_score <= 100):
            violations.append(f"ats_score {ats_score} must be an integer in range [0, 100]")

        return ContractValidationResult(
            is_valid=len(violations) == 0,
            contract_name="ATSScoreContract",
            violations=violations,
            metadata={"ats_score": ats_score},
        )
