"""
Competency Mapping Agent (Section 10.6)
Merges JD + resume + industry standards → weighted competency matrix.
Hard constraint: weights MUST sum to exactly 100.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.agents.base import BaseAgent
from app.core.llm_client import LLMClient
from app.graph.state import InterviewState
from app.mcp import mcp_server
from app.prompts.loader import get_developer_prompt, get_system_prompt

# ── Default fallback matrix ───────────────────────────────────
DEFAULT_MATRIX = [
    {"name": "Technical Skills", "weight": 35, "description": "Core role competency", "rationale": "JD default"},
    {"name": "Problem Solving",  "weight": 25, "description": "Analytical thinking",  "rationale": "JD default"},
    {"name": "System Design",    "weight": 20, "description": "Architecture ability",  "rationale": "JD default"},
    {"name": "Communication",    "weight": 10, "description": "Clarity and teamwork",  "rationale": "JD default"},
    {"name": "Culture Fit",      "weight": 10, "description": "Values alignment",      "rationale": "JD default"},
]


# ── Output schema ─────────────────────────────────────────────

class CompetencyItem(BaseModel):
    name: str
    weight: int = Field(ge=1, le=99)
    description: str = ""
    rationale: str = ""


class CompetencyMatrixOutput(BaseModel):
    competencies: list[CompetencyItem]

    @model_validator(mode="after")
    def weights_sum_to_100(self) -> CompetencyMatrixOutput:
        total = sum(c.weight for c in self.competencies)
        if abs(total - 100) > 1:          # ±1 rounding tolerance
            raise ValueError(
                f"Competency weights must sum to 100, got {total}. "
                "Redistribute weights so they total exactly 100."
            )
        return self


# ── Agent ─────────────────────────────────────────────────────

class CompetencyMappingAgent(BaseAgent):
    agent_name = "CompetencyMappingAgent"
    prompt_version = "v1"

    def _temperature(self) -> float:
        return 0.1

    def _run(self, state: InterviewState, retry_feedback: str | None = None) -> dict:
        jd_data       = state.get("jd_data") or {}
        resume_data   = state.get("resume_data") or {}
        profile       = state.get("profile_summary") or {}
        role          = jd_data.get("target_role", "")

        # Optional company template from MCP resource
        company_template = mcp_server.read_resource(
            f"resource://competency-templates/{role.lower().replace(' ', '-')}"
        ) or {}

        developer = get_developer_prompt("competency_mapping_agent", self.prompt_version)
        user_content = (
            f"JD required skills: {jd_data.get('required_skills', [])}\n"
            f"JD seniority: {jd_data.get('seniority_level', 'MID')}\n"
            f"Resume seniority signal: {resume_data.get('seniority_signal', 'UNKNOWN')}\n"
            f"Candidate strengths: {profile.get('strengths', [])}\n"
            f"Candidate growth edges: {profile.get('growth_edges', [])}\n"
            f"Company template competencies: {company_template.get('competencies', [])}\n\n"
            "Return a JSON object: {\"competencies\": [{\"name\": ..., \"weight\": ..., "
            "\"description\": ..., \"rationale\": ...}, ...]}"
        )

        messages = LLMClient.build_messages(
            system_prompt=get_system_prompt("competency_mapping_agent", self.prompt_version),
            developer_prompt=developer,
            user_content=user_content,
        )

        output: CompetencyMatrixOutput = self._invoke_structured(
            messages, CompetencyMatrixOutput, retry_feedback
        )
        return {"competency_matrix": [c.model_dump() for c in output.competencies]}

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        return {
            "competency_matrix": DEFAULT_MATRIX,
            "error_log": [{"agent": self.agent_name, "error": error}],
        }
