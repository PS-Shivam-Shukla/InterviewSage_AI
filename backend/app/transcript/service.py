"""
Transcript Service — Higher-level business logic for recording turns, formatting transcript text,
and generating downloads.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.transcript.repository import TranscriptRepository
from app.transcript.schemas import (
    ConversationTurnResponse,
    TranscriptExportResponse,
)


class TranscriptService:
    """Service managing conversation turns, transcript exports, and downloads."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TranscriptRepository(db)

    def record_turn(
        self,
        session_id: str,
        speaker: str,
        transcript: str,
        duration_seconds: float = 0.0,
        tokens_used: int = 0,
        agent_name: str = "TechnicalInterviewAgent",
    ) -> ConversationTurnResponse:
        turn = self.repo.add_turn(
            session_id=session_id,
            speaker=speaker,
            transcript=transcript,
            duration_seconds=duration_seconds,
            tokens_used=tokens_used,
            agent_name=agent_name,
        )
        return ConversationTurnResponse(
            id=turn.id,
            session_id=turn.session_id,
            turn_number=turn.turn_number,
            speaker=turn.speaker,
            transcript=turn.transcript,
            duration_seconds=turn.duration_seconds,
            tokens_used=turn.tokens_used,
            agent_name=turn.agent_name,
            created_at=turn.created_at.isoformat(),
        )

    def compile_full_transcript(
        self, session_id: str, interview_id: str
    ) -> TranscriptExportResponse:
        turns = self.repo.list_turns(session_id)
        lines = []
        for t in turns:
            prefix = (
                f"[{t.speaker}] ({t.agent_name})" if t.speaker == "AI_AGENT" else f"[{t.speaker}]"
            )
            lines.append(f"{prefix}: {t.transcript}")

        full_text = "\n".join(lines) if lines else "No conversation turns recorded for session."
        export = self.repo.save_transcript_export(
            interview_id=interview_id,
            session_id=session_id,
            full_text=full_text,
            turn_count=len(turns),
        )

        return TranscriptExportResponse(
            id=export.id,
            interview_id=export.interview_id,
            session_id=export.session_id,
            full_text=export.full_text,
            turn_count=export.turn_count,
            file_path=export.file_path,
            created_at=export.created_at.isoformat(),
        )

    def get_transcript_for_download(self, identifier: str) -> dict[str, Any]:
        """
        Get transcript by interview_id or session_id for file download.
        """
        export = self.repo.get_transcript_by_interview(identifier)
        if not export:
            # Reconstruct from turns
            turns = self.repo.list_turns(identifier)
            lines = [f"[{t.speaker}]: {t.transcript}" for t in turns]
            full_text = (
                "\n".join(lines) if lines else f"Interview Transcript Log for {identifier}\n---\n"
            )
            return {
                "interview_id": identifier,
                "full_text": full_text,
                "turn_count": len(turns),
                "filename": f"transcript_{identifier[:8]}.txt",
            }

        return {
            "interview_id": export.interview_id,
            "full_text": export.full_text,
            "turn_count": export.turn_count,
            "filename": f"transcript_{export.interview_id[:8]}.txt",
        }
