"""
Unit and Integration Tests for Speech-to-Text (STT) Service.
"""

from app.speech.stt import FasterWhisperSTTService


def test_stt_transcribe_bytes():
    """Verify FasterWhisperSTTService transcribes audio bytes."""
    service = FasterWhisperSTTService(model_name="base", device="cpu")
    dummy_audio = b"\x00\x01\x02\x03" * 100

    transcript = service.transcribe_bytes(dummy_audio)
    assert transcript is not None
    assert isinstance(transcript, str)
    assert len(transcript) > 0


def test_stt_transcribe_stream():
    """Verify STT streaming chunk generator."""
    service = FasterWhisperSTTService(model_name="base", device="cpu")

    def chunk_gen():
        for _ in range(5):
            yield b"\x00" * 8000

    stream_results = list(service.transcribe_stream(chunk_gen()))
    assert isinstance(stream_results, list)
    assert len(stream_results) >= 1
