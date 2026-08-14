"""
Career Roadmap Generator.
Generates structured daily, weekly, and monthly action plans for candidate skill development.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.career.schemas import CareerRoadmapResponse


class CareerRoadmapGenerator:
    """Generates multi-tiered daily, weekly, and monthly action plans."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_career_roadmap(self, candidate_id: str) -> CareerRoadmapResponse:
        daily_plan = [
            {
                "day": 1,
                "task": "Review Redis Persistence (RDB vs AOF)",
                "type": "ARTICLE",
                "duration_mins": 30,
            },
            {
                "day": 2,
                "task": "Implement Rate Limiter with Token Bucket",
                "type": "PRACTICE_CODE",
                "duration_mins": 60,
            },
            {
                "day": 3,
                "task": "Read PostgreSQL EXPLAIN ANALYZE docs",
                "type": "DOCUMENTATION",
                "duration_mins": 45,
            },
            {
                "day": 4,
                "task": "Mock Voice Interview on System Design",
                "type": "MOCK_INTERVIEW",
                "duration_mins": 45,
            },
            {
                "day": 5,
                "task": "Solve 2 Medium LeetCode Dynamic Programming problems",
                "type": "PRACTICE_CODE",
                "duration_mins": 60,
            },
        ]

        weekly_plan = [
            {
                "week": 1,
                "focus": "Database & Caching Architecture",
                "deliverable": "Build Redis + Postgres caching layer",
            },
            {
                "week": 2,
                "focus": "Distributed Systems & Messaging",
                "deliverable": "Set up Kafka cluster with partition keying",
            },
            {
                "week": 3,
                "focus": "High Availability & Fault Tolerance",
                "deliverable": "Configure PgBouncer & failover simulation",
            },
            {
                "week": 4,
                "focus": "Full Mock Technical Interview",
                "deliverable": "Complete 60-min simulated Staff Interview",
            },
        ]

        monthly_plan = [
            {"month": 1, "milestone": "Master Distributed Systems Core Principles"},
            {"month": 2, "milestone": "Achieve Top 10% System Design Benchmark Score"},
            {"month": 3, "milestone": "Complete Target Company Interview Prep (Amazon/Google)"},
        ]

        return CareerRoadmapResponse(
            candidate_id=candidate_id,
            daily_plan=daily_plan,
            weekly_plan=weekly_plan,
            monthly_plan=monthly_plan,
        )
