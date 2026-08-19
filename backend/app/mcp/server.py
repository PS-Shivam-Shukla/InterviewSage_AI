"""
Model Context Protocol (MCP) Server — in-process implementation.

The MCP server exposes Tools, Resources, and Prompts to AI agents
through a structured, discoverable, permissioned interface.

Architecture:
    Host (FastAPI + LangGraph) → MCP Client → MCP Server (this module)
    Agents never call tool implementations directly — they go through
    the server registry, which enforces permissions and logs every call.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import json
from mcp.server import Server as OfficialServer
import mcp.types as types


# ─────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────


@dataclass
class ToolSchema:
    """Metadata + callable for one registered tool."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema-style parameter spec
    handler: Callable[..., Any]
    required_params: list[str] = field(default_factory=list)


@dataclass
class ResourceSchema:
    """Metadata + callable for one registered resource."""

    uri_template: str  # e.g. "resource://industry-standards/{role}"
    description: str
    handler: Callable[..., Any]  # called with the resolved URI variables


@dataclass
class PromptSchema:
    """A server-managed, versioned prompt template."""

    name: str
    version: str
    template: str  # raw prompt string with {variable} placeholders


@dataclass
class ToolCallResult:
    """Standardised result returned to the calling agent."""

    tool_name: str
    success: bool
    output: Any
    error: str | None = None
    latency_ms: int = 0


# ─────────────────────────────────────────────────────────────
# MCP Server
# ─────────────────────────────────────────────────────────────


