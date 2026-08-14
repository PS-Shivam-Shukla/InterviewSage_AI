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
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.dependencies import check_interview_ownership, get_current_user
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
    1. Emits initial ack event.
    2. Streams agent execution telemetry (EvaluationAgent + QuestionGeneratorAgent).
    3. Streams evaluation feedback.
    4. Streams next question text token-by-token.
    5. Sends a final [DONE] event.
    """
    # Emit an immediate acknowledgement
    yield await _sse_event({"type": "ack", "message": "Answer received, starting agent execution…"})
    await asyncio.sleep(0)   # yield control to allow flush

    try:
        # Stream EvaluationAgent telemetry start
        yield await _sse_event({
            "type": "telemetry",
            "agent": "EvaluationAgent",
            "status": "RUNNING",
            "detail": "Evaluating candidate answer using rubric & role context…",
        })
        await asyncio.sleep(0)

        from fastapi import HTTPException

        from app.services.interview_service import InterviewService

        svc = InterviewService(db)
        result = svc.submit_answer(interview_id, answer_text)

        if isinstance(result, dict) and result.get("error"):
            yield await _sse_event({"type": "error", "message": result["error"]})
            return

        next_question = result.get("next_question", "")
        evaluation    = result.get("evaluation", {})

        # Stream EvaluationAgent completion telemetry
        yield await _sse_event({
            "type": "telemetry",
            "agent": "EvaluationAgent",
            "status": "COMPLETED",
            "detail": f"Evaluation complete. Score: {evaluation.get('display_score', 'N/A')}",
        })
        await asyncio.sleep(0)

        # Stream evaluation feedback
        if evaluation:
            yield await _sse_event({"type": "evaluation", "data": evaluation})
            await asyncio.sleep(0)

        # Stream QuestionGeneratorAgent telemetry
        if next_question:
            yield await _sse_event({
                "type": "telemetry",
                "agent": "QuestionGeneratorAgent",
                "status": "COMPLETED",
                "detail": f"Generated next question ({result.get('round_type', 'TECHNICAL')})",
            })
            await asyncio.sleep(0)

            # Stream next question word-by-word
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
        from fastapi import HTTPException
        err_msg = exc.detail if isinstance(exc, HTTPException) else str(exc)
        logger.error(f"SSE stream error for interview {interview_id}: {err_msg}")
        yield await _sse_event({"type": "error", "message": err_msg})


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
