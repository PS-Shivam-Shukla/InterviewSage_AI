"""
Evaluation Rubric Definitions.
Defines scoring criteria for Technical, Behavioral, and Executive evaluation types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class RubricCriterion:
    name: str
    weight: float  # e.g. 0.35
    description: str


class EvaluationRubric:
    """Base evaluation rubric containing criteria and weights."""

    def __init__(self, name: str, criteria: List[RubricCriterion]) -> None:
        self.name = name
        self.criteria = criteria

    def score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted composite score from component scores dict."""
        total_score = 0.0
        total_weight = 0.0

        for crit in self.criteria:
            val = scores.get(crit.name, 0.0)
            total_score += val * crit.weight
            total_weight += crit.weight

        if total_weight == 0.0:
            return 0.0

        return round(total_score / total_weight, 2)


TECHNICAL_RUBRIC = EvaluationRubric(
    name="Technical Accuracy & Depth",
    criteria=[
        RubricCriterion("correctness", 0.40, "Accuracy of technical concepts and architecture"),
        RubricCriterion("faithfulness", 0.30, "Groundedness in given system specifications"),
        RubricCriterion("relevancy", 0.20, "Direct relevance to question asked"),
        RubricCriterion("clarity", 0.10, "Structural clarity and absence of jargon confusion"),
    ],
)

BEHAVIORAL_RUBRIC = EvaluationRubric(
    name="Behavioral STAR Method Rubric",
    criteria=[
        RubricCriterion("situation", 0.25, "Clear context and background explanation"),
        RubricCriterion("task", 0.25, "Specific role and responsibility identified"),
        RubricCriterion("action", 0.30, "Technical actions taken by candidate"),
        RubricCriterion("result", 0.20, "Measurable outcomes and business impact"),
    ],
)

EXECUTIVE_RUBRIC = EvaluationRubric(
    name="Executive Leadership & Trade-offs",
    criteria=[
        RubricCriterion("strategic_alignment", 0.35, "Alignment with enterprise business goals"),
        RubricCriterion("trade_off_analysis", 0.35, "Clear discussion of technical trade-offs"),
        RubricCriterion("communication", 0.30, "Executive presence and conciseness"),
    ],
)
