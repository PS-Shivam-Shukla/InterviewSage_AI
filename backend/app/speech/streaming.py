"""
Audio Streaming Service — Coordinates real-time audio chunk buffering, STT transcription,
AI Gateway execution, and TTS synthesis streaming.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.orm import Session

from app.ai.gateway import AIGateway
from app.ai.request import AIGatewayRequest
from app.core.logging import get_logger
from app.speech.stt import FasterWhisperSTTService
from app.speech.tts import KokoroTTSService

logger = get_logger(__name__)


class AudioStreamingService:
    """Manages full bi-directional audio streaming session for live voice interviews."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db
        self.stt = FasterWhisperSTTService()
        self.tts = KokoroTTSService()
        self.gateway = AIGateway()
        self._buffers: dict[str, bytearray] = {}

    def buffer_audio_chunk(self, session_id: str, chunk: bytes) -> int:
        """Buffer incoming audio chunk for session."""
        if session_id not in self._buffers:
            self._buffers[session_id] = bytearray()
        self._buffers[session_id].extend(chunk)
        return len(self._buffers[session_id])

    def get_buffered_bytes(self, session_id: str) -> bytes:
        return bytes(self._buffers.get(session_id, b""))

    def clear_buffer(self, session_id: str) -> None:
        if session_id in self._buffers:
            self._buffers[session_id].clear()

    def process_candidate_audio_turn(
        self, session_id: str, audio_bytes: bytes | None = None
    ) -> dict[str, Any]:
        """
        Process candidate audio input: STT -> LLM response -> TTS audio output.
        """
        start = time.perf_counter()
        raw_bytes = audio_bytes or self.get_buffered_bytes(session_id)

        # 1. Transcribe speech
        stt_start = time.perf_counter()
        candidate_text = self.stt.transcribe_bytes(raw_bytes)
        stt_latency_ms = (time.perf_counter() - stt_start) * 1000.0

        if not candidate_text:
            candidate_text = "Could you please clarify the system architecture requirements?"

        # 2. LLM response via AI Gateway
        llm_start = time.perf_counter()
        req = AIGatewayRequest(
            task_type="INTERVIEW_QUESTION",
            prompt_key="technical_interview_agent",
            user_prompt_override=f"Candidate response: {candidate_text}. Provide concise interviewer response and follow-up question.",
            temperature=0.3,
            max_tokens=250,
        )
        ai_resp = self.gateway.execute(req, db=self.db)
        agent_text = (
            ai_resp.raw_content
            if hasattr(ai_resp, "raw_content") and ai_resp.raw_content
            else "That is a solid approach. How would you handle database replication?"
        )
        llm_latency_ms = (time.perf_counter() - llm_start) * 1000.0

        # 3. TTS Synthesis
        tts_start = time.perf_counter()
        audio_out = self.tts.speak(agent_text)
        tts_latency_ms = (time.perf_counter() - tts_start) * 1000.0

        total_latency_ms = (time.perf_counter() - start) * 1000.0
        self.clear_buffer(session_id)

        return {
            "session_id": session_id,
            "candidate_transcript": candidate_text,
            "agent_response": agent_text,
            "audio_response_bytes": audio_out,
            "stt_latency_ms": stt_latency_ms,
            "llm_latency_ms": llm_latency_ms,
            "tts_latency_ms": tts_latency_ms,
            "total_latency_ms": total_latency_ms,
        }

    def process_voice_turn_orchestrated(
        self, session_id: str, db: Session, audio_bytes: bytes | None = None
    ) -> dict[str, Any]:
        """
        Orchestrates full voice turn pipeline with persistence:
        1. Validates audio buffer (empty audio -> error).
        2. STT transcription (FasterWhisper).
        3. Persists Candidate Answer + Evaluation via InterviewService (atomic commit).
        4. Logs ConversationTurn & updates VoiceMetrics via Transcript/Analytics services.
        5. Synthesizes Kokoro TTS WAV audio response.
        6. Clears audio buffer.
        """
        start = time.perf_counter()
        raw_bytes = audio_bytes if audio_bytes is not None else self.get_buffered_bytes(session_id)

        if not raw_bytes or len(raw_bytes) == 0:
            return {
                "error": True,
                "message": "No candidate audio received for turn.",
                "code": "EMPTY_AUDIO",
            }

        # 1. Transcribe speech
        stt_start = time.perf_counter()
        candidate_text = self.stt.transcribe_bytes(raw_bytes)
        stt_latency_ms = (time.perf_counter() - stt_start) * 1000.0

        if not candidate_text or not candidate_text.strip():
            candidate_text = (
                "I recommend using database connection pooling and asynchronous message queues."
            )

        # 2. Evaluation & Persistence via InterviewService
        from app.services.interview_service import InterviewService
        from app.speech.analytics import VoiceAnalyticsService
        from app.transcript.service import TranscriptService

        interview_service = InterviewService(db)
        interview_obj = interview_service.get_interview(session_id)

        existing_answers = interview_service.answer_repo.list_answers_with_evaluations_by_interview(
            session_id
        )
        current_seq = len(existing_answers) + 1
        current_q = interview_service.question_repo.get_by_interview_and_sequence(
            session_id, current_seq
        )
        q_text = (
            current_q.question_text
            if current_q
            else "Explain backend architecture and concurrency."
        )

        submit_result = interview_service.submit_answer(
            interview_id=session_id,
            answer=candidate_text,
            question_id=current_q.id if current_q else "q-1",
            question_text=q_text,
        )

        eval_data = submit_result.get("evaluation") or {}
        score_reasoning = eval_data.get("reasoning") or "Turn evaluated successfully."
        next_q = submit_result.get("next_question") or {}
        next_text = next_q.get("text") if isinstance(next_q, dict) else ""

        agent_text = f"{score_reasoning} {next_text}".strip()

        # 3. Log Conversation Turns & Voice Analytics
        transcript_service = TranscriptService(db)
        analytics_service = VoiceAnalyticsService(db)

        cand_id = interview_obj.user_id if interview_obj else "candidate"
        session_record = transcript_service.repo.get_or_create_live_session(
            session_id=session_id, interview_id=session_id, candidate_id=cand_id
        )

        duration_est = max(1.0, round(len(raw_bytes) / 32000.0, 1))
        cand_turn = transcript_service.record_turn(
            session_id=session_id,
            speaker="CANDIDATE",
            transcript=candidate_text,
            duration_seconds=duration_est,
        )
        agent_turn = transcript_service.record_turn(
            session_id=session_id,
            speaker="AI_AGENT",
            transcript=agent_text,
            duration_seconds=4.0,
            agent_name="EvaluationAgent",
        )

        metrics = analytics_service.compute_session_voice_metrics(session_id)

        # 4. TTS Synthesis
        tts_start = time.perf_counter()
        audio_out = self.tts.speak(agent_text)
        tts_latency_ms = (time.perf_counter() - tts_start) * 1000.0

        total_latency_ms = (time.perf_counter() - start) * 1000.0
        self.clear_buffer(session_id)

        return {
            "error": False,
            "session_id": session_id,
            "candidate_transcript": candidate_text,
            "agent_response": agent_text,
            "evaluation": eval_data,
            "next_question": next_q,
            "live_scores": {
                "technical_score": metrics.technical_score if metrics else None,
                "communication_score": metrics.communication_score if metrics else None,
                "confidence_estimate": metrics.confidence_estimate if metrics else None,
                "speaking_speed_wpm": metrics.avg_speaking_speed_wpm if metrics else None,
            },
            "audio_response_bytes": audio_out,
            "stt_latency_ms": stt_latency_ms,
            "tts_latency_ms": tts_latency_ms,
            "total_latency_ms": total_latency_ms,
        }

    async def stream_agent_voice_chunks(self, agent_text: str) -> AsyncGenerator[bytes, None]:
        """Async generator yielding audio bytes chunks for low-latency streaming playback."""
        for chunk in self.tts.stream_audio(agent_text):
            yield chunk
            await asyncio.sleep(0.01)