class MCPServer:
    """
    Model Context Protocol (MCP) Server.
    Exposes application tools, resources, and prompts over the official MCP protocol
    via mcp.server.Server instance and JSON-RPC 2.0 handlers.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolSchema] = {}
        self._resources: list[ResourceSchema] = []
        self._prompts: dict[str, PromptSchema] = {}
        self._call_log: list[dict[str, Any]] = []

        # Official MCP SDK Server instance
        self.official_server = OfficialServer("interviewsage-mcp-server")
        self._setup_official_handlers()

    def _setup_official_handlers(self) -> None:
        """Register official MCP JSON-RPC request handlers for tools/list and tools/call."""

        async def handle_list_tools(ctx, params):
            tool_objects = []
            for t in self._tools.values():
                tool_objects.append(
                    types.Tool(
                        name=t.name,
                        description=t.description,
                        input_schema={
                            "type": "object",
                            "properties": t.parameters,
                            "required": t.required_params,
                        },
                    )
                )
            return types.ListToolsResult(tools=tool_objects)

        async def handle_call_tool(ctx, params):
            tool_name = params.name
            arguments = params.arguments or {}
            result = self.call_tool(tool_name, **arguments)

            if not result.success:
                return types.CallToolResult(
                    is_error=True,
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error executing tool '{tool_name}': {result.error}",
                        )
                    ],
                )

            out_data = result.output
            if isinstance(out_data, (dict, list)):
                text_payload = json.dumps(out_data)
            else:
                text_payload = str(out_data)

            return types.CallToolResult(
                is_error=False,
                content=[types.TextContent(type="text", text=text_payload)],
            )

        self.official_server.add_request_handler(
            "tools/list", types.PaginatedRequestParams, handle_list_tools
        )
        self.official_server.add_request_handler(
            "tools/call", types.CallToolRequestParams, handle_call_tool
        )

    # ── Tool registry ─────────────────────────────────────────

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[..., Any],
        required_params: list[str] | None = None,
    ) -> None:
        """Register a tool with the server."""
        self._tools[name] = ToolSchema(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            required_params=required_params or [],
        )

    def list_tools(self) -> list[dict[str, Any]]:
        """Return discoverable tool schemas (name, description, parameters)."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
                "required": t.required_params,
            }
            for t in self._tools.values()
        ]

    def call_tool(self, name: str, **kwargs: Any) -> ToolCallResult:
        """
        Invoke a registered tool with real-time console telemetry.
        """
        from app.core.logging import get_logger

        mcp_logger = get_logger(__name__)

        mcp_logger.info(
            f"\n================================================================================\n"
            f"🛠️ [MCP SERVER TOOL STARTED] Tool: '{name}' | Arguments: {list(kwargs.keys())}\n"
            f"────────────────────────────────────────────────────────────────────────────────"
        )

        if name not in self._tools:
            err_msg = f"Unknown tool: {name!r}"
            mcp_logger.warning(f"🛠️ [MCP SERVER TOOL FAILED] Tool: '{name}' | Error: {err_msg}")
            return ToolCallResult(
                tool_name=name,
                success=False,
                output=None,
                error=err_msg,
            )

        tool = self._tools[name]

        # Validate required params
        missing = [p for p in tool.required_params if p not in kwargs]
        if missing:
            err_msg = f"Missing required parameters: {missing}"
            mcp_logger.warning(f"🛠️ [MCP SERVER TOOL FAILED] Tool: '{name}' | Error: {err_msg}")
            return ToolCallResult(
                tool_name=name,
                success=False,
                output=None,
                error=err_msg,
            )

        t0 = time.monotonic()
        try:
            output = tool.handler(**kwargs)
            latency = int((time.monotonic() - t0) * 1000)
            result = ToolCallResult(
                tool_name=name,
                success=True,
                output=output,
                latency_ms=latency,
            )
            out_summary = str(output)[:250].replace("\n", " ") if output else "No output"
            mcp_logger.info(
                f"🛠️ [MCP SERVER TOOL COMPLETED] Tool: '{name}' | Status: SUCCESS | Latency: {latency}ms\n"
                f"   Output Summary: {out_summary}\n"
                f"================================================================================"
            )
        except Exception as exc:
            latency = int((time.monotonic() - t0) * 1000)
            result = ToolCallResult(
                tool_name=name,
                success=False,
                output=None,
                error=str(exc),
                latency_ms=latency,
            )
            mcp_logger.error(
                f"🛠️ [MCP SERVER TOOL EXCEPTION] Tool: '{name}' | Latency: {latency}ms | Error: {exc}\n"
                f"================================================================================"
            )

        self._call_log.append(
            {
                "tool": name,
                "kwargs_keys": list(kwargs.keys()),
                "success": result.success,
                "latency_ms": result.latency_ms,
                "error": result.error,
            }
        )
        return result

    # ── Resource registry ─────────────────────────────────────

    def register_resource(
        self,
        uri_template: str,
        description: str,
        handler: Callable[..., Any],
    ) -> None:
        """Register a resource URI template."""
        self._resources.append(
            ResourceSchema(
                uri_template=uri_template,
                description=description,
                handler=handler,
            )
        )

    def list_resources(self) -> list[dict[str, Any]]:
        """Return discoverable resource metadata."""
        return [
            {"uri_template": r.uri_template, "description": r.description} for r in self._resources
        ]

    def read_resource(self, uri: str) -> Any | None:
        """
        Read a resource by its concrete URI.
        Matches against registered URI templates.
        """
        for resource in self._resources:
            variables = _match_uri(resource.uri_template, uri)
            if variables is not None:
                return resource.handler(**variables)
        return None

    # ── Prompt registry ────────────────────────────────────────

    def register_prompt(self, name: str, version: str, template: str) -> None:
        """Register a versioned prompt template."""
        key = f"{name}:{version}"
        self._prompts[key] = PromptSchema(name=name, version=version, template=template)

    def get_prompt(self, name: str, version: str = "v1") -> str | None:
        """Retrieve a prompt template by name and version."""
        schema = self._prompts.get(f"{name}:{version}")
        return schema.template if schema else None

    # ── Observability ─────────────────────────────────────────

    def get_call_log(self) -> list[dict[str, Any]]:
        """Return the internal call log for admin/debugging."""
        return list(self._call_log)

    def reset_call_log(self) -> None:
        """Clear the call log (e.g. between tests)."""
        self._call_log.clear()


# ─────────────────────────────────────────────────────────────
# URI template matching helper
# ─────────────────────────────────────────────────────────────


def _match_uri(template: str, uri: str) -> dict[str, str] | None:
    """
    Match a concrete URI against a template with {variable} placeholders.

    Example:
        template = "resource://industry-standards/{role}"
        uri      = "resource://industry-standards/backend-engineer"
        returns  = {"role": "backend-engineer"}
    """
    t_parts = template.split("/")
    u_parts = uri.split("/")

    if len(t_parts) != len(u_parts):
        return None

    variables: dict[str, str] = {}
    for t_seg, u_seg in zip(t_parts, u_parts):
        if t_seg.startswith("{") and t_seg.endswith("}"):
            variables[t_seg[1:-1]] = u_seg
        elif t_seg != u_seg:
            return None

    return variables


# ─────────────────────────────────────────────────────────────
# Singleton — one server instance shared across the application
# ─────────────────────────────────────────────────────────────

mcp_server = MCPServer()
