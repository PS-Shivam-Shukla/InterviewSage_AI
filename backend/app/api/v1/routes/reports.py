from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user, check_interview_ownership
from app.models import User
from app.schemas import InterviewReportResponse, ReportHistoryItem
from app.services import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/user/history",
    response_model=list[ReportHistoryItem],
    summary="Get user's completed interview report history",
)
async def get_user_report_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch history of completed interview reports for the authenticated candidate, newest first.
    """
    service = ReportService(db)
    return service.get_user_report_history(current_user.id)


@router.get(
    "/{interview_id}",
    response_model=InterviewReportResponse,
    summary="Fetch final report",
)
async def get_report(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interview = check_interview_ownership(interview_id, current_user.id, db)
    if interview.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview is still IN_PROGRESS. Report is only available after completion.",
        )
    service = ReportService(db)
    report = service.get_report(interview_id)
    if not report or report.get("generated_at") is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


@router.get("/{interview_id}/pdf", summary="Download report PDF")
async def get_report_pdf(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interview = check_interview_ownership(interview_id, current_user.id, db)
    if interview.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview is still IN_PROGRESS. Report PDF is only available after completion.",
        )
    service = ReportService(db)
    pdf_bytes = service.get_report_pdf(interview_id)
    if pdf_bytes is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=report_{interview_id}.pdf",
        },
    )


@router.post("/{interview_id}/generate", summary="Generate report for interview")
async def generate_report(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_interview_ownership(interview_id, current_user.id, db)
    service = ReportService(db)
    result = service.generate_report(interview_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result
