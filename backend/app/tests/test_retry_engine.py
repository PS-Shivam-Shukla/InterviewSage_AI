"""
Unit Tests for RetryEngine & CircuitBreaker Subsystems.
Verifies retry backoff, circuit breaker trip/recovery states, and fallback execution.
"""

import pytest
from app.ai.retry import CircuitBreaker, CircuitState, RetryEngine


def test_retry_engine_success_on_first_try():
    """Verify function executes successfully on first attempt."""
    engine = RetryEngine(max_retries=2)
    calls = []

    def _sample():
        calls.append(1)
        return "success"

    result = engine.execute_with_retry(_sample, provider="ollama")
    assert result == "success"
    assert len(calls) == 1


def test_retry_engine_retries_and_succeeds():
    """Verify retry engine retries on failure before succeeding."""
    engine = RetryEngine(max_retries=2, initial_delay_ms=10.0)
    attempts = [0]

    def _flaky():
        attempts[0] += 1
        if attempts[0] == 1:
            raise ValueError("Transient error")
        return "flaky_success"

    result = engine.execute_with_retry(_flaky, provider="ollama")
    assert result == "flaky_success"
    assert attempts[0] == 2


def test_retry_engine_fallback_on_max_retries():
    """Verify retry engine invokes fallback when max retries are exceeded."""
    engine = RetryEngine(max_retries=1, initial_delay_ms=10.0)

    def _failing():
        raise RuntimeError("Persistent failure")

    def _fallback():
        return "fallback_result"

    result = engine.execute_with_retry(_failing, provider="openai", fallback_func=_fallback)
    assert result == "fallback_result"


def test_circuit_breaker_trips_on_threshold():
    """Verify CircuitBreaker trips to OPEN when failure threshold is reached."""
    cb = CircuitBreaker(name="test_cb", failure_threshold=2, recovery_time_seconds=10.0)

    assert cb.allow_request() is True
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED

    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False
