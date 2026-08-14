"""
Transcripts API Router.
Exposes endpoints for fetching and downloading interview transcripts.
"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.transcript.service import TranscriptService

router = APIRouter(prefix="/transcripts", tags=["Transcripts"])


@router.get("/{interview_id}", summary="Retrieve transcript by interview ID")
async def get_transcript_by_id(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TranscriptService(db)
    export = service.repo.get_transcript_by_interview(interview_id)
    if not export:
        # Reconstruct transcript
        res = service.get_transcript_for_download(interview_id)
        return {
            "interview_id": interview_id,
            "full_text": res["full_text"],
            "turn_count": res["turn_count"],
        }
    return {
        "id": export.id,
        "interview_id": export.interview_id,
        "session_id": export.session_id,
        "full_text": export.full_text,
        "turn_count": export.turn_count,
        "created_at": export.created_at.isoformat(),
    }


@router.get("/{interview_id}/download", summary="Download transcript text file")
async def download_transcript(
    interview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TranscriptService(db)
    res = service.get_transcript_for_download(interview_id)
    headers = {"Content-Disposition": f"attachment; filename={res['filename']}"}
    return Response(content=res["full_text"], media_type="text/plain", headers=headers)
