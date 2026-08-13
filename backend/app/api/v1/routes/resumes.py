from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from fastapi.concurrency import run_in_threadpool

from app.core.database import get_db
from app.dependencies import get_current_user, check_resume_ownership
from app.models import User
from app.schemas.resume import ResumeResponse, ResumeAnalysisResponse
from app.services import ResumeService
from app.utils.upload_validator import validate_upload_file

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post(
    "/",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload resume",
)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    clean_filename = validate_upload_file(file, content)
    service = ResumeService(db)
    resume, raw_text = await run_in_threadpool(service.upload_resume_fast, current_user.id, clean_filename, content)
    background_tasks.add_task(service.process_resume_background, resume["id"], raw_text, clean_filename)
    return resume


@router.get(
    "/",
    response_model=List[ResumeResponse],
    summary="List all user resumes",
)
async def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResumeService(db)
    return service.list_resumes(current_user.id)


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Fetch parsed resume",
)
async def get_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_resume_ownership(resume_id, current_user.id, db)
    service = ResumeService(db)
    resume = service.get_resume(resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete resume",
)
async def delete_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_resume_ownership(resume_id, current_user.id, db)
    service = ResumeService(db)
    success = service.delete_resume(resume_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return None


@router.put(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Replace resume",
)
async def replace_resume(
    resume_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_resume_ownership(resume_id, current_user.id, db)
    content = await file.read()
    clean_filename = validate_upload_file(file, content)
    service = ResumeService(db)
    updated = await run_in_threadpool(service.replace_resume, resume_id, clean_filename, content)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return updated


@router.get(
    "/{resume_id}/analysis",
    response_model=ResumeAnalysisResponse,
    summary="Get resume AI analysis",
)
async def get_resume_analysis(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_resume_ownership(resume_id, current_user.id, db)
    service = ResumeService(db)
    analysis = service.get_resume_analysis(resume_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume analysis not found")
    return analysis
