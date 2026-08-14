"""
Tool Executor Module — Execution Boundary & Observation Capture.
Enforces strict execution constraints:
1. Validates that requested tool is registered in the MCP tool registry.
2. Validates tool arguments against the tool's machine-readable parameters schema.
3. Executes tool handler safely.
4. Packages result into a structured Observation for PolicyNode loop feedback.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class Observation(BaseModel):
    """Structured observation object returned to PolicyNode after tool execution."""
    tool_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    latency_ms: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ToolExecutor:
    """
    Execution boundary layer for model-mediated tool invocations.
    Prevents direct LLM code execution by routing through registered MCP tool schemas.
    """

    def __init__(self, mcp_registry: Optional[Any] = None) -> None:
        if mcp_registry is None:
            from app.mcp import mcp_server
            self._registry = mcp_server
        else:
            self._registry = mcp_registry

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Observation:
        """
        Validate and execute requested tool name with provided arguments.
        Returns a structured Observation.
        """
        t0 = time.monotonic()
        logger.info(
            f"\n================================================================================\n"
            f"🔧 [TOOL EXECUTOR STARTED] Tool: '{tool_name}' | Arguments Keys: {list(arguments.keys())}\n"
            f"────────────────────────────────────────────────────────────────────────────────"
        )

        try:
            # Route call through registry
            res = self._registry.call_tool(tool_name, **arguments)
            latency = int((time.monotonic() - t0) * 1000)
            success = getattr(res, "success", False)

            if success:
                out_summary = str(getattr(res, "output", None))[:250].replace("\n", " ")
                logger.info(
                    f"🔧 [TOOL EXECUTOR COMPLETED] Tool: '{tool_name}' | Status: SUCCESS | Latency: {latency}ms\n"
                    f"   Output Summary: {out_summary}\n"
                    f"================================================================================"
                )
                return Observation(
                    tool_name=tool_name,
                    success=True,
                    output=getattr(res, "output", None),
                    latency_ms=latency,
                )
            else:
                err_msg = getattr(res, "error", None) or "Tool execution returned unsuccessful status."
                logger.warning(
                    f"🔧 [TOOL EXECUTOR FAILED] Tool: '{tool_name}' | Status: FAILED | Latency: {latency}ms\n"
                    f"   Error: {err_msg}\n"
                    f"================================================================================"
                )
                return Observation(
                    tool_name=tool_name,
                    success=False,
                    error=err_msg,
                    latency_ms=latency,
                )
        except Exception as exc:
            latency = int((time.monotonic() - t0) * 1000)
            logger.error(
                f"🔧 [TOOL EXECUTOR EXCEPTION] Tool: '{tool_name}' | Status: EXCEPTION | Latency: {latency}ms\n"
                f"   Error: {exc}\n"
                f"================================================================================",
                exc_info=True
            )
            return Observation(
                tool_name=tool_name,
                success=False,
                error=str(exc),
                latency_ms=latency,
            )


# Singleton ToolExecutor instance
tool_executor = ToolExecutor()
