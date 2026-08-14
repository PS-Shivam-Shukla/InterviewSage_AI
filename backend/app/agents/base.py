"""
Base agent class — shared retry logic, logging, and structured output
validation that every specialist agent inherits.

Design contract (Section 10):
  - Agents receive InterviewState (or a slice of it).
  - Agents return a dict of ONLY the keys they modify.
  - Agents validate all LLM output against Pydantic schemas before
    writing to state — validation failure triggers up to MAX_RETRIES
    re-prompts with the error injected.
  - All executions are persisted to AGENT_LOG via the MCP tool.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.core.llm_client import LLMClient
from app.core.logging import get_logger
from app.graph.state import InterviewState

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)

MAX_RETRIES = 2


class BaseAgent(ABC):
    """
    Abstract base for every InterviewSage AI agent.

    Subclasses implement `_run` which contains the agent-specific logic.
    `__call__` wraps `_run` with retry, validation, and logging.
    """

    # Subclasses override these
    agent_name: str = "BaseAgent"
    prompt_version: str = "v1"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm = llm_client  # None → real client built lazily; injected for tests

    @property
    def llm_client(self) -> LLMClient:
        """Lazy-build the real LLM client if not injected (e.g. in tests)."""
        if self.llm is None:
            self.llm = LLMClient(temperature=self._temperature())
        return self.llm

    def _temperature(self) -> float:
        """Default temperature; deterministic agents override to 0.1."""
        return 0.4

    # ── Public entry point ────────────────────────────────────

    def __call__(self, state: InterviewState) -> dict:
        """LangGraph node entry point — wraps _run with retries and real-time console tracking."""
        t0 = time.monotonic()
        last_error: str | None = None
        interview_id = state.get("interview_id", "N/A")

        logger.info(
            f"\n================================================================================\n"
            f"🤖 [AGENT STARTED] Agent: {self.agent_name} | Interview ID: {interview_id} | Prompt: {self.prompt_version}\n"
            f"────────────────────────────────────────────────────────────────────────────────"
        )

        for attempt in range(MAX_RETRIES + 1):
            try:
                result = self._run(state, retry_feedback=last_error)
                latency = int((time.monotonic() - t0) * 1000)
                self._log(state, "SUCCESS", result, latency, attempt)
                return result
            except (ValidationError, ValueError) as exc:
                last_error = str(exc)
                logger.warning(
                    f"[{self.agent_name}] attempt {attempt + 1}/{MAX_RETRIES + 1} "
                    f"validation error: {last_error[:120]}"
                )
                if attempt == MAX_RETRIES:
                    latency = int((time.monotonic() - t0) * 1000)
                    self._log(state, "FAILED", {}, latency, attempt, last_error)
                    return self._on_failure(state, last_error)
            except Exception as exc:
                last_error = str(exc)
                logger.error(f"[{self.agent_name}] unexpected error: {last_error}")
                if attempt == MAX_RETRIES:
                    latency = int((time.monotonic() - t0) * 1000)
                    self._log(state, "FAILED", {}, latency, attempt, last_error)
                    return self._on_failure(state, last_error)

        return {}  # unreachable but satisfies type checker

    # ── Subclass contract ─────────────────────────────────────

    @abstractmethod
    def _run(self, state: InterviewState, retry_feedback: str | None = None) -> dict:
        """
        Core agent logic. Must return a dict of state keys to update.
        If output fails validation, raise ValueError or ValidationError
        so the retry loop can re-prompt.
        """

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        """
        Default degraded-path handler after all retries are exhausted.
        Subclasses override to return safe fallback state.
        """
        return {
            "error_log": [
                {
                    "agent": self.agent_name,
                    "error": error,
                    "interview_id": state.get("interview_id"),
                }
            ]
        }

    # ── Helpers ───────────────────────────────────────────────

    def _invoke_structured(
        self,
        messages: list,
        schema: type[T],
        retry_feedback: str | None = None,
    ) -> T:
        """
        Call the LLM and parse output into `schema`.
        If retry_feedback is set, append it as a corrective system message.
        """
        if retry_feedback:
            from langchain_core.messages import SystemMessage

            messages = messages + [
                SystemMessage(
                    content=(
                        f"Your previous response failed validation with this error:\n"
                        f"{retry_feedback}\n"
                        "Please correct your response and return valid JSON matching the schema."
                    )
                )
            ]
        return self.llm_client.invoke_structured(messages, schema)

    def _log(
        self,
        state: InterviewState,
        status: str,
        output: dict,
        latency_ms: int,
        retry_count: int,
        error: str | None = None,
    ) -> None:
        """Write real-time console tracking and persist to AGENT_LOG if a db session is available."""
        # 1. Print formatted real-time telemetry block to console/stdout
        try:
            output_summary = (
                str(output)[:250].replace("\n", " ") if output else (error or "No output")
            )
            logger.info(
                f"🤖 [AGENT COMPLETED] Agent: {self.agent_name} | Status: {status} | Latency: {latency_ms}ms | Retries: {retry_count}\n"
                f"   Output Summary: {output_summary}\n"
                f"================================================================================"
            )
        except Exception:
            pass

        # 2. Persist log to DB via MCP server if session present
        db = state.get("_db_session")
        if db is None:
            return
        try:
            from app.mcp import mcp_server

            mcp_server.call_tool(
                "persist_agent_output",
                db_session=db,
                interview_id=state.get("interview_id", ""),
                agent_name=self.agent_name,
                node_status=status,
                input_snapshot={"keys": list(state.keys())},
                output_snapshot=output,
                latency_ms=latency_ms,
                retry_count=retry_count,
                prompt_version=self.prompt_version,
            )
        except Exception as exc:
            logger.warning(f"[{self.agent_name}] failed to persist log: {exc}")
