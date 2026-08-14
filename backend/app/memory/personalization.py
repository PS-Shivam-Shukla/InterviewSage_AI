"""
Personalization Engine — Tracks skill progress, computes trends, recommends personalized questions,
and generates multi-week learning roadmaps based on longitudinal memory.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.memory.repository import MemoryRepository
from app.memory.schemas import (
    LearningRecommendationResponse,
    PersonalizedQuestionRecommendation,
    SkillProgressResponse,
)


class PersonalizationEngine:
    """Engine providing personalized interview planning and learning roadmap recommendations."""

    def __init__(self, db: Session) -> None:
        self.repo = MemoryRepository(db)

    def record_interview_skills_eval(
        self, candidate_id: str, skill_evaluations: dict[str, float]
    ) -> list[SkillProgressResponse]:
        """
        Record evaluation scores for candidate skills and compute longitudinal progression & trends.
        """
        updated_skills = []
        for skill_name, score in skill_evaluations.items():
            sp = self.repo.upsert_skill_progress(candidate_id, skill_name, score)
            updated_skills.append(
                SkillProgressResponse(
                    id=sp.id,
                    candidate_id=sp.candidate_id,
                    skill_name=sp.skill_name,
                    current_score=sp.current_score,
                    best_score=sp.best_score,
                    average_score=sp.average_score,
                    trend=sp.trend,
                    total_evaluations=sp.total_evaluations,
                    updated_at=sp.updated_at.isoformat(),
                )
            )

        # Sync strengths and weaknesses into profile
        all_skills = self.repo.list_skill_progress(candidate_id)
        strengths = [s.skill_name for s in all_skills if s.current_score >= 75.0]
        weaknesses = [s.skill_name for s in all_skills if s.current_score < 65.0]
        self.repo.update_profile(candidate_id, strengths=strengths, weaknesses=weaknesses)

        return updated_skills

    def get_personalized_question_recommendation(
        self, candidate_id: str
    ) -> PersonalizedQuestionRecommendation:
        """
        Recommend target skill, difficulty, and focus area for next interview based on candidate weaknesses.
        """
        skills = self.repo.list_skill_progress(candidate_id)
        weakest = min(skills, key=lambda s: s.current_score) if skills else None

        if not weakest:
            return PersonalizedQuestionRecommendation(
                target_skill="General System Architecture",
                recommended_difficulty="MEDIUM",
                suggested_focus="Assess foundational software design and problem solving.",
                reasoning="First interview session for candidate - start with baseline assessment.",
            )

        diff = "HARD" if weakest.current_score > 70.0 else ("MEDIUM" if weakest.current_score > 50.0 else "EASY")
        return PersonalizedQuestionRecommendation(
            target_skill=weakest.skill_name,
            recommended_difficulty=diff,
            suggested_focus=f"Deep dive into {weakest.skill_name} concepts, addressing previous score of {weakest.current_score}.",
            reasoning=f"Candidate has trend '{weakest.trend}' in {weakest.skill_name}. Personalizing question to target growth area.",
        )

    def generate_learning_roadmap(
        self, candidate_id: str, interview_id: str | None = None
    ) -> list[LearningRecommendationResponse]:
        """
        Generate a 4-week personalized learning roadmap for candidate based on skill progress.
        """
        skills = self.repo.list_skill_progress(candidate_id)
        weak_skills = sorted(skills, key=lambda s: s.current_score)

        default_topics = [
            ("Docker & Containerization", "HIGH", "Practice building multi-stage Dockerfiles and container networks.", 1),
            ("Database Query Optimization", "HIGH", "Study PostgreSQL indexing, execution plans, and JOIN tuning.", 2),
            ("Concurrency & Async Python", "MEDIUM", "Implement async worker loops using asyncio and task pools.", 3),
            ("Distributed System Design", "MEDIUM", "Design resilient API rate limiters and circuit breaker patterns.", 4),
        ]

        created_recs = []

        if weak_skills:
            for idx, skill in enumerate(weak_skills[:4], 1):
                prio = "HIGH" if skill.current_score < 60.0 else "MEDIUM"
                rec = self.repo.create_recommendation(
                    candidate_id=candidate_id,
                    interview_id=interview_id,
                    target_topic=skill.skill_name,
                    priority=prio,
                    suggested_action=f"Focus intensive practice on {skill.skill_name} (Current Score: {skill.current_score}).",
                    week_number=idx,
                )
                created_recs.append(rec)
        else:
            for topic, prio, action, week in default_topics:
                rec = self.repo.create_recommendation(
                    candidate_id=candidate_id,
                    interview_id=interview_id,
                    target_topic=topic,
                    priority=prio,
                    suggested_action=action,
                    week_number=week,
                )
                created_recs.append(rec)

        return [
            LearningRecommendationResponse(
                id=r.id,
                candidate_id=r.candidate_id,
                interview_id=r.interview_id,
                target_topic=r.target_topic,
                priority=r.priority,
                suggested_action=r.suggested_action,
                week_number=r.week_number,
                created_at=r.created_at.isoformat(),
            )
            for r in created_recs
        ]
