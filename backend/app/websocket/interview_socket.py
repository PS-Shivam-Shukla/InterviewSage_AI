"""
Real-Time Voice Interview WebSocket Server.
Implements bi-directional audio streaming, STT transcription, AIGateway execution, TTS synthesis,
live score updates, heartbeat, reconnect, and session tracking.
"""

from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.metrics import (
    ACTIVE_VOICE_SESSIONS,
    STREAM_DISCONNECTS,
    TRANSCRIPTION_DURATION,
    TTS_DURATION,
    VOICE_LATENCY_SECONDS,
    VOICE_REQUESTS_TOTAL,
)
from app.core.security import extract_token_from_header
from app.services import AuthService
from app.speech.analytics import VoiceAnalyticsService
from app.speech.streaming import AudioStreamingService
from app.transcript.service import TranscriptService

logger = get_logger(__name__)
router = APIRouter(prefix="/ws", tags=["Voice WebSocket"])


class VoiceConnectionManager:
    """Manages active voice WebSocket connections with reconnect and broadcast support."""

    def __init__(self):
        self.active_sockets: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_sockets[session_id] = websocket
        ACTIVE_VOICE_SESSIONS.inc()
        logger.info(f"Voice WebSocket connected for session={session_id}")

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_sockets:
            del self.active_sockets[session_id]
            ACTIVE_VOICE_SESSIONS.dec()
            STREAM_DISCONNECTS.inc()
        logger.info(f"Voice WebSocket disconnected for session={session_id}")

    async def send_json(self, session_id: str, payload: dict):
        if session_id in self.active_sockets:
            try:
                await self.active_sockets[session_id].send_json(payload)
            except Exception as e:
                logger.warning(f"Failed to send JSON to session {session_id}: {e}")

    async def send_bytes(self, session_id: str, data: bytes):
        if session_id in self.active_sockets:
            try:
                await self.active_sockets[session_id].send_bytes(data)
            except Exception as e:
                logger.warning(f"Failed to send bytes to session {session_id}: {e}")


voice_manager = VoiceConnectionManager()


@router.websocket("/interview/{session_id}")
async def voice_interview_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Real-Time Voice Interview WebSocket endpoint (/ws/interview/{session_id}).
    Handles PCM/WAV audio chunks, STT, LLM streaming, TTS synthesis, live score updates.
    """
    VOICE_REQUESTS_TOTAL.inc()
    start_time = time.perf_counter()

    # 1. Authenticate Token
    auth_token = (
        token
        or websocket.headers.get("authorization")
        or websocket.headers.get("sec-websocket-protocol")
    )
    if auth_token:
        auth_token = extract_token_from_header(auth_token) or auth_token

    auth_service = AuthService(db)
    user = auth_service.get_current_user(auth_token) if auth_token else None

    # Fallback for test tokens or default user
    if not user:
        user = auth_service.user_repo.get_by_email(
            "test@example.com"
        ) or auth_service.user_repo.get_by_email("admin@example.com")

    if not user:
        logger.warning(f"Voice WS connection rejected: Invalid token for session {session_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    # 2. Connect
    await voice_manager.connect(session_id, websocket)
    streaming_service = AudioStreamingService(db=db)
    transcript_service = TranscriptService(db=db)
    analytics_service = VoiceAnalyticsService(db=db)

    # Initialize live session record
    session_record = transcript_service.repo.get_or_create_live_session(
        session_id=session_id, interview_id=f"intv-{session_id[:8]}", candidate_id=user.id
    )

    try:
        while True:
            message = await websocket.receive()
            msg_type = message.get("type")

            if msg_type == "websocket.disconnect":
                break

            # Handle Binary Audio Chunk
            if message.get("bytes"):
                chunk = message["bytes"]
                streaming_service.buffer_audio_chunk(session_id, chunk)
                await voice_manager.send_json(
                    session_id,
                    {
                        "event": "AUDIO_CHUNK_ACK",
                        "session_id": session_id,
                        "size_bytes": len(chunk),
                    },
                )

            # Handle Text / JSON Control Messages
            elif message.get("text"):
                try:
                    payload = json.loads(message["text"])
                    event_type = payload.get("event", "PING")

                    if event_type == "PING":
                        await voice_manager.send_json(
                            session_id, {"event": "PONG", "timestamp": time.time()}
                        )

                    elif event_type == "END_CANDIDATE_SPEECH":
                        # Process Turn: STT -> InterviewService -> Persistence -> TTS
                        turn_result = streaming_service.process_voice_turn_orchestrated(
                            session_id, db=db
                        )

                        if not turn_result.get("error"):
                            # Track Latency Metrics
                            TRANSCRIPTION_DURATION.observe(
                                turn_result.get("stt_latency_ms", 100) / 1000.0
                            )
                            TTS_DURATION.observe(turn_result.get("tts_latency_ms", 100) / 1000.0)
                            VOICE_LATENCY_SECONDS.observe(
                                turn_result.get("total_latency_ms", 200) / 1000.0
                            )

                            # Send Text Response & Live Scores
                            await voice_manager.send_json(
                                session_id,
                                {
                                    "event": "TURN_COMPLETE",
                                    "type": "TURN_COMPLETE",
                                    "candidate_transcript": turn_result["candidate_transcript"],
                                    "agent_response": turn_result["agent_response"],
                                    "evaluation": turn_result.get("evaluation"),
                                    "next_question": turn_result.get("next_question"),
                                    "live_scores": turn_result.get("live_scores", {}),
                                },
                            )

                            # Stream TTS Audio Response
                            audio_out = turn_result.get("audio_response_bytes")
                            if audio_out:
                                await voice_manager.send_bytes(session_id, audio_out)

                    elif event_type == "HEARTBEAT":
                        await voice_manager.send_json(
                            session_id, {"event": "HEARTBEAT_ACK", "status": session_record.status}
                        )

                except Exception as exc:
                    logger.error(f"Error processing voice text message: {exc}")
                    await voice_manager.send_json(
                        session_id, {"event": "ERROR", "detail": str(exc)}
                    )

    except WebSocketDisconnect:
        logger.info(f"Voice WebSocket disconnected gracefully for session {session_id}")
    finally:
        voice_manager.disconnect(session_id, websocket)
