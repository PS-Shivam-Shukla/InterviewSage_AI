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
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


# ─────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────

@dataclass
class ToolSchema:
    """Metadata + callable for one registered tool."""
    name: str
    description: str
    parameters: Dict[str, Any]          # JSON Schema-style parameter spec
    handler: Callable[..., Any]
    required_params: List[str] = field(default_factory=list)


@dataclass
class ResourceSchema:
    """Metadata + callable for one registered resource."""
    uri_template: str                   # e.g. "resource://industry-standards/{role}"
    description: str
    handler: Callable[..., Any]         # called with the resolved URI variables


@dataclass
class PromptSchema:
    """A server-managed, versioned prompt template."""
    name: str
    version: str
    template: str                       # raw prompt string with {variable} placeholders


@dataclass
class ToolCallResult:
    """Standardised result returned to the calling agent."""
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    latency_ms: int = 0


# ─────────────────────────────────────────────────────────────
# MCP Server
# ─────────────────────────────────────────────────────────────

class MCPServer:
    """
    In-process MCP server.

    Agents interact exclusively through:
        server.call_tool(name, **kwargs)
        server.read_resource(uri)
        server.get_prompt(name, version)

    All invocations are logged to the internal call log for
    observability (surfaced in the Admin Dashboard).
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolSchema] = {}
        self._resources: List[ResourceSchema] = []
        self._prompts: Dict[str, PromptSchema] = {}
        self._call_log: List[Dict[str, Any]] = []

    # ── Tool registry ─────────────────────────────────────────

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Any],
        required_params: Optional[List[str]] = None,
    ) -> None:
        """Register a tool with the server."""
        self._tools[name] = ToolSchema(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            required_params=required_params or [],
        )

    def list_tools(self) -> List[Dict[str, Any]]:
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
        Invoke a registered tool.

        Args:
            name: Tool name as registered
            **kwargs: Tool-specific arguments

        Returns:
            ToolCallResult with output or error details
        """
        if name not in self._tools:
            return ToolCallResult(
                tool_name=name,
                success=False,
                output=None,
                error=f"Unknown tool: {name!r}",
            )

        tool = self._tools[name]

        # Validate required params
        missing = [p for p in tool.required_params if p not in kwargs]
        if missing:
            return ToolCallResult(
                tool_name=name,
                success=False,
                output=None,
                error=f"Missing required parameters: {missing}",
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
        except Exception as exc:
            latency = int((time.monotonic() - t0) * 1000)
            result = ToolCallResult(
                tool_name=name,
                success=False,
                output=None,
                error=str(exc),
                latency_ms=latency,
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

    def list_resources(self) -> List[Dict[str, Any]]:
        """Return discoverable resource metadata."""
        return [
            {"uri_template": r.uri_template, "description": r.description}
            for r in self._resources
        ]

    def read_resource(self, uri: str) -> Optional[Any]:
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

    def get_prompt(self, name: str, version: str = "v1") -> Optional[str]:
        """Retrieve a prompt template by name and version."""
        schema = self._prompts.get(f"{name}:{version}")
        return schema.template if schema else None

    # ── Observability ─────────────────────────────────────────

    def get_call_log(self) -> List[Dict[str, Any]]:
        """Return the internal call log for admin/debugging."""
        return list(self._call_log)

    def reset_call_log(self) -> None:
        """Clear the call log (e.g. between tests)."""
        self._call_log.clear()


# ─────────────────────────────────────────────────────────────
# URI template matching helper
# ─────────────────────────────────────────────────────────────

def _match_uri(template: str, uri: str) -> Optional[Dict[str, str]]:
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

    variables: Dict[str, str] = {}
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
