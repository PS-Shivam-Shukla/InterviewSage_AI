"""
Unit and Integration Tests for Text-to-Speech (TTS) Service.
"""

import pytest
from app.speech.tts import KokoroTTSService


def test_tts_speak_and_synthesize():
    """Verify KokoroTTSService synthesizes audio WAV/PCM bytes."""
    service = KokoroTTSService(provider="kokoro", voice="en", speed=1.0)
    text = "Welcome to your technical interview session."

    audio_bytes = service.speak(text)
    assert audio_bytes is not None
    assert isinstance(audio_bytes, bytes)
    assert len(audio_bytes) > 40  # Valid WAV header + audio payload


def test_tts_stream_audio():
    """Verify TTS streaming audio chunk generator."""
    service = KokoroTTSService(provider="kokoro", voice="en", speed=1.0)
    text = "Please describe how you would design a rate limiter."

    chunks = list(service.stream_audio(text))
    assert len(chunks) >= 1
    assert isinstance(chunks[0], bytes)
