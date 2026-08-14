"""
LLM Client — provider-agnostic LangChain abstraction.

All agents call this module exclusively. Provider, model, temperature,
and fallback strategy are configuration, not code.
Default provider: Ollama (Qwen 3 Instruct) as specified in Phase 1 Architecture.
"""

from __future__ import annotations

import time
from typing import Any, Optional, Type, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


def _build_chat_model(
    model_name: str,
    temperature: float,
    max_tokens: int,
) -> BaseChatModel:
    """Instantiate a LangChain chat model from configuration."""
    provider = settings.llm_provider.lower()
    
    if provider == "ollama":
        try:
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(
                model=model_name,
                base_url=settings.ollama_base_url,
                temperature=temperature,
            )
        except ImportError:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                base_url=f"{settings.ollama_base_url}/v1",
                api_key="ollama",
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
        # Fallback to OpenAI-compatible interface for local servers
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            base_url=f"{settings.ollama_base_url}/v1",
            api_key="ollama",
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
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
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
            logger.debug(f"LLM response in {latency}ms using {getattr(model, 'model_name', getattr(model, 'model', 'ollama'))}")
            return response.content
        except Exception as exc:
            self._consecutive_failures += 1
            logger.warning(f"LLM call failed ({self._consecutive_failures} consecutive): {exc}")
            raise

    def invoke_structured(
        self,
        messages: list[BaseMessage],
        output_schema: Type[T],
        retry_feedback: Optional[str] = None,
    ) -> T:
        """
        Call the model and parse the response into a Pydantic model.
        Uses LangChain's .with_structured_output() binding.
        """
        model = self._fallback if self._consecutive_failures >= 2 else self._primary
        structured_model = model.with_structured_output(output_schema)
        t0 = time.monotonic()
        try:
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
        developer_prompt: Optional[str] = None,
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

    def __init__(self, responses: Optional[list[Any]] = None) -> None:
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
        output_schema: Type[T],
        retry_feedback: Optional[str] = None,
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
