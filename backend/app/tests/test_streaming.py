"""
Unit and Integration Tests for AudioStreamingService.
"""

from sqlalchemy.orm import Session

from app.speech.streaming import AudioStreamingService


def test_audio_streaming_buffering(db_session: Session):
    """Verify AudioStreamingService buffers incoming audio byte chunks."""
    service = AudioStreamingService(db=db_session)
    session_id = "sess-stream-101"

    b1 = service.buffer_audio_chunk(session_id, b"\x01\x02\x03")
    b2 = service.buffer_audio_chunk(session_id, b"\x04\x05\x06")

    assert b1 == 3
    assert b2 == 6
    assert len(service.get_buffered_bytes(session_id)) == 6

    service.clear_buffer(session_id)
    assert len(service.get_buffered_bytes(session_id)) == 0


def test_audio_streaming_process_turn(db_session: Session):
    """Verify processing candidate audio turn executes STT, LLM response, and TTS synthesis."""
    service = AudioStreamingService(db=db_session)
    session_id = "sess-stream-turn"

    res = service.process_candidate_audio_turn(session_id, audio_bytes=b"\x00" * 500)
    assert res["session_id"] == session_id
    assert "candidate_transcript" in res
    assert "agent_response" in res
    assert isinstance(res["audio_response_bytes"], bytes)
    assert res["total_latency_ms"] > 0
