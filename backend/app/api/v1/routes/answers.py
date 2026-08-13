"""
Answer submission endpoint with Server-Sent Events (SSE) streaming.
POST /interviews/{interview_id}/answers
  - Submits the candidate's answer
  - Resumes the LangGraph interrupt
  - Streams the next interviewer turn token-by-token via SSE
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.dependencies import get_current_user, check_interview_ownership
from app.models import User

logger = get_logger(__name__)
router = APIRouter(prefix="/interviews", tags=["Interview Turns"])


class AnswerRequest(BaseModel):
    answer_text: str


async def _sse_event(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


async def _stream_turn(
    interview_id: str,
    answer_text: str,
    db: Session,
) -> AsyncGenerator[str, None]:
    """
    Core streaming generator:
    1. Persists the answer to state.
    2. Invokes the graph continuation (evaluation + next question generation).
    3. Streams the next question text token-by-token.
    4. Sends a final [DONE] event.
    """
    # Emit an immediate acknowledgement
    yield await _sse_event({"type": "ack", "message": "Answer received, processing…"})
    await asyncio.sleep(0)   # yield control to allow flush

    try:
        from app.services.interview_service import InterviewService
        svc = InterviewService(db)
        result = svc.submit_answer(interview_id, answer_text)

        if isinstance(result, dict) and result.get("error"):
            yield await _sse_event({"type": "error", "message": result["error"]})
            return

        next_question = result.get("next_question", "")
        evaluation    = result.get("evaluation", {})

        # Stream evaluation feedback first
        if evaluation:
            yield await _sse_event({"type": "evaluation", "data": evaluation})
            await asyncio.sleep(0)

        # Stream next question word-by-word
        if next_question:
            words = next_question.split()
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield await _sse_event({"type": "token", "content": chunk})
                await asyncio.sleep(0.03)   # ~33 tokens/sec simulated pacing

        # Done event
        yield await _sse_event({
            "type": "done",
            "interview_complete": result.get("interview_complete", False),
        })

    except Exception as exc:
        logger.error(f"SSE stream error for interview {interview_id}: {exc}")
        yield await _sse_event({"type": "error", "message": "Internal server error"})


@router.post(
    "/{interview_id}/answers",
    summary="Submit answer — streams next interviewer turn via SSE",
    response_class=StreamingResponse,
)
async def submit_answer(
    interview_id: str,
    request: AnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_interview_ownership(interview_id, current_user.id, db)
    return StreamingResponse(
        _stream_turn(interview_id, request.answer_text, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
