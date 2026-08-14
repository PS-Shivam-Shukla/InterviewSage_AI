"""
Retry Engine & Circuit Breaker Subsystem for AI Gateway.
Implements exponential backoff with jitter, timeout controls, circuit breaker states, and fallback execution.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

from app.core.logging import get_logger
from app.core.metrics import LLM_FAILURES_TOTAL, LLM_RETRY_TOTAL

logger = get_logger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Circuit tripped, requests rejected or routed immediately to fallback
    HALF_OPEN = "HALF_OPEN"# Testing recovery


class CircuitBreaker:
    """
    Circuit Breaker for LLM provider health management.
    """

    def __init__(
        self,
        name: str = "llm_circuit",
        failure_threshold: int = 5,
        recovery_time_seconds: float = 30.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_time_seconds = recovery_time_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def allow_request(self) -> bool:
        """Check if request is allowed through circuit breaker."""
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time >= self.recovery_time_seconds:
                logger.info(f"CircuitBreaker [{self.name}] transition OPEN -> HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True

    def record_success(self) -> None:
        """Record successful invocation."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"CircuitBreaker [{self.name}] transition HALF_OPEN -> CLOSED")
            self.state = CircuitState.CLOSED
        self.failure_count = 0

    def record_failure(self) -> None:
        """Record failed invocation and trip circuit if threshold exceeded."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            logger.warning(f"CircuitBreaker [{self.name}] tripped! State -> OPEN (failures={self.failure_count})")
            self.state = CircuitState.OPEN


class RetryEngine:
    """
    Executes callable with exponential backoff, jitter, circuit breaker checking, and fallback invocation.
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay_ms: float = 200.0,
        max_delay_ms: float = 3000.0,
        backoff_factor: float = 2.0,
    ) -> None:
        self.max_retries = max_retries
        self.initial_delay_ms = initial_delay_ms
        self.max_delay_ms = max_delay_ms
        self.backoff_factor = backoff_factor
        self._circuit_breakers: dict[str, CircuitBreaker] = {}

    def get_circuit_breaker(self, provider: str) -> CircuitBreaker:
        """Get or create CircuitBreaker for provider."""
        if provider not in self._circuit_breakers:
            self._circuit_breakers[provider] = CircuitBreaker(name=provider)
        return self._circuit_breakers[provider]

    def execute_with_retry(
        self,
        func: Callable[..., Any],
        provider: str,
        fallback_func: Callable[..., Any] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute func with exponential backoff retries and optional fallback invocation.
        """
        circuit = self.get_circuit_breaker(provider)

        if not circuit.allow_request():
            logger.warning(f"CircuitBreaker for [{provider}] is OPEN. Executing fallback immediately.")
            if fallback_func:
                return fallback_func(*args, **kwargs)
            raise RuntimeError(f"CircuitBreaker for provider [{provider}] is OPEN and no fallback function supplied.")

        attempt = 0
        delay_ms = self.initial_delay_ms

        while attempt <= self.max_retries:
            try:
                attempt += 1
                result = func(*args, **kwargs)
                circuit.record_success()
                return result
            except Exception as exc:
                if attempt > 1:
                    LLM_RETRY_TOTAL.labels(provider=provider).inc()
                logger.warning(f"RetryEngine attempt {attempt}/{self.max_retries + 1} for [{provider}] failed: {exc}")

                if attempt > self.max_retries:
                    circuit.record_failure()
                    LLM_FAILURES_TOTAL.labels(provider=provider).inc()

                    if fallback_func:
                        logger.info(f"Retries exhausted for [{provider}]. Executing fallback implementation.")
                        try:
                            return fallback_func(*args, **kwargs)
                        except Exception as fallback_exc:
                            logger.error(f"Fallback implementation also failed: {fallback_exc}", exc_info=True)
                            raise fallback_exc
                    raise exc

                # Calculate exponential backoff with jitter
                sleep_sec = min(self.max_delay_ms, delay_ms) / 1000.0
                jitter = random.uniform(0, 0.1 * sleep_sec)
                time.sleep(sleep_sec + jitter)
                delay_ms *= self.backoff_factor
