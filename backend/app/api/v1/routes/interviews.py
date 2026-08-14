from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import check_interview_ownership, get_current_user
from app.models import User
from app.schemas import (
    BlueprintApprovalRequest,
    BlueprintApprovalResponse,
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewCreateRequest,
    InterviewPlanResponse,
    InterviewStatusResponse,
)
from app.services import InterviewService

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.post(
    "/",
    response_model=InterviewStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new interview",
)
async def create_interview(
    request: InterviewCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InterviewService(db)
    payload = request.model_dump()
    interview = service.create_interview(
        current_user.id,
        request.resume_id or "",
        request.jd_id or "",
        payload=payload,
    )
    if not interview:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create interview")

    # If new interview created in PLANNING status, trigger background LLM plan generation
    if interview.status == "PLANNING":
        background_tasks.add_task(service.generate_plan_background, interview.id, payload)

    return interview


@router.get(
    "/{interview_id}",
    response_model=InterviewStatusResponse,
    summary="Get interview status",
)
async def get_interview(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interview = check_interview_ownership(interview_id, current_user.id, db)
    return interview


@router.get(
    "/{interview_id}/plan",
    response_model=InterviewPlanResponse,
    summary="Get interview plan",
)
async def get_interview_plan(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_interview_ownership(interview_id, current_user.id, db)
    service = InterviewService(db)
    plan = service.get_interview_plan(interview_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


@router.post(
    "/{interview_id}/approve-blueprint",
    response_model=BlueprintApprovalResponse,
    summary="Approve or override interview blueprint",
)
async def approve_blueprint(
    interview_id: str,
    request: BlueprintApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_interview_ownership(interview_id, current_user.id, db)
    service = InterviewService(db)
    result = service.approve_blueprint(interview_id, overrides=request.overrides)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result


@router.post(
    "/{interview_id}/answers",
    response_model=InterviewAnswerResponse,
    summary="Submit answer for a question",
)
async def submit_answer(
    interview_id: str,
    request: InterviewAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_interview_ownership(interview_id, current_user.id, db)
    service = InterviewService(db)
    result = service.submit_answer(
        interview_id,
        request.answer,
        question_id=request.question_id or "q-1",
        question_text=request.question_text or "",
    )
    return result


@router.post(
    "/{interview_id}/pause",
    response_model=InterviewStatusResponse,
    summary="Pause interview",
)
async def pause_interview(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_interview_ownership(interview_id, current_user.id, db)
    service = InterviewService(db)
    interview = service.pause_interview(interview_id)
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    return interview


@router.post(
    "/{interview_id}/resume",
    response_model=InterviewStatusResponse,
    summary="Resume interview",
)
async def resume_interview(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_interview_ownership(interview_id, current_user.id, db)
    service = InterviewService(db)
    interview = service.resume_interview(interview_id)
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    return interview


@router.post(
    "/{interview_id}/complete",
    response_model=InterviewStatusResponse,
    summary="Explicitly complete interview",
)
async def complete_interview(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_interview_ownership(interview_id, current_user.id, db)
    service = InterviewService(db)
    interview = service.complete_interview(interview_id)
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    return interview
