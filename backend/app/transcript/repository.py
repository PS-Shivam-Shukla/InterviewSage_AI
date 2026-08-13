"""
Transcript Repository — SQL CRUD layer for live sessions, conversation turns, voice metrics, and transcripts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.voice import (
    ConversationTurn,
    LiveSession,
    SpeechEvent,
    TranscriptExport,
    VoiceMetrics,
)


class TranscriptRepository:
    """Repository managing SQL operations for voice session transcripts and metrics."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_live_session(self, session_id: str, interview_id: str, candidate_id: str) -> LiveSession:
        session = self.db.query(LiveSession).filter(LiveSession.id == session_id).first()
        if not session:
            session = LiveSession(
                id=session_id,
                interview_id=interview_id,
                candidate_id=candidate_id,
                status="ACTIVE",
                active_worker_id="worker-01",
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
        return session

    def get_live_session(self, session_id: str) -> Optional[LiveSession]:
        return self.db.query(LiveSession).filter(LiveSession.id == session_id).first()

    def list_active_sessions(self) -> List[LiveSession]:
        return (
            self.db.query(LiveSession)
            .filter(LiveSession.status.in_(["ACTIVE", "IN_PROGRESS"]))
            .order_by(LiveSession.started_at.desc())
            .all()
        )

    def add_turn(
        self,
        session_id: str,
        speaker: str,
        transcript: str,
        duration_seconds: float = 0.0,
        tokens_used: int = 0,
        agent_name: str = "TechnicalInterviewAgent",
    ) -> ConversationTurn:
        existing_turns = (
            self.db.query(ConversationTurn)
            .filter(ConversationTurn.session_id == session_id)
            .all()
        )
        turn_num = len(existing_turns) + 1

        turn = ConversationTurn(
            session_id=session_id,
            turn_number=turn_num,
            speaker=speaker,
            transcript=transcript,
            duration_seconds=duration_seconds,
            tokens_used=tokens_used,
            agent_name=agent_name,
        )
        self.db.add(turn)
        self.db.commit()
        self.db.refresh(turn)
        return turn

    def list_turns(self, session_id: str) -> List[ConversationTurn]:
        return (
            self.db.query(ConversationTurn)
            .filter(ConversationTurn.session_id == session_id)
            .order_by(ConversationTurn.turn_number.asc())
            .all()
        )

    def record_speech_event(
        self, session_id: str, event_type: str, payload_summary: str = "", latency_ms: float = 0.0
    ) -> SpeechEvent:
        evt = SpeechEvent(
            session_id=session_id,
            event_type=event_type,
            payload_summary=payload_summary,
            latency_ms=latency_ms,
        )
        self.db.add(evt)
        self.db.commit()
        self.db.refresh(evt)
        return evt

    def save_transcript_export(
        self, interview_id: str, session_id: str, full_text: str, turn_count: int
    ) -> TranscriptExport:
        export = (
            self.db.query(TranscriptExport)
            .filter(TranscriptExport.session_id == session_id)
            .first()
        )
        if not export:
            export = TranscriptExport(
                interview_id=interview_id,
                session_id=session_id,
                full_text=full_text,
                turn_count=turn_count,
                file_path=f"/transcripts/{interview_id}_{session_id[:8]}.txt",
            )
            self.db.add(export)
        else:
            export.full_text = full_text
            export.turn_count = turn_count

        self.db.commit()
        self.db.refresh(export)
        return export

    def get_transcript_by_interview(self, interview_id: str) -> Optional[TranscriptExport]:
        return (
            self.db.query(TranscriptExport)
            .filter(TranscriptExport.interview_id == interview_id)
            .order_by(TranscriptExport.created_at.desc())
            .first()
        )

    def get_voice_metrics(self, session_id: str) -> Optional[VoiceMetrics]:
        return (
            self.db.query(VoiceMetrics)
            .filter(VoiceMetrics.session_id == session_id)
            .first()
        )
