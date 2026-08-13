from __future__ import annotations

from typing import Any
from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateClassification:
    tier: str  # e.g., "Senior Engineer"
    level: int  # 1 to 7
    vector_scores: dict[str, float]
    summary_reasoning: str


class CandidateClassifier:
    """
    Multi-Vector Candidate Classification Engine.
    Evaluates candidate capability across YOE, Project Complexity, Tech Depth,
    Architecture Exposure, and Leadership Scale rather than simple years of experience.
    """

    TIER_MAP = {
        1: "Intern / Fresher",
        2: "Junior Engineer",
        3: "Mid-Level Engineer",
        4: "Senior Engineer",
        5: "Staff / Lead Engineer",
        6: "Principal Engineer / Architect",
        7: "Engineering Manager",
    }

    def classify(self, resume_json: dict[str, Any], skill_graph: dict[str, Any] | None = None) -> CandidateClassification:
        """
        Classify candidate into seniority tier based on resume metadata and skill graph.
        """
        experience_list = resume_json.get("experience", [])
        projects_list = resume_json.get("projects", [])
        skills_list = resume_json.get("skills", [])

        # 1. YOE Calculation
        total_yoe = self._calculate_yoe(experience_list)
        yoe_score = min(1.0, total_yoe / 12.0)

        # 2. Project Complexity Score
        project_score = self._evaluate_project_complexity(projects_list)

        # 3. Technical Depth Score
        tech_score = self._evaluate_tech_depth(skills_list)

        # 4. Architecture Exposure Score
        arch_score = self._evaluate_architecture_exposure(experience_list, projects_list)

        # 5. Leadership Scale Score
        leadership_score = self._evaluate_leadership_scale(experience_list)

        vector_scores = {
            "yoe": round(yoe_score, 2),
            "project_complexity": round(project_score, 2),
            "tech_depth": round(tech_score, 2),
            "architecture_exposure": round(arch_score, 2),
            "leadership_scale": round(leadership_score, 2),
        }

        # Weighted aggregate score (0.0 to 1.0)
        aggregate_score = (
            0.20 * yoe_score
            + 0.25 * project_score
            + 0.25 * tech_score
            + 0.20 * arch_score
            + 0.10 * leadership_score
        )

        # Map aggregate score to Tier 1-7
        if aggregate_score < 0.20:
            level = 1
        elif aggregate_score < 0.35:
            level = 2
        elif aggregate_score < 0.55:
            level = 3
        elif aggregate_score < 0.75:
            level = 4
        elif aggregate_score < 0.88:
            level = 5
        elif aggregate_score < 0.95:
            level = 6
        else:
            level = 7

        tier_name = self.TIER_MAP[level]
        summary = f"Classified as {tier_name} (Level {level}) with aggregate vector score {round(aggregate_score, 2)}."

        return CandidateClassification(
            tier=tier_name,
            level=level,
            vector_scores=vector_scores,
            summary_reasoning=summary,
        )

    @staticmethod
    def _calculate_yoe(experience_list: list[dict[str, Any]]) -> float:
        """Estimate total YOE from experience timeline."""
        if not experience_list:
            return 0.0
        # Simple heuristic based on number of experience entries if dates not structured
        return float(len(experience_list) * 2.0)

    @staticmethod
    def _evaluate_project_complexity(projects: list[dict[str, Any]]) -> float:
        if not projects:
            return 0.2
        keywords = ["distributed", "scale", "microservices", "high-throughput", "kafka", "redis", "kubernetes", "cloud"]
        score = 0.3
        for proj in projects:
            desc = str(proj.get("description", "")).lower()
            if any(k in desc for k in keywords):
                score += 0.2
        return min(1.0, score)

    @staticmethod
    def _evaluate_tech_depth(skills: list[str]) -> float:
        if not skills:
            return 0.2
        depth_indicators = ["asyncio", "concurrency", "memory", "profiling", "rust", "cpp", "distributed systems", "optimiz"]
        matched = sum(1 for s in skills if any(d in str(s).lower() for d in depth_indicators))
        return min(1.0, 0.3 + (matched * 0.15))

    @staticmethod
    def _evaluate_architecture_exposure(exp: list[dict[str, Any]], proj: list[dict[str, Any]]) -> float:
        combined = str(exp) + str(proj)
        arch_words = ["architecture", "designed", "microservice", "infrastructure", "replication", "sharding", "system design"]
        matches = sum(1 for w in arch_words if w in combined.lower())
        return min(1.0, 0.2 + (matches * 0.15))

    @staticmethod
    def _evaluate_leadership_scale(exp: list[dict[str, Any]]) -> float:
        combined = str(exp).lower()
        lead_words = ["lead", "mentor", "managed", "head", "architected", "roadmap", "hiring"]
        matches = sum(1 for w in lead_words if w in combined)
        return min(1.0, 0.1 + (matches * 0.2))
