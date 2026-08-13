"""
AI Career Intelligence API Router.
Exposes endpoints for hiring prediction, benchmark percentiles, company interview profiles,
adaptive difficulty engine, skill gap analysis, roadmaps, interview replay annotations, and recruiter insights.
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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
from app.career.service import CareerIntelligenceService
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import User

router = APIRouter(prefix="/career", tags=["AI Career Intelligence"])


@router.get("/hiring-prediction/{candidate_id}", response_model=HiringPredictionResponse, summary="Predict candidate hire probability")
async def get_hiring_prediction(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CareerIntelligenceService(db)
    return service.get_hiring_prediction(candidate_id)


@router.get("/benchmark/{candidate_id}", response_model=IndustryBenchmarkResponse, summary="Compare candidate with industry benchmarks")
async def get_benchmark(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CareerIntelligenceService(db)
    return service.get_benchmark(candidate_id)


@router.get("/company/{company}", response_model=CompanyProfileResponse, summary="Retrieve company interview profile & weightings")
async def get_company_profile(
    company: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CareerIntelligenceService(db)
    return service.get_company(company)


@router.post("/adaptive/start", response_model=AdaptiveStartResponse, summary="Start adaptive difficulty interview session")
async def start_adaptive_session(
    payload: AdaptiveStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CareerIntelligenceService(db)
    return service.start_adaptive_session(payload)


@router.post("/adaptive/next-question", response_model=AdaptiveNextQuestionResponse, summary="Calculate next adaptive question difficulty")
async def get_adaptive_next_question(
    payload: AdaptiveNextQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CareerIntelligenceService(db)
    return service.get_adaptive_next_question(payload)


@router.get("/roadmap/{candidate_id}", response_model=CareerRoadmapResponse, summary="Retrieve candidate learning roadmap")
async def get_career_roadmap(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CareerIntelligenceService(db)
    return service.get_roadmap(candidate_id)


@router.get("/replay/{interview_id}", response_model=InterviewReplayResponse, summary="Retrieve interview replay AI annotations")
async def get_interview_replay(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CareerIntelligenceService(db)
    return service.get_replay(interview_id)


@router.get("/skill-gap/{candidate_id}", response_model=SkillGapResponse, summary="Analyze candidate missing skill concepts")
async def get_skill_gap(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CareerIntelligenceService(db)
    return service.get_skill_gap(candidate_id)


@router.get("/recruiter-insights/{interview_id}", response_model=RecruiterInsightsResponse, summary="Retrieve recruiter decision insights")
async def get_recruiter_insights(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CareerIntelligenceService(db)
    return service.get_recruiter_insights(interview_id)
