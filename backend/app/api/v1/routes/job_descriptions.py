from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user, check_job_description_ownership, check_resume_ownership
from app.models import User
from app.schemas import JobDescriptionCreateRequest, JobDescriptionResponse, JobDescriptionMatchResponse
from app.services import JobDescriptionService

router = APIRouter(prefix="/job-descriptions", tags=["Job Descriptions"])


@router.post(
    "/",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit and parse job description",
)
async def create_job_description(
    request: JobDescriptionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = JobDescriptionService(db)
    payload = {
        "jd_text": request.raw_text,
        "target_role": request.target_role,
        "company_name": request.company_name,
        "industry": request.industry,
        "user_id": current_user.id,
    }
    jd = await run_in_threadpool(service.create_job_description, payload)
    return jd


@router.get(
    "/",
    response_model=List[JobDescriptionResponse],
    summary="List all user job descriptions",
)
async def list_job_descriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = JobDescriptionService(db)
    return service.list_job_descriptions(current_user.id)


@router.get(
    "/{jd_id}",
    response_model=JobDescriptionResponse,
    summary="Fetch parsed job description",
)
async def get_job_description(
    jd_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_job_description_ownership(jd_id, current_user.id, db)
    service = JobDescriptionService(db)
    jd = service.get_job_description(jd_id)
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")
    return jd


@router.post(
    "/{jd_id}/match/{resume_id}",
    response_model=JobDescriptionMatchResponse,
    summary="Compute ATS match score between Resume and Job Description",
)
async def match_resume_with_jd(
    jd_id: str,
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_job_description_ownership(jd_id, current_user.id, db)
    check_resume_ownership(resume_id, current_user.id, db)
    service = JobDescriptionService(db)
    match_result = service.match_resume_with_jd(jd_id, resume_id)
    return match_result
