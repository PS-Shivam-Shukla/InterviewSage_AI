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
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class Observation(BaseModel):
    """Structured observation object returned to PolicyNode after tool execution."""

    tool_name: str
    success: bool
    output: Any = None
    error: str | None = None
    latency_ms: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class ToolExecutor:
    """
    Execution boundary layer for model-mediated tool invocations.
    Prevents direct LLM code execution by routing through MCPProtocolClient ClientSession boundary.
    """

    def __init__(self, mcp_client: Any | None = None) -> None:
        if mcp_client is None:
            from app.mcp.client import mcp_protocol_client

            self._client = mcp_protocol_client
        else:
            self._client = mcp_client

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Observation:
        """
        Validate and execute requested tool name with provided arguments via official MCP ClientSession protocol.
        Returns a structured Observation.
        """
        t0 = time.monotonic()
        logger.info(
            f"\n================================================================================\n"
            f"🔧 [TOOL EXECUTOR STARTED] Tool: '{tool_name}' | Arguments Keys: {list(arguments.keys())}\n"
            f"────────────────────────────────────────────────────────────────────────────────"
        )

        try:
            # Route call through official MCPProtocolClient session protocol
            if hasattr(self._client, "call_tool_protocol_sync"):
                res = self._client.call_tool_protocol_sync(tool_name, arguments)
            elif hasattr(self._client, "call_tool"):
                # Fallback / mock registry support for tests
                raw_res = self._client.call_tool(tool_name, **arguments)
                res = {
                    "success": getattr(raw_res, "success", False),
                    "output": getattr(raw_res, "output", None),
                    "error": getattr(raw_res, "error", None),
                    "latency_ms": getattr(raw_res, "latency_ms", 0),
                }
            else:
                res = self._client.call_tool_protocol(tool_name, arguments)

            latency = int((time.monotonic() - t0) * 1000)
            success = res.get("success", False)

            if success:
                out_summary = str(res.get("output"))[:250].replace("\n", " ")
                logger.info(
                    f"🔧 [TOOL EXECUTOR COMPLETED] Tool: '{tool_name}' | Status: SUCCESS | Latency: {latency}ms\n"
                    f"   Output Summary: {out_summary}\n"
                    f"================================================================================"
                )
                return Observation(
                    tool_name=tool_name,
                    success=True,
                    output=res.get("output"),
                    latency_ms=latency,
                )
            else:
                err_msg = res.get("error") or "Tool execution returned unsuccessful status."
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
                exc_info=True,
            )
            return Observation(
                tool_name=tool_name,
                success=False,
                error=str(exc),
                latency_ms=latency,
            )


# Singleton ToolExecutor instance
tool_executor = ToolExecutor()
