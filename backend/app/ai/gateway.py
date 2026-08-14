"""
Enterprise AI Gateway — Single Entry Point for All LLM Executions.
Coordinates Model Routing, Prompt Registry, Retry Engine, Circuit Breaker, JSON Repair, and Token Accounting.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.ai.cost_tracker import CostTracker
from app.ai.request import AIGatewayRequest
from app.ai.response import AIGatewayResponse
from app.ai.retry import RetryEngine
from app.ai.router import ModelRouter, ModelSpec
from app.ai.token_tracker import TokenTracker
from app.ai.validator import JSONValidator
from app.core.logging import get_logger
from app.core.metrics import (
    LLM_ERRORS_TOTAL,
    LLM_LATENCY_SECONDS,
    LLM_REQUESTS_TOTAL,
)
from app.models.llm_audit import LLMRequest, LLMResponse
from app.prompts.registry import PromptRegistry

logger = get_logger(__name__)


class AIGateway:
    """
    Enterprise AI Gateway orchestrating LLM execution, resiliency, prompt versioning, and accounting.
    """

    def __init__(
        self,
        router: Optional[ModelRouter] = None,
        registry: Optional[PromptRegistry] = None,
        retry_engine: Optional[RetryEngine] = None,
    ) -> None:
        self.router = router or ModelRouter()
        self.registry = registry or PromptRegistry()
        self.retry_engine = retry_engine or RetryEngine()

    def _execute_llm_call(
        self,
        provider: str,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Execute raw LLM inference call via local Ollama or API provider.
        """
        if provider == "ollama":
            try:
                import httpx
                from app.core.config import settings

                url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
                payload = {
                    "model": model_name,
                    "prompt": f"System: {system_prompt}\nUser: {user_prompt}",
                    "stream": False,
                    "options": {"temperature": temperature, "num_ctx": max_tokens},
                }

                with httpx.Client(timeout=15.0) as client:
                    res = client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        response_text = str(data.get("response") or "")
                        if response_text:
                            return response_text
                        raise RuntimeError("Ollama returned empty response string")
                    raise RuntimeError(f"Ollama HTTP request failed with status code {res.status_code}: {res.text}")
            except Exception as exc:
                logger.error(f"Ollama direct HTTP call failed: {exc}")
                raise RuntimeError(f"LLM Provider 'ollama' request failed: {exc}") from exc

        raise ValueError(f"LLM Provider '{provider}' is unconfigured or unavailable")

    def execute(
        self,
        request: AIGatewayRequest,
        db: Optional[Session] = None,
    ) -> AIGatewayResponse:
        """
        Execute an AI Gateway Request with full resiliency, validation, metrics, and token accounting.
        """
        start_t = time.perf_counter()
        spec = self.router.select_model(
            task_type=request.task_type,
            provider_override=request.provider_override,
            model_override=request.model_override,
        )

        # Render version-controlled prompt
        rendered = self.registry.render(
            prompt_key=request.prompt_key,
            version=request.prompt_version,
            variables=request.variables,
        )

        sys_prompt = request.system_prompt_override or rendered["system"]
        usr_prompt = request.user_prompt_override or rendered["user"]

        LLM_REQUESTS_TOTAL.labels(model_name=spec.model_name, task_type=request.task_type).inc()

        def _primary_invocation() -> str:
            return self._execute_llm_call(
                provider=spec.provider,
                model_name=spec.model_name,
                system_prompt=sys_prompt,
                user_prompt=usr_prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

        def _fallback_invocation() -> str:
            fb_spec = self.router.get_fallback(spec)
            logger.info(f"AIGateway executing fallback provider [{fb_spec.provider}] model [{fb_spec.model_name}]")
            return self._execute_llm_call(
                provider=fb_spec.provider,
                model_name=fb_spec.model_name,
                system_prompt=sys_prompt,
                user_prompt=usr_prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

        raw_output = ""
        success = True
        error_msg = None
        retry_count = 0

        try:
            raw_output = self.retry_engine.execute_with_retry(
                func=_primary_invocation,
                provider=spec.provider,
                fallback_func=_fallback_invocation,
            )
        except Exception as exc:
            success = False
            error_msg = str(exc)
            LLM_ERRORS_TOTAL.labels(model_name=spec.model_name).inc()
            logger.error(f"AIGateway request execution failed: {exc}", exc_info=True)

        duration_ms = int((time.perf_counter() - start_t) * 1000)
        LLM_LATENCY_SECONDS.labels(provider=spec.provider, model_name=spec.model_name).observe(duration_ms / 1000.0)

        # JSON Validation & Structured Output Repair
        parsed_json = None
        repair_performed = False

        if success and request.require_json:
            is_valid, parsed_json, repair_performed = JSONValidator.validate_and_repair(raw_output)
            if not is_valid:
                logger.warning("Structured output repair failed to parse valid JSON.")

        # Token & Cost Accounting
        accounting = TokenTracker.record_usage(
            provider=spec.provider,
            model_name=spec.model_name,
            prompt_text=f"{sys_prompt}\n{usr_prompt}",
            completion_text=raw_output,
            db=db,
            interview_id=request.interview_id,
            user_id=request.user_id,
        )

        # Persist LLM Request & Response audit tables
        if db is not None:
            try:
                llm_req = LLMRequest(
                    id=str(uuid.uuid4()),
                    request_id=request.interview_id or "gateway-req",
                    interview_id=request.interview_id,
                    provider=spec.provider,
                    model_name=spec.model_name,
                    task_type=request.task_type,
                    prompt_version=rendered["version"],
                    prompt_tokens=accounting["prompt_tokens"],
                    completion_tokens=accounting["completion_tokens"],
                    total_tokens=accounting["total_tokens"],
                    latency_ms=duration_ms,
                    cost_usd=accounting["cost_usd"],
                    success=success,
                    error_message=error_msg,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(llm_req)
                db.flush()

                llm_res = LLMResponse(
                    id=str(uuid.uuid4()),
                    llm_request_id=llm_req.id,
                    raw_output=raw_output,
                    parsed_output=json.dumps(parsed_json) if parsed_json else None,
                    retry_count=retry_count,
                    repair_performed=repair_performed,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(llm_res)
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.error(f"Failed to persist LLMRequest audit trail: {exc}", exc_info=True)

        return AIGatewayResponse(
            success=success,
            raw_content=raw_output,
            parsed_json=parsed_json,
            provider=spec.provider,
            model_name=spec.model_name,
            prompt_version=rendered["version"],
            prompt_tokens=accounting["prompt_tokens"],
            completion_tokens=accounting["completion_tokens"],
            total_tokens=accounting["total_tokens"],
            latency_ms=duration_ms,
            cost_usd=accounting["cost_usd"],
            retry_count=retry_count,
            repair_performed=repair_performed,
            error_message=error_msg,
        )


# Singleton AI Gateway instance
ai_gateway = AIGateway()
