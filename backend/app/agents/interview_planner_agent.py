"""
Interview Planner Agent (Section 10.7)
Uses the Dynamic Interview Strategy Engine (DISE) to classify candidates and generate custom blueprints.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.agents.base import BaseAgent
from app.graph.state import InterviewState
from app.strategy.blueprint_generator import BlueprintGenerator, InterviewBlueprint
from app.strategy.classifier import CandidateClassifier

# Initialize DISE singleton engines
classifier = CandidateClassifier()
blueprint_generator = BlueprintGenerator()


class RoundDetail(BaseModel):
    type: str
    duration_minutes: int
    question_count: int


class InterviewPlanOutput(BaseModel):
    hr_question_count: int = Field(ge=2, le=8)
    technical_question_count: int = Field(ge=3, le=12)
    estimated_duration_minutes: int = Field(ge=20, le=120)
    round_structure: list[RoundDetail] = Field(default_factory=list)

    @model_validator(mode="after")
    def total_in_range(self) -> InterviewPlanOutput:
        total = self.hr_question_count + self.technical_question_count
        if not 8 <= total <= 16:
            raise ValueError(
                f"Total questions must be 8–16, got {total}. Adjust hr or technical count."
            )
        return self


class InterviewPlannerAgent(BaseAgent):
    agent_name = "InterviewPlannerAgent"
    prompt_version = "v1"

    def _run(self, state: InterviewState, retry_feedback: str | None = None) -> dict:
        resume_data = state.get("resume_data") or state.get("resume_json") or {}
        jd_data = state.get("jd_data") or state.get("jd_json") or {}
        skill_graph = state.get("skill_graph") or {}

        # 1. Candidate Classification via DISE Engine
        classification = classifier.classify(resume_data, skill_graph)

        # 2. Blueprint Generation via DISE Engine
        blueprint: InterviewBlueprint = blueprint_generator.generate(
            classification=classification,
            jd_json=jd_data,
            duration_minutes=60,
        )

        hr_count = 4
        tech_count = 7

        plan = InterviewPlanOutput(
            hr_question_count=hr_count,
            technical_question_count=tech_count,
            estimated_duration_minutes=blueprint.total_duration_minutes,
            round_structure=[
                RoundDetail(type="HR", duration_minutes=20, question_count=hr_count),
                RoundDetail(type="TECHNICAL", duration_minutes=40, question_count=tech_count),
            ],
        )

        return {
            "interview_plan": plan.model_dump(),
            "classification": {
                "tier": classification.tier,
                "level": classification.level,
                "vector_scores": classification.vector_scores,
                "summary": classification.summary_reasoning,
            },
            "interview_blueprint": {
                "candidate_tier": blueprint.candidate_tier,
                "candidate_level": blueprint.candidate_level,
                "total_duration_minutes": blueprint.total_duration_minutes,
                "total_questions": blueprint.total_questions,
            },
        }

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        fallback = InterviewPlanOutput(
            hr_question_count=4,
            technical_question_count=6,
            estimated_duration_minutes=60,
            round_structure=[
                RoundDetail(type="HR", duration_minutes=20, question_count=4),
                RoundDetail(type="TECHNICAL", duration_minutes=40, question_count=6),
            ],
        )
        return {
            "interview_plan": fallback.model_dump(),
            "error_log": [{"agent": self.agent_name, "error": error}],
        }
