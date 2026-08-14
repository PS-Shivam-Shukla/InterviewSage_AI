"""
Industry Benchmark Engine.
Compares candidate scores against industry standards across key categories (Coding, System Design, SQL, AI, Communication, Leadership).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.career.schemas import BenchmarkCategoryDetail, IndustryBenchmarkResponse
from app.models.candidate_memory import SkillProgress


class IndustryBenchmarkEngine:
    """Computes industry benchmarks and candidate percentiles."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_candidate_benchmark(self, candidate_id: str) -> IndustryBenchmarkResponse:
        skills = self.db.query(SkillProgress).filter(SkillProgress.candidate_id == candidate_id).all()
        skill_map = {s.skill_name.lower(): s.current_score for s in skills}

        categories_def = [
            ("Coding & Algorithms", "coding", 68.0, 92.0),
            ("System Design & Architecture", "system design", 65.0, 90.0),
            ("SQL & Data Modeling", "sql", 70.0, 94.0),
            ("AI & Machine Learning", "ai", 62.0, 88.0),
            ("Communication & Clarity", "communication", 72.0, 95.0),
            ("Leadership & Behavioral", "leadership", 70.0, 93.0),
        ]

        details = []
        tot_percentile = 0.0

        for cat_name, key, avg_s, top_s in categories_def:
            score = skill_map.get(key, skill_map.get(cat_name.lower(), 78.0))
            percentile = min(99.0, max(5.0, ((score - 40.0) / 55.0) * 95.0))
            tot_percentile += percentile
            details.append(
                BenchmarkCategoryDetail(
                    category=cat_name,
                    candidate_score=round(score, 1),
                    industry_average=avg_s,
                    top_10_percentile=top_s,
                    percentile=round(percentile, 1),
                )
            )

        overall_pct = tot_percentile / len(categories_def)

        return IndustryBenchmarkResponse(
            candidate_id=candidate_id,
            overall_percentile=round(overall_pct, 1),
            categories=details,
        )
