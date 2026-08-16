"""
LLM Client — provider-agnostic LangChain abstraction.

All agents call this module exclusively. Provider, model, temperature,
and fallback strategy are configuration, not code.
Default provider: Ollama (Qwen 3 Instruct) as specified in Phase 1 Architecture.
"""

from __future__ import annotations

import json
import time
from typing import Any, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


def check_ollama_health(host: str | None = None, timeout: float = 3.0) -> bool:
    """
    Non-blocking pre-flight connectivity check to Ollama server.
    NEVER starts or spawns any server process.
    """
    import urllib.request

    target_host = host or settings.ollama_base_url
    hosts_to_try = [target_host]
    if "localhost" in target_host:
        hosts_to_try.append(target_host.replace("localhost", "127.0.0.1"))

    for h in hosts_to_try:
        url = f"{h.rstrip('/')}/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "InterviewSageAI-HealthCheck"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status_code = getattr(resp, "status", None) or (resp.getcode() if hasattr(resp, "getcode") else 200)
                if status_code == 200:
                    logger.info(f"[OLLAMA CHECK] host={h} status=AVAILABLE")
                    return True
        except Exception as exc:
            logger.warning(f"[OLLAMA CHECK] host={h} status=UNAVAILABLE error={exc}")
    return False


def _build_chat_model(
    model_name: str,
    temperature: float,
    max_tokens: int,
) -> BaseChatModel:
    """Instantiate a LangChain chat model from configuration."""
    provider = settings.llm_provider.lower()

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            try:
                from langchain_community.chat_models import ChatOllama
            except ImportError as exc:
                raise RuntimeError(
                    "LLM provider is set to 'ollama', but neither 'langchain_ollama' nor "
                    "'langchain_community.chat_models.ChatOllama' could be imported. "
                    "Please install the `langchain-ollama` package."
                ) from exc

        return ChatOllama(
            model=model_name,
            base_url=settings.ollama_base_url,
            temperature=temperature,
            num_predict=max_tokens or 2048,
            num_ctx=8192,
            format="json",
            timeout=120.0,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.llm_api_key or "fake-key",
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.llm_api_key or "fake-key",
        )
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider}'. "
            "Supported providers are 'ollama', 'openai', and 'anthropic'."
        )


class LLMClient:
    """
    Thin wrapper around LangChain chat models.

    Features:
      - Primary + fallback model
      - Structured output binding (.with_structured_output)
      - Per-call latency logging
      - Automatic fallback on provider error (2 consecutive failures)
    """

    def __init__(
        self,
        model_name: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> None:
        self._model_name = model_name or settings.llm_model_name
        self._temperature = temperature if temperature is not None else settings.llm_temperature
        self._max_tokens = max_tokens or settings.llm_max_tokens

        self._primary: BaseChatModel = _build_chat_model(
            self._model_name, self._temperature, self._max_tokens
        )
        self._fallback: BaseChatModel = _build_chat_model(
            settings.llm_fallback_model, self._temperature, self._max_tokens
        )
        self._consecutive_failures = 0

    # ── Core call ─────────────────────────────────────────────

    def invoke(self, messages: list[BaseMessage]) -> str:
        """
        Send a list of LangChain messages and return the text reply.
        Falls back to the secondary model after 2 consecutive failures.
        """
        model = self._fallback if self._consecutive_failures >= 2 else self._primary
        t0 = time.monotonic()
        try:
            response = model.invoke(messages)
            self._consecutive_failures = 0
            latency = int((time.monotonic() - t0) * 1000)
            logger.debug(
                f"LLM response in {latency}ms using {getattr(model, 'model_name', getattr(model, 'model', 'ollama'))}"
            )
            return response.content
        except Exception as exc:
            self._consecutive_failures += 1
            logger.warning(f"LLM call failed ({self._consecutive_failures} consecutive): {exc}")
            raise

    def invoke_structured(
        self,
        messages: list[BaseMessage],
        output_schema: type[T],
        retry_feedback: str | None = None,
    ) -> T:
        """
        Call the model and parse the response into a Pydantic model.
        Uses LangChain's .with_structured_output() binding.
        """
        model = self._fallback if self._consecutive_failures >= 2 else self._primary
        t0 = time.monotonic()
        try:
            if settings.llm_provider.lower() == "ollama":
                response = model.invoke(messages)
                content_str = getattr(response, "content", str(response)).strip()

                # Strip Qwen3 <think>...</think> reasoning tokens before parsing
                import re as _re
                content_str = _re.sub(r"<think>.*?</think>", "", content_str, flags=_re.DOTALL).strip()

                # Strip markdown code fences
                if content_str.startswith("```"):
                    content_str = content_str.split("```", 2)[1]
                    if content_str.startswith("json"):
                        content_str = content_str[4:].strip()
                content_str = content_str.strip()

                # Guard against empty / whitespace-only responses
                if not content_str:
                    raise ValueError(
                        "Ollama returned an empty response body (model produced no JSON output). "
                        "This usually means the model ran out of tokens or the think block consumed the full output."
                    )

                # Find the first '{' — ignore any leading text/whitespace before JSON
                json_start = content_str.find("{")
                if json_start == -1:
                    raise ValueError(
                        f"Ollama response contains no JSON object. "
                        f"Response (first 200 chars): {content_str[:200]!r}"
                    )
                content_str = content_str[json_start:]

                data = json.loads(content_str)
                result: T = output_schema.model_validate(data)
            else:
                structured_model = model.with_structured_output(output_schema)
                result: T = structured_model.invoke(messages)
            self._consecutive_failures = 0
            latency = int((time.monotonic() - t0) * 1000)
            logger.debug(f"Structured LLM response in {latency}ms")
            return result
        except Exception as exc:
            self._consecutive_failures += 1
            logger.warning(f"Structured LLM call failed: {exc}")
            raise

    # ── Convenience helpers ────────────────────────────────────

    @staticmethod
    def build_messages(
        system_prompt: str,
        user_content: str,
        developer_prompt: str | None = None,
    ) -> list[BaseMessage]:
        """
        Assemble a message list following the 4-layer prompt architecture:
        system → developer → user.
        """
        msgs: list[BaseMessage] = [SystemMessage(content=system_prompt)]
        if developer_prompt:
            msgs.append(SystemMessage(content=developer_prompt))
        msgs.append(HumanMessage(content=user_content))
        return msgs


# ─────────────────────────────────────────────────────────────
# FakeLLMClient — deterministic test double
# ─────────────────────────────────────────────────────────────


class FakeLLMClient(LLMClient):
    """
    Test double that returns pre-configured responses without any
    real API call. Used across all unit and workflow tests.
    """

    def __init__(self, responses: list[Any] | None = None) -> None:
        self._responses: list[Any] = responses or []
        self._call_index = 0
        self._consecutive_failures = 0
        self._calls: list[list[BaseMessage]] = []

    def invoke(self, messages: list[BaseMessage]) -> str:
        self._calls.append(messages)
        if self._call_index < len(self._responses):
            result = self._responses[self._call_index]
            self._call_index += 1
            return str(result)
        return "Fake LLM response"

    def invoke_structured(
        self,
        messages: list[BaseMessage],
        output_schema: type[T],
        retry_feedback: str | None = None,
    ) -> T:
        self._calls.append(messages)
        if self._call_index < len(self._responses):
            result = self._responses[self._call_index]
            self._call_index += 1
            if isinstance(result, output_schema):
                return result
            if isinstance(result, dict):
                return output_schema(**result)
        return output_schema.model_construct()

    @property
    def calls(self) -> list[list[BaseMessage]]:
        return self._calls
