"""
Career Intelligence Service — Unified orchestrator for adaptive engine, hiring predictions,
benchmarks, company profiles, skill gap analysis, roadmaps, replay annotations, and recruiter insights.
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.career.adaptive import AdaptiveDifficultyEngine
from app.career.benchmark import IndustryBenchmarkEngine
from app.career.company import CompanyProfileEngine
from app.career.insights import RecruiterInsightsEngine
from app.career.knowledge_graph import KnowledgeGraphEngine
from app.career.prediction import HiringPredictionEngine
from app.career.replay import InterviewReplayEngine
from app.career.roadmap import CareerRoadmapGenerator
from app.career.schemas import (
    AdaptiveNextQuestionRequest,
    AdaptiveNextQuestionResponse,
    AdaptiveStartRequest,
    AdaptiveStartResponse,
    CareerRoadmapResponse,
    CompanyProfileResponse,
    HiringPredictionResponse,
    IndustryBenchmarkResponse,
    InterviewReplayResponse,
    RecruiterInsightsResponse,
    SkillGapResponse,
)
from app.career.skill_gap import SkillGapAnalyzer


class CareerIntelligenceService:
    """Core Manager coordinating all AI Career Intelligence Platform engines."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.adaptive = AdaptiveDifficultyEngine(db)
        self.prediction = HiringPredictionEngine(db)
        self.benchmark = IndustryBenchmarkEngine(db)
        self.company = CompanyProfileEngine(db)
        self.skill_gap = SkillGapAnalyzer(db)
        self.roadmap = CareerRoadmapGenerator(db)
        self.replay = InterviewReplayEngine(db)
        self.insights = RecruiterInsightsEngine(db)
        self.graph = KnowledgeGraphEngine(db)

    def get_hiring_prediction(self, candidate_id: str) -> HiringPredictionResponse:
        pred = self.prediction.predict_hiring_outcome(candidate_id)
        reasons = json.loads(pred.key_reasons) if pred.key_reasons else []
        return HiringPredictionResponse(
            candidate_id=pred.candidate_id,
            hire_probability=pred.hire_probability,
            confidence_score=pred.confidence_score,
            outcome=pred.outcome,
            key_reasons=reasons,
            strengths=[r for r in reasons if "strong" in r.lower() or "proven" in r.lower()],
            drawbacks=[r for r in reasons if "gap" in r.lower() or "latency" in r.lower() or "low" in r.lower()],
        )

    def get_benchmark(self, candidate_id: str) -> IndustryBenchmarkResponse:
        return self.benchmark.get_candidate_benchmark(candidate_id)

    def get_company(self, company_name: str) -> CompanyProfileResponse:
        return self.company.get_company_profile(company_name)

    def start_adaptive_session(self, payload: AdaptiveStartRequest) -> AdaptiveStartResponse:
        sess = self.adaptive.start_session(
            interview_id=payload.interview_id,
            candidate_id=payload.candidate_id,
            initial_difficulty=payload.initial_difficulty,
        )
        return AdaptiveStartResponse(
            session_id=sess.id,
            interview_id=sess.interview_id,
            candidate_id=sess.candidate_id,
            current_difficulty=sess.current_difficulty,
            status=sess.status,
        )

    def get_adaptive_next_question(self, payload: AdaptiveNextQuestionRequest) -> AdaptiveNextQuestionResponse:
        res = self.adaptive.process_answer_and_adjust(
            session_id=payload.session_id,
            performance_score=payload.performance_score,
            response_latency_seconds=payload.response_latency_seconds,
        )
        return AdaptiveNextQuestionResponse(
            session_id=res["session_id"],
            previous_difficulty=res["previous_difficulty"],
            new_difficulty=res["new_difficulty"],
            adjustment_reason=res["adjustment_reason"],
            suggested_focus=res["suggested_focus"],
        )

    def get_skill_gap(self, candidate_id: str) -> SkillGapResponse:
        return self.skill_gap.analyze_skill_gaps(candidate_id)

    def get_roadmap(self, candidate_id: str) -> CareerRoadmapResponse:
        return self.roadmap.generate_career_roadmap(candidate_id)

    def get_replay(self, interview_id: str) -> InterviewReplayResponse:
        return self.replay.get_interview_replay(interview_id)

    def get_recruiter_insights(self, interview_id: str) -> RecruiterInsightsResponse:
        return self.insights.get_recruiter_insights(interview_id)
